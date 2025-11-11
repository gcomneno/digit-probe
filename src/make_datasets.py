#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_datasets.py (mirrors + offline fallback)
Scarica e prepara dataset di cifre per π ed e.
Se tutti i mirror falliscono, tenta il fallback offline via mpmath (se installato).

Esempi:
  python3 make_datasets.py --n 100000
  python3 make_datasets.py --n 250000 --only pi --outdir data
  python3 make_datasets.py --only e
  python3 make_datasets.py --offline --only pi   # genera localmente con mpmath
"""

import argparse
import os
import re
import sys
import time
import urllib.request
import urllib.error

# --- MIRRORS ---
PI_SOURCES = [
    # mirror UMN
    "https://www.geom.umn.edu/~huberty/math5337/groupe/digits.html",
    # mirror molto usato (file testuale diretto con 1M cifre)
    "https://www.angio.net/pi/digits/pi1000000.txt",
    # pagina con molte cifre (HTML, ma estraiamo solo i digit)
    "https://www.piday.org/million/",
]

E_SOURCES = [
    # APOD NASA
    "https://apod.nasa.gov/htmltest/gifcity/e.2mil",
    # OEIS: A001113 (contiene righe testuali, ma estraiamo solo le cifre)
    "https://oeis.org/A001113/b001113.txt",
]

DEFAULT_TARGETS = {"pi": "pi_100k.txt", "e": "e_100k.txt"}

USER_AGENT = "Mozilla/5.0 (compatible; digit-probe/1.1; +local)"
TIMEOUT = 30
RETRIES = 3
SLEEP_BETWEEN = 2.0  # seconds

try:
    import mpmath as mp
    MP_AVAIL = True
except Exception:
    MP_AVAIL = False


def http_get(url: str) -> str:
    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_err = e
            print(f"[warn] Tentativo {attempt}/{RETRIES} fallito su {url}: {e}", file=sys.stderr)
            if attempt < RETRIES:
                time.sleep(SLEEP_BETWEEN)
    raise RuntimeError(f"Download fallito definitivamente: {url} ({last_err})")


def extract_digits(raw_html_or_text: str) -> str:
    return "".join(re.findall(r"\d", raw_html_or_text))


def trim_leading_integer(digits: str, constant_name: str, keep_integer: bool) -> str:
    if keep_integer or not digits:
        return digits
    if constant_name == "pi" and digits[0] == "3":
        return digits[1:]
    if constant_name == "e" and digits[0] == "2":
        return digits[1:]
    return digits


def write_file(path: str, digits: str):
    with open(path, "w", encoding="utf8") as f:
        f.write(digits)


def sha256_hex(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("ascii", errors="ignore")).hexdigest()


def fallback_offline(constant_name: str, n: int) -> str:
    if not MP_AVAIL:
        raise RuntimeError("Fallback offline richiesto ma mpmath non è installato (pip install mpmath).")
    mp.mp.dps = max(50, n + 10)
    if constant_name == "pi":
        s = mp.nstr(mp.pi, n + 2)  # es: "3.1415..."
    elif constant_name == "e":
        s = mp.nstr(mp.e, n + 2)
    else:
        raise ValueError("Costante sconosciuta: " + constant_name)
    return extract_digits(s)


def make_one(constant_name: str, sources: list[str], n: int, out_path: str, keep_integer: bool, offline: bool):
    print(f"\n[{constant_name}] Target: {out_path} ({n} cifre)")
    data_digits = None

    if not offline:
        # prova tutti i mirror
        for url in sources:
            print(f"[{constant_name}] Scaricamento da {url} ...")
            try:
                raw = http_get(url)
                all_digits = extract_digits(raw)
                if not all_digits:
                    print(f"[warn] Nessuna cifra estratta da {url}", file=sys.stderr)
                    continue
                cleaned = trim_leading_integer(all_digits, constant_name, keep_integer)
                if len(cleaned) < n:
                    print(f"[warn] {constant_name}: trovate {len(cleaned)} cifre utili (<{n}), continuo con altro mirror.", file=sys.stderr)
                    continue
                data_digits = cleaned[:n]
                break
            except Exception as e:
                print(f"[warn] Mirror fallito: {e}", file=sys.stderr)

    if data_digits is None:
        print(f"[info] Uso fallback offline (mpmath) per {constant_name} ...")
        all_digits = fallback_offline(constant_name, n)
        cleaned = trim_leading_integer(all_digits, constant_name, keep_integer)
        if len(cleaned) < n:
            raise RuntimeError(f"{constant_name}: fallback offline ha prodotto solo {len(cleaned)} cifre utili.")
        data_digits = cleaned[:n]

    write_file(out_path, data_digits)
    print(f"[{constant_name}] Scritto {out_path} ({len(data_digits)} cifre).")
    print(f"[{constant_name}] SHA256: {sha256_hex(data_digits)}")


def parse_args():
    ap = argparse.ArgumentParser(description="Scarica e prepara dataset di cifre per π ed e (con mirrors e fallback offline).")
    ap.add_argument("--n", type=int, default=100_000, help="Numero di cifre (default 100000).")
    ap.add_argument("--outdir", default=".", help="Directory di output (default .)")
    ap.add_argument("--only", choices=["pi", "e", "both"], default="both", help="Quale costante produrre (default both).")
    ap.add_argument("--keep-integer", action="store_true", help="Mantieni la cifra intera iniziale (es. '3' per π, '2' per e).")
    ap.add_argument("--offline", action="store_true", help="Forza generazione offline con mpmath (non scarica).")
    return ap.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    targets = {
        "pi": os.path.join(args.outdir, DEFAULT_TARGETS["pi"] if args.n == 100_000 else f"pi_{args.n}.txt"),
        "e":  os.path.join(args.outdir, DEFAULT_TARGETS["e"]  if args.n == 100_000 else f"e_{args.n}.txt"),
    }

    todo = []
    if args.only in ("pi", "both"):
        todo.append(("pi", PI_SOURCES, targets["pi"]))
    if args.only in ("e", "both"):
        todo.append(("e", E_SOURCES, targets["e"]))

    for name, sources, outp in todo:
        make_one(
            constant_name=name,
            sources=sources,
            n=args.n,
            out_path=outp,
            keep_integer=args.keep_integer,
            offline=args.offline,
        )

    print("\nFatto. Esempi di esecuzione con digit_probe:")
    for name, _, outp in todo:
        print(f"  python3 digit_probe.py --file {outp}")


if __name__ == "__main__":
    # import re moved up for digit extraction
    main()
