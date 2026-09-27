import unittest

from whisper_summary.infrastructure.llm.model_options import (
    AUTO_MODEL_CANDIDATES,
    Backend,
    CODEX_CLI_WEIGHT,
    ModelCandidate,
)
from whisper_summary.infrastructure.llm.weighted_selection import (
    InvalidModelPoolError,
    NoAvailableModelCandidateError,
    choose_weighted_candidate,
    validate_model_candidates,
)


class _FixedRng:
    def __init__(self, values):
        self._values = list(values)
        self._idx = 0

    def random(self) -> float:
        value = self._values[self._idx]
        self._idx = min(self._idx + 1, len(self._values) - 1)
        return value


class TestWeightedSelection(unittest.TestCase):
    def setUp(self):
        self.candidates = [
            ModelCandidate(Backend.GEMINI, "gemini-a", 5),
            ModelCandidate(Backend.OPENAI, "openai-a", 5),
            ModelCandidate(Backend.OLLAMA, "ollama-a", 10),
        ]

    def test_choose_weighted_candidate_is_deterministic(self):
        rng = _FixedRng([0.0, 0.26, 0.8])
        available = set(Backend)

        self.assertEqual(
            choose_weighted_candidate(
                self.candidates,
                available_backends=available,
                rng=rng,
            ),
            self.candidates[0],
        )
        self.assertEqual(
            choose_weighted_candidate(
                self.candidates,
                available_backends=available,
                rng=rng,
            ),
            self.candidates[1],
        )
        self.assertEqual(
            choose_weighted_candidate(
                self.candidates,
                available_backends=available,
                rng=rng,
            ),
            self.candidates[2],
        )

    def test_auto_model_candidates_match_percentage_budget(self):
        self.assertEqual(
            AUTO_MODEL_CANDIDATES,
            (
                ModelCandidate(Backend.GEMINI, "gemini-3.7-flash", 0.91),
                ModelCandidate(
                    Backend.GEMINI,
                    "gemini-2.5-flash-lite",
                    1.82,
                ),
                ModelCandidate(Backend.GEMINI, "gemini-2.5-flash", 0.91),
                ModelCandidate(
                    Backend.GEMINI,
                    "gemini-3-flash-preview",
                    0.91,
                ),
                ModelCandidate(
                    Backend.GEMINI,
                    "gemini-3.1-flash-lite",
                    2.73,
                ),
                ModelCandidate(
                    Backend.GEMINI,
                    "gemini-3.5-flash-lite",
                    2.72,
                ),
                ModelCandidate(
                    Backend.CODEX_CLI,
                    "gpt-6-luna",
                    CODEX_CLI_WEIGHT,
                ),
            ),
        )

    def test_codex_cli_receives_ninety_percent_of_auto_pool(self):
        total_weight = sum(
            candidate.weight for candidate in AUTO_MODEL_CANDIDATES
        )
        codex_candidate = next(
            candidate
            for candidate in AUTO_MODEL_CANDIDATES
            if candidate.backend == Backend.CODEX_CLI
        )

        self.assertAlmostEqual(
            codex_candidate.weight / total_weight,
            0.90,
        )
        self.assertAlmostEqual(total_weight, 100)
        self.assertAlmostEqual(total_weight - codex_candidate.weight, 10)

    def test_filters_unavailable_backends_and_recalculates_weights(self):
        selected = choose_weighted_candidate(
            self.candidates,
            available_backends={Backend.OPENAI, Backend.OLLAMA},
            rng=_FixedRng([0.2]),
        )

        self.assertEqual(selected, self.candidates[1])

    def test_excludes_a_previous_candidate_before_retry(self):
        selected = choose_weighted_candidate(
            self.candidates,
            available_backends=set(Backend),
            excluded={self.candidates[0].key},
            rng=_FixedRng([0.0]),
        )

        self.assertEqual(selected, self.candidates[1])

    def test_rejects_invalid_model_pool(self):
        invalid_pools = [
            [],
            [
                ModelCandidate(
                    "unknown",  # type: ignore[arg-type]
                    "model-a",
                    1,
                )
            ],
            [ModelCandidate(Backend.GEMINI, "", 1)],
            [
                ModelCandidate(
                    Backend.GEMINI,
                    "gemini-a",
                    "heavy",  # type: ignore[arg-type]
                )
            ],
            [ModelCandidate(Backend.GEMINI, "gemini-a", 0)],
            [ModelCandidate(Backend.GEMINI, "gemini-a", -1)],
            [
                ModelCandidate(Backend.GEMINI, "gemini-a", 1),
                ModelCandidate(Backend.GEMINI, "gemini-a", 2),
            ],
        ]

        for candidates in invalid_pools:
            with self.subTest(candidates=candidates):
                with self.assertRaises(InvalidModelPoolError):
                    validate_model_candidates(candidates)

    def test_rejects_pool_without_eligible_candidates(self):
        with self.assertRaisesRegex(
            NoAvailableModelCandidateError,
            "openai",
        ):
            choose_weighted_candidate(
                self.candidates[:1],
                available_backends={Backend.OPENAI},
                rng=_FixedRng([0.0]),
            )


if __name__ == "__main__":
    unittest.main()
