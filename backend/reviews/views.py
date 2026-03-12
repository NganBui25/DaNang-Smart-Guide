from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Review
from .serializers import ReviewSerializer, ReviewCreateSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint để quản lý đánh giá.
    - POST /api/reviews/     - Tạo review mới
    - GET  /api/reviews/{id}/ - Xem review
    """
    queryset = Review.objects.select_related('user', 'place').prefetch_related('images')

    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Cần đăng nhập để đánh giá'}, status=status.HTTP_401_UNAUTHORIZED)
        return super().create(request, *args, **kwargs)
