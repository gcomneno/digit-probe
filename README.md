# Digit-Probe
Analizzatore **statistico/strutturale** per sequenze numeriche.

Supporta:
- **cifre** (`digits`): file di sole cifre `0..9` (eventuali spazi/newline vengono ignorati)
- **interi** (`integers`): un intero per riga con **alfabeto dichiarato** (`--alphabet M`)

Pensato per diagnosticare **random-like vs struttura** in stream numerici e per ispezionare **bucket** prodotti da strumenti esterni:
(es. [Turbo-Bucketizer](https://github.com/gcomneno/turbo-bucketizer))
(o [Turbo-Bucketizer-2](https://github.com/gcomneno/turbo-bucketizer-cpp))

---

## ✨ Cosa misura

- **Distribuzione** per simbolo, **chi-square**, **z-score**
- **Runs test** (pari/dispari)
- **Gaps** per simbolo (conteggio e **gap medio**)
- **Autocorrelazione** (lag `1..5`)
- **Compression ratio (zlib)** come proxy di ripetizione/struttura
- **N-gram predictor** (n=1..3, split 80/20)
- **SchurProbe** *(additività mod M)*
  - Coppie `i<j`, indice `k=(i+j) mod R`
  - Verifica `(seq[i]+seq[j]) % M == seq[k]`
  - `N_triples = C(R,2)`, atteso `E = N_triples/M`, varianza `N p (1-p)`, `z-score` standard

Output: **stampa leggibile** + **JSON** opzionale con `--report-json` (compatibile con `compare_reports.py`).

---

## 🚀 Installazione

Richiede **Python 3.11+** (ok anche 3.13).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # leggero: usa solo stdlib + pochi pacchetti
```

> Suggerito: tenere i dataset/risultati fuori dal versionamento (`.gitignore` già predisposto).

---

## 🧩 Struttura repo (essenziale)

```bash
src/
  digit_probe.py          # core analyzer (CLI)
  compare_reports.py      # confronto tra più JSON
  make_datasets.py        # generatori semplici (pi, e, gradienti, ecc.)
  generative/
    gen_rng_digits_zoo.py # RNG Zoo per test di regressione
    gen_rng_1_90.py       # (opzionale) generatori su 1..90

tests/
  basic.sh                # smoke test rapido
  advanced.sh             # test avanzati (gradienti, bucket, schur-stress)
  test_rng_digits_ci.py   # test di regressione RNG Zoo

datasets/
  pi_100k.txt             # esempi offline
  e_100k.txt
  ...
Makefile
```

---

## ⌨️ Uso rapido

### Modalità **digits** (cifre senza spazi “logici”)

```bash
python3 src/digit_probe.py --file pi_100k.txt --report-json pi.json
```

- L’input è trattato come **stream di cifre**: i caratteri `0..9` vengono letti, tutto il resto viene ignorato (spazi, newline, virgole…).
- File tipico: una lunga stringa di cifre, opzionalmente con newline finali.

### Modalità **integers** (un intero per riga, serve `--alphabet`)

```bash
# Esempio: bucket in [0..4095]
python3 src/digit_probe.py --file buckets_k12.txt --integers --alphabet 4096 --report-json buckets.json
```

- Ogni riga deve contenere un singolo intero (con eventuali spazi iniziali/finali).
- I valori sono usati **mod M** (`M = --alphabet`), quindi un valore 5000 con `--alphabet 4096` diventa 5000 % 4096.

### Opzioni principali

```text
--file PATH             input (digits o integers)
--n N                   limita la lunghezza analizzata
--integers              abilita modalità "integers"
--alphabet M            alfabeto per integers (obbligatorio con --integers)
--report-json OUT.json  salva un report JSON
--schur-N R             R massimo per SchurProbe (default: 5000)
```

---

## 🧷 Guida rapida – come preparare un tuo dataset

### 1. Decidi il tipo di sequenza

- **Cifre (`digits`)**:
  - sequenze come cifre di π, e, costanti, output di funzioni hash, stream di cifre da log, cifre di estrazioni del Lotto, ecc.
- **Interi (`integers`)**:
  - bucket ID (`0..M-1`),
  - valori discreti (stati di un automa, classi, label),
  - output di PRNG personalizzati, ecc.

### 2. Preparazione file per modalità `digits`

Formato consigliato: file di testo con **solo cifre** (più eventuali newline).

Esempi:

- hai un CSV con cifre miste ad altro, puoi “spremere” solo i numeri:

  ```bash
  # Estrai solo cifre e scrivi in mydigits.txt
  tr -cd '0-9' < raw_input.txt > mydigits.txt
  ```

- ora puoi analizzare:

  ```bash
  python3 src/digit_probe.py --file mydigits.txt --report-json mydigits.json
  ```

### 3. Preparazione file per modalità `integers`

Formato: **un intero per riga**.

Esempi:

- hai bucket ID `0..4095`:

  ```text
  17
  210
  3
  4095
  0
  ...
  ```

  analisi:

  ```bash
  python3 src/digit_probe.py     --file my_buckets.txt     --integers     --alphabet 4096     --report-json my_buckets.json
  ```

- hai numeri `1..90` (es. estrazioni del Lotto) uno per riga:

  ```bash
  python3 src/digit_probe.py     --file lotto_2025_numbers.txt     --integers     --alphabet 90     --report-json lotto_2025_integers.json
  ```

  (internamente verranno usati mod 90, ma se i valori sono già in `1..90` l’effetto è nullo).

### 4. Confrontare più dataset

Una volta che hai i tuoi JSON (`--report-json`), puoi confrontarli:

```bash
python3 src/compare_reports.py   out/mio_dataset.json   out/rng_uniform.json   --baseline out/rng_uniform.json   --md out/compare_mio_vs_rng.md
```

Questo produce un Markdown con:

- differenze sulle metriche chiave (chi-square, autocorr, compressione, Schur…),
- un **AnomalyScore** sintetico per capire chi è più “strano” rispetto alla baseline.

---

## 🧪 RNG Zoo & test di regressione (CI)

Il progetto contiene una piccola **RNG Zoo a cifre** per verificare che gli strumenti diagnostici non si rompano nel tempo:

Dataset generati da `src/generative/gen_rng_digits_zoo.py`:

- `digits_rng_uniform.txt` → cifre 0..9 da RNG uniforme “sano”
- `digits_rng_biased7.txt` → distribuzione **truccata** con 7 iper-favorito (~40%)
- `digits_rng_lcg_mod10.txt` → LCG modulo 10 **marcio e periodico** (solo 4 cifre usate)

La CI (GitHub Actions) lancia `pytest` e verifica che:

- l’RNG **uniforme** risulti:
  - chi-square piccolo,
  - z-score per cifra vicino a 0,
  - compressione compatibile con random-like,
  - SchurProbe con `z` vicino a 0;
- il dataset **biased7** risulti **fortemente non uniforme**:
  - il 7 è iper-frequente,
  - chi-square e SchurProbe con z enormi,
  - gaps e compressione rivelano il trucco;
- il dataset **LCG mod10** venga visto come completamente **non-random**:
  - solo poche cifre usate,
  - chi-square mostruoso,
  - autocorrelazioni forti,
  - compressione quasi totale.

Se cambiano algoritmi/parametri interni e questi test iniziano a fallire, è un campanello d’allarme: qualcosa nel motore di analisi si è degradato.

---

## 📦 Dataset “famosi” (offline)

Genera 100k cifre di π o e **senza rete**:

```bash
python3 src/make_datasets.py --n 100000 --only pi --offline
python3 src/make_datasets.py --n 100000 --only e  --offline
```

Poi analizza:

```bash
python3 src/digit_probe.py --file pi_100k.txt --report-json pi.json
python3 src/digit_probe.py --file e_100k.txt  --report-json e.json
```

---

## 🧪 Suite di test

Comandi:

```bash
make test-basic     # random, pi (offline), sequenza costante
make test-advanced  # gradiente, bucket (sintetico o Turbo), schur-stress
make selftest       # aggrega i JSON in out/SELFTEST_SUMMARY.md
```

Se hai Turbo-Bucketizer e vuoi usarlo davvero nei test avanzati:

```bash
TURBO_BIN=/percorso/turbo-bucketizer make test-advanced
```

Risultati in `out/` (JSON + Markdown di confronto).

---

## 🔍 Confronto report (più file)

Confronta due o più JSON:

```bash
python3 src/compare_reports.py out/pi.json out/e.json --baseline out/pi.json --md out/compare_pi_e.md
```

Output sintetico (ordinabile) con indicatori di severità e **AnomalyScore**.

---

## 📘 Esempi interpretativi (due dritte)

- **Compressione zlib**
  - *digits (M=10)* random-like ⇒ ~**0.46–0.50**
  - valori **molto bassi** (≪0.44) ⇒ ripetizioni/strutture/periodicità

- **Autocorrelazione**
  - random-like ⇒ `|ρ|` piccoli (≲0.02 con N grandi)
  - picchi stabili ⇒ dipendenze

- **SchurProbe (z)**
  - `z ≈ 0` ⇒ in linea con casualità mod M
  - `|z|` alto ⇒ struttura additiva (pattern, periodi, generazioni affini)

---

## 🧠 SchurProbe in due righe

Su `R` simboli (cap a `--schur-N`), testiamo tutte le coppie `i<j` e chiediamo se la “somma mod M” riappare in posizione `k=(i+j) mod R`.
Atteso “casuale”: **1 volta su M**. Misuriamo quanto te ne discosti con uno **z-score** binomiale standard.

---

## 🔗 Integrazione con Turbo-Bucketizer

- Esporta bucket come **interi** (`0..(2^k-1)`) in `txt/csv`
- Analizza con `--integers --alphabet 2^k`
- Confronta con baseline random, gradienti e sequenze sintetiche (`tests/advanced.sh` lo fa per te)

---

## 🧾 JSON di output (schema minimo)

```json
{
  "mode": "digits|integers",
  "N": 100000,
  "alphabet": 10,
  "chi_square": 4.093,
  "expected_per_bin": 10000.0,
  "counts": {"0":9999, "1":10137, ...},
  "runs": {"Z": 0.565, "p_two_tailed": 0.5724},
  "autocorr": {"1": -0.0025, "2": 0.0022, ...},
  "compress_ratio": 0.4817,
  "ngram": {"1": 0.1013, "2": 0.1026, "3": 0.0998},
  "schur": {
    "triples": 12497500,
    "count": 124749,
    "expected": 125777.4,
    "fraction": 0.00998,
    "z": -2.91,
    "first_violation_index": 59
  }
}
```

---

## 🛠️ Note pratiche

- In **integers mode** i valori sono usati **mod M** (M=`--alphabet`).
- `--n` può accelerare prove rapide (es. `--n 20000`).
- `--schur-N` (default 5000) limita il costo di SchurProbe (crescita ~quadratica).

---

## Case study

- [Lotto 2025 – caratterizzazione con Digit-Probe](docs/case-study-lotto-2025.md)
  Esempio reale di utilizzo in modalità `integers` (1..90), confrontato con un RNG uniforme baseline.

---

## 📄 Licenza

MIT. Vedi `LICENSE`.

---

## 💡 Motto
> “Se è **random-like**, non lo è per sempre. Se è **strutturato**, lo becchiamo.”
