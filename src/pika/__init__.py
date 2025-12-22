"""PIKA system modeling framework.

This package includes:
- A legacy simulation engine (System/Flow/Integrator, etc.) used by tests and demos.
- A newer modular layer under subpackages (core/, flow/, integrator/, process/).
- A web portal under :mod:`pika.portal`.

System identity for the modular layer is configured via :mod:`pika.config.system`.
"""

from .config import SimulationConfig, resolve_seed
from .config.system import SystemIdentity, system_identity
from .core import Point, System
from .flow import Flow
from .identity import identity
from .integrator import Integrator
from .process import Process

__all__ = [
    "SimulationConfig",
    "resolve_seed",
    "SystemIdentity",
    "system_identity",
    "identity",
    "Point",
    "System",
    "Process",
    "Flow",
    "Integrator",
]
