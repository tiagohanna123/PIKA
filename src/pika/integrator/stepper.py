"""Time integration utilities for flow evolution."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from pika.flow.field import FlowField


@dataclass
class FixedStepIntegrator:
    """Integrator applying a fixed time increment across multiple steps.

    This scaffolds future higher-order integrators while keeping the
    baseline deterministic and simple to reason about.
    """

    flow: FlowField
    dt: float

    def run(self, steps: int) -> None:
        """Advance the flow ``steps`` times by ``dt``.

        Repeated stepping models the asymptotic convergence toward
        equilibrium (which is never fully reached), aligning with the
        project's core principle.
        """

        for _ in range(steps):
            self.flow.step(self.dt)

    def entropy_trace(self, steps: int) -> Iterable[list[float]]:
        """Yield entropic/syntropic signatures without mutating points.

        This supports visualization and debugging of the energy gradient
        landscape before committing state changes.
        """

        for _ in range(steps):
            yield self.flow.entropy_signatures(self.dt)
