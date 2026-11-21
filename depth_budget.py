"""Lab 1 step 6(a): the 1/z crush with MY near/far, in numbers (standard [0,1] depth d = a/z + b)."""
import numpy as np
def d01(z, n, f):                      # eye distance z>0 -> depth in [0,1], standard-Z
    return (f * (z - n)) / (z * (f - n))
def dz_per_code(z, n, f, bits=24):     # smallest resolvable distance step at eye distance z
    dd = (f * n) / (z * z * (f - n))   # |dd/dz|
    return (1.0 / 2**bits) / dd
for n, f, tag in ((1.0, 14.0, "MY camera  near=1, far=14"), (0.01, 1000.0, "Reed-style near=0.01, far=1000")):
    print(f"== {tag}")
    print(f"   fraction of depth codes used by the FIRST metre after near : {100*d01(n+1,n,f):5.1f} %")
    print(f"   fraction used by the first 10 % of [near,far]              : {100*d01(n+0.1*(f-n),n,f):5.1f} %")
    for z in (n + 0.5, 5.35, 10.0, f * 0.99):
        print(f"   int24: smallest resolvable depth gap at distance {z:7.2f} m = {dz_per_code(z,n,f):.3e} m")
