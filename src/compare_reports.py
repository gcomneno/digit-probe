#!/usr/bin/env python3
"""
compare_reports.py

Confronta uno o più report JSON prodotti da digit_probe.py.

- Stampa un riepilogo per file (chi², compress_ratio, runs, max|autocorr|, ngram_best, Schur z)
- Calcola un AnomalyScore aggregato rispetto a una baseline opzionale
- Può esportare:
  - CSV (--csv)
  - tabella Markdown (--md)

Uso tipico:

    python3 src/compare_reports.py pi.json e.json --baseline pi.json --md compare_pi_e.md
"""

import argparse
import json
import math
import os
from typing import Any, Dict, List, Optional, Tuple


def load_report(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf8") as f:
        data = json.load(f)
    data["_path"] = path
    data["_name"] = os.path.basename(path)
    return data


def safe_get_runs(data: Dict[str, Any]) -> Tuple[float, float]:
    """Estrae (Z, p) dal blocco 'runs' in modo robusto."""
    runs = data.get("runs", {}) or {}
    Z = runs.get("Z", float("nan"))
    # schema nuovo: p_two_tailed
    p = runs.get("p_two_tailed")
    if p is None:
        # eventuali schemi vecchi o alternativi
        p = runs.get("p") or runs.get("p_value") or float("nan")
    return float(Z), float(p)


def safe_get_autocorr_max(data: Dict[str, Any]) -> float:
    """Restituisce max|autocorr|, calcolandolo se necessario."""
    # Se un giorno lo salviamo già precomputato:
    if "autocorr_max_abs" in data:
        return float(data["autocorr_max_abs"])

    ac = data.get("autocorr")
    if not isinstance(ac, dict) or not ac:
        return float("nan")

    try:
        vals = [float(v) for v in ac.values()]
        return max(abs(v) for v in vals)
    except Exception:
        return float("nan")


def safe_get_ngram_best(data: Dict[str, Any]) -> float:
    """Restituisce la miglior accuracy n-gram, calcolandola se necessario."""
    # Eventuale campo già pronto
    if "ngram_best" in data:
        return float(data["ngram_best"])

    ng = data.get("ngram")
    if not isinstance(ng, dict) or not ng:
        return float("nan")

    try:
        vals = [float(v) for v in ng.values()]
        return max(vals)
    except Exception:
        return float("nan")


def safe_get_schur(data: Dict[str, Any]) -> Dict[str, Any]:
    sch = data.get("schur", {}) or {}
    res = {
        "triples": sch.get("triples", float("nan")),
        "count": sch.get("count", float("nan")),
        "expected": sch.get("expected", float("nan")),
        "fraction": sch.get("fraction", float("nan")),
        "z": sch.get("z", float("nan")),
        "first_violation_index": sch.get("first_violation_index", None),
    }
    return res


def fmt(x: Any, digits: int = 4) -> str:
    try:
        if x is None:
            return "-"
        if isinstance(x, float):
            if math.isnan(x):
                return "nan"
            return f"{x:.{digits}f}"
        return str(x)
    except Exception:
        return str(x)


def severity_and_score(
    r: Dict[str, Any],
    baseline: Optional[Dict[str, Any]] = None,
) -> Tuple[str, float]:
    """
    Calcola una severità (green/yellow/red) e uno score numerico.
    L'idea è avere uno score >1 se qualcosa è un po' strano rispetto alla baseline
    o ai valori 'attesi' generici.
    """
    chi2 = float(r.get("chi_square", float("nan")))
    comp = float(r.get("compress_ratio", float("nan")))
    runsZ, _ = safe_get_runs(r)
    ac_max = safe_get_autocorr_max(r)
    sch = safe_get_schur(r)
    sch_z = float(sch.get("z", float("nan")))
    ngram_best = safe_get_ngram_best(r)

    # baseline (se fornita)
    if baseline is not None:
        b_chi2 = float(baseline.get("chi_square", float("nan")))
        b_comp = float(baseline.get("compress_ratio", float("nan")))
        b_runsZ, _ = safe_get_runs(baseline)
        b_ac = safe_get_autocorr_max(baseline)
        b_sch_z = float(safe_get_schur(baseline).get("z", float("nan")))
        b_ng = safe_get_ngram_best(baseline)
    else:
        b_chi2 = b_comp = b_runsZ = b_ac = b_sch_z = b_ng = float("nan")

    score = 0.0
    weight_sum = 0.0

    def add_term(val: float, ref: float, scale: float = 1.0, hard_ref: Optional[float] = None):
        nonlocal score, weight_sum
        if math.isnan(val):
            return
        base = ref
        if math.isnan(base) and hard_ref is not None:
            base = hard_ref
        if math.isnan(base):
            # non abbiamo né baseline né riferimento assoluto → saltiamo
            return
        # normalizza come dev standardizzata approx
        s = abs((val - base) / max(scale, 1e-9))
        score += s
        weight_sum += 1.0

    # euristiche:
    add_term(chi2, b_chi2, scale=5.0, hard_ref=10.0)  # 10 ≈ valore medio per df=9
    add_term(comp, b_comp, scale=0.02, hard_ref=0.48)  # atteso ~0.46–0.50
    add_term(runsZ, b_runsZ, scale=1.0, hard_ref=0.0)  # Z vicino allo 0
    add_term(ac_max, b_ac, scale=0.01, hard_ref=0.0)  # atteso ac_max piccolo
    add_term(sch_z, b_sch_z, scale=1.0, hard_ref=0.0)  # z Schur vicino 0
    add_term(ngram_best, b_ng, scale=0.01, hard_ref=0.10)  # ~10%

    if weight_sum > 0:
        norm_score = score / weight_sum
    else:
        norm_score = 0.0

    # mapping grezzo severità
    if norm_score < 0.8:
        sev = "green"
    elif norm_score < 1.8:
        sev = "yellow"
    else:
        sev = "red"

    return sev, norm_score


def main() -> None:
    ap = argparse.ArgumentParser(description="Confronta report JSON di digit-probe.")
    ap.add_argument("reports", nargs="+", help="Report JSON da confrontare")
    ap.add_argument("--baseline", help="Report JSON da usare come baseline per Δ e score")
    ap.add_argument("--csv", help="Esporta un CSV riassuntivo")
    ap.add_argument("--md", help="Esporta tabella Markdown riassuntiva")
    args = ap.parse_args()

    reports: List[Dict[str, Any]] = [load_report(p) for p in args.reports]

    baseline_data: Optional[Dict[str, Any]] = None
    if args.baseline:
        # baseline può essere anche uno dei report
        for r in reports:
            if os.path.abspath(r["_path"]) == os.path.abspath(args.baseline):
                baseline_data = r
                break
        if baseline_data is None:
            baseline_data = load_report(args.baseline)

    # arricchisci con metriche derivate
    enriched = []
    for r in reports:
        runsZ, runs_p = safe_get_runs(r)
        ac_max = safe_get_autocorr_max(r)
        sch = safe_get_schur(r)
        ngram_best = safe_get_ngram_best(r)

        sev, score = severity_and_score(r, baseline=baseline_data)

        row = {
            "name": r["_name"],
            "path": r["_path"],
            "N": r.get("N", r.get("TOTAL_DIGITS", float("nan"))),
            "chi2": float(r.get("chi_square", float("nan"))),
            "compress_ratio": float(r.get("compress_ratio", float("nan"))),
            "runsZ": runsZ,
            "runs_p": runs_p,
            "max_abs_autocorr": ac_max,
            "ngram_best": ngram_best,
            "sch_z": float(sch.get("z", float("nan"))),
            "sch_count": float(sch.get("count", float("nan"))),
            "sch_expected": float(sch.get("expected", float("nan"))),
            "sch_fraction": float(sch.get("fraction", float("nan"))),
            "severity": sev,
            "score": score,
        }
        enriched.append(row)

    # stampa per-file
    for row in enriched:
        print(
            f"▶ {row['name']}  (N={row['N']})  "
            f"{'🟢' if row['severity']=='green' else '🟡' if row['severity']=='yellow' else '🔴'} "
            f"severity={row['severity']}  score={fmt(row['score'],4)}"
        )
        print(
            f"  chi²={fmt(row['chi2'])} [green] | comp={fmt(row['compress_ratio'])} | "
            f"runs(Z,p)=({fmt(row['runsZ'])},{fmt(row['runs_p'])})"
        )
        print(
            f"  max|autocorr|={fmt(row['max_abs_autocorr'])} [green] | ngram_best={fmt(row['ngram_best'])}"
        )
        print(
            f"  Schur: z={fmt(row['sch_z'])} [green]  count={fmt(row['sch_count'])}  "
            f"expected≈{fmt(row['sch_expected'])}  frac={fmt(row['sch_fraction'])}"
        )
        print()

    # ordina per (score, |Schur z|, chi², max|ac|)
    def sort_key(row: Dict[str, Any]):
        return (
            row["score"],
            abs(row["sch_z"]) if not math.isnan(row["sch_z"]) else float("inf"),
            row["chi2"] if not math.isnan(row["chi2"]) else float("inf"),
            row["max_abs_autocorr"] if not math.isnan(row["max_abs_autocorr"]) else float("inf"),
        )

    enriched_sorted = sorted(enriched, key=sort_key)

    # stampa confronto tabellare semplice
    print("=== COMPARISON (sorted by AnomalyScore, |Schur z|, chi², max|ac|) ===")
    print(
        "file | N | severity | score | chi² | Δχ² | comp | Δcomp | runsZ | ΔrunsZ | "
        "max|ac| | Δmax|ac| | ngram_best | Δngram | Schur z | ΔSchur z"
    )

    # baseline numerica per Δ
    if baseline_data is not None:
        b_row = None
        for r in enriched:
            if os.path.abspath(r["path"]) == os.path.abspath(baseline_data["_path"]):
                b_row = r
                break
    else:
        b_row = None

    def delta(val: float, base: Optional[float]) -> float:
        if base is None or math.isnan(base) or math.isnan(val):
            return float("nan")
        return val - base

    for row in enriched_sorted:
        if b_row is not None:
            d_chi2 = delta(row["chi2"], b_row["chi2"])
            d_comp = delta(row["compress_ratio"], b_row["compress_ratio"])
            d_runsZ = delta(row["runsZ"], b_row["runsZ"])
            d_ac = delta(row["max_abs_autocorr"], b_row["max_abs_autocorr"])
            d_ng = delta(row["ngram_best"], b_row["ngram_best"])
            d_sch = delta(row["sch_z"], b_row["sch_z"])
        else:
            d_chi2 = d_comp = d_runsZ = d_ac = d_ng = d_sch = float("nan")

        print(
            f"{row['name']} | {row['N']} | {row['severity']} | {fmt(row['score'],4)} | "
            f"{fmt(row['chi2'])} | {fmt(d_chi2)} | "
            f"{fmt(row['compress_ratio'])} | {fmt(d_comp)} | "
            f"{fmt(row['runsZ'])} | {fmt(d_runsZ)} | "
            f"{fmt(row['max_abs_autocorr'])} | {fmt(d_ac)} | "
            f"{fmt(row['ngram_best'])} | {fmt(d_ng)} | "
            f"{fmt(row['sch_z'])} | {fmt(d_sch)}"
        )

    # CSV opzionale
    if args.csv:
        import csv

        with open(args.csv, "w", newline="", encoding="utf8") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "file",
                    "N",
                    "chi_square",
                    "compress_ratio",
                    "runs_Z",
                    "runs_p",
                    "max_abs_autocorr",
                    "ngram_best",
                    "sch_z",
                    "sch_count",
                    "sch_expected",
                    "sch_fraction",
                    "severity",
                    "score",
                ]
            )
            for row in enriched:
                w.writerow(
                    [
                        row["name"],
                        row["N"],
                        row["chi2"],
                        row["compress_ratio"],
                        row["runsZ"],
                        row["runs_p"],
                        row["max_abs_autocorr"],
                        row["ngram_best"],
                        row["sch_z"],
                        row["sch_count"],
                        row["sch_expected"],
                        row["sch_fraction"],
                        row["severity"],
                        row["score"],
                    ]
                )
        print(f"[csv] scritto: {args.csv}")

    # Markdown opzionale
    if args.md:
        with open(args.md, "w", encoding="utf8") as f:
            f.write("# Digit-Probe Compare\n\n")
            if baseline_data is not None:
                f.write(f"**Baseline:** `{os.path.basename(baseline_data['_path'])}`\n\n")
            f.write(
                "| file | N | severity | score | chi² | comp | runsZ | max|ac| | ngram_best | Schur z |\n"
            )
            f.write("|---|---:|:--:|--:|--:|--:|--:|--:|--:|--:|\n")
            for row in enriched_sorted:
                f.write(
                    f"| {row['name']} | {row['N']} | {row['severity']} | {fmt(row['score'],4)} | "
                    f"{fmt(row['chi2'])} | {fmt(row['compress_ratio'])} | {fmt(row['runsZ'])} | "
                    f"{fmt(row['max_abs_autocorr'])} | {fmt(row['ngram_best'])} | {fmt(row['sch_z'])} |\n"
                )
        print(f"[md] scritto: {args.md}")


if __name__ == "__main__":
    main()
