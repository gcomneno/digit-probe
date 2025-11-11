#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compare_reports.py (v1.1)
Confronta report JSON prodotti da digit_probe.py, con severity, anomaly score e export Markdown/CSV.
"""
from __future__ import annotations
import argparse, json, os, sys, math, csv
from typing import Any, Dict, List, Optional

# ---------- utils ----------
def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf8") as f:
        return json.load(f)

def safe_get(d: Dict[str, Any], path: List[str], default=None):
    cur = d
    try:
        for k in path:
            cur = cur[k]
        return cur
    except Exception:
        return default

def max_abs(values: List[float]) -> float:
    vals = [v for v in values if isinstance(v, (int, float))]
    return max((abs(v) for v in vals), default=float("nan"))

def fmt(x, digits=4):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "nan"
    if isinstance(x, float):
        return f"{x:.{digits}f}"
    return str(x)

# ---------- core ----------
def summarize_report(path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    N          = data.get("N")
    chi        = data.get("chi_square")
    comp       = data.get("compress_ratio")
    runsZ      = safe_get(data, ["runs", "Z"])
    runsP      = safe_get(data, ["runs", "p"])
    autocorr   = data.get("autocorr", [])
    max_ac     = max_abs(autocorr)
    ngram      = data.get("n_gram", {})
    ngram_max  = max(ngram.values()) if isinstance(ngram, dict) and ngram else float("nan")
    sch_count  = safe_get(data, ["schur", "count"])
    sch_exp    = safe_get(data, ["schur", "expected"])
    sch_z      = safe_get(data, ["schur", "z"])
    sch_frac   = safe_get(data, ["schur", "fraction"])

    # Severity euristica:
    # - Schur |z|   : green <3, yellow 3..6, red >6
    # - chi-square  : green < 30, yellow 30..60, red > 60  (per 10 classi; tarabile)
    # - max|ac|     : green < 0.01, yellow 0.01..0.03, red > 0.03
    sev_sch = "green" if (isinstance(sch_z,(int,float)) and abs(sch_z)<3) else ("yellow" if isinstance(sch_z,(int,float)) and abs(sch_z)<=6 else "red")
    sev_chi = "green" if (isinstance(chi,(int,float)) and chi<30) else ("yellow" if isinstance(chi,(int,float)) and chi<=60 else "red")
    sev_ac  = "green" if (isinstance(max_ac,(int,float)) and max_ac<0.01) else ("yellow" if isinstance(max_ac,(int,float)) and max_ac<=0.03 else "red")
    # AnomalyScore semplice (pesi: Schur 0.6, chi 0.3, autocorr 0.1; normalizzato):
    score = 0.0
    if isinstance(sch_z,(int,float)): score += 0.6*min(10.0, abs(sch_z)/3.0)   # 1 unità ≈ 3σ
    if isinstance(chi,(int,float)):   score += 0.3*min(10.0, chi/30.0)         # 1 unità ≈ chi² 30
    if isinstance(max_ac,(int,float)):score += 0.1*min(10.0, max_ac/0.03)      # 1 unità ≈ 0.03
    # Severity globale: mappa score → colore
    sev_glob = "green" if score < 1.0 else ("yellow" if score < 2.0 else "red")

    return {
        "file": os.path.basename(path),
        "N": N,
        "chi_square": chi,
        "compress_ratio": comp,
        "runs_Z": runsZ,
        "runs_p": runsP,
        "autocorr": autocorr,
        "max_abs_autocorr": max_ac,
        "ngram_best": ngram_max,
        "sch_count": sch_count,
        "sch_expected": sch_exp,
        "sch_z": sch_z,
        "sch_fraction": sch_frac,
        "sev_schur": sev_sch,
        "sev_chi": sev_chi,
        "sev_ac": sev_ac,
        "anomaly_score": score,
        "severity": sev_glob,
    }

def compute_deltas(ref: Dict[str, Any], other: Dict[str, Any]) -> Dict[str, Optional[float]]:
    keys = ["chi_square", "compress_ratio", "runs_Z", "runs_p", "max_abs_autocorr", "ngram_best", "sch_z", "sch_fraction", "anomaly_score"]
    deltas = {}
    for k in keys:
        a = ref.get(k)
        b = other.get(k)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            deltas[k] = b - a
        else:
            deltas[k] = None
    return deltas

def anomaly_key(row: Dict[str, Any]) -> tuple:
    # Ordina per anomaly_score (desc), poi |Schur z|, poi chi², poi max|ac|
    z = row.get("sch_z")
    chi = row.get("chi_square")
    mac = row.get("max_abs_autocorr")
    score = row.get("anomaly_score")
    return (-(score if isinstance(score,(int,float)) else float("-inf")),
            -(abs(z) if isinstance(z,(int,float)) else float("-inf")),
            -(chi if isinstance(chi,(int,float)) else float("-inf")),
            -(mac if isinstance(mac,(int,float)) else float("-inf")))

# ---------- text I/O ----------
def color_emoji(sev:str)->str:
    return {"green":"🟢","yellow":"🟡","red":"🔴"}.get(sev,"⚪")

def print_single_summary(s: Dict[str, Any]):
    print(f"\n▶ {s['file']}  (N={s['N']})  {color_emoji(s['severity'])} severity={s['severity']}  score={fmt(s['anomaly_score'])}")
    print(f"  chi²={fmt(s['chi_square'])} [{s['sev_chi']}] | comp={fmt(s['compress_ratio'])} | runs(Z,p)=({fmt(s['runs_Z'])},{fmt(s['runs_p'])})")
    print(f"  max|autocorr|={fmt(s['max_abs_autocorr'])} [{s['sev_ac']}] | ngram_best={fmt(s['ngram_best'])}")
    print(f"  Schur: z={fmt(s['sch_z'])} [{s['sev_schur']}]  count={fmt(s['sch_count'],0)}  expected≈{fmt(s['sch_expected'],0)}  frac={fmt(s['sch_fraction'])}")

def print_comparison_table(rows: List[Dict[str, Any]], baseline: Optional[Dict[str, Any]] = None):
    headers = ["file","N","severity","score","chi²","Δχ²","comp","Δcomp","runsZ","ΔrunsZ","max|ac|","Δmax|ac|","ngram_best","Δngram","Schur z","ΔSchur z"]
    print("\n=== COMPARISON (sorted by AnomalyScore, |Schur z|, chi², max|ac|) ===")
    print(" | ".join(headers))
    ref = baseline
    for r in sorted(rows, key=anomaly_key):
        deltas = compute_deltas(ref, r) if ref else {}
        print(" | ".join([
            r["file"],
            str(r["N"]),
            r.get("severity","-"),
            fmt(r.get("anomaly_score")),
            fmt(r["chi_square"]),
            (fmt(deltas.get("chi_square")) if ref else "-"),
            fmt(r["compress_ratio"]),
            (fmt(deltas.get("compress_ratio")) if ref else "-"),
            fmt(r["runs_Z"]),
            (fmt(deltas.get("runs_Z")) if ref else "-"),
            fmt(r["max_abs_autocorr"]),
            (fmt(deltas.get("max_abs_autocorr")) if ref else "-"),
            fmt(r["ngram_best"]),
            (fmt(deltas.get("ngram_best")) if ref else "-"),
            fmt(r["sch_z"]),
            (fmt(deltas.get("sch_z")) if ref else "-"),
        ]))

def write_csv(path: str, rows: List[Dict[str, Any]]):
    fields = ["file","N","severity","anomaly_score","chi_square","compress_ratio","runs_Z","runs_p","max_abs_autocorr","ngram_best","sch_z","sch_count","sch_expected","sch_fraction"]
    with open(path,"w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in sorted(rows, key=anomaly_key):
            w.writerow({k:r.get(k) for k in fields})
    print(f"[csv] scritto: {path}")

def write_md(path: str, rows: List[Dict[str, Any]], baseline: Optional[Dict[str, Any]]):
    with open(path, "w", encoding="utf8") as f:
        f.write("# Digit-Probe Compare\n\n")
        if baseline:
            f.write(f"**Baseline:** `{baseline['file']}`\n\n")
        f.write("| file | N | severity | score | chi² | comp | runsZ | max|ac| | ngram_best | Schur z |\n")
        f.write("|---|---:|:--:|--:|--:|--:|--:|--:|--:|--:|\n")
        for r in sorted(rows, key=anomaly_key):
            f.write(f"| {r['file']} | {r['N']} | {r.get('severity','-')} | {fmt(r.get('anomaly_score'))} | "
                    f"{fmt(r['chi_square'])} | {fmt(r['compress_ratio'])} | {fmt(r['runs_Z'])} | "
                    f"{fmt(r['max_abs_autocorr'])} | {fmt(r['ngram_best'])} | {fmt(r['sch_z'])} |\n")
    print(f"[md] scritto: {path}")

# ---------- CLI ----------
def parse_args():
    ap = argparse.ArgumentParser(description="Confronta report JSON prodotti da digit_probe.py.")
    ap.add_argument("reports", nargs="+", help="Uno o più file .json.")
    ap.add_argument("--baseline", help="Report JSON da usare come baseline per Δ.")
    ap.add_argument("--csv", help="Esporta la tabella comparativa in CSV.")
    ap.add_argument("--md", help="Esporta tabella in Markdown.")
    return ap.parse_args()

def main():
    a = parse_args()
    rows=[]
    for p in a.reports:
        if not os.path.exists(p):
            print(f"[warn] file non trovato: {p}", file=sys.stderr)
            continue
        try:
            data=load_json(p)
            rows.append(summarize_report(p,data))
        except Exception as e:
            print(f"[warn] errore su {p}: {e}", file=sys.stderr)
    if not rows: sys.exit("Nessun report valido.")

    base_row=None
    if a.baseline:
        if os.path.exists(a.baseline):
            base_row = summarize_report(a.baseline, load_json(a.baseline))
        else:
            print(f"[warn] baseline non trovata: {a.baseline}", file=sys.stderr)

    for r in rows:
        print_single_summary(r)

    print_comparison_table(rows, baseline=base_row)

    if a.csv:
        write_csv(a.csv, rows)
    if a.md:
        write_md(a.md, rows, base_row)

if __name__ == "__main__":
    main()
