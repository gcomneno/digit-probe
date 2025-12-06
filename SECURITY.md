# Security Policy – digit-probe
digit-probe fa parte dell'ecosistema GiadaWare.

## Segreti e configurazione
- Nessuna API key, token o password deve essere committata nella repository.
- I file `.env` e simili devono restare locali e sono ignorati da Git.
- Il file `.env.example` fornisce un modello delle variabili richieste.

## CI/CD
- I workflow GitHub Actions usano permessi minimi (`permissions: contents: read`).
- I job che eseguono build/test su codice esterno non devono accedere a segreti sensibili.
- È attivo un controllo automatico di segreti (`.github/workflows/secret-scan.yml`).

## Plugin, estensioni, AI
- Usare un numero minimo di estensioni IDE / browser quando si lavora sul progetto.
- Installare solo plugin con:
  - repository pubblico,
  - manutenzione recente,
  - numero significativo di utenti.
- Trattare eventuali agent/skills AI che modificano il repo come un runner CI:
  - accesso solo alle directory necessarie,
  - nessuna chiave hard-coded nei file manipolati.

## Social engineering
- Non inserire credenziali seguendo link ricevuti via mail/chat.
- Aprire sempre i servizi esterni digitando manualmente l'URL ufficiale.
- Non eseguire script trovati in issue/commenti senza averli rivisti.
