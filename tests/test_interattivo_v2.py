#!/usr/bin/env python3
"""
Test interattivo migliorato del sistema medico Claude-Fisio
"""

import asyncio
import logging
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from agent.agent import rag_agent
from agent.tools import vector_search_tool, VectorSearchInput
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging - riduci i log Neo4j
logging.getLogger('neo4j').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_search_interattivo():
    """Test ricerca interattiva."""
    print("\n🔍 TEST RICERCA MEDICA")
    print("=" * 50)
    
    while True:
        query = input("\n📝 Inserisci una domanda medica (o 'quit' per uscire): ")
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
            
        try:
            print("⏳ Cercando...")
            # Test ricerca
            search_input = VectorSearchInput(query=query, limit=3)
            results = await vector_search_tool(search_input)
            
            print(f"\n📊 Trovati {len(results)} risultati:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. 📄 {result.document_title}")
                print(f"   📈 Score: {result.score:.3f}")
                print(f"   📝 Contenuto: {result.content[:150]}...")
                
        except Exception as e:
            print(f"❌ Errore: {e}")

async def test_quiz_migliorato():
    """Test generazione quiz migliorato con quiz specifici."""
    print("\n🎯 TEST GENERAZIONE QUIZ MIGLIORATO")
    print("=" * 50)
    
    while True:
        print("\nEsempi di argomenti disponibili:")
        print("- anatomia della spalla")
        print("- riabilitazione del ginocchio") 
        print("- dolore lombare")
        print("- terapia manuale")
        print("- biomeccanica")
        
        topic = input("\n📚 Inserisci argomento quiz (o 'quit' per uscire): ")
        
        if topic.lower() in ['quit', 'exit', 'q']:
            break
            
        num_questions = input("📝 Numero domande (default 3): ") or "3"
        
        try:
            num_questions = int(num_questions)
            
            # Prompt migliorato per quiz più specifici
            quiz_prompt = f"""
            Genera un quiz professionale di fisioterapia con {num_questions} domande specifiche su: {topic}.
            
            Requisiti:
            1. Domande specifiche e dettagliate basate sulla documentazione medica
            2. Per domande a scelta multipla: fornisci 4 opzioni con contenuti reali
            3. Includi la risposta corretta per ogni domanda
            4. Aggiungi spiegazioni brevi per ogni risposta
            5. Usa terminologia medica appropriata
            
            Formato richiesto:
            DOMANDA [numero]: [testo domanda specifica]
            A) [opzione specifica]
            B) [opzione specifica] 
            C) [opzione specifica]
            D) [opzione specifica]
            RISPOSTA CORRETTA: [lettera]
            SPIEGAZIONE: [spiegazione breve]
            """
            
            print(f"\n⏳ Generando quiz specifico su '{topic}'...")
            
            # Usa l'agent per generare il quiz
            result = await rag_agent.run(quiz_prompt)
            
            if hasattr(result, 'output') and result.output:
                print(f"\n✅ Quiz generato con successo!")
                print("=" * 60)
                print(result.output)
                print("=" * 60)
                
                # Opzione per quiz interattivo
                interactive = input("\n🎮 Vuoi rispondere al quiz interattivamente? (s/n): ")
                if interactive.lower() in ['s', 'si', 'y', 'yes']:
                    await quiz_interattivo(result.output)
                    
            elif hasattr(result, 'data') and result.data:
                print(f"\n✅ Quiz generato con successo!")
                print("=" * 60)
                print(result.data)
                print("=" * 60)
            else:
                print("❌ Errore nella generazione del quiz")
                
        except ValueError:
            print("❌ Numero domande non valido")
        except Exception as e:
            print(f"❌ Errore: {e}")

