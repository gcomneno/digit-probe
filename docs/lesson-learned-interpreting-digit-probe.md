# Lesson learned — Interpretare Digit-Probe senza farsi ingannare dalla baseline

**Data:** 30 luglio 2026
**Ambito:** analisi statistica e strutturale di sequenze discrete
**Strumento:** Digit-Probe 1.0.0
**Stato:** esercitazione riproducibile completata

## Sintesi

Una metrica non è significativa in assoluto.

Il suo risultato dipende da almeno tre elementi:

1. che cosa rappresenta ogni simbolo della sequenza;
2. quale comportamento teorico viene assunto come baseline;
3. quali dipendenze sono introdotte dalla codifica o dal processo che produce i dati.

La lezione principale emersa dagli esercizi è:

> Prima di interpretare una deviazione statistica, bisogna verificare che
> l'ipotesi nulla corrisponda davvero alla rappresentazione dei dati.

Una sequenza può essere:

- uniforme nelle frequenze ma completamente prevedibile;
- poco correlata ma fortemente sbilanciata;
- apparentemente anomala soltanto perché viene confrontata con la baseline sbagliata;
- compatibile con un comportamento random-like senza che questo costituisca
  una prova matematica di casualità.

Nessuna singola metrica certifica la casualità.

## Obiettivi dell'esercitazione

Gli esercizi avevano lo scopo di imparare a distinguere:

- distribuzione dei simboli;
- ordine e dipendenze seriali;
- prevedibilità locale;
- ripetitività e comprimibilità;
- gap tra occorrenze;
- struttura additiva;
- significatività statistica;
- artefatti introdotti dalla rappresentazione.

Sono stati costruiti o analizzati sei casi progressivi:

1. sequenza uniforme ma periodica;
2. sequenza pseudo-casuale uniforme;
3. sequenza random-like con forte bias sulla cifra `7`;
4. una singola estrazione Lotto rappresentata come 110 cifre;
5. lo storico Lotto 2023–2026 rappresentato come stream di cifre;
6. lo stesso storico separato in cifre delle decine e delle unità.

---

## Esperimento 1 — Uniforme ma completamente periodica

### Dataset

La sequenza è stata costruita ripetendo mille volte:

```text
0123456789
```

Dimensione complessiva:

```text
10.000 cifre
```

### Risultati principali

| Metrica | Risultato |
|---|---:|
| Occorrenze per cifra | 1.000 ciascuna |
| Chi-square | 0,0000 |
| Z-score per cifra | 0 per tutte |
| Runs test | Z = 99,985; p ≈ 0 |
| Compression ratio | 0,0054 |
| Predictor n=1 | 10% |
| Predictor n=2 | 100% |
| Predictor n=3 | 100% |
| SchurProbe | fraction = 1; z = +10605,54 |

### Interpretazione

Conteggi, chi-square e Z-score descrivono una distribuzione perfettamente
uniforme.

Non descrivono però l'ordine.

La sequenza è totalmente deterministica:

- ogni cifra ricompare esattamente dopo dieci posizioni;
- il contesto permette di prevedere sempre il simbolo successivo;
- la sequenza è quasi interamente comprimibile;
- autocorrelazione, runs test e SchurProbe rilevano una struttura estrema.

### Lesson learned

> Uniformità delle frequenze non significa casualità.

Il chi-square può risultare perfetto anche su una sequenza costruita con un
pattern banale e completamente prevedibile.

---

## Esperimento 2 — Baseline pseudo-casuale uniforme

### Dataset

Sono state generate 10.000 cifre tramite un PRNG con seed fisso:

```text
seed = 20260730
alfabeto = 0..9
```

Il seed fisso rende l'esperimento riproducibile.

### Risultati principali

| Metrica | Risultato |
|---|---:|
| Chi-square | 4,1920 |
| Runs test | Z = 1,040; p = 0,298 |
| Autocorrelazioni lag 1..5 | tra -0,0035 e +0,0076 |
| Compression ratio | 0,5071 |
| Predictor n=1..3 | circa 9–10% |
| SchurProbe | fraction = 0,09997; z = -0,40 |

### Interpretazione

Le frequenze non sono perfette: oscillano naturalmente attorno alle mille
occorrenze attese.

Le altre metriche non rilevano dipendenze forti:

