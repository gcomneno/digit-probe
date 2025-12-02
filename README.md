# digit-probe
Analizzatore **statistico/strutturale** per sequenze numeriche. 

Supporta:
- **cifre** (`digits`): file di sole cifre `0..9` senza spazi/newline
- **interi** (`integers`): un intero per riga con **alfabeto dichiarato** (`--alphabet M`)

Pensato per diagnosticare **random-like vs struttura** in stream numerici e per ispezionare **bucket** prodotti da strumenti esterni 
(es. [Turbo-Bucketizer](https://github.com/gcomneno/turbo-bucketizer)).
(es. [Turbo-Bucketizer-2](https://github.com/gcomneno/turbo-bucketizer-cpp)).
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
pip install -r requirements.txt  # leggero o vuoto: usa stdlib
````

> Suggerito: tenere i dataset/risultati fuori dal versionamento (`.gitignore` già predisposto).

---

## 🧩 Struttura repo (essenziale)

```bash
src/
  digit_probe.py
  compare_reports.py
  make_datasets.py
tests/
  basic.sh, 
  advanced.sh,
  gen_*.py
Makefile
```

---

## ⌨️ Uso rapido

### Modalità **digits** (cifre senza spazi)

```bash
python3 src/digit_probe.py --file pi_100k.txt --report-json pi.json
```

### Modalità **integers** (un intero per riga, serve `--alphabet`)

```bash
# Esempio: bucket in [0..4095]
python3 src/digit_probe.py --file buckets_k12.txt --integers --alphabet 4096 --report-json buckets.json
```

### Opzioni principali

```
--file PATH             input (digits o integers)
--n N                   limita la lunghezza analizzata
--integers              abilita modalità "integers"
--alphabet M            alfabeto per integers (obbligatorio con --integers)
--report-json OUT.json  salva un report JSON
--schur-N R             R massimo per SchurProbe (default: 5000)
```

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

## 📄 Licenza
MIT. Vedi `LICENSE`.

---

## 💡 Motto
> “Se è **random-like**, non lo è per sempre. Se è **strutturato**, lo becchiamo.”
