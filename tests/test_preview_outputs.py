from pika.preview.info import run_preview
from pika.config import SimulationConfig


def test_preview_runs():
    report = run_preview(SimulationConfig(dt=0.01, steps=5, seed=0))
    assert "history" in report
    assert len(report["history"]) == 5
