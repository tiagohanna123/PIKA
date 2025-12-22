"""Legacy process definitions and contributions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List
import math

import numpy as np

from pika.core import Point, System


@dataclass
class ProcessContribution:
    point_id: int
    energy_rate: float
    velocity_delta: np.ndarray
    label: str


class Process:
    """Base class for local processes (legacy engine)."""

    label: str = "process"

    def compute(self, system: System, point: Point, t: float) -> ProcessContribution:
        raise NotImplementedError


class Viscosity(Process):
    def __init__(self, mu: float):
        self.mu = mu
        self.label = "viscosity"

    def compute(self, system: System, point: Point, t: float) -> ProcessContribution:
        drag = -self.mu * point.velocity
        energy_rate = -float(np.dot(drag, point.velocity))
        return ProcessContribution(point.id, energy_rate, drag, self.label)


class GoalAttraction(Process):
    def __init__(self, k: float, goal: np.ndarray):
        self.k = k
        self.goal = np.array(goal, dtype=float)
        self.label = "goal_attraction"

    def compute(self, system: System, point: Point, t: float) -> ProcessContribution:
        displacement = self.goal - point.position
        accel = self.k * displacement
        energy_rate = float(np.dot(accel, point.velocity))
        return ProcessContribution(point.id, energy_rate, accel, self.label)


class OrganizationBarrier(Process):
    def __init__(self, k: float, center: np.ndarray, radius: float):
        self.k = k
        self.center = np.array(center, dtype=float)
        self.radius = radius
        self.label = "organization_barrier"

    def compute(self, system: System, point: Point, t: float) -> ProcessContribution:
        offset = point.position - self.center
        dist = np.linalg.norm(offset) + 1e-9
        if dist <= self.radius:
            repel = self.k * (offset / dist)
        else:
            repel = np.zeros_like(point.position)
        energy_rate = float(np.dot(repel, point.velocity))
        return ProcessContribution(point.id, energy_rate, repel, self.label)


class InternalPump(Process):
    def __init__(self, power: float):
        self.power = power
        self.label = "internal_pump"

    def compute(self, system: System, point: Point, t: float) -> ProcessContribution:
        return ProcessContribution(point.id, self.power, np.zeros_like(point.velocity), self.label)


class CouplingKernel(Process):
    def __init__(self, alpha: float, length_scale: float):
        self.alpha = alpha
        self.length_scale = length_scale
        self.label = "coupling_kernel"

    def compute(self, system: System, point: Point, t: float) -> ProcessContribution:
        influence = np.zeros_like(point.velocity)
        for other in system.points:
            if other.id == point.id:
                continue
            delta = other.position - point.position
            dist = np.linalg.norm(delta) + 1e-9
            weight = np.exp(-(dist**2) / (2 * self.length_scale**2))
            influence += weight * (other.velocity - point.velocity)
        accel = self.alpha * influence
        energy_rate = float(np.dot(accel, point.velocity))
        return ProcessContribution(point.id, energy_rate, accel, self.label)


class NoiseExploration(Process):
    def __init__(self, sigma: float, rng: Callable[[], np.ndarray]):
        self.sigma = sigma
        self.rng = rng
        self.label = "noise_exploration"

    def compute(self, system: System, point: Point, t: float) -> ProcessContribution:
        noise = self.sigma * self.rng()
        energy_rate = float(np.dot(noise, point.velocity))
        return ProcessContribution(point.id, energy_rate, noise, self.label)


class AdaptiveRegulator(Process):
    """Feedback mechanism nudging |X| toward zero without forcing equilibrium."""

    def __init__(self, gain: float, monitor: Callable[[], float]):
        self.gain = gain
        self.monitor = monitor
        self.label = "adaptive_regulator"

    def compute(self, system: System, point: Point, t: float) -> ProcessContribution:
        x_value = self.monitor()
        damping = -self.gain * np.tanh(x_value) * point.velocity
        energy_rate = -float(np.dot(damping, point.velocity))
        return ProcessContribution(point.id, energy_rate, damping, self.label)


class EntropyForce(Process):
    """Constant entropic vector (continuous disturbance).

    Applies a constant acceleration vector to every point, while charging
    an always-negative energy rate so it counts as entropy (Φσ).
    """

    def __init__(self, magnitude: float, direction: np.ndarray):
        self.magnitude = float(magnitude)
        d = np.array(direction, dtype=float)
        n = float(np.linalg.norm(d))
        self.direction = d / (n + 1e-12)
        self.label = "entropy_force"

    @staticmethod
    def from_polar(magnitude: float, angle_deg: float) -> "EntropyForce":
        theta = math.radians(float(angle_deg))
        direction = np.array([math.cos(theta), math.sin(theta)], dtype=float)
        return EntropyForce(magnitude=magnitude, direction=direction)

    def compute(self, system: System, point: Point, t: float) -> ProcessContribution:
        accel = self.magnitude * self.direction
        energy_rate = -abs(float(np.dot(accel, point.velocity)))
        return ProcessContribution(point.id, energy_rate, accel, self.label)


class SyntropyWaveRegulator(Process):
    """Organizing wave vectors modulated to push X -> 0."""

    def __init__(self, gain: float, k: float, omega: float, monitor: Callable[[], float]):
        self.gain = float(gain)
        self.k = float(k)
        self.omega = float(omega)
        self.monitor = monitor
        self.label = "syntropy_wave_regulator"

    def compute(self, system: System, point: Point, t: float) -> ProcessContribution:
        x_value = float(self.monitor())
        amp = -self.gain * math.tanh(x_value)

        x0 = float(point.position[0])
        y0 = float(point.position[1])
        base = np.array(
            [
                math.sin(self.k * x0 + self.omega * float(t)),
                math.cos(self.k * y0 + self.omega * float(t)),
            ],
            dtype=float,
        )

        accel = amp * base
        energy_rate = float(np.dot(accel, point.velocity))
        return ProcessContribution(point.id, energy_rate, accel, self.label)


def default_processes(goal: np.ndarray) -> List[Process]:
    return [
        InternalPump(power=0.1),
        GoalAttraction(k=0.5, goal=goal),
        Viscosity(mu=0.05),
        OrganizationBarrier(k=0.2, center=goal, radius=0.5),
    ]
