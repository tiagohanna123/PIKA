"""Geometric preview producing plots."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List
import numpy as np
import matplotlib.pyplot as plt

from ..identity import identity
from ..config import SimulationConfig
from ..core import System
from ..process import default_processes, NoiseExploration
from ..flow import Flow
from ..integrator import Integrator
from ..geometry import TrajectoryRecorder


def build_geo_flow(seed: int | None = None) -> tuple[Flow, TrajectoryRecorder]:
    rng = np.random.default_rng(seed)
    system = System(dimension=2)
    for _ in range(20):
        system.add_point(rng.uniform(-1, 1, size=2), rng.normal(0, 0.4, size=2), energy=0.3)
    goal = np.array([0.4, -0.2])
    processes = default_processes(goal=goal)
    processes.append(NoiseExploration(sigma=0.08, rng=lambda: rng.normal(0, 1, size=2)))
    flow = Flow(system=system, processes=processes)
    recorder = TrajectoryRecorder.for_system(system)
    return flow, recorder


def render_plot(recorder: TrajectoryRecorder, flow: Flow, output: Path) -> None:
    plt.figure(figsize=(6, 6))
    traces = recorder.as_arrays()
    for trace in traces:
        plt.plot(trace[:, 0], trace[:, 1], alpha=0.4)
        plt.scatter(trace[-1, 0], trace[-1, 1], s=20)
    plt.quiver(
        [p.position[0] for p in flow.system.points],
        [p.position[1] for p in flow.system.points],
        [p.velocity[0] for p in flow.system.points],
        [p.velocity[1] for p in flow.system.points],
        color="tab:blue",
        alpha=0.6,
    )
    plt.title(f"{identity.id} v{identity.version} | Final positions")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.axis("equal")
    plt.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output)
    plt.close()


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Geometric preview with trajectories and velocities")
    parser.add_argument("--dt", type=float, default=0.02)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--save", type=Path, default=Path("frames/final.png"))
    args = parser.parse_args(argv)

    config = SimulationConfig(dt=args.dt, steps=args.steps, seed=None)
    flow, recorder = build_geo_flow(seed=config.seed)
    integrator = Integrator(flow=flow, dt=config.dt, steps=config.steps)

    metrics = integrator.run()
    for _ in metrics:
        recorder.capture(flow.system)

    render_plot(recorder, flow, args.save)
    print(f"Saved geometric preview to {args.save}")


if __name__ == "__main__":
    main()
