"""Pure metric calculation and analysis orchestration."""

from __future__ import annotations

import collections
import math
import statistics
import zlib
from dataclasses import asdict, dataclass
from typing import Literal, Sequence


@dataclass(frozen=True)
class AnalysisConfig:
    """Explicit settings for an analysis run."""

    schur_capacity: int = 5000

    def __post_init__(self) -> None:
        if (
            not isinstance(self.schur_capacity, int)
            or isinstance(self.schur_capacity, bool)
            or self.schur_capacity <= 0
        ):
            raise ValueError("schur_capacity must be a positive integer")


@dataclass(frozen=True)
class RunsResult:
    z_score: float
    p_two_tailed: float


@dataclass(frozen=True)
class GapResult:
    count: int
    mean: float


@dataclass(frozen=True)
class SchurResult:
    """Result of the pair-based modular-additivity diagnostic.

    ``first_matching_relation_index`` is the ``right`` (second-pair) index of
    the first matching relation encountered while iterating pairs by increasing
    ``left`` and then increasing ``right``.  It is ``None`` when no relation
    matches.  It is not an index of a failed relation.
    """

    triples: int
    count: int
    expected: float
    fraction: float
    z_score: float
    first_matching_relation_index: int | None

    @property
    def first_violation_index(self) -> int | None:
        """Deprecated compatibility alias for ``first_matching_relation_index``."""
        return self.first_matching_relation_index


@dataclass(frozen=True, eq=False)
class AnalysisResult:
    """All calculated values needed by the existing human and JSON reports."""

    mode: Literal["digits", "integers"]
    sample_size: int
    alphabet: int
    counts: dict[int, int]
    chi_square: float
    expected_per_bin: float
    zscores: dict[int, float]
    runs: RunsResult
    gaps: dict[int, GapResult]
    autocorr: dict[int, float]
    compress_ratio: float
    ngram_accuracy: dict[int, float]
    schur: SchurResult
    max_observed: int | None = None

    __hash__ = None

    def __eq__(self, other: object) -> bool:
        """Compare results deterministically, treating unavailable (NaN) values as equal."""
        if not isinstance(other, AnalysisResult):
            return NotImplemented
        return _normalise_for_comparison(asdict(self)) == _normalise_for_comparison(asdict(other))


