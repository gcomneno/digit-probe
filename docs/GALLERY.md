# Digit-Probe – Gallery di casi reali e sintetici

Questa pagina raccoglie alcuni dataset analizzati con `digit_probe.py`, per dare un'idea del **profilo statistico** di casi reali vs RNG sintetici.

Ogni riga riassume alcune metriche chiave:

- `N`: lunghezza della sequenza
- `M`: dimensione alfabeto (`alphabet`)
- `χ²`: chi-quadrato sulla distribuzione dei simboli
- `compress`: rapporto di compressione zlib (più basso = più struttura/ripetizione)
- `max_rho`: massimo valore assoluto di autocorrelazione sui lag 1..5
- `Schur z`: z-score del test SchurProbe

---

| Dataset | Tipo | N | M | χ² | compress | max_rho (lag≤5) | Schur z |
|:--------|:-----|---:|---:|---:|--------:|----------------:|--------:|
| Lotto 2025 – integers (1..90) | integers | 10505 | 90 | 92.39 | 0.3858 | 0.0305 | -2.36 |
| RNG 1..90 – baseline | integers | 10505 | 90 | 101.92 | 0.3851 | 0.0070 | -0.67 |
| π – 100k cifre | digits | 100000 | 10 | 4.09 | 0.4817 | 0.0027 | 0.59 |
| e – 100k cifre | digits | 100000 | 10 | 17.68 | 0.4819 | 0.0022 | 0.06 |
| Primi – cifre concatenati (≈100k) | digits | 100000 | 10 | 16508.61 | 0.4194 | 0.2317 | -23.80 |
| Gradiente mod 10 – 0..9 ripetuti (100k) | digits | 100000 | 10 | 0.00 | 0.0023 | 0.5151 | 10605.54 |
| RNG digits – uniform (0..9) | digits | 21010 | 10 | 2.84 | 0.5038 | 0.0061 | -0.08 |
| RNG digits – biased7 (7≈40%) | digits | 21010 | 10 | 21783.74 | 0.4487 | 0.0121 | -39.92 |
| RNG digits – LCG mod10 (marcio) | digits | 21010 | 10 | 31515.00 | 0.0023 | 0.9999 | 3977.52 |
