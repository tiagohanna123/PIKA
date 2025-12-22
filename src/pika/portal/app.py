from __future__ import annotations

from dataclasses import asdict
import json
from hashlib import sha1
import math
from datetime import datetime, timezone

import plotly.graph_objects as go
from dash import Dash, Input, Output, State, callback, dcc, html, ctx
from dash.exceptions import PreventUpdate

from .scenarios import SCENARIOS, ScenarioId, list_scenarios
from pika.config.system import system_identity
from .simulation import run_simulation


_LIVE_RUNTIME: dict = {
    "config_key": None,
    "flow": None,
    "metrics": [],
    "positions": [],
    "velocities": [],
    "internal_energy": [],
}


_SLIDER_TOOLTIP = {"placement": "bottom", "always_visible": False}


CONTROL_PRESETS: dict[str, dict] = {
    "closed_equilibrium": {
        "label": "Fechado (X → 0)",
        "description": "Sistema mais 'fechado': sem ruído e sem bomba; ondas sintropicas ajustam para X tender a 0 frente à força entrópica.",
        "values": {
            "pump_power": 0.00,
            "noise_sigma": 0.00,
            "coupling_alpha": 0.00,
            "viscosity_mu": 0.08,
            "entropy_force_mag": 0.25,
            "entropy_force_angle": 0.0,
            "syntropy_wave_gain": 0.45,
            "syntropy_wave_k": 2.0,
            "syntropy_wave_omega": 1.5,
            "toggles": ["regulator", "kinematics"],
        },
    },
    "balanced_live": {
        "label": "Equilíbrio ao vivo (suave)",
        "description": "Preset para ver dinâmica fluida: dt menor, ondas moderadas, pouco ruído; bom para live mode.",
        "values": {
            "dt": 0.02,
            "pump_power": 0.05,
            "noise_sigma": 0.02,
            "viscosity_mu": 0.06,
            "entropy_force_mag": 0.20,
            "entropy_force_angle": 20.0,
            "syntropy_wave_gain": 0.30,
            "syntropy_wave_k": 2.0,
            "syntropy_wave_omega": 2.0,
            "live_interval": 100,
            "toggles": ["noise", "regulator", "kinematics"],
        },
    },
    "entropy_dominant": {
        "label": "Entropia domina", 
        "description": "A força entrópica é alta e a sintropia é baixa; X tende a ficar negativo.",
        "values": {
            "pump_power": 0.00,
            "noise_sigma": 0.00,
            "entropy_force_mag": 0.60,
            "entropy_force_angle": 0.0,
            "syntropy_wave_gain": 0.05,
            "syntropy_wave_k": 2.0,
            "syntropy_wave_omega": 1.0,
            "toggles": ["kinematics"],
        },
    },
    "syntropy_dominant": {
        "label": "Sintropia domina",
        "description": "Ondas organizadoras fortes; bom para ver padrões/ondas, mas pode saturar e oscilar.",
        "values": {
            "pump_power": 0.00,
            "noise_sigma": 0.00,
            "entropy_force_mag": 0.15,
            "entropy_force_angle": 0.0,
            "syntropy_wave_gain": 1.20,
            "syntropy_wave_k": 3.0,
            "syntropy_wave_omega": 3.0,
            "toggles": ["regulator", "kinematics"],
        },
    },
    "exploration": {
        "label": "Exploração (η)",
        "description": "Mais ruído para exploração; útil para ver transições e instabilidades.",
        "values": {
            "pump_power": 0.05,
            "noise_sigma": 0.10,
            "entropy_force_mag": 0.20,
            "entropy_force_angle": 0.0,
            "syntropy_wave_gain": 0.25,
            "syntropy_wave_k": 1.5,
            "syntropy_wave_omega": 1.0,
            "toggles": ["noise", "regulator", "kinematics"],
        },
    },
}


def _hover_help(text: str) -> html.Span:
    return html.Span(
        " (i)",
        title=text,
        style={
            "cursor": "help",
            "color": "#666",
            "marginLeft": "6px",
            "fontSize": "0.9rem",
            "userSelect": "none",
        },
    )


