"""Time integration utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List
import numpy as np

from .flow import Flow, FlowMetrics


def semi_implicit_euler(flow: Flow, dt: float, steps: int) -> List[FlowMetrics]:
    metrics: List[FlowMetrics] = []
    for _ in range(steps):
        metrics.append(flow.step(dt))
    return metrics


def rk2(flow: Flow, dt: float, steps: int) -> List[FlowMetrics]:
    metrics: List[FlowMetrics] = []
    for _ in range(steps):
        state_snapshot = [(p.velocity.copy(), p.internal_energy) for p in flow.system.points]
        m1 = flow.step(dt / 2)
        for p, (vel0, e0) in zip(flow.system.points, state_snapshot):
            p.velocity = vel0
            p.internal_energy = e0
        m2 = flow.step(dt)
        metrics.append(m2)
    return metrics


@dataclass
class Integrator:
    flow: Flow
    dt: float
    steps: int
    scheme: Callable[[Flow, float, int], List[FlowMetrics]] = semi_implicit_euler

    def run(self) -> List[FlowMetrics]:
        return self.scheme(self.flow, self.dt, self.steps)
