"""Which model/texture the Lab scripts use.  Default = MY model (Candi Siwa, make_siwa.py).
Set M3_MODEL=data/pusaka_model.obj M3_TEX=data/relief.ppm to use the committed fallback."""
import os
MODEL = os.environ.get("M3_MODEL", "data/mymodel.obj")
TEX = os.environ.get("M3_TEX", "data/mytexture.ppm")
