## Funzionalità del Dominio Medico

- **Generazione di Quiz**: Creazione intelligente di quiz dalla documentazione di fisioterapia
- **Estrazione di Entità Mediche**: Strutture anatomiche, condizioni patologiche, trattamenti
- **Ragionamento Clinico**: Generazione e validazione di domande basate sull'evidenza
- **Lingua Italiana**: Pieno supporto per la formazione medica in italiano
- **Ricerca Ibrida**: Similarità semantica + attraversamento del grafo di conoscenza medico
- **Analisi Didattica**: Tracciamento dei progressi e ottimizzazione dell'apprendimento# RAG Medico con Knowledge Graph per la Formazione in Fisioterapia

Sistema intelligente di generazione di quiz per la formazione in fisioterapia che utilizza un'architettura RAG ibrida. Combina la ricerca vettoriale con i grafi di conoscenza per creare valutazioni didattiche contestualmente pertinenti e pedagogicamente valide dalla documentazione medica.

Realizzato con:

- Pydantic AI per il Framework dell'Agente AI Medico
- Graphiti per il Knowledge Graph Medico
- Postgres con PGVector per il Database Vettoriale
- Neo4j per il Motore del Knowledge Graph (Graphiti si connette a questo)
- FastAPI per l'API dell'Agente Medico
- Supporto alla Lingua Italiana per i Contenuti Didattici

## Panoramica

Questo sistema include quattro componenti principali:

1.  **Pipeline di Ingestione di Documenti Medici**: Elabora la documentazione di fisioterapia utilizzando il chunking semantico e costruisce sia gli embedding vettoriali sia le relazioni del grafo di conoscenza medico.
2.  **Interfaccia Agente AI Medico**: Un agente conversazionale basato su Pydantic AI in grado di cercare contenuti medici e generare quiz didattici.
3.  **Sistema di Generazione di Quiz**: Crea quiz intelligenti basati sulla documentazione medica con ragionamento clinico e validazione basata sull'evidenza.
4.  **API di Streaming**: Backend FastAPI con risposte in streaming in tempo reale e capacità di ricerca medica complete.

## Prerequisiti

-   Python 3.11 o superiore
-   Database PostgreSQL (come Neon)
-   Database Neo4j (per il knowledge graph)
-   Chiave API di un provider LLM (OpenAI, Ollama, Gemini, ecc.)

## Installazione

### 1. Impostare un ambiente virtuale

```bash
# Crea e attiva l'ambiente virtuale
python -m venv venv       # python3 su Linux
source venv/bin/activate  # Su Linux/macOS
# oppure
venv\Scripts\activate     # Su Windows
```

### 2. Installare le dipendenze

```bash
pip install -r requirements.txt
```

### 3. Impostare le tabelle richieste in Postgres

Esegui l'SQL in `sql/schema.sql` per creare tutte le tabelle, gli indici e le funzioni necessarie.

Assicurati di modificare le dimensioni degli embedding alle righe 31, 67 e 100 in base al tuo modello di embedding. `text-embedding-3-small` di OpenAI è 1536 e `nomic-embed-text` di Ollama è 768 dimensioni, come riferimento.

Nota che questo script eliminerà tutte le tabelle prima di crearle/ricrearle!

### 4. Impostare Neo4j

Hai un paio di opzioni facili per impostare Neo4j:

#### Opzione A: Usare Local-AI-Packaged (Setup semplificato - Raccomandato)

1.  Clona il repository: `git clone https://github.com/coleam00/local-ai-packaged`
2.  Segui le istruzioni di installazione per impostare Neo4j tramite il pacchetto
3.  Nota il nome utente e la password che imposti in `.env` e l'URI sarà `bolt://localhost:7687`

#### Opzione B: Usare Neo4j Desktop

