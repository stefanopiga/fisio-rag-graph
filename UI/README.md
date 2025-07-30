# Fisio AI Studio

Un'applicazione moderna per lo studio di fisioterapia con intelligenza artificiale integrata.

## Caratteristiche

- 🎨 **Design Moderno**: Interfaccia scura e professionale basata su design system strutturato
- 🤖 **AI Integrata**: Collegamento con il sistema RAG di fisioterapia
- 💬 **Chat Intelligente**: Conversazioni in tempo reale con streaming
- 📱 **Cross-Platform**: Funziona su desktop (via Tauri) e mobile (via PWA)
- 🔧 **Strumenti Specializzati**: Analizzatore PDF, quiz generator, database anatomico

## Tecnologie

- **Frontend**: React 18 + TypeScript + Styled Components
- **Desktop**: Tauri (alternativa sicura a Electron)  
- **Mobile**: Progressive Web App (PWA)
- **Backend**: Integrazione con FastAPI del progetto fisio-rag+graph

## Avvio Rapido

1.  **Backend**:
    ```bash
    python -m agent.api
    ```
2.  **Frontend**:
    ```bash
    cd agentic-RAG/fisio-rag+graph/UI
    npm install
    npm run dev
    ```
3.  **CLI (Alternativa)**:

## Struttura Progetto

```
src/
├── components/        # Componenti React riutilizzabili
├── styles/           # Design system e stili globali  
├── types/            # Definizioni TypeScript
├── hooks/            # Custom hooks React
└── App.tsx           # Componente principale
```

## Configurazione

Modifica `.env` con gli endpoint del tuo backend:

```env
VITE_API_BASE_URL=http://localhost:8058
VITE_WS_URL=ws://localhost:8058/ws
```

## Distribuzione

### Desktop
Il build Tauri genera un installer per Windows/macOS/Linux.

### Mobile
L'app è una PWA installabile direttamente dal browser.

## Sicurezza

- ✅ Validazione input lato client e server  
- ✅ Rate limiting configurabile
- ✅ HTTPS in produzione
- ✅ Gestione sicura delle sessioni