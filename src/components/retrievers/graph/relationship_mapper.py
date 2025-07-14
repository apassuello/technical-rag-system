"""
Relationship mapper for Epic 2 Week 2.

This module provides advanced semantic relationship detection between entities
in technical documents, using transformer models and pattern matching to
identify and classify relationships between RISC-V concepts.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import re

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
except ImportError:
    np = None
    SentenceTransformer = None

from src.core.interfaces import Document
from .config.graph_config import RelationshipDetectionConfig
from .entity_extraction import Entity
from .document_graph_builder import GraphNode, GraphEdge

logger = logging.getLogger(__name__)


@dataclass
class Relationship:
    """Represents a detected relationship between entities."""
    source_entity: str
    target_entity: str
    relationship_type: str
    confidence: float
    evidence: str
    document_id: str
    source_pos: int = 0
    target_pos: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RelationshipMapperError(Exception):
    """Raised when relationship mapping operations fail."""
    pass


class RelationshipMapper:
    """
    Advanced semantic relationship mapper for technical documents.
    
    This class identifies and classifies relationships between entities
    using multiple strategies:
    - Pattern-based relationship extraction
    - Semantic similarity-based relationships
    - Context-aware relationship classification
    - Transformer-based relationship scoring
    
    Supports relationship types:
    - implements: One entity implements another
    - extends: One entity extends or builds upon another
    - requires: One entity requires another for functionality
    - conflicts: Entities that cannot coexist or are incompatible
    - relates_to: General semantic relationship
    """
    
    def __init__(self, config: RelationshipDetectionConfig):
        """
        Initialize the relationship mapper.
        
        Args:
            config: Relationship detection configuration
        """
        self.config = config
        self.model = None
        
        # Relationship patterns
        self.relationship_patterns = self._get_relationship_patterns()
        
        # Statistics
        self.stats = {
            "relationships_detected": 0,
            "documents_processed": 0,
            "processing_time": 0.0,
            "model_load_time": 0.0,
            "pattern_matches": 0,
            "semantic_matches": 0
        }
        
        # Initialize model if using semantic approach
        if self.config.implementation == "semantic":
            self._initialize_model()
        
        logger.info(f"RelationshipMapper initialized with {self.config.implementation} implementation")
    
    def _initialize_model(self) -> None:
        """Initialize sentence transformer model for semantic analysis."""
        if SentenceTransformer is None:
            raise RelationshipMapperError(
                "sentence-transformers is not installed. Install with: pip install sentence-transformers"
            )
        
        start_time = time.time()
        
        try:
            # Use the same model as the embedder for consistency
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            self.model = SentenceTransformer(model_name)
            
            self.stats["model_load_time"] = time.time() - start_time
            logger.info(f"Loaded relationship model: {model_name} in {self.stats['model_load_time']:.3f}s")
            
        except Exception as e:
            logger.warning(f"Failed to load semantic model: {str(e)}. Falling back to pattern-only approach.")
            self.model = None
    
    def _get_relationship_patterns(self) -> Dict[str, List[str]]:
        """
        Get regex patterns for relationship extraction.
        
        Returns:
            Dictionary mapping relationship types to regex patterns
        """
        return {
            "implements": [
                r"(\w+(?:\s+\w+)*)\s+implements?\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+implementation\s+of\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+realizes?\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+provides?\s+(\w+(?:\s+\w+)*)\s+functionality",
                r"(\w+(?:\s+\w+)*)\s+supports?\s+(\w+(?:\s+\w+)*)\s+standard",
            ],
            "extends": [
                r"(\w+(?:\s+\w+)*)\s+extends?\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+extension\s+(?:of\s+)?(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+builds?\s+(?:on|upon)\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+based\s+on\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+enhances?\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+adds?\s+to\s+(\w+(?:\s+\w+)*)",
            ],
            "requires": [
                r"(\w+(?:\s+\w+)*)\s+requires?\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+depends?\s+on\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+needs?\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+uses?\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+relies?\s+on\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+assumes?\s+(\w+(?:\s+\w+)*)",
            ],
            "conflicts": [
                r"(\w+(?:\s+\w+)*)\s+conflicts?\s+with\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+incompatible\s+with\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+cannot\s+(?:be\s+)?used\s+with\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+excludes?\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+mutually\s+exclusive\s+(?:with\s+)?(\w+(?:\s+\w+)*)",
            ],
            "relates_to": [
                r"(\w+(?:\s+\w+)*)\s+(?:is\s+)?(?:related\s+to|associated\s+with)\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+and\s+(\w+(?:\s+\w+)*)\s+(?:work\s+together|interact)",
                r"(\w+(?:\s+\w+)*)\s+communicates?\s+with\s+(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*)\s+interfaces?\s+with\s+(\w+(?:\s+\w+)*)",
            ]
        }
    
    def detect_relationships(self, documents: List[Document], 
                           document_entities: Dict[str, List[Entity]]) -> Dict[str, List[Relationship]]:
        """
        Detect relationships between entities in documents.
        
        Args:
            documents: List of documents to analyze
            document_entities: Dictionary mapping document IDs to entities
            
        Returns:
            Dictionary mapping document IDs to detected relationships
        """
        if not documents or not document_entities:
            return {}
        
        start_time = time.time()
        
        try:
            all_relationships = {}
            
            for document in documents:
                doc_id = document.metadata.get("id", "unknown")
                doc_entities = document_entities.get(doc_id, [])
                if not doc_entities:
                    continue
                
                relationships = self._detect_document_relationships(document, doc_entities)
                all_relationships[doc_id] = relationships
            
            # Update statistics
            processing_time = time.time() - start_time
            self.stats["documents_processed"] += len(documents)
            self.stats["processing_time"] += processing_time
            total_relationships = sum(len(rels) for rels in all_relationships.values())
            self.stats["relationships_detected"] += total_relationships
            
            logger.info(
                f"Detected {total_relationships} relationships from {len(documents)} documents "
                f"in {processing_time:.3f}s"
            )
            
            return all_relationships
            
        except Exception as e:
            logger.error(f"Relationship detection failed: {str(e)}")
            raise RelationshipMapperError(f"Failed to detect relationships: {str(e)}") from e
    
    def _detect_document_relationships(self, document: Document, entities: List[Entity]) -> List[Relationship]:
        """
        Detect relationships within a single document.
        
        Args:
            document: Document to analyze
            entities: Entities found in the document
            
        Returns:
            List of detected relationships
        """
        relationships = []
        
        # Pattern-based relationship detection
        pattern_relationships = self._detect_pattern_relationships(document, entities)
        relationships.extend(pattern_relationships)
        
        # Semantic similarity-based relationships (if model is available)
        if self.model is not None:
            semantic_relationships = self._detect_semantic_relationships(document, entities)
            relationships.extend(semantic_relationships)
        
        # Co-occurrence-based relationships for close entities
        cooccurrence_relationships = self._detect_cooccurrence_relationships(document, entities)
        relationships.extend(cooccurrence_relationships)
        
        # Remove duplicates and apply confidence filtering
        relationships = self._deduplicate_relationships(relationships)
        relationships = [r for r in relationships if r.confidence >= self.config.similarity_threshold]
        
        # Limit relationships per entity if configured
        if self.config.max_relationships_per_node > 0:
            relationships = self._limit_relationships_per_entity(relationships)
        
        return relationships
    
    def _detect_pattern_relationships(self, document: Document, entities: List[Entity]) -> List[Relationship]:
        """Detect relationships using regex patterns."""
        relationships = []
        content = document.content
        
        for relationship_type, patterns in self.relationship_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    if len(match.groups()) >= 2:
                        source_text = match.group(1).strip()
                        target_text = match.group(2).strip()
                        
                        # Find matching entities
                        source_entity = self._find_best_entity_match(source_text, entities)
                        target_entity = self._find_best_entity_match(target_text, entities)
                        
                        if source_entity and target_entity and source_entity != target_entity:
                            relationship = Relationship(
                                source_entity=source_entity.text,
                                target_entity=target_entity.text,
                                relationship_type=relationship_type,
                                confidence=0.9,  # High confidence for pattern matches
                                evidence=match.group(0),
                                document_id=document.metadata.get("id", "unknown"),
                                source_pos=source_entity.start_pos,
                                target_pos=target_entity.start_pos,
                                metadata={"detection_method": "pattern", "pattern": pattern}
                            )
                            relationships.append(relationship)
                            self.stats["pattern_matches"] += 1
        
        return relationships
    
    def _detect_semantic_relationships(self, document: Document, entities: List[Entity]) -> List[Relationship]:
        """Detect relationships using semantic similarity."""
        if not self.model:
            return []
        
        relationships = []
        
        # Create entity pairs for comparison
        entity_pairs = []
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                if entity1.text != entity2.text:
                    entity_pairs.append((entity1, entity2))
        
        if not entity_pairs:
            return relationships
        
        # Get entity contexts for better relationship detection
        entity_contexts = []
        for entity1, entity2 in entity_pairs:
            context1 = self._get_entity_context(document.content, entity1)
            context2 = self._get_entity_context(document.content, entity2)
            combined_context = f"{context1} [SEP] {context2}"
            entity_contexts.append(combined_context)
        
        # Calculate semantic similarities
        try:
            embeddings = self.model.encode(entity_contexts)
            
            # Compare with relationship type embeddings
            relationship_descriptions = {
                "implements": "implements provides realizes functionality",
                "extends": "extends builds upon enhances adds to",
                "requires": "requires depends on needs uses relies on",
                "conflicts": "conflicts incompatible excludes cannot use",
                "relates_to": "related associated interacts communicates interfaces"
            }
            
            relationship_embeddings = self.model.encode(list(relationship_descriptions.values()))
            
            for i, (entity1, entity2) in enumerate(entity_pairs):
                context_embedding = embeddings[i:i+1]
                
                # Find best matching relationship type
                similarities = np.dot(context_embedding, relationship_embeddings.T)[0]
                best_relationship_idx = np.argmax(similarities)
                best_confidence = float(similarities[best_relationship_idx])
                
                if best_confidence >= self.config.similarity_threshold:
                    relationship_type = list(relationship_descriptions.keys())[best_relationship_idx]
                    
                    relationship = Relationship(
                        source_entity=entity1.text,
                        target_entity=entity2.text,
                        relationship_type=relationship_type,
                        confidence=best_confidence,
                        evidence=f"Semantic context: {entity_contexts[i][:100]}...",
                        document_id=document.metadata.get("id", "unknown"),
                        source_pos=entity1.start_pos,
                        target_pos=entity2.start_pos,
                        metadata={"detection_method": "semantic", "similarity_score": best_confidence}
                    )
                    relationships.append(relationship)
                    self.stats["semantic_matches"] += 1
        
        except Exception as e:
            logger.warning(f"Semantic relationship detection failed: {str(e)}")
        
        return relationships
    
    def _detect_cooccurrence_relationships(self, document: Document, entities: List[Entity]) -> List[Relationship]:
        """Detect relationships based on entity co-occurrence and proximity."""
        relationships = []
        
        # Sort entities by position
        sorted_entities = sorted(entities, key=lambda e: e.start_pos)
        
        # Find entities that are close to each other
        for i, entity1 in enumerate(sorted_entities):
            for entity2 in sorted_entities[i+1:]:
                # Check if entities are within reasonable distance
                distance = entity2.start_pos - entity1.end_pos
                
                if distance > 500:  # Too far apart
                    break
                
                if distance < 100:  # Very close entities
                    # Determine relationship type based on entity types and context
                    relationship_type = self._infer_relationship_type(entity1, entity2, document.content)
                    
                    if relationship_type:
                        # Lower confidence for inferred relationships
                        confidence = min(entity1.confidence, entity2.confidence) * 0.6
                        
                        if confidence >= self.config.similarity_threshold:
                            context = document.content[
                                max(0, entity1.start_pos - 50):
                                min(len(document.content), entity2.end_pos + 50)
                            ]
                            
                            relationship = Relationship(
                                source_entity=entity1.text,
                                target_entity=entity2.text,
                                relationship_type=relationship_type,
                                confidence=confidence,
                                evidence=context,
                                document_id=document.metadata.get("id", "unknown"),
                                source_pos=entity1.start_pos,
                                target_pos=entity2.start_pos,
                                metadata={"detection_method": "cooccurrence", "distance": distance}
                            )
                            relationships.append(relationship)
        
        return relationships
    
    def _find_best_entity_match(self, text: str, entities: List[Entity]) -> Optional[Entity]:
        """Find the best matching entity for the given text."""
        text_lower = text.lower().strip()
        
        # Exact match first
        for entity in entities:
            if entity.text.lower().strip() == text_lower:
                return entity
        
        # Substring match
        best_match = None
        best_score = 0
        
        for entity in entities:
            entity_text = entity.text.lower().strip()
            
            # Check if entity text is contained in the pattern match
            if entity_text in text_lower or text_lower in entity_text:
                # Score based on length similarity and overlap
                overlap = len(set(entity_text.split()) & set(text_lower.split()))
                max_words = max(len(entity_text.split()), len(text_lower.split()))
                score = overlap / max_words if max_words > 0 else 0
                
                if score > best_score and score > 0.5:  # Minimum overlap threshold
                    best_match = entity
                    best_score = score
        
        return best_match
    
    def _get_entity_context(self, content: str, entity: Entity, window: int = 100) -> str:
        """Get surrounding context for an entity."""
        start = max(0, entity.start_pos - window)
        end = min(len(content), entity.end_pos + window)
        return content[start:end].strip()
    
    def _infer_relationship_type(self, entity1: Entity, entity2: Entity, content: str) -> Optional[str]:
        """Infer relationship type based on entity types and context."""
        # Simple heuristics based on entity labels
        if entity1.label == "EXTENSION" or entity2.label == "EXTENSION":
            return "extends"
        elif entity1.label == "PROTOCOL" and entity2.label == "ARCH":
            return "implements"
        elif entity1.label == "ARCH" and entity2.label == "TECH":
            return "requires"
        elif entity1.label == entity2.label:
            return "relates_to"
        else:
            return "relates_to"  # Default relationship
    
    def _deduplicate_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        """Remove duplicate relationships, keeping the highest confidence ones."""
        seen = {}
        
        for relationship in relationships:
            # Create key for deduplication (bidirectional for some relationships)
            if self.config.enable_bidirectional and relationship.relationship_type in ["relates_to", "conflicts"]:
                # For bidirectional relationships, use sorted order
                entities = sorted([relationship.source_entity, relationship.target_entity])
                key = (entities[0], entities[1], relationship.relationship_type)
            else:
                key = (relationship.source_entity, relationship.target_entity, relationship.relationship_type)
            
            if key not in seen or relationship.confidence > seen[key].confidence:
                seen[key] = relationship
        
        return list(seen.values())
    
    def _limit_relationships_per_entity(self, relationships: List[Relationship]) -> List[Relationship]:
        """Limit the number of relationships per entity."""
        entity_counts = defaultdict(int)
        limited_relationships = []
        
        # Sort by confidence (highest first)
        sorted_relationships = sorted(relationships, key=lambda r: r.confidence, reverse=True)
        
        for relationship in sorted_relationships:
            source_count = entity_counts[relationship.source_entity]
            target_count = entity_counts[relationship.target_entity]
            
            if (source_count < self.config.max_relationships_per_node and 
                target_count < self.config.max_relationships_per_node):
                
                limited_relationships.append(relationship)
                entity_counts[relationship.source_entity] += 1
                entity_counts[relationship.target_entity] += 1
        
        return limited_relationships
    
    def get_relationship_types(self) -> List[str]:
        """Get list of supported relationship types."""
        return list(self.relationship_patterns.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get relationship detection statistics.
        
        Returns:
            Dictionary with detection statistics
        """
        stats = self.stats.copy()
        
        if stats["documents_processed"] > 0:
            stats["avg_relationships_per_document"] = (
                stats["relationships_detected"] / stats["documents_processed"]
            )
            stats["avg_processing_time_per_document"] = (
                stats["processing_time"] / stats["documents_processed"]
            )
        else:
            stats["avg_relationships_per_document"] = 0.0
            stats["avg_processing_time_per_document"] = 0.0
        
        # Add detection method breakdown
        stats["pattern_percentage"] = (
            (stats["pattern_matches"] / max(stats["relationships_detected"], 1)) * 100
        )
        stats["semantic_percentage"] = (
            (stats["semantic_matches"] / max(stats["relationships_detected"], 1)) * 100
        )
        
        return stats
    
    def reset_statistics(self) -> None:
        """Reset detection statistics."""
        self.stats = {
            "relationships_detected": 0,
            "documents_processed": 0,
            "processing_time": 0.0,
            "model_load_time": self.stats["model_load_time"],  # Keep model load time
            "pattern_matches": 0,
            "semantic_matches": 0
        }