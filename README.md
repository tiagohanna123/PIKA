# PIKA System Framework

Identity is volatile; configure the system name, description, version, and symbol once via environment variables:

```bash
export PIKA_SYSTEM_ID="MySystem"
export PIKA_SYSTEM_DESCRIPTION="Experimental field"
export PIKA_SYSTEM_VERSION="0.2.0"
export PIKA_SYSTEM_SYMBOL="Ψ"
```

## Layout
- `src/pika/identity.py`: single source of system identity (env + fallback)
- `src/pika/config.py`: simulation defaults (dt, steps, seed)
- `src/pika/core.py`: points and system container
- `src/pika/process.py`: process plugins (viscosity, goal attraction, barriers, pumps, coupling, noise, regulator)
- `src/pika/flow.py`: ΦS, Φσ, X, dX/dt accounting
- `src/pika/integrator.py`: semi-implicit Euler + RK2 option
- `src/pika/geometry.py`: density/curvature proxies and trajectory recording
- `src/pika/preview/`: info (logs/JSON/CSV) + geo (plots) + version text preview
- `examples/`: runnable demos
- `tests/`: regression tests
- `docs/model.md`: concise model description

## Quickstart (info preview)
```bash
PYTHONPATH=src python -m pika.preview.info --dt 0.05 --steps 50 --out report.json --csv report.csv
```
Printed lines include identity, final X and dX/dt, and the tail of the metrics table. JSON/CSV capture the full history.

## Geometric preview
```bash
PYTHONPATH=src python -m pika.preview.geo --dt 0.02 --steps 200 --save frames/final.png
```
Generates a trajectory plot with scatter/quiver overlays. The file is created under `frames/` by default.

## Deterministic version preview
```bash
PYTHONPATH=src python -m pika.preview.version --dt 0.05 --steps 5
```
Renders a table of per-point energies and instantaneous dE/dt signatures using the configured identity.

## Examples
- `examples/demo_info.py`: runs the info preview
- `examples/demo_geo_2d.py`: produces the geometric PNG
- `examples/demo_x_tends_to_zero.py`: shows |X| decaying via feedback regulation

## Testing
```bash
PYTHONPATH=src pytest
```
