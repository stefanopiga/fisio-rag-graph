# Guida all'Uso e Manuale Operativo

Questa guida fornisce le istruzioni per configurare, eseguire e mantenere il sistema Fisio-RAG+Graph.

## 1. Configurazione dell'Ambiente

### Prerequisiti
- Python 3.11+ (raccomandato per compatibilità)
- Conda (Anaconda o Miniconda) - **OBBLIGATORIO per Windows**
- PostgreSQL con estensione pgvector
- Neo4j per Knowledge Graph
- Accesso a un provider di modelli LLM (es. OpenAI, Anthropic, Google)

### Installazione con Conda (Raccomandato)

#### 1.1 Setup Ambiente Conda
```bash
# Creare ambiente fisio-rag
conda create -n fisio-rag python=3.11 -y

# Attivare ambiente
conda activate fisio-rag

# Installare dipendenze critiche via conda (risolve conflitti pyarrow su Windows)
conda install -c conda-forge pyarrow -y

# Installare requirements Python
pip install -r requirements.txt
```

#### 1.2 Configurazione Database
```bash
# Eseguire schema SQL su PostgreSQL
psql -d "your_database_url" -f sql/schema.sql

# Verificare estensioni installate
psql -d "your_database_url" -c "SELECT extname FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp', 'pg_trgm');"
```

#### 1.3 Configurazione Ambiente
```bash
# Copiare configurazione di esempio
cp env.txt .env

# Modificare .env con credenziali reali:
# - DATABASE_URL (PostgreSQL connection)
# - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
# - LLM_API_KEY (OpenAI o provider scelto)
```

### Installazione Alternativa (Docker)
1.  **Clonare il repository** (se non già fatto).
2.  **Creare un ambiente conda**:
    ```bash
    conda create -n fisio-rag python=3.10
    conda activate fisio-rag
    ```
3.  **Installare le dipendenze Python**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configurare i servizi di backend (Database e Grafo)**:
    *   Il modo più semplice per avviare PostgreSQL (con pgvector) e Graphiti è tramite Docker. Assicurarsi che i servizi siano configurati correttamente e che le credenziali corrispondano a quelle nei file di ambiente. Un file `docker-compose.yml` di esempio dovrebbe essere presente per facilitare l'avvio.
    ```bash
    docker-compose up -d
    ```
5.  **Configurare le variabili d'ambiente**:
    *   Copiare il file `.env.example` in un nuovo file chiamato `.env`.
    *   Compilare il file `.env` con le proprie credenziali:
        *   `DATABASE_URL`: L'URL di connessione al database PostgreSQL.
        *   `GRAPHITI_API_KEY`: La chiave API per il servizio Graphiti.
        *   `OPENAI_API_KEY` (o la chiave per il provider LLM scelto): La chiave API per il modello di linguaggio.
        *   Altre configurazioni specifiche del provider LLM (modello, provider, etc.).

## 2. Ingestione dei Dati

Il sistema impara dai documenti presenti nella cartella `documents/fisioterapia`.

### Aggiungere Nuovi Documenti
- Per aggiungere nuove conoscenze, semplicemente inserire nuovi file di testo (`.txt`, `.md`) nella cartella `documents/fisioterapia`.

### Eseguire la Pipeline di Ingestione

#### Metodo 1: Script Dedicato (Raccomandato)
```bash
# Attivare ambiente
conda activate fisio-rag

# Navigare al progetto
cd C:\Users\aless\Desktop\Claude-Fisio\agentic-RAG\fisio-rag+graph

# Eseguire ingestione documenti
python -m ingestion.ingest

# Opzione con pulizia database
python -m ingestion.ingest --clean
```

#### Metodo 2: Script Legacy
```bash
conda run -n fisio-rag python run_medical_ingestion.py
```

**Importante**: Per impostazione predefinita, lo script pulisce i dati esistenti prima di eseguirne di nuovi per evitare duplicati.

Questo script processerà tutti i documenti, creerà chunk, estrarrà entità, genererà embedding e popolerà sia PostgreSQL che Neo4j.

## 3. Utilizzo del Sistema

Una volta completata l'ingestione, è possibile interagire con l'agente in diverse modalità.

### Modalità 1: Avvio Sistema Completo (Raccomandato)

