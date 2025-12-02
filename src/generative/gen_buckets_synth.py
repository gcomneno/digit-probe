#!/usr/bin/env python3

import argparse
import sys

ap = argparse.ArgumentParser(
    description="Genera sequenza di interi 0..M-1 con salto fisso (stride) mod M."
)
ap.add_argument("--m", type=int, required=True, help="alfabeto (es. 4096)")
ap.add_argument("--n", type=int, required=True, help="lunghezza")
ap.add_argument("--stride", type=int, default=257, help="salto per step (coprime con m)")
ap.add_argument("--start", type=int, default=0)
args = ap.parse_args()

M, N, s, x = args.m, args.n, args.stride % args.m, args.start % args.m
for _ in range(N):
    sys.stdout.write(str(x) + "\n")
    x = (x + s) % M
