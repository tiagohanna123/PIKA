from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

import numpy as np
from numpy.random import Generator

from pika.core import System
from pika.flow import Flow
from pika.process import (
    AdaptiveRegulator,
    CouplingKernel,
    EntropyForce,
    GoalAttraction,
    InternalPump,
    NoiseExploration,
    OrganizationBarrier,
    Process,
    SyntropyWaveRegulator,
    Viscosity,
)

ScenarioId = Literal["core", "finance", "biology", "fluids"]


@dataclass(frozen=True)
class ProcessBuildResult:
    processes: list[Process]
    monitor_value: dict[str, float] | None = None


@dataclass(frozen=True)
class ScenarioPreset:
    id: ScenarioId
    title: str
    description: str
    goal: np.ndarray
    default_points: int
    build_processes: Callable[[Generator, np.ndarray, dict], ProcessBuildResult]


def _build_processes_core(
    rng: Generator,
    goal: np.ndarray,
    params: dict,
) -> ProcessBuildResult:
    include_noise = bool(params.get("include_noise", True))
    include_coupling = bool(params.get("include_coupling", True))
    include_regulator = bool(params.get("include_regulator", True))

    pump_power = float(params.get("pump_power", 0.10))
    goal_k = float(params.get("goal_k", 0.50))
    viscosity_mu = float(params.get("viscosity_mu", 0.05))
    barrier_k = float(params.get("barrier_k", 0.20))
    barrier_radius = float(params.get("barrier_radius", 0.50))

    noise_sigma = float(params.get("noise_sigma", 0.05))
    coupling_alpha = float(params.get("coupling_alpha", 0.00))
    coupling_length = float(params.get("coupling_length", 0.75))

    monitor_value = {"x": 0.0}

    def monitor() -> float:
        return float(monitor_value["x"])

    processes: list[Process] = [
        EntropyForce.from_polar(
            magnitude=float(params.get("entropy_force_mag", 0.20)),
            angle_deg=float(params.get("entropy_force_angle", 0.0)),
        ),
        InternalPump(power=pump_power),
        GoalAttraction(k=goal_k, goal=goal),
        Viscosity(mu=viscosity_mu),
        OrganizationBarrier(k=barrier_k, center=goal, radius=barrier_radius),
    ]

    if include_coupling and coupling_alpha != 0.0:
        processes.append(CouplingKernel(alpha=coupling_alpha, length_scale=coupling_length))

    if include_noise and noise_sigma > 0.0:
        processes.append(NoiseExploration(sigma=noise_sigma, rng=lambda: rng.normal(0, 1, size=2)))

    if include_regulator:
        processes.append(
            SyntropyWaveRegulator(
                gain=float(params.get("syntropy_wave_gain", float(params.get("regulator_gain", 0.20)))),
                k=float(params.get("syntropy_wave_k", 2.0)),
                omega=float(params.get("syntropy_wave_omega", 1.0)),
                monitor=monitor,
            )
        )

    return ProcessBuildResult(processes=processes, monitor_value=monitor_value if include_regulator else None)


def _preset(
    *,
    id: ScenarioId,
    title: str,
    description: str,
    goal: tuple[float, float],
    default_points: int,
) -> ScenarioPreset:
    def build_processes(rng: Generator, goal_vec: np.ndarray, params: dict) -> ProcessBuildResult:
        return _build_processes_core(rng, goal_vec, params)

    return ScenarioPreset(
        id=id,
        title=title,
        description=description,
        goal=np.array(goal, dtype=float),
        default_points=default_points,
        build_processes=build_processes,
    )


SCENARIOS: dict[ScenarioId, ScenarioPreset] = {
    "core": _preset(
        id="core",
        title="Núcleo PIKA (Sintropia ↔ Entropia)",
        description=(
            "Cenário base: bomba interna (ação), atração ao objetivo (organização), "
            "viscosidade (dissipação) e barreira de organização. Opcional: ruído (η), acoplamento e regulador."
        ),
        goal=(0.5, 0.0),
        default_points=20,
    ),
    "finance": _preset(
        id="finance",
        title="Mercados Financeiros (Ciclos e Choques)",
        description=(
            "Equilíbrio dinâmico com choques estocásticos (η) e regulação por feedback para tender |X| → 0. "
            "Útil para visualizar fases sintrópicas/entrópicas e transições."
        ),
        goal=(0.4, -0.2),
        default_points=30,
    ),
    "biology": _preset(
        id="biology",
        title="Biologia (Homeostase)",
        description=(
            "Maior amortecimento (viscosidade) + regulação de feedback, para estabilização em torno de uma zona de equilíbrio dinâmico."
        ),
        goal=(0.0, 0.0),
        default_points=25,
    ),
    "fluids": _preset(
        id="fluids",
        title="Fluidos (Acoplamento + Dissipação)",
        description=(
            "Enfatiza acoplamento entre pontos (fluxo coletivo) e viscosidade (dissipação), aproximando comportamento de fluidos."
        ),
        goal=(0.2, 0.2),
        default_points=40,
    ),
}


def list_scenarios() -> list[ScenarioPreset]:
    return [SCENARIOS[key] for key in ("core", "finance", "biology", "fluids")]


def build_flow(*, scenario: ScenarioId, seed: int | None, points: int, params: dict) -> Flow:
    rng = np.random.default_rng(seed)
    preset = SCENARIOS[scenario]

    system = System(dimension=2)
    for _ in range(int(points)):
        pos = rng.uniform(-1, 1, size=2)
        vel = rng.normal(0, float(params.get("initial_velocity_sigma", 0.30)), size=2)
        system.add_point(pos, vel, energy=float(params.get("initial_energy", 0.50)))

    goal = preset.goal
    build_result = preset.build_processes(rng, goal, params)
    flow = Flow(system=system, processes=list(build_result.processes))

    if build_result.monitor_value is not None:
        monitor_value = build_result.monitor_value

        def _update_monitor(metrics) -> None:
            monitor_value["x"] = float(metrics.x)

        flow._update_monitor = _update_monitor  # type: ignore[attr-defined]

    return flow


def build_flow_from_state(
    *,
    scenario: ScenarioId | str,
    system_points: list[dict],
    params: dict,
    rng: Generator,
    monitor_x: float = 0.0,
    t: float = 0.0,
) -> Flow:
    """Create a Flow rehydrated from explicit point state.

    This is used by the portal's live-mode stepping: it keeps the stochastic
    RNG continuous across ticks and seeds the regulator monitor with the last X.
    """

    scenario_id: ScenarioId = scenario if isinstance(scenario, str) else scenario
    preset = SCENARIOS[scenario_id]

    system = System(dimension=2)
    for p in system_points:
        system.add_point(
            np.array(p["position"], dtype=float),
            np.array(p["velocity"], dtype=float),
            energy=float(p.get("internal_energy", 0.0)),
        )

    goal = preset.goal
    build_result = preset.build_processes(rng, goal, params)
    flow = Flow(system=system, processes=list(build_result.processes))
    flow.t = float(t)

    if build_result.monitor_value is not None:
        monitor_value = build_result.monitor_value
        monitor_value["x"] = float(monitor_x)

        def _update_monitor(metrics) -> None:
            monitor_value["x"] = float(metrics.x)

        flow._update_monitor = _update_monitor  # type: ignore[attr-defined]

    return flow
