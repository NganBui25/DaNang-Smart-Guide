from django.db import models
from users.models import User
from places.models import Place

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='reviews')
    content = models.TextField()
    rating = models.FloatField()
    sentiment_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review by {self.user.username} for {self.place.name}"

class Image(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True, related_name='images')
    place = models.ForeignKey(Place, on_delete=models.CASCADE, null=True, blank=True, related_name='images')
    image_path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
