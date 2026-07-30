"""Public API for deterministic, in-memory numeric sequence analysis.

The functions exported here perform no input/output.  Use :mod:`digit_probe.cli`
for the command-line interface and :mod:`digit_probe.reporting` for reports.
"""

from .core import AnalysisConfig, AnalysisResult, analyze_digits, analyze_integer_symbols

__all__ = [
    "AnalysisConfig",
    "AnalysisResult",
    "analyze_digits",
    "analyze_integer_symbols",
]