def _live_config_key(*, scenario: str, dt: float, points: int, seed: int | None, params: dict, integrate_positions: bool) -> str:
    payload = {
        "scenario": scenario,
        "dt": dt,
        "points": points,
        "seed": seed,
        "integrate_positions": integrate_positions,
        "params": params,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha1(blob.encode("utf-8")).hexdigest()


def _coerce_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _serialize_result(result) -> dict:
    metrics = [asdict(m) for m in result.metrics]
    return {
        "metrics": metrics,
        "positions": result.positions.tolist(),
        "velocities": result.velocities.tolist(),
        "internal_energy": result.internal_energy.tolist(),
    }


def _figure_timeseries(metrics: list[dict]) -> go.Figure:
    if not metrics:
        fig = go.Figure()
        fig.update_layout(title="Run a simulation to see metrics")
        return fig

    t = list(range(1, len(metrics) + 1))
    x_series = [float(m.get("x", 0.0)) for m in metrics]
    phi_s_series = [float(m.get("phi_s", 0.0)) for m in metrics]
    phi_sigma_series = [float(m.get("phi_sigma", 0.0)) for m in metrics]
    e_total_series = [float(m.get("total_energy", 0.0)) for m in metrics]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=x_series, mode="lines", name="X = Φs − Φσ"))
    fig.add_trace(go.Scatter(x=t, y=phi_s_series, mode="lines", name="Φs (syntropy)", opacity=0.8))
    fig.add_trace(go.Scatter(x=t, y=phi_sigma_series, mode="lines", name="Φσ (entropy)", opacity=0.8))
    fig.add_trace(go.Scatter(x=t, y=e_total_series, mode="lines", name="E_total", opacity=0.8))

    fig.update_layout(
        title="Flow metrics over time",
        xaxis_title="step",
        yaxis_title="value",
        legend_orientation="h",
        legend_y=-0.2,
        margin=dict(l=30, r=10, t=50, b=60),
    )
    return fig


def _figure_field(*, positions, velocities, energy, vector_scale: float) -> go.Figure:
    x = [p[0] for p in positions]
    y = [p[1] for p in positions]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="markers",
            name="points",
            marker=dict(
                size=9,
                color=energy,
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="internal E"),
            ),
        )
    )

    # Velocity vectors as line segments.
    line_x: list[float] = []
    line_y: list[float] = []
    for (px, py), (vx, vy) in zip(positions, velocities):
        line_x.extend([px, px + vector_scale * vx, None])
        line_y.extend([py, py + vector_scale * vy, None])

    fig.add_trace(
        go.Scatter(
            x=line_x,
            y=line_y,
            mode="lines",
            name="velocity",
            line=dict(width=1),
            opacity=0.7,
        )
    )

    fig.update_layout(
        title="Field view (positions, velocity vectors, internal energy)",
        xaxis_title="x",
        yaxis_title="y",
        xaxis=dict(scaleanchor="y", scaleratio=1),
        margin=dict(l=30, r=10, t=50, b=40),
        showlegend=False,
    )
    return fig


def _figure_field_3d(*, positions, velocities, energy, vector_scale: float, z_scale: float) -> go.Figure:
    x = [p[0] for p in positions]
    y = [p[1] for p in positions]
    z = list(energy)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(
                size=4,
                color=z,
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="internal E"),
            ),
        )
    )

    line_x: list[float] = []
    line_y: list[float] = []
    line_z: list[float] = []
    for (px, py), (vx, vy), z0 in zip(positions, velocities, z):
        magnitude = math.hypot(vx, vy)
        z_end = z0 + z_scale * magnitude
        line_x.extend([px, px + vector_scale * vx, None])
        line_y.extend([py, py + vector_scale * vy, None])
        line_z.extend([z0, z_end, None])

    fig.add_trace(
        go.Scatter3d(
            x=line_x,
            y=line_y,
            z=line_z,
            mode="lines",
            line=dict(width=2, color="lightsteelblue"),
            opacity=0.7,
        )
    )

    fig.update_layout(
        title="Campo 3D (energia interna no eixo z)",
        scene=dict(
            xaxis_title="x",
            yaxis_title="y",
            zaxis_title="energia interna",
            aspectmode="auto",
        ),
        margin=dict(l=30, r=10, t=50, b=40),
        showlegend=False,
    )
    return fig


