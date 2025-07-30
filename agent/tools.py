"""
Tools for the Pydantic AI agent.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import json
import random

from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Temporary bypass for sentence_transformers dependency issue
try:
    from sentence_transformers import CrossEncoder
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("[WARNING] sentence_transformers not available - using fallback re-ranking")
    CrossEncoder = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from .db_utils import (
    vector_search,
    hybrid_search,
    get_document,
    list_documents,
    get_document_chunks
)
from .graph_utils import (
    search_knowledge_graph,
    get_entity_relationships,
    graph_client
)
from .models import ChunkResult, GraphSearchResult, DocumentMetadata
from .providers import get_embedding_client, get_embedding_model

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Cross-Encoder model for re-ranking
# This model is small, fast, and optimized for re-ranking tasks.
if SENTENCE_TRANSFORMERS_AVAILABLE:
    try:
        cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        print("[INFO] Cross-Encoder initialized successfully")
    except Exception as e:
        print(f"[WARNING] Failed to initialize Cross-Encoder: {e}")
        print("[INFO] Using fallback re-ranking without Cross-Encoder")
        cross_encoder = None
        SENTENCE_TRANSFORMERS_AVAILABLE = False
else:
    cross_encoder = None
    print("[INFO] Using fallback re-ranking without Cross-Encoder")

# Initialize embedding client with flexible provider
embedding_client = get_embedding_client()
EMBEDDING_MODEL = get_embedding_model()


async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using OpenAI.
    
    Args:
        text: Text to embed
    
    Returns:
        Embedding vector
    """
    try:
        response = await embedding_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


# Re-ranking function
def rerank_documents(query: str, documents: List[ChunkResult]) -> List[ChunkResult]:
    """
    Re-ranks a list of documents based on their relevance to a query using a Cross-Encoder.
    Falls back to original ranking if Cross-Encoder is not available.

    Args:
        query: The search query.
        documents: A list of ChunkResult objects to be re-ranked.

    Returns:
        A new list of ChunkResult objects sorted by re-ranked relevance.
    """
    if not documents:
        return []

    # Check if Cross-Encoder is available
    if not SENTENCE_TRANSFORMERS_AVAILABLE or cross_encoder is None:
        # Fallback: return documents with their original scores (no re-ranking)
        logger.info("Cross-Encoder not available, using original ranking")
        return documents

    # Prepare pairs for the Cross-Encoder
    pairs = [(query, doc.content) for doc in documents]

    # Get scores from the Cross-Encoder
    scores = cross_encoder.predict(pairs)

    # Add scores to documents and sort
    for doc, score in zip(documents, scores):
        doc.score = float(score)  # Convert numpy.float32 to native Python float immediately

    # Sort documents by the new score in descending order
    return sorted(documents, key=lambda x: x.score, reverse=True)


# Tool Input Models
class VectorSearchInput(BaseModel):
    """Input for vector search tool."""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, description="Maximum number of results")


class QuizGeneratorInput(BaseModel):
    """Input for quiz generation tool."""
    topic: str = Field(..., description="Quiz topic from medical documentation")
    num_questions: int = Field(default=5, description="Number of questions to generate (1-10)")
    difficulty_level: str = Field(default="medium", description="Difficulty level: easy, medium, hard")
    question_types: List[str] = Field(default=["multiple_choice", "open_ended"], description="Types of questions to include")
    language: str = Field(default="italian", description="Language for questions and answers")


class GraphSearchInput(BaseModel):
    """Input for graph search tool."""
    query: str = Field(..., description="Search query")


class HybridSearchInput(BaseModel):
    """Input for hybrid search tool."""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=5, description="Final number of results after re-ranking")
    initial_retrieval_size: int = Field(default=15, description="Number of documents to retrieve before re-ranking")


class DocumentInput(BaseModel):
    """Input for document retrieval."""
    document_id: str = Field(..., description="Document ID to retrieve")


class DocumentListInput(BaseModel):
    """Input for listing documents."""
    limit: int = Field(default=20, description="Maximum number of documents")
    offset: int = Field(default=0, description="Number of documents to skip")


class EntityRelationshipInput(BaseModel):
    """Input for entity relationship query."""
    entity_name: str = Field(..., description="Name of the entity")
    depth: int = Field(default=2, description="Maximum traversal depth")


class EntityTimelineInput(BaseModel):
    """Input for entity timeline query."""
    entity_name: str = Field(..., description="Name of the entity")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")


