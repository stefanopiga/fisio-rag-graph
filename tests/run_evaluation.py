import asyncio
import os
import httpx
import json # Added for json.loads
from dotenv import load_dotenv
from datasets import load_dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from langchain_openai import ChatOpenAI
from datasets import Dataset

import nest_asyncio
nest_asyncio.apply()

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# --- DEBUGGING STEP ---
print("--- Inizio Debug Variabili d'Ambiente ---")
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"OPENAI_API_KEY trovata. Inizia con: {api_key[:5]}")
else:
    print("ATTENZIONE: OPENAI_API_KEY non trovata!")
print("-----------------------------------------")

# Configurazione
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/chat/stream")
EVAL_DATASET_PATH = "evaluation_dataset_lombare.jsonl"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

async def get_rag_response(query: str) -> dict:
    """
    Interroga l'API del RAG e restituisce la risposta completa.
    Simula una chiamata simile a quella di cli.py ma raccoglie
    la risposta e i contesti.
    """
    full_response_content = ""
    contexts = []
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # CORREZIONE: Il server si aspetta 'message', non 'text'.
            async with client.stream("POST", API_URL, json={"message": query}) as response:
                response.raise_for_status()
                async for chunk in response.aiter_text():
                    if not chunk.strip():
                        continue
                    
                    if chunk.startswith("data:"):
                        data_str = chunk[len("data:"):].strip()
                        try:
                            data = json.loads(data_str)
                            
                            if data.get("type") == "text":
                                full_response_content += data.get("content", "")
                            elif data.get("type") == "contexts":
                                contexts = data.get("contexts", [])

                        except json.JSONDecodeError:
                            print(f"Attenzione: Impossibile fare il parse del chunk JSON: {data_str}")

        except httpx.HTTPStatusError as e:
            print(f"Errore HTTP: {e}")
            return {"answer": "", "contexts": []}
        except Exception as e:
            print(f"Errore durante la richiesta: {e}")
            return {"answer": "", "contexts": []}

    return {"answer": full_response_content, "contexts": [str(c) for c in contexts]}

async def main():
    """
    Funzione principale per eseguire la valutazione.
    """
    # Carica il dataset di valutazione
    print(f"Caricamento del dataset da: {EVAL_DATASET_PATH}")
    eval_dataset = load_dataset("json", data_files=EVAL_DATASET_PATH)
    eval_df = eval_dataset["train"].to_pandas()

    # Prepara i dati per la valutazione
    questions = eval_df["question"].tolist()
    ground_truths = eval_df["ground_truth"].tolist()
    
    answers = []
    contexts = []

    print("Inizio della raccolta delle risposte dal sistema RAG...")
    for question in questions:
        print(f"  - Ottenendo risposta per: '{question[:50]}...'")
        response = await get_rag_response(question)
        answers.append(response["answer"])
        contexts.append(response["contexts"])
    
    # Crea un oggetto Dataset di Hugging Face per Ragas
    ragas_dataset_dict = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }
    ragas_dataset = Dataset.from_dict(ragas_dataset_dict)

    # Configura le metriche
    metrics = [
        faithfulness,
        answer_relevancy,
        context_recall,
        context_precision,
    ]

    # Inizializza il modello LLM per la valutazione
    # Nota: Ragas usa un LLM per giudicare le risposte.
    if LLM_PROVIDER == "openai":
        llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL_NAME", "gpt-4-turbo"))
    else:
        # Qui andrebbe aggiunta la logica per altri provider (Ollama, Gemini, etc.)
        # Per ora, usiamo OpenAI come default per la valutazione.
        print("Provider LLM non supportato per la valutazione, usando OpenAI come fallback.")
        llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL_NAME", "gpt-4-turbo"))

    print("\nInizio valutazione con Ragas...")
    result = evaluate(
        dataset=ragas_dataset,
        metrics=metrics,
        llm=llm,
        raise_exceptions=False # Non bloccare l'esecuzione in caso di errore su una singola riga
    )

    print("\n--- Risultati della Valutazione RAG ---")
    print(result)
    print("--------------------------------------")
    
    # Converti i risultati in un dataframe pandas per una migliore visualizzazione
    results_df = result.to_pandas()
    print("\nDettagli dei punteggi:")
    print(results_df.head())

    # Salva i risultati dettagliati in un file CSV per un'analisi approfondita
    results_df.to_csv("test-results/evaluation_results_detailed.csv", index=False, encoding="utf-8-sig")
    print("\nRisultati dettagliati salvati in 'test-results/evaluation_results_detailed.csv'")


if __name__ == "__main__":
    asyncio.run(main()) 