- autocorrelazioni vicine a zero;
- predictor vicino alla probabilità casuale `1/10`;
- compressione compatibile con uno stream random-like;
- SchurProbe vicino alla frazione teorica `1/10`.

### Lesson learned

> In un campione finito, piccole irregolarità sono normali.

Una distribuzione artificialmente perfetta può essere più sospetta di una
distribuzione con modeste fluttuazioni.

---

## Esperimento 3 — Ordine random-like, distribuzione truccata

### Dataset

È stata generata una sequenza di 10.000 cifre nella quale il simbolo `7`
aveva un peso molto maggiore degli altri.

Risultato osservato:

```text
occorrenze della cifra 7 = 3.937
```

### Risultati principali

| Metrica | Risultato |
|---|---:|
| Chi-square | 9588,6120 |
| Z-score della cifra 7 | +92,876 |
| Runs test | Z = 0,283; p = 0,777 |
| Autocorrelazioni lag 1..5 | vicine a zero |
| Compression ratio | 0,4561 |
| Predictor n=1 | 40,7% |
| Predictor n=2 | 40,69% |
| Gap medio della cifra 7 | 2,54 |
| SchurProbe | z = -16,36 |

### Interpretazione

L'ordine non presenta una periodicità evidente, ma la distribuzione è
fortemente sbilanciata.

Il predictor raggiunge circa il 40% non perché abbia imparato una regola
sequenziale, ma perché può ottenere quasi lo stesso risultato predicendo
sempre il simbolo più frequente.

La baseline uniforme del predictor è il 10%, ma la baseline empirica più
onesta è circa il 39,37%, cioè la frequenza del `7`.

Il gap medio conferma il bias:

```text
probabilità del 7 ≈ 0,3937
gap medio atteso ≈ 1 / 0,3937 ≈ 2,54
```

### Lesson learned

> Un predictor sopra la baseline uniforme non implica necessariamente una
> struttura nell'ordine.

Può limitarsi a sfruttare uno sbilanciamento marginale delle frequenze.

Per valutare l'informazione realmente ricavata dal contesto bisogna
confrontare il predictor con almeno due baseline:

- scelta uniforme tra tutti i simboli;
- previsione costante del simbolo più frequente.

---

## Esperimento 4 — Una singola estrazione Lotto come 110 cifre

### Rappresentazione

Una tabella contenente 55 numeri Lotto è stata convertita mantenendo la
larghezza fissa di due cifre:

```text
82 -> 8, 2
03 -> 0, 3
01 -> 0, 1
```

Il dataset risultante contieneva:

```text
55 numeri
110 cifre
alfabeto 0..9
```

### Risultati principali

| Metrica | Risultato |
|---|---:|
| Chi-square | 9,4545 |
| Runs test | Z = 1,549; p = 0,121 |
| Cifra più frequente | 8, con 18 occorrenze |
| Z-score della cifra 8 | +2,111 |
| Compression ratio | 0,6545 |
| Predictor | circa 5–14% |
| SchurProbe | z = -1,18 |

### Interpretazione

Il campione è troppo piccolo per conclusioni robuste.

Con appena 110 cifre:

- una singola previsione cambia sensibilmente la percentuale del predictor;
- l'overhead di zlib altera il rapporto di compressione;
- uno Z-score moderato su una delle dieci cifre può comparire per caso;
- nessuna metrica isolata giustifica una conclusione sulla casualità
  dell'estrazione.

L'esperimento misura soprattutto la distribuzione delle cifre usate per
scrivere i numeri, non la distribuzione dei 55 valori nell'universo `1..90`.

### Lesson learned

> La scelta del simbolo determina la domanda statistica.

Trattare `82` come un simbolo intero oppure come due cifre produce due
esperimenti diversi e risponde a domande diverse.

---

## Esperimento 5 — Storico Lotto 2023–2026 come stream di cifre

### Dataset

Sono stati integrati quattro database SQLite annuali:

| Anno | Estrazioni | Numeri |
|---|---:|---:|
| 2023 | 182 | 10.010 |
| 2024 | 209 | 11.495 |
| 2025 | 208 | 11.440 |
| 2026, fino al 28 luglio | 120 | 6.600 |
| **Totale** | **719** | **39.545** |

Ogni numero è stato rappresentato con due cifre, producendo:

```text
79.090 cifre
```

