#!/usr/bin/env python3

import argparse
import random
import sys

ap = argparse.ArgumentParser(
    description="Genera cifre con pattern additivo debole per stress SchurProbe."
)
ap.add_argument("--n", type=int, default=50000)
ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--bias", type=int, default=2, help="shift additivo quando scatta il vincolo")
args = ap.parse_args()

random.seed(args.seed)
seq = []
for _ in range(args.n):
    x = random.randint(0, 9)
    if len(seq) > 2 and (seq[-2] + seq[-1]) % 2 == 0:
        x = (seq[-1] + args.bias) % 10
    seq.append(x)

sys.stdout.write("".join(str(x) for x in seq))
