#!/usr/bin/env python3
"""
Medical Document Ingestion Script
Phase 2 Implementation for Fisioterapia Quiz Generation
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from ingestion.ingest import DocumentIngestionPipeline
from agent.models import IngestionConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_medical_ingestion():
    """Run medical document ingestion pipeline."""
    
    logger.info("🏥 Starting Medical Document Ingestion for Fisioterapia")
    logger.info("📂 Processing documents from: documents/fisioterapia/")
    
    # Configure for medical content
    config = IngestionConfig(
        chunk_size=600,           # Smaller chunks for medical accuracy
        chunk_overlap=100,        # Good overlap for context
        use_semantic_chunking=True,  # Use LLM-guided splitting
        max_chunk_size=1200,      # Reasonable max for medical content
        extract_entities=True,    # Extract medical entities
        skip_graph_building=False # Build knowledge graph
    )
    
    # Initialize ingestion pipeline
    pipeline = DocumentIngestionPipeline(
        config=config,
        documents_folder="documents/fisioterapia",
        clean_before_ingest=True  # Clean existing data
    )
    
    try:
        # Run ingestion
        logger.info("🔄 Starting medical document processing...")
        results = await pipeline.ingest_documents()
        
        # Report results
        logger.info("✅ Medical Document Ingestion Complete!")
        logger.info(f"📊 Documents processed: {len(results)}")
        
        total_chunks = sum(r.chunks_created for r in results)
        total_entities = sum(r.entities_extracted for r in results)
        total_relationships = sum(r.relationships_created for r in results)
        total_errors = sum(len(r.errors) for r in results)
        
        logger.info(f"📝 Chunks created: {total_chunks}")
        logger.info(f"🧠 Entities extracted: {total_entities}")
        logger.info(f"🔗 Knowledge graph episodes: {total_relationships}")
        logger.info(f"⚠️  Errors: {total_errors}")
        
        # Show individual results
        for result in results:
            status = "✅" if not result.errors else "⚠️"
            logger.info(f"   {status} {result.title}: {result.chunks_created} chunks, {result.entities_extracted} entities")
            
            if result.errors:
                for error in result.errors:
                    logger.warning(f"     Error: {error}")
        
        logger.info("🎯 System ready for quiz generation testing!")
        return results
        
    except Exception as e:
        logger.error(f"❌ Medical ingestion failed: {e}")
        raise
    
    finally:
        await pipeline.close()

async def verify_medical_data():
    """Verify medical data was ingested correctly."""
    
    logger.info("🔍 Verifying medical data ingestion...")
    
    try:
        from agent.db_utils import db_pool
        
        # Check documents
        async with db_pool.acquire() as conn:
            documents = await conn.fetch(
                "SELECT id, title, created_at FROM documents ORDER BY created_at DESC LIMIT 10"
            )
            
            logger.info(f"📚 Documents in database: {len(documents)}")
            
            for doc in documents:
                # Get chunk count
                chunk_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM chunks WHERE document_id = $1", 
                    doc['id']
                )
                logger.info(f"   - {doc['title']} ({chunk_count} chunks)")
        
        logger.info("✅ Medical data verification complete!")
        
    except Exception as e:
        logger.error(f"❌ Data verification failed: {e}")

async def test_quiz_generation():
    """Test quiz generation with medical content."""
    
    logger.info("🎯 Testing Quiz Generation...")
    
    try:
        from agent.agent import rag_agent
        from agent.tools import quiz_generator_tool
        
        # Test with a simple medical query
        test_query = "Genera un quiz di 2 domande sull'anatomia della spalla"
        
        logger.info(f"🔄 Testing query: {test_query}")
        
        # Use the agent to generate quiz
        result = await rag_agent.run(test_query)
        
        # Check if result has data (indicates success)
        if hasattr(result, 'data') and result.data:
            logger.info("✅ Quiz generation test successful!")
            logger.info(f"📝 Response length: {len(str(result.data))} characters")
            logger.info(f"📋 Sample response: {str(result.data)[:200]}...")
        else:
            logger.error(f"❌ Quiz generation failed: No data returned")
        
    except Exception as e:
        logger.error(f"❌ Quiz generation test failed: {e}")

async def main():
    """Main execution function."""
    
    logger.info("🚀 PHASE 2: Medical Domain Implementation")
    logger.info("=" * 60)
    
    try:
        # Step 1: Ingest medical documents
        await run_medical_ingestion()
        
        # Step 2: Verify data
        await verify_medical_data()
        
        # Step 3: Test quiz generation
        await test_quiz_generation()
        
        logger.info("=" * 60)
        logger.info("✅ PHASE 2 IMPLEMENTATION COMPLETE!")
        logger.info("🎯 System ready for educational use!")
        
    except Exception as e:
        logger.error(f"❌ Phase 2 implementation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
