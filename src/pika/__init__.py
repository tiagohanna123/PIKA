"""Pika modeling framework with configurable system identity."""
from .identity import identity, SystemIdentity
from .config import SimulationConfig
from .core import Point, System
from .process import Process
from .flow import Flow
from .integrator import Integrator

__all__ = [
    "identity",
    "SystemIdentity",
    "SimulationConfig",
    "Point",
    "System",
    "Process",
    "Flow",
    "Integrator",
]
"""Pika system modeling framework.

This package provides a modular foundation for simulating energy-driven
systems. The naming of the system is configurable via
:mod:`pika.config.system` to avoid hardcoding identities.
"""

from .config.system import SystemIdentity, system_identity

__all__ = ["SystemIdentity", "system_identity"]
