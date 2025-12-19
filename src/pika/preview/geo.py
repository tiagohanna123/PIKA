"""Geometric preview producing plots."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List
import numpy as np
import struct
import zlib

from ..identity import identity
from ..config import SimulationConfig
from ..core import System
from ..process import default_processes, NoiseExploration
from ..flow import Flow
from ..integrator import Integrator
from ..geometry import TrajectoryRecorder


def build_geo_flow(seed: int | None = None) -> tuple[Flow, TrajectoryRecorder]:
    rng = np.random.default_rng(seed)
    system = System(dimension=2)
    for _ in range(20):
        system.add_point(rng.uniform(-1, 1, size=2), rng.normal(0, 0.4, size=2), energy=0.3)
    goal = np.array([0.4, -0.2])
    processes = default_processes(goal=goal)
    processes.append(NoiseExploration(sigma=0.08, rng=lambda: rng.normal(0, 1, size=2)))
    flow = Flow(system=system, processes=processes)
    recorder = TrajectoryRecorder.for_system(system)
    return flow, recorder


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack("!I", len(data))
        + tag
        + data
        + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def _write_png(image: np.ndarray, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    height, width = len(image), len(image[0])
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw_rows = []
    for row in image:
        packed = bytearray()
        for pixel in row:
            packed.extend(int(c) & 0xFF for c in pixel)
        raw_rows.append(bytes(packed))
    raw_data = b"".join(b"\x00" + r for r in raw_rows)
    compressed = zlib.compress(raw_data, 9)
    with output.open("wb") as f:
        f.write(signature)
        f.write(_png_chunk(b"IHDR", ihdr))
        f.write(_png_chunk(b"IDAT", compressed))
        f.write(_png_chunk(b"IEND", b""))


def _draw_line(canvas: np.ndarray, p0: tuple[int, int], p1: tuple[int, int], color: tuple[int, int, int]) -> None:
    x0, y0 = p0
    x1, y1 = p1
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        if 0 <= x0 < len(canvas[0]) and 0 <= y0 < len(canvas):
            canvas[y0][x0] = list(color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def render_plot(recorder: TrajectoryRecorder, flow: Flow, output: Path) -> None:
    traces = recorder.as_arrays()
    all_positions = [p.position for p in flow.system.points]
    for trace in traces:
        all_positions.extend(trace)
    if not all_positions:
        return
    coords = np.array(all_positions)
    mins = coords.min(axis=0)
    maxs = coords.max(axis=0)
    span = np.maximum(maxs - mins, 1e-6)
    size = 512

    def to_pixel(point: np.ndarray) -> tuple[int, int]:
        norm = (point - mins) / span
        x = int(np.clip(norm[0], 0, 1) * (size - 1))
        y = int(np.clip(1 - norm[1], 0, 1) * (size - 1))
        return x, y

    canvas = [[[255, 255, 255] for _ in range(size)] for _ in range(size)]
    for trace in traces:
        pixels = [to_pixel(pt) for pt in trace]
        for start, end in zip(pixels[:-1], pixels[1:]):
            _draw_line(canvas, start, end, (180, 180, 180))
        if pixels:
            x, y = pixels[-1]
            canvas[y][x] = [50, 100, 200]

    velocities = [p.velocity for p in flow.system.points]
    for pt, vel in zip(flow.system.points, velocities):
        base = np.array(to_pixel(pt.position))
        target = base + np.array([int(vel[0] * 10), int(-vel[1] * 10)])
        target = np.clip(target, 0, size - 1)
        _draw_line(canvas, tuple(base), tuple(target), (30, 30, 30))

    header_text = f"{identity.id} v{identity.version}"[:50]
    for idx, _ch in enumerate(header_text):
        start = idx * 6
        if start + 6 >= size:
            break
        for y in range(5, min(8, size)):
            for x in range(start, min(start + 5, size)):
                canvas[y][x] = [240, 240, 240]

    _write_png(canvas, output)


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Geometric preview with trajectories and velocities")
    parser.add_argument("--dt", type=float, default=0.02)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--save", type=Path, default=None, help="Output image path (alias for --out)")
    parser.add_argument("--out", type=Path, default=Path("frames/final.png"), help="Output image path")
    args = parser.parse_args(argv)

    output = args.save or args.out
    config = SimulationConfig(dt=args.dt, steps=args.steps, seed=None)
    flow, recorder = build_geo_flow(seed=config.seed)
    integrator = Integrator(flow=flow, dt=config.dt, steps=config.steps)

    metrics = integrator.run()
    for _ in metrics:
        recorder.capture(flow.system)

    render_plot(recorder, flow, output)
    print(f"Saved geometric preview to {output}")


if __name__ == "__main__":
    main()
