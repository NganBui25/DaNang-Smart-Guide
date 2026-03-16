from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()
    reviewer_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'reviewer_name', 'reviewer_avatar',
            'rating', 'comment', 'sentiment_score', 'created_at',
        ]

    def get_reviewer_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_reviewer_avatar(self, obj):
        return getattr(obj.user, 'avatar', None)


class ReviewCreateSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=2000)

    class Meta:
        model = Review
        fields = ['place', 'rating', 'comment']

    def validate_comment(self, value: str):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Nội dung là bắt buộc.')
        return cleaned

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)
