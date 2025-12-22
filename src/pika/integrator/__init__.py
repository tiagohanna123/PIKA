"""Time integration.

``pika.integrator`` is a package; re-export the legacy Integrator used by
tests and preview CLIs.
"""

from .legacy import Integrator, rk2, semi_implicit_euler

__all__ = ["Integrator", "semi_implicit_euler", "rk2"]

