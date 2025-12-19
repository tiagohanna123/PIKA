"""Numerical helpers for stability."""
from __future__ import annotations

import numpy as np


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def safe_norm(vec: np.ndarray, eps: float = 1e-9) -> float:
    return float(np.linalg.norm(vec) + eps)
