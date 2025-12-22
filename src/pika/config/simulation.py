"""Simulation configuration defaults.

This module lives under the ``pika.config`` package (not a sibling file)
so that imports like ``from pika.config import SimulationConfig`` work
consistently.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Optional


@dataclass(frozen=True)
class SimulationConfig:
    dt: float
    steps: int
    seed: Optional[int]

    @classmethod
    def from_environment(cls, *, default_dt: float = 0.05, default_steps: int = 200) -> "SimulationConfig":
        dt_env = float(os.getenv("PIKA_DT", default_dt))
        steps_env = int(os.getenv("PIKA_STEPS", default_steps))
        seed_env = os.getenv("PIKA_SEED")
        seed = int(seed_env) if seed_env is not None else None
        return cls(dt=dt_env, steps=steps_env, seed=seed)


def resolve_seed(seed: Optional[int]) -> Optional[int]:
    """Return the seed to use for stochastic components."""

    return seed
