# digit-probe v1.0.0 — Initial stable release
Analizzatore leggero di sequenze numeriche (cifre o interi) con report statistici, confronto tra dataset e supporto a casi d’uso “random-like vs struttura”.

Questa è la prima versione stabile e completa del toolkit.

---

## ✨ Highlights
- **Analisi end-to-end** di sequenze:
  - cifre decimali (es. π, e)
  - interi generici (es. bucket del Turbo-Bucketizer)
- **Metriche chiave**:
  - Chi-square (uniformità per M simboli)
  - Runs test (parità) con Z-score
  - Gaps (conteggio e distanza media tra occorrenze)
  - Autocorrelazione lag 1..5
  - Compression ratio (zlib) come proxy di ripetizioni e struttura facilmente comprimibile
  - N-gram predictor (n=1..3) con split 80/20
  - **SchurProbe** (triple a+b=c mod M) con atteso e z-score
- **Report strutturati**: JSON (per automazione) + riepilogo CLI leggibile
- **Comparatore**: ranking multi-metrica con export in **CSV** e **Markdown**
- **Dataset ready-made**: generazione offline di 100k cifre per **π** ed **e** (fallback `mpmath`)

---

## 📦 Contenuto
- `digit_probe.py` — analisi singolo dataset (stdout + `--report-json`)
- `make_datasets.py` — genera `pi_100k.txt` / `e_100k.txt` (online/offline)
- `compare_reports.py` — confronto tra più report `.json` (CSV/MD opzionali)

---

## 🧪 Esempi rapidi
```bash
# 1) Genera 100k cifre (offline con mpmath)
python3 make_datasets.py --n 100000 --only pi --offline
python3 make_datasets.py --n 100000 --only e  --offline

# 2) Analizza π ed e
python3 digit_probe.py --file pi_100k.txt --report-json pi.json
python3 digit_probe.py --file e_100k.txt  --report-json e.json

# 3) Confronta i report ed esporta CSV/Markdown
python3 compare_reports.py pi.json e.json --baseline pi.json --csv compare.csv --md compare.md
````

Modalità per **interi** (es. bucket Turbo-B, M=256):

```bash
python3 digit_probe.py --file buckets.txt --integers --alphabet 256 --report-json buckets.json
python3 compare_reports.py pi.json buckets.json --baseline pi.json --md compare.md
```

---

## 🧠 Interpretazione rapida delle metriche
* **Chi-square**: più vicino ai dof (M−1) e con varianza attesa → copertura uniforme.
* **Runs Z (parità)**: |Z| ≲ 2 ≈ casuale; molto alto → struttura nell’ordine.
* **Autocorr (lag 1..5)**: |ρ| ≲ 0.05 su dataset ampi → assenza di dipendenza seriale.
* **Compression ratio (zlib)**: più alto → meno struttura facilmente comprimibile rilevata da zlib; va interpretato con le metriche di distribuzione e dipendenza. Per cifre base-10 il limite teorico è ≈ 0.415.
* **N-gram accuracy**: ≈ 1/M se stream imprevedibile.
* **SchurProbe**: z vicino a 0 allinea al caso random-like.

---

## 🧰 Requisiti
* **Python** 3.12+ (raccomandato **3.13**)
* **Pacchetti**: `mpmath` (solo per `make_datasets.py` offline)

Setup tipico:
```bash
python3.13 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
pip install mpmath
```

---

## 📑 Formati di output

### Report JSON (estratto campi principali)
```jsonc
{
  "file": "pi_100k.txt",
  "N": 100000,
  "alphabet": 10,
  "chi_square": 4.0930,
  "runs": {"Z": 0.5646, "p_two_tailed": 0.5724},
  "autocorr": {"lag1": -0.0025, "lag2": 0.0022, "lag3": -0.0027, "lag4": 0.0001, "lag5": 0.0027},
  "compress_ratio": 0.4817,
  "ngram": {"n1": 0.1013, "n2": 0.1026, "n3": 0.0998},
  "schur": {"tested": 5000, "count": 124749, "expected": 125777.42, "z": -2.91, "fraction": 0.0100},
  "source_sha256": "…",
  "notes": "integer_part=true|false, generator=mpmath|http, …"
}
```

Il comparatore produce:
* **stdout** con ranking, severità (`green/yellow/red`) e **AnomalyScore**
* **`--csv`** tabellare
* **`--md`** riassunto Markdown (pronto da committare)

---

## ✅ Stato qualità (autoregolato)

* Validato su:
  * **π** e **e** (100k cifre, offline)
  * Sequenze di **bucket** (M variabili, N ampi)
* Nessun crash noto su input > 100k campioni
* Output **riproducibili** (stesse opzioni ⇒ stessi risultati)

---

## 🔄 Compatibilità / Breaking changes
* Nessuna incompatibilità rispetto ai prototipi precedenti: le opzioni esistenti sono stabili.
* I report JSON sono **backwards-compatible** con la pipeline `compare_reports.py`.

---

## ⚠️ Note e limiti noti
- **Affidabilità χ² locale**: per finestre piccole con λ=N/M < 5 l’interpretazione del χ² va presa con cautela.
- **Ordine vs frequenze**: alcuni test (runs/autocorr/ngram) misurano **struttura dell’ordine**, non solo bias marginale.
- Le metriche non sono un certificato di “randomness crittografica”!

---

## 🙏 Credits

Grazie a **Giancarlo** per l’idea, i dataset e i test incrociati (π, e, Turbo-B).
Il progetto nasce per indagare *struttura vs casualità* in sequenze reali e sintetiche.

---

## 🔖 Tag corrente
`v1.0.0 — Initial stable release`