L'ordine usato è stato:

1. data crescente;
2. ruota nell'ordine ufficiale;
3. posizione da 1 a 5.

### Risultati con baseline uniforme ingenua

| Metrica | Risultato |
|---|---:|
| Chi-square | 1743,3026 |
| Z-score della cifra 9 | -39,389 |
| Runs test | Z = 4,884; p ≈ 0 |
| Autocorrelazione lag 1 | -0,0418 |
| Autocorrelazioni lag 2..5 | circa zero |
| Compression ratio | 0,4827 |
| Predictor n=1..3 | circa 10,4–10,7% |
| SchurProbe | z = -1,02 |

Il chi-square sembrava indicare un'anomalia enorme.

Era invece un falso allarme causato dalla baseline.

### Distribuzione teorica corretta delle cifre in `01..90`

Nell'intero universo dei novanta numeri:

| Cifra | Occorrenze teoriche |
|---|---:|
| 0 | 18 |
| 1..8 | 19 ciascuna |
| 9 | 10 |

La cifra `9` è meno frequente per costruzione, perché esistono:

```text
09, 19, 29, ..., 89, 90
```

ma non esistono `91..99`.

Su 39.545 numeri, i conteggi attesi corretti sono circa:

| Cifra | Conteggio atteso |
|---|---:|
| 0 | 7909,00 |
| 1..8 | 8348,39 ciascuna |
| 9 | 4393,89 |

Ricalcolando esternamente il chi-square con questa baseline:

```text
chi-square ≈ 7,6207
gradi di libertà = 9
p-value ≈ 0,5728
```

Non emerge quindi alcuna anomalia evidente nella distribuzione delle cifre
rispetto al modello corretto.

### Artefatto decina-unità

Lo stream completo alterna sistematicamente:

```text
decina, unità, decina, unità, ...
```

Le due posizioni non hanno la stessa distribuzione teorica.

Questo può influenzare:

- autocorrelazione al lag 1;
- runs test pari/dispari;
- frequenze aggregate;
- qualsiasi test che assuma simboli identicamente distribuiti.

### Lesson learned

> Un test corretto applicato con un'ipotesi nulla sbagliata produce una
> conclusione sbagliata.

Il valore numerico della metrica può essere calcolato perfettamente e,
nonostante ciò, essere privo del significato attribuito dall'analista.

---

## Esperimento 6 — Separazione tra decine e unità

Lo storico è stato diviso in due sequenze da 39.545 cifre:

- stream delle decine;
- stream delle unità.

### Unità

Nei numeri `01..90`, ogni cifra `0..9` compare esattamente nove volte come
unità.

La baseline uniforme di Digit-Probe è quindi appropriata.

| Metrica | Risultato |
|---|---:|
| Chi-square | 4,4068 |
| p-value chi-square | circa 0,8827 |
| Z-score per cifra | tra circa -1,04 e +1,28 |
| Runs test | Z = 2,060; p = 0,039 |
| Autocorrelazioni | vicine a zero |
| Compression ratio | 0,4978 |
| Predictor | circa 9,2–10,3% |
| SchurProbe | z = -0,53 |

La distribuzione delle unità è fortemente compatibile con l'uniformità.

Il `p = 0,039` del runs test è un segnale debole, non una prova di anomalia.

Deve essere valutato considerando:

- il numero complessivo di metriche osservate;
- le dipendenze introdotte dalle cinquine senza ripetizione;
- la stabilità su anni, ruote o finestre temporali separate;
- un'eventuale baseline Monte Carlo che rispetti le regole reali del Lotto.

### Decine

La distribuzione teorica delle decine non è uniforme:

| Decina | Probabilità teorica |
|---|---:|
| 0 | 9/90 |
| 1..8 | 10/90 ciascuna |
| 9 | 1/90 |

Il chi-square uniforme di Digit-Probe produce:

```text
chi-square = 3505,9923
```

ma il valore è incompatibile con l'ipotesi nulla reale.

Con la baseline corretta:

```text
chi-square ≈ 8,8845
gradi di libertà = 9
p-value ≈ 0,4480
```

Anche le decine risultano compatibili con la loro distribuzione teorica.

### Lesson learned

> Separare componenti con distribuzioni diverse può trasformare un falso
> allarme in un risultato interpretabile.

---