def _normalise_for_comparison(value: object) -> object:
    if isinstance(value, float) and math.isnan(value):
        return "__digit_probe_nan__"
    if isinstance(value, dict):
        return {key: _normalise_for_comparison(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalise_for_comparison(item) for item in value]
    return value


def compress_ratio_bytes(data: bytes) -> float:
    if not data:
        return float("nan")
    return len(zlib.compress(data, level=6)) / float(len(data))


def counts_and_chi_square(seq: Sequence[int], alphabet: int) -> tuple[dict[int, int], float, float]:
    """Return counts per symbol, chi-square, and expected count per bin."""
    counts = {symbol: 0 for symbol in range(alphabet)}
    for symbol in seq:
        if 0 <= symbol < alphabet:
            counts[symbol] += 1
    size = len(seq)
    if alphabet == 0 or size == 0:
        return counts, float("nan"), float("nan")
    expected = size / float(alphabet)
    chi_square = 0.0
    for symbol in range(alphabet):
        deviation = counts[symbol] - expected
        chi_square += (deviation * deviation) / (expected if expected > 0 else 1.0)
    return counts, chi_square, expected


def zscores_per_symbol(counts: dict[int, int], expected: float) -> dict[int, float]:
    """Calculate ``(observed - expected) / sqrt(expected)`` for each symbol."""
    if expected <= 0:
        return {symbol: 0.0 for symbol in counts}
    scale = math.sqrt(expected)
    return {symbol: (count - expected) / scale for symbol, count in counts.items()}


def runs_test_even_odd(seq: Sequence[int]) -> RunsResult:
    """Run the existing parity runs test, returning normal-approximation values."""
    size = len(seq)
    if size < 2:
        return RunsResult(float("nan"), float("nan"))
    classes = [symbol & 1 for symbol in seq]
    even_count = sum(1 for value in classes if value == 0)
    odd_count = size - even_count
    if even_count == 0 or odd_count == 0:
        return RunsResult(float("nan"), float("nan"))

    runs = 1 + sum(1 for index in range(1, size) if classes[index] != classes[index - 1])
    mean = 1 + (2 * even_count * odd_count) / size
    variance = (2 * even_count * odd_count * (2 * even_count * odd_count - size)) / (
        size * size * (size - 1)
    )
    sigma = math.sqrt(variance) if variance > 0 else 0.0
    z_score = (runs - mean) / sigma if sigma > 0 else 0.0
    return RunsResult(z_score, math.erfc(abs(z_score) / math.sqrt(2.0)))


def gaps_summary(seq: Sequence[int], alphabet: int) -> dict[int, GapResult]:
    """Calculate number and mean size of successive gaps for each symbol."""
    last: dict[int, int | None] = {symbol: None for symbol in range(alphabet)}
    gap_counts = {symbol: 0 for symbol in range(alphabet)}
    gap_sums = {symbol: 0 for symbol in range(alphabet)}
    for index, symbol in enumerate(seq):
        if 0 <= symbol < alphabet:
            if last[symbol] is not None:
                gap_counts[symbol] += 1
                gap_sums[symbol] += index - last[symbol]
            last[symbol] = index
    return {
        symbol: GapResult(
            count=gap_counts[symbol],
            mean=gap_sums[symbol] / gap_counts[symbol] if gap_counts[symbol] else float("inf"),
        )
        for symbol in range(alphabet)
    }


def autocorr_lags(seq: Sequence[int], lags: Sequence[int]) -> dict[int, float]:
    """Calculate Pearson-style autocorrelation for each requested lag."""
    size = len(seq)
    if size < 2:
        return {lag: float("nan") for lag in lags}
    mean = statistics.mean(seq)
    denominator = sum((symbol - mean) ** 2 for symbol in seq)
    if denominator == 0:
        return {lag: 0.0 for lag in lags}
    correlations: dict[int, float] = {}
    for lag in lags:
        if lag <= 0 or lag >= size:
            correlations[lag] = float("nan")
            continue
        numerator = 0.0
        for index in range(size - lag):
            numerator += (seq[index] - mean) * (seq[index + lag] - mean)
        correlations[lag] = numerator / denominator
    return correlations


def ngram_predictor_accuracy(
    seq: Sequence[int], alphabet: int, n: int, train_frac: float = 0.8
) -> float:
    """Calculate the existing n-gram predictor accuracy with its 80/20 split."""
    del alphabet  # The historical predictor accepts this argument but does not use it.
    size = len(seq)
    if size < 4:
        return float("nan")
    train_size = int(size * train_frac)
    if train_size < n + 1:
        train_size = min(size - 1, max(n + 1, int(size * 0.7)))
    train = seq[:train_size]
    test = seq[train_size:]

    if n == 1:
        counts = collections.Counter(train)
        if not counts:
            return float("nan")
        top = counts.most_common(1)[0][0]
        return sum(1 for symbol in test if symbol == top) / len(test) if test else float("nan")

    transitions: dict[tuple[int, ...], collections.Counter[int]] = {}
    for index in range(n, len(train)):
        context = tuple(train[index - n : index])
        transitions.setdefault(context, collections.Counter())[train[index]] += 1

    fallback = collections.Counter(train).most_common(1)[0][0]
    correct = 0
    total = 0
    for index in range(n, len(test)):
        context = tuple(test[index - n : index])
        prediction = transitions.get(context, collections.Counter()).most_common(1)
        top = prediction[0][0] if prediction else fallback
        correct += top == test[index]
        total += 1
    return correct / total if total else float("nan")


def schur_probe(seq: Sequence[int], alphabet: int, capacity: int) -> SchurResult:
    """Run the pair-based modular-additivity diagnostic.

    The reported first-match index is the second-pair (``right``) index of the
    first matching relation in increasing ``left``, then ``right`` order.
    """
    size = min(len(seq), capacity)
    if size < 3 or alphabet <= 0:
        return SchurResult(0, 0, 0.0, 0.0, float("nan"), None)

    triples = size * (size - 1) // 2
    probability = 1.0 / float(alphabet)
    expected = triples * probability
    sigma = math.sqrt(expected * (1.0 - probability))
    count = 0
    first_index: int | None = None
    for left in range(size - 1):
        left_symbol = seq[left]
        for right in range(left + 1, size):
            target = (left + right) % size
            if (left_symbol + seq[right]) % alphabet == seq[target] % alphabet:
                count += 1
                if first_index is None:
                    first_index = right
    z_score = (count - expected) / sigma if sigma > 0 else 0.0
    return SchurResult(triples, count, expected, count / float(triples), z_score, first_index)


def _analyze(
    seq: Sequence[int],
    mode: Literal["digits", "integers"],
    alphabet: int,
    config: AnalysisConfig,
    max_observed: int | None = None,
) -> AnalysisResult:
    counts, chi_square, expected = counts_and_chi_square(seq, alphabet)
    zscores = zscores_per_symbol(counts, expected if expected == expected else 0.0)
    gaps = gaps_summary(seq, alphabet)
    if mode == "digits":
        compressed = "".join(chr(48 + symbol) for symbol in seq).encode("ascii", errors="ignore")
    else:
        compressed = ("\n".join(str(symbol) for symbol in seq) + "\n").encode(
            "utf8", errors="ignore"
        )
    return AnalysisResult(
        mode=mode,
        sample_size=len(seq),
        alphabet=alphabet,
        counts=counts,
        chi_square=chi_square,
        expected_per_bin=expected,
        zscores=zscores,
        runs=runs_test_even_odd(seq),
        gaps=gaps,
        autocorr=autocorr_lags(seq, [1, 2, 3, 4, 5]),
        compress_ratio=compress_ratio_bytes(compressed),
        ngram_accuracy={n: ngram_predictor_accuracy(seq, alphabet, n) for n in (1, 2, 3)},
        schur=schur_probe(seq, alphabet, config.schur_capacity),
        max_observed=max_observed if mode == "integers" else None,
    )


def _validated_config(config: AnalysisConfig | None) -> AnalysisConfig:
    if config is None:
        return AnalysisConfig()
    if not isinstance(config, AnalysisConfig):
        raise TypeError("config must be an AnalysisConfig or None")
    return config


def analyze_digits(digits: Sequence[int], config: AnalysisConfig | None = None) -> AnalysisResult:
    """Analyze an in-memory sequence of decimal digits without performing I/O."""
    seq = list(digits)
    if any(
        not isinstance(digit, int) or isinstance(digit, bool) or not 0 <= digit <= 9
        for digit in seq
    ):
        raise ValueError("digits must contain integers from 0 through 9")
    return _analyze(seq, "digits", 10, _validated_config(config))


def analyze_integer_symbols(
    symbols: Sequence[int], alphabet: int, config: AnalysisConfig | None = None
) -> AnalysisResult:
    """Analyze integer symbols modulo an explicit positive alphabet without I/O."""
    if not isinstance(alphabet, int) or isinstance(alphabet, bool) or alphabet <= 0:
        raise ValueError("alphabet must be a positive integer")
    seq = list(symbols)
    if any(not isinstance(symbol, int) or isinstance(symbol, bool) for symbol in seq):
        raise ValueError("symbols must contain integers")
    return _analyze(
        [symbol % alphabet for symbol in seq],
        "integers",
        alphabet,
        _validated_config(config),
        max(seq) if seq else -1,
    )
