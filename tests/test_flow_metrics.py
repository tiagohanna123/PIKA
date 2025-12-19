import numpy as np
from pika.core import System
from pika.flow import Flow
from pika.process import Viscosity


def test_dx_dt_computed():
    system = System(dimension=2)
    system.add_point([0, 0], [1.0, 0], energy=0.0)
    flow = Flow(system=system, processes=[Viscosity(mu=0.2)])
    m1 = flow.step(0.1)
    m2 = flow.step(0.1)
    assert m2.dx_dt != 0
