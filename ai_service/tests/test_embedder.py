from __future__ import annotations

import importlib
import os
import unittest
from unittest.mock import Mock, patch

import numpy as np

import ai_service.models.embedder as embedder


class EmbedderRuntimeTests(unittest.TestCase):
    def test_resolve_device_auto_uses_cuda_when_available(self):
        self.assertEqual(embedder.resolve_device(preferred="auto", cuda_available=True), "cuda")

    def test_resolve_device_auto_uses_cpu_when_cuda_unavailable(self):
        self.assertEqual(embedder.resolve_device(preferred="auto", cuda_available=False), "cpu")

    def test_resolve_device_cuda_requires_cuda(self):
        with self.assertRaises(RuntimeError):
            embedder.resolve_device(preferred="cuda", cuda_available=False)

    def test_runtime_info_contains_expected_fields(self):
        with patch.dict(
            os.environ,
            {"AI_DEVICE": "cpu", "SBERT_MODEL": "test-model", "VECTOR_DIMENSION": "3"},
            clear=False,
        ):
            module = importlib.reload(embedder)
            runtime = module.get_runtime_info()
        importlib.reload(embedder)

        self.assertEqual(runtime["device"], "cpu")
        self.assertEqual(runtime["model_name"], "test-model")
        self.assertIn("torch_version", runtime)
        self.assertIn("cuda_available", runtime)
        self.assertEqual(runtime["vector_dimension"], 3)

    def test_ensure_model_loaded_uses_selected_device(self):
        fake_model = Mock()
        fake_model.encode.return_value = np.array([1.0, 2.0, 3.0], dtype=np.float32)

        with patch.object(embedder, "SentenceTransformer", return_value=fake_model) as ctor:
            with patch.object(
                embedder,
                "get_runtime_info",
                return_value={
                    "device": "cpu",
                    "model_name": "mock-model",
                    "torch_version": "test",
                    "cuda_available": False,
                    "gpu_name": None,
                    "requested_device": "cpu",
                    "vector_dimension": 768,
                },
            ):
                model = embedder.ensure_model_loaded(force_reload=True)

        self.assertIs(model, fake_model)
        ctor.assert_called_once_with(embedder.MODEL_NAME, device="cpu")


if __name__ == "__main__":
    unittest.main()
