"""
FastAPI endpoints for the agentic RAG system.
"""

import os
import asyncio
import json
import logging
import time
import psutil
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path as FilePath
import uuid

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Depends,
    Request,
    status,
    Query,
    Path,
    Header,
    Body,
)
from starlette.websockets import WebSocketState
from fastapi.responses import JSONResponse, StreamingResponse
from .debug_logger import debug_logger
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn
from dotenv import load_dotenv
from pydantic import Field, ConfigDict, BaseModel, ValidationError
from starlette.websockets import WebSocketDisconnect

# Load environment variables from .env file
load_dotenv()

from .agent import run_agent_reasoning, AgentDependencies
from .db_utils import (
    initialize_database,
    close_database,
    create_session,
    get_session,
    add_message,
    get_session_messages,
    test_connection,
    # Document management
    create_document,
    get_document,
    update_document,
    delete_document,
    list_documents,
    get_document_count,
    # Session management
    list_sessions,
    get_session_count,
    delete_session,
    update_session
)
from .graph_utils import initialize_graph, close_graph, test_graph_connection
from .models import (
    ChatRequest,
    ChatResponse,
    SearchRequest,
    SearchResponse,
    StreamDelta,
    ErrorResponse,
    HealthStatus,
    ComponentStatus,
    SystemStatus,
    ToolCall,
    SearchType,
    WebSocketMessage,
    WebSocketResponse,
    LogEntry,
    LogBatch,
    # Document models
    DocumentCreateRequest,
    DocumentUpdateRequest,
    DocumentResponse,
    DocumentListResponse,
    # Session models
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    SessionListResponse
)
from .tools import (
    vector_search_tool,
    graph_search_tool,
    hybrid_search_tool,
    list_documents_tool,
    VectorSearchInput,
    GraphSearchInput,
    HybridSearchInput,
    DocumentListInput
)
from .auth_utils import (
    create_access_token, 
    authenticate_user, 
    blacklist_token,
    decode_token
)
from .models import LoginRequest, LoginResponse, TokenResponse, LogoutRequest

# Load environment variables
load_dotenv()

# --- Session Management ---
class SessionManager:
    """A simple in-memory session manager."""
    _instance = None
    _sessions: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance

    def get_or_create_session(self, session_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        if session_id and session_id in self._sessions:
            return session_id
        
        new_session_id = str(uuid.uuid4())
        self._sessions[new_session_id] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "history": []
        }
        logger.info(f"Created new session {new_session_id} for user {user_id}")
        return new_session_id

    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._sessions.get(session_id)

    def update_session_history(self, session_id: str, message: Dict[str, Any]):
        if session_id in self._sessions:
            self._sessions[session_id]["history"].append(message)

# --- FastAPI App Initialization ---
logger = logging.getLogger(__name__)