#### Terminale 1 - Server API
```bash
# Attivare ambiente
conda activate fisio-rag

# Navigare al progetto
cd C:\Users\aless\Desktop\Claude-Fisio\agentic-RAG\fisio-rag+graph

# Avviare server API
python -m agent.api
```

#### Terminale 2 - CLI Interattiva
```bash
# Attivare ambiente
conda activate fisio-rag

# Navigare al progetto
cd C:\Users\aless\Desktop\Claude-Fisio\agentic-RAG\fisio-rag+graph

# Avviare CLI
python cli.py
```

### Modalità 2: Test Interattivo (per Sviluppo e Debug)
- Questa modalità è ideale per testare rapidamente i componenti senza avviare un server.

```bash
conda run -n fisio-rag python test_interattivo_v2.py
```
Apparirà un menu che permette di:
- **Testare la ricerca**: Verificare la capacità di recupero dei documenti.
- **Generare quiz**: Testare la funzione di generazione di quiz su un argomento.
- **Chattare liberamente**: Interagire direttamente con l'agente.
- **Visualizzare statistiche**: Controllare il numero di documenti e chunk nel database.

### Modalità 3: Applicazione Client-Server (per Uso Normale)
- Questa è la modalità operativa standard, che simula un ambiente di produzione.

**Passo A: Avviare il Server API**
- Il server gestisce tutta la logica dell'agente. Deve rimanere in esecuzione in un terminale.

```bash
conda run -n fisio-rag uvicorn agent.api:app --reload --port 8058
```

**Passo B: Avviare il Client CLI**
- In un **secondo terminale**, avviare l'interfaccia a riga di comando per iniziare a chattare.

```bash
conda run -n fisio-rag python cli.py
```

Ora è possibile porre domande di fisioterapia direttamente dalla CLI. La CLI comunicherà con il server API per ottenere le risposte.

### Modalità 4: Valutazione del Sistema
- Per valutare le performance del sistema RAG, utilizzare lo script di valutazione:

```bash
conda run -n fisio-rag python tests/run_evaluation.py
```

I risultati della valutazione verranno salvati nella cartella `test-results/`.

## 4. Comandi di Avvio Rapido

### Setup Completo (Prima Esecuzione)
```bash
# 1. Creare e attivare ambiente
conda create -n fisio-rag python=3.11 -y
conda activate fisio-rag

# 2. Installare dipendenze
conda install -c conda-forge pyarrow -y
pip install -r requirements.txt

# 3. Configurare database
psql -d "your_database_url" -f sql/schema.sql

# 4. Configurare ambiente
cp env.txt .env
# [Modificare .env con credenziali reali]

# 5. Ingestione documenti
python -m ingestion.ingest --clean
```

### Avvio Operativo (Esecuzioni Successive)
```bash
# Terminale 1 - Server API
conda activate fisio-rag
cd C:\Users\aless\Desktop\Claude-Fisio\agentic-RAG\fisio-rag+graph
python -m agent.api

# Terminale 2 - CLI
conda activate fisio-rag
cd C:\Users\aless\Desktop\Claude-Fisio\agentic-RAG\fisio-rag+graph
python cli.py
```

### Comandi di Manutenzione
```bash
# Aggiornamento documenti
python -m ingestion.ingest

# Test sistema
python complete_medical_test.py

# Valutazione performance
python tests/run_evaluation.py
```

## 5. Manutenzione

### Aggiornamento delle Entità Mediche
- Il sistema di estrazione delle entità si basa sul file `ingestion/medical_entities.md`.
- Per migliorare l'accuratezza o espandere la conoscenza del sistema, è possibile modificare questo file aggiungendo o rimuovendo termini sotto le rispettive categorie (`Anatomical Structures`, `Pathological Conditions`, etc.).
- Dopo aver modificato il file, è **necessario eseguire nuovamente la pipeline di ingestione** (`python -m ingestion.ingest --clean`) per applicare le modifiche ai dati esistenti.

### Note Critiche per Windows
- **Ambiente Conda obbligatorio** per risolvere conflitti `pyarrow` su Windows
- **Due terminali separati** per API e CLI
- **Schema SQL** deve essere eseguito prima dell'ingestione
- **File `.env`** configurazione essenziale per connessioni database e API
- **Percorsi assoluti** raccomandati per evitare problemi di navigazione 