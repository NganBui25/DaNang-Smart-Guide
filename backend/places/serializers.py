import re
from rest_framework import serializers
from .models import Place, Category, Tag, Bookmark, PlaceImage


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class PlaceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceImage
        fields = ['id', 'image_url', 'caption', 'is_primary']


class PlaceListSerializer(serializers.ModelSerializer):
    """Serializer nhẹ dùng cho danh sách và kết quả tìm kiếm"""
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = [
            'id', 'name', 'address', 'lat', 'lng',
            'category', 'tags', 'is_hidden_gem', 'status',
            'primary_image', 'avg_rating',
        ]

    def get_primary_image(self, obj):
        img = obj.images.filter(is_primary=True).first() or obj.images.first()
        return img.image_url if img else None

    def get_avg_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews.exists():
            return None
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)


class PlaceDetailSerializer(serializers.ModelSerializer):
    """Serializer đầy đủ dùng cho trang chi tiết"""
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    images = PlaceImageSerializer(many=True, read_only=True)
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    submitted_by_username = serializers.SerializerMethodField()

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tags', many=True, write_only=True, required=False
    )

    class Meta:
        model = Place
        fields = [
            'id', 'name', 'description', 'address', 'lat', 'lng',
            'category', 'category_id', 'tags', 'tag_ids', 'images',
            'is_hidden_gem', 'status', 'ai_sentiment_summary',
            'submitted_by_username', 'avg_rating', 'review_count',
            'created_at', 'updated_at',
        ]

    def get_avg_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews.exists():
            return None
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)

    def get_review_count(self, obj):
        return obj.reviews.count()

    def get_submitted_by_username(self, obj):
        return obj.submitted_by.username if obj.submitted_by else None


class PlaceSubmitSerializer(serializers.ModelSerializer):
    """Dùng khi user crowdsource đóng góp địa điểm"""
    name = serializers.CharField(required=True, max_length=255)
    address = serializers.CharField(required=True, max_length=255)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tags', many=True, required=False
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', required=False, allow_null=True
    )

    class Meta:
        model = Place
        fields = ['name', 'description', 'address', 'lat', 'lng', 'category_id', 'tag_ids']

    def validate_description(self, value: str):
        if value:
            value = re.sub(r'<[^>]+>', '', value).strip()
        return value

    def validate(self, attrs):
        if not attrs.get('name', '').strip():
            raise serializers.ValidationError({'name': 'Tên địa điểm là bắt buộc.'})
        if not attrs.get('address', '').strip():
            raise serializers.ValidationError({'address': 'Địa chỉ là bắt buộc.'})
        return attrs

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        validated_data['status'] = 'PENDING'
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['submitted_by'] = request.user
        place = super().create(validated_data)
        if tags:
            place.tags.set(tags)
        return place


class BookmarkSerializer(serializers.ModelSerializer):
    place = PlaceListSerializer(read_only=True)

    class Meta:
        model = Bookmark
        fields = ['id', 'place', 'created_at']
