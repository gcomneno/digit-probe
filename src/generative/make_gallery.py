#!/usr/bin/env python3
"""
Genera GALLERY.md a partire da una lista di report JSON prodotti da digit_probe.py.

Include sia casi reali (Lotto, pi, e, primi, gradienti) sia RNG sintetici
(uniforme, biased, LCG marcio, ecc.), se i relativi JSON sono presenti in out/.
"""

from __future__ import annotations

import json
from pathlib import Path

# ROOT: radice del repo
# __file__ = src/generative/make_gallery.py
# parents[0] = src/generative
# parents[1] = src
# parents[2] = <root del repo>
ROOT = Path(__file__).resolve().parents[2]

OUT_DIR = ROOT / "out"
GALLERY = ROOT / "docs/GALLERY.md"

# (label, filename JSON relativo a OUT_DIR)
CASES: list[tuple[str, str]] = [
    # --- REALI / SEMI-REALI ---
    ("Lotto 2025 – integers (1..90)", "lotto-2025-full-integers.json"),
    ("RNG 1..90 – baseline", "lotto-2025-rng-1-90.json"),
    ("π – 100k cifre", "pi_100k.json"),
    ("e – 100k cifre", "e_100k.json"),
    ("Primi – cifre concatenati (≈100k)", "primes_100k_digits.json"),
    ("Gradiente mod 10 – 0..9 ripetuti (100k)", "gradient_mod10_100k.json"),
    # --- RNG ZOO (digits) ---
    ("RNG digits – uniform (0..9)", "digits_rng_uniform.json"),
    ("RNG digits – biased7 (7≈40%)", "digits_rng_biased7.json"),
    ("RNG digits – LCG mod10 (marcio)", "digits_rng_lcg_mod10.json"),
]


def fmt(x, nd: int = 4) -> str:
    """Formatta numeri float con nd decimali, o '–' se None."""
    if x is None:
        return "–"
    try:
        return f"{float(x):.{nd}f}"
    except Exception:
        return str(x)


def load_report(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def max_abs_autocorr(report: dict) -> float | None:
    """Restituisce il massimo valore assoluto di autocorrelazione sui lag 1..5."""
    ac = report.get("autocorr")
    if not isinstance(ac, dict):
        return None
    vals: list[float] = []
    for v in ac.values():
        try:
            if v is None:
                continue
            vals.append(abs(float(v)))
        except (TypeError, ValueError):
            continue
    return max(vals) if vals else None


def make_gallery() -> None:
    rows: list[dict] = []

    for label, fname in CASES:
        path = OUT_DIR / fname
        if not path.exists():
            print(f"[warn] JSON non trovato, salto: {fname}")
            continue

        rep = load_report(path)
        mode = rep.get("mode")
        N = rep.get("N")
        M = rep.get("alphabet")
        chi2 = rep.get("chi_square")
        compress = rep.get("compress_ratio")
        schur = rep.get("schur", {})
        schur_z = schur.get("z")
        max_rho = max_abs_autocorr(rep)

        rows.append(
            {
                "label": label,
                "mode": mode,
                "N": N,
                "M": M,
                "chi2": chi2,
                "compress": compress,
                "max_rho": max_rho,
                "schur_z": schur_z,
            }
        )

    lines: list[str] = []
    lines.append("# Digit-Probe – Gallery di casi reali e sintetici\n")
    lines.append(
        "Questa pagina raccoglie alcuni dataset analizzati con `digit_probe.py`, "
        "per dare un'idea del **profilo statistico** di casi reali vs RNG sintetici.\n"
    )
    lines.append("Ogni riga riassume alcune metriche chiave:\n")
    lines.append(
        "- `N`: lunghezza della sequenza\n"
        "- `M`: dimensione alfabeto (`alphabet`)\n"
        "- `χ²`: chi-quadrato sulla distribuzione dei simboli\n"
        "- `compress`: rapporto di compressione zlib (più basso = più struttura/ripetizione)\n"
        "- `max_rho`: massimo valore assoluto di autocorrelazione sui lag 1..5\n"
        "- `Schur z`: z-score del test SchurProbe\n"
    )
    lines.append("---\n")

    lines.append("| Dataset | Tipo | N | M | χ² | compress | max_rho (lag≤5) | Schur z |")
    lines.append("|:--------|:-----|---:|---:|---:|--------:|----------------:|--------:|")

    for row in rows:
        label = row["label"]
        mode = row["mode"]
        N = row["N"]
        M = row["M"]
        chi2 = fmt(row["chi2"], 2)
        compress = fmt(row["compress"], 4)
        max_rho = fmt(row["max_rho"], 4)
        schur_z = fmt(row["schur_z"], 2)

        lines.append(
            f"| {label} | {mode} | {N} | {M} | {chi2} | " f"{compress} | {max_rho} | {schur_z} |"
        )

    GALLERY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[ok] scritto {GALLERY} ({len(rows)} righe dati)")


if __name__ == "__main__":
    make_gallery()
