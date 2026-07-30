"""Command-line input/output boundary for digit-probe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .core import AnalysisConfig, analyze_digits, analyze_integer_symbols
from .reporting import render_human_report, report_mapping


def read_digits_file(path: str, n: int | None = None) -> list[int]:
    data = Path(path).read_text(encoding="utf8", errors="ignore")
    digits = [ord(character) - 48 for character in data if "0" <= character <= "9"]
    return digits[:n] if n is not None else digits


def read_integers_file(path: str, n: int | None = None) -> list[int]:
    values: list[int] = []
    with Path(path).open("r", encoding="utf8", errors="ignore") as input_file:
        for line in input_file:
            line = line.strip()
            if not line:
                continue
            try:
                value = int(line)
            except Exception:
                continue
            values.append(value)
            if n is not None and len(values) >= n:
                break
    return values


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="digit-probe: analisi di sequenze di cifre/interi")
    parser.add_argument(
        "--file", required=True, help="Input file: digits (senza spazi) o integers (uno per riga)"
    )
    parser.add_argument("--n", type=int, default=None, help="Limita la lunghezza analizzata")
    parser.add_argument(
        "--integers", action="store_true", help="Abilita modalità interi (uno per riga)."
    )
    parser.add_argument(
        "--alphabet",
        type=int,
        default=None,
        help="Alfabeto per modalità integers (obbligatorio se --integers).",
    )
    parser.add_argument(
        "--report-json",
        type=str,
        default=None,
        help="Scrive un report JSON compatibile con compare_reports.py",
    )
    parser.add_argument(
        "--mc",
        type=int,
        default=None,
        help="(opzionale) Monte Carlo reps baseline (non obbligatorio)",
    )
    parser.add_argument(
        "--schur-N",
        dest="schur_N",
        type=int,
        default=5000,
        help="R massimo per SchurProbe (default: 5000)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Run the installed command, including its established exit behavior."""
    args = parse_args(argv)
    # Legacy CLI accepted non-positive --schur-N values; all produce the
    # historical empty Schur result.  Keep that behavior at the CLI boundary
    # while the public AnalysisConfig correctly rejects invalid capacities.
    config = AnalysisConfig(schur_capacity=max(args.schur_N, 1))
    if args.integers:
        if args.alphabet is None or args.alphabet <= 0:
            raise SystemExit("[err] in modalità --integers devi fornire --alphabet > 0")
        result = analyze_integer_symbols(
            read_integers_file(args.file, args.n),
            args.alphabet,
            config,
        )
    else:
        result = analyze_digits(read_digits_file(args.file, args.n), config)
    print(render_human_report(result), end="")
    if args.report_json:
        with Path(args.report_json).open("w", encoding="utf8") as output_file:
            json.dump(report_mapping(result), output_file, ensure_ascii=False, indent=2)
        print(f"[report-json] scritto: {args.report_json}")
