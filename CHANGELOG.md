# Changelog

## 1.0.0 — First stable public package/API release

`1.0.0` marks the first intentionally stable public Python package and CLI surface for Digit Probe.

Digit Probe remains **research technology**. This release does not classify the project as a productionized service or product.

### Public package surface

The supported installed package provides:

- `AnalysisConfig`;
- `AnalysisResult`;
- `analyze_digits()`;
- `analyze_integer_symbols()`;
- the `digit-probe` CLI;
- the `python -m digit_probe` module entry point.

The installed wheel intentionally does not ship repository-only dataset generators, comparison utilities, fixtures, case studies, or development scripts.

### Analysis capabilities

The package provides descriptive measurements for ordered numeric sequences, including:

- per-symbol counts;
- chi-square and z-scores;
- parity runs;
- gaps;
- autocorrelation;
- zlib compression ratio;
- majority/contextual N-gram accuracy;
- SchurProbe modular-additive diagnostics.

### Consumer boundary

The release documents an explicit consumer-safe contract.

Domain consumers own:

- vocabulary and semantic mapping;
- observation order;
- strict domain validation;
- baseline selection;
- downstream interpretation.

For strict categorical vocabularies represented with alphabet size `M`, callers should validate and map symbols into `0..M-1` before invoking `analyze_integer_symbols()`.

### Compatibility boundaries

The Python library API is the supported consumer surface.

The historical JSON report remains available for compatibility with repository tooling, but it is not a versioned external evidence schema.

Repository comparison utilities may contain heuristic scores or labels; those are not part of the core consumer-safe analysis contract.

### Interpretation limits

Digit Probe measurements alone do not establish:

- anomaly;
- defect;
- incident;
- threat;
- intrusion;
- causality;
- malicious intent;
- process correctness;
- certified randomness or non-randomness.

### Packaging

- Python requirement: `>=3.11`.
- Runtime package dependencies: none outside the Python standard library.
- Wheel and sdist are validated with `twine check`.
- The package smoke test installs the built wheel into an isolated virtual environment before exercising the installed CLI and public API.

### Historical note

The previous public GitHub prototype release was `v0.1.0`.

The jump to `1.0.0` identifies the first deliberately stabilized public package/API boundary after the repository's prototype and research-hardening work. It does not indicate Production/Stable product maturity.
