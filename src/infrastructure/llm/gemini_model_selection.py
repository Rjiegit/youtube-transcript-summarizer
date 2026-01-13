from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol


class _RandomLike(Protocol):
    def random(self) -> float:  # returns [0.0, 1.0)
        ...


@dataclass(frozen=True)
class WeightedModel:
    model: str
    weight: int

def choose_weighted_model(
    candidates: Iterable[WeightedModel],
    *,
    rng: _RandomLike,
) -> str:
    weighted = list(candidates)
    if not weighted:
        raise ValueError("No weighted model candidates provided")

    total_weight = sum(item.weight for item in weighted)
    if total_weight <= 0:
        raise ValueError("Total weight must be positive")

    pick = rng.random() * total_weight
    running = 0.0
    for item in weighted:
        running += item.weight
        if pick < running:
            return item.model

    # Floating point edge case: fall back to last item.
    return weighted[-1].model
