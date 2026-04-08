from unittest.mock import MagicMock, patch

from django.test import TestCase

from .models import Place


class PlaceSignalTests(TestCase):
    @patch("places.signals.requests.post")
    def test_vectorize_payload_is_sanitized_before_request(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"vector": [0.1, 0.2, 0.3]}
        mock_post.return_value = mock_response

        with self.assertLogs("places.signals", level="INFO") as logs:
            place = Place.objects.create(
                name="Cafe Test",
                status="APPROVED",
                address=None,
                description=None,
                category=None,
            )

        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["place_id"], str(place.id))
        self.assertEqual(payload["text"], "Cafe Test")
        self.assertNotIn("None", payload["text"])
        self.assertIn('"text": "Cafe Test"', "\n".join(logs.output))

        place.refresh_from_db()
        self.assertEqual(place.embedding_vector, [0.1, 0.2, 0.3])
