"""State representation for a system point.

State is kept intentionally abstract to allow multidimensional physical
variables (e.g., velocity, charge, spin). The state container provides a
consistent interface for processes to interrogate and mutate local
conditions without assuming a fixed schema.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, MutableMapping


@dataclass
class PointState:
    """Mutable mapping of state variables for a point.

    The mapping-based approach avoids locking the model into a single
    coordinate system or set of conserved quantities, which is essential
    for studying multiple phenomena within the same spatial substrate.
    """

    variables: MutableMapping[str, float] = field(default_factory=dict)

    def energy(self) -> float:
        """Return the current energy scalar for the point.

        Energy is treated as a first-class observable because dE/dt is
        the criterion for entropic vs. syntropic behavior.
        """

        return self.variables.get("energy", 0.0)

    def as_mapping(self) -> Mapping[str, float]:
        """Expose a read-only view of the variables.

        Processes should prefer this to avoid unintended coupling.
        """

        return dict(self.variables)

    def update_energy(self, delta: float) -> None:
        """Shift energy by ``delta`` while preserving sign semantics."""

        self.variables["energy"] = self.energy() + delta
