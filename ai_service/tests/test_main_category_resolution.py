from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import numpy as np

from ai_service import main


class CategoryResolutionTests(unittest.TestCase):
    @patch.object(main, "compute_similarity_batch")
    @patch.object(main, "encode_text")
    def test_resolve_category_match_returns_best_database_category(self, mock_encode_text, mock_similarity):
        cursor = Mock()
        cursor.fetchall.return_value = [
            {"id": 1, "name": "Cafe"},
            {"id": 2, "name": "Quan an"},
        ]

        mock_encode_text.side_effect = [
            np.asarray([1.0, 0.0], dtype=np.float32),
            np.asarray([0.99, 0.01], dtype=np.float32),
            np.asarray([0.0, 1.0], dtype=np.float32),
        ]
        mock_similarity.return_value = [("1", 0.92)]

        resolved = main._resolve_category_match(cursor, "quan cafe")

        self.assertEqual(resolved, {"id": 1, "name": "Cafe", "score": 0.92})
        cursor.execute.assert_called_once()

    @patch.object(main, "compute_similarity_batch")
    @patch.object(main, "encode_text")
    def test_resolve_category_match_returns_none_when_score_below_threshold(self, mock_encode_text, mock_similarity):
        cursor = Mock()
        cursor.fetchall.return_value = [{"id": 1, "name": "Cafe"}]

        mock_encode_text.side_effect = [
            np.asarray([1.0, 0.0], dtype=np.float32),
            np.asarray([0.9, 0.1], dtype=np.float32),
        ]
        mock_similarity.return_value = [("1", 0.2)]

        resolved = main._resolve_category_match(cursor, "quan cafe")

        self.assertIsNone(resolved)


if __name__ == "__main__":
    unittest.main()
