from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from pika.flow import Flow, FlowMetrics

from .scenarios import ScenarioId, build_flow


LiveState = dict


@dataclass(frozen=True)
class SimulationResult:
    metrics: list[FlowMetrics]
    positions: np.ndarray  # (steps+1, n, 2)
    velocities: np.ndarray  # (steps+1, n, 2)
    internal_energy: np.ndarray  # (steps+1, n)


def run_simulation(
    *,
    scenario: ScenarioId,
    dt: float,
    steps: int,
    seed: int | None,
    points: int,
    params: dict,
    integrate_positions: bool,
) -> SimulationResult:
    """Run a PIKA simulation and return time series suitable for plotting.

    Notes
    -----
    The core (legacy) engine updates velocity and internal energy. Position
    integration is optional here for interactive visualization; enabling it
    can change the dynamics since some processes depend on position.
    """

    flow = build_flow(scenario=scenario, seed=seed, points=points, params=params)
    return _run_flow(flow=flow, dt=dt, steps=steps, integrate_positions=integrate_positions)


def init_live_state(
    *,
    scenario: ScenarioId,
    seed: int | None,
    points: int,
    params: dict,
) -> LiveState:
    """Create a JSON-serializable live simulation state.

    The returned state is meant to be stored in Dash (dcc.Store) and
    rehydrated across interval ticks.
    """

    # We keep RNG state explicitly so NoiseExploration remains continuous across ticks.
    rng = np.random.default_rng(seed)

    system_points = []
    initial_velocity_sigma = float(params.get("initial_velocity_sigma", 0.30))
    initial_energy = float(params.get("initial_energy", 0.50))
    for _ in range(int(points)):
        pos = rng.uniform(-1, 1, size=2)
        vel = rng.normal(0, initial_velocity_sigma, size=2)
        system_points.append(
            {
                "position": pos.tolist(),
                "velocity": vel.tolist(),
                "internal_energy": float(initial_energy),
            }
        )

    return {
        "scenario": str(scenario),
        "points": int(points),
        "params": dict(params),
        "t": 0.0,
        "step": 0,
        "monitor_x": 0.0,
        "rng_state": rng.bit_generator.state,
        "system_points": system_points,
    }


def step_live_state(*, state: LiveState, dt: float, integrate_positions: bool) -> tuple[LiveState, FlowMetrics]:
    """Advance a live state by one step and return updated state + metrics."""

    # Rehydrate RNG.
    rng = np.random.default_rng()
    if "rng_state" in state and state["rng_state"] is not None:
        rng.bit_generator.state = state["rng_state"]

    # Build a flow from current point state, using RNG only for stochastic processes.
    from .scenarios import build_flow_from_state

    flow = build_flow_from_state(
        scenario=state["scenario"],
        system_points=state["system_points"],
        params=state.get("params", {}),
        rng=rng,
        monitor_x=float(state.get("monitor_x", 0.0)),
        t=float(state.get("t", 0.0)),
    )

    metrics = flow.step(dt)
    update_monitor = getattr(flow, "_update_monitor", None)
    if callable(update_monitor):
        update_monitor(metrics)

    if integrate_positions:
        for p in flow.system.points:
            p.position = p.position + dt * p.velocity

    # Snapshot back into serializable state.
    next_points = []
    for p in flow.system.points:
        next_points.append(
            {
                "position": p.position.tolist(),
                "velocity": p.velocity.tolist(),
                "internal_energy": float(p.internal_energy),
            }
        )

    next_state: LiveState = {
        **state,
        "t": float(state.get("t", 0.0)) + float(dt),
        "step": int(state.get("step", 0)) + 1,
        "monitor_x": float(metrics.x),
        "rng_state": rng.bit_generator.state,
        "system_points": next_points,
    }
    return next_state, metrics


def _run_flow(*, flow: Flow, dt: float, steps: int, integrate_positions: bool) -> SimulationResult:
    system = flow.system
    n = len(system.points)

    positions = np.zeros((steps + 1, n, system.dimension), dtype=float)
    velocities = np.zeros((steps + 1, n, system.dimension), dtype=float)
    internal_energy = np.zeros((steps + 1, n), dtype=float)

    def snapshot(step_index: int) -> None:
        for i, p in enumerate(system.points):
            positions[step_index, i, :] = p.position
            velocities[step_index, i, :] = p.velocity
            internal_energy[step_index, i] = p.internal_energy

    snapshot(0)

    metrics: list[FlowMetrics] = []
    for step_index in range(1, steps + 1):
        m = flow.step(dt)
        metrics.append(m)

        update_monitor = getattr(flow, "_update_monitor", None)
        if callable(update_monitor):
            update_monitor(m)

        if integrate_positions:
            for p in system.points:
                p.position = p.position + dt * p.velocity

        snapshot(step_index)

    return SimulationResult(
        metrics=metrics,
        positions=positions,
        velocities=velocities,
        internal_energy=internal_energy,
    )
