#!/usr/bin/env python3
"""
Script di test per diagnosticare problemi di connettività database Neon.
Testa la connessione senza l'intero framework dell'applicazione.
"""

import asyncio
import asyncpg
import os
import sys
import traceback
from dotenv import load_dotenv

async def test_basic_connection():
    """Test connessione di base al database."""
    print("🔍 Testing basic database connection...")
    
    try:
        # Load environment variables
        load_dotenv()
        database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return False
            
        print(f"📍 Database URL (masked): {database_url[:20]}...{database_url[-20:]}")
        
        # Test basic connection
        conn = await asyncpg.connect(database_url)
        print("✅ Basic connection successful!")
        
        # Test simple query
        result = await conn.fetchval("SELECT version();")
        print(f"📊 PostgreSQL version: {result}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"📋 Error type: {type(e).__name__}")
        traceback.print_exc()
        return False

async def test_schema_access():
    """Test accesso allo schema staging."""
    print("\n🔍 Testing schema 'staging' access...")
    
    try:
        load_dotenv()
        database_url = os.getenv("DATABASE_URL")
        
        conn = await asyncpg.connect(database_url)
        
        # Check if staging schema exists
        schema_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = 'staging'
            );
        """)
        
        if schema_exists:
            print("✅ Schema 'staging' exists")
            
            # Try to set search_path
            await conn.execute("SET search_path TO staging;")
            print("✅ Successfully set search_path to staging")
            
            # List tables in staging schema
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'staging'
                ORDER BY table_name;
            """)
            
            if tables:
                print(f"📋 Tables in staging schema: {[t['table_name'] for t in tables]}")
            else:
                print("⚠️  No tables found in staging schema")
                
        else:
            print("❌ Schema 'staging' does not exist")
            
            # List available schemas
            schemas = await conn.fetch("""
                SELECT schema_name FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY schema_name;
            """)
            print(f"📋 Available schemas: {[s['schema_name'] for s in schemas]}")
        
        await conn.close()
        return schema_exists
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        traceback.print_exc()
        return False

async def test_extensions():
    """Test se le estensioni richieste sono installate."""
    print("\n🔍 Testing required PostgreSQL extensions...")
    
    try:
        load_dotenv()
        database_url = os.getenv("DATABASE_URL")
        
        conn = await asyncpg.connect(database_url)
        
        # Check required extensions
        required_extensions = ['vector', 'uuid-ossp', 'pg_trgm']
        
        for ext in required_extensions:
            exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_extension WHERE extname = $1
                );
            """, ext)
            
            if exists:
                print(f"✅ Extension '{ext}' is installed")
            else:
                print(f"❌ Extension '{ext}' is NOT installed")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Extensions test failed: {e}")
        traceback.print_exc()
        return False

async def test_connection_pool():
    """Test connessione con pool (come nell'app)."""
    print("\n🔍 Testing connection pool (like in app)...")
    
    try:
        load_dotenv()
        database_url = os.getenv("DATABASE_URL")
        
        # Create pool with same settings as app
        pool = await asyncpg.create_pool(
            database_url,
            min_size=1,  # Reduced for test
            max_size=5,  # Reduced for test
            server_settings={'search_path': 'staging'}
        )
        print("✅ Connection pool created successfully")
        
        # Test acquire connection
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT current_user;")
            print(f"✅ Pool connection test successful, user: {result}")
        
        await pool.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection pool test failed: {e}")
        traceback.print_exc()
        return False

async def main():
    """Esegue tutti i test di connessività."""
    print("🚀 Starting database connectivity diagnosis...")
    print("=" * 60)
    
    results = {
        'basic_connection': await test_basic_connection(),
        'schema_access': await test_schema_access(),
        'extensions': await test_extensions(),
        'connection_pool': await test_connection_pool()
    }
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Database connectivity is working.")
        print("   The issue might be in the application startup code.")
    else:
        print("\n⚠️  Some tests failed. Database has connectivity issues.")
        print("   Check Neon dashboard for database status.")
    
    return all_passed

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)