"""Point representation within the system field."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .state import PointState


@dataclass
class Point:
    """Spatial point with state and energy accumulation.

    Position is modeled as an iterable of floats to avoid forcing a
    specific coordinate system (Cartesian, polar, or manifold charts can
    be layered later). The point delegates energy handling to its state
    so that processes can uniformly adjust energy.
    """

    position: Iterable[float]
    state: PointState

    def apply_energy_change(self, delta: float) -> None:
        """Modify the point's energy.

        Positive ``delta`` denotes syntropic contribution (dE/dt ≥ 0),
        negative denotes entropic (dE/dt < 0). The method intentionally
        avoids clamping to keep the simulation faithful to natural drift.
        """

        self.state.update_energy(delta)
