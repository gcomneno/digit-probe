#!/usr/bin/env python3
"""
Test di regressione per Digit-Probe usando la RNG Zoo a cifre (0..9):

- digits_rng_uniform.txt    -> deve sembrare random-like
- digits_rng_biased7.txt    -> deve mostrare un bias mostruoso sul 7
- digits_rng_lcg_mod10.txt  -> deve essere chiaramente periodico/marcio

Se questi test iniziano a fallire, vuol dire che abbiamo rotto qualcosa
nei calcoli statistici o nei report di digit_probe.py.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from src.generative.gen_rng_zoo import main as gen_rng_zoo_main

BASE_DIR = Path(__file__).resolve().parent.parent
DIGIT_PROBE = BASE_DIR / "src" / "digit_probe.py"
DATASETS_DIR = BASE_DIR / "datasets"


def run_digit_probe_digits(input_path: Path, json_out: Path) -> dict:
    """Esegue digit_probe.py in modalità digits e ritorna il JSON."""
    cmd = [
        sys.executable,
        str(DIGIT_PROBE),
        "--file",
        str(input_path),
        "--alphabet",
        "0123456789",
        "--report-json",
        str(json_out),
    ]
    # Se digit_probe stampa su stdout/stderr, lasciamo tutto così com'è
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    data = json.loads(json_out.read_text(encoding="utf-8"))
    return data


@pytest.fixture(scope="session", autouse=True)
def ensure_rng_datasets() -> None:
    """
    Garantisce che la RNG Zoo sia presente prima di eseguire i test.

    Usa tests/gen_rng_zoo.py per (ri)generare i file
    digits_rng_uniform.txt, digits_rng_biased7.txt, digits_rng_lcg_mod10.txt.
    """
    gen_rng_zoo_main()
    assert (DATASETS_DIR / "digits_rng_uniform.txt").exists()
    assert (DATASETS_DIR / "digits_rng_biased7.txt").exists()
    assert (DATASETS_DIR / "digits_rng_lcg_mod10.txt").exists()


def test_uniform_rng_looks_random(tmp_path: Path) -> None:
    """L'RNG uniforme deve sembrare random-like su tutti i test chiave."""
    src = DATASETS_DIR / "digits_rng_uniform.txt"
    out = tmp_path / "uniform.json"
    report = run_digit_probe_digits(src, out)

    assert report["mode"] == "digits"
    assert report["N"] > 10000

    chi2 = report["chi_square"]
    schur_z = report["schur"]["z"]
    compress = report["compress_ratio"]

    # Chi-quadrato molto piccolo (vicino al valore atteso ~9)
    assert chi2 < 30.0

    # Schur z-score vicino a 0
    assert abs(schur_z) < 3.0

    # Compressione in un range da random-like su alfabeto 10
    assert 0.4 < compress < 0.6


def test_biased7_shows_strong_marginal_bias(tmp_path: Path) -> None:
    """Il dataset biased7 deve mostrare un bias fortissimo su 7."""
    src = DATASETS_DIR / "digits_rng_biased7.txt"
    out = tmp_path / "biased7.json"
    report = run_digit_probe_digits(src, out)

    N = report["N"]
    counts = report["counts"]
    chi2 = report["chi_square"]
    compress = report["compress_ratio"]
    schur_z = report["schur"]["z"]

    # Il 7 deve essere iper-frequente (≈40% del totale)
    count_7 = counts["7"]
    assert count_7 > 0.3 * N  # <- qui N è usato

    # Chi-quadrato fuori scala rispetto a un RNG sano
    assert chi2 > 1000.0

    # SchurProbe deve vedere una deviazione molto grossa
    assert abs(schur_z) > 10.0

    # Distribuzione compressibile più dell'uniforme
    assert compress < 0.49


def test_lcg_mod10_is_clearly_broken(tmp_path: Path) -> None:
    """
    L'LCG mod 10 deve risultare chiaramente non-random:

    - solo 4 cifre usate
    - chi-quadrato enorme
    - autocorrelazioni forti
    - n-gram predictor molto sopra baseline
    - compressione quasi totale
    """
    src = DATASETS_DIR / "digits_rng_lcg_mod10.txt"
    out = tmp_path / "lcg.json"
    report = run_digit_probe_digits(src, out)

    counts = report["counts"]
    chi2 = report["chi_square"]
    compress = report["compress_ratio"]
    autocorr = report["autocorr"]
    schur_z = report["schur"]["z"]

    # Solo 0,1,7,8 devono comparire; le altre devono essere zero
    used = {d for d, c in counts.items() if c > 0}
    assert used == {"0", "1", "7", "8"}

    # Deviazione mostruosa rispetto all'uniforme
    assert chi2 > 10000.0

    # Autocorrelazioni fortissime a qualche lag (es. lag 2 o 4)
    assert abs(autocorr["2"]) > 0.5 or abs(autocorr["4"]) > 0.5

    # Compressione quasi totale (stringa altamente periodica)
    assert compress < 0.1

    # SchurProbe totalmente fuori scala
    assert abs(schur_z) > 100.0