1.  Scarica e installa [Neo4j Desktop](https://neo4j.com/download/)
2.  Crea un nuovo progetto e aggiungi un DBMS locale
3.  Avvia il DBMS e imposta una password
4.  Nota i dettagli di connessione (URI, nome utente, password)

### 5. Configurare le variabili d'ambiente

Crea un file `.env` nella root del progetto:

```bash
# Configurazione Database (esempio stringa di connessione Neon)
DATABASE_URL=postgresql://username:password@ep-example-12345.us-east-2.aws.neon.tech/neondb

# Configurazione Neo4j  
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Configurazione Provider LLM (scegline uno)
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-api-key
LLM_CHOICE=gpt-4.1-mini

# Configurazione Embedding
EMBEDDING_PROVIDER=openai
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=sk-your-api-key
EMBEDDING_MODEL=text-embedding-3-small

# Configurazione Ingestione
INGESTION_LLM_CHOICE=gpt-4.1-nano  # Modello più veloce per l'elaborazione

# Configurazione Applicazione
APP_ENV=development
LOG_LEVEL=INFO
APP_PORT=8058
```

Per altri provider LLM:

```bash
# Ollama (Locale)
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_CHOICE=qwen2.5:14b-instruct

# OpenRouter
LLM_PROVIDER=openrouter
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=your-openrouter-key
LLM_CHOICE=anthropic/claude-3-5-sonnet

# Gemini
LLM_PROVIDER=gemini
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta
LLM_API_KEY=your-gemini-key
LLM_CHOICE=gemini-2.5-flash
```

## Avvio Rapido

### 1. Prepara i tuoi documenti

Aggiungi i tuoi documenti alla cartella `documents/` (supporta Markdown, PDF e DOCX):

```bash
mkdir -p documents
# Aggiungi i tuoi file in uno dei formati supportati:
# - Markdown: documents/anatomia_lombare.md
# - PDF: documents/manuale_fisioterapia.pdf  
# - Word: documents/protocolli_riabilitazione.docx
# - Testo: documents/linee_guida.txt
```

**Formati supportati:**
- ✅ **Markdown** (`.md`, `.markdown`) - Con parsing di intestazioni e struttura
- ✅ **PDF** (`.pdf`) - Con estrazione intelligente del testo
- ✅ **Word DOCX** (`.docx`) - Con preservazione di formattazione e tabelle
- ✅ **Testo semplice** (`.txt`) - Per documenti non strutturati

Questo include 21 documenti dettagliati sulle principali aziende tecnologiche e le loro iniziative AI. Tieni presente che l'elaborazione di tutti questi file nel knowledge graph richiederà molto tempo (potenzialmente più di 30 minuti) a causa della complessità computazionale dell'estrazione di entità e della costruzione di relazioni.

### 2. Esegui l'ingestione dei documenti

**Importante**: devi prima eseguire l'ingestione per popolare i database prima che l'agente possa fornire risposte significative.

```bash
# Ingestione base con chunking semantico
python -m ingestion.ingest

# Pulisci i dati esistenti e re-ingerisci tutto
python -m ingestion.ingest --clean

# Impostazioni personalizzate per un'elaborazione più rapida (senza knowledge graph)
python -m ingestion.ingest --chunk-size 800 --no-semantic --verbose
```

Il processo di ingestione:

-   Analizzerà e dividerà semanticamente i tuoi documenti
-   Genererà embedding per la ricerca vettoriale
-   Estrarrà entità e relazioni per il knowledge graph
-   Salverà tutto in PostgreSQL e Neo4j

NOTA che questo può richiedere un po' di tempo perché i knowledge graph sono molto costosi dal punto di vista computazionale!

### 3. Configura il comportamento dell'agente (Opzionale)

Prima di avviare il server API, puoi personalizzare quando l'agente utilizza strumenti diversi modificando il prompt di sistema in `agent/prompts.py`. Il prompt di sistema controlla:

-   Quando usare la ricerca vettoriale rispetto alla ricerca nel knowledge graph
-   Come combinare i risultati da fonti diverse
-   La strategia di ragionamento dell'agente per la selezione degli strumenti

### 4. Avvia il server API (Terminale 1)

```bash
# Avvia il server FastAPI
python -m agent.api

# Il server sarà disponibile su http://localhost:8058
```

### 5. Usa l'interfaccia a riga di comando (Terminale 2)

La CLI fornisce un modo interattivo per chattare con l'agente e vedere quali strumenti utilizza per ogni query.

```bash
# Avvia la CLI in un terminale separato dall'API (si connette all'API predefinita su http://localhost:8058)
python cli.py

# Connettiti a un URL diverso
python cli.py --url http://localhost:8058

# Connettiti a una porta specifica
python cli.py --port 8080
```

#### Funzionalità della CLI

-   **Risposte in streaming in tempo reale** - Vedi la risposta dell'agente mentre viene generata
-   **Visibilità sull'uso degli strumenti** - Capisci quali strumenti ha usato l'agente:
    -   `vector_search` - Ricerca di similarità semantica
    -   `graph_search` - Query sul knowledge graph
    -   `hybrid_search` - Approccio di ricerca combinato
-   **Gestione della sessione** - Mantiene il contesto della conversazione
-   **Output con codice colore** - Risposte e informazioni sugli strumenti facili da leggere

#### Esempio di sessione CLI

```
🤖 Agentic RAG with Knowledge Graph CLI
============================================================
Connesso a: http://localhost:8058

Tu: Quali sono le iniziative AI di Microsoft?

🤖 Assistente:
Microsoft ha diverse importanti iniziative AI tra cui...

🛠 Strumenti utilizzati:
  1. vector_search (query='Iniziative AI di Microsoft', limit=10)
  2. graph_search (query='Progetti AI di Microsoft')

────────────────────────────────────────────────────────────

Tu: Come è collegata Microsoft a OpenAI?

🤖 Assistente:
Microsoft ha una significativa partnership strategica con OpenAI...

🛠 Strumenti utilizzati:
  1. hybrid_search (query='Partnership Microsoft OpenAI', limit=10)
  2. get_entity_relationships (entity='Microsoft')
```

#### Comandi CLI

-   `help` - Mostra i comandi disponibili
-   `health` - Controlla lo stato della connessione API
-   `clear` - Pulisce la sessione corrente
-   `exit` o `quit` - Esce dalla CLI

### 6. Testa il sistema

#### Controllo dello stato

```bash
curl http://localhost:8058/health
```

#### Chatta con l'agente (non-streaming)

```bash
curl -X POST "http://localhost:8058/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quali sono le principali iniziative AI di Google?"
  }'
```

#### Chat in streaming

```bash
curl -X POST "http://localhost:8058/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Confronta le strategie AI di Microsoft e Google",
  }'
```

## Come funziona

### Il potere del RAG Ibrido + Knowledge Graph

Questo sistema combina il meglio di entrambi i mondi:

**Database Vettoriale (PostgreSQL + pgvector)**:

-   Ricerca di similarità semantica tra i chunk di documenti
-   Recupero rapido di informazioni contestualmente pertinenti
-   Eccellente per trovare documenti su argomenti simili

**Knowledge Graph (Neo4j + Graphiti)**:

-   Relazioni temporali tra entità (aziende, persone, tecnologie)
-   Attraversamento del grafo per scoprire connessioni
-   Perfetto per comprendere partnership, acquisizioni ed evoluzione nel tempo

**Agente Intelligente**:

-   Sceglie automaticamente la migliore strategia di ricerca
-   Combina i risultati da entrambi i database
-   Fornisce risposte consapevoli del contesto con citazioni delle fonti

### Query di esempio

Il sistema eccelle nelle query che beneficiano sia della ricerca semantica che della comprensione delle relazioni:

-   **Domande Semantiche**: "A quale ricerca AI sta lavorando Google?"
    -   Usa la ricerca vettoriale per trovare chunk di documenti pertinenti sulla ricerca AI di Google

-   **Domande sulle Relazioni**: "Come sono collegate Microsoft e OpenAI?"
    -   Usa il knowledge graph untuk per attraversare relazioni e partnership

-   **Domande Temporali**: "Mostrami la timeline degli annunci AI di Meta"
    -   Sfrutta le capacità temporali di Graphiti per tracciare i cambiamenti nel tempo

-   **Analisi Complesse**: "Confronta le strategie AI delle aziende FAANG"
    -   Combina la ricerca vettoriale per i documenti di strategia con l'attraversamento del grafo per l'analisi competitiva

### Perché questa architettura funziona così bene

1.  **Punti di Forza Complementari**: La ricerca vettoriale trova contenuti semanticamente simili mentre i knowledge graph rivelano connessioni nascoste

2.  **Intelligenza Temporale**: Graphiti traccia come i fatti cambiano nel tempo, perfetto per il panorama AI in rapida evoluzione

3.  **Supporto Flessibile per LLM**: Passa da OpenAI, Ollama, OpenRouter o Gemini in base alle tue esigenze

4.  **Pronto per la Produzione**: Test completi, gestione degli errori e monitoraggio

## Documentazione API

Visita http://localhost:8058/docs per la documentazione API interattiva una volta che il server è in esecuzione.

## Funzionalità Chiave

-   **Ricerca Ibrida**: Combina senza soluzione di continuità la similarità vettoriale e l'attraversamento del grafo
-   **Conoscenza Temporale**: Traccia come le informazioni cambiano nel tempo
-   **Risposte in Streaming**: Risposte AI in tempo reale con Server-Sent Events
-   **Provider Flessibili**: Supporto per più provider di LLM e di embedding
-   **Chunking Semantico**: Suddivisione intelligente dei documenti utilizzando l'analisi LLM
-   **Pronto per la Produzione**: Test completi, logging e gestione degli errori

## Struttura del Progetto

```
agentic-rag-knowledge-graph/
├── agent/                  # Agente AI e API
│   ├── agent.py           # Agente Pydantic AI principale
│   ├── api.py             # Applicazione FastAPI
│   ├── providers.py       # Astrazione del provider LLM
│   └── models.py          # Modelli di dati
├── ingestion/             # Elaborazione documenti
│   ├── ingest.py         # Pipeline di ingestione principale
│   ├── chunker.py        # Chunking semantico
│   └── embedder.py       # Generazione di embedding
├── sql/                   # Schema del database
├── documents/             # I tuoi file markdown
└── tests/                # Suite di test completa
```

## Esecuzione dei Test

```bash
# Esegui tutti i test
pytest

# Esegui con la copertura
pytest --cov=agent --cov=ingestion --cov-report=html

# Esegui categorie di test specifiche
pytest tests/agent/
pytest tests/ingestion/
```

## Risoluzione dei problemi

### Problemi Comuni

**Connessione al Database**: Assicurati che il tuo `DATABASE_URL` sia corretto e che il database sia accessibile

```bash
# Testa la tua connessione
psql -d "$DATABASE_URL" -c "SELECT 1;"
```

**Connessione a Neo4j**: Verifica che la tua istanza Neo4j sia in esecuzione e che le credenziali siano corrette

```bash
# Controlla se Neo4j è accessibile (modifica l'URL se necessario)
curl -u neo4j:password http://localhost:7474/db/data/
```

**Nessun risultato dall'Agente**: Assicurati di aver eseguito prima la pipeline di ingestione

```bash
python -m ingestion.ingest --verbose
```

**Problemi con l'API LLM**: Controlla la tua chiave API e la configurazione del provider in `.env`

---

Realizzato con ❤️ usando Pydantic AI, FastAPI, PostgreSQL e Neo4j. 