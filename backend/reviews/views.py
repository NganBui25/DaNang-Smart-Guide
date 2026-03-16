from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Review
from .serializers import ReviewSerializer, ReviewCreateSerializer


class ReviewViewSet(viewsets.ViewSet):
    """
    - GET  /api/reviews/?place={id}   Lấy reviews theo địa điểm
    - POST /api/reviews/              Tạo review mới (cần đăng nhập)
    - DELETE /api/reviews/{id}/       Admin xóa review
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        place_id = request.query_params.get("place")
        if not place_id:
            return Response({"error": "Cần truyền ?place=<id>"}, status=status.HTTP_400_BAD_REQUEST)
        reviews = Review.objects.filter(place_id=place_id).select_related("user").order_by("-created_at")
        return Response(ReviewSerializer(reviews, many=True).data)

    def create(self, request):
        serializer = ReviewCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        try:
            review = Review.objects.get(pk=pk)
        except Review.DoesNotExist:
            return Response({"error": "Review không tồn tại"}, status=status.HTTP_404_NOT_FOUND)
        # Only review owner or admin can delete
        if review.user != request.user and not request.user.is_admin:
            return Response({"error": "Không có quyền xóa review này."}, status=status.HTTP_403_FORBIDDEN)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
