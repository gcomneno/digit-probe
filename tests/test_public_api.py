"""Boundary and compatibility tests for the importable digit-probe package."""

from __future__ import annotations

import argparse
import builtins
import json
import math
import random
import subprocess
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, fields
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from digit_probe import (  # noqa: E402
    AnalysisConfig,
    AnalysisResult,
    analyze_digits,
    analyze_integer_symbols,
)
from digit_probe.cli import parse_args  # noqa: E402
from digit_probe.reporting import render_human_report, report_mapping  # noqa: E402


def json_round_trip(mapping: dict[str, object]) -> dict[str, object]:
    """Mirror JSON's conversion of integer object keys into strings."""
    return json.loads(json.dumps(mapping))


def test_public_api_analyzes_decimal_digits() -> None:
    result = analyze_digits([0, 1, 2, 3], AnalysisConfig(schur_capacity=3))

    assert result.mode == "digits"
    assert result.sample_size == 4
    assert result.alphabet == 10
    assert result.counts[0] == 1
    assert result.counts[9] == 0
    assert result.schur.triples == 3


def test_public_api_analyzes_integer_symbols_modulo_alphabet() -> None:
    result = analyze_integer_symbols(
        [-1, 0, 5], alphabet=5, config=AnalysisConfig(schur_capacity=3)
    )

    assert result.mode == "integers"
    assert result.counts == {0: 2, 1: 0, 2: 0, 3: 0, 4: 1}
    assert result.max_observed == 5


def test_schur_first_match_is_the_second_index_and_uses_matching_terminology() -> None:
    result = analyze_digits([0, 0, 0], AnalysisConfig(schur_capacity=3))

    assert result.schur.count == result.schur.triples == 3
    assert result.schur.fraction == 1.0
    assert result.schur.first_matching_relation_index == 1
    assert result.schur.first_violation_index == 1  # Deprecated API alias.

    report = report_mapping(result)["schur"]
    assert report["first_violation_index"] == 1
    assert "first_matching_relation_index" not in report

    human_report = render_human_report(result)
    assert "first matching relation at index 1 (second pair index)" in human_report
    assert "first violation" not in human_report


def test_schur_reports_no_first_match_when_no_relations_match() -> None:
    result = analyze_digits([1, 1, 1], AnalysisConfig(schur_capacity=3))

    assert result.schur.count == 0
    assert result.schur.first_matching_relation_index is None
    assert result.schur.first_violation_index is None  # Deprecated API alias.
    report = report_mapping(result)["schur"]
    assert report["first_violation_index"] is None
    assert "first_matching_relation_index" not in report
    assert "first matching relation at index" not in render_human_report(result)


