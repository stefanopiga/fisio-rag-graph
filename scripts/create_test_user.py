import asyncio
import asyncpg
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agent.auth_utils import get_password_hash

async def create_test_user():
    try:
        conn = await asyncpg.connect('postgresql://raguser:ragpass123@localhost:5432/agentic_rag_db')
        
        # Create user table if not exists
        sql_file = Path(__file__).parent.parent / "sql" / "users_table.sql"
        with open(sql_file, 'r') as f:
            await conn.execute(f.read())
        
        # Create test user
        password_hash = await get_password_hash('testpass123')
        await conn.execute('''
            INSERT INTO users (username, password_hash, email, full_name)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (username) DO UPDATE
            SET password_hash = $2
        ''', 'testuser', password_hash, 'test@example.com', 'Test User')
        
        print('Test user created successfully!')
        await conn.close()
    except Exception as e:
        print(f'Error creating test user: {e}')

if __name__ == "__main__":
    asyncio.run(create_test_user())