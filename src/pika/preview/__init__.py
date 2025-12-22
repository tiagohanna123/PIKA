"""Preview utilities.

This package hosts lightweight diagnostics (CLI helpers, plots, etc.).

Keep this module import-side-effect-free: consumers should import the
specific preview they need (e.g. :mod:`pika.preview.info`) rather than
loading everything at package import time.
"""

__all__: list[str] = []
