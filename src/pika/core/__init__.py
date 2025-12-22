"""Core types.

The name ``pika.core`` is a package (not the legacy flat module).
We re-export the legacy engine's ``Point`` and ``System`` here so that
imports like ``from pika.core import System`` keep working.
"""

from .legacy import Point, System

__all__ = ["Point", "System"]

