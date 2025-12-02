#!/usr/bin/env python3
"""
Genera una sequenza RNG uniform(1..90) lunga quanto il dataset Lotto 2025
e la salva in datasets/lotto_2025_numbers_rng.txt (un numero per riga).
"""

from __future__ import annotations

import random
from pathlib import Path

SRC = Path("datasets/lotto_2025_numbers.txt")
OUT = Path("datasets/lotto_2025_numbers_rng.txt")


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"File sorgente non trovato: {SRC}")

    text = SRC.read_text(encoding="utf-8").strip()
    tokens = [t for t in text.splitlines() if t.strip()]
    n = len(tokens)

    # Seed fisso per avere sempre la stessa sequenza RNG di baseline
    random.seed(123456)

    nums = [str(random.randint(1, 90)) for _ in range(n)]
    OUT.write_text("\n".join(nums) + "\n", encoding="utf-8")

    print(f"Generati {n} numeri uniformi 1..90 in {OUT}")


if __name__ == "__main__":
    main()
