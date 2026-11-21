"""Module 3 -- Lab 1 step 2: MY OWN model -- Candi Siwa (Prambanan), low-poly blockout.

Input  : the floor plan I traced in Module 2 (../Module2_final (1)/myplan.json, copied to
         data/myplan.json).  Footprints (outer wall, inner platform, temple body, cella,
         stairs, three niche shrines) are read from that file, so Module 2 -> Module 3
         is one continuous artefact.
Output : data/mymodel.obj      (positions + vt + f, CCW-outward, real per-face UV)
         data/mytexture.ppm    (256x256 procedural sandstone with carved panel band)

HONEST NOTE: plan x/y come from my schematic plan (base 34 m is the published figure;
inner offsets are proportional estimates).  HEIGHTS below are my own estimates
(Candi Siwa is ~47 m tall in total), not a survey.

Coordinates (right-handed, y up, entrance faces +x = east):
    world_x =  (plan_x - 17) * S          world_z = -(plan_y - 17) * S     world_y = h * S
S = 1.5 / 47 so that the whole temple is 1.5 units tall, like the fallback model, so the
same camera / light / model matrix of raster3d.py, raytrace.py and web/viewer.js apply.

Run:  python make_siwa.py
"""
from __future__ import annotations

import json
import os

import numpy as np

from objio import save_obj
from ppm_io import write_ppm
from srgb import linear_to_srgb, to_u8

S = 1.5 / 47.0     # blockout is ~43 m tall -> 1.37 units
TILE_M = 8.0          # one texture tile covers 8 m of wall (constant texel density)


