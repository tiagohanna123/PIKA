"""Interactive portal (web UI) for running and visualizing PIKA simulations."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from dash import Dash


def create_app() -> "Dash":
	# Lazy import to avoid side effects during package import.
	from .app import create_app as _create_app

	return _create_app()


__all__ = ["create_app"]
