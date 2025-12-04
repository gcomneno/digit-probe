# Analisi comparata delle cifre di "π, e" con `digit-probe`

Questo documento riassume i risultati dell’analisi statistico–strutturale effettuata con `digit-probe` sulle prime **100.000 cifre decimali** di:
- π (`pi_100k.txt` → `pi.json`)
- e (`e_100k.txt` → `e.json`)

Entrambi i dataset sono stati generati in modalità **offline** tramite `mpmath`, considerando **solo le cifre della mantissa** (la parte intera è stata scartata).

L’obiettivo non è “dimostrare” nulla di profondo su π o e (problemi aperti di teoria dei numeri restano tali), ma verificare se, con una batteria di test ragionevole, emergono segnali di **struttura sfruttabile** o se il comportamento osservato è compatibile con una sequenza **random-like** su alfabeto decimale.

---

## 1. Setup e modalità di analisi

- Modalità: `digits`
- Lunghezza: `N = 100000`
- Alfabeto: `0..9` (M = 10)
- File:
  - `pi_100k.txt` → `pi.json`
  - `e_100k.txt`  → `e.json`

Per ciascuna sequenza `digit-probe` ha calcolato:

- **Distribuzione** per cifra, **chi-square**, **z-score**
- **Runs test** (pari vs dispari)
- **Gaps** (conteggio e gap medio per simbolo)
- **Autocorrelazione** (lag 1..5)
- **Compression ratio (zlib)** sul testo delle cifre
- **N-gram predictor** (n = 1,2,3) con split 80/20
- **SchurProbe**:
  - si considerano i primi `R = 5000` simboli
  - si testano tutte le coppie `i < j` con `k = (i + j) mod R`
  - condizione: `(seq[i] + seq[j]) % 10 == seq[k]`
  - atteso casuale: ~1 tripletta “buona” su 10
    → `E = C(R,2) / 10`, varianza binomiale `N p (1-p)`, z-score standard

---

## 2. Risultati sintetici

### 2.1 Tabella riassuntiva

| metrica              | π (`pi.json`)                       | e (`e.json`)                         |
|----------------------|-------------------------------------|--------------------------------------|
| N                    | 100.000                             | 100.000                              |
| alfabeto             | 10                                  | 10                                   |
| chi-square           | 4.093                               | 17.682                               |
| compress ratio (zlib)| 0.48173                             | 0.48188                              |
| runs Z (pari/dispari)| 0.5646  (p ≈ 0.57)                  | 0.3232 (p ≈ 0.75)                    |
| max \|autocorr\|     | ≈ 0.0027                            | ≈ 0.0022                             |
| n-gram best acc.     | ~10.26% (n=2)                       | ~10.10% (n=2)                        |
| Schur triples        | 12.497.500                          | 12.497.500                           |
| Schur count          | 1.250.371                           | 1.249.813                            |
| Schur expected       | 1.249.750                           | 1.249.750                            |
| Schur fraction       | ≈ 0,1000                            | ≈ 0,1000                             |
| Schur z-score        | ≈ 0,586                             | ≈ 0,059                              |

---

## 3. Analisi per metrica

### 3.1 Distribuzione e chi-square
Entrambe le sequenze mostrano conteggi per cifra molto vicini all’atteso teorico (10.000 ciascuna):
- π: chi² ≈ **4,09** (molto basso per 9 d.o.f., ma perfettamente plausibile)
- e: chi² ≈ **17,68** (leggermente più alto, ma ancora in range normale)

Gli z-score per singola cifra restano tutti nell’intervallo ±3σ, quindi:
> **Conclusione:** nessuna cifra “dominante” o “mancante” in modo sospetto per π o e.
> Distribuzione compatibile con un modello uniforme iid su 0..9.

---

### 3.2 Runs test (pari/dispari)

- π: Z ≈ 0,56, p ≈ 0,57
- e: Z ≈ 0,32, p ≈ 0,75

In entrambi i casi il p-value è ben lontano da soglie tipiche di allarme (0,05 / 0,01).

> **Conclusione:** la sequenza pari/dispari non mostra pattern evidenti; l’alternanza è compatibile con casualità.

---

### 3.3 Gaps (distanza tra occorrenze)

Per ciascun simbolo:
- numero di gap ≈ numero di occorrenze
- gap medio ≈ 10 (tra ~9,74 e ~10,15 in tutti i casi)

Per una sorgente iid uniforme su 10 simboli, il gap medio atteso è esattamente 10.

> **Conclusione:** la “spaziatura” media tra ricorrenze dei digit è in linea con l’ipotesi di indipendenza e uniformità, sia per π che per e.

---

### 3.4 Autocorrelazione

Primi 5 lag:
- π: \|ρ(lag)\| ≤ ~0,0027
- e: \|ρ(lag)\| ≤ ~0,0022

Per N=100.000 questi valori sono molto piccoli; non appaiono picchi nettamente fuori scala.

> **Conclusione:** nessuna correlazione lineare evidente a corto raggio.
> Le cifre successive non “si inseguono” con pattern banali rilevabili dall’autocorrelazione.

---

### 3.5 Compression ratio (zlib)

- π: 0,48173
- e: 0,48188

