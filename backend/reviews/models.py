from django.db import models
from users.models import User
from places.models import Place


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="Điểm đánh giá từ 1 đến 5 sao"
    )
    comment = models.TextField(help_text="Nội dung đánh giá")
    sentiment_score = models.FloatField(null=True, blank=True, help_text="Điểm cảm xúc AI (-1 đến 1)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews_review'
        unique_together = ('user', 'place')

    def __str__(self):
        return f"Review by {self.user.username} for {self.place.name} ({self.rating}★)"
