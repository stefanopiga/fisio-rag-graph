#!/usr/bin/env python3
"""
Medical Quiz System - Complete Test Suite

Questo script esegue un test end-to-end completo del sistema,
verificando le funzionalità con asserzioni reali e generando
un report di riepilogo dinamico in formato Markdown.
"""

import asyncio
import logging
import json
from pathlib import Path
import sys
from datetime import datetime

# Aggiunge la root del progetto al path per permettere le importazioni
sys.path.append(str(Path(__file__).parent))

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Funzioni di Test ---

async def test_medical_search():
    """Testa le capacità di ricerca di contenuti medici con asserzioni."""
    logger.info("🔍 Inizio test: Ricerca Contenuti Medici...")
    results_summary = []
    try:
        from agent.tools import vector_search_tool, VectorSearchInput
        
        test_queries = [
            "anatomia della spalla", "riabilitazione del ginocchio", "terapia manuale",
            "biomeccanica del movimento", "muscoli rotatori", "legamento crociato anteriore"
        ]
        
        for query in test_queries:
            search_input = VectorSearchInput(query=query, limit=5)
            results = await vector_search_tool(search_input)
            
            assert len(results) > 0, f"La ricerca per '{query}' non ha prodotto risultati."
            assert results[0].score > 0.4, f"Il punteggio di similarità per '{query}' è troppo basso."
            
            results_summary.append({
                "query": query,
                "results_found": len(results),
                "best_match_score": round(results[0].score, 3)
            })
        
        logger.info("✅ Superato: Ricerca Contenuti Medici")
        return {"status": "✅ Passed", "details": results_summary}
        
    except Exception as e:
        logger.error(f"❌ Fallito: Ricerca Contenuti Medici - {e}")
        return {"status": f"❌ Failed: {e}", "details": results_summary}

async def test_quiz_scenarios():
    """Testa la generazione di quiz con asserzioni su output e tempi."""
    logger.info("🎯 Inizio test: Scenari di Generazione Quiz...")
    results_summary = []
    try:
        from agent.tools import quiz_generator_tool, QuizGeneratorInput
        
        scenarios = [
            {"name": "Anatomia Base", "topic": "anatomia della spalla", "num_questions": 3, "difficulty": "easy"},
            {"name": "Riabilitazione Intermedia", "topic": "riabilitazione del ginocchio", "num_questions": 5, "difficulty": "medium"},
            {"name": "Terapia Avanzata", "topic": "terapia manuale", "num_questions": 4, "difficulty": "hard"}
        ]
        
        for scenario in scenarios:
            quiz_input = QuizGeneratorInput(
                topic=scenario["topic"],
                num_questions=scenario["num_questions"],
                difficulty_level=scenario["difficulty"]
            )
            
            start_time = asyncio.get_event_loop().time()
            quiz_result = await quiz_generator_tool(quiz_input)
            generation_time = asyncio.get_event_loop().time() - start_time
            
            assert "error" not in quiz_result, f"Errore nella generazione quiz per '{scenario['name']}'"
            assert quiz_result.get("num_questions") == scenario["num_questions"], f"Numero di domande errato per '{scenario['name']}'"
            
            results_summary.append({
                "scenario": scenario['name'],
                "generation_time_s": round(generation_time, 2),
                "questions_generated": quiz_result.get("num_questions", 0),
                "status": "✅ Passed"
            })

        logger.info("✅ Superato: Scenari di Generazione Quiz")
        return {"status": "✅ Passed", "details": results_summary}
        
    except Exception as e:
        logger.error(f"❌ Fallito: Scenari di Generazione Quiz - {e}")
        return {"status": f"❌ Failed: {e}", "details": results_summary}

