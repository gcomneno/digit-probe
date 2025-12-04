#!/usr/bin/env python3
"""
Genera un dataset di cifre a partire dai numeri primi:

- concatenazione delle cifre dei primi (2, 3, 5, 7, 11, 13, 17, ...)
- si ferma quando raggiunge (o supera di poco) N cifre
- scrive in datasets/primes_100k_digits.txt
"""

from __future__ import annotations

import math
from pathlib import Path

OUT = Path("datasets/primes_100k_digits.txt")
TARGET_N = 100_000  # cifre


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    r = int(math.isqrt(n))
    f = 3
    while f <= r:
        if n % f == 0:
            return False
        f += 2
    return True


def gen_primes_digits(target: int) -> str:
    buf: list[str] = []
    total = 0
    p = 2
    while total < target:
        if is_prime(p):
            s = str(p)
            buf.append(s)
            total += len(s)
        p += 1
    return "".join(buf)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    digits = gen_primes_digits(TARGET_N)
    OUT.write_text(digits + "\n", encoding="utf-8")
    print(f"[ok] scritto {OUT} ({len(digits)} cifre)")


if __name__ == "__main__":
    main()
