"""Lab 1 step 3-4 / Analysis A1: trace ONE vertex of MY model (data/mymodel.obj) through
object -> world -> view -> clip -> NDC -> screen, and read the columns of M and V.
Same camera / model matrix as raster3d.py (eye (2.6,2,3.4), centre (0,0.7,0), fovy 45,
near 1, far 14, M = rot_y(35) @ scale(1.4)), framebuffer 512x512.

Run:  python trace_vertex.py [--index 2]
"""
import argparse
import numpy as np
from objio import load_obj
from transforms import rot_y, scale, translate, look_at, perspective, viewport
import config

ap = argparse.ArgumentParser(); ap.add_argument("--index", type=int, default=2)
ap.add_argument("--model", default=config.MODEL)
a = ap.parse_args()
np.set_printoptions(precision=4, suppress=True)

mesh = load_obj(a.model)
p_obj = np.r_[mesh.positions[a.index], 1.0]
M = rot_y(35) @ scale((1.4, 1.4, 1.4))
V = look_at((2.6, 2.0, 3.4), (0, 0.7, 0))
P = perspective(45.0, 1.0, 1.0, 14.0)
w, h = 512, 512

world = M @ p_obj
eye = V @ world
clip = P @ eye
ndc = clip[:3] / clip[3]
scr = viewport(ndc[None, :], w, h)[0]

print(f"model: {a.model}   vertex index {a.index}")
print(f"object  p        = {p_obj}")
print(f"world   M p      = {world}")
print(f"view    V (M p)  = {eye}      (z<0: in front of the camera, distance {-eye[2]:.4f})")
print(f"clip    P V M p  = {clip}   (w = -z_eye = {clip[3]:.4f})")
print(f"ndc     clip/w   = {ndc}")
print(f"screen  512x512  = x {scr[0]:.2f}  y {scr[1]:.2f}  depth {scr[2]:.4f}")
print("\nM = rot_y(35) @ scale(1.4):"); print(M)
print("column reading of M (where do the model axes go?):")
for k, n in enumerate(["+x", "+y", "+z", "origin"]):
    print(f"  col {k+1} ({n:6s}) -> {M[:, k]}")
print("\nV = look_at(eye=(2.6,2,3.4), centre=(0,0.7,0)):"); print(V)
print("column reading of V (world axes expressed in the camera frame):")
for k, n in enumerate(["+x", "+y", "+z", "origin"]):
    print(f"  col {k+1} (world {n:6s}) -> {V[:, k]}")
chk = V @ np.r_[2.6, 2.0, 3.4, 1.0]
print(f"\ncheck: V @ camera_position = {chk}  (must be the origin)")
