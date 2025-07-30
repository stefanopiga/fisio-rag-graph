# Piano di Test Manuale: AUTH-02 - Integrazione Autenticazione Frontend

**Obiettivo**: Validare il corretto funzionamento del flusso di autenticazione frontend dopo l'integrazione con il backend.

**Prerequisiti**:
- Il server backend (FastAPI) deve essere in esecuzione e accessibile.
- L'applicazione frontend (React/Vite) deve essere in esecuzione.

---

### Caso di Test 1: Visualizzazione Pagina di Login

- **ID**: `TC-AUTH-02-01`
- **Descrizione**: Verifica che un utente non autenticato venga reindirizzato alla pagina di login.
- **Passi**:
  1. Aprire il browser e navigare all'URL dell'applicazione frontend.
- **Risultato Atteso**:
  - La pagina di login viene visualizzata correttamente.
  - L'interfaccia principale dell'applicazione non è accessibile.

---

### Caso di Test 2: Login con Credenziali Errate

- **ID**: `TC-AUTH-02-02`
- **Descrizione**: Verifica che il sistema gestisca correttamente un tentativo di login con credenziali non valide.
- **Passi**:
  1. Inserire uno username e/o una password errati nel form di login.
  2. Cliccare sul pulsante "Login".
- **Risultato Atteso**:
  - Viene mostrato un messaggio di errore (es. "Credenziali non valide").
  - L'utente rimane sulla pagina di login.

---

### Caso di Test 3: Login con Credenziali Corrette

- **ID**: `TC-AUTH-02-03`
- **Descrizione**: Verifica il successo del login con credenziali valide.
- **Passi**:
  1. Inserire username e password corretti.
  2. Cliccare sul pulsante "Login".
- **Risultato Atteso**:
  - L'utente viene reindirizzato all'interfaccia principale dell'applicazione.
  - La connessione WebSocket viene stabilita (l'indicatore di stato passa a "Connesso").
  - Un token di autenticazione (`authToken`) viene salvato nel `localStorage` del browser.

---

### Caso di Test 4: Persistenza della Sessione

- **ID**: `TC-AUTH-02-04`
- **Descrizione**: Verifica che la sessione utente persista dopo un ricaricamento della pagina.
- **Passi**:
  1. Effettuare un login con successo (vedi `TC-AUTH-02-03`).
  2. Ricaricare la pagina del browser.
- **Risultato Atteso**:
  - L'utente rimane autenticato e visualizza l'interfaccia principale senza dover effettuare nuovamente il login.

---

### Caso di Test 5: Funzionalità di Logout

- **ID**: `TC-AUTH-02-05`
- **Descrizione**: Verifica il corretto funzionamento del logout.
- **Passi**:
  1. Effettuare un login con successo.
  2. Cliccare sul pulsante "Logout" nell'header.
- **Risultato Atteso**:
  - L'utente viene reindirizzato alla pagina di login.
  - Il token di autenticazione (`authToken`) viene rimosso dal `localStorage`.
  - La connessione WebSocket viene terminata.

---

### Caso di Test 6: Accesso non autorizzato (opzionale)

- **ID**: `TC-AUTH-02-06`
- **Descrizione**: Simula un tentativo di accesso a WebSocket senza token valido.
- **Passi**:
  1. Effettuare il login.
  2. Aprire gli strumenti per sviluppatori del browser, andare nella sezione "Application" -> "Local Storage".
  3. Cancellare la chiave `authToken`.
  4. Ricaricare la pagina.
- **Risultato Atteso**:
  - L'utente viene reindirizzato alla pagina di login, siccome il token non è più presente.