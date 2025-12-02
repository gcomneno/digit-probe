#!/usr/bin/env python3

import argparse
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--repeat", type=int, default=10000, help="quante volte ripetere '0123456789'")
args = ap.parse_args()

sys.stdout.write("0123456789" * args.repeat)