Il limite teorico per una sorgente perfettamente casuale su alfabeto 10 è ~0,415 (entropia in bit per simbolo / 8), ma:

- su 100k cifre, un rapporto attorno a 0,47–0,50 è del tutto realistico
- valori **molto più bassi** (<0,44) sarebbero indicativi di forte struttura/ripetizione

> **Conclusione:** le sequenze non risultano “facilmente comprimibili” oltre quanto ci si aspetterebbe da un sorgente ad alta entropia.
> Nessun pattern macroscopico sfruttato da zlib.

---

### 3.6 N-gram predictor (n=1..3)

Accuracy sul set di test (20% finale):

- π:
  - n=1: ~10,0%
  - n=2: ~10,26%
  - n=3: ~9,98%
- e:
  - n=1: ~10,0%
  - n=2: ~10,10%
  - n=3: ~9,84%

Baseline “pura” (indovinare a caso una cifra su 10) = **10%**.

> **Conclusione:** i modelli n-gram non riescono a sfruttare alcuna struttura ripetitiva stabile;
> il vantaggio rispetto al “lancio di una moneta a 10 facce” è trascurabile.
> In pratica: **non imparano nulla di utile**.

---

### 3.7 SchurProbe (test additivo mod 10)

Per entrambi i casi:
- si considerano i primi `R = 5000` digit
- si testano tutte le coppie `i<j`:
  - `triples = C(5000,2) = 12.497.500`
- condizione:
  `(seq[i] + seq[j]) % 10 == seq[(i + j) % 5000]`
- atteso con modello casuale:
  `E = triples / 10 = 1.249.750` (~10% delle triple)

Risultati:
- π:
  - `count ≈ 1.250.371`
  - `expected = 1.249.750`
  - `fraction ≈ 0,1000497`
  - `z ≈ 0,586`
- e:
  - `count ≈ 1.249.813`
  - `expected = 1.249.750`
  - `fraction ≈ 0,1000050`
  - `z ≈ 0,059`

Entrambi i valori di z-score sono **molto vicini a 0**, con e addirittura più “aderente” all’atteso di π.

> **Conclusione:** anche sotto il test additivo “alla Schur” (che cerca struttura del tipo
> “somma di due posizioni ricade spesso in un terzo indice con la stessa somma mod 10”)
> **π ed e si comportano come sequenze casuali**.
> Non emerge alcuna struttura additiva “sospetta” nella finestra di 5000 cifre.

---

## 4. Conclusioni complessive

Su un blocco di **100.000 cifre**:

- π (`pi.json`) e e (`e.json`) risultano:
  - **distribuiti in modo equilibrato** sulle 10 cifre
  - privi di pattern evidenti in termini di:
    - alternanza pari/dispari
    - distanza tra ricorrenze dei simboli
    - autocorrelazione a lag corti
  - **poco comprimibili** (come ci si aspetta da una sorgente ad alta entropia)
  - **non predicibili** da modelli n-gram banali (accuracy ~10%)
  - **coerenti con la casualità** anche rispetto al test **SchurProbe**.

In altre parole:
> All’interno della sensibilità di `digit-probe` e della finestra analizzata,
> **π ed e si comportano come ottimi generatori pseudo–casuali decimali**.

Questo non dice nulla di definitivo sul loro status di numeri normali (problema aperto),
ma fornisce una base pratica: **i due dataset sono ottime baseline “random-like”** per confrontare:
- sequenze provenienti da generatori pseudo–casuali,
- bucket generati da sistemi come Turbo-Bucketizer,
- sequenze sospette, gradienti, trappole artificiali, ecc.

---

## 5. Uso come baseline nel progetto

Nel contesto di `digit-probe`, i file:
- `pi.json`
- `e.json`

possono essere generati ed usati come:
- **riferimento di “profilo sano”** nelle suite di test (`make selftest`, `make test-basic`, ecc.)
- base per il confronto tramite `compare_reports.py`, ad esempio:

```bash
python3 src/compare_reports.py pi.json e.json --baseline pi.json --md compare_pi_e.md

=== COMPARISON (sorted by AnomalyScore, |Schur z|, chi², max|ac|) ===
file   | N      | severity| score  | chi²   |  Δχ²   | comp   | Δcomp  | runsZ  | ΔrunsZ | max|ac |        | Δmax|ac|        | ngram  | Δngram |
pi.json| 100000 | green   | 0.0000 | 4.0930 | 0.0000 | 0.4817 | 0.0000 | 0.5646 | 0.0000 | 0.0027 | 0.0000 | 0.1026 | 0.0000 | 0.5855 | 0.0000 |
e.json | 100000 | green   | 0.6176 | 17.6820| 13.5890| 0.4819 | 0.0001 | 0.3232 | -0.2414| 0.0022 | -0.0005| 0.1010 | -0.0017| 0.0594 | -0.5261|
```

In questo modo, qualsiasi altra sequenza analizzata può essere confrontata numericamente con questi due casi, sfruttando:
- chi-square,
- max |autocorr|,
- anomalie nei runs,
- Schur z-score,
- AnomalyScore aggregato.

Se una sequenza “stona” visibilmente rispetto a π/e su più di una metrica,
`digit-probe` ha individuato qualcosa che merita di essere guardato con più attenzione.
