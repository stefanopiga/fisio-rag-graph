import os
import asyncio
from urllib.parse import urlparse, urlunparse
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from dotenv import load_dotenv
import asyncpg

# Load test environment variables
load_dotenv('.env.test', override=True)

from agent.api import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    # Store original env vars
    original_env = {
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'DB_SCHEMA': os.getenv('DB_SCHEMA'),
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY', 'test-secret-key'),
        'JWT_ALGORITHM': os.getenv('JWT_ALGORITHM', 'HS256'),
        'JWT_EXPIRATION_MINUTES': os.getenv('JWT_EXPIRATION_MINUTES', '30')
    }
    
    # Set test environment variables
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key'
    os.environ['JWT_ALGORITHM'] = 'HS256'
    os.environ['JWT_EXPIRATION_MINUTES'] = '30'
    
    yield
    
    # Restore original env vars
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]


@pytest.fixture(scope="session")
def mock_db_pool():
    """Create a mock database pool."""
    pool = MagicMock()
    pool.acquire = MagicMock()
    pool.close = AsyncMock()  # Make close async
    
    # Create a mock connection
    mock_conn = AsyncMock()
    
    # Mock the fetchrow method for authenticate_user
    mock_conn.fetchrow = AsyncMock(return_value={
        'id': '8555d5ed-42ea-4556-bf5b-591f53831879',
        'username': 'testuser',
        'hashed_password': '$2b$12$dVyw1yhI6HK7joT.W7zIM.ERQsSWm7qlpvZpMLH5G9gEbhXguLbu6',  # bcrypt hash of 'testpass123'
        'is_active': True
    })
    
    # Mock the execute method
    mock_conn.execute = AsyncMock(return_value="DELETE 1")  # Simulate successful delete
    mock_conn.fetchval = AsyncMock(return_value=False)  # For token blacklist check
    mock_conn.close = AsyncMock()
    
    # Mock transaction context manager
    class AsyncTransactionManager:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None
    
    mock_conn.transaction = MagicMock(return_value=AsyncTransactionManager())
    
    # Make acquire return an async context manager
    class AsyncContextManager:
        async def __aenter__(self):
            return mock_conn
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    pool.acquire.return_value = AsyncContextManager()
    
    return pool


@pytest.fixture(autouse=True)
def mock_database_connections(mock_db_pool, request):
    """Mock all database-related functions."""
    # Determine if this is an invalid login test
    is_invalid_login_test = 'invalid' in request.node.name
    
    with patch('agent.db_utils.pool', mock_db_pool), \
         patch('agent.db_utils.initialize_database', new_callable=AsyncMock), \
         patch('agent.db_utils.get_db_connection', new_callable=AsyncMock, return_value=mock_db_pool.acquire()), \
         patch('agent.db_utils.close_database', new_callable=AsyncMock), \
         patch('agent.api.initialize_database', new_callable=AsyncMock), \
         patch('agent.api.initialize_graph', new_callable=AsyncMock), \
         patch('agent.api.test_connection', new_callable=AsyncMock, return_value=True), \
         patch('agent.api.test_graph_connection', new_callable=AsyncMock, return_value=True), \
         patch('agent.graph_utils.close_graph', new_callable=AsyncMock), \
         patch('asyncpg.connect', new_callable=AsyncMock) as mock_connect:
        
        # Mock asyncpg.connect to return our mock connection
        async def mock_connect_func(*args, **kwargs):
            mock_conn = AsyncMock()
            
            if is_invalid_login_test:
                # Return None for invalid credentials
                mock_conn.fetchrow = AsyncMock(return_value=None)
            else:
                # Return valid user for correct credentials
                mock_conn.fetchrow = AsyncMock(return_value={
                    'id': '8555d5ed-42ea-4556-bf5b-591f53831879',
                    'username': 'testuser',
                    'hashed_password': '$2b$12$dVyw1yhI6HK7joT.W7zIM.ERQsSWm7qlpvZpMLH5G9gEbhXguLbu6',  # bcrypt hash of 'testpass123'
                    'is_active': True
                })
            
            mock_conn.execute = AsyncMock(return_value="DELETE 1")
            mock_conn.fetchval = AsyncMock(return_value=False)
            mock_conn.close = AsyncMock()
            
            # Mock transaction context manager
            class AsyncTransactionManager:
                async def __aenter__(self):
                    return self
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None
            
            mock_conn.transaction = MagicMock(return_value=AsyncTransactionManager())
            return mock_conn
        
        mock_connect.side_effect = mock_connect_func
        
        yield


@pytest.fixture(scope="function")
async def async_client():
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
