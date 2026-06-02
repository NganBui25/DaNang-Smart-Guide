import logging
import re
import unicodedata

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
WORD_PATTERN = re.compile(r"\w+", re.UNICODE)


def _normalize_text(value):
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower().strip()


def _tokenize(value):
    return [_normalize_text(token) for token in WORD_PATTERN.findall(value or "")]


def _canonicalize_place_name(name):
    primary_name = re.split(r"\s+-\s+", str(name or ""), maxsplit=1)[0]
    normalized = _normalize_text(primary_name)
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _dedupe_serialized_results(results):
    seen = set()
    deduped = []
    for item in results:
        key = _canonicalize_place_name(item.get("name"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


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
        reviews = place.reviews.select_related("user").order_by("-created_at")
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

    def _keyword_fallback(self, query, top_k, request, parsed_intent=None):
        parsed_intent = parsed_intent or {}
        semantic_query = (parsed_intent.get("semantic_text") or query).strip()
        keywords = [w for w in _tokenize(semantic_query) if len(w) >= 2][:8]
        category = (parsed_intent.get("category") or "").strip()

        if not keywords and not category:
            return []

        candidate_filter = Q()
        for kw in keywords:
            candidate_filter |= (
                Q(name__icontains=kw)
                | Q(address__icontains=kw)
                | Q(description__icontains=kw)
            )

        places = (
            Place.objects.filter(status="APPROVED")
            .select_related("category")
            .prefetch_related("tags")
            .distinct()
        )
        if category:
            places = places.filter(category__name__iexact=category)
        if candidate_filter:
            places = places.filter(candidate_filter)

        candidate_places = list(places[: max(top_k * 8, 24)])
        if not candidate_places and category:
            candidate_places = list(
                Place.objects.filter(status="APPROVED", category__name__iexact=category)
                .select_related("category")
                .prefetch_related("tags")
                .distinct()[: max(top_k * 8, 24)]
            )
        if not candidate_places:
            return []

        def rank_place(place):
            score = 0
            category_name = _normalize_text(place.category.name if place.category else "")
            name_text = _normalize_text(place.name)
            address_text = _normalize_text(place.address)
            description_text = _normalize_text(place.description)
            semantic_text = _normalize_text(semantic_query)

            if category and category_name == _normalize_text(category):
                score += 6

            if semantic_text:
                if semantic_text and semantic_text in description_text:
                    score += 5
                elif semantic_text and semantic_text in name_text:
                    score += 4

            for kw in keywords:
                if kw in name_text:
                    score += 4
                if kw in description_text:
                    score += 3
                if kw in address_text:
                    score += 1

            return score

        ranked_places = sorted(
            candidate_places,
            key=lambda place: (
                -rank_place(place),
                place.name.lower(),
            ),
        )

        serializer = PlaceListSerializer(ranked_places[: max(top_k * 2, top_k)], many=True, context={"request": request})
        results = serializer.data
        score_lookup = {str(place.id): rank_place(place) for place in ranked_places}

        for item in results:
            item["ai_score"] = float(score_lookup.get(str(item["id"]), 0))
            item["match_reason"] = "keyword_fallback"
        return _dedupe_serialized_results(results)[:top_k]

    def create(self, request):
        query = request.data.get("query", "").strip()
        top_k = int(request.data.get("top_k", 10))
        user_lat = request.data.get("user_lat")
        user_lng = request.data.get("user_lng")
        if not query:
            return Response({"error": "Vui long nhap tu khoa tim kiem"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ai_payload = {
                "text": query, 
                "top_k": top_k,
                "user_lat": user_lat,
                "user_lng": user_lng
            }
            ai_response = requests.post(
                f"{AI_SERVICE_URL}/search",
                json=ai_payload,
                timeout=10,
            )
            ai_response.raise_for_status()
            
            ai_data = ai_response.json()
            ai_results = ai_data.get("results", [])
            parsed_intent = ai_data.get("parsed_intent", {})
        except requests.exceptions.RequestException as e:
            logger.exception("AI Service unreachable for query='%s'", query)
            return Response(
                {"error": f"AI Service khong phan hoi: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not ai_results:
            fallback_results = self._keyword_fallback(
                query,
                top_k,
                request,
                parsed_intent if "parsed_intent" in locals() else None,
            )
            return Response(
                {
                    "query": query,
                    "count": len(fallback_results),
                    "results": fallback_results,
                    "fallback": "keyword",
                    "parsed_intent": parsed_intent if 'parsed_intent' in locals() else None
                }
            )

        place_ids = [str(r["place_id"]) for r in ai_results]
        score_map = {str(r["place_id"]): r["score"] for r in ai_results}
        reason_map = {str(r["place_id"]): r.get("match_reason", "") for r in ai_results}
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
            item["match_reason"] = reason_map.get(str(item["id"]), "")
        results = _dedupe_serialized_results(results)
        logger.info("semantic_search query='%s' results=%s", query, len(results))
        return Response({"query": query, "count": len(results),"parsed_intent": parsed_intent, "results": results})
