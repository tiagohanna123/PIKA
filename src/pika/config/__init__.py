"""Configuration surface for PIKA.

This package intentionally owns the name ``pika.config``.

It includes:
- System identity configuration (see :mod:`pika.config.system`)
- Simulation defaults (see :mod:`pika.config.simulation`)
"""

from .simulation import SimulationConfig, resolve_seed

__all__ = ["SimulationConfig", "resolve_seed"]

