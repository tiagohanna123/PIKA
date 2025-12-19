"""Geometry utilities for spatial analysis and plotting helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

from .core import Point, System


def pairwise_distances(points: List[Point]) -> np.ndarray:
    coords = np.stack([p.position for p in points])
    diff = coords[:, None, :] - coords[None, :, :]
    return np.linalg.norm(diff, axis=-1)


def density_proxy(points: List[Point], bins: int = 10) -> np.ndarray:
    coords = np.stack([p.position for p in points])
    hist, _ = np.histogramdd(coords, bins=bins)
    return hist


def curvature_proxy(traj: List[np.ndarray]) -> float:
    if len(traj) < 3:
        return 0.0
    diffs = np.diff(np.stack(traj), axis=0)
    norms = np.linalg.norm(diffs, axis=1) + 1e-9
    unit = diffs / norms[:, None]
    changes = np.diff(unit, axis=0)
    return float(np.mean(np.linalg.norm(changes, axis=1)))


@dataclass
class TrajectoryRecorder:
    traces: List[List[np.ndarray]]

    @classmethod
    def for_system(cls, system: System) -> "TrajectoryRecorder":
        return cls(traces=[[p.position.copy()] for p in system.points])

    def capture(self, system: System) -> None:
        for trace, point in zip(self.traces, system.points):
            trace.append(point.position.copy())

    def as_arrays(self) -> List[np.ndarray]:
        return [np.stack(trace) for trace in self.traces]
