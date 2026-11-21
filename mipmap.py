"""Module 3 -- Mipmaps (Lab 2 step 4): the Module 1 Nyquist limit, for textures.

A far-away textured surface puts many texels inside one pixel; point/bilinear
sampling then UNDERSAMPLES the texture -> shimmer / moire. A mip pyramid holds
pre-filtered half-size copies; the renderer picks the level where 1 texel ~ 1
pixel. Each level is a GAMMA-CORRECT box downscale (average in LINEAR light,
Module 1) of the level above.

Run:  python mipmap.py            (renders the temple far away, with/without mips)
"""
from __future__ import annotations

import os

import numpy as np

from srgb import srgb_to_linear, linear_to_srgb


def build_pyramid(tex_u8, levels=4):
    """List of (H,W,3) linear-light float arrays; level k is 1/2^k size."""
    lin = srgb_to_linear(tex_u8.astype(np.float64) / 255.0)
    pyr = [lin]
    for _ in range(levels - 1):
        a = pyr[-1]
        h, w = a.shape[0] // 2 * 2, a.shape[1] // 2 * 2
        a = a[:h, :w]
        pyr.append((a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]) / 4.0)
    return pyr


def lod_from_uv(u, v, tex_size):
    """Per-pixel LOD = log2(texels-per-pixel), from screen-space UV derivatives."""
    if u.shape[0] < 2 or u.shape[1] < 2:
        return np.zeros_like(u)
    dudy, dudx = np.gradient(u)
    dvdy, dvdx = np.gradient(v)
    rho = np.maximum(np.hypot(dudx, dvdx), np.hypot(dudy, dvdy)) * tex_size
    return np.log2(np.maximum(np.nan_to_num(rho, nan=1.0, posinf=1.0), 1.0))


def sample_trilinear(pyr, u, v, lod):
    """Blend the two nearest levels (tent weights), bilinear within each."""
    from raster3d import sample_bilinear
    n = len(pyr)
    lod = np.clip(lod, 0, n - 1)
    out = np.zeros((*u.shape, 3))
    for k in range(n):
        wk = np.maximum(0.0, 1.0 - np.abs(lod - k))
        if wk.any():
            out += wk[..., None] * sample_bilinear(pyr[k], u, v)
    return out


def hf_energy(img_u8):
    """High-frequency energy: mean squared 1-pixel difference (shimmer proxy)."""
    f = img_u8.astype(np.float64)
    return float((np.diff(f, axis=0) ** 2).mean() + (np.diff(f, axis=1) ** 2).mean())


def main():
    from objio import load_obj
    from ppm_io import read_ppm, write_ppm
    from raster3d import render
    from transforms import rot_y, scale
    from metrics import ssim
    mesh = load_obj(__import__("config").MODEL)
    tex = read_ppm(__import__("config").TEX)
    pyr = build_pyramid(tex, 4)
    print("pyramid:", [p.shape[:2] for p in pyr])
    model = rot_y(35) @ scale((1.4, 1.4, 1.4))
    far_cam = dict(eye=(26, 20, 34), center=(0, 0.7, 0), far=120.0, fovy=20.0)  # temple ~ 60 px
    os.makedirs("out", exist_ok=True)
    res = {}
    for name, mip in (("nomip", None), ("mip", pyr)):
        img, _, _ = render(mesh, w=128, h=128, tex_u8=tex, model=model, mip=mip, **far_cam)
        write_ppm(f"out/far_{name}.ppm", img)
        res[name] = img
    # shimmer proxy: render a 1-pixel camera nudge and measure frame-to-frame change
    far2 = dict(far_cam, eye=(26.05, 20, 34))
    for name, mip in (("nomip", None), ("mip", pyr)):
        img2, _, _ = render(mesh, w=128, h=128, tex_u8=tex, model=model, mip=mip, **far2)
        d = np.abs(res[name].astype(float) - img2.astype(float)).mean()
        print(f"{name:6s} HF energy {hf_energy(res[name]):8.1f}   "
              f"frame-to-frame change after a tiny camera nudge: {d:.2f}")
    print(f"SSIM(nomip, mip) = {ssim(res['nomip'], res['mip']):.3f}")
    print("wrote out/far_nomip.ppm, out/far_mip.ppm  (compare: mip is smoother and stable)")


if __name__ == "__main__":
    main()
