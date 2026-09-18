# Digit Probe

Digit Probe is a **research-oriented statistical and structural analyzer for ordered numeric sequences**.

It provides a small Python API and CLI for measuring properties of:

- decimal digit streams (`0..9`);
- integer-symbol streams with an explicit alphabet.

Digit Probe produces **descriptive measurements**. It does not by itself establish anomaly, defect, threat, causality, malicious intent, process correctness, or certified randomness/non-randomness.

> Development status: **Beta**.
> Version `1.0.0` marks the first intentionally stable public package/API surface; it does not mean that Digit Probe is a productionized service or product.

Italian presentation copy:
https://github.com/gcomneno/digit-probe/blob/main/README.it.md

---

## Installation

Digit Probe requires Python 3.11 or newer.

For the user-facing package release:

```bash
python -m pip install digit-probe
```

From a repository checkout:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

The installed `digit-probe` package has no runtime dependencies outside the Python standard library.

---

## Quick start

### Decimal digits

Given a text file containing digits:

```bash
digit-probe --file digits.txt --report-json report.json
```

In digit mode, the CLI extracts characters `0..9` from the input and ignores other characters.

### Integer symbols

For one integer per line:

```bash
digit-probe \
  --file buckets.txt \
  --integers \
  --alphabet 4096 \
  --report-json report.json
```

Integer mode applies modulo normalization:

```text
symbol -> symbol % alphabet
```

For strict categorical vocabularies, the caller should validate and map values into `0..M-1` before analysis.

### CLI help

```bash
digit-probe --help
```

The module entry point is also available:

```bash
python -m digit_probe --help
```

---

## Python API

The supported public imports are:

```python
from digit_probe import (
    AnalysisConfig,
    AnalysisResult,
    analyze_digits,
    analyze_integer_symbols,
)
```

Example:

```python
from digit_probe import AnalysisConfig, analyze_digits

result = analyze_digits(
    [3, 1, 4, 1, 5, 9],
    AnalysisConfig(schur_capacity=100),
)

print(result.chi_square)
```

Integer-symbol example:

```python
from digit_probe import AnalysisConfig, analyze_integer_symbols

result = analyze_integer_symbols(
    [17, 210, 3, 4095],
    alphabet=4096,
    config=AnalysisConfig(schur_capacity=500),
)

print(result.autocorr)
```

The core analysis API works on in-memory sequences and does not perform file I/O, print output, parse command-line arguments, or terminate the process.

---

## Measurements

Digit Probe currently reports these metric families:

- per-symbol counts;
- chi-square and per-symbol z-scores;
- parity runs;
- per-symbol gaps;
- autocorrelation;
- zlib compression ratio;
- majority and contextual N-gram prediction accuracy;
- SchurProbe modular-additive diagnostics.

These measurements do not all have the same semantic relationship with a numeric encoding.

For nominal categories:

- counts, chi-square, z-scores, gaps, and N-gram equality/context structure are preserved under appropriate bijective relabeling, up to relabeling of symbol-specific results;
- parity runs, numeric autocorrelation, textual compression, and SchurProbe depend on the concrete numeric representation.

The encoding, baseline, and metric must therefore be interpreted together.

---

## Consumer contract

The authoritative consumer boundary is documented at:

https://github.com/gcomneno/digit-probe/blob/main/docs/consumer-contract.md

The current supported consumer level is the **Python library consumer**.

A domain application remains responsible for:

- defining its vocabulary;
- mapping domain observations to numeric symbols;
- preserving observation order;
- validating domain-specific values;
- choosing an appropriate baseline;
- interpreting measurements in domain terms.

For a strict categorical vocabulary represented with alphabet size `M`, the recommended boundary is:

```text
domain observations
    -> deterministic consumer mapping
    -> strict consumer validation
    -> symbols in 0..M-1
    -> analyze_integer_symbols(...)
    -> AnalysisResult
    -> consumer-owned interpretation
```

---

## Empty and short inputs

The core API accepts empty and short sequences.

Some measurements may then be unavailable or non-computable and may be represented by sentinel numeric values such as `NaN` or infinity.

These states are not evidence of normality, randomness, correctness, or absence of structure.

Applications may impose stricter minimum-length requirements before invoking Digit Probe.

---

## Reproducibility

A reproducible core analysis should identify at least:

- the exact ordered input sequence;
- analysis mode;
- declared alphabet for integer mode;
- any caller-side mapping or normalization;
- the effective `AnalysisConfig`;
- Digit Probe package/source version identity.

For exact reproduction of representation-dependent details, runtime implementation details may also matter. Compression in particular depends on the concrete serialized byte representation and compression implementation.

---

## JSON reporting

The CLI can emit the historical JSON report format:

```bash
digit-probe --file digits.txt --report-json report.json
```

This JSON format is maintained for compatibility with repository tooling, but it is **not a versioned external evidence schema**.

Consumers should not infer stronger stability or scientific meaning from the JSON representation than from the documented Python analysis contract.

---

## Installed package vs repository tools

The installed wheel intentionally contains only the supported `digit_probe` package, its CLI entry point, metadata, and license.

The repository also contains research/development utilities such as:

- dataset generators;
- report comparison tooling;
- regression fixtures;
- shell test suites;
- case studies and interpretation notes.

Those checkout-only tools are useful for research and project development but are not part of the installed-package compatibility surface.

Repository documentation:

- Consumer contract:
  https://github.com/gcomneno/digit-probe/blob/main/docs/consumer-contract.md
- Lotto case study:
  https://github.com/gcomneno/digit-probe/blob/main/docs/case-study-lotto-2025.md
- Interpretation lesson:
  https://github.com/gcomneno/digit-probe/blob/main/docs/lesson-learned-interpreting-digit-probe.md

---

## Known boundaries

Digit Probe does not provide:

- anomaly verdicts;
- security incident or intrusion detection;
- defect or correctness verdicts;
- causal inference;
- malicious-intent inference;
- cryptographic randomness certification;
- a versioned evidence schema;
- a hosted service or dashboard.

The repository's historical comparison utilities may expose heuristic labels or scores. Those are not part of the consumer-safe core analysis contract.

---

## Development and verification

The repository CI verifies:

- Ruff;
- pytest;
- pre-commit;
- package build/install smoke;
- blocking dependency audit for the supported dependency set;
- secret scanning.

A release candidate is additionally built as wheel and sdist and checked with `twine check`.

---

## License

MIT. See https://github.com/gcomneno/digit-probe/blob/main/LICENSE
