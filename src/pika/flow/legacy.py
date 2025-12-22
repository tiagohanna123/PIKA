"""Legacy flow aggregation and energetic accounting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from pika.core import System
from pika.process import Process, ProcessContribution


@dataclass
class FlowMetrics:
    phi_s: float
    phi_sigma: float
    x: float
    dx_dt: float
    total_energy: float
    kinetic_energy: float
    internal_energy: float


@dataclass
class Flow:
    system: System
    processes: List[Process]
    t: float = 0.0
    history: List[FlowMetrics] = field(default_factory=list)

    def step(self, dt: float) -> FlowMetrics:
        contributions: List[ProcessContribution] = []
        for process in self.processes:
            for point in self.system.points:
                contributions.append(process.compute(self.system, point, self.t))

        phi_s = sum(c.energy_rate for c in contributions if c.energy_rate >= 0.0)
        phi_sigma = sum(-c.energy_rate for c in contributions if c.energy_rate < 0.0)
        x_value = phi_s - phi_sigma

        for c in contributions:
            p = self.system.points[c.point_id]
            p.apply_velocity_change(dt * c.velocity_delta)
            p.apply_energy_change(dt * c.energy_rate)

        energies = self.system.energies()
        dx_dt = (x_value - self.history[-1].x) / dt if self.history else 0.0
        metrics = FlowMetrics(
            phi_s=phi_s,
            phi_sigma=phi_sigma,
            x=x_value,
            dx_dt=dx_dt,
            total_energy=energies["total"],
            kinetic_energy=energies["kinetic"],
            internal_energy=energies["internal"],
        )
        self.history.append(metrics)
        self.t += dt
        return metrics

    def metrics_table(self) -> List[Dict[str, float]]:
        return [
            {
                "t": i,
                "phi_s": m.phi_s,
                "phi_sigma": m.phi_sigma,
                "x": m.x,
                "dx_dt": m.dx_dt,
                "E_total": m.total_energy,
                "E_internal": m.internal_energy,
                "E_kin": m.kinetic_energy,
            }
            for i, m in enumerate(self.history)
        ]
