#!/usr/bin/env bash
# Lab 3 step 5: reproduce from a clean clone. Run from Module3/.
set -euo pipefail
python3 -m venv .venv_repro && . .venv_repro/bin/activate
pip install -q -r requirements.txt
python make_model.py          # fallback model + relief.ppm
python make_siwa.py           # MY model (Candi Siwa) + mytexture.ppm
python tests.py
python raster3d.py --model data/mymodel.obj --tex data/mytexture.ppm --w 256 --h 256
python raytrace.py --model data/mymodel.obj --tex data/mytexture.ppm --w 256 --h 256
python compare.py out/temple_raster.ppm out/temple_rt.ppm
echo "Verified: $(python --version) NumPy $(python -c 'import numpy;print(numpy.__version__)') on $(date +%F)"
echo "Next: npx serve .  -> http://localhost:3000/web/   (or ?cmp=1 for compare mode)"
