from django.contrib import admin
from .models import Place, Category, Tag, Bookmark, PlaceImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'status', 'is_hidden_gem', 'submitted_by', 'created_at']
    list_filter = ['status', 'is_hidden_gem', 'category']
    search_fields = ['name', 'address', 'description']
    filter_horizontal = ['tags']
    readonly_fields = ['created_at', 'updated_at', 'embedding_vector']
    list_editable = ['status', 'is_hidden_gem']
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'description', 'address', 'lat', 'lng', 'category', 'tags')
        }),
        ('Trạng thái & Gắn cờ', {
            'fields': ('status', 'is_hidden_gem', 'submitted_by')
        }),
        ('AI Engine', {
            'fields': ('ai_sentiment_summary', 'embedding_vector'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['approve_places', 'reject_places']

    @admin.action(description='✅ Duyệt các địa điểm đã chọn')
    def approve_places(self, request, queryset):
        updated = 0
        for place in queryset.filter(status='PENDING'):
            place.status = 'APPROVED'
            place.save()  # Triggers signal for vectorization
            updated += 1
        self.message_user(request, f"Đã duyệt {updated} địa điểm.")

    @admin.action(description='❌ Từ chối các địa điểm đã chọn')
    def reject_places(self, request, queryset):
        count = queryset.filter(status='PENDING').update(status='REJECTED')
        self.message_user(request, f"Đã từ chối {count} địa điểm.")


@admin.register(PlaceImage)
class PlaceImageAdmin(admin.ModelAdmin):
    list_display = ['place', 'is_primary', 'image_url', 'created_at']
    list_filter = ['is_primary']


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'place', 'created_at']