async def test_medical_entities():
    """Testa l'estrazione di entità mediche con asserzioni."""
    logger.info("🧬 Inizio test: Estrazione Entità Mediche...")
    try:
        from ingestion.graph_builder import GraphBuilder
        from ingestion.chunker import DocumentChunk
        
        test_content = "La sindrome da impingement della spalla richiede una terapia di rinforzo."
        test_chunk = DocumentChunk(content=test_content, index=0, start_char=0, end_char=len(test_content), metadata={}, token_count=len(test_content.split()))
        
        # Correzione: Utilizza le chiavi in italiano come definite in medical_entities.md
        expected_entities = {
            "Struttura Anatomica": ["spalla"],
            "Patologia": ["sindrome da impingement"],
            "Procedura di Trattamento": ["terapia di rinforzo"]
        }
        
        graph_builder = GraphBuilder()
        enriched_chunks = await graph_builder.extract_entities_from_chunks(
            [test_chunk], extract_anatomical=True, extract_pathological=True, extract_treatments=True
        )
        
        extracted_entities = enriched_chunks[0].metadata.get('entities', {})
        
        for entity_type, expected_list in expected_entities.items():
            assert entity_type in extracted_entities, f"Tipo di entità mancante: {entity_type}"
            for expected in expected_list:
                assert expected in extracted_entities[entity_type], f"Entità '{expected}' non trovata in '{entity_type}'"
        
        logger.info("✅ Superato: Estrazione Entità Mediche")
        return {"status": "✅ Passed", "details": extracted_entities}
        
    except Exception as e:
        logger.error(f"❌ Fallito: Estrazione Entità Mediche - {e}")
        return {"status": f"❌ Failed: {e}", "details": {}}

# --- Funzione di Report ---

def generate_markdown_report(results: dict):
    """Genera un report di riepilogo in formato Markdown."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"test-results/TEST_SUMMARY_{timestamp}.md"
    
    report_content = f"""# 📜 Test Suite Execution Summary - {timestamp}

## 📊 Overall Results

| Test Suite                | Status                               |
| :------------------------ | :----------------------------------- |
| **Medical Content Search**    | {results['search']['status']}        |
| **Quiz Generation Scenarios** | {results['quiz']['status']}          |
| **Medical Entity Extraction** | {results['entities']['status']}      |

---

## 🔍 Medical Content Search Details

| Query                          | Results Found | Best Match Score |
| :----------------------------- | :------------ | :--------------- |
"""
    for detail in results['search'].get('details', []):
        report_content += f"| `{detail['query']}` | {detail['results_found']} | **{detail['best_match_score']}** |\n"

    report_content += """
---

## 🎯 Quiz Generation Scenario Details

| Scenario                    | Generation Time (s) | Questions Generated | Status      |
| :-------------------------- | :------------------ | :------------------ | :---------- |
"""
    for detail in results['quiz'].get('details', []):
        report_content += f"| {detail['scenario']} | {detail['generation_time_s']}s | {detail['questions_generated']} | **{detail['status']}** |\n"

    report_content += f"""
---

## 🧬 Medical Entity Extraction Details

**Status**: {results['entities']['status']}

"""
    if 'details' in results['entities']:
        report_content += "```json\n"
        report_content += json.dumps(results['entities']['details'], indent=2, ensure_ascii=False)
        report_content += "\n```\n"

    report_content += "\n---\n\n**Report generato da `complete_medical_test.py`**"

    # Scrive il file di report
    Path("test-results").mkdir(exist_ok=True)
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    return report_filename

# --- Main Orchestrator ---

async def main():
    """Funzione principale che orchestra i test e la generazione del report."""
    
    logger.info("="*60)
    logger.info("🧪 ESECUZIONE TEST SUITE COMPLETA - Medical Quiz System")
    logger.info("="*60)
    
    # Esegue tutti i test in parallelo
    test_results = await asyncio.gather(
        test_medical_search(),
        test_quiz_scenarios(),
        test_medical_entities()
    )
    
    results = {
        "search": test_results[0],
        "quiz": test_results[1],
        "entities": test_results[2]
    }
    
    # Genera il report
    report_file = generate_markdown_report(results)
    
    logger.info("="*60)
    logger.info("🏁 TEST SUITE COMPLETATA")
    logger.info("="*60)
    
    # Stampa un riepilogo finale
    print("\n--- RISULTATI TEST ---")
    print(f"Ricerca Contenuti Medici: {results['search']['status']}")
    print(f"Generazione Quiz:         {results['quiz']['status']}")
    print(f"Estrazione Entità:        {results['entities']['status']}")
    print("------------------------")
    print(f"\n📄 Report di riepilogo dettagliato salvato in: {report_file}")
    print("\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Errore critico durante l'esecuzione della test suite: {e}")
        sys.exit(1) 