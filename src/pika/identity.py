"""Configurable system identity.

The system name is volatile by design. Identity is loaded from environment
variables with a single file fallback so renaming the system never requires
code changes elsewhere.
"""
from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_SYSTEM_ID = "Pika-System"
DEFAULT_SYSTEM_DESCRIPTION = "Energy-driven system field"
DEFAULT_SYSTEM_VERSION = "0.0.0"
DEFAULT_SYSTEM_SYMBOL = "πκ"


@dataclass(frozen=True)
class SystemIdentity:
    """Immutable descriptor for the modeled system."""

    id: str
    description: str
    version: str
    symbol: str

    @classmethod
    def load(cls) -> "SystemIdentity":
        """Load identity from environment with safe fallbacks.

        Centralizing this logic guarantees that every module reads the
        same identity without duplicating environment lookups.
        """

        return cls(
            id=os.getenv("PIKA_SYSTEM_ID", DEFAULT_SYSTEM_ID),
            description=os.getenv("PIKA_SYSTEM_DESCRIPTION", DEFAULT_SYSTEM_DESCRIPTION),
            version=os.getenv("PIKA_SYSTEM_VERSION", DEFAULT_SYSTEM_VERSION),
            symbol=os.getenv("PIKA_SYSTEM_SYMBOL", DEFAULT_SYSTEM_SYMBOL),
        )


identity = SystemIdentity.load()
