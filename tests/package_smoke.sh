#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
PYTHON="${PYTHON:-python3}"

"$PYTHON" -m build --outdir "$TMP_DIR/dist" "$ROOT"
"$PYTHON" -m twine check "$TMP_DIR/dist"/*

"$PYTHON" -m venv "$TMP_DIR/venv"
"$TMP_DIR/venv/bin/python" -m pip install "$TMP_DIR/dist"/*.whl

mkdir "$TMP_DIR/work"
printf '0123456789012345678901234567890123456789\n' > "$TMP_DIR/work/digits.txt"

cd "$TMP_DIR/work"
"$TMP_DIR/venv/bin/digit-probe" --help
"$TMP_DIR/venv/bin/digit-probe" \
  --file digits.txt \
  --schur-N 20 \
  --report-json report.json

"$TMP_DIR/venv/bin/python" - <<'PY'
import json
from pathlib import Path

report = json.loads(Path("report.json").read_text(encoding="utf-8"))
assert report["mode"] == "digits"
assert report["N"] == 40
assert report["alphabet"] == 10
PY
