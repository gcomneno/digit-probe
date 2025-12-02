#!/usr/bin/env python3

import json
import math
import sys

from pathlib import Path

def fmt_runs(r: dict) -> str:
    """Format runs test as 'Z=.., p=..' handling None/NaN safely."""
    if not isinstance(r, dict) or not r:
        return "-"
    z = r.get("Z")
    p = r.get("p_two_tailed")

    # Se Z manca o è NaN → niente da mostrare
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "-"

    # p può essere None / NaN / non numerico
    if p is None:
        return f"Z={z:.2f}, p=None"
    if isinstance(p, float) and math.isnan(p):
        return f"Z={z:.2f}, p=nan"
    try:
        return f"Z={z:.2f}, p={float(p):.4f}"
    except Exception:
        # fallback se p è stringa o altro tipo strano
        return f"Z={z:.2f}, p={p}"

def fmt_schur(s: dict) -> str:
    """Format SchurProbe as 'z=.., frac=..' gestendo None/NaN."""
    if not isinstance(s, dict) or not s:
        return "-"
    z = s.get("z")
    frac = s.get("fraction")

    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "-"
    if frac is None or (isinstance(frac, float) and math.isnan(frac)):
        return f"z={z:.2f}, frac=?"
    try:
        return f"z={z:.2f}, frac={float(frac):.6f}"
    except Exception:
        return f"z={z:.2f}, frac={frac}"

def fmt_num(x, nd: int = 4) -> str:
    """Format numero o restituisci stringa grezza."""
    if isinstance(x, (int, float)):
        if isinstance(x, float) and math.isnan(x):
            return "nan"
        return f"{x:.{nd}f}"
    return str(x)

def get_out_dir_from_argv() -> Path:
    """
    Interpreta gli argomenti in modo tollerante:

      - nessun argomento  -> 'out'
      - 'DIR'             -> usa DIR
      - '--in DIR'        -> usa DIR
      - '-i DIR'          -> usa DIR

    Ignora qualsiasi altra fantasia del Makefile.
    """
    args = sys.argv[1:]
    if not args:
        return Path("out")

    # Forma: --in DIR o -i DIR
    if args[0] in ("--in", "-i"):
        if len(args) >= 2:
            return Path(args[1])
        # se manca la dir dopo --in, ricadi su default
        return Path("out")

    # Forma semplice: primo argomento = directory
    return Path(args[0])

def main() -> None:
    out_dir = get_out_dir_from_argv()

    if not out_dir.exists():
        print(f"[err] directory non trovata: {out_dir}", file=sys.stderr)
        sys.exit(1)

    json_files = sorted(p for p in out_dir.glob("*.json"))
    if not json_files:
        print(f"[warn] nessun JSON trovato in {out_dir}", file=sys.stderr)
        sys.exit(0)

    print("file | N | chi² | comp | runs(Z,p) | Schur(z, frac)")
    print("---- | --:| ---:| ---:| ---------- | --------------")

    for path in json_files:
        try:
            with open(path, "r", encoding="utf8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[warn] skip {path.name}: {e}", file=sys.stderr)
            continue

        N = data.get("N") or data.get("n") or "?"
        chi2 = data.get("chi_square", "?")
        comp = data.get("compress_ratio", "?")
        runs_str = fmt_runs(data.get("runs", {}))
        schur_str = fmt_schur(data.get("schur", {}))

        print(
            f"{path.name} | {N} | {fmt_num(chi2,4)} | {fmt_num(comp,4)} | "
            f"{runs_str} | {schur_str}"
        )

if __name__ == "__main__":
    main()