# Tool Implementation Functions
async def vector_search_tool(input_data: VectorSearchInput) -> List[ChunkResult]:
    """
    Perform vector similarity search.
    
    Args:
        input_data: Search parameters
    
    Returns:
        List of matching chunks
    """
    try:
        # Generate embedding for the query
        embedding = await generate_embedding(input_data.query)
        
        # Perform vector search
        results = await vector_search(
            embedding=embedding,
            limit=input_data.limit
        )

        # Convert to ChunkResult models
        return [
            ChunkResult(
                chunk_id=str(r["chunk_id"]),
                document_id=str(r["document_id"]),
                content=r["content"],
                score=r["similarity"],
                metadata=r["metadata"],
                document_title=r["document_title"],
                document_source=r["document_source"]
            )
            for r in results
        ]
        
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []


async def graph_search_tool(input_data: GraphSearchInput) -> List[GraphSearchResult]:
    """
    Search the knowledge graph.
    
    Args:
        input_data: Search parameters
    
    Returns:
        List of graph search results
    """
    try:
        results = await search_knowledge_graph(
            query=input_data.query
        )
        
        # Convert to GraphSearchResult models
        return [
            GraphSearchResult(
                fact=r["fact"],
                uuid=r["uuid"],
                valid_at=r.get("valid_at"),
                invalid_at=r.get("invalid_at"),
                source_node_uuid=r.get("source_node_uuid")
            )
            for r in results
        ]
        
    except Exception as e:
        logger.error(f"Graph search failed: {e}")
        return []


async def hybrid_search_tool(input_data: HybridSearchInput) -> List[ChunkResult]:
    """
    Perform hybrid search (vector + keyword) with re-ranking.
    
    Args:
        input_data: Search parameters
    
    Returns:
        List of matching chunks
    """
    try:
        # Generate embedding for the query
        embedding = await generate_embedding(input_data.query)
        
        # Step 1: Perform initial retrieval with a larger size
        initial_results = await vector_search(
            embedding=embedding,
            limit=input_data.initial_retrieval_size
        )
        
        if not initial_results:
            return []

        # Convert to ChunkResult models for re-ranking
        initial_chunks = [
            ChunkResult(
                chunk_id=str(r["chunk_id"]),
                document_id=str(r["document_id"]),
                content=r["content"],
                score=r["similarity"],
                metadata=r["metadata"],
                document_title=r["document_title"],
                document_source=r["document_source"]
            )
            for r in initial_results
        ]
        
        # Step 2: Re-rank the initial results
        reranked_chunks = rerank_documents(input_data.query, initial_chunks)
        
        # Step 3: Return the top N results after re-ranking
        return reranked_chunks[:input_data.limit]
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        return []


async def get_document_tool(input_data: DocumentInput) -> Optional[Dict[str, Any]]:
    """
    Retrieve a complete document.
    
    Args:
        input_data: Document retrieval parameters
    
    Returns:
        Document data or None
    """
    try:
        document = await get_document(input_data.document_id)
        
        if document:
            # Also get all chunks for the document
            chunks = await get_document_chunks(input_data.document_id)
            document["chunks"] = chunks
        
        return document
        
    except Exception as e:
        logger.error(f"Document retrieval failed: {e}")
        return None


async def list_documents_tool(input_data: DocumentListInput) -> List[DocumentMetadata]:
    """
    List available documents.
    
    Args:
        input_data: Listing parameters
    
    Returns:
        List of document metadata
    """
    try:
        documents = await list_documents(
            limit=input_data.limit,
            offset=input_data.offset
        )
        
        # Convert to DocumentMetadata models
        return [
            DocumentMetadata(
                id=d["id"],
                title=d["title"],
                source=d["source"],
                metadata=d["metadata"],
                created_at=datetime.fromisoformat(d["created_at"]),
                updated_at=datetime.fromisoformat(d["updated_at"]),
                chunk_count=d.get("chunk_count")
            )
            for d in documents
        ]
        
    except Exception as e:
        logger.error(f"Document listing failed: {e}")
        return []


async def get_entity_relationships_tool(input_data: EntityRelationshipInput) -> Dict[str, Any]:
    """
    Get relationships for an entity.
    
    Args:
        input_data: Entity relationship parameters
    
    Returns:
        Entity relationships
    """
    try:
        return await get_entity_relationships(
            entity=input_data.entity_name,
            depth=input_data.depth
        )
        
    except Exception as e:
        logger.error(f"Entity relationship query failed: {e}")
        return {
            "central_entity": input_data.entity_name,
            "related_entities": [],
            "relationships": [],
            "depth": input_data.depth,
            "error": str(e)
        }


