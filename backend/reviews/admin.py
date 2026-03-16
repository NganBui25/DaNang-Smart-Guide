from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'place', 'rating', 'sentiment_score', 'created_at']
    list_filter = ['rating']
    search_fields = ['comment', 'user__username', 'place__name']
    readonly_fields = ['created_at', 'sentiment_score']

    actions = ['delete_selected_reviews']
