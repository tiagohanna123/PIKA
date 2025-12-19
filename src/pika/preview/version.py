"""Deterministic version preview for quick comparisons."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from textwrap import dedent
from typing import Iterable, Sequence, Tuple
import numpy as np

from pika.identity import identity
from pika.core import System
from pika.process import GoalAttraction, Viscosity, Process
from pika.flow import Flow
from pika.integrator import Integrator


@dataclass(frozen=True)
class PreviewFrame:
    step: int
    energies: Tuple[float, ...]
    entropy_signatures: Tuple[float, ...]


@dataclass(frozen=True)
class VersionPreview:
    system_id: str
    system_version: str
    description: str
    dt: float
    frames: Tuple[PreviewFrame, ...]

    def as_dict(self) -> dict:
        return {
            "system_id": self.system_id,
            "system_version": self.system_version,
            "description": self.description,
            "dt": self.dt,
            "frames": [
                {
                    "step": frame.step,
                    "energies": list(frame.energies),
                    "entropy_signatures": list(frame.entropy_signatures),
                }
                for frame in self.frames
            ],
        }


def render_preview(preview: VersionPreview) -> str:
    title = f"{preview.system_id} | version {preview.system_version}".strip()
    header = f"dt = {preview.dt:.4f} | description: {preview.description}"

    energy_header = " | ".join(
        ["step"]
        + [f"p{i} energy" for i in range(len(preview.frames[0].energies))]
        + [f"p{i} dE/dt" for i in range(len(preview.frames[0].entropy_signatures))]
    )

    rows = []
    for frame in preview.frames:
        energies = " | ".join(f"{energy:.4f}" for energy in frame.energies)
        signatures = " | ".join(f"{signature:.4f}" for signature in frame.entropy_signatures)
        rows.append(f"{frame.step:>4} | {energies} | {signatures}")

    legend = dedent(
        """
        Legend
        - Energies accumulate process contributions after each step.
        - dE/dt columns show the instantaneous syntropic (>= 0) or
          entropic (< 0) signatures reported before integration.
        """
    ).strip()

    lines = [title, header, energy_header, "-" * len(energy_header), *rows, legend]
    return "\n".join(lines)


def generate_version_preview(
    *,
    coordinates: Sequence[Sequence[float]] = ((0.0, 0.0), (1.0, 0.0)),
    processes: Iterable[Process] | None = None,
    dt: float = 0.1,
    steps: int = 5,
) -> VersionPreview:
    preview_processes = list(
        processes
        if processes is not None
        else (
            GoalAttraction(k=0.2, goal=np.array([0.5, 0.0])),
            Viscosity(mu=0.05),
        )
    )

    system = System(dimension=2)
    for coord in coordinates:
        system.add_point(position=np.array(coord), velocity=np.zeros(2))

    flow = Flow(system=system, processes=list(preview_processes))
    integrator = Integrator(flow=flow, dt=dt, steps=steps)

    frames = []
    for step_index in range(1, steps + 1):
        signatures = tuple(
            process.compute(system, point, 0.0).energy_rate
            for point in system.points
            for process in preview_processes
        )
        integrator.flow.step(dt)
        energies = tuple(point.total_energy() for point in system.points)
        frames.append(
            PreviewFrame(
                step=step_index,
                energies=energies,
                entropy_signatures=signatures,
            )
        )

    return VersionPreview(
        system_id=identity.id,
        system_version=identity.version,
        description=identity.description,
        dt=dt,
        frames=tuple(frames),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a deterministic preview of the configured system.",
    )
    parser.add_argument("--dt", type=float, default=0.1, help="Time step for integration.")
    parser.add_argument("--steps", type=int, default=5, help="Number of integration steps.")
    return parser


def main(argv=None) -> None:
    parser = _build_parser()
    parser.add_argument("--coordinates", nargs="*", type=float, help="Flat list of coordinates (x y x y ...)")
    args = parser.parse_args(argv)
    if args.coordinates:
        coords = list(zip(args.coordinates[::2], args.coordinates[1::2]))
    else:
        coords = ((0.0, 0.0), (1.0, 0.0))
    preview = generate_version_preview(coordinates=coords, dt=args.dt, steps=args.steps)
    print(render_preview(preview))


if __name__ == "__main__":
    main()
