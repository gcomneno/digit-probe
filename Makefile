# ==== Test Suite Digit-Probe ====

PY ?= python3
DP ?= $(PY) digit_probe.py
CMP ?= $(PY) compare_reports.py
MKD ?= $(PY) make_datasets.py

OUTDIR ?= out
TESTDIR ?= tests

.PHONY: test-basic test-advanced selftest clean-tests

test-basic:
	@mkdir -p $(OUTDIR)
	bash $(TESTDIR)/basic.sh "$(PY)" "$(OUTDIR)"

test-advanced:
	@mkdir -p $(OUTDIR)
	bash $(TESTDIR)/advanced.sh "$(PY)" "$(OUTDIR)"

selftest: test-basic test-advanced
	@$(PY) $(TESTDIR)/selftest_aggregate.py --in out --md out/SELFTEST_SUMMARY.md
	@echo "[ok] Selftest completato. Vedi: out/SELFTEST_SUMMARY.md"

clean-tests:
	@rm -rf $(OUTDIR)
	@echo "[ok] Pulito $(OUTDIR)"
