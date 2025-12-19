# Pika Model (current snapshot)

- Systems are fields of points with position, velocity, and internal energy.
- Processes act locally, injecting or dissipating power and steering velocity.
- Flow aggregates concurrent processes; ΦS sums syntropic rates (dE/dt ≥ 0), Φσ sums magnitudes of entrópico rates (dE/dt < 0), and X = ΦS − Φσ.
- Integration advances positions/energies while recording X and dX/dt to illustrate asymptotic regulation (X tends toward 0 without forcing equilibrium).
- Geometry utilities compute densities/curvature proxies and expose trajectories for plotting.
