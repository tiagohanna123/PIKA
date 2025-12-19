"""Flow-level orchestration of process interactions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence

from pika.config.system import system_identity
from pika.core.point import Point
from pika.process.base import Process


@dataclass
class FlowField:
    """Collection of points evolving under multiple processes.

    The field aggregates local energy deltas from each process and
    applies them to the points. This models simultaneous interactions
    and keeps the entropic/syntropic classification rooted in dE/dt.
    """

    points: Sequence[Point]
    processes: Iterable[Process] = field(default_factory=list)

    def step(self, dt: float) -> None:
        """Advance the field by ``dt`` applying all processes.

        Each process contributes an energy delta. Aggregation occurs per
        point to preserve superposition of local interactions. The system
        identity is not used numerically but is available for logging or
        instrumentation hooks.
        """

        _ = system_identity  # access shows intentional dependency for logging/debugging.
        for point in self.points:
            total_delta = sum(process.energy_delta(point, dt) for process in self.processes)
            point.apply_energy_change(total_delta)

    def entropy_signatures(self, dt: float) -> List[float]:
        """Preview the entropic/syntropic signatures for the next step.

        This avoids mutating state while still surfacing dE/dt-oriented
        diagnostics. Positive values indicate syntropic behavior.
        """

        signatures: List[float] = []
        for point in self.points:
            delta = sum(process.energy_delta(point, dt) for process in self.processes)
            signatures.append(delta / dt if dt != 0 else 0.0)
        return signatures
