"""
Database utilities for PostgreSQL connection and operations.
"""

import asyncio
import asyncpg
import logging
import os
import json
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

pool = None
DATABASE_URL = os.getenv("DATABASE_URL")

async def get_pool():
    """Get database pool with robust retry logic, creating it if it doesn't exist (lazy loading)."""
    global pool
    if pool is None:
        max_retries = 3
        base_delay = 1.0  # Start with 1 second
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Creating database pool (attempt {attempt + 1}/{max_retries})...")
                
                # Reduced pool size for Neon database compatibility
                pool = await asyncpg.create_pool(
                    DATABASE_URL,
                    min_size=1,  # Reduced from 5 for Neon compatibility
                    max_size=5,  # Reduced from 20 for Neon compatibility  
                    server_settings={'search_path': 'staging'},
                    command_timeout=30  # 30 second timeout for commands
                )
                logger.info("Database connection pool created successfully (Neon-compatible settings)")

                # Test the pool with a simple query
                async with pool.acquire() as connection:
                    await connection.fetchval("SELECT 1")
                    logger.info("Database pool health check successful")

                # Initialize extensions and schema on first successful connection
                await _initialize_database_schema(pool)
                
                return pool
                
            except Exception as e:
                logger.warning(f"Database pool creation attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Failed to create database pool after {max_retries} attempts")
                    pool = None
                    raise
    
    return pool

async def _initialize_database_schema(db_pool):
    """Initialize database extensions and schema (separate function for clarity)."""
    try:
        async with db_pool.acquire() as connection:
            # Enable required extensions in a dedicated transaction
            logger.info("Enabling required database extensions...")
            await connection.execute("""
                START TRANSACTION;
                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                CREATE EXTENSION IF NOT EXISTS "pg_trgm";
                CREATE EXTENSION IF NOT EXISTS "vector";
                COMMIT;
            """)
            logger.info("Database extensions enabled successfully.")

            # Apply main schema
            logger.info("Applying database schema...")
            schema_path = Path(__file__).parent.parent / "sql" / "schema.sql"
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            await connection.execute(schema_sql)
            logger.info("Database schema applied successfully.")
            
    except Exception as e:
        logger.error(f"Error initializing database schema: {e}")
        # Don't re-raise - schema might already exist
        logger.info("Continuing despite schema initialization error (might already exist)")

async def initialize_database():
    """Initializes the database configuration, but defers pool creation to first use."""
    global pool
    logger.info("Database initialization configured (lazy loading mode for Neon compatibility)")
    logger.info("Pool will be created on first database access with retry logic")
    # Pool creation is now deferred to get_pool() function

async def get_db_connection():
    """Gets a database connection from the pool, creating pool if needed."""
    current_pool = await get_pool()
    return await current_pool.acquire()

def release_db_connection(connection):
    """Releases a connection back to the pool."""
    if pool:
        # Use a task to run release in the background
        # asyncio.create_task(pool.release(connection))
        # For now, let's do it directly for simplicity in some contexts
        # but be aware of blocking in async code.
        # This part might need refinement based on invocation context.
        pass # Simplified for now

async def close_database():
    """Closes the database connection pool."""
    global pool
    if pool:
        await pool.close()
        pool = None
        logger.info("Database connection pool closed.")


# Session Management Functions
async def create_session(
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timeout_minutes: int = 60
) -> str:
    """
    Create a new session.
    
    Args:
        user_id: Optional user ID to associate with session
        metadata: Optional metadata dict
        timeout_minutes: Session timeout in minutes
        
    Returns:
        Session ID string
    """
    session_id = str(uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes)
    
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO sessions (id, user_id, metadata, expires_at)
            VALUES ($1, $2, $3, $4)
            RETURNING id::text
            """,
            UUID(session_id),
            user_id,
            json.dumps(metadata or {}),
            expires_at
        )
        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id


async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get session by ID.
    
    Args:
        session_id: Session UUID
    
    Returns:
        Session data or None if not found/expired
    """
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT 
                id::text,
                user_id,
                metadata,
                created_at,
                updated_at,
                expires_at
            FROM sessions
            WHERE id = $1::uuid
            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """,
            session_id
        )
        
        if result:
            return {
                "id": result["id"],
                "user_id": result["user_id"],
                "metadata": json.loads(result["metadata"]),
                "created_at": result["created_at"].isoformat(),
                "updated_at": result["updated_at"].isoformat(),
                "expires_at": result["expires_at"].isoformat() if result["expires_at"] else None
            }
        
        return None


async def update_session(session_id: str, metadata: Dict[str, Any]) -> bool:
    """
    Update session metadata.
    
    Args:
        session_id: Session UUID
        metadata: New metadata to merge
    
    Returns:
        True if updated, False if not found
    """
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE sessions
            SET metadata = metadata || $2::jsonb
            WHERE id = $1::uuid
            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """,
            session_id,
            json.dumps(metadata)
        )
        
        return result.split()[-1] != "0"


