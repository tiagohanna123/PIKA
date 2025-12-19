"""CLI for informational previews (metrics, logs, JSON/CSV)."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import List
import numpy as np

from ..identity import identity
from ..config import SimulationConfig
from ..core import System
from ..process import default_processes, NoiseExploration, AdaptiveRegulator
from ..flow import Flow
from ..integrator import Integrator
from ..geometry import TrajectoryRecorder


def build_demo_system(seed: int | None = None) -> Flow:
    rng = np.random.default_rng(seed)
    system = System(dimension=2)
    for _ in range(12):
        pos = rng.uniform(-1, 1, size=2)
        vel = rng.normal(0, 0.3, size=2)
        system.add_point(pos, vel, energy=0.5)

    monitor_value = {"x": 0.0}

    def monitor() -> float:
        return monitor_value["x"]

    goal = np.array([0.5, 0.0])
    processes = default_processes(goal=goal)
    processes.append(NoiseExploration(sigma=0.05, rng=lambda: rng.normal(0, 1, size=2)))
    adaptive = AdaptiveRegulator(gain=0.2, monitor=monitor)
    processes.append(adaptive)

    flow = Flow(system=system, processes=processes)

    def update_monitor(metrics):
        monitor_value["x"] = metrics.x

    flow._update_monitor = update_monitor  # type: ignore[attr-defined]
    return flow


def run_preview(config: SimulationConfig) -> dict:
    flow = build_demo_system(seed=config.seed)
    recorder = TrajectoryRecorder.for_system(flow.system)
    integrator = Integrator(flow=flow, dt=config.dt, steps=config.steps)

    metrics = integrator.run()
    for m in metrics:
        flow._update_monitor(m)  # type: ignore[attr-defined]
        recorder.capture(flow.system)

    table = flow.metrics_table()
    summary = {
        "identity": identity.__dict__,
        "dt": config.dt,
        "steps": config.steps,
        "history": table,
    }
    return summary


def write_outputs(report: dict, out_json: Path | None, out_csv: Path | None) -> None:
    if out_json:
        out_json.write_text(json.dumps(report, indent=2))
    if out_csv:
        with out_csv.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=report["history"][0].keys())
            writer.writeheader()
            writer.writerows(report["history"])


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Informational preview for the configured system")
    parser.add_argument("--dt", type=float, default=0.05)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--out", type=Path, default=None, help="Optional JSON output")
    parser.add_argument("--csv", type=Path, default=None, help="Optional CSV output")
    args = parser.parse_args(argv)

    config = SimulationConfig(dt=args.dt, steps=args.steps, seed=None)
    report = run_preview(config)

    print(f"System: {identity.id} ({identity.symbol}) v{identity.version}")
    print(f"Description: {identity.description}")
    if report["history"]:
        last = report["history"][-1]
        print(f"Final X={last['x']:.4f} dX/dt={last['dx_dt']:.4f} E_total={last['E_total']:.4f}")
    write_outputs(report, args.out, args.csv)

    print("t\tphi_s\tphi_sigma\tX\tE_total")
    for row in report["history"][-10:]:
        print(f"{row['t']}\t{row['phi_s']:.3f}\t{row['phi_sigma']:.3f}\t{row['x']:.3f}\t{row['E_total']:.3f}")


if __name__ == "__main__":
    main()
