#!/usr/bin/env python3
"""
Genera un baseline RNG 1..90 allineato al Lotto 2025:

- legge datasets/lotto_2025_numbers.txt per determinare N
- genera N interi uniformi in [1..90] con seed fisso
- scrive datasets/lotto_2025_numbers_rng.txt
"""

from __future__ import annotations

import random
from pathlib import Path

LOTTO_PATH = Path("datasets/lotto_2025_numbers.txt")
OUT_PATH = Path("datasets/lotto_2025_numbers_rng.txt")


def count_numbers(path: Path) -> int:
    """Conta quanti interi ci sono nel file (uno per riga)."""
    n = 0
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # se la riga non è un intero, la saltiamo
            try:
                int(line)
            except ValueError:
                continue
            n += 1
    return n


def main() -> None:
    if not LOTTO_PATH.exists():
        raise SystemExit(
            f"[err] File Lotto non trovato: {LOTTO_PATH}. "
            "Assicurati di aver già generato datasets/lotto_2025_numbers.txt."
        )

    N = count_numbers(LOTTO_PATH)
    print(f"[info] Trovati {N} numeri in {LOTTO_PATH}")

    rnd = random.Random(123456)  # seed fisso per run ripetibili

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for _ in range(N):
            x = rnd.randint(1, 90)
            f.write(f"{x}\n")

    print(f"[ok] scritto baseline RNG 1..90 in {OUT_PATH}")


if __name__ == "__main__":
    main()
