"""
Knowledge graph builder for extracting entities and relationships.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timezone
import asyncio
import re

from graphiti_core import Graphiti
from dotenv import load_dotenv

from .chunker import DocumentChunk

# Import graph utilities
try:
    from ..agent.graph_utils import GraphitiClient
except ImportError:
    # For direct execution or testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent.graph_utils import GraphitiClient

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds knowledge graph from document chunks."""
    
    def __init__(self, entities_file: str = "ingestion/medical_entities.md"):
        """Initialize graph builder."""
        self.graph_client = GraphitiClient()
        self._initialized = False
        self.entities_file = entities_file
        self.entity_lists = self._load_entities_from_file()

    def _load_entities_from_file(self) -> Dict[str, Set[str]]:
        """Load entities from the markdown file."""
        if not os.path.exists(self.entities_file):
            logger.warning(f"Entities file not found: {self.entities_file}. Using empty lists.")
            return {
                "anatomical_structures": set(),
                "pathological_conditions": set(),
                "treatment_procedures": set(),
                "medical_devices": set()
            }
        
        with open(self.entities_file, 'r', encoding='utf-8') as f:
            content = f.read()

        entity_lists = {}
        current_entity_type = None

        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('## '):
                # Map markdown header to dictionary key
                header = line[3:].strip()
                if header == "Anatomical Structures":
                    current_entity_type = "anatomical_structures"
                elif header == "Pathological Conditions":
                    current_entity_type = "pathological_conditions"
                elif header == "Treatment Procedures":
                    current_entity_type = "treatment_procedures"
                elif header == "Medical Devices":
                    current_entity_type = "medical_devices"
                else:
                    current_entity_type = None
                
                if current_entity_type:
                    entity_lists[current_entity_type] = set()

            elif line.startswith('- ') and current_entity_type:
                entity = line[2:].strip()
                if entity:
                    entity_lists[current_entity_type].add(entity)
        
        return entity_lists

    async def initialize(self):
        """Initialize graph client."""
        if not self._initialized:
            await self.graph_client.initialize()
            self._initialized = True
    
    async def close(self):
        """Close graph client."""
        if self._initialized:
            await self.graph_client.close()
            self._initialized = False
    
    async def add_document_to_graph(
        self,
        chunks: List[DocumentChunk],
        document_title: str,
        document_source: str,
        document_metadata: Optional[Dict[str, Any]] = None,
        batch_size: int = 3  # Reduced batch size for Graphiti
    ) -> Dict[str, Any]:
        """
        Add document chunks to the knowledge graph.
        
        Args:
            chunks: List of document chunks
            document_title: Title of the document
            document_source: Source of the document
            document_metadata: Additional metadata
            batch_size: Number of chunks to process in each batch
        
        Returns:
            Processing results
        """
        if not self._initialized:
            await self.initialize()
        
        if not chunks:
            return {"episodes_created": 0, "errors": []}
        
        logger.info(f"Adding {len(chunks)} chunks to knowledge graph for document: {document_title}")
        logger.info("⚠️ Large chunks will be truncated to avoid Graphiti token limits.")
        
        # Check for oversized chunks and warn
        oversized_chunks = [i for i, chunk in enumerate(chunks) if len(chunk.content) > 6000]
        if oversized_chunks:
            logger.warning(f"Found {len(oversized_chunks)} chunks over 6000 chars that will be truncated: {oversized_chunks}")
        
        episodes_created = 0
        errors = []
        
        # Process chunks one by one to avoid overwhelming Graphiti
        for i, chunk in enumerate(chunks):
            try:
                # Create episode ID
                episode_id = f"{document_source}_{chunk.index}_{datetime.now().timestamp()}"
                
                # Prepare episode content with size limits
                episode_content = self._prepare_episode_content(
                    chunk,
                    document_title,
                    document_metadata
                )
                
                # Create source description (shorter)
                source_description = f"Document: {document_title} (Chunk: {chunk.index})"
                
                # Add episode to graph
                await self.graph_client.add_episode(
                    episode_id=episode_id,
                    content=episode_content,
                    source=source_description,
                    timestamp=datetime.now(timezone.utc),
                    metadata={
                        "document_title": document_title,
                        "document_source": document_source,
                        "chunk_index": chunk.index,
                        "original_length": len(chunk.content),
                        "processed_length": len(episode_content)
                    }
                )
                
                episodes_created += 1
                logger.info(f"✓ Added episode {episode_id} to knowledge graph ({episodes_created}/{len(chunks)})")
                
                # Small delay between each episode to reduce API pressure
                if i < len(chunks) - 1:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                error_msg = f"Failed to add chunk {chunk.index} to graph: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                
                # Continue processing other chunks even if one fails
                continue
        
        result = {
            "episodes_created": episodes_created,
            "total_chunks": len(chunks),
            "errors": errors
        }
        
        logger.info(f"Graph building complete: {episodes_created} episodes created, {len(errors)} errors")
        return result
    
    def _prepare_episode_content(
        self,
        chunk: DocumentChunk,
        document_title: str,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Prepare episode content with minimal context to avoid token limits.
        
        Args:
            chunk: Document chunk
            document_title: Title of the document
            document_metadata: Additional metadata
        
        Returns:
            Formatted episode content (optimized for Graphiti)
        """
        # Limit chunk content to avoid Graphiti's 8192 token limit
        # Estimate ~4 chars per token, keep content under 6000 chars to leave room for processing
        max_content_length = 6000
        
        content = chunk.content
        if len(content) > max_content_length:
            # Truncate content but try to end at a sentence boundary
            truncated = content[:max_content_length]
            last_sentence_end = max(
                truncated.rfind('. '),
                truncated.rfind('! '),
                truncated.rfind('? ')
            )
            
            if last_sentence_end > max_content_length * 0.7:  # If we can keep 70% and end cleanly
                content = truncated[:last_sentence_end + 1] + " [TRUNCATED]"
            else:
                content = truncated + "... [TRUNCATED]"
            
            logger.warning(f"Truncated chunk {chunk.index} from {len(chunk.content)} to {len(content)} chars for Graphiti")
        
        # Add minimal context (just document title for now)
        if document_title and len(content) < max_content_length - 100:
            episode_content = f"[Doc: {document_title[:50]}]\n\n{content}"
        else:
            episode_content = content
        
        return episode_content
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count (4 chars per token)."""
        return len(text) // 4
    
    def _is_content_too_large(self, content: str, max_tokens: int = 7000) -> bool:
        """Check if content is too large for Graphiti processing."""
        return self._estimate_tokens(content) > max_tokens
    
    async def extract_entities_from_chunks(
        self,
        chunks: List[DocumentChunk],
        extract_anatomical: bool = True,
        extract_pathological: bool = True,
        extract_treatments: bool = True
    ) -> List[DocumentChunk]:
        """
        Extract entities from chunks and add to metadata.
        
        Args:
            chunks: List of document chunks
            extract_anatomical: Whether to extract anatomical structures
            extract_pathological: Whether to extract pathological conditions
            extract_treatments: Whether to extract treatment procedures
        
        Returns:
            Chunks with entity metadata added
        """
        logger.info(f"Extracting entities from {len(chunks)} chunks")
        
        enriched_chunks = []
        
        for chunk in chunks:
            entities = {
                "anatomical_structures": [],
                "pathological_conditions": [],
                "treatment_procedures": [],
                "medical_devices": []
            }
            
            content = chunk.content
            
            # Extract anatomical structures
            if extract_anatomical:
                entities["anatomical_structures"] = self._extract_anatomical_structures(content)
            
            # Extract pathological conditions
            if extract_pathological:
                entities["pathological_conditions"] = self._extract_pathological_conditions(content)
            
            # Extract treatment procedures
            if extract_treatments:
                entities["treatment_procedures"] = self._extract_treatment_procedures(content)
            
            # Extract medical devices
            entities["medical_devices"] = self._extract_medical_devices(content)
            
            # Create enriched chunk
            enriched_chunk = DocumentChunk(
                content=chunk.content,
                index=chunk.index,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                metadata={
                    **chunk.metadata,
                    "entities": entities,
                    "entity_extraction_date": datetime.now().isoformat()
                },
                token_count=chunk.token_count
            )
            
            # Preserve embedding if it exists
            if hasattr(chunk, 'embedding'):
                enriched_chunk.embedding = chunk.embedding
            
            enriched_chunks.append(enriched_chunk)
        
        logger.info("Entity extraction complete")
        return enriched_chunks
    
    def _extract_anatomical_structures(self, text: str) -> List[str]:
        """Extract anatomical structures from text."""
        anatomical_structures = self.entity_lists.get("anatomical_structures", set())
        found_structures = set()
        text_lower = text.lower()
        
        for structure in anatomical_structures:
            # Case-insensitive search with word boundaries
            pattern = r'\b' + re.escape(structure.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_structures.add(structure)
        
        return list(found_structures)
    
    def _extract_pathological_conditions(self, text: str) -> List[str]:
        """Extract pathological conditions from text."""
        pathological_conditions = self.entity_lists.get("pathological_conditions", set())
        found_conditions = set()
        text_lower = text.lower()
        
        for condition in pathological_conditions:
            if condition.lower() in text_lower:
                found_conditions.add(condition)
        
        return list(found_conditions)
    
    def _extract_treatment_procedures(self, text: str) -> List[str]:
        """Extract treatment procedures from text."""
        treatment_procedures = self.entity_lists.get("treatment_procedures", set())
        found_procedures = set()
        text_lower = text.lower()
        
        for procedure in treatment_procedures:
            if procedure.lower() in text_lower:
                found_procedures.add(procedure)
        
        return list(found_procedures)
    
    def _extract_medical_devices(self, text: str) -> List[str]:
        """Extract medical devices and tools from text."""
        medical_devices = self.entity_lists.get("medical_devices", set())
        found_devices = set()
        text_lower = text.lower()
        
        for device in medical_devices:
            if device.lower() in text_lower:
                found_devices.add(device)
        
        return list(found_devices)
    
    async def clear_graph(self):
        """Clear all data from the knowledge graph."""
        if not self._initialized:
            await self.initialize()
        
        logger.warning("Clearing knowledge graph...")
        await self.graph_client.clear_graph()
        logger.info("Knowledge graph cleared")


# Factory function
def create_graph_builder() -> GraphBuilder:
    """Create graph builder instance."""
    return GraphBuilder()