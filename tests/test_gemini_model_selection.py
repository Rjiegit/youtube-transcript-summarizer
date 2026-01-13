import unittest

from src.infrastructure.llm.gemini_model_selection import (
    WeightedModel,
    choose_weighted_model,
)


class _FixedRng:
    def __init__(self, values):
        self._values = list(values)
        self._idx = 0

    def random(self) -> float:
        value = self._values[self._idx]
        self._idx = min(self._idx + 1, len(self._values) - 1)
        return value


class TestGeminiModelSelection(unittest.TestCase):
    def test_choose_weighted_model_deterministic(self):
        candidates = [
            WeightedModel("a", 5),
            WeightedModel("b", 5),
            WeightedModel("c", 10),
        ]

        rng = _FixedRng([0.0, 0.26, 0.8])
        self.assertEqual(choose_weighted_model(candidates, rng=rng), "a")
        self.assertEqual(choose_weighted_model(candidates, rng=rng), "b")
        self.assertEqual(choose_weighted_model(candidates, rng=rng), "c")

    def test_choose_weighted_model_rejects_empty(self):
        with self.assertRaises(ValueError):
            choose_weighted_model([], rng=_FixedRng([0.5]))
