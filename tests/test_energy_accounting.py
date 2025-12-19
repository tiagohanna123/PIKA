import numpy as np
from pika.core import System
from pika.flow import Flow
from pika.process import InternalPump


def test_energy_signs():
    system = System(dimension=2)
    system.add_point([0, 0], [0, 0], energy=0.0)
    flow = Flow(system=system, processes=[InternalPump(power=1.0)])
    metrics = flow.step(dt=0.1)
    assert metrics.phi_s > 0
    assert metrics.phi_sigma == 0
    assert metrics.total_energy > 0
