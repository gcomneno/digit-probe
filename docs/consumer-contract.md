# Consumer contract

Digit Probe analyzes ordered numeric discrete representations.

It does not own the domain meaning of the symbols it receives, and its
measurements must not be interpreted independently of the representation and
baseline chosen by the consumer.

This document defines the minimum consumer-safe contract supported by the
current public Python API.

## Consumer levels

Digit Probe distinguishes three consumer levels.

### Library consumer

A library consumer calls the public Python API directly:

- `AnalysisConfig`
- `AnalysisResult`
- `analyze_digits()`
- `analyze_integer_symbols()`

This is the consumer level directly supported by the current package.

### Evidence consumer

An evidence consumer consumes a serialized analysis result independently of
the Python objects that produced it.

The current JSON report is useful for compatibility with existing tooling, but
it is not a versioned evidence contract:

- it has no schema/version identifier;
- it does not contain complete reproducibility identity;
- it retains historical field names and compatibility behavior;
- non-finite numeric states are not represented through a strict versioned
  schema.

Consumers must therefore not treat the current JSON report as an independently
versioned evidence format.

### Domain application

A domain application owns the observations that are converted into numeric
symbols.

It is responsible for:

- defining the domain vocabulary;
- choosing the mapping from observations to numeric symbols;
- preserving the intended observation order;
- enforcing domain-specific validity rules;
- choosing an appropriate baseline;
- interpreting Digit Probe measurements in domain terms.

Digit Probe does not infer domain semantics from symbol values.

## Numeric representation

A correct numeric calculation does not by itself guarantee a correct domain
interpretation.

For nominal categories, arbitrary integer labels may carry no meaningful
numeric ordering, distance, parity, or additive structure. Some Digit Probe
metrics depend only on equality or frequency structure, while others depend on
the concrete numeric representation.

The consumer must therefore know what semantic properties its numeric encoding
is intended to preserve.

## Metric encoding sensitivity

| Metric family | Effect of arbitrary bijective renumbering of nominal categories |
| --- | --- |
| Counts | Preserved up to relabeling of count keys. |
| Chi-square | Preserved when the same alphabet is used and the recoding is bijective. |
| Z-scores | Preserved up to relabeling/permutation. |
| Gaps | Preserved up to relabeling of the symbols whose gaps are measured. |
| Parity runs | Representation-sensitive because parity is derived from the numeric symbol. |
| Autocorrelation | Representation-sensitive because symbol codes are treated as numeric magnitudes. |
| Compression ratio | Representation-sensitive because concrete textual bytes are compressed. |
| N-gram majority/context prediction | Preserved under bijective relabeling of symbols because equality/context structure is preserved. |
| SchurProbe | Representation-sensitive because it uses modular addition of numeric symbols. |

Modulo collisions are not bijective recodings and may change any affected
measurement.

## Integer-symbol analysis

`analyze_integer_symbols(sequence, alphabet=M)` accepts integer symbols and
normalizes each symbol using Python modulo `M` before metric calculation.

For example:

```text
-1 % 5 == 4
5 % 5 == 0
90 % 90 == 0
```

This behavior is part of the existing integer analysis semantics.

It is suitable when modulo-`M` arithmetic is itself meaningful to the
consumer.

It is not strict categorical-vocabulary validation.

A consumer that owns a strict categorical vocabulary must validate its input
before calling Digit Probe and must provide symbols already mapped into:

```text
0 <= symbol < M
```

When that precondition holds, modulo normalization is an identity transform.

Digit Probe rejects:

- booleans as symbols;
- non-integer symbols;
- invalid alphabets such as booleans, non-integers, zero, or negative values.

`max_observed` records the maximum value from the original integer sequence,
before modulo normalization. For an empty integer sequence it is `-1`.

## Digits analysis

`analyze_digits()` accepts only integer digits in `0..9`.

It rejects booleans, non-integers, negative integers, and integers greater than
9.

Unlike integer-symbol analysis, digit analysis does not apply modulo
normalization.

## Empty, short, and degenerate inputs

The core API accepts empty and short sequences.

Some metrics may then be unavailable, degenerate, or represented by sentinel
numeric states such as `NaN` or infinity.

Such values mean that the corresponding measurement is unavailable or
non-computable under the current input. They are not evidence of normality,
randomness, absence of structure, or correctness.

Consumers must distinguish:

- a finite calculated measurement;
- an unavailable/non-computable measurement;
- absence of evidence.

A domain application may impose stricter minimum-length requirements before
calling Digit Probe.

## Stable public surface

The current public Python surface consists of:

- `AnalysisConfig`;
- `AnalysisResult`;
- `analyze_digits()`;
- `analyze_integer_symbols()`.

For identical ordered input, alphabet, effective configuration, and
implementation, the core analysis is deterministic.

`AnalysisConfig` currently contains `schur_capacity`.

`AnalysisResult` is the structured public result returned by the library API.

The following surfaces must not be confused with a versioned consumer evidence
contract:

- the current unversioned JSON report;
- CLI input-cleaning behavior;
- `compare_reports.py`;
- its heuristic severity and `AnomalyScore` logic.

Those compatibility or research surfaces do not define stronger scientific or
domain conclusions than the core measurements themselves.

## Reproducibility

A reproducible analysis must identify at least:

- the exact ordered input sequence before analysis;
- analysis mode (`digits` or `integers`);
- the declared alphabet for integer mode;
- the consumer-owned mapping or normalization applied before Digit Probe;
- the effective `AnalysisConfig`;
- Digit Probe implementation identity, such as package version plus source
  commit.

For exact reproduction of representation-dependent implementation details,
the relevant runtime environment may also matter. Compression results in
particular depend on the concrete byte representation and compression
implementation.

CLI reproduction additionally requires the original file contents and
effective CLI options because the historical CLI performs input filtering that
the public library API does not perform.

## Interpretation boundary

Digit Probe may provide descriptive evidence such as:

- symbol frequencies or distribution under a stated baseline;
- measured ordered dependence under a documented diagnostic;
- observed gap structure;
- contextual prediction accuracy under the documented split and predictor;
- compressibility of the concrete analyzed representation;
- the result of the documented modular-additive SchurProbe diagnostic.

Digit Probe alone does not establish:

- anomaly;
- defect;
- incident;
- threat;
- intrusion;
- causality;
- malicious intent;
- correctness or incorrectness of a domain process;
- certified randomness;
- certified non-randomness.

A downstream consumer may form domain conclusions from Digit Probe
measurements together with additional evidence and policy, but those
conclusions remain consumer-owned.

## Consumer-safe boundary for the first Proof of Value

The existing public API is sufficient for the first consumer Proof of Value.

A new strict non-modulo API is not required beforehand.

The PoV consumer must instead enforce this boundary explicitly:

```text
domain observations
    -> consumer-owned deterministic mapping
    -> consumer-owned validation
    -> symbols strictly in 0..M-1
    -> analyze_integer_symbols(...)
    -> AnalysisResult
    -> consumer-owned interpretation
```

Therefore:

```text
STRICT_API_REQUIRED_BEFORE_POV = NO
CALLER_SIDE_STRICT_VALIDATION_REQUIRED = YES
```

A future strict library boundary should be introduced only if a demonstrated
consumer need requires Digit Probe itself to own vocabulary/range rejection.