## Relazione con `lotto-digit-coverage-dynamics`

Il progetto `lotto-digit-coverage-dynamics` considera correttamente entrambe
le cifre dei numeri rappresentati come `01..90`.

La sua domanda non è:

> Le cifre sono uniformemente distribuite?

La sua domanda è:

> Come evolve la copertura delle cifre decimali osservate nei numeri
> `01..90`?

L'asimmetria tra le cifre, in particolare la rarità del `9`, è parte
strutturale del modello e viene incorporata nel kernel combinatorio esatto.

Non sarebbe corretto eliminare le decine dal modello canonico.

Analizzare soltanto le unità sarebbe un esperimento secondario diverso,
utile come controllo simmetrico ma non equivalente alla copertura decimale
completa.

La decisione presa durante l'esercitazione è stata:

- non modificare Digit-Probe;
- non modificare il modello di `lotto-digit-coverage-dynamics`;
- mantenere esplicita la responsabilità dell'analista nella scelta della
  rappresentazione e della baseline;
- usare trasformazioni o calcoli esterni quando l'ipotesi uniforme standard
  non è appropriata.

---

## Come leggere le principali metriche

### Conteggi, chi-square e Z-score

Rispondono principalmente alla domanda:

> I simboli compaiono con le frequenze previste dalla baseline?

Non rispondono alla domanda:

> In quale ordine compaiono?

Il chi-square richiede conteggi attesi coerenti con il modello generatore.

Uno Z-score per simbolo identifica quale categoria contribuisce allo
sbilanciamento, ma deve essere interpretato considerando il numero di
categorie osservate.

### Runs test

Verifica se una classificazione binaria, in Digit-Probe pari/dispari, alterna
troppo o troppo poco rispetto all'ipotesi nulla.

Un p-value piccolo:

- non indica la probabilità che i dati siano casuali;
- non identifica la causa dell'anomalia;
- non prova da solo che il processo generatore sia difettoso.

### Gap medio

Per un simbolo con probabilità approssimativa `p`, il gap medio atteso è:

```text
gap medio ≈ 1 / p
```

Un simbolo molto frequente ha quindi gap medio basso.

Il gap descrive la ricorrenza, ma non distingue automaticamente tra bias
marginale e struttura temporale.

### Autocorrelazione

Misura dipendenze lineari tra valori separati da un determinato lag.

Valori vicini a zero non garantiscono casualità:

- può esistere un forte bias nelle frequenze;
- possono esistere dipendenze non lineari;
- la struttura può apparire a lag non analizzati;
- la codifica può mescolare sottosequenze differenti.

### Compression ratio

È un proxy pratico della ripetitività.

- valori molto bassi suggeriscono pattern o ridondanza;
- valori random-like indicano assenza di ripetizioni facilmente comprimibili;
- sui dataset piccoli l'overhead del formato compresso pesa molto.

Non è un test formale di casualità.

### N-gram predictor

Misura quanto il contesto precedente aiuta a prevedere il simbolo successivo.

Deve essere confrontato con:

- la baseline uniforme `1/M`;
- la frequenza del simbolo più comune;
- eventualmente una baseline ottenuta da simulazioni coerenti con il
  processo reale.

Un risultato elevato può dipendere da:

- periodicità;
- transizioni condizionate;
- dipendenze Markoviane;
- semplice sbilanciamento delle frequenze.

### SchurProbe

Cerca una specifica struttura additiva modulo `M`.

- `z` vicino a zero è compatibile con la baseline del test;
- valori estremi indicano una relazione additiva forte;
- un risultato tranquillo non esclude strutture di altro tipo.

---

## Errori interpretativi osservati

Durante l'esercitazione sono emersi alcuni errori utili da conservare.

### Errore 1 — Confondere uniformità e casualità

Correzione:

> La distribuzione marginale non descrive l'ordine.

### Errore 2 — Considerare ogni predictor sopra `1/M` come intelligente

Correzione:

> Prima confrontarlo con la strategia che predice sempre il simbolo più
> frequente.

### Errore 3 — Usare l'autocorrelazione come certificato globale

Correzione:

> L'autocorrelazione misura una classe limitata di dipendenze e non rileva
> direttamente un bias marginale.

### Errore 4 — Interpretare `p < 0,05` come prova conclusiva

Correzione:

> Un singolo p-value piccolo può essere un falso positivo, soprattutto dopo
> molti test.

### Errore 5 — Ignorare la rappresentazione

Correzione:

> Interi, cifre, decine e unità sono simbolizzazioni differenti e rispondono
> a domande differenti.

### Errore 6 — Applicare la baseline uniforme a categorie non uniformi

Correzione:

> Calcolare prima le probabilità teoriche reali o costruire una baseline
> simulata coerente.

---

## Workflow operativo riutilizzabile

Prima di analizzare un nuovo dataset:

### 1. Definire il simbolo

Chiedersi:

- ogni carattere è un simbolo?
- ogni numero è un simbolo?
- gli zeri iniziali hanno significato?
- esistono posizioni con distribuzioni differenti?

### 2. Definire l'ipotesi nulla

Stabilire esplicitamente:

- quali simboli sono possibili;
- con quali probabilità;
- se le osservazioni sono indipendenti;
- quali vincoli esistono nel processo generatore.

### 3. Verificare la baseline di ogni metrica

Non assumere automaticamente:

```text
probabilità = 1 / numero_di_simboli
```

L'uniformità deve derivare dal modello, non dalla comodità.

### 4. Usare metriche complementari

Almeno una metrica per ciascun livello:

- distribuzione: chi-square e Z-score;
- ordine: runs test e autocorrelazione;
- prevedibilità: predictor;
- ripetitività: compressione;
- ricorrenza: gap;
- struttura additiva: SchurProbe.

### 5. Costruire una baseline comparabile

Preferire, quando possibile:

- PRNG con seed fisso;
- simulazione Monte Carlo del processo reale;
- dataset sintetico con una sola proprietà alterata;
- confronto con sottocampioni temporali o categoriali.

### 6. Controllare la dimensione del campione

Su campioni piccoli:

- percentuali e Z-score oscillano maggiormente;
- la compressione è dominata dall'overhead;
- il predictor ha pochi casi di test;
- un valore estremo isolato è meno stabile.

### 7. Cercare replicabilità

Un segnale è più credibile se:

- ricompare su anni distinti;
- ricompare su ruote distinte;
- è stabile su finestre temporali;
- sopravvive a una baseline Monte Carlo corretta.

### 8. Formulare conclusioni limitate

Scrivere:

> Non emergono strutture rilevabili con queste metriche e questa baseline.

Evitare:

> La sequenza è sicuramente casuale.

---

## Modalità interi e normalizzazione

Quando l'universo logico è `1..M` ma Digit-Probe usa simboli modulo `M`, è
prudente normalizzare:

```text
simbolo = valore - 1
```

Per il Lotto:

```text
1  -> 0
2  -> 1
...
90 -> 89
```

In questo modo i novanta valori occupano esattamente l'alfabeto `0..89`.

Senza normalizzazione:

```text
90 % 90 = 0
```

e il valore `90` viene rappresentato dallo stesso residuo dello zero.

---

## File prodotti durante l'esercitazione

I dataset e i report sono stati salvati sotto `out/exercises/`:

```text
01-periodic-digits.txt
01-periodic-digits.json
02-random-digits.txt
02-random-digits.json
03-biased-seven.txt
03-biased-seven.json
04-lotto-110-digits.txt
04-lotto-110-digits.json
05-lotto-history-2023-2026-digits.txt
05-lotto-history-2023-2026-digits.json
05-lotto-history-2023-2026-manifest.tsv
06-lotto-history-tens.txt
06-lotto-history-tens.json
06-lotto-history-units.txt
06-lotto-history-units.json
```

Questi file sono artefatti di lavoro e non devono necessariamente essere
versionati.

---

## Conclusione finale

Digit-Probe è efficace nel mostrare proprietà differenti della stessa
sequenza, purché i risultati vengano letti nel contesto corretto.

Gli esercizi hanno mostrato quattro casi fondamentali:

1. distribuzione uniforme con ordine totalmente prevedibile;
2. distribuzione uniforme e comportamento random-like;
3. ordine random-like con forte bias marginale;
4. falso allarme causato da una baseline incompatibile con la codifica.

La regola da conservare è:

> Metrica, rappresentazione e baseline formano un unico contratto
> interpretativo. Se uno dei tre elementi è sbagliato, anche una misura
> calcolata correttamente può raccontare una storia falsa.
