"""System identity configuration.

The system name is intentionally centralized here to avoid hardcoding
volatile nomenclature across the codebase. Downstream modules should
import :data:`system_identity` instead of embedding strings, enabling
simple renaming or contextual switching of the modeled system.
"""
from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class SystemIdentity:
    """Immutable descriptor for the modeled system.

    Attributes
    ----------
    id: str
        Primary identifier for the system. Defaults to the environment
        variable ``PIKA_SYSTEM_ID`` or ``"Pika"`` when unset.
    description: str
        Optional human-readable context for logging or visual outputs.
    version: str
        Semantic tag for the current configuration. Defaults to the
        environment variable ``PIKA_SYSTEM_VERSION`` or ``"0.0.0"`` when
        unset.
    """

    id: str
    description: str = ""
    version: str = "0.0.0"

    @classmethod
    def from_environment(cls) -> "SystemIdentity":
        """Create an identity sourced from environment variables.

        Centralizing this lookup avoids duplicated logic and keeps
        renaming a single-step operation.
        """

        system_id = os.getenv("PIKA_SYSTEM_ID", "Pika")
        system_description = os.getenv("PIKA_SYSTEM_DESCRIPTION", "")
        system_version = os.getenv("PIKA_SYSTEM_VERSION", "0.0.0")
        return cls(id=system_id, description=system_description, version=system_version)


# Single, shared identity instance used across the framework.
system_identity = SystemIdentity.from_environment()
