# Case study – Lotto 2025 (tutte le ruote)
Questo case study mostra come usare **Digit-Probe** per caratterizzare un dataset reale:
tutte le estrazioni del Lotto 2025 (tutte le ruote), viste come sequenza di interi `1..90`.
---

## Dataset
- Origine: archivio pubblico estrazioni Lotto 2025.
- Costruzione:
  - per ogni estrazione si prendono i 55 numeri (11 ruote × 5 numeri),
  - si appiattano in una sequenza unica,
  - si salvano come un intero per riga (`1..90`).

Nel repository, il dataset risultante è:
```bash
datasets/lotto_2025_numbers.txt
```

contiene:

```bash
N = 10505
valori in [1..90]
un intero per riga
```

---

## Metodo
Usiamo Digit-Probe in modalità **integers** con alfabeto `M = 90`:

```bash
python src/digit_probe.py \
  --file datasets/lotto_2025_numbers.txt \
  --integers \
  --alphabet 90 \
  --report-json out/lotto-2025-full-integers.json
```

* `--integers` abilita la modalità "un intero per riga".
* `--alphabet 90` dichiara che i simboli appartengono a `0..89` (nel caso Lotto i valori sono `1..90`, l’effetto del mod è nullo).
* `--report-json` salva un report strutturato, utile per confronti successivi.

---

## Risultati (estratto)
Output testuale di Digit-Probe:

```bash
MODE: integers  |  N=10505  alphabet M=90  (max_observed=90)

Chi-square (M=90 bins): 92.39 (expected per bin=116.72)

Runs test (even/odd values): Z=1.653, p=0.098

Autocorrelation (lags 1..5):
  lag 1: +0.0158
  lag 2: -0.0305
  lag 3: +0.0027
  lag 4: +0.0000
  lag 5: -0.0149

Compression ratio (zlib over "ints text"): 0.3858

N-gram predictor (80/20 split) over integer symbols:
  n=1: 0.9995% (baseline≈1.11%)
  n=2: 0.9528% (baseline≈1.11%)
  n=3: 1.0010% (baseline≈1.11%)

SchurProbe (first 5000 symbols):
  triples=12,497,500  count=137,988  expected≈138,861
  fraction=0.011041  z=-2.36
```

Per confronto, un RNG uniforme `1..90` con la stessa lunghezza e seed fisso (`datasets/lotto_2025_numbers_rng.txt`) produce un profilo molto simile:

```bash
N=10505, M=90
chi-square ≈ 101.92
compress   ≈ 0.3851
max_rho    ≈ 0.0070
Schur z    ≈ -0.67
```

---

## Interpretazione

### Distribuzione 1..90
- Il **chi-quadrato** di Lotto 2025 (≈92.4) è persino inferiore al valore atteso per 89 gradi di libertà.
- Non emergono numeri o gruppi di numeri palesemente iper-frequenti o sotto-rappresentati.

### Struttura temporale
- Le **autocorrelazioni** sui lag 1..5 sono tutte piccole (in modulo ≲ 0.03).
- Il **runs test** pari/dispari (Z≈1.65, p≈0.098) è borderline ma non segnala pattern eclatanti nella sequenza di parità.

### Predicibilità locale
- Gli **n-gram** (n=1..3) centrano il prossimo numero con ~1% di successo, a fronte di una baseline ≈1.11% per `M=90`.
- In pratica il predittore Markoviano non trova regolarità sfruttabili.

### Struttura additiva (SchurProbe)
- Il test **SchurProbe** restituisce z≈−2.36:
  * è una deviazione misurabile dall’ideale uniforme,
  * ma è lontanissima dai valori “catastrofici” che si osservano su sequenze palesemente strutturate (gradiente 0..9, LCG marcio, ecc.).

---

## Conclusione
Per le metriche calcolate da Digit-Probe:
- il dataset **Lotto 2025** ha un profilo molto simile a quello di un **RNG uniforme 1..90** con la stessa lunghezza;
- non emergono bias grossolani né strutture seriali forti del tipo che ci si aspetterebbe da un generatore difettoso.

Non è una prova matematica di “piena casualità” (il Lotto non è un RNG), ma un’indicazione chiara:
**a questo livello di analisi non salta fuori alcun “trucco facile” sfruttabile**.

Per confrontare Lotto 2025 con altri dataset (π, e, primi, gradienti, RNG biased, LCG, ecc.) vedi anche la [GALLERY](../GALLERY.md).
