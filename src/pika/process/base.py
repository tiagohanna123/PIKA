"""Process abstractions for local transformations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pika.core.point import Point


class Process(Protocol):
    """Interface for local transformations acting on a point.

    A process inspects local state and returns the energy delta it
    induces per time step. Sign indicates entropy (negative) or
    syntropy (positive) following the dE/dt criterion.
    """

    def energy_delta(self, point: Point, dt: float) -> float:  # pragma: no cover - protocol
        ...


@dataclass
class LinearEnergyProcess:
    """Simple process applying a constant energy slope.

    This provides a baseline implementation to validate flow plumbing
    without constraining future non-linear processes.
    """

    slope: float

    def energy_delta(self, point: Point, dt: float) -> float:
        return self.slope * dt
