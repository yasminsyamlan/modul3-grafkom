
import os
import numpy as np
import matplotlib.pyplot as plt

import raster3d
from broken_scene import _zfight_scene, TRI_COLS

# Scene dan kamera yang sama dengan pengujian z-fighting
mesh = _zfight_scene()

cam = dict(
    eye=(0, 1, 6),
    center=(0, 1, -1),
    cull_back=False,
    far=200,
    tri_colors=TRI_COLS,
    light_dir=(0, 0.2, 1)
)

# Render sebelum perbaikan
_, depth_bad, _ = raster3d.render(
    mesh, w=192, h=192,
    near=1e-3, depth_bits=16, **cam
)

# Render setelah perbaikan
_, depth_fixed, _ = raster3d.render(
    mesh, w=192, h=192,
    near=1.0, depth_bits=16, **cam
)

# Ambil nilai depth yang valid
bad = depth_bad[np.isfinite(depth_bad)]
fixed = depth_fixed[np.isfinite(depth_fixed)]

# Buat folder laporan jika belum ada
os.makedirs("report", exist_ok=True)

# Buat histogram perbandingan
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].hist(bad, bins=60, range=(0, 1))
axes[0].set_title("Before Fix: Near = 0.001")
axes[0].set_xlabel("Depth Value")
axes[0].set_ylabel("Pixel Count")
axes[0].grid(alpha=0.25)

axes[1].hist(fixed, bins=60, range=(0, 1))
axes[1].set_title("After Fix: Near = 1.0")
axes[1].set_xlabel("Depth Value")
axes[1].set_ylabel("Pixel Count")
axes[1].grid(alpha=0.25)

fig.suptitle("Z-Fighting Depth Distribution")
plt.tight_layout()

plt.savefig(
    "report/fig_zfight_histogram.png",
    dpi=200,
    bbox_inches="tight"
)

plt.close()

print("Histogram berhasil dibuat!")
print("File: report/fig_zfight_histogram.png")
print("Valid depth pixels before:", len(bad))
print("Valid depth pixels after :", len(fixed))