async def get_entity_timeline_tool(input_data: EntityTimelineInput) -> List[Dict[str, Any]]:
    """
    Get timeline of facts for an entity.
    
    Args:
        input_data: Timeline query parameters
    
    Returns:
        Timeline of facts
    """
    try:
        # Parse dates if provided
        start_date = None
        end_date = None
        
        if input_data.start_date:
            start_date = datetime.fromisoformat(input_data.start_date)
        if input_data.end_date:
            end_date = datetime.fromisoformat(input_data.end_date)
        
        # Get timeline from graph
        timeline = await graph_client.get_entity_timeline(
            entity_name=input_data.entity_name,
            start_date=start_date,
            end_date=end_date
        )
        
        return timeline
        
    except Exception as e:
        logger.error(f"Entity timeline query failed: {e}")
        return []


# Combined search function for agent use
async def perform_comprehensive_search(
    query: str,
    use_vector: bool = True,
    use_graph: bool = True,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Perform a comprehensive search using multiple methods.
    
    Args:
        query: Search query
        use_vector: Whether to use vector search
        use_graph: Whether to use graph search
        limit: Maximum results per search type (only applies to vector search)
    
    Returns:
        Combined search results
    """
    results = {
        "query": query,
        "vector_results": [],
        "graph_results": [],
        "total_results": 0
    }
    
    tasks = []
    
    if use_vector:
        tasks.append(vector_search_tool(VectorSearchInput(query=query, limit=limit)))
    
    if use_graph:
        tasks.append(graph_search_tool(GraphSearchInput(query=query)))
    
    if tasks:
        search_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        if use_vector and not isinstance(search_results[0], Exception):
            results["vector_results"] = search_results[0]
        
        if use_graph:
            graph_idx = 1 if use_vector else 0
            if not isinstance(search_results[graph_idx], Exception):
                results["graph_results"] = search_results[graph_idx]
    
    results["total_results"] = len(results["vector_results"]) + len(results["graph_results"])
    
    return results


async def quiz_generator_tool(input_data: QuizGeneratorInput) -> Dict[str, Any]:
    """
    Generate educational quiz based on medical documentation.
    
    This tool creates intelligent quiz questions using hybrid search
    to find relevant content and knowledge graph for clinical relationships.
    
    Args:
        input_data: Quiz generation parameters
    
    Returns:
        Generated quiz with questions and answers
    """
    try:
        # Step 1: Use hybrid search to find relevant medical content
        hybrid_results = await hybrid_search_tool(HybridSearchInput(
            query=input_data.topic,
            limit=5,  # We still want the top 5 for the quiz context
            initial_retrieval_size=20 # But we retrieve more initially
        ))
        
        if not hybrid_results:
            return {
                "error": "No relevant medical content found for the specified topic",
                "topic": input_data.topic,
                "questions": []
            }
        
        # Step 2: Use knowledge graph to find anatomical relationships
        graph_results = await graph_search_tool(GraphSearchInput(
            query=input_data.topic
        ))
        
        # Step 3: Generate quiz questions based on content
        quiz_questions = await _generate_medical_quiz_questions(
            topic=input_data.topic,
            content_chunks=hybrid_results,
            graph_facts=graph_results,
            num_questions=input_data.num_questions,
            difficulty_level=input_data.difficulty_level,
            question_types=input_data.question_types,
            language=input_data.language
        )
        
        # Step 4: Format quiz response
        quiz_response = {
            "topic": input_data.topic,
            "difficulty_level": input_data.difficulty_level,
            "num_questions": len(quiz_questions),
            "language": input_data.language,
            "questions": quiz_questions,
            "sources_used": len(hybrid_results),
            "graph_facts_used": len(graph_results),
            "generated_at": datetime.now().isoformat()
        }
        
        return quiz_response
        
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        return {
            "error": f"Quiz generation failed: {str(e)}",
            "topic": input_data.topic,
            "questions": []
        }


async def _generate_medical_quiz_questions(
    topic: str,
    content_chunks: List[Any],
    graph_facts: List[Any],
    num_questions: int,
    difficulty_level: str,
    question_types: List[str],
    language: str
) -> List[Dict[str, Any]]:
    """
    Generate medical quiz questions using LLM with structured prompts.
    
    This function creates contextually relevant medical questions
    based on the retrieved content and knowledge graph facts.
    """
    questions = []
    
    # Prepare content context for LLM
    content_context = "\n\n".join([
        f"**{chunk.document_title}**: {chunk.content[:500]}..."
        for chunk in content_chunks[:8]  # Use top 8 chunks
    ])
    
    # Prepare graph context
    graph_context = "\n".join([
        f"- {fact.fact}" for fact in graph_facts[:10]  # Use top 10 facts
    ])
    
    # Generate questions based on content
    for i in range(num_questions):
        question_type = random.choice(question_types)
        
        if question_type == "multiple_choice":
            question = await _generate_multiple_choice_question(
                topic, content_context, graph_context, difficulty_level, language, i+1
            )
        elif question_type == "open_ended":
            question = await _generate_open_ended_question(
                topic, content_context, graph_context, difficulty_level, language, i+1
            )
        else:
            # Default to multiple choice
            question = await _generate_multiple_choice_question(
                topic, content_context, graph_context, difficulty_level, language, i+1
            )
        
        if question:
            questions.append(question)
    
    return questions


async def _generate_multiple_choice_question(
    topic: str, content_context: str, graph_context: str, 
    difficulty_level: str, language: str, question_num: int
) -> Dict[str, Any]:
    """
    Generate a multiple choice question using LLM.
    """
    try:
        # TODO: Sostituire questa logica statica con una vera chiamata a un LLM.
        # L'implementazione attuale è un placeholder per garantire la funzionalità del tool.
        # Esempio di come potrebbe essere con un client LLM:
        # response = await llm_client.chat.completions.create(
        #     model="gpt-4-turbo",
        #     messages=[
        #         {"role": "system", "content": "Sei un esperto di fisioterapia che crea domande per quiz..."},
        #         {"role": "user", "content": f"Crea una domanda a scelta multipla su {topic}..."}
        #     ],
        #     response_model=QuestionModel
        # )
        # return response.dict()

        # Create a structured multiple choice question
        question_data = {
            "id": f"mc_{question_num}",
            "type": "multiple_choice",
            "question": f"Domanda {question_num}: Basandosi sulla documentazione su {topic}, quale delle seguenti affermazioni è corretta?",
            "options": [
                "A) Opzione generata dal contenuto medico",
                "B) Opzione alternativa basata su relazioni anatomiche",
                "C) Opzione di distrazione clinicamente plausibile",
                "D) Opzione di controllo per valutazione comprensione"
            ],
            "correct_answer": "A",
            "explanation": f"La risposta corretta è basata sul contenuto documentale specifico riguardante {topic}.",
            "difficulty": difficulty_level,
            "source_content": content_context[:200] + "...",
            "clinical_reasoning": "Questa domanda verifica la comprensione delle relazioni anatomiche e terapeutiche."
        }
        
        return question_data
        
    except Exception as e:
        logger.error(f"Failed to generate multiple choice question: {e}")
        return None


async def _generate_open_ended_question(
    topic: str, content_context: str, graph_context: str,
    difficulty_level: str, language: str, question_num: int
) -> Dict[str, Any]:
    """
    Generate an open-ended question using LLM.
    """
    try:
        # TODO: Sostituire questa logica statica con una vera chiamata a un LLM.
        # Questa è un'implementazione placeholder.
        # Create a structured open-ended question
        question_data = {
            "id": f"oe_{question_num}",
            "type": "open_ended",
            "question": f"Domanda {question_num}: Spiega le implicazioni cliniche e terapeutiche relative a {topic}, considerando le relazioni anatomiche e i protocolli di trattamento.",
            "expected_elements": [
                "Descrizione anatomica accurata",
                "Relazioni con strutture adiacenti",
                "Implicazioni terapeutiche",
                "Evidenza clinica supportante"
            ],
            "scoring_criteria": {
                "accuracy": "Precisione delle informazioni mediche",
                "completeness": "Completezza della risposta",
                "clinical_reasoning": "Ragionamento clinico appropriato",
                "evidence_based": "Supporto evidence-based"
            },
            "difficulty": difficulty_level,
            "source_content": content_context[:200] + "...",
            "clinical_context": "Questa domanda valuta la capacità di integrazione delle conoscenze anatomiche e terapeutiche."
        }
        
        return question_data
        
    except Exception as e:
        logger.error(f"Failed to generate open-ended question: {e}")
        return None