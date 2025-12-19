"""Demonstrate regulation nudging X toward zero without forcing equilibrium."""
from pika.preview.info import run_preview
from pika.config import SimulationConfig

if __name__ == "__main__":
    report = run_preview(SimulationConfig(dt=0.05, steps=100, seed=42))
    print(report["history"][-5:])
