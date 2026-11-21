"""Module 3 -- Lab 2 step 3: perspective-correct vs naive UV (Example E4), rendered.

A checkerboard floor receding to the horizon. Naive (screen-linear) UV makes the
checks the same size on screen all the way back -> the floor 'swims' / bends at
the diagonal; perspective-correct (u/w, 1/w, divide) shrinks them with 1/z.

Run:  python perspective_demo.py
"""
from __future__ import annotations

import os

import numpy as np

from objio import Mesh
from ppm_io import write_ppm
from raster3d import render
from metrics import ssim, psnr


def checker(n=256, cells=8):
    y, x = np.mgrid[0:n, 0:n]
    c = (((x * cells // n) + (y * cells // n)) % 2).astype(np.uint8)
    return np.repeat((60 + 180 * c)[..., None], 3, axis=2).astype(np.uint8)


def e4_numbers():
    """Closed-form E4: wL=1, wR=9, screen midpoint."""
    wl, wr, ul, ur = 1.0, 9.0, 0.0, 1.0
    naive = 0.5 * (ul + ur)
    num = 0.5 * (ul / wl + ur / wr)
    den = 0.5 * (1 / wl + 1 / wr)
    return naive, num / den


def main():
    naive, pc = e4_numbers()
    print(f"E4 midpoint u: naive = {naive:.2f}   perspective-correct = {pc:.2f}")
    pos = np.array([[-3, -1, -1.5], [3, -1, -1.5], [3, -1, -30], [-3, -1, -30]], float)
    uv = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
    # uv scaled so the floor repeats a few times
    uv = uv * np.array([1.0, 1.0])
    mesh = Mesh(pos, uv, [[0, 1, 2], [0, 2, 3]], [[0, 1, 2], [0, 2, 3]])
    tex = checker()
    kw = dict(w=256, h=256, tex_u8=tex, near=1.0, far=60.0, fovy=60.0,
              eye=(0, 0, 0), center=(0, -0.2, -1), light_dir=(0, 1, 0))
    good, _, _ = render(mesh, perspective_correct=True, **kw)
    bad, _, _ = render(mesh, perspective_correct=False, **kw)
    os.makedirs("out", exist_ok=True)
    write_ppm("out/floor_correct.ppm", good)
    write_ppm("out/floor_naive.ppm", bad)
    print(f"SSIM(naive, correct) = {ssim(bad, good):.3f}   PSNR = {psnr(bad, good):.1f} dB")
    print("wrote out/floor_correct.ppm and out/floor_naive.ppm  (view both: naive 'swims')")


if __name__ == "__main__":
    main()
