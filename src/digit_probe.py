#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
digit_probe.py
Analizzatore statistico/strutturale per sequenze numeriche:
- Modalità "digits": file di sole cifre 0..9 (senza spazi/newline)
- Modalità "integers": file di interi (uno per riga), alfabeto dichiarato via --alphabet

Metriche:
- Distribuzione, chi-square, z-score per simbolo
- Runs test (pari/dispari)
- Gaps per simbolo (conteggio e gap medio)
- Autocorrelazione (lag 1..5)
- Compression ratio (zlib)
- N-gram predictor (n = 1..3) con split 80/20
- SchurProbe: test a coppie (i<j) con c = (i+j) mod R e verifica (a+b) ≡ seq[c] (mod M)
  * N_triples = C(R,2) → atteso = N_triples / M ; var = N p (1-p); z-score standard

Output: stampa leggibile + opzionale JSON con --report-json (compatibile con compare_reports.py)
"""

import argparse
import collections
import json
import math
import statistics
import zlib
from typing import Dict, List, Optional, Tuple

# ---------- Helpers I/O ----------


def read_digits_file(path: str, n: Optional[int] = None) -> List[int]:
    with open(path, "r", encoding="utf8", errors="ignore") as f:
        data = f.read()
    digits = [ord(c) - 48 for c in data if "0" <= c <= "9"]
    if n is not None:
        digits = digits[:n]
    return digits


def read_integers_file(path: str, n: Optional[int] = None) -> List[int]:
    out = []
    with open(path, "r", encoding="utf8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                v = int(line)
            except Exception:
                continue
            out.append(v)
            if n is not None and len(out) >= n:
                break
    return out


def compress_ratio_bytes(b: bytes) -> float:
    if not b:
        return float("nan")
    comp = zlib.compress(b, level=6)
    return len(comp) / float(len(b))


# ---------- Statistiche base ----------


def counts_and_chi_square(seq: List[int], M: int) -> Tuple[Dict[int, int], float, float]:
    """Ritorna: counts per simbolo, chi-square, expected per bin."""
    cnt = {i: 0 for i in range(M)}
    for x in seq:
        if 0 <= x < M:
            cnt[x] += 1
    N = len(seq)
    if M == 0 or N == 0:
        return cnt, float("nan"), float("nan")
    expected = N / float(M)
    chi2 = 0.0
    for i in range(M):
        dev = cnt[i] - expected
        chi2 += (dev * dev) / (expected if expected > 0 else 1.0)
    return cnt, chi2, expected


def zscores_per_symbol(counts: Dict[int, int], expected: float) -> Dict[int, float]:
    """Z = (obs - E)/sqrt(E) per ciascun simbolo; se E==0 -> 0."""
    z = {}
    if expected <= 0:
        for k in counts:
            z[k] = 0.0
        return z
    s = math.sqrt(expected)
    for k, v in counts.items():
        z[k] = (v - expected) / s
    return z


def runs_test_even_odd(seq: List[int]) -> Tuple[float, float]:
    """Runs test su parità (even/odd). Ritorna Z e p(two-tailed) approx (normale)."""
    N = len(seq)
    if N < 2:
        return float("nan"), float("nan")
    # Classi: even(0), odd(1)
    classes = [x & 1 for x in seq]
    n0 = sum(1 for c in classes if c == 0)
    n1 = N - n0
    if n0 == 0 or n1 == 0:
        return float("nan"), float("nan")

    R = 1
    for i in range(1, N):
        if classes[i] != classes[i - 1]:
            R += 1

    mu = 1 + (2 * n0 * n1) / N
    var = (2 * n0 * n1 * (2 * n0 * n1 - N)) / (N * N * (N - 1)) if N > 1 else 0.0
    sigma = math.sqrt(var) if var > 0 else 0.0
    Z = (R - mu) / sigma if sigma > 0 else 0.0
    # Approssimiamo p con normale standard (due code)
    try:
        # senza scipy: uso erfc
        p_two = math.erfc(abs(Z) / math.sqrt(2.0))
    except Exception:
        p_two = float("nan")
    return Z, p_two


def top_k_by_freq(counts: Dict[int, int], k: int = 5) -> List[Tuple[int, int]]:
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]


def gaps_summary(seq: List[int], M: int) -> Dict[int, Tuple[int, float]]:
    """Per ogni simbolo, calcola (#gap, gap medio)."""
    last = {i: None for i in range(M)}
    gaps_count = {i: 0 for i in range(M)}
    gaps_sum = {i: 0 for i in range(M)}
    for idx, x in enumerate(seq):
        if 0 <= x < M:
            if last[x] is not None:
                gaps_count[x] += 1
                gaps_sum[x] += idx - last[x]
            last[x] = idx
    out = {}
    for i in range(M):
        c = gaps_count[i]
        mean_gap = (gaps_sum[i] / c) if c > 0 else float("inf")
        out[i] = (c, mean_gap)
    return out


def autocorr_lags(seq: List[int], lags: List[int]) -> Dict[int, float]:
    """Autocorrelazione di Pearson per lag in lags; seq come interi."""
    N = len(seq)
    if N < 2:
        return {lag: float("nan") for lag in lags}
    mu = statistics.mean(seq)
    # varianza (uso denominatore N)
    denom = sum((x - mu) * (x - mu) for x in seq)
    if denom == 0:
        return {lag: 0.0 for lag in lags}
    out = {}
    for L in lags:
        if L <= 0 or L >= N:
            out[L] = float("nan")
            continue
        num = 0.0
        for i in range(N - L):
            num += (seq[i] - mu) * (seq[i + L] - mu)
        out[L] = num / denom
    return out


# ---------- N-gram predictor (n=1..3) ----------


def ngram_predictor_accuracy(seq: List[int], M: int, n: int, train_frac: float = 0.8) -> float:
    """Modello Markov n-gram (frequenze massime) con split 80/20; accuracy sul test."""
    N = len(seq)
    if N < 4:
        return float("nan")
    trainN = int(N * train_frac)
    if trainN < n + 1:
        trainN = min(N - 1, max(n + 1, int(N * 0.7)))
    train = seq[:trainN]
    test = seq[trainN:]

    if n == 1:
        # modello unigram: predice il simbolo più frequente nel train
        cnt = collections.Counter(train)
        if not cnt:
            return float("nan")
        top = cnt.most_common(1)[0][0]
        correct = sum(1 for x in test if x == top)
        return correct / len(test) if test else float("nan")

    # n>=2
    trans = {}  # key: tuple(context), val: Counter(next)
    for i in range(n, len(train)):
        ctx = tuple(train[i - n : i])
        nxt = train[i]
        c = trans.get(ctx)
        if c is None:
            c = collections.Counter()
            trans[ctx] = c
        c[nxt] += 1

    correct = 0
    total = 0
    for i in range(n, len(test)):
        ctx = tuple(test[i - n : i])
        nxt = test[i]
        # se contesto mai visto -> fallback a unigram su train
        if ctx not in trans:
            # fallback
            # predici il simbolo più frequente del train
            # (già calcolato per n=1, ma ricalcolo semplice)
            top = collections.Counter(train).most_common(1)[0][0]
        else:
            top = trans[ctx].most_common(1)[0][0]
        correct += 1 if top == nxt else 0
        total += 1
    return (correct / total) if total > 0 else float("nan")


# ---------- SchurProbe (pair-based, c = (i+j) mod R) ----------


def schur_probe(seq: List[int], M: int, Rcap: int = 5000) -> Dict[str, float]:
    """
    Test additivo:
      - Prendiamo R = min(len(seq), Rcap)
      - Per ogni coppia i<j (N_triples = C(R,2)), definiamo k = (i+j) % R
      - Verifica: (seq[i] + seq[j]) % M == seq[k]
      - Atteso (iid uniforme): p = 1/M; E = N*p; Var = N p (1-p); z = (count - E)/sqrt(Var)

    Ritorna dict con chiavi:
      - triples, count, expected, fraction, z, first_violation_index
    """
    R = min(len(seq), Rcap)
    if R < 3 or M <= 0:
        return {
            "triples": 0,
            "count": 0,
            "expected": 0.0,
            "fraction": 0.0,
            "z": float("nan"),
            "first_violation_index": None,
        }

    N_tr = R * (R - 1) // 2
    p = 1.0 / float(M)
    expected = N_tr * p
    var = expected * (1.0 - p)  # binomiale
    sigma = math.sqrt(var) if var > 0 else 0.0

    count = 0
    first_idx = None  # memorizza j (o indice lineare) del primo "match"
    # Itera coppie
    # Per evitare di fare modulo ad ogni passo, è ok mantenerlo semplice
    for i in range(R - 1):
        ai = seq[i]
        for j in range(i + 1, R):
            k = (i + j) % R
            if ((ai + seq[j]) % M) == (seq[k] % M):
                count += 1
                if first_idx is None:
                    first_idx = j

    z = (count - expected) / sigma if sigma > 0 else 0.0
    frac = count / float(N_tr) if N_tr > 0 else 0.0
    return {
        "triples": N_tr,
        "count": count,
        "expected": expected,
        "fraction": frac,
        "z": z,
        "first_violation_index": first_idx,
    }


# ---------- Modalità di analisi ----------


def analyze_digits_mode(
    seq: List[int],
    Ncap: Optional[int],
    mc: Optional[int],
    schur_N: int,
    report_json_path: Optional[str],
) -> None:
    # trim
    if Ncap is not None and Ncap > 0:
        seq = seq[:Ncap]
    N = len(seq)
    M = 10

    print(f"MODE: digits  |  TOTAL DIGITS: {N}")

    # Distribuzione + chi2
    counts, chi2, expected = counts_and_chi_square(seq, M)
    for d in range(M):
        print(f"  {d}: {counts.get(d,0)}")
    print(f"\nChi-square (10 bins): {chi2:.4f} (expected per bin={expected:.2f})\n")

    # Z-scores simbolo
    zs = zscores_per_symbol(counts, expected if expected == expected else 0.0)
    print("Z-scores per digit:")
    for d in range(M):
        sign = "+" if zs[d] >= 0 else ""
        print(f"  {d}: {sign}{zs[d]:.3f}")
    print()

    # Runs test (even/odd)
    Z, p = runs_test_even_odd(seq)
    print(f"Runs test (even/odd): Z={Z:.3f}, p={p if p==p else float('nan'):.3f}\n")

    # Gaps
    gaps = gaps_summary(seq, M)
    print("Gaps summary (count, mean gap):")
    for d in range(M):
        c, g = gaps[d]
        mg = f"{g:.2f}" if math.isfinite(g) else "inf"
        print(f"  {d}: {c} gaps, mean {mg}")
    print()

    # Autocorrelazione
    ac = autocorr_lags(seq, [1, 2, 3, 4, 5])
    print("Autocorrelation (lags 1..5):")
    for L in [1, 2, 3, 4, 5]:
        v = ac[L]
        sign = "+" if v >= 0 else ""
        print(f"  lag 1: {sign}{v:.4f}" if L == 1 else f"  lag {L}: {sign}{v:.4f}")
    print()

    # Compression ratio
    s = "".join(chr(48 + x) for x in seq).encode("ascii", errors="ignore")
    comp = compress_ratio_bytes(s)
    print(f"Compression ratio (zlib over text): {comp:.4f}")
    if comp <= 0.44:
        print(
            "  --> sotto ~0.44; può indicare ripetizioni o testo breve (limite teorico ~0.415 per alfabeto 10)."
        )
    else:
        print("  --> compatibile con sequenze random-like su alfabeto 10.")
    print()

    # N-gram predictor (n=1..3)
    print("N-gram predictor (80/20 split):")
    best_acc = {}
    for n in (1, 2, 3):
        acc = ngram_predictor_accuracy(seq, M, n)
        best_acc[n] = acc
        print(f"  n={n}: {acc*100:.4f}% (baseline≈{100.0/M:.0f}%)")
    print()

    # SchurProbe
    print("SchurProbe (first 5000 symbols):")
    sch = schur_probe(seq, M, Rcap=schur_N)
    if sch["first_violation_index"] is not None:
        print(f"  first violation at index {sch['first_violation_index']}")
    print(f"  triples={sch['triples']:,}  count={sch['count']}  expected≈{sch['expected']:.0f}")
    print(f"  fraction={sch['fraction']:.8f}  z={sch['z']:+.2f}\n")

    # JSON report
    if report_json_path:
        report = {
            "mode": "digits",
            "N": N,
            "alphabet": M,
            "chi_square": chi2,
            "expected_per_bin": expected,
            "counts": counts,
            "zscores": {int(k): float(v) for k, v in zs.items()},
            "runs": {"Z": float(Z), "p_two_tailed": float(p) if p == p else None},
            "gaps": {
                int(k): {
                    "count": int(v[0]),
                    "mean": (float(v[1]) if math.isfinite(v[1]) else None),
                }
                for k, v in gaps.items()
            },
            "autocorr": {int(k): float(v) for k, v in ac.items()},
            "compress_ratio": comp,
            "ngram": {int(k): float(v) for k, v in best_acc.items()},
            "schur": {
                "triples": int(sch["triples"]),
                "count": int(sch["count"]),
                "expected": float(sch["expected"]),
                "fraction": float(sch["fraction"]),
                "z": float(sch["z"]),
                "first_violation_index": (
                    int(sch["first_violation_index"])
                    if sch["first_violation_index"] is not None
                    else None
                ),
            },
        }
        with open(report_json_path, "w", encoding="utf8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"[report-json] scritto: {report_json_path}")


def analyze_integers_mode(
    seq: List[int],
    alphabet: int,
    Ncap: Optional[int],
    schur_N: int,
    report_json_path: Optional[str],
) -> None:
    if Ncap is not None and Ncap > 0:
        seq = seq[:Ncap]
    N = len(seq)
    M = alphabet
    if M <= 0:
        raise SystemExit("[err] --alphabet è richiesto e deve essere > 0 in modalità --integers")

    # clamp values to [0..M-1] se necessario
    max_obs = max(seq) if seq else -1
    seq_mod = [x % M for x in seq]

    print(f"MODE: integers  |  N={N}  alphabet M={M}  (max_observed={max_obs})\n")

    # Distribuzione + chi2
    counts, chi2, expected = counts_and_chi_square(seq_mod, M)
    print(f"Chi-square (M={M} bins): {chi2:.4f} (expected per bin={expected:.2f})\n")

    # Runs su parità
    Z, p = runs_test_even_odd(seq_mod)
    print(f"Runs test (even/odd values): Z={Z:.3f}, p={p if p==p else float('nan'):.3f}\n")

    # Gaps (top-5 per frequenza)
    gaps = gaps_summary(seq_mod, M)
    top5 = top_k_by_freq(counts, k=5)
    print("Gaps summary (top-5 symbols by freq):")
    for sym, _ in top5:
        c, g = gaps[sym]
        mg = f"{g:.2f}" if math.isfinite(g) else "inf"
        print(f"  {sym}: {c} gaps, mean {mg}")
    print()

    # Autocorrelazione
    ac = autocorr_lags(seq_mod, [1, 2, 3, 4, 5])
    print("Autocorrelation (lags 1..5):")
    for L in [1, 2, 3, 4, 5]:
        v = ac[L]
        sign = "+" if v >= 0 else ""
        print(f"  lag 1: {sign}{v:.4f}" if L == 1 else f"  lag {L}: {sign}{v:.4f}")
    print()

    # Compression ratio (integers → testo con newline)
    txt = ("\n".join(str(x) for x in seq_mod) + "\n").encode("utf8", errors="ignore")
    comp = compress_ratio_bytes(txt)
    print(f"Compression ratio (zlib over 'ints text'): {comp:.4f}\n")

    # N-gram (n=1..3)
    print("N-gram predictor (80/20 split) over integer symbols:")
    best_acc = {}
    for n in (1, 2, 3):
        acc = ngram_predictor_accuracy(seq_mod, M, n)
        best_acc[n] = acc
        base = 100.0 / M if M > 0 else 0.0
        print(f"  n={n}: {acc*100:.4f}% (baseline≈{base:.2f}%)")
    print()

    # SchurProbe
    print("SchurProbe (first 5000 symbols):")
    sch = schur_probe(seq_mod, M, Rcap=schur_N)
    if sch["first_violation_index"] is not None:
        print(f"  first violation at index {sch['first_violation_index']}")
    print(
        f"  triples={sch['triples']:,}  count={sch['count']}  expected≈{sch['expected']:.0f}  "
        f"frac={sch['fraction']:.6f}  z={sch['z']:+.2f}\n"
    )

    # JSON report
    if report_json_path:
        report = {
            "mode": "integers",
            "N": N,
            "alphabet": M,
            "chi_square": chi2,
            "expected_per_bin": expected,
            "counts": counts,
            "runs": {"Z": float(Z), "p_two_tailed": float(p) if p == p else None},
            "gaps_top5": {
                int(sym): {
                    "count": int(gaps[sym][0]),
                    "mean": (float(gaps[sym][1]) if math.isfinite(gaps[sym][1]) else None),
                }
                for sym, _ in top5
            },
            "autocorr": {int(k): float(v) for k, v in ac.items()},
            "compress_ratio": comp,
            "ngram": {int(k): float(v) for k, v in best_acc.items()},
            "schur": {
                "triples": int(sch["triples"]),
                "count": int(sch["count"]),
                "expected": float(sch["expected"]),
                "fraction": float(sch["fraction"]),
                "z": float(sch["z"]),
                "first_violation_index": (
                    int(sch["first_violation_index"])
                    if sch["first_violation_index"] is not None
                    else None
                ),
            },
        }
        with open(report_json_path, "w", encoding="utf8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"[report-json] scritto: {report_json_path}")


# ---------- main ----------


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="digit-probe: analisi di sequenze di cifre/interi")
    ap.add_argument(
        "--file",
        required=True,
        help="Input file: digits (senza spazi) o integers (uno per riga)",
    )
    ap.add_argument("--n", type=int, default=None, help="Limita la lunghezza analizzata")
    ap.add_argument(
        "--integers",
        action="store_true",
        help="Abilita modalità interi (uno per riga).",
    )
    ap.add_argument(
        "--alphabet",
        type=int,
        default=None,
        help="Alfabeto per modalità integers (obbligatorio se --integers).",
    )
    ap.add_argument(
        "--report-json",
        type=str,
        default=None,
        help="Scrive un report JSON compatibile con compare_reports.py",
    )
    # opzioni legacy / placeholder
    ap.add_argument(
        "--mc",
        type=int,
        default=None,
        help="(opzionale) Monte Carlo reps baseline (non obbligatorio)",
    )
    ap.add_argument(
        "--schur-N",
        dest="schur_N",
        type=int,
        default=5000,
        help="R massimo per SchurProbe (default: 5000)",
    )
    return ap.parse_args()


def main() -> None:
    a = parse_args()

    if a.integers:
        if a.alphabet is None or a.alphabet <= 0:
            raise SystemExit("[err] in modalità --integers devi fornire --alphabet > 0")
        seq = read_integers_file(a.file, a.n)
        analyze_integers_mode(seq, a.alphabet, a.n, a.schur_N, a.report_json)
    else:
        seq = read_digits_file(a.file, a.n)
        analyze_digits_mode(seq, a.n, a.mc, a.schur_N, a.report_json)


if __name__ == "__main__":
    main()
