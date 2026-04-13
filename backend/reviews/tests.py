from unittest.mock import MagicMock, patch

import requests
from django.conf import settings
from django.test import RequestFactory, TestCase

from places.models import Place
from users.models import User

from .models import Review
from .serializers import ReviewCreateSerializer
from .signals import SENTIMENT_TIMEOUT_SECONDS


class ReviewSignalTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.place = Place.objects.create(name="Test Place", status="PENDING")
        self.user_index = 0

    def _create_user(self):
        self.user_index += 1
        return User.objects.create_user(
            username=f"reviewer{self.user_index}",
            email=f"reviewer{self.user_index}@example.com",
            password="password123",
        )

    @patch("reviews.signals.requests.post")
    def test_creating_review_updates_place_sentiment_summary(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"summary": "Da so danh gia tich cuc."}
        mock_post.return_value = mock_response

        Review.objects.create(
            user=self._create_user(),
            place=self.place,
            rating=5,
            comment="Khong gian yen tinh",
        )

        self.place.refresh_from_db()
        self.assertEqual(self.place.ai_sentiment_summary, "Da so danh gia tich cuc.")

        mock_post.assert_called_once()
        self.assertEqual(
            mock_post.call_args.args[0],
            f"{settings.AI_SERVICE_URL}/sentiment",
        )
        self.assertEqual(
            mock_post.call_args.kwargs["json"],
            {"reviews": ["Khong gian yen tinh"]},
        )
        self.assertEqual(
            mock_post.call_args.kwargs["timeout"],
            SENTIMENT_TIMEOUT_SECONDS,
        )

    @patch("reviews.signals.requests.post")
    def test_signal_only_sends_latest_50_review_comments(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"summary": "Updated summary"}
        mock_post.return_value = mock_response

        for idx in range(50):
            Review.objects.create(
                user=self._create_user(),
                place=self.place,
                rating=4,
                comment=f"comment {idx}",
            )

        mock_post.reset_mock()

        Review.objects.create(
            user=self._create_user(),
            place=self.place,
            rating=5,
            comment="latest comment",
        )

        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(len(payload["reviews"]), 50)
        self.assertIn("latest comment", payload["reviews"])
        self.assertNotIn("comment 0", payload["reviews"])

    @patch("reviews.signals.requests.post", side_effect=requests.exceptions.Timeout("AI timeout"))
    def test_ai_errors_do_not_block_review_creation(self, mock_post):
        review = Review.objects.create(
            user=self._create_user(),
            place=self.place,
            rating=3,
            comment="On nhung hoi dong",
        )

        self.assertTrue(Review.objects.filter(pk=review.pk).exists())
        self.place.refresh_from_db()
        self.assertIsNone(self.place.ai_sentiment_summary)
        mock_post.assert_called_once()

    @patch("reviews.signals.requests.post")
    def test_updating_existing_review_does_not_call_ai_again(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"summary": "Initial summary"}
        mock_post.return_value = mock_response

        review = Review.objects.create(
            user=self._create_user(),
            place=self.place,
            rating=4,
            comment="Lan dau",
        )

        mock_post.reset_mock()
        review.comment = "Da cap nhat"
        review.save()

        mock_post.assert_not_called()

    @patch("reviews.signals.requests.post")
    def test_serializer_trims_comment_before_signal_payload(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"summary": "Trimmed summary"}
        mock_post.return_value = mock_response

        request = self.factory.post("/api/reviews/")
        request.user = self._create_user()
        serializer = ReviewCreateSerializer(
            data={
                "place": self.place.pk,
                "rating": 5,
                "comment": "  rat dang thu  ",
            },
            context={"request": request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        review = serializer.save()

        self.assertEqual(review.comment, "rat dang thu")
        self.assertEqual(
            mock_post.call_args.kwargs["json"],
            {"reviews": ["rat dang thu"]},
        )
