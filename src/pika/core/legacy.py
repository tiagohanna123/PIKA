"""Legacy core primitives: points and system container.

The repository contains both a newer modular layer under subpackages and a
legacy "flat" API used by the original tests and preview scripts.

This module hosts the legacy types so that imports like
``from pika.core import System`` resolve reliably.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np


@dataclass
class Point:
    """Smallest distinguishable unit of state (legacy engine).

    Each point holds position, velocity, and internal energy.
    """

    position: np.ndarray
    velocity: np.ndarray
    internal_energy: float = 0.0
    id: int = 0

    def kinetic_energy(self) -> float:
        return 0.5 * float(np.dot(self.velocity, self.velocity))

    def total_energy(self) -> float:
        return self.kinetic_energy() + self.internal_energy

    def apply_velocity_change(self, delta_v: np.ndarray) -> None:
        self.velocity = self.velocity + delta_v

    def apply_energy_change(self, delta_e: float) -> None:
        self.internal_energy += delta_e


@dataclass
class System:
    """Collection of points evolving in shared space (legacy engine)."""

    dimension: int
    points: List[Point] = field(default_factory=list)

    def add_point(self, position: np.ndarray, velocity: np.ndarray, *, energy: float = 0.0) -> Point:
        pid = len(self.points)
        point = Point(
            position=np.array(position, dtype=float),
            velocity=np.array(velocity, dtype=float),
            internal_energy=float(energy),
            id=pid,
        )
        self.points.append(point)
        return point

    def energies(self) -> dict:
        internal = sum(p.internal_energy for p in self.points)
        kinetic = sum(p.kinetic_energy() for p in self.points)
        return {
            "internal": internal,
            "kinetic": kinetic,
            "total": internal + kinetic,
        }