def box_faces(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box [x0,x1]x[y0,y1]x[z0,z1] in PLAN metres (x east, z = plan y north,
    y height). Returns 24 world verts, 12 CCW-outward triangles (local index) and 24 uv.
    Each of the 6 faces has its OWN 4 vertices + UV (a shared-corner box cannot carry a
    different UV per face). UV = metres / TILE_M, so texel density is uniform."""
    def W(px, h, py):               # plan -> world
        return ((px - 17.0) * S, h * S, -(py - 17.0) * S)

    verts, uvs, tris = [], [], []

    def quad(p00, p10, p11, p01, u_len, v_len):
        # p00,p10,p11,p01 are given CCW seen from OUTSIDE.
        base = len(verts)
        verts.extend([W(*p) for p in (p00, p10, p11, p01)])
        uvs.extend([(0, 0), (u_len / TILE_M, 0), (u_len / TILE_M, v_len / TILE_M),
                    (0, v_len / TILE_M)])
        tris.append((base, base + 1, base + 2))
        tris.append((base, base + 2, base + 3))

    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    # world z = -plan_y : so plan +y (north) is world -z.
    # +x face (east)  : seen from +x, CCW = going (south->north) along bottom
    quad((x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0), dz, dy)
    # -x face (west)
    quad((x0, y0, z1), (x0, y0, z0), (x0, y1, z0), (x0, y1, z1), dz, dy)
    # +plan_y face (north, world -z)
    quad((x1, y0, z1), (x0, y0, z1), (x0, y1, z1), (x1, y1, z1), dx, dy)
    # -plan_y face (south, world +z)
    quad((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), dx, dy)
    # top (+y): CCW seen from above
    quad((x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1), dx, dz)
    # bottom (-y)
    quad((x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0), dx, dz)
    return verts, tris, uvs


def plan_rect(plan, pid):
    for p in plan["polylines"]:
        if p["id"] == pid:
            xs = [q[0] for q in p["points"]]; ys = [q[1] for q in p["points"]]
            return min(xs), max(xs), min(ys), max(ys)
    raise KeyError(pid)


def build(plan):
    boxes = []          # (x0,x1,y0h,y1h,z0,z1)  plan metres, heights in metres
    ox0, ox1, oz0, oz1 = plan_rect(plan, "outer_wall")        # 0..34
    ix0, ix1, iz0, iz1 = plan_rect(plan, "inner_platform")    # 5..29
    bx0, bx1, bz0, bz1 = plan_rect(plan, "temple_body")       # 9..25
    cx0, cx1, cz0, cz1 = plan_rect(plan, "cella")             # 14..20
    cxm, czm = (cx0 + cx1) / 2, (cz0 + cz1) / 2               # 17, 17

    # 1. outer terrace (batur), 2. inner platform, 3. temple body
    boxes.append((ox0, ox1, 0.0, 1.5, oz0, oz1))
    boxes.append((ix0, ix1, 1.5, 4.0, iz0, iz1))
    boxes.append((bx0, bx1, 4.0, 14.0, bz0, bz1))
    # 4. roof: 6 shrinking tiers (the stepped pyramid roof, 14 m -> 41 m)
    half = 8.0
    y = 14.0
    for k in range(6):
        h = 4.0 if k < 5 else 3.0
        boxes.append((cxm - half, cxm + half, y, y + h, czm - half, czm + half))
        y += h
        half -= 1.15
    # 5. finial: ratna on top
    boxes.append((cxm - 0.8, cxm + 0.8, y, y + 4.0, czm - 0.8, czm + 0.8))
    boxes.append((cxm - 0.35, cxm + 0.35, y + 4.0, y + 6.0, czm - 0.35, czm + 0.35))

    # 6. four stairs (each: 4 treads rising 0.375 m, plan width from the plan file)
    def stair(pid, axis):
        x0, x1, z0, z1 = plan_rect(plan, pid)
        if pid == "entrance_stair":            # east, treads march in -x towards temple
            treads = 4
            for t in range(treads):
                xa = x1 - (t + 1) * (x1 - x0) / treads * 1.0
                boxes.append((x1 - (t + 1) * (x1 - x0) / treads, x1, 0.0, 1.5 * (treads - t) / treads, z0, z1))
        elif pid == "stair_west":
            treads = 4
            for t in range(treads):
                boxes.append((x0, x0 + (t + 1) * (x1 - x0) / treads, 0.0, 1.5 * (treads - t) / treads, z0, z1))
        elif pid == "stair_north":             # plan y 29..34 (north)
            treads = 4
            for t in range(treads):
                boxes.append((x0, x1, 0.0, 1.5 * (treads - t) / treads, z1 - (t + 1) * (z1 - z0) / treads, z1))
        elif pid == "stair_south":
            treads = 4
            for t in range(treads):
                boxes.append((x0, x1, 0.0, 1.5 * (treads - t) / treads, z0, z0 + (t + 1) * (z1 - z0) / treads))
    for pid in ("entrance_stair", "stair_west", "stair_north", "stair_south"):
        stair(pid, None)

    # 7. three niche shrines against the temple body (Durga N, Agastya S, Ganesha W)
    for pid in ("shrine_durga_north", "shrine_agastya_south", "shrine_ganesha_west"):
        x0, x1, z0, z1 = plan_rect(plan, pid)
        boxes.append((x0, x1, 4.0, 11.0, z0, z1))
        boxes.append((x0 + 0.5, x1 - 0.5, 11.0, 13.0, z0 + 0.5, z1 - 0.5))

    # 8. four corner votive stupas on the inner platform
    for (px, pz) in ((7.0, 7.0), (27.0, 7.0), (7.0, 27.0), (27.0, 27.0)):
        boxes.append((px - 1.2, px + 1.2, 4.0, 6.0, pz - 1.2, pz + 1.2))
        boxes.append((px - 0.7, px + 0.7, 6.0, 8.0, pz - 0.7, pz + 0.7))

    positions, uvs, faces, face_uvs = [], [], [], []
    for (x0, x1, h0, h1, z0, z1) in boxes:
        v, t, uv = box_faces(x0, x1, h0, h1, z0, z1)
        off = len(positions)
        positions.extend(v); uvs.extend(uv)
        for (a, b, c) in t:
            faces.append((a + off, b + off, c + off))
            face_uvs.append((a + off, b + off, c + off))
    return np.array(positions), np.array(uvs), faces, face_uvs, len(boxes)


def sandstone(n=256):
    """Deterministic procedural texture: stone courses (rows of blocks, mortar lines),
    a carved relief band, and low-frequency staining. No RNG, no binary assets in Git."""
    y, x = np.mgrid[0:n, 0:n].astype(np.float64)
    course_h, block_w = n / 8.0, n / 4.0
    row = np.floor(y / course_h)
    xo = (x + (row % 2) * block_w / 2) % block_w
    yo = y % course_h
    mortar = ((xo < 2) | (yo < 2)).astype(float)
    base = 0.62 + 0.10 * np.sin(2 * np.pi * (x * 0.031 + y * 0.017)) * np.cos(2 * np.pi * y * 0.021)
    grain = 0.04 * np.sin(2 * np.pi * (x * 0.37 + y * 0.11)) * np.sin(2 * np.pi * y * 0.29)
    lum = base + grain
    band = (y > 0.38 * n) & (y < 0.62 * n)                  # carved relief band
    rel = 0.5 + 0.5 * np.sin(2 * np.pi * x / (n / 8.0)) * np.sin(2 * np.pi * (y - 0.38 * n) / (0.24 * n) * 1.0)
    lum = np.where(band, lum * (0.72 + 0.28 * rel), lum)
    lum = np.where(mortar > 0, lum * 0.55, lum)
    lum = np.clip(lum, 0.05, 0.98)
    tint = (1.00, 0.84, 0.64)
    lin = np.dstack([lum * tint[0], lum * tint[1], lum * tint[2]])
    return to_u8(linear_to_srgb(np.clip(lin, 0, 1)))


def main():
    os.makedirs("data", exist_ok=True)
    src = "data/myplan.json"
    with open(src, "r", encoding="utf-8") as fh:
        plan = json.load(fh)
    positions, uvs, faces, face_uvs, nbox = build(plan)
    save_obj("data/mymodel.obj", positions, uvs, faces, face_uvs)
    tex = sandstone()
    write_ppm("data/mytexture.ppm", tex)
    print(f"plan: {plan['name'][:60]}")
    print(f"wrote data/mymodel.obj  ({nbox} boxes, {len(positions)} verts, {len(faces)} triangles)")
    print(f"wrote data/mytexture.ppm ({tex.shape[1]}x{tex.shape[0]})")
    print(f"bbox: min {positions.min(0).round(3)}  max {positions.max(0).round(3)}")


if __name__ == "__main__":
    main()
