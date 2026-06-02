from __future__ import annotations

import unittest

from ai_service.query_parser import _fallback_parser


class QueryParserTests(unittest.TestCase):
    def test_fallback_normalizes_category_and_semantic_text(self):
        parsed = _fallback_parser("quan cafe yen tinh gan bien")

        self.assertEqual(parsed["category"], "Cafe")
        self.assertEqual(parsed["location_anchor"], "bien")
        self.assertEqual(parsed["distance_rule"], {"operator": "<", "value": 5})
        self.assertEqual(parsed["semantic_text"], "yen tinh")

    def test_fallback_handles_near_me_queries(self):
        parsed = _fallback_parser("dia diem vui choi cho tre em gan toi")

        self.assertEqual(parsed["category"], "Vui choi")
        self.assertIsNone(parsed["location_anchor"])
        self.assertEqual(parsed["distance_rule"], {"operator": "<", "value": 3})
        self.assertEqual(parsed["semantic_text"], "tre em")


if __name__ == "__main__":
    unittest.main()
