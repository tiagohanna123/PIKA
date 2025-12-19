"""Geometric scaffolding for positioning points."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from pika.core.point import Point
from pika.core.state import PointState


@dataclass
class EuclideanSpace:
    """Minimal Euclidean embedding for points.

    The geometry layer remains intentionally light to accommodate future
    manifolds or graph-based topologies. It currently seeds points along
    provided coordinates and attaches blank state containers.
    """

    dimension: int

    def seed_points(self, coordinates: Sequence[Iterable[float]]) -> list[Point]:
        """Create points anchored at the supplied coordinates.

        The seeding function separates spatial layout from process
        definitions, keeping concerns clean for experiments that swap
        geometries without touching process code.
        """

        points: list[Point] = []
        for coordinate in coordinates:
            points.append(Point(position=coordinate, state=PointState()))
        return points
