"""Geometry utilities.

Re-exports the legacy helpers used by preview scripts.
"""

from .legacy import TrajectoryRecorder, curvature_proxy, density_proxy, pairwise_distances

__all__ = ["TrajectoryRecorder", "pairwise_distances", "density_proxy", "curvature_proxy"]

