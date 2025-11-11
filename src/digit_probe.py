#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
digit_probe.py (v3.0 — digits + integers/bucket)
Analisi statistica di sequenze:
- Modalità 'digits' (default): legge solo cifre 0..9 dal file.
- Modalità 'integers' (--integers): legge interi non negativi (p.es. bucket 0..2^k-1).

Metriche: chi², z-scores (solo digits), runs (pari/dispari), gaps, autocorr, compress ratio,
N-gram (80/20 split), SchurProbe (A+B=C con simboli uguali), Monte Carlo opzionale, JSON export.

Esempi:
  # DIGITS (π)
  python3 digit_probe.py --file pi_100k.txt --report-json pi.json

  # INTEGERS (bucket Turbo-B, k=8 ⇒ M=256)
  python3 digit_probe.py --file buckets.txt --integers --alphabet 256 --report-json buckets.json

  # Monte Carlo baseline
  python3 digit_probe.py --file buckets.txt --integers --alphabet 256 --mc 100
"""

from __future__ import annotations
import argparse, collections, math, os, sys, zlib, random, json
from typing import List, Dict, Any, Sequence, Tuple, Optional

# Optional dependency: mpmath (solo per --source digits)
try:
    import mpmath as mp
    MP_AVAIL = True
except Exception:
    MP_AVAIL = False

DIGITS = tuple(str(i) for i in range(10))

# ---------- I/O ----------
def load_digits_from_file(path: str, n: int | None = None) -> str:
    s = []
    with open(path, 'r', encoding='utf8') as fh:
        for line in fh:
            for ch in line:
                if ch.isdigit():
                    s.append(ch)
                if n and len(s) >= n:
                    break
            if n and len(s) >= n:
                break
    return ''.join(s) if n is None else ''.join(s[:n])

def load_integers_from_file(path: str, n: int | None = None) -> List[int]:
    txt = open(path, 'r', encoding='utf8').read()
    vals: List[int] = []
    cur = ""
    for ch in txt:
        if ch.isdigit():
            cur += ch
        else:
            if cur:
                vals.append(int(cur))
                if n and len(vals) >= n:
                    return vals
                cur = ""
    if cur:
        vals.append(int(cur))
    return vals if (n is None) else vals[:n]

def generate_constant_digits(kind: str, n: int) -> str:
    if not MP_AVAIL:
        raise RuntimeError("mpmath non disponibile: pip install mpmath")
    import mpmath as mp  # local import safe
    mp.mp.dps = max(50, n + 10)
    if kind == 'pi': s = mp.nstr(mp.pi, n + 2)
    elif kind in ('e', 'exp'): s = mp.nstr(mp.e, n + 2)
    else: raise ValueError("Costante sconosciuta: " + kind)
    digits = [ch for ch in s if ch.isdigit()]
    return ''.join(digits[:n])

# ---------- STAT BASE ----------
def digit_counts_str(seq: str) -> Dict[str, int]:
    c = collections.Counter(seq)
    return {d: c.get(d, 0) for d in DIGITS}

def counts_over_alphabet_int(seq: Sequence[int], M: int) -> List[int]:
    counts = [0]*M
    for v in seq:
        if 0 <= v < M:
            counts[v] += 1
    return counts

def chi_square_from_counts(counts: Sequence[int], expected: float) -> float:
    return sum((c-expected)**2/expected for c in counts)

def z_scores_digits(obs: Dict[str,int]) -> Dict[str,float]:
    N, p = sum(obs.values()), 0.1
    var = N*p*(1-p)
    σ = math.sqrt(var) if var>0 else float('nan')
    return {d: ((obs[d]-N*p)/σ if σ>0 else float('nan')) for d in DIGITS}

# ---------- RUNS TEST ----------
def runs_test_binary(binary_seq: List[int]) -> tuple[float,float]:
    n = len(binary_seq)
    n1 = sum(binary_seq); n2 = n - n1
    if n1==0 or n2==0 or n<20: return float('nan'), float('nan')
    runs = 1 + sum(binary_seq[i]!=binary_seq[i-1] for i in range(1,n))
    exp_r = 1 + 2*n1*n2/n
    var_r = (2*n1*n2*(2*n1*n2 - n))/(n**2*(n-1))
    if var_r <= 0: return float('nan'), float('nan')
    z = (runs-exp_r)/math.sqrt(var_r)
    p = 2*(1-0.5*(1+math.erf(abs(z)/math.sqrt(2))))
    return z,p

# ---------- AUTOCORR ----------
def autocorrelation(vals: Sequence[float], lag: int=1)->float:
    n=len(vals)
    if n<=lag: return float('nan')
    mean=sum(vals)/n
    num=sum((vals[i]-mean)*(vals[i+lag]-mean) for i in range(n-lag))
    den=sum((x-mean)**2 for x in vals)
    return num/den if den else float('nan')

# ---------- COMPRESS ----------
def compressibility_ratio_bytes(b: bytes)->float:
    if not b: return 1.0
    c = zlib.compress(b)
    return len(c)/len(b)

def compress_ratio_for_digits(seq_digits_text: str)->float:
    return compressibility_ratio_bytes(seq_digits_text.encode('ascii',errors='ignore'))

def compress_ratio_for_integers(seq_ints: Sequence[int])->float:
    # rappresentazione testuale "num num ..." per coerenza con input tipico
    s = " ".join(map(str, seq_ints)).encode('ascii', errors='ignore')
    return compressibility_ratio_bytes(s)

# ---------- N-GRAM (generico) ----------
class NGramPredictor:
    """
    N-gram su sequenze GENERICHE (hashable).
    Usa tuple di lunghezza n come contesto.
    """
    def __init__(self, n:int=2):
        assert n>=1
        self.n=n
        self.ctx: Dict[Tuple[Any,...], collections.Counter] = {}
        self.global_next = collections.Counter()

    def train(self, seq: Sequence[Any]):
        if len(seq)<=self.n: return
        for i in range(len(seq)-self.n):
            ctx = tuple(seq[i:i+self.n])
            nxt = seq[i+self.n]
            self.ctx.setdefault(ctx, collections.Counter())[nxt]+=1
            self.global_next[nxt]+=1

    def predict(self, ctx: Tuple[Any,...]) -> Any:
        c = self.ctx.get(ctx)
        if c and len(c)>0: return c.most_common(1)[0][0]
        if self.global_next: return self.global_next.most_common(1)[0][0]
        return None

    def accuracy_on(self, seq: Sequence[Any]) -> float:
        if len(seq)<=self.n: return float('nan')
        correct=0; total=0
        for i in range(len(seq)-self.n):
            ctx = tuple(seq[i:i+self.n])
            truth = seq[i+self.n]
            pred = self.predict(ctx)
            if pred == truth: correct += 1
            total += 1
        return correct/total if total>0 else float('nan')

# ---------- Monte Carlo ----------
def mc_random_digits(length:int, reps:int)->Dict[str,float]:
    rng = random.Random(1234567)
    chi_sum=0.0; comp_sum=0.0
    for _ in range(reps):
        seq = ''.join(rng.choice(DIGITS) for _ in range(length))
        counts = digit_counts_str(seq)
        chi_sum += chi_square_from_counts(counts.values(), length/10.0)
        comp_sum += compress_ratio_for_digits(seq)
    return {'chi_mean': chi_sum/reps, 'comp_mean': comp_sum/reps}

def mc_random_integers(length:int, M:int, reps:int)->Dict[str,float]:
    rng = random.Random(1234567)
    chi_sum=0.0; comp_sum=0.0
    for _ in range(reps):
        seq = [rng.randrange(M) for __ in range(length)]
        counts = counts_over_alphabet_int(seq, M)
        chi_sum += chi_square_from_counts(counts, length/M)
        comp_sum += compress_ratio_for_integers(seq)
    return {'chi_mean': chi_sum/reps, 'comp_mean': comp_sum/reps}

# ---------- Schur Probe ----------
def schur_probe_count_symbols(seq: Sequence[Any], max_n:int) -> tuple[int|None, int, int]:
    """
    Conta triple (i,j,k) con i+j=k < N_eff e seq[i]==seq[j]==seq[k].
    Restituisce (first_violation, total_count, N_eff).
    """
    n = min(len(seq), max_n)
    first=None; tot=0
    for i in range(1,n):
        si = seq[i]
        for j in range(1,n):
            k = i+j
            if k>=n: break
            if si == seq[j] == seq[k]:
                tot += 1
                if first is None:
                    first = k
    return first, tot, n

def schur_expected_from_empirical_counts(counts: Sequence[int], N: int) -> tuple[float, float]:
    """
    atteso = (#triples) * sum_d (p_d^3), con p_d = c_d/N
    """
    if N<=0: return 0.0, 0.0
    p_equal = 0.0
    for c in counts:
        p = c/N
        p_equal += p*p*p
    total_triples = (N-1)*N//2
    return total_triples*p_equal, p_equal

# ---------- ANALYSIS ----------
def analyze_digits_mode(seq_digits_text: str, limit_n:int|None, mc:int, schur_N:int, json_path:str|None):
    # cleanup + cutting
    seq = ''.join(ch for ch in seq_digits_text if ch.isdigit())
    if limit_n: seq = seq[:limit_n]
    N = len(seq)
    if N==0: print("No digits loaded."); return

    print(f"MODE: digits  |  TOTAL DIGITS: {N}")
    obs = digit_counts_str(seq)
    [print(f"  {d}: {obs[d]}") for d in DIGITS]

    exp = N/10.0
    chi = chi_square_from_counts(obs.values(), exp)
    print(f"\nChi-square (10 bins): {chi:.4f} (expected per bin={exp:.2f})")

    zs = z_scores_digits(obs)
    print("\nZ-scores per digit:")
    for d in DIGITS:
        print(f"  {d}: {zs[d]:+.3f}")

    # runs on even/odd
    bin_seq = [1 if (int(ch)%2==0) else 0 for ch in seq]
    z_run, p_run = runs_test_binary(bin_seq)
    print(f"\nRuns test (even/odd): Z={z_run:.3f}, p={p_run:.3f}")

    # gaps
    print("\nGaps summary (count, mean gap):")
    for d in DIGITS:
        idxs = [i for i,ch in enumerate(seq) if ch==d]
        if len(idxs)<=1: print(f"  {d}: <2 occurrences>")
        else:
            gaps = [idxs[i+1]-idxs[i] for i in range(len(idxs)-1)]
            print(f"  {d}: {len(gaps)} gaps, mean {sum(gaps)/len(gaps):.2f}")

    # autocorr over numeric values 0..9
    vals = [int(ch) for ch in seq]
    print("\nAutocorrelation (lags 1..5):")
    for lag in range(1,6):
        print(f"  lag {lag}: {autocorrelation(vals, lag):+.4f}")

    # compression (text)
    cr = compress_ratio_for_digits(seq)
    print(f"\nCompression ratio (zlib over text): {cr:.4f}")
    if cr < 0.44:
        print("  --> sotto ~0.44; può indicare ripetizioni o testo breve (limite teorico ~0.415 per alfabeto 10).")
    elif cr < 0.60:
        print("  --> compatibile con sequenze random-like su alfabeto 10.")
    else:
        print("  --> poco comprimibile (alta entropia o testo breve).")

    # N-gram (80/20)
    split = int(N*0.8); tr = list(seq[:split]); ts = list(seq[split:])
    print("\nN-gram predictor (80/20 split):")
    ngram_acc={}
    for n in (1,2,3):
        ng=NGramPredictor(n); ng.train(tr)
        acc=ng.accuracy_on(ts); ngram_acc[n]=acc
        print(f"  n={n}: {acc:.4%} (baseline≈10%)")

    # Schur
    print(f"\nSchurProbe (first {schur_N} symbols):")
    first, tot, N_eff = schur_probe_count_symbols(list(seq), schur_N)
    exp_sch, p_eq = schur_expected_from_empirical_counts([obs[d] for d in DIGITS], N_eff)
    tot_tri = (N_eff-1)*N_eff//2
    frac = tot/tot_tri if tot_tri else float('nan')
    σ = math.sqrt(exp_sch*(1-p_eq)) if exp_sch>0 else float('nan')
    z_sch = (tot-exp_sch)/σ if (σ and σ>0) else float('nan')
    if first is not None: print(f"  first violation at index {first}")
    print(f"  triples={tot_tri:,}  count={tot:,}  expected≈{int(exp_sch):,}  frac={frac:.5f}  z={z_sch:+.2f}")

    # MC baseline
    mc_mean=None
    if mc>0:
        mc_mean = mc_random_digits(N, mc)
        print(f"\nMonte Carlo baseline (digits, {mc} reps): χ²≈{mc_mean['chi_mean']:.4f}, comp≈{mc_mean['comp_mean']:.4f}")

    # JSON
    if json_path:
        metrics = {
            "mode":"digits","alphabet":10,"N":N,
            "chi_square":chi,
            "runs":{"Z":z_run,"p":p_run},
            "autocorr":[autocorrelation(vals,lag) for lag in range(1,6)],
            "compress_ratio":cr,
            "z_scores":zs,
            "n_gram":ngram_acc,
            "schur":{"count":tot,"expected":exp_sch,"z":z_sch,"fraction":frac,"N_eff":N_eff},
            "montecarlo":mc_mean,
        }
        with open(json_path,"w",encoding="utf8") as f: json.dump(metrics,f,indent=2)
        print(f"\n[report-json] scritto: {json_path}")

def analyze_integers_mode(seq_ints: List[int], M_hint:int|None, limit_n:int|None, mc:int, schur_N:int, json_path:str|None):
    # cut + deduce alphabet
    if limit_n: seq_ints = seq_ints[:limit_n]
    if not seq_ints: print("No integers loaded."); return
    maxv = max(seq_ints)
    if M_hint is None:
        M = maxv+1
    else:
        M = int(M_hint)
    # clamp to [0..M-1]
    seq = [v for v in seq_ints if 0 <= v < M]
    N = len(seq)
    if N==0: print("No integers in range 0..M-1."); return

    print(f"MODE: integers  |  N={N}  alphabet M={M}  (max_observed={maxv})")

    counts = counts_over_alphabet_int(seq, M)
    E = N/M
    chi = chi_square_from_counts(counts, E)
    print(f"\nChi-square (M={M} bins): {chi:.4f} (expected per bin={E:.2f})")

    # runs on parity of value
    bin_seq = [1 if (v%2==0) else 0 for v in seq]
    z_run, p_run = runs_test_binary(bin_seq)
    print(f"\nRuns test (even/odd values): Z={z_run:.3f}, p={p_run:.3f}")

    # simple gaps for a few frequent symbols (top 5)
    print("\nGaps summary (top-5 symbols by freq):")
    top5 = sorted(range(M), key=lambda x: counts[x], reverse=True)[:5]
    for sym in top5:
        idxs = [i for i,v in enumerate(seq) if v==sym]
        if len(idxs)<=1: print(f"  {sym}: <2 occurrences>")
        else:
            gaps = [idxs[i+1]-idxs[i] for i in range(len(idxs)-1)]
            print(f"  {sym}: {len(gaps)} gaps, mean {sum(gaps)/len(gaps):.2f}")

    # autocorr on raw values (scaled optional)
    print("\nAutocorrelation (lags 1..5):")
    vals = list(map(float, seq))
    for lag in range(1,6):
        print(f"  lag {lag}: {autocorrelation(vals, lag):+.4f}")

    # compression on textual ints (just heuristic)
    cr = compress_ratio_for_integers(seq)
    print(f"\nCompression ratio (zlib over 'ints text'): {cr:.4f}")

    # N-gram (80/20) on INTEGER symbols
    split = int(N*0.8); tr = seq[:split]; ts = seq[split:]
    print("\nN-gram predictor (80/20 split) over integer symbols:")
    ngram_acc={}
    for n in (1,2,3):
        ng=NGramPredictor(n); ng.train(tr)
        acc=ng.accuracy_on(ts); ngram_acc[n]=acc
        base = 1.0/M if M>0 else float('nan')
        print(f"  n={n}: {acc:.4%} (baseline≈{base:.2%})")

    # Schur over symbols equality
    print(f"\nSchurProbe (first {schur_N} symbols):")
    first, tot, N_eff = schur_probe_count_symbols(seq, schur_N)
    exp_sch, p_eq = schur_expected_from_empirical_counts(counts_over_alphabet_int(seq[:N_eff], M), N_eff)
    tot_tri = (N_eff-1)*N_eff//2
    frac = tot/tot_tri if tot_tri else float('nan')
    σ = math.sqrt(exp_sch*(1-p_eq)) if exp_sch>0 else float('nan')
    z_sch = (tot-exp_sch)/σ if (σ and σ>0) else float('nan')
    if first is not None: print(f"  first violation at index {first}")
    print(f"  triples={tot_tri:,}  count={tot:,}  expected≈{int(exp_sch):,}  frac={frac:.6f}  z={z_sch:+.2f}")

    # MC baseline
    mc_mean=None
    if mc>0:
        mc_mean = mc_random_integers(N, M, mc)
        print(f"\nMonte Carlo baseline (integers, {mc} reps): χ²≈{mc_mean['chi_mean']:.4f}, comp≈{mc_mean['comp_mean']:.4f}")

    # JSON
    if json_path:
        metrics = {
            "mode":"integers","alphabet":M,"N":N,
            "chi_square":chi,
            "runs":{"Z":z_run,"p":p_run},
            "autocorr":[autocorrelation(vals,lag) for lag in range(1,6)],
            "compress_ratio":cr,
            "n_gram":ngram_acc,
            "schur":{"count":tot,"expected":exp_sch,"z":z_sch,"fraction":frac,"N_eff":N_eff},
            "montecarlo":mc_mean,
        }
        with open(json_path,"w",encoding="utf8") as f: json.dump(metrics,f,indent=2)
        print(f"\n[report-json] scritto: {json_path}")

# ---------- CLI ----------
def parse_args():
    ap=argparse.ArgumentParser(description="Analizza sequenze di cifre o interi (bucket) e produce statistiche.")
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--file','-f',help="File di input.")
    g.add_argument('--source','-s',choices=['pi','e'],help="Genera cifre via mpmath (modalità digits).")
    ap.add_argument('--integers', action='store_true', help="Interpreta l'input come interi (bucket-mode).")
    ap.add_argument('--alphabet','-A', type=int, default=None, help="Cardinalità alfabeto (p.es. 256 con k=8). Se assente: max+1 osservato.")
    ap.add_argument('--n', type=int, default=None, help="Limita a N simboli (default: tutti).")
    ap.add_argument('--mc', type=int, default=0, help="Monte Carlo reps (default 0=off).")
    ap.add_argument('--schur-N', type=int, default=5000, help="Dimensione finestra per SchurProbe (default 5000).")
    ap.add_argument('--report-json', help="Scrivi un JSON con tutte le metriche.")
    return ap.parse_args()

def main():
    a = parse_args()
    if a.file:
        if not os.path.exists(a.file):
            sys.exit("File non trovato.")
        if a.integers:
            seq_ints = load_integers_from_file(a.file, a.n)
            analyze_integers_mode(seq_ints, a.alphabet, a.n, a.mc, a.schir_N if hasattr(a,'schir_N') else a.__dict__['schur_N'], a.report_json)
        else:
            seq = load_digits_from_file(a.file, a.n)
            analyze_digits_mode(seq, a.n, a.mc, a.schir_N if hasattr(a,'schir_N') else a.__dict__['schur_N'], a.report_json)
    else:
        # --source → solo digits
        if not MP_AVAIL:
            sys.exit("mpmath richiesto per --source")
        if a.n is None or a.n<=0:
            sys.exit("--source richiede --n (>0)")
        seq = generate_constant_digits(a.source, a.n)
        analyze_digits_mode(seq, a.n, a.mc, a.schir_N if hasattr(a,'schir_N') else a.__dict__['schur_N'], a.report_json)

if __name__=="__main__":
    main()