# Message Management Functions
async def add_message(
    session_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Add a message to a session.
    
    Args:
        session_id: Session UUID
        role: Message role (user/assistant/system)
        content: Message content
        metadata: Optional message metadata
    
    Returns:
        Message ID
    """
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO messages (session_id, role, content, metadata)
            VALUES ($1::uuid, $2, $3, $4)
            RETURNING id::text
            """,
            session_id,
            role,
            content,
            json.dumps(metadata or {})
        )
        
        return result["id"]


async def get_session_messages(
    session_id: str,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get messages for a session.
    
    Args:
        session_id: Session UUID
        limit: Maximum number of messages to return
    
    Returns:
        List of messages ordered by creation time
    """
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        query = """
            SELECT 
                id::text,
                role,
                content,
                metadata,
                created_at
            FROM messages
            WHERE session_id = $1::uuid
            ORDER BY created_at
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        results = await conn.fetch(query, session_id)
        
        return [
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"]),
                "created_at": row["created_at"].isoformat()
            }
            for row in results
        ]


# Document Management Functions
async def get_document(document_id: str) -> Optional[Dict[str, Any]]:
    """
    Get document by ID.
    
    Args:
        document_id: Document UUID
    
    Returns:
        Document data or None if not found
    """
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT 
                id::text,
                title,
                source,
                content,
                metadata,
                created_at,
                updated_at
            FROM documents
            WHERE id = $1::uuid
            """,
            document_id
        )
        
        if result:
            return {
                "id": result["id"],
                "title": result["title"],
                "source": result["source"],
                "content": result["content"],
                "metadata": json.loads(result["metadata"]),
                "created_at": result["created_at"].isoformat(),
                "updated_at": result["updated_at"].isoformat()
            }
        
        return None


async def list_documents(
    limit: int = 100,
    offset: int = 0,
    metadata_filter: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    List documents with optional filtering.
    
    Args:
        limit: Maximum number of documents to return
        offset: Number of documents to skip
        metadata_filter: Optional metadata filter
    
    Returns:
        List of documents
    """
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        query = """
            SELECT 
                d.id::text,
                d.title,
                d.source,
                d.metadata,
                d.created_at,
                d.updated_at,
                COUNT(c.id) AS chunk_count
            FROM documents d
            LEFT JOIN chunks c ON d.id = c.document_id
        """
        
        params = []
        conditions = []
        
        if metadata_filter:
            conditions.append(f"d.metadata @> ${len(params) + 1}::jsonb")
            params.append(json.dumps(metadata_filter))
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += """
            GROUP BY d.id, d.title, d.source, d.metadata, d.created_at, d.updated_at
            ORDER BY d.created_at DESC
            LIMIT $%d OFFSET $%d
        """ % (len(params) + 1, len(params) + 2)
        
        params.extend([limit, offset])
        
        results = await conn.fetch(query, *params)
        
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "source": row["source"],
                "metadata": json.loads(row["metadata"]),
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
                "chunk_count": row["chunk_count"]
            }
            for row in results
        ]


async def get_document_count(
    metadata_filter: Optional[Dict[str, Any]] = None
) -> int:
    """
    Get total count of documents.

    Args:
        metadata_filter: Optional metadata filter

    Returns:
        Total document count
    """
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        query = "SELECT COUNT(*) FROM documents"
        params = []
        
        if metadata_filter:
            query += " WHERE metadata @> $1::jsonb"
            params.append(json.dumps(metadata_filter))
        
        result = await conn.fetchval(query, *params)
        return result


