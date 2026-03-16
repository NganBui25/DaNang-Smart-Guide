import uuid
from django.db import models
from users.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        db_table = 'places_category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'places_tag'

    def __str__(self):
        return self.name


class Place(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='places'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='places')

    is_hidden_gem = models.BooleanField(default=False, help_text="Địa điểm bản địa ít người biết")
    status = models.CharField(max_length=20, default='PENDING', choices=STATUS_CHOICES)

    # Crowdsourcing
    submitted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='submitted_places', help_text="Người đóng góp địa điểm"
    )

    # AI fields
    embedding_vector = models.JSONField(
        null=True, blank=True,
        help_text="Vector ngữ nghĩa (768 chiều từ PhoBERT/MiniLM)"
    )
    ai_sentiment_summary = models.TextField(
        null=True, blank=True,
        help_text="Tóm tắt cảm xúc từ reviews do AI tạo ra"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'places_place'

    def __str__(self):
        return self.name


class PlaceImage(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='images')
    image_url = models.CharField(max_length=500)
    caption = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False, help_text="Ảnh bìa thumbnail")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'places_image'

    def __str__(self):
        return f"Image for {self.place.name} ({'primary' if self.is_primary else 'secondary'})"


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_bookmark'
        unique_together = ('user', 'place')

    def __str__(self):
        return f"{self.user.username} → {self.place.name}"
