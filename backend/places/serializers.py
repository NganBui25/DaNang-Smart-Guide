from rest_framework import serializers
from .models import Place, Category, Tag, Bookmark


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class PlaceListSerializer(serializers.ModelSerializer):
    """Serializer nhẹ dùng cho danh sách (không kèm reviews đầy đủ)"""
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Place
        fields = [
            'id', 'name', 'address', 'lat', 'lng',
            'category', 'tags', 'is_hidden_gem', 'status',
        ]


class PlaceDetailSerializer(serializers.ModelSerializer):
    """Serializer đầy đủ dùng cho trang chi tiết"""
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
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
            'category', 'category_id', 'tags', 'tag_ids',
            'is_hidden_gem', 'status', 'created_at', 'updated_at',
        ]


class PlaceSubmitSerializer(serializers.ModelSerializer):
    """Serializer cho Crowdsourcing - người dùng submit địa điểm mới"""
    class Meta:
        model = Place
        fields = ['name', 'description', 'address', 'lat', 'lng']

    def create(self, validated_data):
        # Mọi địa điểm mới đều ở trạng thái PENDING chờ admin duyệt
        validated_data['status'] = 'PENDING'
        return super().create(validated_data)


class BookmarkSerializer(serializers.ModelSerializer):
    place = PlaceListSerializer(read_only=True)

    class Meta:
        model = Bookmark
        fields = ['id', 'place', 'created_at']
