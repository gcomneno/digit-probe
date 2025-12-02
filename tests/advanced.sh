#!/usr/bin/env bash
set -euo pipefail
PY=${1:-python3}
OUT=${2:-out}

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo ">>> ADVANCED TESTS → output in: $OUT (root=$ROOT)"

mkdir -p "$OUT"

# 4) Gradient 0..9 ripetuto
"$PY" "$ROOT/tests/gen_gradient.py" --repeat 10000 > "$OUT/grad.txt"
"$PY" "$ROOT/src/digit_probe.py" --file "$OUT/grad.txt" --report-json "$OUT/grad.json"

# 5) Bucketizzazione (integers)
if [[ -n "${TURBO_BIN:-}" && -x "${TURBO_BIN:-}" ]]; then
  echo "[info] uso Turbo-Bucketizer: $TURBO_BIN"
  "$TURBO_BIN" --cidr 10.0.0.0/16 --k 12 --sample 40960 --export "$OUT/buckets_k12.txt"
else
  echo "[info] TURBO_BIN non definita — uso generatore sintetico"
  "$PY" "$ROOT/tests/gen_buckets_synth.py" --m 4096 --n 40960 --stride 257 > "$OUT/buckets_k12.txt"
fi
"$PY" "$ROOT/src/digit_probe.py" --file "$OUT/buckets_k12.txt" --integers --alphabet 4096 --report-json "$OUT/buckets_k12.json"

# 6) Schur stress (pattern additivo debole)
"$PY" "$ROOT/tests/gen_schur_trap.py" --n 50000 > "$OUT/schur_trap.txt"
"$PY" "$ROOT/src/digit_probe.py" --file "$OUT/schur_trap.txt" --report-json "$OUT/schur_trap.json"

# Confronti mirati
"$PY" "$ROOT/src/compare_reports.py" "$OUT/grad.json" "$OUT/rnd.json" --baseline "$OUT/rnd.json" --md "$OUT/compare_grad_vs_rnd.md"
"$PY" "$ROOT/src/compare_reports.py" "$OUT/buckets_k12.json" "$OUT/rnd.json" --baseline "$OUT/rnd.json" --md "$OUT/compare_buckets_vs_rnd.md"
"$PY" "$ROOT/src/compare_reports.py" "$OUT/schur_trap.json" "$OUT/rnd.json" --baseline "$OUT/rnd.json" --md "$OUT/compare_schurtrap_vs_rnd.md"

echo "[ok] ADVANCED terminati."
