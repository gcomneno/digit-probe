#!/usr/bin/env bash
set -euo pipefail
PY=${1:-python3}
OUT=${2:-out}

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo ">>> BASIC TESTS → output in: $OUT (root=$ROOT)"

mkdir -p "$OUT"

# 1) Random puro (baseline)
"$PY" "$ROOT/tests/gen_random.py" --n 100000 > "$OUT/rnd_100k.txt"
"$PY" "$ROOT/src/digit_probe.py" --file "$OUT/rnd_100k.txt" --report-json "$OUT/rnd.json"

# 2) Pi (offline)
"$PY" "$ROOT/src/make_datasets.py" --n 100000 --only pi --offline
cp "$ROOT/pi_100k.txt" "$OUT/pi_100k.txt"
"$PY" "$ROOT/src/digit_probe.py" --file "$OUT/pi_100k.txt" --report-json "$OUT/pi.json"

# 3) Sequenza costante di '7' (100k cifre) – senza usare pipe/head per evitare SIGPIPE
"$PY" - << 'EOF' > "$OUT/const_7.txt"
N = 100_000
print("7" * N, end="")
EOF

"$PY" "$ROOT/src/digit_probe.py" --file "$OUT/const_7.txt" --report-json "$OUT/const.json"

# Confronti rapidi
"$PY" "$ROOT/src/compare_reports.py" "$OUT/pi.json" "$OUT/rnd.json" \
  --baseline "$OUT/rnd.json" --md "$OUT/compare_pi_vs_rnd.md"

"$PY" "$ROOT/src/compare_reports.py" "$OUT/const.json" "$OUT/rnd.json" \
  --baseline "$OUT/rnd.json" --md "$OUT/compare_const_vs_rnd.md"

echo "[ok] BASIC terminati."