# Session Management Functions - Enhanced
async def list_sessions(
    user_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    include_expired: bool = False
) -> List[Dict[str, Any]]:
    """
    List sessions with optional filtering.

    Args:
        user_id: Optional user ID filter
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip
        include_expired: Whether to include expired sessions

    Returns:
        List of sessions
    """
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        query = """
            SELECT 
                s.id::text,
                s.user_id,
                s.metadata,
                s.created_at,
                s.updated_at,
                s.expires_at,
                COUNT(m.id) AS message_count
            FROM sessions s
            LEFT JOIN messages m ON s.id = m.session_id
        """
        
        conditions = []
        params = []
        
        if user_id:
            conditions.append(f"s.user_id = ${len(params) + 1}")
            params.append(user_id)
        
        if not include_expired:
            conditions.append("(s.expires_at IS NULL OR s.expires_at > CURRENT_TIMESTAMP)")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += """
            GROUP BY s.id, s.user_id, s.metadata, s.created_at, s.updated_at, s.expires_at
            ORDER BY s.created_at DESC
            LIMIT $%d OFFSET $%d
        """ % (len(params) + 1, len(params) + 2)
        
        params.extend([limit, offset])
        
        results = await conn.fetch(query, *params)
        
        return [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "metadata": json.loads(row["metadata"]),
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
                "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
                "message_count": row["message_count"]
            }
            for row in results
        ]


