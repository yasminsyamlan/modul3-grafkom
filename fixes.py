"""Module 3 -- Lab 2 step 5: pitfall-driven fixes, each with a number.

  1. back-face culling      -> how many triangles / how much time it saves
  2. reverse-Z + float depth -> smallest resolvable depth gap vs distance
  3. normal matrix (M^-T)    -> normals stay perpendicular under non-uniform scale

Run:  python fixes.py
"""
from __future__ import annotations

import time

import numpy as np

from objio import load_obj
from ppm_io import read_ppm
from raster3d import render
from transforms import perspective, look_at, rot_y, scale, project


def backface_culling():
    mesh = load_obj(__import__("config").MODEL)
    tex = read_ppm(__import__("config").TEX)
    model = rot_y(35) @ scale((1.4, 1.4, 1.4))
    kw = dict(w=256, h=256, tex_u8=tex, model=model)
    t0 = time.perf_counter(); a, _, fa = render(mesh, cull_back=False, **kw); ta = time.perf_counter() - t0
    t0 = time.perf_counter(); b, _, fb = render(mesh, cull_back=True, **kw); tb = time.perf_counter() - t0
    # count back-facing triangles from signed screen-space area
    P = perspective(45, 1.0, 1.0, 14.0); V = look_at((2.6, 2.0, 3.4), (0, 0.7, 0))
    _, ndc = project(P, V, model, mesh.positions)
    s = ndc[mesh.faces][:, :, :2]
    area = (s[:, 1, 0] - s[:, 0, 0]) * (s[:, 2, 1] - s[:, 0, 1]) - (s[:, 1, 1] - s[:, 0, 1]) * (s[:, 2, 0] - s[:, 0, 0])
    back = int((area < 0).sum())            # NDC y is up here, so CCW (front) has area > 0
    print("[1] back-face culling")
    print(f"    triangles: {mesh.n_tris}   back-facing (culled): {back} ({100*back/mesh.n_tris:.0f}%)")
    print(f"    time: {ta*1000:.0f} ms -> {tb*1000:.0f} ms   image identical: {np.array_equal(a, b)}")


def depth_precision():
    n, f = 0.01, 1000.0
    print("[2] depth precision, near=0.01 far=1000 (smallest resolvable gap, metres)")
    print(f"    {'dist':>6} {'int24 std-Z':>14} {'float32 std-Z':>15} {'float32 reverse-Z':>19}")
    for d in (1, 10, 100, 500):
        # NDC-ish depth in [0,1]: standard d01 = f(d-n)/(d(f-n)); reverse = 1 - that
        def z01(x): return f * (x - n) / (x * (f - n))
        step_int = 1.0 / (2 ** 24 - 1)
        dz = z01(d + 1e-3) - z01(d - 1e-3)             # d(depth)/d(dist) numerically
        slope = abs(dz) / 2e-3
        gap_int = step_int / slope
        zs = np.float32(z01(d)); gap_f = float(np.spacing(zs)) / slope
        zr = np.float32(1.0 - z01(d)); gap_r = float(np.spacing(zr)) / slope
        print(f"    {d:6d} {gap_int:14.2e} {gap_f:15.2e} {gap_r:19.2e}")
    print("    reverse-Z: near->1, far->0 and a float buffer; float spacing is finest near 0,")
    print("    exactly where the 1/z mapping is coarsest (far) -> the two crushes cancel.")


def normal_matrix():
    M = scale((3.0, 1.0, 1.0))                      # non-uniform scale
    tangent = np.array([1.0, 1.0, 0.0]); normal = np.array([1.0, -1.0, 0.0])  # n . t = 0
    t2 = (M[:3, :3] @ tangent)
    n_bad = M[:3, :3] @ normal
    n_good = np.linalg.inv(M[:3, :3]).T @ normal
    print("[3] normal matrix under scale(3,1,1)")
    print(f"    n.t before: {normal @ tangent:.3f}")
    print(f"    after, n' = M n        : n'.t' = {n_bad @ t2:7.3f}   (NOT perpendicular)")
    print(f"    after, n' = M^-T n     : n'.t' = {n_good @ t2:7.3f}   (perpendicular)")
    L = np.array([1.0, 1.0, 0.0]) / np.sqrt(2)
    for lab, n in (("M n", n_bad), ("M^-T n", n_good)):
        n = n / np.linalg.norm(n); print(f"    Lambert N.L with {lab:7s}: {max(0.0, n @ L):.3f}")


if __name__ == "__main__":
    backface_culling(); print(); depth_precision(); print(); normal_matrix()
