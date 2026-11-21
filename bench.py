"""Module 3 -- Lab 3 step 3: rasterisation vs ray tracing, predict THEN measure.

Writes your PREDICTION first (edit PRED below before running), then times both
renderers at several resolutions and adds a HARD SHADOW to the ray tracer.
(A rasteriser needs a shadow map for the same effect -- left as an extension.)

Run:  python bench.py
"""
from __future__ import annotations

import os
import time

import numpy as np

from objio import load_obj
from ppm_io import read_ppm, write_ppm
from transforms import rot_y, scale
import raster3d
import raytrace

PRED = {"raster_over_rt_time_ratio": 0.2,          # <- your prediction: t_raster / t_raytrace
        "better_shadow_reflection": "raytrace"}     # <- and why, in your report


def t(fn, reps=2):
    best = 1e9
    for _ in range(reps):
        s = time.perf_counter(); fn(); best = min(best, time.perf_counter() - s)
    return best


def main():
    mesh = load_obj(__import__("config").MODEL)
    tex = read_ppm(__import__("config").TEX)
    model = rot_y(35) @ scale((1.4, 1.4, 1.4))
    print(f"triangles: {mesh.n_tris}   prediction: {PRED}\n")
    print(f"{'res':>9} {'raster ms':>10} {'raytrace ms':>12} {'RT+shadow ms':>13} {'raster/RT':>10}")
    for n in (64, 128, 256):
        a = t(lambda: raster3d.render(mesh, w=n, h=n, tex_u8=tex, model=model, cull_back=True))
        b = t(lambda: raytrace.render(mesh, w=n, h=n, tex_u8=tex, model=model))
        c = t(lambda: raytrace.render(mesh, w=n, h=n, tex_u8=tex, model=model, shadow=True), reps=1)
        print(f"{n:>4}x{n:<4} {a*1e3:10.0f} {b*1e3:12.0f} {c*1e3:13.0f} {a/b:10.2f}")
    LD = (0.9, 0.35, 0.5)      # low, oblique sun so the tier shadows are long enough to see
    img0, _ = raytrace.render(mesh, w=256, h=256, tex_u8=tex, model=model, light_dir=LD)
    img1, _ = raytrace.render(mesh, w=256, h=256, tex_u8=tex, model=model, light_dir=LD, shadow=True)
    os.makedirs("out", exist_ok=True)
    write_ppm("out/temple_rt_shadow.ppm", img1)
    dark = (img1.astype(int).sum(2) < img0.astype(int).sum(2) - 30).sum()
    print(f"\nhard shadow darkens {dark} pixels ({100*dark/img0.shape[0]/img0.shape[1]:.1f}% of frame)")
    print("wrote out/temple_rt_shadow.ppm")
    print("\nReconcile in the report: why the ratio differs from your prediction; where the")
    print("choice flips (many triangles -> raster+BVH-less RT is O(pixels*tris); RT cores; GI).")


if __name__ == "__main__":
    main()
