from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from ai_service import main


class GeocodingStrategyTests(unittest.TestCase):
    def test_build_area_like_clause_uses_meaningful_tokens(self):
        clause, params = main._build_area_like_clause("quan lien chieu")

        self.assertEqual(
            clause,
            "(p.address LIKE %s OR p.name LIKE %s) AND (p.address LIKE %s OR p.name LIKE %s)",
        )
        self.assertEqual(params, ["%lien%", "%lien%", "%chieu%", "%chieu%"])

    @patch.object(main, "get_coordinates")
    def test_area_anchor_without_distance_prefers_like_search(self, mock_get_coordinates):
        cursor = Mock()

        target_lat, target_lng, use_like_search = main._resolve_anchor_search_strategy(
            cursor,
            "quan lien chieu",
            "area",
            None,
            None,
            None,
        )

        self.assertIsNone(target_lat)
        self.assertIsNone(target_lng)
        self.assertTrue(use_like_search)
        mock_get_coordinates.assert_not_called()

    @patch.object(main, "_lookup_anchor_coordinates_in_db")
    @patch.object(main, "get_coordinates")
    def test_point_anchor_uses_geocoding_before_database_lookup(self, mock_get_coordinates, mock_lookup_anchor):
        cursor = Mock()
        mock_get_coordinates.return_value = (16.061, 108.224)

        target_lat, target_lng, use_like_search = main._resolve_anchor_search_strategy(
            cursor,
            "cau rong",
            "point",
            {"operator": "<", "value": 3},
            None,
            None,
        )

        self.assertEqual((target_lat, target_lng), (16.061, 108.224))
        self.assertFalse(use_like_search)
        mock_lookup_anchor.assert_not_called()

    @patch.object(main, "_lookup_anchor_coordinates_in_db")
    @patch.object(main, "get_coordinates")
    def test_anchor_falls_back_to_database_lookup_when_geocoding_misses(self, mock_get_coordinates, mock_lookup_anchor):
        cursor = Mock()
        mock_get_coordinates.return_value = (None, None)
        mock_lookup_anchor.return_value = (16.07, 108.18)

        target_lat, target_lng, use_like_search = main._resolve_anchor_search_strategy(
            cursor,
            "song han",
            "point",
            {"operator": "<", "value": 3},
            None,
            None,
        )

        self.assertEqual((target_lat, target_lng), (16.07, 108.18))
        self.assertFalse(use_like_search)
        mock_lookup_anchor.assert_called_once_with(cursor, "song han")


if __name__ == "__main__":
    unittest.main()
