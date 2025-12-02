#!/usr/bin/env python3
"""
Genera una piccola "RNG Zoo" di CIFRE (0..9) per digit-probe (mode=digits).

- Se esiste data/lotto/lotto_2025_digits.txt, usa il suo numero di cifre come N.
- Altrimenti usa un fallback N=21010.

Produce tre dataset in datasets/:

  - datasets/digits_rng_uniform.txt    : cifre 0..9 uniformi
  - datasets/digits_rng_lcg_mod10.txt : LCG mod 10 (marcio, periodo corto)
  - datasets/digits_rng_biased7.txt   : cifre con 7 pesantemente favorito

Formato: una lunga stringa di cifre per file (senza spazi), come il file Lotto.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Iterable

# Dove prendo N (per allinearmi al Lotto 2025, se presente)
LOTTO_DIGITS = Path("data/lotto/lotto_2025_digits.txt")
OUT_DIR = Path("datasets")
FALLBACK_N = 21010  # lo stesso del Lotto 2025 (10505 numeri × 2 cifre)


def infer_N() -> int:
    """Ricava N da lotto_2025_digits.txt se esiste, altrimenti usa FALLBACK_N."""
    if LOTTO_DIGITS.exists():
        text = LOTTO_DIGITS.read_text(encoding="utf-8")
        n = sum(ch.isdigit() for ch in text)
        print(f"[info] Trovato {LOTTO_DIGITS}, N={n} cifre.")
        return n
    print(f"[warn] {LOTTO_DIGITS} non trovato, uso N={FALLBACK_N} come fallback.")
    return FALLBACK_N


def gen_uniform_digits(n: int) -> Iterable[str]:
    """Cifre 0..9 uniformi, RNG "normale"."""
    rnd = random.Random(123456)
    for _ in range(n):
        yield str(rnd.randint(0, 9))


def gen_lcg_mod10(n: int) -> Iterable[str]:
    """
    LCG marcio modulo 10 (ci aspettiamo pattern forti).

    X_{k+1} = (a * X_k + c) mod m, qui m=10.
    Parametri scelti apposta "così così".
    """
    m = 10
    a = 3
    c = 7
    x = 1

    for _ in range(n):
        x = (a * x + c) % m
        yield str(x)


def gen_biased7(n: int) -> Iterable[str]:
    """
    Cifre 0..9 con 7 pesantemente favorito.

    Usiamo weights:
      - tutte le cifre peso 1
      - 7 peso 6

    → 7 ~ 6/(6+9) ≈ 40% circa, le altre ~6% ciascuna.
    """
    rnd = random.Random(987654)
    digits = list(range(10))
    weights = [1] * 10
    weights[7] = 6  # bias sul 7

    # rnd.choices restituisce una lista di int, la trasformiamo in stringhe
    choices = rnd.choices(digits, weights=weights, k=n)
    for d in choices:
        yield str(d)


def write_digits_dataset(path: Path, digits: Iterable[str]) -> None:
    """
    Scrive una lunga stringa di cifre (come lotto_2025_digits.txt).
    """
    text = "".join(digits) + "\n"
    path.write_text(text, encoding="utf-8")
    print(f"[ok] Scritto {path}")


def main() -> None:
    n = infer_N()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    write_digits_dataset(OUT_DIR / "digits_rng_uniform.txt", gen_uniform_digits(n))
    write_digits_dataset(OUT_DIR / "digits_rng_lcg_mod10.txt", gen_lcg_mod10(n))
    write_digits_dataset(OUT_DIR / "digits_rng_biased7.txt", gen_biased7(n))


if __name__ == "__main__":
    main()
