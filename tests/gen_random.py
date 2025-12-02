#!/usr/bin/env python3

import argparse, random, sys

ap=argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=100000)
ap.add_argument("--seed", type=int, default=0)
args=ap.parse_args()

random.seed(args.seed)

s="".join(str(random.randint(0,9)) for _ in range(args.n))

sys.stdout.write(s)
