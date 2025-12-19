"""Lightweight numpy compatibility layer for offline testing.

This is intentionally minimal and supports only the operations exercised
by the preview and test suites. It is not a drop-in replacement for the
full NumPy library.
"""
from __future__ import annotations

import math
import random as _random
from typing import Iterable, List


class Array(list):
    def __add__(self, other):
        if isinstance(other, Array):
            return Array(a + b for a, b in zip(self, other))
        return Array(a + other for a in self)

    def __sub__(self, other):
        if isinstance(other, Array):
            return Array(a - b for a, b in zip(self, other))
        return Array(a - other for a in self)

    def __mul__(self, other):
        if isinstance(other, Array):
            return Array(a * b for a, b in zip(self, other))
        return Array(a * other for a in self)

    __rmul__ = __mul__

    def __truediv__(self, other):
        if isinstance(other, Array):
            return Array(a / b for a, b in zip(self, other))
        return Array(a / other for a in self)

    def copy(self):
        return Array(self)


def array(seq, dtype=None):
    return Array(seq)


def zeros(shape, dtype=float):
    if isinstance(shape, int):
        return Array([0.0 for _ in range(shape)])
    return Array([Array([0.0 for _ in range(shape[1])]) for _ in range(shape[0])])


def zeros_like(seq):
    return Array([0.0 for _ in seq])


def dot(a: Iterable[float], b: Iterable[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def stack(arrays: List[Iterable[float]], axis: int = 0):
    return Array([Array(a) for a in arrays])


def diff(arrays: Array, axis: int = 0):
    result = []
    for i in range(1, len(arrays)):
        result.append(Array(a - b for a, b in zip(arrays[i], arrays[i - 1])))
    return Array(result)


def exp(x):
    return math.exp(x)


def tanh(x):
    return math.tanh(x)


class _Linalg:
    @staticmethod
    def norm(vec, axis=None):
        if axis is None:
            return math.sqrt(sum(v * v for v in vec))
        if axis in (-1, 1):
            return Array(math.sqrt(sum(v * v for v in row)) for row in vec)
        raise NotImplementedError


linalg = _Linalg()


def histogramdd(coords, bins=10):
    coords = list(coords)
    if not coords:
        return Array(), []
    dims = len(coords[0])
    mins = [min(c[i] for c in coords) for i in range(dims)]
    maxs = [max(c[i] for c in coords) for i in range(dims)]
    edges = [Array(mins[i] + (maxs[i] - mins[i]) * j / bins for j in range(bins + 1)) for i in range(dims)]
    hist = [[0 for _ in range(bins)] for _ in range(bins)] if dims == 2 else [[[0]]]
    for c in coords:
        xi = min(int((c[0] - mins[0]) / (maxs[0] - mins[0] + 1e-9) * bins), bins - 1)
        yi = min(int((c[1] - mins[1]) / (maxs[1] - mins[1] + 1e-9) * bins), bins - 1) if dims > 1 else 0
        hist[xi][yi] += 1
    return Array(hist), edges


class _Generator:
    def __init__(self, seed=None):
        self.rng = _random.Random(seed)

    def uniform(self, low, high, size=None):
        if isinstance(size, int):
            return Array(self.rng.uniform(low, high) for _ in range(size))
        return Array(self.rng.uniform(low, high) for _ in range(size[0]))

    def normal(self, mean, std, size=None):
        if isinstance(size, int):
            return Array(self.rng.gauss(mean, std) for _ in range(size))
        return Array(self.rng.gauss(mean, std) for _ in range(size[0]))


def default_rng(seed=None):
    return _Generator(seed)


class _RandomModule:
    def default_rng(self, seed=None):
        return _Generator(seed)

    def normal(self, mean, std, size=None):
        return default_rng().normal(mean, std, size=size)

    def uniform(self, low, high, size=None):
        return default_rng().uniform(low, high, size=size)


random = _RandomModule()


__all__ = [
    "array",
    "zeros",
    "zeros_like",
    "stack",
    "diff",
    "dot",
    "exp",
    "tanh",
    "linalg",
    "histogramdd",
    "default_rng",
    "random",
    "Array",
]
