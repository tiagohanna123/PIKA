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

## Interactive portal (web)
Run the portal locally and interact with simulations in the browser:

```bash
pip install -e .
pika-portal
```

Then open `http://127.0.0.1:8050/`.

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
This repository hosts an extensible Python framework for modeling energy-driven systems. The system identity is configurable through environment variables, ensuring the name remains flexible as the project evolves.

## Configuration
Set the system identity without touching code:

```bash
export PIKA_SYSTEM_ID="MySystem"
export PIKA_SYSTEM_DESCRIPTION="Experimental energy field"
export PIKA_SYSTEM_VERSION="0.1.0"
```

## Modules
- **config**: centralized system identity (`SystemIdentity`, `system_identity`).
- **core**: foundational types for points and state tracking.
- **process**: local transformations that express dE/dt contributions.
- **flow**: orchestration layer combining processes across the field.
- **integrator**: time marching utilities prepared for higher-order schemes.
- **geometry**: spatial scaffolding to seed and arrange points.

## Quickstart
```python
from pika.config.system import system_identity
from pika.geometry.space import EuclideanSpace
from pika.process.base import LinearEnergyProcess
from pika.flow.field import FlowField
from pika.integrator.stepper import FixedStepIntegrator
from pika.preview import generate_version_preview

space = EuclideanSpace(dimension=2)
points = space.seed_points(coordinates=[(0.0, 0.0), (1.0, 0.0)])
processes = [LinearEnergyProcess(slope=0.2), LinearEnergyProcess(slope=-0.05)]
field = FlowField(points=points, processes=processes)
integrator = FixedStepIntegrator(flow=field, dt=0.1)

print(f"Operating system: {system_identity.id}")
integrator.run(steps=5)
print([p.state.energy() for p in points])

# Lightweight preview that highlights how this version evolves energy
preview = generate_version_preview(dt=0.05, steps=3)
print(preview.as_dict())

# Text visualization for quick inspection
from pika.preview.version import render_preview
print(render_preview(preview))
```

### Command-line preview visualization
Generate a text-based visualization without writing any code:

```bash
PYTHONPATH=src python -m pika.preview.version --dt 0.05 --steps 5
```

This uses the configured system identity (via environment variables) and prints
a table with energies and dE/dt signatures per step so you can compare
different versions side by side.
