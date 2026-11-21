"""Lab 2 step 4 (stronger evidence): is the mip render closer to the TRUE far view?
Truth = same far camera rendered at 4x4 supersampling (512x512, no mip) then gamma-correct
box-downscaled to 128x128 (Module 1).  Compare error of (a) point/bilinear texel sampling
(no mip) and (b) trilinear mip, plus frame-to-frame flicker under a camera nudge.
Run: python mip_eval.py"""
import numpy as np
import config
from objio import load_obj
from ppm_io import read_ppm, write_ppm
from raster3d import render
from mipmap import build_pyramid, hf_energy
from transforms import rot_y, scale
from metrics import psnr, ssim
from srgb import srgb_to_linear, linear_to_srgb

mesh = load_obj(config.MODEL); tex = read_ppm(config.TEX); pyr = build_pyramid(tex, 4)
M = rot_y(35) @ scale((1.4, 1.4, 1.4))
cam = dict(eye=(26, 20, 34), center=(0, 0.7, 0), far=120.0, fovy=20.0)
def box_down(img, k):
    lin = srgb_to_linear(img.astype(float) / 255.0)
    H, W = lin.shape[:2]
    lin = lin.reshape(H // k, k, W // k, k, 3).mean((1, 3))
    return np.clip(linear_to_srgb(lin) * 255 + .5, 0, 255).astype(np.uint8)
big, _, _ = render(mesh, w=512, h=512, tex_u8=tex, model=M, **cam)
ref = box_down(big, 4)
write_ppm("out/far_truth.ppm", ref)
out = {}
for name, mip in (("nomip", None), ("mip", pyr)):
    a, _, _ = render(mesh, w=128, h=128, tex_u8=tex, model=M, mip=mip, **cam)
    b, _, _ = render(mesh, w=128, h=128, tex_u8=tex, model=M, mip=mip, **dict(cam, eye=(26.4, 20, 34)))
    out[name] = a
    print(f"{name:6s} PSNR vs truth {psnr(a, ref):6.2f} dB   SSIM {ssim(a, ref):.4f}   "
          f"HF {hf_energy(a):7.1f}   nudge change {np.abs(a.astype(float)-b.astype(float)).mean():.3f}")
