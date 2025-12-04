#!/usr/bin/env python3
"""
Genera un dataset di cifre con gradiente mod 10:

0,1,2,3,4,5,6,7,8,9,0,1,2,3,...

- lunghezza TARGET_N cifre
- scrive in datasets/gradient_mod10_100k.txt
"""

from __future__ import annotations

from pathlib import Path

OUT = Path("datasets/gradient_mod10_100k.txt")
TARGET_N = 100_000  # cifre


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    digits = []
    for i in range(TARGET_N):
        digits.append(str(i % 10))
    txt = "".join(digits) + "\n"
    OUT.write_text(txt, encoding="utf-8")
    print(f"[ok] scritto {OUT} ({TARGET_N} cifre)")


if __name__ == "__main__":
    main()
