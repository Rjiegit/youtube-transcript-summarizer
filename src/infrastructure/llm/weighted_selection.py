from __future__ import annotations

from collections.abc import Iterable, Set
from numbers import Real
from typing import Protocol

from src.infrastructure.llm.model_options import Backend, ModelCandidate


class _RandomLike(Protocol):
    def random(self) -> float:  # returns [0.0, 1.0)
        ...


class InvalidModelPoolError(ValueError):
    """Raised when the code-defined auto model pool is invalid."""


class NoAvailableModelCandidateError(ValueError):
    """Raised when no configured candidate can use available credentials."""


def validate_model_candidates(
    candidates: Iterable[ModelCandidate],
) -> tuple[ModelCandidate, ...]:
    configured = tuple(candidates)
    if not configured:
        raise InvalidModelPoolError(
            "Auto model candidate pool cannot be empty"
        )

    seen: set[tuple[Backend, str]] = set()
    for candidate in configured:
        if not isinstance(candidate.backend, Backend):
            raise InvalidModelPoolError(
                f"Unknown model backend: {candidate.backend!r}"
            )
        if not candidate.model.strip():
            raise InvalidModelPoolError("Model name cannot be empty")
        if (
            isinstance(candidate.weight, bool)
            or not isinstance(candidate.weight, Real)
            or candidate.weight <= 0
        ):
            raise InvalidModelPoolError(
                f"Weight must be positive for "
                f"{candidate.backend.value}:{candidate.model}"
            )
        if candidate.key in seen:
            raise InvalidModelPoolError(
                f"Duplicate auto model candidate: "
                f"{candidate.backend.value}:{candidate.model}"
            )
        seen.add(candidate.key)

    return configured


def choose_weighted_candidate(
    candidates: Iterable[ModelCandidate],
    *,
    available_backends: Set[Backend],
    rng: _RandomLike,
    excluded: Set[tuple[Backend, str]] | None = None,
) -> ModelCandidate:
    configured = validate_model_candidates(candidates)
    excluded_keys = excluded or set()
    eligible = [
        candidate
        for candidate in configured
        if candidate.backend in available_backends
        and candidate.key not in excluded_keys
    ]
    if not eligible:
        available = ", ".join(
            sorted(backend.value for backend in available_backends)
        ) or "none"
        configured_labels = ", ".join(
            f"{candidate.backend.value}:{candidate.model}"
            for candidate in configured
        )
        raise NoAvailableModelCandidateError(
            "No auto model candidate is eligible "
            f"(available providers: {available}; "
            f"configured candidates: {configured_labels})"
        )

    total_weight = sum(candidate.weight for candidate in eligible)
    pick = rng.random() * total_weight
    running = 0.0
    for candidate in eligible:
        running += candidate.weight
        if pick < running:
            return candidate

    return eligible[-1]
