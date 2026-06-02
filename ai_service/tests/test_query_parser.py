from __future__ import annotations

import unittest

from ai_service.query_parser import _fallback_parser


class QueryParserTests(unittest.TestCase):
    def test_fallback_normalizes_category_and_semantic_text(self):
        parsed = _fallback_parser("quan cafe yen tinh gan bien")

        self.assertEqual(parsed["category"], "Cafe")
        self.assertEqual(parsed["location_anchor"], "bien")
        self.assertEqual(parsed["location_type"], "area")
        self.assertEqual(parsed["distance_rule"], {"operator": "<", "value": 5})
        self.assertEqual(parsed["semantic_text"], "yen tinh")

    def test_fallback_handles_near_me_queries(self):
        parsed = _fallback_parser("dia diem vui choi cho tre em gan toi")

        self.assertEqual(parsed["category"], "Vui choi")
        self.assertIsNone(parsed["location_anchor"])
        self.assertIsNone(parsed["location_type"])
        self.assertEqual(parsed["distance_rule"], {"operator": "<", "value": 3})
        self.assertEqual(parsed["semantic_text"], "tre em")

    def test_fallback_infers_point_location_type(self):
        parsed = _fallback_parser("quan cafe view dep gan song han")

        self.assertEqual(parsed["location_anchor"], "song han")
        self.assertEqual(parsed["location_type"], "point")

    def test_fallback_extracts_area_anchor_from_query(self):
        parsed = _fallback_parser("co quan nuong nao ngon o quan lien chieu khong")

        self.assertEqual(parsed["category"], "Quan an")
        self.assertEqual(parsed["location_anchor"], "quan lien chieu")
        self.assertEqual(parsed["location_type"], "area")


if __name__ == "__main__":
    unittest.main()