# Application configuration
APP_ENV = os.getenv("APP_ENV", "development")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# Application startup time for uptime calculation
start_time = time.time()

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set debug level for our module during development
if APP_ENV == "development":
    logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup
    logger.info("Starting up agentic RAG API...")
    
    try:
        # Database connectivity restored! Re-enabling full initialization
        logger.info("Starting full database initialization...")
        
        # Initialize database connections
        await initialize_database()
        logger.info("Database initialized")
        
        # Initialize graph database
        await initialize_graph()
        logger.info("Graph database initialized")
        
        # Test connections
        db_ok = await test_connection()
        graph_ok = await test_graph_connection()
        
        if not db_ok:
            logger.error("Database connection failed")
        if not graph_ok:
            logger.error("Graph database connection failed")
        
        logger.info("Agentic RAG API startup complete (full production mode)")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down agentic RAG API...")
    
    try:
        # await close_database()
        # await close_graph()
        logger.info("Connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI app
app = FastAPI(
    title="Agentic RAG with Knowledge Graph for Physiotherapy",
    description="AI agent combining vector search and knowledge graph for medical education in physiotherapy",
    version="1.0.0",
    lifespan=lifespan
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log detailed validation errors."""
    body = await request.body()
    logger.error(f"Validation error for request body: {body.decode()}")
    logger.error(f"Validation error details: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# Add middleware with flexible CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Helper functions for agent execution
async def get_or_create_session(request: ChatRequest) -> str:
    """Get existing session or create new one."""
    if request.session_id:
        session = await get_session(request.session_id)
        if session:
            return request.session_id
    
    # Create new session
    return await create_session(
        user_id=request.user_id,
        metadata=request.metadata
    )


async def get_conversation_context(
    session_id: str,
    max_messages: int = 10
) -> List[Dict[str, str]]:
    """
    Get recent conversation context.
    
    Args:
        session_id: Session ID
        max_messages: Maximum number of messages to retrieve
    
    Returns:
        List of messages
    """
    messages = await get_session_messages(session_id, limit=max_messages)
    
    return [
        {
            "role": msg["role"],
            "content": msg["content"]
        }
        for msg in messages
    ]


async def save_conversation_turn(
    session_id: str,
    user_message: str,
    assistant_message: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Save a conversation turn to the database.
    
    Args:
        session_id: Session ID
        user_message: User's message
        assistant_message: Assistant's response
        metadata: Optional metadata
    """
    # Save user message
    await add_message(
        session_id=session_id,
        role="user",
        content=user_message,
        metadata=metadata or {}
    )
    
    # Save assistant message
    await add_message(
        session_id=session_id,
        role="assistant",
        content=assistant_message,
        metadata=metadata or {}
    )


# ========================================
# HEALTH CHECK AND SYSTEM STATUS ENDPOINTS  
# ========================================

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint with detailed component status."""
    try:
        start_check_time = time.time()
        
        # Test database connections with timing
        db_start = time.time()
        db_status = await test_connection()
        db_time = (time.time() - db_start) * 1000
        
        # Test graph database with timing  
        graph_start = time.time()
        graph_status = await test_graph_connection()
        graph_time = (time.time() - graph_start) * 1000
        
        # Create detailed component status
        components = [
            ComponentStatus(
                name="database",
                status="healthy" if db_status else "unhealthy",
                response_time_ms=db_time,
                details={"connection_pool": "active"} if db_status else {"error": "connection_failed"}
            ),
            ComponentStatus(
                name="graph_database",
                status="healthy" if graph_status else "unhealthy", 
                response_time_ms=graph_time,
                details={"neo4j_connection": "active"} if graph_status else {"error": "connection_failed"}
            ),
            ComponentStatus(
                name="llm_connection",
                status="healthy",  # Assume OK if we can respond
                response_time_ms=0.0,
                details={"model": os.getenv("LLM_CHOICE", "gpt-4o-mini")}
            )
        ]
        
        # Determine overall status
        if db_status and graph_status:
            status = "healthy"
        elif db_status or graph_status:
            status = "degraded"
        else:
            status = "unhealthy"
        
        # Calculate uptime
        uptime = time.time() - start_time
        
        return HealthStatus(
            status=status,
            database=db_status,
            graph_database=graph_status,
            llm_connection=True,
            version=APP_VERSION,
            timestamp=datetime.now(),
            components=components,
            uptime_seconds=uptime
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.get("/status", response_model=SystemStatus)
async def system_status():
    """Comprehensive system status endpoint."""
    try:
        # Get memory usage
        process = psutil.Process()
        memory_info = process.memory_info()
        
        memory_usage = {
            "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
            "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
            "percent": round(process.memory_percent(), 2)
        }
        
        # Test all components with detailed timing
        components = []
        
        # Database component
        db_start = time.time()
        try:
            db_status = await test_connection()
            db_time = (time.time() - db_start) * 1000
            components.append(ComponentStatus(
                name="postgresql",
                status="healthy" if db_status else "unhealthy",
                response_time_ms=db_time,
                details={
                    "schema": os.getenv("DB_SCHEMA", "public"),
                    "pool_size": "5-20 connections"
                }
            ))
        except Exception as e:
            components.append(ComponentStatus(
                name="postgresql", 
                status="unhealthy",
                details={"error": str(e)}
            ))
        
        # Graph database component
        graph_start = time.time()
        try:
            graph_status = await test_graph_connection()
            graph_time = (time.time() - graph_start) * 1000
            components.append(ComponentStatus(
                name="neo4j",
                status="healthy" if graph_status else "unhealthy",
                response_time_ms=graph_time,
                details={
                    "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                    "graphiti_initialized": graph_status
                }
            ))
        except Exception as e:
            components.append(ComponentStatus(
                name="neo4j",
                status="unhealthy", 
                details={"error": str(e)}
            ))
        
        # LLM component
        components.append(ComponentStatus(
            name="llm",
            status="healthy",  # Assume healthy if we can respond
            details={
                "model": os.getenv("LLM_CHOICE", "gpt-4o-mini"),
                "base_url": os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
            }
        ))
        
        # Embedding component
        components.append(ComponentStatus(
            name="embeddings",
            status="healthy",
            details={
                "model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                "dimensions": int(os.getenv("VECTOR_DIMENSION", "1536"))
            }
        ))
        
        # Get basic statistics (document and session counts)
        try:
            doc_count = await get_document_count()
            session_count = await get_session_count()
            statistics = {
                "total_documents": doc_count,
                "total_sessions": session_count,
                "active_sessions": await get_session_count(include_expired=False)
            }
        except Exception as e:
            logger.warning(f"Failed to get statistics: {e}")
            statistics = {"error": "Failed to retrieve statistics"}
        
        # Calculate uptime
        uptime = time.time() - start_time
        
        return SystemStatus(
            version=APP_VERSION,
            environment=APP_ENV,
            uptime_seconds=uptime,
            memory_usage=memory_usage,
            components=components,
            statistics=statistics
        )
        
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        raise HTTPException(status_code=500, detail="System status check failed")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint."""
    try:
        # Get or create session
        session_id = await get_or_create_session(request)
        
        # Create dependencies
        dependencies = AgentDependencies(session_id=session_id, user_id=request.user_id)

        # Execute agent reasoning
        response = await run_agent_reasoning(request.message, dependencies)
        
        # In this refactored version, tool calls are not explicitly returned by default.
        # This can be added back if needed by modifying run_agent_reasoning.
        tools_used = [] 

        await save_conversation_turn(
            session_id=session_id,
            user_message=request.message,
            assistant_message=response,
            metadata={
                "user_id": request.user_id,
                "tool_calls": len(tools_used)
            }
        )

        return ChatResponse(
            message=response,
            session_id=session_id,
            tools_used=tools_used,
            metadata={"search_type": str(request.search_type)}
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _stream_chat_response(request: ChatRequest):
    """Generate streaming response using the new instructor-based agent."""
    # Try to get session, but continue even if database unavailable
    try:
        session_id = await get_or_create_session(request)
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
    except Exception as e:
        logger.warning(f"Session creation failed (continuing without persistence): {e}")
        session_id = request.session_id or f"temp-session-{uuid.uuid4()}"
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

    try:
        dependencies = AgentDependencies(session_id=session_id, user_id=request.user_id)
        
        # Try to save user message, but continue if it fails
        try:
            await add_message(
                session_id=session_id,
                role="user",
                content=request.message,
                metadata={"user_id": request.user_id}
            )
            logger.debug("User message saved to database")
        except Exception as e:
            logger.warning(f"Failed to save user message (continuing without persistence): {e}")

        # Core AI reasoning - this works with Neo4j + OpenAI only
        try:
            logger.info(f"Calling run_agent_reasoning with message: {request.message[:100]}")
            full_response = await run_agent_reasoning(request.message, dependencies)
            if isinstance(full_response, str):
                logger.info(f"run_agent_reasoning returned: {full_response[:100] if full_response else 'None'}")
            else:
                logger.info(f"run_agent_reasoning returned non-string: {type(full_response)}")
                logger.info(f"Response content: {full_response}")
                # If it's a dict, try to extract the content
                if isinstance(full_response, dict):
                    full_response = full_response.get('content', str(full_response))
                else:
                    full_response = str(full_response)
        except Exception as e:
            logger.error(f"run_agent_reasoning failed: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            full_response = f"Sorry, I encountered an error: {str(e)}"
        
        # Simulate streaming for now
        words = full_response.split()
        for word in words:
            yield f"data: {json.dumps({'type': 'text', 'content': word + ' '})}\n\n"
            await asyncio.sleep(0.05) # Simulate processing time

        # The new agent doesn't expose tool calls or contexts in the same way.
        # This can be re-implemented if needed.
        contexts = dependencies.retrieved_contexts
        if contexts:
            yield f"data: {json.dumps({'type': 'contexts', 'contexts': contexts})}\n\n"

        # Try to save assistant response, but continue if it fails
        try:
            await add_message(
                session_id=session_id,
                role="assistant",
                content=full_response,
                metadata={
                    "streamed": True,
                    "tool_calls": 0, # Placeholder
                    "retrieved_contexts_count": len(contexts)
                }
            )
            logger.debug("Assistant message saved to database")
        except Exception as e:
            logger.warning(f"Failed to save assistant message (continuing without persistence): {e}")
        
        yield f"data: {json.dumps({'type': 'completed'})}\n\n"

    except Exception as e:
        logger.error(f"Stream error: {e}")
        error_chunk = {
            "type": "error",
            "content": f"Stream error: {str(e)}"
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"

@app.post("/chat/stream", response_model=ChatResponse)
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint using Server-Sent Events."""
    try:
        return StreamingResponse(
            _stream_chat_response(request),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
    except Exception as e:
        logger.error(f"Streaming chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/vector")
async def search_vector(request: SearchRequest):
    """Vector search endpoint."""
    try:
        input_data = VectorSearchInput(
            query=request.query,
            limit=request.limit
        )
        
        start_time = datetime.now()
        results = await vector_search_tool(input_data)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            results=results,
            total_results=len(results),
            search_type="vector",
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/graph")
async def search_graph(request: SearchRequest):
    """Knowledge graph search endpoint."""
    try:
        input_data = GraphSearchInput(
            query=request.query
        )
        
        start_time = datetime.now()
        results = await graph_search_tool(input_data)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            graph_results=results,
            total_results=len(results),
            search_type="graph",
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Graph search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/hybrid")
async def search_hybrid(request: SearchRequest):
    """Hybrid search endpoint."""
    try:
        input_data = HybridSearchInput(
            query=request.query,
            limit=request.limit
        )
        
        start_time = datetime.now()
        results = await hybrid_search_tool(input_data)
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            results=results,
            total_results=len(results),
            search_type="hybrid",
            query_time_ms=query_time
        )
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# SEARCH FUNCTIONALITY ENDPOINTS
# ========================================

@app.post("/search", response_model=SearchResponse)
async def unified_search(request: SearchRequest):
    """Unified search endpoint that supports all search types."""
    try:
        start_time = datetime.now()
        
        if request.search_type == SearchType.VECTOR:
            # Vector search
            input_data = VectorSearchInput(
                query=request.query,
                limit=request.limit
            )
            results = await vector_search_tool(input_data)
            
            return SearchResponse(
                results=results,
                total_results=len(results),
                search_type="vector",
                query_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        elif request.search_type == SearchType.GRAPH:
            # Graph search
            input_data = GraphSearchInput(
                query=request.query
            )
            results = await graph_search_tool(input_data)
            
            return SearchResponse(
                graph_results=results,
                total_results=len(results),
                search_type="graph",
                query_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        else:  # HYBRID
            # Hybrid search
            input_data = HybridSearchInput(
                query=request.query,
                limit=request.limit
            )
            results = await hybrid_search_tool(input_data)
            
            return SearchResponse(
                results=results,
                total_results=len(results),
                search_type="hybrid",
                query_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
    except Exception as e:
        logger.error(f"Unified search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Additional specialized search endpoints for backward compatibility
@app.get("/search/vector", response_model=SearchResponse)
async def search_vector_get(
    query: str = Query(..., description="Search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum results")
):
    start_time = datetime.now()
    input_data = VectorSearchInput(query=query, limit=limit)
    results = await vector_search_tool(input_data)
    return SearchResponse(
        results=results,
        total_results=len(results),
        search_type=SearchType.VECTOR,
        query_time_ms=(datetime.now() - start_time).total_seconds() * 1000
    )

@app.get("/search/graph", response_model=SearchResponse)
async def search_graph_get(
    query: str = Query(..., description="Search query")
):
    start_time = datetime.now()
    input_data = GraphSearchInput(query=query)
    results = await graph_search_tool(input_data)
    return SearchResponse(
        graph_results=results,
        total_results=len(results),
        search_type=SearchType.GRAPH,
        query_time_ms=(datetime.now() - start_time).total_seconds() * 1000
    )

@app.get("/search/hybrid", response_model=SearchResponse)
async def search_hybrid_get(
    query: str = Query(..., description="Search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum results")
):
    start_time = datetime.now()
    input_data = HybridSearchInput(query=query, limit=limit)
    results = await hybrid_search_tool(input_data)
    return SearchResponse(
        results=results,
        total_results=len(results),
        search_type=SearchType.HYBRID,
        query_time_ms=(datetime.now() - start_time).total_seconds() * 1000
    )


# Enhanced document endpoints
@app.get("/documents/{document_id}/chunks")
async def get_document_chunks_endpoint(
    document_id: str = Path(..., description="Document ID")
):
    """Get all chunks for a specific document."""
    try:
        # Check if document exists
        document = await get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get chunks
        from .db_utils import get_document_chunks
        chunks = await get_document_chunks(document_id)
        
        return {
            "document_id": document_id,
            "document_title": document["title"],
            "chunks": chunks,
            "total_chunks": len(chunks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document chunks retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Debug endpoints
@app.post("/api/frontend-logs")
async def receive_frontend_logs(request: Request):
    """Riceve e salva i log dal frontend"""
    try:
        body = await request.json()
        logs = body.get("logs", [])
        
        date_str = datetime.utcnow().strftime("%Y%m%d")
        log_file = FilePath("logs/frontend") / f"events_{date_str}.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, "a", encoding="utf-8") as f:
            for log_entry in logs:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        return {"status": "success", "logs_received": len(logs)}
    except Exception as e:
        logger.error(f"Error receiving frontend logs: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/debug/last-request")
async def get_last_request_trace():
    """Ottieni il trace dell'ultima richiesta per debug"""
    trace = debug_logger.get_last_request_trace()
    if trace:
        return trace
    raise HTTPException(status_code=404, detail="No request trace found")

@app.get("/api/debug/health")
async def debug_health_check():
    """Health check dettagliato con stato di ogni componente"""
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy",
        "components": {}
    }
    
    # Check Neo4j
    try:
        from .graph_utils import neo4j_driver
        with neo4j_driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()
        health_status["components"]["neo4j"] = {
            "status": "healthy",
            "message": "Connected and responsive"
        }
    except Exception as e:
        health_status["components"]["neo4j"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check PostgreSQL
    try:
        from .db_utils import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        health_status["components"]["postgresql"] = {
            "status": "healthy",
            "message": "Connected and responsive"
        }
    except Exception as e:
        health_status["components"]["postgresql"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check OpenAI
    try:
        test_embedding = await generate_embedding("test")
        health_status["components"]["openai"] = {
            "status": "healthy",
            "message": "API responding"
        }
    except Exception as e:
        health_status["components"]["openai"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Add request trace info
    last_trace = debug_logger.get_last_request_trace()
    if last_trace:
        health_status["last_request"] = {
            "request_id": last_trace.get("request_id"),
            "timestamp": last_trace.get("start_time"),
            "phases": len(last_trace.get("phases", []))
        }
    
    return health_status


# Graph-specific endpoints
@app.get("/graph/entities/{entity_name}")
async def get_entity_relationships_endpoint(
    entity_name: str = Path(..., description="Entity name"),
    depth: int = Query(default=2, ge=1, le=5, description="Relationship depth")
):
    """Get relationships for a specific entity."""
    try:
        from .graph_utils import get_entity_relationships
        relationships = await get_entity_relationships(entity_name, depth=depth)
        
        return {
            "entity": entity_name,
            "depth": depth,
            "relationships": relationships
        }
        
    except Exception as e:
        logger.error(f"Entity relationships retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/statistics")
async def get_graph_statistics():
    """Get knowledge graph statistics."""
    try:
        from .graph_utils import graph_client
        stats = await graph_client.get_graph_statistics()
        
        return {
            "graph_statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Graph statistics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


LOG_FILE_PATH = "logs/frontend.log"

@app.post("/log")
async def receive_log(batch: LogBatch):
    """Receive a batch of logs from the frontend and write to a file."""
    try:
        log_dir = os.path.dirname(LOG_FILE_PATH)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            for log in batch.logs:
                log_line = f"[{log.timestamp.isoformat()}] [{log.level.upper()}] {log.message}\\n"
                f.write(log_line)
        
        return {"status": "ok", "received_logs": len(batch.logs)}
    except Exception as e:
        logger.error(f"Failed to process and write logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to process and write logs")


# ========================================
# DOCUMENT MANAGEMENT ENDPOINTS
# ========================================

@app.post("/documents", response_model=DocumentResponse, status_code=201)
async def create_document_endpoint(request: DocumentCreateRequest):
    """Create a new document."""
    try:
        document_id = await create_document(
            title=request.title,
            content=request.content,
            source=request.source,
            metadata=request.metadata
        )
        
        # Fetch the created document to return complete data
        document = await get_document(document_id)
        if not document:
            raise HTTPException(status_code=500, detail="Failed to retrieve created document")
        
        return DocumentResponse(
            id=document["id"],
            title=document["title"],
            source=document["source"],
            content=document["content"],
            metadata=document["metadata"],
            created_at=document["created_at"],
            updated_at=document["updated_at"]
        )
        
    except Exception as e:
        logger.error(f"Document creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document_endpoint(document_id: str = Path(..., description="Document ID")):
    """Get a document by ID."""
    try:
        document = await get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse(
            id=document["id"],
            title=document["title"],
            source=document["source"],
            content=document["content"],
            metadata=document["metadata"],
            created_at=document["created_at"],
            updated_at=document["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document_endpoint(
    request: DocumentUpdateRequest,
    document_id: str = Path(..., description="Document ID")
):
    """Update a document."""
    try:
        # Check if document exists
        existing_document = await get_document(document_id)
        if not existing_document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Update document
        updated = await update_document(
            document_id=document_id,
            title=request.title,
            content=request.content,
            source=request.source,
            metadata=request.metadata
        )
        
        if not updated:
            raise HTTPException(status_code=404, detail="Document not found or no changes made")
        
        # Fetch updated document
        document = await get_document(document_id)
        return DocumentResponse(
            id=document["id"],
            title=document["title"],
            source=document["source"],
            content=document["content"],
            metadata=document["metadata"],
            created_at=document["created_at"],
            updated_at=document["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}", status_code=204)
async def delete_document_endpoint(document_id: str = Path(..., description="Document ID")):
    """Delete a document."""
    try:
        deleted = await delete_document(document_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents", response_model=DocumentListResponse)
async def list_documents_endpoint(
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of documents"),
    offset: int = Query(default=0, ge=0, description="Number of documents to skip"),
    metadata_filter: Optional[str] = Query(default=None, description="JSON metadata filter")
):
    """List documents with pagination and filtering."""
    try:
        # Parse metadata filter if provided
        parsed_filter = None
        if metadata_filter:
            try:
                parsed_filter = json.loads(metadata_filter)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in metadata_filter")
        
        # Get documents and total count
        documents = await list_documents(
            limit=limit,
            offset=offset,
            metadata_filter=parsed_filter
        )
        
        total = await get_document_count(metadata_filter=parsed_filter)
        
        document_responses = [
            DocumentResponse(
                id=doc["id"],
                title=doc["title"],
                source=doc["source"],
                metadata=doc["metadata"],
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
                chunk_count=doc["chunk_count"]
            )
            for doc in documents
        ]
        
        return DocumentListResponse(
            documents=document_responses,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# SESSION MANAGEMENT ENDPOINTS
# ========================================

@app.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session_endpoint(request: SessionCreateRequest):
    """Create a new session."""
    try:
        session_id = await create_session(
            user_id=request.user_id,
            metadata=request.metadata,
            timeout_minutes=request.timeout_minutes
        )
        
        # Fetch the created session to return complete data
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=500, detail="Failed to retrieve created session")
        
        return SessionResponse(
            id=session["id"],
            user_id=session["user_id"],
            metadata=session["metadata"],
            created_at=datetime.fromisoformat(session["created_at"]),
            updated_at=datetime.fromisoformat(session["updated_at"]),
            expires_at=datetime.fromisoformat(session["expires_at"]) if session["expires_at"] else None,
            message_count=0
        )
        
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_info(session_id: str = Path(..., description="Session ID")):
    """Get session information."""
    try:
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get message count for this session
        messages = await get_session_messages(session_id)
        
        return SessionResponse(
            id=session["id"],
            user_id=session["user_id"],
            metadata=session["metadata"],
            created_at=datetime.fromisoformat(session["created_at"]),
            updated_at=datetime.fromisoformat(session["updated_at"]),
            expires_at=datetime.fromisoformat(session["expires_at"]) if session["expires_at"] else None,
            message_count=len(messages)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session_endpoint(
    request: SessionUpdateRequest,
    session_id: str = Path(..., description="Session ID")
):
    """Update session metadata."""
    try:
        # Check if session exists
        existing_session = await get_session(session_id)
        if not existing_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update session
        updated = await update_session(session_id, request.metadata)
        if not updated:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Fetch updated session
        session = await get_session(session_id)
        messages = await get_session_messages(session_id)
        
        return SessionResponse(
            id=session["id"],
            user_id=session["user_id"],
            metadata=session["metadata"],
            created_at=datetime.fromisoformat(session["created_at"]),
            updated_at=datetime.fromisoformat(session["updated_at"]),
            expires_at=datetime.fromisoformat(session["expires_at"]) if session["expires_at"] else None,
            message_count=len(messages)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}", status_code=204)
async def delete_session_endpoint(session_id: str = Path(..., description="Session ID")):
    """Delete a session and its messages."""
    try:
        deleted = await delete_session(session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions", response_model=SessionListResponse)
async def list_sessions_endpoint(
    user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of sessions"),
    offset: int = Query(default=0, ge=0, description="Number of sessions to skip"),
    include_expired: bool = Query(default=False, description="Include expired sessions")
):
    """List sessions with pagination and filtering."""
    try:
        # Get sessions and total count
        sessions = await list_sessions(
            user_id=user_id,
            limit=limit,
            offset=offset,
            include_expired=include_expired
        )
        
        total = await get_session_count(
            user_id=user_id,
            include_expired=include_expired
        )
        
        session_responses = [
            SessionResponse(
                id=session["id"],
                user_id=session["user_id"],
                metadata=session["metadata"],
                created_at=datetime.fromisoformat(session["created_at"]),
                updated_at=datetime.fromisoformat(session["updated_at"]),
                expires_at=datetime.fromisoformat(session["expires_at"]) if session["expires_at"] else None,
                message_count=session["message_count"]
            )
            for session in sessions
        ]
        
        return SessionListResponse(
            sessions=session_responses,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Session listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/messages")
async def get_session_messages_endpoint(
    session_id: str = Path(..., description="Session ID"),
    limit: Optional[int] = Query(default=None, ge=1, le=1000, description="Maximum number of messages")
):
    """Get messages for a session."""
    try:
        # Check if session exists
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        messages = await get_session_messages(session_id, limit=limit)
        
        return {
            "session_id": session_id,
            "messages": messages,
            "total": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session messages retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket Endpoints
async def keep_alive(websocket: WebSocket):
    """Sends a ping message every 20 seconds to keep the connection alive."""
    while websocket.client_state == 'CONNECTED':
        try:
            await asyncio.sleep(20)
            if websocket.client_state == 'CONNECTED':
                await websocket.send_json(WebSocketResponse(
                    type="ping",
                    data={"message": "keep-alive"},
                ).model_dump(mode='json'))
                logger.debug("Sent keep-alive ping")
        except (WebSocketDisconnect, asyncio.CancelledError):
            logger.info("Keep-alive task stopped.")
            break
        except Exception as e:
            logger.warning(f"Error in keep-alive task: {e}")
            break

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("WebSocket endpoint called")
    await websocket.accept()
    logger.info("WebSocket connection accepted.")
    
    keep_alive_task = None
    try:
        logger.info("Starting WebSocket setup...")
        # Start keep-alive task
        keep_alive_task = asyncio.create_task(keep_alive(websocket))
        logger.info("Keep-alive task created")

        logger.info("Entering main message loop...")
        logger.info(f"Initial WebSocket state: {websocket.client_state}")
        
        async with debug_logger.websocket_request_context(str(websocket.client_state)) as request_id:
            # Send connection confirmation inside the request context
            logger.info(f"WebSocket client state: {websocket.client_state}")
            if websocket.client_state == WebSocketState.CONNECTED:
                logger.info("Sending connection confirmation...")
                confirmation = WebSocketResponse(
                    type="connected",
                    data={"message": "Connected to Fisio RAG Assistant"}
                )
                logger.info(f"Confirmation message created: {confirmation}")
                await websocket.send_json(confirmation.model_dump(mode='json'))
                logger.info("Connection confirmation sent successfully")
                debug_logger.log_backend_event(
                    request_id,
                    "confirmation_sent",
                    "Initial connection confirmation sent to client"
                )
            while True:
                current_state = websocket.client_state
                logger.info(f"Loop iteration - WebSocket state: {current_state}")
                debug_logger.log_backend_event(
                    request_id,
                    "websocket_loop",
                    f"WebSocket loop iteration, state: {current_state}"
                )
                
                if current_state != WebSocketState.CONNECTED:
                    logger.info(f"WebSocket not connected (state: {current_state}), exiting loop")
                    debug_logger.log_backend_event(
                        request_id,
                        "websocket_disconnect",
                        f"WebSocket disconnected with state: {current_state}"
                    )
                    break
                # Use receive_text() for robust UTF-8 handling
                logger.info("WebSocket waiting for message...")
                try:
                    message_text = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    logger.info(f"WebSocket received message: {message_text[:200]}...")
                    debug_logger.log_backend_event(
                        request_id,
                        "message_received",
                        f"Received message of length {len(message_text)}",
                        {"preview": message_text[:200]}
                    )
                except asyncio.TimeoutError:
                    logger.info("WebSocket timeout waiting for message, continuing...")
                    continue
                except Exception as e:
                    logger.error(f"Error receiving WebSocket message: {e}")
                    debug_logger.log_backend_event(
                        request_id,
                        "message_receive_error",
                        "Failed to receive message",
                        error=e
                    )
                    break
                
                try:
                    # Manually parse JSON after receiving text
                    data = json.loads(message_text)
                    logger.info(f"JSON parsed successfully, message type: {data.get('type', 'unknown')}")
                    message = WebSocketMessage.model_validate(data)
                    logger.info("WebSocket message validation successful")
                    debug_logger.log_backend_event(
                        request_id,
                        "message_parsed",
                        f"Message parsed: type={data.get('type')}",
                        {"message_type": data.get('type'), "has_data": bool(data.get('data'))}
                    )
                    
                    # Process validated message (MOVED INSIDE TRY BLOCK)
                    session_id = message.session_id
                    user_id = message.user_id
                    logger.info(f"Processing message type: {message.type}, session: {session_id}, user: {user_id}")

                    if message.type == "ping":
                        logger.info("Handling ping message")
                        if websocket.client_state == 'CONNECTED':
                            await websocket.send_json(WebSocketResponse(
                                type="message",
                                data={"message": "pong"},
                                session_id=session_id
                            ).model_dump(mode='json'))

                    elif message.type == "chat":
                        logger.info("Handling chat message")
                        chat_data = message.data
                        chat_request = ChatRequest(
                        message=chat_data.get("message", ""),
                        session_id=session_id,
                        user_id=user_id,
                        metadata=chat_data.get("metadata", {}),
                        search_type=SearchType(chat_data.get("search_type", "hybrid"))
                        )
                        logger.info(f"ChatRequest created: {chat_request.message}")
                        debug_logger.log_backend_event(
                            request_id,
                            "chat_request_created",
                            f"Processing chat message: {chat_request.message[:100]}",
                            {"session_id": session_id, "user_id": user_id}
                        )
                        try:
                            logger.info("Starting _stream_chat_response...")
                            debug_logger.log_backend_event(
                                request_id,
                                "stream_start",
                                "Starting response stream"
                            )
                            chunk_count = 0
                            async for chunk in _stream_chat_response(chat_request):
                                chunk_count += 1
                            logger.info(f"Received chunk {chunk_count}: {chunk[:100]}...")
                            debug_logger.log_backend_event(
                                request_id,
                                "stream_chunk",
                                f"Chunk {chunk_count} received",
                                {"chunk_size": len(chunk), "preview": chunk[:100]}
                            )
                            if websocket.client_state != 'CONNECTED':
                                logger.warning("Client disconnected during stream, stopping.")
                                break
                            if chunk.startswith("data: "):
                                chunk_data = chunk[6:].strip()
                                if chunk_data:
                                    try:
                                        parsed_chunk = json.loads(chunk_data)
                                        if websocket.client_state == 'CONNECTED':
                                            # Extract just the data part, not the whole chunk
                                            chunk_type = parsed_chunk.get("type", "chunk")
                                            chunk_content = parsed_chunk.get("content", "")
                                            chunk_contexts = parsed_chunk.get("contexts", None)
                                            
                                            # Build appropriate data based on type
                                            if chunk_type == "text":
                                                response_data = {"content": chunk_content}
                                            elif chunk_type == "contexts":
                                                response_data = {"contexts": chunk_contexts}
                                            elif chunk_type == "session":
                                                response_data = {"session_id": parsed_chunk.get("session_id")}
                                            else:
                                                response_data = parsed_chunk
                                            
                                            await websocket.send_json(WebSocketResponse(
                                                type=chunk_type,
                                                data=response_data,
                                                session_id=session_id,
                                                request_id=str(uuid.uuid4())
                                            ).model_dump(mode='json'))
                                    except json.JSONDecodeError:
                                        logger.warning(f"Failed to parse JSON chunk: {chunk_data}")
                                        pass

                            if websocket.client_state == 'CONNECTED':
                                await websocket.send_json(WebSocketResponse(
                                    type="completed",
                                    data={"message": "Stream completed"},
                                    session_id=session_id
                                ).model_dump(mode='json'))

                        except Exception as e:
                            logger.error(f"Error during chat streaming: {e}")
                            if websocket.client_state == 'CONNECTED':
                                await websocket.send_json(WebSocketResponse(
                                    type="error",
                                    data={"error": str(e)},
                                    session_id=session_id
                                ).model_dump(mode='json'))

                except (json.JSONDecodeError, ValidationError) as e:
                    logger.error(f"WebSocket message validation error: {e}")
                    debug_logger.log_backend_event(
                        request_id,
                        "validation_error",
                        "Message validation failed",
                        error=e
                    )
                    if websocket.client_state == 'CONNECTED':
                        error_response = WebSocketResponse(
                            type="error",
                            data={"error": "Invalid message format", "details": str(e)}
                        )
                        await websocket.send_json(error_response.model_dump(mode='json'))
                    continue

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed by client.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the WebSocket endpoint: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        if websocket.client_state == 'CONNECTED':
            try:
                await websocket.close(code=1011)
            except Exception as close_exc:
                logger.error(f"Failed to close WebSocket gracefully: {close_exc}")
    finally:
        if keep_alive_task and not keep_alive_task.done():
            keep_alive_task.cancel()
            logger.info("Keep-alive task cancelled.")


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    
    return ErrorResponse(
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=str(uuid.uuid4())
    )


# Development server
if __name__ == "__main__":
    # Forcing IPv4 host to avoid Windows localhost resolution issues
    run_host = "127.0.0.1" if APP_HOST == "0.0.0.0" else APP_HOST
    
    uvicorn.run(
        "agent.api:app",
        host=run_host,  # CORRECTED: Use the stable localhost IP for Windows dev
        port=APP_PORT,
        log_level=LOG_LEVEL.lower(),
        reload=(APP_ENV == "development")
    )

# Authentication endpoints
@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Authenticate user and return JWT token.
    
    - **username**: User's username
    - **password**: User's password
    
    Returns JWT token and user information.
    """
    start_time = time.time()
    
    # Authenticate user
    user = await authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    token_data = await create_access_token(user["id"], user["username"])
    
    # TEMPORARY: Skip session creation for AUTH-02 testing (no database available)
    # session_id = await create_session(user["id"], {
    #     "login_method": "password",
    #     "user_agent": "Unknown"
    # })
    session_id = "temp-session-id"  # Temporary session ID for testing
    
    response_time = time.time() - start_time
    logger.info(f"User {user['username']} logged in successfully in {response_time:.3f}s")
    
    return LoginResponse(
        token=TokenResponse(
            access_token=token_data["access_token"],
            token_type="bearer",
            expires_in=token_data["expires_in"]
        ),
        user={
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "is_superuser": user["is_superuser"]
        },
        session_id=session_id
    )

@app.post("/auth/logout", status_code=204)
async def logout(
    authorization: str = Header(None),
    request: LogoutRequest = Body(...)
):
    """
    Logout user and invalidate JWT token.
    
    - **Authorization**: Bearer token in header
    - **session_id**: Optional session ID to invalidate
    
    Adds token to blacklist and optionally invalidates session.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    
    try:
        # Decode token to get user info
        payload = await decode_token(token)
        user_id = payload["sub"]
        jti = payload["jti"]
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        
        # Blacklist the token
        await blacklist_token(jti, user_id, expires_at)
        
        # Optionally invalidate session
        if request.session_id:
            await delete_session(request.session_id)
        
        logger.info(f"User {payload['username']} logged out successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during logout"
        )