async def get_session_count(
    user_id: Optional[str] = None,
    include_expired: bool = False
) -> int:
    """
    Get total count of sessions.

    Args:
        user_id: Optional user ID filter
        include_expired: Whether to include expired sessions

    Returns:
        Total session count
    """
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        query = "SELECT COUNT(*) FROM sessions"
        conditions = []
        params = []
        
        if user_id:
            conditions.append(f"user_id = ${len(params) + 1}")
            params.append(user_id)
        
        if not include_expired:
            conditions.append("(expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        result = await conn.fetchval(query, *params)
        return result


async def delete_session(session_id: str) -> bool:
    """
    Delete a session and its messages.

    Args:
        session_id: Session UUID

    Returns:
        True if deleted, False if not found
    """
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        async with conn.transaction():
            # Delete messages first (due to foreign key constraint)
            await conn.execute(
                "DELETE FROM messages WHERE session_id = $1::uuid",
                session_id
            )
            
            # Delete session
            result = await conn.execute(
                "DELETE FROM sessions WHERE id = $1::uuid",
                session_id
            )
            
            return result.split()[-1] != "0"


# Vector Search Functions
async def vector_search(
    embedding: List[float],
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search.
    
    Args:
        embedding: Query embedding vector
        limit: Maximum number of results
    
    Returns:
        List of matching chunks ordered by similarity (best first)
    """
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        # Convert embedding to PostgreSQL vector string format
        # PostgreSQL vector format: '[1.0,2.0,3.0]' (no spaces after commas)
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        results = await conn.fetch(
            "SELECT * FROM match_chunks($1::vector, $2)",
            embedding_str,
            limit
        )
        
        return [
            {
                "chunk_id": row["chunk_id"],
                "document_id": row["document_id"],
                "content": row["content"],
                "similarity": row["similarity"],
                "metadata": json.loads(row["metadata"]),
                "document_title": row["document_title"],
                "document_source": row["document_source"]
            }
            for row in results
        ]


async def hybrid_search(
    embedding: List[float],
    query_text: str,
    limit: int = 10,
    text_weight: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search (vector + keyword).
    
    Args:
        embedding: Query embedding vector
        query_text: Query text for keyword search
        limit: Maximum number of results
        text_weight: Weight for text similarity (0-1)
    
    Returns:
        List of matching chunks ordered by combined score (best first)
    """
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        # Convert embedding to PostgreSQL vector string format
        # PostgreSQL vector format: '[1.0,2.0,3.0]' (no spaces after commas)
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        results = await conn.fetch(
            "SELECT * FROM hybrid_search($1::vector, $2, $3, $4)",
            embedding_str,
            query_text,
            limit,
            text_weight
        )
        
        return [
            {
                "chunk_id": row["chunk_id"],
                "document_id": row["document_id"],
                "content": row["content"],
                "combined_score": row["combined_score"],
                "vector_similarity": row["vector_similarity"],
                "text_similarity": row["text_similarity"],
                "metadata": json.loads(row["metadata"]),
                "document_title": row["document_title"],
                "document_source": row["document_source"]
            }
            for row in results
        ]


# Chunk Management Functions
async def get_document_chunks(document_id: str) -> List[Dict[str, Any]]:
    """
    Get all chunks for a document.
    
    Args:
        document_id: Document UUID
    
    Returns:
        List of chunks ordered by chunk index
    """
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        results = await conn.fetch(
            "SELECT * FROM get_document_chunks($1::uuid)",
            document_id
        )
        
        return [
            {
                "chunk_id": row["chunk_id"],
                "content": row["content"],
                "chunk_index": row["chunk_index"],
                "metadata": json.loads(row["metadata"])
            }
            for row in results
        ]


# Utility Functions
async def execute_query(query: str, *params) -> List[Dict[str, Any]]:
    """
    Execute a custom query.
    
    Args:
        query: SQL query
        *params: Query parameters
    
    Returns:
        Query results
    """
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        results = await conn.fetch(query, *params)
        return [dict(row) for row in results]


async def test_connection() -> bool:
    """
    Test database connection.
    
    Returns:
        True if connection successful
    """
    try:
        current_pool = await get_pool()
        async with current_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

async def check_database_health():
    """
    Comprehensive database health check with detailed diagnostics.
    Returns dict with health status and metrics.
    """
    health_status = {
        'healthy': False,
        'pool_status': 'unknown',
        'connection_test': False,
        'response_time_ms': None,
        'error': None,
        'pool_stats': {}
    }
    
    try:
        import time
        start_time = time.time()
        
        # Check if pool exists and is healthy
        current_pool = await get_pool()
        if current_pool is None:
            health_status['pool_status'] = 'not_created'
            health_status['error'] = 'Pool not created'
            return health_status
        
        health_status['pool_status'] = 'created'
        
        # Get pool statistics
        if hasattr(current_pool, '_holders'):
            health_status['pool_stats'] = {
                'size': len(current_pool._holders),
                'max_size': current_pool._max_size,
                'min_size': current_pool._min_size
            }
        
        # Test actual connection
        async with current_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            if result == 1:
                health_status['connection_test'] = True
                health_status['healthy'] = True
            
        end_time = time.time()
        health_status['response_time_ms'] = round((end_time - start_time) * 1000, 2)
        
        logger.debug(f"Database health check successful: {health_status['response_time_ms']}ms")
        
    except Exception as e:
        health_status['error'] = str(e)
        logger.warning(f"Database health check failed: {e}")
        
    return health_status

# --- Document Management ---

async def create_document(
    title: str,
    content: str,
    source: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Create a new document and return its ID."""
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        query = """
            INSERT INTO documents (title, content, source, metadata)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """
        doc_id = await conn.fetchval(
            query, title, content, source, json.dumps(metadata or {})
        )
        return str(doc_id)

async def get_document(document_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a document by its ID."""
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        query = "SELECT * FROM documents WHERE id = $1"
        record = await conn.fetchrow(query, UUID(document_id))
        return dict(record) if record else None

async def update_document(
    document_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    source: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Update a document's fields."""
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        fields_to_update = {
            "title": title,
            "content": content,
            "source": source,
            "metadata": json.dumps(metadata) if metadata is not None else None,
        }
        
        updates = ", ".join(
            f"{key} = ${i+2}" for i, (key, value) in enumerate(fields_to_update.items()) if value is not None
        )
        
        if not updates:
            return False

        query = f"UPDATE documents SET {updates}, updated_at = CURRENT_TIMESTAMP WHERE id = $1"
        
        values = [UUID(document_id)] + [v for v in fields_to_update.values() if v is not None]
        
        result = await conn.execute(query, *values)
        return result.split(" ")[1] == "1"


async def delete_document(document_id: str) -> bool:
    """Delete a document and its associated chunks."""
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        query = "DELETE FROM documents WHERE id = $1"
        result = await conn.execute(query, UUID(document_id))
        return result.split(" ")[1] == "1"

async def list_documents(
    limit: int = 20,
    offset: int = 0,
    metadata_filter: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """List documents with pagination and metadata filtering."""
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        query = "SELECT * FROM document_summaries"
        conditions = []
        params = []

        if metadata_filter:
            conditions.append("metadata @> $1")
            params.append(json.dumps(metadata_filter))

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])

        records = await conn.fetch(query, *params)
        return [dict(r) for r in records]

async def get_document_count(metadata_filter: Optional[Dict[str, Any]] = None) -> int:
    """Get the total count of documents."""
    current_pool = await get_pool()
    async with current_pool.acquire() as conn:
        query = "SELECT COUNT(*) FROM documents"
        params = []
        if metadata_filter:
            query += " WHERE metadata @> $1"
            params.append(json.dumps(metadata_filter))
        
        count = await conn.fetchval(query, *params)
        return count or 0

# --- Session Management ---