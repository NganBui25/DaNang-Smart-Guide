import requests
from django.conf import settings
from django.db.models import Q
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Place, Category, Tag, Bookmark
from .serializers import (
    PlaceListSerializer, PlaceDetailSerializer,
    PlaceSubmitSerializer, TagSerializer, CategorySerializer,
    BookmarkSerializer
)
from reviews.serializers import ReviewSerializer

AI_SERVICE_URL = getattr(settings, 'AI_SERVICE_URL', 'http://localhost:8000')


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class PlaceViewSet(viewsets.ModelViewSet):
    """
    API endpoint để xem và submit địa điểm.
    - GET  /api/places/          - Danh sách địa điểm APPROVED
    - GET  /api/places/{id}/     - Chi tiết địa điểm
    - POST /api/places/          - Crowdsourcing: submit địa điểm mới (→ PENDING)
    - GET  /api/places/{id}/reviews/ - Danh sách reviews của địa điểm
    """
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'address', 'description']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        qs = Place.objects.filter(status='APPROVED').select_related('category').prefetch_related('tags')

        # Filter theo category
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category__name__icontains=category)

        # Filter chỉ hidden gem
        is_hidden = self.request.query_params.get('hidden_gem')
        if is_hidden == '1':
            qs = qs.filter(is_hidden_gem=True)

        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return PlaceListSerializer
        if self.action == 'create':
            return PlaceSubmitSerializer
        return PlaceDetailSerializer

    @action(detail=True, methods=['get'], url_path='reviews')
    def reviews(self, request, pk=None):
        """GET /api/places/{id}/reviews/ - Lấy reviews của địa điểm"""
        place = self.get_object()
        reviews = place.reviews.select_related('user').prefetch_related('images')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='bookmark')
    def bookmark(self, request, pk=None):
        """POST /api/places/{id}/bookmark/ - Toggle bookmark địa điểm"""
        if not request.user.is_authenticated:
            return Response({'error': 'Cần đăng nhập'}, status=status.HTTP_401_UNAUTHORIZED)
        place = self.get_object()
        bookmark, created = Bookmark.objects.get_or_create(user=request.user, place=place)
        if not created:
            bookmark.delete()
            return Response({'bookmarked': False})
        return Response({'bookmarked': True})


class SearchViewSet(viewsets.ViewSet):
    """
    API Tìm kiếm ngữ nghĩa (Semantic Search) tích hợp AI Service.
    POST /api/search/  - Body: {"query": "quán cà phê chill gần biển", "top_k": 10}
    """

    def create(self, request):
        query = request.data.get('query', '').strip()
        top_k = int(request.data.get('top_k', 10))

        if not query:
            return Response({'error': 'Vui lòng nhập từ khoá tìm kiếm'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Gọi AI Service để tìm place_ids gần nhất theo vector
        try:
            ai_response = requests.post(
                f"{AI_SERVICE_URL}/search",
                json={"text": query, "top_k": top_k},
                timeout=10
            )
            ai_response.raise_for_status()
            ai_results = ai_response.json().get('results', [])
        except requests.exceptions.RequestException as e:
            return Response(
                {'error': f'AI Service không phản hồi: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if not ai_results:
            return Response({'query': query, 'results': []})

        # 2. Lấy danh sách place_ids từ FAISS (sắp xếp theo score)
        place_ids = [r['place_id'] for r in ai_results]
        score_map = {r['place_id']: r['score'] for r in ai_results}

        # 3. Truy vấn MySQL để lấy thông tin chi tiết của các địa điểm
        places = Place.objects.filter(
            id__in=place_ids,
            status='APPROVED'
        ).select_related('category').prefetch_related('tags')

        # 4. Sắp xếp lại theo thứ tự score FAISS (score nhỏ = gần hơn = tốt hơn)
        places_dict = {p.id: p for p in places}
        ordered_places = [places_dict[pid] for pid in place_ids if pid in places_dict]

        serializer = PlaceListSerializer(ordered_places, many=True)
        results = serializer.data

        # Gắn thêm AI score vào response để frontend có thể dùng nếu cần
        for i, item in enumerate(results):
            item['ai_score'] = round(score_map.get(item['id'], 0), 4)

        return Response({'query': query, 'count': len(results), 'results': results})
