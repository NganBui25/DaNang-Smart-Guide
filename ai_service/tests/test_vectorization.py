from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np

from ai_service import vectorization


class VectorizationTests(unittest.TestCase):
    def test_compute_similarity_faiss_matches_numpy(self):
        query = np.asarray([1.0, 0.0, 0.0], dtype=np.float32)
        vectors = {
            "exact": np.asarray([1.0, 0.0, 0.0], dtype=np.float32),
            "close": np.asarray([0.9, 0.1, 0.0], dtype=np.float32),
            "far": np.asarray([0.0, 1.0, 0.0], dtype=np.float32),
        }

        numpy_results = vectorization.compute_similarity_batch(
            query,
            vectors,
            top_k=3,
            search_backend="numpy",
        )
        faiss_results = vectorization.compute_similarity_batch(
            query,
            vectors,
            top_k=3,
            search_backend="faiss",
        )

        self.assertEqual([item[0] for item in numpy_results], [item[0] for item in faiss_results])
        self.assertEqual(len(numpy_results), len(faiss_results))
        for numpy_item, faiss_item in zip(numpy_results, faiss_results):
            self.assertAlmostEqual(numpy_item[1], faiss_item[1], places=5)

    def test_faiss_backend_falls_back_to_numpy_when_unavailable(self):
        with patch.object(vectorization, "FAISS_AVAILABLE", False):
            self.assertEqual(vectorization.get_search_backend_name("faiss"), "numpy")


if __name__ == "__main__":
    unittest.main()
