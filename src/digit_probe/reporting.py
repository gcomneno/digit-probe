"""Conversion and human-readable rendering of analysis results."""

from __future__ import annotations

import math
from typing import Any

from .core import AnalysisResult


def report_mapping(result: AnalysisResult) -> dict[str, Any]:
    """Convert a result to the established JSON-compatible report mapping."""
    schur = {
        "triples": int(result.schur.triples),
        "count": int(result.schur.count),
        "expected": float(result.schur.expected),
        "fraction": float(result.schur.fraction),
        "z": float(result.schur.z_score),
        "first_violation_index": result.schur.first_violation_index,
    }
    report: dict[str, Any] = {
        "mode": result.mode,
        "N": result.sample_size,
        "alphabet": result.alphabet,
        "chi_square": result.chi_square,
        "expected_per_bin": result.expected_per_bin,
        "counts": result.counts,
    }
    if result.mode == "digits":
        report["zscores"] = {int(symbol): float(value) for symbol, value in result.zscores.items()}
    report.update(
        {
            "runs": {
                "Z": float(result.runs.z_score),
                "p_two_tailed": (
                    float(result.runs.p_two_tailed)
                    if result.runs.p_two_tailed == result.runs.p_two_tailed
                    else None
                ),
            },
        }
    )
    if result.mode == "digits":
        report["gaps"] = {
            int(symbol): {
                "count": int(gap.count),
                "mean": float(gap.mean) if math.isfinite(gap.mean) else None,
            }
            for symbol, gap in result.gaps.items()
        }
    else:
        top5 = sorted(result.counts.items(), key=lambda item: (-item[1], item[0]))[:5]
        report["gaps_top5"] = {
            int(symbol): {
                "count": int(result.gaps[symbol].count),
                "mean": float(result.gaps[symbol].mean)
                if math.isfinite(result.gaps[symbol].mean)
                else None,
            }
            for symbol, _ in top5
        }
    report.update(
        {
            "autocorr": {int(lag): float(value) for lag, value in result.autocorr.items()},
            "compress_ratio": result.compress_ratio,
            "ngram": {int(n): float(value) for n, value in result.ngram_accuracy.items()},
            "schur": schur,
        }
    )
    return report


def _signed(value: float, precision: int) -> str:
    return f"{'+' if value >= 0 else ''}{value:.{precision}f}"


def render_human_report(result: AnalysisResult) -> str:
    """Render the established ordinary console report without printing it."""
    lines: list[str] = []
    if result.mode == "digits":
        lines.append(f"MODE: digits  |  TOTAL DIGITS: {result.sample_size}")
        for digit in range(result.alphabet):
            lines.append(f"  {digit}: {result.counts.get(digit, 0)}")
        lines.extend(
            [
                f"\nChi-square (10 bins): {result.chi_square:.4f} (expected per bin={result.expected_per_bin:.2f})\n",
                "Z-scores per digit:",
            ]
        )
        lines.extend(
            f"  {digit}: {_signed(result.zscores[digit], 3)}" for digit in range(result.alphabet)
        )
        lines.append("")
        lines.append(
            f"Runs test (even/odd): Z={result.runs.z_score:.3f}, p={result.runs.p_two_tailed:.3f}\n"
        )
        lines.append("Gaps summary (count, mean gap):")
        for digit in range(result.alphabet):
            gap = result.gaps[digit]
            mean = f"{gap.mean:.2f}" if math.isfinite(gap.mean) else "inf"
            lines.append(f"  {digit}: {gap.count} gaps, mean {mean}")
        lines.append("")
    else:
        lines.append(
            f"MODE: integers  |  N={result.sample_size}  alphabet M={result.alphabet}  "
            f"(max_observed={result.max_observed})\n"
        )
        lines.append(
            f"Chi-square (M={result.alphabet} bins): {result.chi_square:.4f} "
            f"(expected per bin={result.expected_per_bin:.2f})\n"
        )
        lines.append(
            f"Runs test (even/odd values): Z={result.runs.z_score:.3f}, "
            f"p={result.runs.p_two_tailed:.3f}\n"
        )
        lines.append("Gaps summary (top-5 symbols by freq):")
        for symbol, _ in sorted(result.counts.items(), key=lambda item: (-item[1], item[0]))[:5]:
            gap = result.gaps[symbol]
            mean = f"{gap.mean:.2f}" if math.isfinite(gap.mean) else "inf"
            lines.append(f"  {symbol}: {gap.count} gaps, mean {mean}")
        lines.append("")

    lines.append("Autocorrelation (lags 1..5):")
    for lag in [1, 2, 3, 4, 5]:
        lines.append(f"  lag {lag}: {_signed(result.autocorr[lag], 4)}")
    lines.append("")
    if result.mode == "digits":
        lines.append(f"Compression ratio (zlib over text): {result.compress_ratio:.4f}")
        if result.compress_ratio <= 0.44:
            lines.append(
                "  --> sotto ~0.44; può indicare ripetizioni o testo breve "
                "(limite teorico ~0.415 per alfabeto 10)."
            )
        else:
            lines.append("  --> compatibile con sequenze random-like su alfabeto 10.")
        lines.append("")
        lines.append("N-gram predictor (80/20 split):")
        baseline = f"{100.0 / result.alphabet:.0f}"
    else:
        lines.append(f"Compression ratio (zlib over 'ints text'): {result.compress_ratio:.4f}\n")
        lines.append("N-gram predictor (80/20 split) over integer symbols:")
        baseline = f"{100.0 / result.alphabet:.2f}"
    for n in (1, 2, 3):
        lines.append(f"  n={n}: {result.ngram_accuracy[n] * 100:.4f}% (baseline≈{baseline}%)")
    lines.append("")
    lines.append("SchurProbe (first 5000 symbols):")
    if result.schur.first_violation_index is not None:
        lines.append(f"  first violation at index {result.schur.first_violation_index}")
    if result.mode == "digits":
        lines.append(
            f"  triples={result.schur.triples:,}  count={result.schur.count}  "
            f"expected≈{result.schur.expected:.0f}"
        )
        lines.append(f"  fraction={result.schur.fraction:.8f}  z={result.schur.z_score:+.2f}\n")
    else:
        lines.append(
            f"  triples={result.schur.triples:,}  count={result.schur.count}  "
            f"expected≈{result.schur.expected:.0f}  frac={result.schur.fraction:.6f}  "
            f"z={result.schur.z_score:+.2f}\n"
        )
    return "\n".join(lines) + "\n"
