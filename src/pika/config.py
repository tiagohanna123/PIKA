"""Compatibility shim for historical imports.

The canonical configuration package is :mod:`pika.config`.
This module remains to avoid breaking older references but should not be
used for new code.
"""

from __future__ import annotations

from pika.config.simulation import SimulationConfig, resolve_seed

__all__ = ["SimulationConfig", "resolve_seed"]