def create_app() -> Dash:
    app = Dash(__name__)

    scenario_options = [
        {"label": f"{preset.title}", "value": preset.id}
        for preset in list_scenarios()
    ]

    app.layout = html.Div(
        [
            dcc.Store(id="sim-data"),
            dcc.Store(id="live-enabled", data=False),
            dcc.Interval(id="auto-run-interval", interval=200, disabled=True),
            html.Div(
                [
                    html.Div(
                        [
                            html.H1("Portal PIKA", style={"margin": 0}),
                            html.Div(
                                f"Sistema: {system_identity.id} • v{system_identity.version}",
                                style={"color": "#666"},
                            ),
                        ],
                        style={"padding": "12px 16px", "borderBottom": "1px solid #eee"},
                    ),
                    dcc.Tabs(
                        id="tabs",
                        value="tab-sim",
                        children=[
                            dcc.Tab(label="Simulação", value="tab-sim", children=[
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.H3("Como usar"),
                                                html.Details(
                                                    [
                                                        html.Summary("Guia rápido (clique para expandir)"),
                                                        dcc.Markdown(
                                                            r"""
1) **Escolha o cenário** (ele define o objetivo e a interpretação).
2) Ajuste **dt**, **steps** e **points**.
3) Clique em **Rodar simulação** para uma execução completa.
4) Para ver dinâmica contínua, use **Modo ao vivo** e diminua o intervalo.

**Leitura dos termos**
- **Entropia (Φσ)**: aqui é um **vetor constante** (força contínua) que "puxa" o sistema.
- **Sintropia (Φs)**: vetores organizadores em **ondas**, com amplitude modulada para empurrar **X → 0**.
""",
                                                            mathjax=True,
                                                        ),
                                                    ]
                                                ),
                                                html.Hr(),
                                                html.H3("Presets"),
                                                html.Div(
                                                    [
                                                        html.Label("Preset de controle"),
                                                        _hover_help(
                                                            "Ajusta vários parâmetros de uma vez (dt, ruído, entropia/sintropia, live interval e toggles) para um objetivo típico."
                                                        ),
                                                    ]
                                                ),
                                                dcc.Dropdown(
                                                    id="control-preset",
                                                    options=[
                                                        {"label": CONTROL_PRESETS[k]["label"], "value": k}
                                                        for k in CONTROL_PRESETS
                                                    ],
                                                    value="balanced_live",
                                                    clearable=False,
                                                ),
                                                html.Div(id="control-preset-desc", style={"marginTop": "8px", "color": "#444"}),
                                                html.Div(
                                                    "Use um preset e depois ajuste finamente se quiser.",
                                                    style={"fontSize": "0.85rem", "color": "#555", "marginTop": "6px"},
                                                ),
                                                html.Hr(),
                                                html.H3("Cenário"),
                                                html.Div(
                                                    [
                                                        html.Label("Cenário"),
                                                        _hover_help(
                                                            "Define o objetivo (goal) e a interpretação do experimento; muda também o número de pontos padrão."
                                                        ),
                                                    ]
                                                ),
                                                dcc.Dropdown(
                                                    id="scenario",
                                                    options=scenario_options,
                                                    value="core",
                                                    clearable=False,
                                                ),
                                                html.Div(id="scenario-desc", style={"marginTop": "8px", "color": "#444"}),
                                                html.Hr(),
                                                html.H3("Tempo"),
                                                html.Div([
                                                    html.Label("dt (passo de tempo)"),
                                                    _hover_help("Controla a resolução temporal. dt menor = dinâmica mais suave/estável, porém mais lenta e com mais passos para ver evolução."),
                                                ]),
                                                dcc.Input(id="dt", type="number", value=0.05, min=0.0001, step=0.01),
                                                html.Div("Menor dt = mais suave, porém mais lento.", style={"fontSize": "0.85rem", "color": "#555"}),
                                                html.Div([
                                                    html.Label("steps (nº de passos)", style={"marginTop": "6px"}),
                                                    _hover_help("Quantidade de iterações. Controla o horizonte temporal total (aprox. steps × dt)."),
                                                ]),
                                                dcc.Input(id="steps", type="number", value=200, min=1, step=10),
                                                html.Div("Mais steps = série temporal mais longa.", style={"fontSize": "0.85rem", "color": "#555"}),
                                                html.Div([
                                                    html.Label("points (nº de pontos)", style={"marginTop": "6px"}),
                                                    _hover_help("Número de partículas/pontos do sistema. Mais pontos = campo mais rico, porém mais pesado e com mais interações."),
                                                ]),
                                                dcc.Input(id="points", type="number", value=20, min=2, step=1),
                                                html.Div("Mais pontos = campo mais rico, porém mais pesado.", style={"fontSize": "0.85rem", "color": "#555"}),
                                                html.Div([
                                                    html.Label("seed (opcional)", style={"marginTop": "6px"}),
                                                    _hover_help("Semente do gerador aleatório. Fixar a seed torna o experimento reprodutível (ruído e inicialização)."),
                                                ]),
                                                dcc.Input(id="seed", type="number", value=0, min=0, step=1),
                                                html.Hr(),
                                                html.Details([
                                                    html.Summary("Processos"),
                                                    html.Div([
                                                        html.Div([
                                                            html.Label("Bomba interna (pump_power)"),
                                                            _hover_help("Fonte interna de energia (dE/dt positivo). Aumenta Φs (sintropia) e tende a elevar energia interna."),
                                                        ]),
                                                        dcc.Slider(id="pump_power", min=0.0, max=0.5, step=0.01, value=0.10, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                        html.Div("Ação/fonte interna (tende a aumentar energia interna).", style={"fontSize": "0.85rem", "color": "#555"}),
                                                        html.Div([
                                                            html.Label("Atração ao objetivo (goal_k)", style={"marginTop": "6px"}),
                                                            _hover_help("Força organizadora em direção ao objetivo do cenário. Em geral aumenta organização do fluxo e pode aumentar Φs."),
                                                        ]),
                                                        dcc.Slider(id="goal_k", min=0.0, max=2.0, step=0.05, value=0.50, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                        html.Div("Organiza o movimento em direção ao objetivo do cenário.", style={"fontSize": "0.85rem", "color": "#555"}),
                                                        html.Div([
                                                            html.Label("Viscosidade (viscosity_mu)", style={"marginTop": "6px"}),
                                                            _hover_help("Amortecimento/dissipação. Reduz velocidade e energia cinética; tende a aumentar Φσ (entropia) por perdas."),
                                                        ]),
                                                        dcc.Slider(id="viscosity_mu", min=0.0, max=0.5, step=0.01, value=0.05, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                        html.Div("Dissipação/amortecimento (tende a reduzir energia cinética).", style={"fontSize": "0.85rem", "color": "#555"}),
                                                        html.Div([
                                                            html.Label("Barreira (barrier_k)", style={"marginTop": "6px"}),
                                                            _hover_help("Intensidade da barreira de organização (repulsão dentro do raio). Ajuda a moldar trajetórias e evitar colapso no centro."),
                                                        ]),
                                                        dcc.Slider(id="barrier_k", min=0.0, max=1.0, step=0.02, value=0.20, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                        html.Div([
                                                            html.Label("Raio da barreira (barrier_radius)", style={"marginTop": "6px"}),
                                                            _hover_help("Raio de atuação da barreira. Define a região em que a força repulsiva entra em ação."),
                                                        ]),
                                                        dcc.Slider(id="barrier_radius", min=0.0, max=2.0, step=0.05, value=0.50, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                        html.Div([
                                                            html.Label("Ruído (noise_sigma)", style={"marginTop": "6px"}),
                                                            _hover_help("Intensidade do ruído estocástico η. Aumenta exploração e variabilidade; pode impedir convergência se alto."),
                                                        ]),
                                                        dcc.Slider(id="noise_sigma", min=0.0, max=0.25, step=0.01, value=0.05, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                        html.Div("Exploração estocástica (pode desestabilizar ou ajudar a escapar de mínimos locais).", style={"fontSize": "0.85rem", "color": "#555"}),
                                                        html.Div([
                                                            html.Label("Acoplamento (coupling_alpha)", style={"marginTop": "6px"}),
                                                            _hover_help("Força de acoplamento entre pontos. Faz o sistema agir de forma mais coletiva (tende a alinhar velocidades)."),
                                                        ]),
                                                        dcc.Slider(id="coupling_alpha", min=0.0, max=1.0, step=0.05, value=0.00, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                        html.Div([
                                                            html.Label("Escala de acoplamento (coupling_length)", style={"marginTop": "6px"}),
                                                            _hover_help("Alcance do acoplamento (quanto maior, mais vizinhos influenciam)."),
                                                        ]),
                                                        dcc.Slider(id="coupling_length", min=0.05, max=2.0, step=0.05, value=0.75, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                        html.Div([
                                                            html.Label("Ganho do regulador (regulator_gain)", style={"marginTop": "6px"}),
                                                            _hover_help("Compatibilidade/legado: usado como fallback para wave_gain. Aumentar tende a tornar a correção para X→0 mais forte."),
                                                        ]),
                                                        dcc.Slider(id="regulator_gain", min=0.0, max=1.0, step=0.05, value=0.20, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                        html.Hr(),
                                                        html.Div([
                                                            html.Label("Entropia: força constante (magnitude)", style={"marginTop": "6px"}),
                                                            _hover_help("Magnitude do vetor entrópico constante. Quanto maior, mais perturbação contínua (tende a aumentar Φσ)."),
                                                        ]),
                                                        dcc.Slider(id="entropy_force_mag", min=0.0, max=1.0, step=0.02, value=0.20, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                        html.Div("Vetor contínuo: quanto maior, mais Φσ domina.", style={"fontSize": "0.85rem", "color": "#555"}),
                                                        html.Div([
                                                            html.Label("Entropia: direção (ângulo em graus)", style={"marginTop": "6px"}),
                                                            _hover_help("Direção do vetor entrópico no plano XY. Muda o sentido do 'vento' que perturba o sistema."),
                                                        ]),
                                                        dcc.Slider(id="entropy_force_angle", min=0, max=360, step=5, value=0, marks={0: "0", 90: "90", 180: "180", 270: "270", 360: "360"}, tooltip=_SLIDER_TOOLTIP),
                                                        html.Div([
                                                            html.Label("Sintropia: ganho das ondas (wave_gain)", style={"marginTop": "6px"}),
                                                            _hover_help("Intensidade das ondas organizadoras. Aumentar acelera correção para X→0, mas pode gerar oscilação se muito alto."),
                                                        ]),
                                                        dcc.Slider(id="syntropy_wave_gain", min=0.0, max=2.0, step=0.05, value=0.20, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                        html.Div("Controle organizador: aumenta/reduz para empurrar X → 0.", style={"fontSize": "0.85rem", "color": "#555"}),
                                                        html.Div([
                                                            html.Label("Sintropia: frequência espacial (wave_k)", style={"marginTop": "6px"}),
                                                            _hover_help("Define quantas 'ondulações' no espaço. k maior = padrões mais rápidos no espaço e mais sensibilidade à posição."),
                                                        ]),
                                                        dcc.Slider(id="syntropy_wave_k", min=0.0, max=10.0, step=0.25, value=2.0, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                        html.Div([
                                                            html.Label("Sintropia: frequência temporal (wave_omega)", style={"marginTop": "6px"}),
                                                            _hover_help("Velocidade de variação temporal das ondas. omega maior = oscilação mais rápida no tempo."),
                                                        ]),
                                                        dcc.Slider(id="syntropy_wave_omega", min=0.0, max=10.0, step=0.25, value=1.0, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                        html.Div([
                                                            html.Label("Opções"),
                                                            _hover_help("Ativa/desativa componentes do modelo (ruído, acoplamento, regulador) e a integração de posições para visualização cinemática."),
                                                        ]),
                                                        dcc.Checklist(
                                                            id="toggles",
                                                            options=[
                                                                {"label": "Incluir ruído (η)", "value": "noise"},
                                                                {"label": "Incluir acoplamento", "value": "coupling"},
                                                                {"label": "Incluir regulador (feedback)", "value": "regulator"},
                                                                {"label": "Integrar posição (cinemática visual)", "value": "kinematics"},
                                                            ],
                                                            value=["noise", "regulator", "kinematics"],
                                                            style={"marginTop": "6px"},
                                                        ),
                                                        html.Div(
                                                            "Dica: para um 'sistema fechado', teste sem ruído e sem bomba; deixe o regulador ligado e ajuste wave_gain.",
                                                            style={"fontSize": "0.85rem", "color": "#555", "marginTop": "6px"},
                                                        ),
                                                    ])
                                                ]),
                                                html.Hr(),
                                                html.Div([
                                                    html.Label("Escala do vetor (visualização de campo)", style={"marginTop": "12px"}),
                                                    _hover_help("Apenas visual: multiplica o tamanho das setas de velocidade no gráfico 2D (não altera a simulação)."),
                                                ]),
                                                dcc.Slider(id="vector_scale", min=0.0, max=2.5, step=0.05, value=1.0, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                html.Div([
                                                    html.Label("Escala vertical para 3D (z_scale)", style={"marginTop": "8px"}),
                                                    _hover_help("Apenas visual: escala o comprimento vertical dos vetores no 3D (proporcional ao módulo da velocidade)."),
                                                ]),
                                                dcc.Slider(id="z_scale", min=0.0, max=2.0, step=0.05, value=0.5, marks={}, tooltip=_SLIDER_TOOLTIP),
                                                html.Button("Rodar simulação", id="run", n_clicks=0, style={"marginTop": "10px"}),
                                                html.Div([
                                                    html.Button("Modo ao vivo: iniciar", id="live-toggle", n_clicks=0, style={"marginTop": "8px"}),
                                                    _hover_help("Executa 1 passo por tick usando dcc.Interval. Bom para ver a dinâmica em tempo real."),
                                                ]),
                                                html.Div(
                                                    [
                                                        html.Div([
                                                            html.Label("Intervalo do modo ao vivo (ms)", style={"marginTop": "8px"}),
                                                            _hover_help("Tempo entre ticks no modo ao vivo. Menor = mais fluido, porém pode pesar no navegador/CPU."),
                                                        ]),
                                                        dcc.Slider(
                                                            id="live-interval",
                                                            min=50,
                                                            max=2000,
                                                            step=50,
                                                            value=200,
                                                            marks={50: "50", 200: "200", 500: "500", 1000: "1000", 2000: "2000"},
                                                            tooltip=_SLIDER_TOOLTIP,
                                                        ),
                                                        html.Div(id="live-status", style={"fontSize": "0.85rem", "color": "#555"}),
                                                    ],
                                                    style={"marginTop": "6px"},
                                                ),
                                                html.Div(id="run-summary", style={"marginTop": "10px", "color": "#333"}),
                                            ],
                                            style={
                                                "width": "360px",
                                                "padding": "16px",
                                                "borderRight": "1px solid #ddd",
                                                "height": "calc(100vh - 58px)",
                                                "overflowY": "auto",
                                                "boxSizing": "border-box",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                dcc.Graph(id="timeseries"),
                                                html.Div(
                                                    [
                                                        html.Div([
                                                            html.Label("Passo de visualização"),
                                                            _hover_help("Escolhe qual passo do histórico será mostrado nos gráficos de campo (2D/3D). Não re-simula; só troca o frame exibido."),
                                                        ]),
                                                        dcc.Slider(
                                                            id="view_step",
                                                            min=0,
                                                            max=200,
                                                            step=1,
                                                            value=200,
                                                            marks={},
                                                            tooltip=_SLIDER_TOOLTIP,
                                                            updatemode="drag",
                                                        ),
                                                    ],
                                                    style={"padding": "0 16px"},
                                                ),
                                                dcc.Graph(id="field"),
                                                dcc.Graph(id="field-3d", style={"height": "40vh"}),
                                            ],
                                            style={"flex": "1", "height": "calc(100vh - 58px)", "overflowY": "auto"},
                                        ),
                                    ],
                                    style={"display": "flex"},
                                ),
                            ]),
                            dcc.Tab(label="Ajuda", value="tab-help", children=[
                                html.Div(
                                    [
                                        dcc.Markdown(
                                            r"""
### Fundamentos

$\displaystyle \frac{dX}{dt} = S(t) - H(t) + \eta(t)$

Nesta implementação:
- $S(t) \equiv \Phi_s$ (soma de contribuições com dE/dt ≥ 0)
- $H(t) \equiv \Phi_\sigma$ (soma de |dE/dt| das contribuições negativas)
- $X = \Phi_s - \Phi_\sigma$ (balanço líquido)

Use os sliders para ajustar ação (bomba), organização (atração), dissipação (viscosidade), ruído (η), acoplamento e regulador.
""",
                                            mathjax=True,
                                        )
                                    ],
                                    style={"padding": "16px"},
                                ),
                            ]),
                        ],
                    ),
                ]
            ),
        ],
        style={"fontFamily": "system-ui, -apple-system, Segoe UI, Roboto"},
    )

    @callback(
        Output("sim-data", "data"),
        Output("timeseries", "figure"),
        Output("view_step", "max"),
        Output("view_step", "value"),
        Output("run-summary", "children"),
        Input("run", "n_clicks"),
        Input("auto-run-interval", "n_intervals"),
        State("live-enabled", "data"),
        State("scenario", "value"),
        State("dt", "value"),
        State("steps", "value"),
        State("seed", "value"),
        State("points", "value"),
        State("pump_power", "value"),
        State("goal_k", "value"),
        State("viscosity_mu", "value"),
        State("barrier_k", "value"),
        State("barrier_radius", "value"),
        State("noise_sigma", "value"),
        State("coupling_alpha", "value"),
        State("coupling_length", "value"),
        State("regulator_gain", "value"),
        State("entropy_force_mag", "value"),
        State("entropy_force_angle", "value"),
        State("syntropy_wave_gain", "value"),
        State("syntropy_wave_k", "value"),
        State("syntropy_wave_omega", "value"),
        State("toggles", "value"),
        prevent_initial_call=False,
    )
    def on_run(
        n_clicks: int,
        auto_run_ticks: int,
        live_enabled: bool,
        scenario: ScenarioId,
        dt,
        steps,
        seed,
        points,
        pump_power,
        goal_k,
        viscosity_mu,
        barrier_k,
        barrier_radius,
        noise_sigma,
        coupling_alpha,
        coupling_length,
        regulator_gain,
        entropy_force_mag,
        entropy_force_angle,
        syntropy_wave_gain,
        syntropy_wave_k,
        syntropy_wave_omega,
        toggles,
    ) -> tuple[dict, go.Figure, int, int, html.Div]:
        steps_i = max(1, _coerce_int(steps, 200))
        dt_f = _coerce_float(dt, 0.05)
        seed_i = None if seed is None else _coerce_int(seed, 0)
        points_i = max(2, _coerce_int(points, SCENARIOS[str(scenario)].default_points if scenario in SCENARIOS else 20))
        live_enabled = bool(live_enabled)
        trigger = ctx.triggered_id
        if trigger == "auto-run-interval" and not live_enabled:
            raise PreventUpdate

        toggles = toggles or []
        params = {
            "pump_power": _coerce_float(pump_power, 0.10),
            "goal_k": _coerce_float(goal_k, 0.50),
            "viscosity_mu": _coerce_float(viscosity_mu, 0.05),
            "barrier_k": _coerce_float(barrier_k, 0.20),
            "barrier_radius": _coerce_float(barrier_radius, 0.50),
            "noise_sigma": _coerce_float(noise_sigma, 0.05),
            "coupling_alpha": _coerce_float(coupling_alpha, 0.00),
            "coupling_length": _coerce_float(coupling_length, 0.75),
            "regulator_gain": _coerce_float(regulator_gain, 0.20),
            "entropy_force_mag": _coerce_float(entropy_force_mag, 0.20),
            "entropy_force_angle": _coerce_float(entropy_force_angle, 0.0),
            "syntropy_wave_gain": _coerce_float(syntropy_wave_gain, _coerce_float(regulator_gain, 0.20)),
            "syntropy_wave_k": _coerce_float(syntropy_wave_k, 2.0),
            "syntropy_wave_omega": _coerce_float(syntropy_wave_omega, 1.0),
            "include_noise": "noise" in toggles,
            "include_coupling": "coupling" in toggles,
            "include_regulator": "regulator" in toggles,
        }

        integrate_positions = "kinematics" in toggles

        # Manual run: compute full series.
        if trigger != "auto-run-interval":
            # Reset server-side live runtime.
            _LIVE_RUNTIME["config_key"] = None
            _LIVE_RUNTIME["flow"] = None
            _LIVE_RUNTIME["metrics"] = []
            _LIVE_RUNTIME["positions"] = []
            _LIVE_RUNTIME["velocities"] = []
            _LIVE_RUNTIME["internal_energy"] = []

            result = run_simulation(
                scenario=scenario,
                dt=dt_f,
                steps=steps_i,
                seed=seed_i,
                points=points_i,
                params=params,
                integrate_positions=integrate_positions,
            )
            data = _serialize_result(result)
            fig = _figure_timeseries(data["metrics"])
            current_step = steps_i
        else:
            # Live tick: advance one step in a server-side runtime (keeps RNG/process state continuous).
            config_key = _live_config_key(
                scenario=str(scenario),
                dt=dt_f,
                points=points_i,
                seed=seed_i,
                params=params,
                integrate_positions=integrate_positions,
            )

            if _LIVE_RUNTIME["flow"] is None or _LIVE_RUNTIME["config_key"] != config_key:
                from .scenarios import build_flow

                flow = build_flow(scenario=scenario, seed=seed_i, points=points_i, params=params)
                _LIVE_RUNTIME["config_key"] = config_key
                _LIVE_RUNTIME["flow"] = flow
                _LIVE_RUNTIME["metrics"] = []
                _LIVE_RUNTIME["positions"] = []
                _LIVE_RUNTIME["velocities"] = []
                _LIVE_RUNTIME["internal_energy"] = []

                # Snapshot step 0.
                system = flow.system
                _LIVE_RUNTIME["positions"].append([p.position.tolist() for p in system.points])
                _LIVE_RUNTIME["velocities"].append([p.velocity.tolist() for p in system.points])
                _LIVE_RUNTIME["internal_energy"].append([float(p.internal_energy) for p in system.points])

            flow = _LIVE_RUNTIME["flow"]
            m = flow.step(dt_f)
            update_monitor = getattr(flow, "_update_monitor", None)
            if callable(update_monitor):
                update_monitor(m)

            if integrate_positions:
                for p in flow.system.points:
                    p.position = p.position + dt_f * p.velocity

            _LIVE_RUNTIME["metrics"].append(m)
            _LIVE_RUNTIME["positions"].append([p.position.tolist() for p in flow.system.points])
            _LIVE_RUNTIME["velocities"].append([p.velocity.tolist() for p in flow.system.points])
            _LIVE_RUNTIME["internal_energy"].append([float(p.internal_energy) for p in flow.system.points])

            data = {
                "metrics": [asdict(mm) for mm in _LIVE_RUNTIME["metrics"]],
                "positions": _LIVE_RUNTIME["positions"],
                "velocities": _LIVE_RUNTIME["velocities"],
                "internal_energy": _LIVE_RUNTIME["internal_energy"],
            }
            fig = _figure_timeseries(data["metrics"])
            current_step = len(_LIVE_RUNTIME["metrics"])

        last = data["metrics"][-1] if data["metrics"] else {}
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        live_mode = "Modo ao vivo" if trigger == "auto-run-interval" else "Execução manual"
        summary_lines = [
            html.Div(f"{live_mode} • último disparo: {timestamp}"),
            html.Div(f"Cenário: {SCENARIOS[scenario].title}"),
            html.Div(
                f"Último passo: X={last.get('x', 0.0):.4f}  dX/dt={last.get('dx_dt', 0.0):.4f}  E_total={last.get('total_energy', 0.0):.4f}"
            ),
            html.Div(f"Passos simulados: {steps_i}"),
        ]
        if trigger == "auto-run-interval":
            summary_lines.append(html.Div(f"Ticks ao vivo: {auto_run_ticks or 0}"))
        summary = html.Div(summary_lines)

        view_max = max(0, current_step)
        view_value = max(0, min(view_max, current_step))
        return data, fig, view_max, view_value, summary

    @callback(Output("scenario-desc", "children"), Input("scenario", "value"))
    def on_scenario_change(scenario: ScenarioId):
        preset = SCENARIOS[scenario]
        return html.Div([
            html.Strong(preset.title),
            html.Div(preset.description),
        ])

    @callback(
        Output("live-enabled", "data"),
        Output("live-toggle", "children"),
        Output("auto-run-interval", "disabled"),
        Input("live-toggle", "n_clicks"),
        State("live-enabled", "data"),
    )
    def toggle_live_mode(n_clicks: int, live_enabled: bool):
        enabled = bool(live_enabled)
        if n_clicks is None or n_clicks == 0:
            return False, "Modo ao vivo: iniciar", True
        enabled = not enabled
        return enabled, (
            "Modo ao vivo: parar" if enabled else "Modo ao vivo: iniciar"
        ), not enabled

    @callback(
        Output("auto-run-interval", "interval"),
        Input("live-interval", "value"),
    )
    def update_auto_interval(interval_ms):
        return max(50, _coerce_int(interval_ms, 200))

    @callback(
        Output("control-preset-desc", "children"),
        Output("dt", "value"),
        Output("pump_power", "value"),
        Output("viscosity_mu", "value"),
        Output("noise_sigma", "value"),
        Output("coupling_alpha", "value"),
        Output("entropy_force_mag", "value"),
        Output("entropy_force_angle", "value"),
        Output("syntropy_wave_gain", "value"),
        Output("syntropy_wave_k", "value"),
        Output("syntropy_wave_omega", "value"),
        Output("live-interval", "value"),
        Output("toggles", "value"),
        Input("control-preset", "value"),
        prevent_initial_call=False,
    )
    def apply_control_preset(preset_id: str):
        preset = CONTROL_PRESETS.get(preset_id) or CONTROL_PRESETS["balanced_live"]
        values = preset["values"]
        desc = html.Div([
            html.Strong(preset["label"]),
            html.Div(preset["description"]),
        ])

        return (
            desc,
            float(values.get("dt", 0.05)),
            float(values.get("pump_power", 0.10)),
            float(values.get("viscosity_mu", 0.05)),
            float(values.get("noise_sigma", 0.05)),
            float(values.get("coupling_alpha", 0.00)),
            float(values.get("entropy_force_mag", 0.20)),
            float(values.get("entropy_force_angle", 0.0)),
            float(values.get("syntropy_wave_gain", 0.20)),
            float(values.get("syntropy_wave_k", 2.0)),
            float(values.get("syntropy_wave_omega", 1.0)),
            int(values.get("live_interval", 200)),
            list(values.get("toggles", ["noise", "regulator", "kinematics"])),
        )

    @callback(
        Output("live-status", "children"),
        Input("live-enabled", "data"),
        Input("live-interval", "value"),
    )
    def live_status_message(live_enabled, interval_ms):
        live_enabled = bool(live_enabled)
        interval_ms = _coerce_int(interval_ms, 500)
        if live_enabled:
            return f"Modo ao vivo ativo • intervalo {interval_ms} ms"
        return "Modo ao vivo desativado"

    @callback(
        Output("field", "figure"),
        Input("sim-data", "data"),
        Input("view_step", "value"),
        Input("vector_scale", "value"),
    )
    def on_field(data: dict | None, view_step: int, vector_scale):
        if not data:
            fig = go.Figure()
            fig.update_layout(title="Run a simulation to see the field")
            return fig

        vector_scale_f = _coerce_float(vector_scale, 1.0)

        step = _coerce_int(view_step, 0)
        step = max(0, min(step, len(data["positions"]) - 1))

        positions = data["positions"][step]
        velocities = data["velocities"][step]
        energy = data["internal_energy"][step]

        return _figure_field(
            positions=positions,
            velocities=velocities,
            energy=energy,
            vector_scale=vector_scale_f,
        )

    @callback(
        Output("field-3d", "figure"),
        Input("sim-data", "data"),
        Input("view_step", "value"),
        Input("vector_scale", "value"),
        Input("z_scale", "value"),
    )
    def on_field_3d(data: dict | None, view_step: int, vector_scale, z_scale):
        if not data:
            fig = go.Figure()
            fig.update_layout(title="Run a simulation to see the 3D field")
            return fig

        vector_scale_f = _coerce_float(vector_scale, 1.0)
        z_scale_f = _coerce_float(z_scale, 0.5)

        step = _coerce_int(view_step, 0)
        step = max(0, min(step, len(data["positions"]) - 1))

        positions = data["positions"][step]
        velocities = data["velocities"][step]
        energy = data["internal_energy"][step]

        return _figure_field_3d(
            positions=positions,
            velocities=velocities,
            energy=energy,
            vector_scale=vector_scale_f,
            z_scale=z_scale_f,
        )

    return app


def main() -> None:
    app = create_app()
    # On Windows, the reloader can spawn/exit quickly and look like a crash.
    # Keep a single stable process for local validation.
    app.run(debug=False, use_reloader=False, host="127.0.0.1", port=8050)


if __name__ == "__main__":
    main()
