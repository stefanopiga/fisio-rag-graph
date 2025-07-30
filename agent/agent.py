"""
Main Instructor-based agent for agentic RAG with knowledge graph.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import instructor
from openai import OpenAI

from .prompts import SYSTEM_PROMPT
from .tools import (
    vector_search_tool,
    graph_search_tool,
    hybrid_search_tool,
    get_document_tool,
    list_documents_tool,
    get_entity_relationships_tool,
    get_entity_timeline_tool,
    quiz_generator_tool,
    VectorSearchInput,
    GraphSearchInput,
    HybridSearchInput,
    DocumentInput,
    DocumentListInput,
    EntityRelationshipInput,
    EntityTimelineInput,
    QuizGeneratorInput
)
from .providers import get_llm_provider, get_llm_model_name

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class AgentDependencies:
    """Dependencies for the agent."""
    session_id: str
    user_id: Optional[str] = None
    search_preferences: Dict[str, Any] = field(default_factory=lambda: {
        "use_vector": True,
        "use_graph": True,
        "default_limit": 10
    })
    retrieved_contexts: List[Dict[str, Any]] = field(default_factory=list)


def create_instructor_client() -> instructor.Instructor:
    """Creates and returns an instructor-patched OpenAI client."""
    provider = get_llm_provider()
    if provider.lower() == 'openai':
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        
        return instructor.patch(OpenAI(api_key=api_key))
    
    # Add other providers like Anthropic, Google, etc. as needed
    # For example:
    # if provider.lower() == 'anthropic':
    #     return instructor.patch(anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")))

    raise NotImplementedError(f"LLM provider '{provider}' is not supported by instructor in this setup.")


# Global instructor client
client = create_instructor_client()

async def run_agent_reasoning(query: str, dependencies: AgentDependencies) -> Any:
    """
    This function replaces the Pydantic-AI agent logic.
    It uses instructor to decide which tool to call based on the user query.
    """
    
    # In a real-world scenario, you'd have a more sophisticated routing logic here.
    # For now, we'll keep it simple and assume a primary tool or use LLM to decide.
    # This is a placeholder for a more complex reasoning step.
    
    # Simple logic: if the query contains "quiz", use the quiz tool.
    # Otherwise, use hybrid search.
    if "quiz" in query.lower():
        # This part would ideally also use instructor to parse parameters
        # For simplicity, we create a default input.
        quiz_input = QuizGeneratorInput(topic=query)
        return await quiz_generator(quiz_input)

    # Default to hybrid search for general queries
    search_input = HybridSearchInput(query=query)
    results = await hybrid_search(search_input, dependencies)
    
    # Here, you would typically pass the results to the LLM for synthesis.
    # We will return the raw results for now.
    
    # Let's create a synthesized response using the LLM
    model_name = get_llm_model_name()
    
    # Format results for the LLM
    if results:
        context = "\n\n".join([
            f"Document {i+1}:\n{result.get('content', '')}" 
            for i, result in enumerate(results)
        ])
    else:
        context = "No relevant documents found."

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"User query: {query}\n\nContext:\n{context}"},
                {"role": "assistant", "content": "Based on the provided context, here is the answer:"}
            ],
            stream=False
        )
        # Extract the content properly
        result = response.choices[0].message.content
        logger.info(f"LLM response type: {type(result)}, content: {result[:100] if isinstance(result, str) else str(result)[:100]}")
        return result if isinstance(result, str) else str(result)
    except Exception as e:
        logger.error(f"LLM call failed in run_agent_reasoning: {e}")
        return f"Sorry, I encountered an error processing your request: {str(e)}"


# --- Tool Functions (Refactored from Agent Tools) ---

async def vector_search(
    input_data: VectorSearchInput, 
    dependencies: AgentDependencies
) -> List[Dict[str, Any]]:
    """
    Performs vector similarity search.
    """
    results = await vector_search_tool(input_data)
    results_as_dict = [
        {
            "content": r.content,
            "score": r.score,
            "document_title": r.document_title,
            "document_source": r.document_source,
            "chunk_id": r.chunk_id
        }
        for r in results
    ]
    dependencies.retrieved_contexts.extend(results_as_dict)
    return results_as_dict


async def graph_search(
    input_data: GraphSearchInput,
    dependencies: AgentDependencies
) -> List[Dict[str, Any]]:
    """
    Searches the knowledge graph.
    """
    results = await graph_search_tool(input_data)
    results_as_dict = [
        {
            "fact": r.fact,
            "uuid": r.uuid,
            "valid_at": r.valid_at,
            "invalid_at": r.invalid_at,
            "source_node_uuid": r.source_node_uuid
        }
        for r in results
    ]
    dependencies.retrieved_contexts.extend(results_as_dict)
    return results_as_dict


async def hybrid_search(
    input_data: HybridSearchInput,
    dependencies: AgentDependencies
) -> List[Dict[str, Any]]:
    """
    Performs hybrid search.
    """
    results = await hybrid_search_tool(input_data)
    results_as_dict = [
        {
            "content": r.content,
            "score": r.score,
            "document_title": r.document_title,
            "document_source": r.document_source,
            "chunk_id": r.chunk_id
        }
        for r in results
    ]
    dependencies.retrieved_contexts.extend(results_as_dict)
    return results_as_dict


async def get_document(
    input_data: DocumentInput
) -> Optional[Dict[str, Any]]:
    """
    Retrieves a specific document.
    """
    document = await get_document_tool(input_data)
    if document:
        return {
            "id": document["id"],
            "title": document["title"],
            "source": document["source"],
            "content": document["content"],
            "chunk_count": len(document.get("chunks", [])),
            "created_at": document["created_at"]
        }
    return None


async def list_documents(
    input_data: DocumentListInput
) -> List[Dict[str, Any]]:
    """
    Lists available documents.
    """
    documents = await list_documents_tool(input_data)
    return [
        {
            "id": d.id,
            "title": d.title,
            "source": d.source,
            "chunk_count": d.chunk_count,
            "created_at": d.created_at.isoformat()
        }
        for d in documents
    ]


async def get_entity_relationships(
    input_data: EntityRelationshipInput
) -> Dict[str, Any]:
    """
    Gets relationships for a specific entity.
    """
    return await get_entity_relationships_tool(input_data)


async def get_entity_timeline(
    input_data: EntityTimelineInput
) -> List[Dict[str, Any]]:
    """
g   Gets the timeline of facts for a specific entity.
    """
    return await get_entity_timeline_tool(input_data)


async def quiz_generator(
    input_data: QuizGeneratorInput
) -> Dict[str, Any]:
    """
    Generates an educational quiz.
    """
    quiz_result = await quiz_generator_tool(input_data)
    if "error" in quiz_result:
        return {
            "success": False,
            "error": quiz_result["error"],
            "topic": input_data.topic
        }
    return {
        "success": True,
        "topic": quiz_result["topic"],
        "difficulty_level": quiz_result["difficulty_level"],
        "num_questions": quiz_result["num_questions"],
        "questions": quiz_result["questions"],
        "sources_used": quiz_result["sources_used"],
        "generated_at": quiz_result["generated_at"]
    }

# Placeholder for the old rag_agent variable for compatibility
# This should be removed once all calling code is updated.
rag_agent = None