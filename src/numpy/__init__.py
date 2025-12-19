"""Lightweight numpy compatibility layer for offline testing.

This is intentionally minimal and supports only the operations exercised
by the preview and test suites. It is not a drop-in replacement for the
full NumPy library.
"""
from __future__ import annotations

import math
import random as _random
from typing import Iterable, List


class uint8(int):
    pass


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

    @property
    def shape(self):
        if not self:
            return (0,)
        if isinstance(self[0], Array):
            return (len(self),) + self[0].shape
        return (len(self),)

    def min(self, axis=None):
        if axis is None:
            return min(self)
        if axis in (0, -1, 1):
            return Array(min(col[i] for col in self) for i in range(len(self[0])))
        raise NotImplementedError

    def max(self, axis=None):
        if axis is None:
            return max(self)
        if axis in (0, -1, 1):
            return Array(max(col[i] for col in self) for i in range(len(self[0])))
        raise NotImplementedError


def array(seq, dtype=None):
    return Array(seq)


def zeros(shape, dtype=float):
    if isinstance(shape, int):
        return Array([0.0 for _ in range(shape)])
    return Array([Array([0.0 for _ in range(shape[1])]) for _ in range(shape[0])])


def full(shape, fill_value, dtype=None):
    def _fill(subshape):
        if isinstance(subshape, int):
            return Array(fill_value for _ in range(subshape))
        if len(subshape) == 0:
            return fill_value
        return Array(_fill(subshape[1:]) for _ in range(subshape[0]))

    return _fill(shape if isinstance(shape, tuple) else (shape,))


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


def maximum(a, b):
    if isinstance(a, Array):
        return Array(max(x, b[i] if isinstance(b, Array) else b) for i, x in enumerate(a))
    if isinstance(b, Array):
        return Array(max(a, y) for y in b)
    return max(a, b)


def clip(a, min_value, max_value):
    if isinstance(a, Array):
        return Array(min(max(x, min_value), max_value) for x in a)
    return min(max(a, min_value), max_value)


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
