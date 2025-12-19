"""Pika system modeling framework.

This package provides a modular foundation for simulating energy-driven
systems. The naming of the system is configurable via
:mod:`pika.config.system` to avoid hardcoding identities.
"""

from .config.system import SystemIdentity, system_identity

__all__ = ["SystemIdentity", "system_identity"]