@pytest.mark.parametrize(
    "analyze",
    [
        lambda: analyze_digits([0, 1, 2, 3], AnalysisConfig(schur_capacity=3)),
        lambda: analyze_integer_symbols(
            [0, 1, 2, 3], alphabet=5, config=AnalysisConfig(schur_capacity=3)
        ),
    ],
)
def test_core_analysis_is_pure(
    analyze: Callable[[], AnalysisResult],
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_open(*args: object, **kwargs: object) -> object:
        raise AssertionError("core analysis must not open files")

    def fail_parse_args(*args: object, **kwargs: object) -> object:
        raise AssertionError("core analysis must not parse arguments")

    def fail_exit(*args: object, **kwargs: object) -> object:
        raise AssertionError("core analysis must not exit")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr(Path, "open", fail_open)
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", fail_parse_args)
    monkeypatch.setattr(sys, "exit", fail_exit)
    analyze()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_identical_analysis_inputs_are_structurally_equal() -> None:
    config = AnalysisConfig(schur_capacity=4)
    assert analyze_digits([0, 1, 2, 3, 4], config) == analyze_digits([0, 1, 2, 3, 4], config)


def test_analysis_result_equality_treats_nan_as_unavailable() -> None:
    left = analyze_digits([], AnalysisConfig(schur_capacity=3))
    right = analyze_digits([], AnalysisConfig(schur_capacity=3))

    assert math.isnan(left.chi_square)
    assert left == right
    assert isinstance(left, AnalysisResult)


def test_analysis_result_public_structure_matches_origin_main() -> None:
    """Keep the stable dataclass fields, ``asdict()``, repr, and equality contract."""
    expected_fields = (
        "mode",
        "sample_size",
        "alphabet",
        "counts",
        "chi_square",
        "expected_per_bin",
        "zscores",
        "runs",
        "gaps",
        "autocorr",
        "compress_ratio",
        "ngram_accuracy",
        "schur",
        "max_observed",
    )
    result = analyze_digits([0, 1, 2, 3], AnalysisConfig(schur_capacity=3))

    assert tuple(field.name for field in fields(AnalysisResult)) == expected_fields
    assert tuple(asdict(result)) == expected_fields
    assert repr(result).startswith("AnalysisResult(mode=")
    assert not hasattr(result, "ngram_majority_accuracy")


@pytest.mark.parametrize(
    ("result", "fixture"),
    [
        (
            analyze_digits([0, 1, 2, 3], AnalysisConfig(schur_capacity=3)),
            "legacy_digits_report.json",
        ),
        (
            analyze_integer_symbols(
                [-1, 0, 5], alphabet=5, config=AnalysisConfig(schur_capacity=3)
            ),
            "legacy_integers_report.json",
        ),
    ],
)
def test_json_reports_match_captured_legacy_reports(result: object, fixture: str) -> None:
    legacy = json.loads((ROOT / "tests" / "fixtures" / fixture).read_text(encoding="utf8"))
    assert json_round_trip(report_mapping(result)) == legacy  # type: ignore[arg-type]


def test_legacy_fixture_explicitly_preserves_json_nan_values() -> None:
    raw_fixture = (ROOT / "tests" / "fixtures" / "legacy_digits_report.json").read_text(
        encoding="utf8"
    )
    parsed_fixture = json.loads(raw_fixture)

    assert "NaN" in raw_fixture
    assert math.isnan(parsed_fixture["autocorr"]["4"])
    assert parsed_fixture["runs"]["p_two_tailed"] is not None


def test_ngram_one_keeps_the_historical_training_majority_semantics() -> None:
    rng = random.Random(20260730)
    digits = rng.choices(range(10), weights=[1, 1, 1, 1, 1, 1, 1, 6, 1, 1], k=10_000)
    result = analyze_digits(digits, AnalysisConfig(schur_capacity=3))

    train_size = int(len(digits) * 0.8)
    train = digits[:train_size]
    test = digits[train_size:]
    training_majority = Counter(train).most_common(1)[0][0]
    expected = sum(symbol == training_majority for symbol in test) / len(test)

    assert result.ngram_accuracy[1] == expected
    assert set(report_mapping(result)["ngram"]) == {1, 2, 3}
    report = render_human_report(result)
    assert "Valutazione N-gram e baseline (split 80/20)" in report
    assert "probabilità uniforme (1/alfabeto): 10.0000%" in report
    assert (
        'ngram["1"] — majority baseline empirica storica '
        "(maggioranza nel training, valutata sull'intero holdout): "
        f"{expected * 100:.4f}%" in report
    )
    assert "  n=1:" not in report
    assert report.count('ngram["1"]') == 1
    for n in (2, 3):
        assert f"n={n} (valutato su holdout[{n}:]):" in report
    assert "Δ=" not in report
    assert (
        "Il confronto con la majority baseline è interpretativo: solo un miglioramento "
        "sostanziale e stabile può suggerire informazione nel contesto." in report
    )


def test_ngram_human_report_for_uniform_biased_and_periodic_sequences() -> None:
    uniform_rng = random.Random(20260730)
    uniform = [uniform_rng.randrange(10) for _ in range(10_000)]
    biased_rng = random.Random(20260731)
    biased = biased_rng.choices(range(10), weights=[1, 1, 1, 1, 1, 1, 1, 6, 1, 1], k=10_000)
    periodic = list(range(10)) * 1000

    config = AnalysisConfig(schur_capacity=3)
    uniform_result = analyze_digits(uniform, config)
    biased_result = analyze_digits(biased, config)
    periodic_result = analyze_digits(periodic, config)
    uniform_report = render_human_report(uniform_result)
    biased_report = render_human_report(biased_result)
    periodic_report = render_human_report(periodic_result)

    assert all(math.isfinite(uniform_result.ngram_accuracy[n]) for n in (1, 2, 3))
    assert "probabilità uniforme (1/alfabeto): 10.0000%" in uniform_report
    assert 'ngram["1"] — majority baseline empirica storica' in uniform_report
    assert biased_result.ngram_accuracy[1] > 0.3
    assert 'ngram["1"] — majority baseline empirica storica' in biased_report
    assert periodic_result.ngram_accuracy[1] == 0.1
    assert periodic_result.ngram_accuracy[2] == periodic_result.ngram_accuracy[3] == 1.0
    for n in (2, 3):
        assert f"n={n} (valutato su holdout[{n}:]): 100.0000%" in periodic_report


def test_ngram_human_report_preserves_short_split_unavailable_values() -> None:
    result = analyze_digits([0, 1, 2, 3], AnalysisConfig(schur_capacity=3))
    report = render_human_report(result)

    assert result.ngram_accuracy[1] == 0.0
    assert math.isnan(result.ngram_accuracy[2]) and math.isnan(result.ngram_accuracy[3])
    assert 'ngram["1"] — majority baseline empirica storica' in report
    assert "n=2 (valutato su holdout[2:]): n/a" in report
    assert "n=3 (valutato su holdout[3:]): n/a" in report


@pytest.mark.parametrize(
    ("digits", "expected_size"),
    [([], 0), ([7], 1), ([0, 0, 0, 0], 4)],
)
def test_digits_edge_cases_keep_existing_semantics(digits: list[int], expected_size: int) -> None:
    result = analyze_digits(digits)
    assert result.sample_size == expected_size
    assert sum(result.counts.values()) == expected_size


def test_integer_edge_cases_keep_existing_semantics() -> None:
    result = analyze_integer_symbols([], alphabet=3)
    assert result.sample_size == 0
    assert result.max_observed == -1
    with pytest.raises(ValueError, match="positive integer"):
        analyze_integer_symbols([1], alphabet=0)


@pytest.mark.parametrize("capacity", [True, 0, -1, 1.5, "3"])
def test_analysis_config_rejects_invalid_schur_capacity(capacity: object) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        AnalysisConfig(schur_capacity=capacity)  # type: ignore[arg-type]


@pytest.mark.parametrize("digits", [[True], [1.0], [-1], [10], ["1"]])
def test_digits_reject_invalid_values_and_types(digits: list[object]) -> None:
    with pytest.raises(ValueError, match="integers from 0 through 9"):
        analyze_digits(digits)  # type: ignore[arg-type]


@pytest.mark.parametrize("symbols", [[True], [1.0], ["1"]])
def test_integer_symbols_reject_invalid_types(symbols: list[object]) -> None:
    with pytest.raises(ValueError, match="symbols must contain integers"):
        analyze_integer_symbols(symbols, alphabet=3)  # type: ignore[arg-type]


@pytest.mark.parametrize("alphabet", [True, 0, -1, 1.5, "3"])
def test_integer_alphabet_rejects_invalid_values_and_types(alphabet: object) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        analyze_integer_symbols([1], alphabet=alphabet)  # type: ignore[arg-type]


def test_analysis_rejects_non_config_objects() -> None:
    with pytest.raises(TypeError, match="AnalysisConfig or None"):
        analyze_digits([0], config=False)  # type: ignore[arg-type]


def test_cli_argument_defaults_and_integer_validation() -> None:
    args = parse_args(["--file", "input.txt"])
    assert args.n is None
    assert args.integers is False
    assert args.alphabet is None
    assert args.mc is None
    assert args.schur_N == 5000


@pytest.mark.parametrize("schur_capacity", [0, -1])
def test_cli_preserves_legacy_nonpositive_schur_capacity(
    schur_capacity: int, tmp_path: Path
) -> None:
    input_path = tmp_path / "digits.txt"
    input_path.write_text("0123", encoding="utf8")

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "src" / "digit_probe.py"),
            "--file",
            str(input_path),
            "--schur-N",
            str(schur_capacity),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "triples=0  count=0  expected≈0" in completed.stdout


def test_cli_output_is_accepted_by_compare_reports(tmp_path: Path) -> None:
    input_path = tmp_path / "digits.txt"
    report_path = tmp_path / "report.json"
    markdown_path = tmp_path / "comparison.md"
    input_path.write_text("01230123", encoding="utf8")

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "src" / "digit_probe.py"),
            "--file",
            str(input_path),
            "--schur-N",
            "4",
            "--report-json",
            str(report_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "src" / "compare_reports.py"),
            str(report_path),
            str(report_path),
            "--baseline",
            str(report_path),
            "--md",
            str(markdown_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert markdown_path.exists()