async def quiz_interattivo(quiz_text):
    """Modalità quiz interattiva."""
    print("\n🎮 MODALITÀ QUIZ INTERATTIVA")
    print("=" * 50)
    
    # Parsing semplice del quiz
    lines = quiz_text.split('\n')
    domande = []
    current_question = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('DOMANDA'):
            if current_question:
                domande.append(current_question)
            current_question = {'domanda': line}
        elif line.startswith(('A)', 'B)', 'C)', 'D)')):
            if 'opzioni' not in current_question:
                current_question['opzioni'] = []
            current_question['opzioni'].append(line)
        elif line.startswith('RISPOSTA CORRETTA:'):
            current_question['risposta'] = line.replace('RISPOSTA CORRETTA:', '').strip()
        elif line.startswith('SPIEGAZIONE:'):
            current_question['spiegazione'] = line.replace('SPIEGAZIONE:', '').strip()
    
    if current_question:
        domande.append(current_question)
    
    # Esegui quiz interattivo
    punteggio = 0
    totale = len(domande)
    
    for i, domanda in enumerate(domande, 1):
        if 'domanda' in domanda:
            print(f"\n📝 {domanda['domanda']}")
            
            if 'opzioni' in domanda:
                for opzione in domanda['opzioni']:
                    print(f"   {opzione}")
                
                risposta_utente = input("\n👉 La tua risposta (A/B/C/D): ").upper().strip()
                
                if 'risposta' in domanda and risposta_utente == domanda['risposta']:
                    print("✅ Corretto!")
                    punteggio += 1
                else:
                    print(f"❌ Sbagliato. Risposta corretta: {domanda.get('risposta', 'N/A')}")
                
                if 'spiegazione' in domanda:
                    print(f"💡 Spiegazione: {domanda['spiegazione']}")
                
                input("\n⏵ Premi Enter per continuare...")
    
    # Risultato finale
    print(f"\n🏆 RISULTATO FINALE")
    print("=" * 30)
    print(f"Punteggio: {punteggio}/{totale} ({punteggio/totale*100:.1f}%)")
    
    if punteggio == totale:
        print("🌟 Perfetto! Ottima conoscenza!")
    elif punteggio >= totale * 0.8:
        print("👍 Molto bene! Buona preparazione!")
    elif punteggio >= totale * 0.6:
        print("📚 Discreto, ma puoi migliorare!")
    else:
        print("📖 Serve più studio su questo argomento!")

async def test_chat_libero():
    """Test chat libero con l'agent."""
    print("\n💬 CHAT LIBERO CON L'AGENT MEDICO")
    print("=" * 50)
    print("Puoi fare qualsiasi domanda medica/fisioterapica!")
    
    while True:
        question = input("\n❓ La tua domanda (o 'quit' per uscire): ")
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
            
        try:
            print(f"\n⏳ Elaborando risposta...")
            
            # Usa l'agent per rispondere
            result = await rag_agent.run(question)
            
            if hasattr(result, 'output') and result.output:
                print(f"\n🤖 Risposta:")
                print("-" * 40)
                print(result.output)
                print("-" * 40)
            elif hasattr(result, 'data') and result.data:
                print(f"\n🤖 Risposta:")
                print("-" * 40)
                print(result.data)
                print("-" * 40)
            else:
                print("❌ Errore nella generazione della risposta")
                
        except Exception as e:
            print(f"❌ Errore: {e}")

async def menu_principale():
    """Menu principale interattivo."""
    while True:
        print("\n🏥 SISTEMA MEDICO CLAUDE-FISIO v2.0")
        print("=" * 50)
        print("1. 🔍 Test Ricerca Documenti")
        print("2. 🎯 Test Quiz Professionale (Migliorato)")
        print("3. 💬 Chat Libero con Agent")
        print("4. 📊 Statistiche Sistema")
        print("5. ❌ Esci")
        
        choice = input("\n👉 Scegli opzione (1-5): ")
        
        if choice == "1":
            await test_search_interattivo()
        elif choice == "2":
            await test_quiz_migliorato()
        elif choice == "3":
            await test_chat_libero()
        elif choice == "4":
            await mostra_statistiche()
        elif choice == "5":
            print("\n👋 Arrivederci!")
            break
        else:
            print("❌ Opzione non valida")

async def mostra_statistiche():
    """Mostra statistiche del sistema."""
    print("\n📊 STATISTICHE SISTEMA")
    print("=" * 50)
    
    try:
        from agent.db_utils import db_pool
        
        # Inizializza connessione
        await db_pool.initialize()
        
        async with db_pool.acquire() as conn:
            # Conta documenti
            doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
            
            # Conta chunks
            chunk_count = await conn.fetchval("SELECT COUNT(*) FROM chunks")
            
            # Documenti per tipo
            doc_stats = await conn.fetch("""
                SELECT 
                    title,
                    COUNT(*) as chunk_count
                FROM documents d
                JOIN chunks c ON d.id = c.document_id
                GROUP BY d.id, d.title
                ORDER BY chunk_count DESC
            """)
            
        print(f"📄 Documenti totali: {doc_count}")
        print(f"📝 Chunks totali: {chunk_count}")
        print(f"📈 Media chunks per documento: {chunk_count/doc_count:.1f}")
        
        print("\n📚 Distribuzione contenuti:")
        for stat in doc_stats:
            title = stat['title'][:50] + "..." if len(stat['title']) > 50 else stat['title']
            print(f"   - {title}: {stat['chunk_count']} chunks")
            
        await db_pool.close()
        
    except Exception as e:
        print(f"❌ Errore nel recupero statistiche: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(menu_principale())
    except KeyboardInterrupt:
        print("\n\n👋 Uscita forzata. Arrivederci!")
    except Exception as e:
        print(f"\n❌ Errore critico: {e}")
