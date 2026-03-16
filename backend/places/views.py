import logging
import requests
from django.conf import settings
from django.db.models import Q
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Place, Category, Tag, Bookmark
from .serializers import (
    PlaceListSerializer, PlaceDetailSerializer,
    PlaceSubmitSerializer, TagSerializer, CategorySerializer,
    BookmarkSerializer,
)
from reviews.serializers import ReviewSerializer

AI_SERVICE_URL = getattr(settings, "AI_SERVICE_URL", "http://localhost:8000")
logger = logging.getLogger(__name__)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class PlaceViewSet(viewsets.ModelViewSet):
    """
    API endpoint de xem va submit dia diem.
    - GET  /api/places/              Danh sach dia diem APPROVED
    - GET  /api/places/{id}/         Chi tiet dia diem
    - POST /api/places/              Crowdsourcing: submit dia diem moi (-> PENDING)
    - GET  /api/places/{id}/reviews/ Danh sach reviews cua dia diem
    """

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "address", "description"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        qs = (
            Place.objects.filter(status="APPROVED")
            .select_related("category")
            .prefetch_related("tags", "images")
        )

        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category__name__icontains=category)

        is_hidden = self.request.query_params.get("hidden_gem")
        if is_hidden == "1":
            qs = qs.filter(is_hidden_gem=True)

        return qs

    def get_permissions(self):
        if self.action in ["create", "bookmark", "bookmarks"]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action == "list":
            return PlaceListSerializer
        if self.action == "create":
            return PlaceSubmitSerializer
        return PlaceDetailSerializer

    @action(detail=True, methods=["get"], url_path="reviews")
    def reviews(self, request, pk=None):
        """GET /api/places/{id}/reviews/ - Lay reviews cua dia diem"""
        place = self.get_object()
        reviews = place.reviews.select_related("user").prefetch_related("images")
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="bookmark")
    def bookmark(self, request, pk=None):
        """POST /api/places/{id}/bookmark/ - Toggle bookmark dia diem"""
        place = self.get_object()
        bookmark, created = Bookmark.objects.get_or_create(user=request.user, place=place)
        if not created:
            bookmark.delete()
            return Response({"bookmarked": False})
        return Response({"bookmarked": True})

    @action(detail=False, methods=["get"], url_path="bookmarks")
    def bookmarks(self, request):
        """GET /api/places/bookmarks/ - Danh sach bookmark cua user"""
        bookmarks = (
            Bookmark.objects.filter(user=request.user)
            .select_related("place__category")
            .prefetch_related("place__tags", "place__images")
        )
        serializer = BookmarkSerializer(bookmarks, many=True, context={"request": request})
        return Response(serializer.data)


class SearchViewSet(viewsets.ViewSet):
    """
    API Tim kiem ngu nghia (Semantic Search) tich hop AI Service.
    POST /api/search/  - Body: {"query": "quan ca phe chill gan bien", "top_k": 10}
    """

    permission_classes = [AllowAny]

    def _keyword_fallback(self, query, top_k, request):
        keywords = [w for w in query.split() if len(w) >= 2][:8]
        if not keywords:
            return []

        q_filter = Q()
        for kw in keywords:
            q_filter |= (
                Q(name__icontains=kw)
                | Q(address__icontains=kw)
                | Q(description__icontains=kw)
            )

        places = (
            Place.objects.filter(status="APPROVED")
            .filter(q_filter)
            .select_related("category")
            .prefetch_related("tags")
            .distinct()[:top_k]
        )

        serializer = PlaceListSerializer(places, many=True, context={"request": request})
        results = serializer.data
        for item in results:
            item["ai_score"] = 0.0
            item["match_reason"] = "keyword_fallback"
        return results

    def create(self, request):
        query = request.data.get("query", "").strip()
        top_k = int(request.data.get("top_k", 10))

        if not query:
            return Response({"error": "Vui long nhap tu khoa tim kiem"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ai_response = requests.post(
                f"{AI_SERVICE_URL}/search",
                json={"text": query, "top_k": top_k},
                timeout=10,
            )
            ai_response.raise_for_status()
            ai_results = ai_response.json().get("results", [])
        except requests.exceptions.RequestException as e:
            logger.exception("AI Service unreachable for query='%s'", query)
            return Response(
                {"error": f"AI Service khong phan hoi: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not ai_results:
            fallback_results = self._keyword_fallback(query, top_k, request)
            return Response(
                {
                    "query": query,
                    "count": len(fallback_results),
                    "results": fallback_results,
                    "fallback": "keyword",
                }
            )

        place_ids = [str(r["place_id"]) for r in ai_results]
        score_map = {str(r["place_id"]): r["score"] for r in ai_results}

        places = (
            Place.objects.filter(id__in=place_ids, status="APPROVED")
            .select_related("category")
            .prefetch_related("tags")
        )

        places_dict = {str(p.id): p for p in places}
        ordered_places = [places_dict[pid] for pid in place_ids if pid in places_dict]

        serializer = PlaceListSerializer(ordered_places, many=True, context={"request": request})
        results = serializer.data

        for item in results:
            item["ai_score"] = round(score_map.get(str(item["id"]), 0), 4)

        logger.info("semantic_search query='%s' results=%s", query, len(results))
        return Response({"query": query, "count": len(results), "results": results})
