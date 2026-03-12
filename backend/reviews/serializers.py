from rest_framework import serializers
from .models import Review, Image


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'image_path']


class ReviewSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'reviewer_name', 'rating', 'content', 'sentiment_score', 'images', 'created_at']

    def get_reviewer_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['place', 'rating', 'content']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)
