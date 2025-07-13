"""
Document graph builder for Epic 2 Week 2.

This module provides graph construction capabilities for technical documents,
using NetworkX to build knowledge graphs that capture relationships between
concepts, protocols, architectures, and extensions in RISC-V documentation.
"""

import logging
import time
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict

try:
    import networkx as nx
    import numpy as np
except ImportError:
    nx = None
    np = None

from src.core.interfaces import Document
from .config.graph_config import GraphBuilderConfig
from .entity_extraction import Entity, EntityExtractor

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Represents a node in the document graph."""
    node_id: str
    node_type: str  # concept, protocol, architecture, extension
    text: str
    documents: Set[str] = field(default_factory=set)
    frequency: int = 0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self) -> int:
        return hash(self.node_id)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, GraphNode):
            return False
        return self.node_id == other.node_id


@dataclass
class GraphEdge:
    """Represents an edge in the document graph."""
    source: str
    target: str
    edge_type: str  # implements, extends, requires, conflicts
    weight: float
    confidence: float
    documents: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self) -> int:
        return hash((self.source, self.target, self.edge_type))


class DocumentGraphBuilderError(Exception):
    """Raised when graph construction operations fail."""
    pass


class DocumentGraphBuilder:
    """
    Builds knowledge graphs from technical documents.
    
    This class constructs NetworkX graphs that capture semantic relationships
    between technical concepts in RISC-V documentation. It processes entities
    extracted from documents and builds a graph structure that can be used
    for graph-based retrieval and analysis.
    
    Features:
    - NetworkX-based graph construction
    - Support for multiple node types (concept, protocol, architecture, extension)
    - Multiple relationship types (implements, extends, requires, conflicts)
    - Incremental graph updates
    - Memory optimization with graph pruning
    - Performance monitoring and statistics
    """
    
    def __init__(self, config: GraphBuilderConfig, entity_extractor: EntityExtractor):
        """
        Initialize the document graph builder.
        
        Args:
            config: Graph builder configuration
            entity_extractor: Entity extractor for processing documents
        """
        if nx is None:
            raise DocumentGraphBuilderError("NetworkX is not installed. Install with: pip install networkx")
        
        self.config = config
        self.entity_extractor = entity_extractor
        
        # Initialize graph
        self.graph = nx.DiGraph()  # Directed graph for relationships
        
        # Node and edge tracking
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[Tuple[str, str, str], GraphEdge] = {}
        
        # Document tracking
        self.document_entities: Dict[str, List[Entity]] = {}
        self.processed_documents: Set[str] = set()
        
        # Statistics
        self.stats = {
            "documents_processed": 0,
            "total_nodes": 0,
            "total_edges": 0,
            "construction_time": 0.0,
            "last_update_time": 0.0,
            "memory_usage_mb": 0.0,
            "pruning_operations": 0
        }
        
        logger.info(f"DocumentGraphBuilder initialized with {self.config.implementation} backend")
    
    def build_graph(self, documents: List[Document]) -> nx.DiGraph:
        """
        Build knowledge graph from documents.
        
        Args:
            documents: List of documents to process
            
        Returns:
            NetworkX directed graph
        """
        if not documents:
            logger.warning("No documents provided for graph construction")
            return self.graph
        
        start_time = time.time()
        
        try:
            logger.info(f"Building graph from {len(documents)} documents")
            
            # Extract entities from all documents
            document_entities = self.entity_extractor.extract_entities(documents)
            
            # Build nodes from entities
            self._build_nodes(document_entities)
            
            # Build edges from co-occurrence and semantic relationships
            self._build_edges(documents, document_entities)
            
            # Prune graph if enabled
            if self.config.enable_pruning:
                self._prune_graph()
            
            # Update statistics
            construction_time = time.time() - start_time
            self._update_statistics(documents, construction_time)
            
            logger.info(
                f"Graph construction completed in {construction_time:.3f}s "
                f"({len(self.nodes)} nodes, {len(self.edges)} edges)"
            )
            
            return self.graph
            
        except Exception as e:
            logger.error(f"Graph construction failed: {str(e)}")
            raise DocumentGraphBuilderError(f"Failed to build graph: {str(e)}") from e
    
    def update_graph(self, new_documents: List[Document]) -> nx.DiGraph:
        """
        Incrementally update graph with new documents.
        
        Args:
            new_documents: List of new documents to add
            
        Returns:
            Updated NetworkX directed graph
        """
        if not new_documents:
            return self.graph
        
        # Filter out already processed documents
        unprocessed_docs = [
            doc for doc in new_documents 
            if doc.metadata.get("id", "unknown") not in self.processed_documents
        ]
        
        if not unprocessed_docs:
            logger.info("All documents already processed")
            return self.graph
        
        start_time = time.time()
        
        try:
            logger.info(f"Updating graph with {len(unprocessed_docs)} new documents")
            
            # Extract entities from new documents
            new_entities = self.entity_extractor.extract_entities(unprocessed_docs)
            
            # Update nodes
            self._update_nodes(new_entities)
            
            # Update edges
            self._update_edges(unprocessed_docs, new_entities)
            
            # Prune if necessary
            if self.config.enable_pruning and len(self.nodes) > self.config.max_graph_size:
                self._prune_graph()
            
            # Update statistics
            update_time = time.time() - start_time
            self.stats["last_update_time"] = update_time
            self.stats["documents_processed"] += len(unprocessed_docs)
            
            logger.info(f"Graph updated in {update_time:.3f}s")
            
            return self.graph
            
        except Exception as e:
            logger.error(f"Graph update failed: {str(e)}")
            raise DocumentGraphBuilderError(f"Failed to update graph: {str(e)}") from e
    
    def _build_nodes(self, document_entities: Dict[str, List[Entity]]) -> None:
        """Build graph nodes from extracted entities."""
        entity_groups = defaultdict(list)
        
        # Group entities by normalized text and type
        for doc_id, entities in document_entities.items():
            for entity in entities:
                key = self._normalize_entity_text(entity.text, entity.label)
                entity_groups[key].append((entity, doc_id))
        
        # Create nodes from entity groups
        for normalized_key, entity_instances in entity_groups.items():
            node_id = self._generate_node_id(normalized_key)
            
            # Aggregate information from all instances
            entity_types = [e[0].label for e in entity_instances]
            most_common_type = max(set(entity_types), key=entity_types.count)
            
            # Get representative text (longest variant)
            texts = [e[0].text for e in entity_instances]
            representative_text = max(texts, key=len)
            
            # Calculate aggregate confidence
            confidences = [e[0].confidence for e in entity_instances]
            avg_confidence = sum(confidences) / len(confidences)
            
            # Get all documents containing this entity
            documents = set(e[1] for e in entity_instances)
            
            # Create node
            node = GraphNode(
                node_id=node_id,
                node_type=self._map_entity_to_node_type(most_common_type),
                text=representative_text,
                documents=documents,
                frequency=len(entity_instances),
                confidence=avg_confidence,
                metadata={
                    "entity_variants": list(set(texts)),
                    "source_types": list(set(entity_types))
                }
            )
            
            self.nodes[node_id] = node
            
            # Add node to NetworkX graph
            self.graph.add_node(
                node_id,
                node_type=node.node_type,
                text=node.text,
                frequency=node.frequency,
                confidence=node.confidence,
                documents=list(node.documents),
                metadata=node.metadata
            )
        
        logger.info(f"Created {len(self.nodes)} nodes from entities")
    
    def _build_edges(self, documents: List[Document], document_entities: Dict[str, List[Entity]]) -> None:
        """Build graph edges from entity co-occurrence and relationships."""
        # Store document entities for edge building
        self.document_entities.update(document_entities)
        
        # Build edges from co-occurrence within documents
        for doc_id, entities in document_entities.items():
            if len(entities) < 2:
                continue
            
            # Create edges between entities in the same document
            for i, entity1 in enumerate(entities):
                for entity2 in entities[i+1:]:
                    self._create_co_occurrence_edge(entity1, entity2, doc_id)
        
        # Build semantic relationship edges
        self._build_semantic_edges(documents, document_entities)
        
        logger.info(f"Created {len(self.edges)} edges from relationships")
    
    def _create_co_occurrence_edge(self, entity1: Entity, entity2: Entity, doc_id: str) -> None:
        """Create co-occurrence edge between two entities."""
        node1_id = self._generate_node_id(self._normalize_entity_text(entity1.text, entity1.label))
        node2_id = self._generate_node_id(self._normalize_entity_text(entity2.text, entity2.label))
        
        if node1_id == node2_id:
            return  # Skip self-loops
        
        # Determine edge type based on entity types and context
        edge_type = self._determine_edge_type(entity1, entity2)
        
        # Calculate edge weight and confidence
        weight = self._calculate_edge_weight(entity1, entity2)
        confidence = min(entity1.confidence, entity2.confidence) * 0.8  # Co-occurrence has lower confidence
        
        # Create or update edge
        edge_key = (node1_id, node2_id, edge_type)
        
        if edge_key in self.edges:
            # Update existing edge
            edge = self.edges[edge_key]
            edge.weight = max(edge.weight, weight)  # Keep highest weight
            edge.confidence = max(edge.confidence, confidence)
            edge.documents.add(doc_id)
        else:
            # Create new edge
            edge = GraphEdge(
                source=node1_id,
                target=node2_id,
                edge_type=edge_type,
                weight=weight,
                confidence=confidence,
                documents={doc_id},
                metadata={"creation_type": "co_occurrence"}
            )
            self.edges[edge_key] = edge
            
            # Add edge to NetworkX graph
            self.graph.add_edge(
                node1_id,
                node2_id,
                edge_type=edge_type,
                weight=weight,
                confidence=confidence,
                documents=list(edge.documents),
                metadata=edge.metadata
            )
    
    def _build_semantic_edges(self, documents: List[Document], document_entities: Dict[str, List[Entity]]) -> None:
        """Build semantic relationship edges using text analysis."""
        # This is a simplified implementation - in practice, you might use
        # more sophisticated NLP techniques for relationship extraction
        
        relationship_patterns = {
            "implements": [
                r"(\w+)\s+implements?\s+(\w+)",
                r"(\w+)\s+implementation\s+of\s+(\w+)",
            ],
            "extends": [
                r"(\w+)\s+extends?\s+(\w+)",
                r"(\w+)\s+extension\s+of\s+(\w+)",
                r"(\w+)\s+based\s+on\s+(\w+)",
            ],
            "requires": [
                r"(\w+)\s+requires?\s+(\w+)",
                r"(\w+)\s+depends?\s+on\s+(\w+)",
                r"(\w+)\s+needs?\s+(\w+)",
            ],
            "conflicts": [
                r"(\w+)\s+conflicts?\s+with\s+(\w+)",
                r"(\w+)\s+incompatible\s+with\s+(\w+)",
            ]
        }
        
        import re
        
        for doc_id, entities in document_entities.items():
            # Find document by metadata id
            document = None
            for doc in documents:
                if doc.metadata.get("id", "unknown") == doc_id:
                    document = doc
                    break
            
            if document is None:
                continue
            
            content = document.content.lower()
            
            # Find explicit relationships in text
            for relationship_type, patterns in relationship_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    
                    for match in matches:
                        if len(match) == 2:
                            source_text, target_text = match
                            self._create_semantic_edge(
                                source_text, target_text, relationship_type, 
                                entities, doc_id
                            )
    
    def _create_semantic_edge(self, source_text: str, target_text: str, 
                            relationship_type: str, entities: List[Entity], doc_id: str) -> None:
        """Create semantic relationship edge between entities."""
        # Find matching entities
        source_entity = self._find_matching_entity(source_text, entities)
        target_entity = self._find_matching_entity(target_text, entities)
        
        if not source_entity or not target_entity:
            return
        
        source_id = self._generate_node_id(self._normalize_entity_text(source_entity.text, source_entity.label))
        target_id = self._generate_node_id(self._normalize_entity_text(target_entity.text, target_entity.label))
        
        if source_id == target_id:
            return
        
        # High confidence for explicit relationships
        confidence = 0.9
        weight = 1.0
        
        edge_key = (source_id, target_id, relationship_type)
        
        if edge_key in self.edges:
            edge = self.edges[edge_key]
            edge.confidence = max(edge.confidence, confidence)
            edge.documents.add(doc_id)
        else:
            edge = GraphEdge(
                source=source_id,
                target=target_id,
                edge_type=relationship_type,
                weight=weight,
                confidence=confidence,
                documents={doc_id},
                metadata={"creation_type": "semantic_pattern"}
            )
            self.edges[edge_key] = edge
            
            # Add edge to NetworkX graph
            self.graph.add_edge(
                source_id,
                target_id,
                edge_type=relationship_type,
                weight=weight,
                confidence=confidence,
                documents=list(edge.documents),
                metadata=edge.metadata
            )
    
    def _find_matching_entity(self, text: str, entities: List[Entity]) -> Optional[Entity]:
        """Find entity that matches the given text."""
        text_lower = text.lower().strip()
        
        # Exact match first
        for entity in entities:
            if entity.text.lower().strip() == text_lower:
                return entity
        
        # Partial match
        for entity in entities:
            if text_lower in entity.text.lower() or entity.text.lower() in text_lower:
                return entity
        
        return None
    
    def _update_nodes(self, new_entities: Dict[str, List[Entity]]) -> None:
        """Update graph nodes with new entities."""
        self._build_nodes(new_entities)
    
    def _update_edges(self, new_documents: List[Document], new_entities: Dict[str, List[Entity]]) -> None:
        """Update graph edges with new documents and entities."""
        self._build_edges(new_documents, new_entities)
        
        # Mark documents as processed
        for document in new_documents:
            self.processed_documents.add(document.metadata.get("id", "unknown"))
    
    def _prune_graph(self) -> None:
        """Prune graph to keep it within size limits."""
        if len(self.nodes) <= self.config.max_graph_size:
            return
        
        start_time = time.time()
        
        # Calculate node importance scores
        node_scores = {}
        for node_id, node in self.nodes.items():
            # Score based on frequency, confidence, and connectivity
            degree = self.graph.degree(node_id) if self.graph.has_node(node_id) else 0
            score = (
                node.frequency * 0.4 +
                node.confidence * 0.3 +
                degree * 0.3
            )
            node_scores[node_id] = score
        
        # Keep top nodes
        nodes_to_keep = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)
        nodes_to_keep = nodes_to_keep[:self.config.max_graph_size]
        keep_ids = set(node_id for node_id, _ in nodes_to_keep)
        
        # Remove low-importance nodes
        nodes_to_remove = set(self.nodes.keys()) - keep_ids
        
        for node_id in nodes_to_remove:
            # Remove from our tracking
            if node_id in self.nodes:
                del self.nodes[node_id]
            
            # Remove from NetworkX graph
            if self.graph.has_node(node_id):
                self.graph.remove_node(node_id)
        
        # Clean up edges
        edges_to_remove = []
        for edge_key, edge in self.edges.items():
            if edge.source not in keep_ids or edge.target not in keep_ids:
                edges_to_remove.append(edge_key)
        
        for edge_key in edges_to_remove:
            del self.edges[edge_key]
        
        pruning_time = time.time() - start_time
        self.stats["pruning_operations"] += 1
        
        logger.info(
            f"Pruned graph in {pruning_time:.3f}s "
            f"(removed {len(nodes_to_remove)} nodes, {len(edges_to_remove)} edges)"
        )
    
    def _normalize_entity_text(self, text: str, entity_type: str) -> str:
        """Normalize entity text for consistent node creation."""
        # Basic normalization
        normalized = text.lower().strip()
        
        # Remove common prefixes/suffixes for technical terms
        if entity_type in ["TECH", "PROTOCOL"]:
            normalized = normalized.replace("the ", "").replace(" extension", "")
        
        return normalized
    
    def _generate_node_id(self, normalized_text: str) -> str:
        """Generate unique node ID from normalized text."""
        return hashlib.md5(normalized_text.encode()).hexdigest()[:12]
    
    def _map_entity_to_node_type(self, entity_type: str) -> str:
        """Map entity types to node types."""
        mapping = {
            "TECH": "concept",
            "PROTOCOL": "protocol", 
            "ARCH": "architecture",
            "EXTENSION": "extension"
        }
        return mapping.get(entity_type, "concept")
    
    def _determine_edge_type(self, entity1: Entity, entity2: Entity) -> str:
        """Determine edge type between two entities."""
        # Simple heuristics based on entity types
        if entity1.label == "EXTENSION" or entity2.label == "EXTENSION":
            return "extends"
        elif entity1.label == "PROTOCOL" and entity2.label == "ARCH":
            return "implements"
        elif entity1.label == "ARCH" and entity2.label == "TECH":
            return "requires"
        else:
            return "relates_to"  # Default relationship
    
    def _calculate_edge_weight(self, entity1: Entity, entity2: Entity) -> float:
        """Calculate edge weight between two entities."""
        # Weight based on entity confidence and proximity
        base_weight = (entity1.confidence + entity2.confidence) / 2
        
        # Boost weight if entities are close in text
        if hasattr(entity1, 'start_pos') and hasattr(entity2, 'start_pos'):
            distance = abs(entity1.start_pos - entity2.start_pos)
            if distance < 100:  # Close entities
                proximity_bonus = 0.2
            else:
                proximity_bonus = 0.0
        else:
            proximity_bonus = 0.0
        
        return min(base_weight + proximity_bonus, 1.0)
    
    def _update_statistics(self, documents: List[Document], construction_time: float) -> None:
        """Update graph construction statistics."""
        self.stats["documents_processed"] += len(documents)
        self.stats["total_nodes"] = len(self.nodes)
        self.stats["total_edges"] = len(self.edges)
        self.stats["construction_time"] += construction_time
        
        # Estimate memory usage (rough approximation)
        node_memory = len(self.nodes) * 200  # Bytes per node
        edge_memory = len(self.edges) * 150  # Bytes per edge
        self.stats["memory_usage_mb"] = (node_memory + edge_memory) / (1024 * 1024)
        
        # Update processed documents
        for document in documents:
            self.processed_documents.add(document.metadata.get("id", "unknown"))
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive graph statistics.
        
        Returns:
            Dictionary with graph statistics
        """
        stats = self.stats.copy()
        
        # Add NetworkX graph metrics
        if self.graph:
            stats["networkx_nodes"] = self.graph.number_of_nodes()
            stats["networkx_edges"] = self.graph.number_of_edges()
            
            if self.graph.number_of_nodes() > 0:
                stats["avg_degree"] = sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes()
                stats["density"] = nx.density(self.graph)
                
                # Calculate connected components
                if self.graph.is_directed():
                    stats["strongly_connected_components"] = nx.number_strongly_connected_components(self.graph)
                    stats["weakly_connected_components"] = nx.number_weakly_connected_components(self.graph)
                else:
                    stats["connected_components"] = nx.number_connected_components(self.graph)
            else:
                stats["avg_degree"] = 0.0
                stats["density"] = 0.0
                stats["connected_components"] = 0
        
        # Node type distribution
        node_type_counts = defaultdict(int)
        for node in self.nodes.values():
            node_type_counts[node.node_type] += 1
        stats["node_type_distribution"] = dict(node_type_counts)
        
        # Edge type distribution
        edge_type_counts = defaultdict(int)
        for edge in self.edges.values():
            edge_type_counts[edge.edge_type] += 1
        stats["edge_type_distribution"] = dict(edge_type_counts)
        
        return stats
    
    def get_graph(self) -> nx.DiGraph:
        """Get the constructed NetworkX graph."""
        return self.graph
    
    def get_subgraph(self, node_ids: List[str], radius: int = 1) -> nx.DiGraph:
        """
        Get subgraph around specified nodes.
        
        Args:
            node_ids: List of central node IDs
            radius: Distance from central nodes to include
            
        Returns:
            NetworkX subgraph
        """
        if not node_ids or not self.graph:
            return nx.DiGraph()
        
        # Find all nodes within radius
        subgraph_nodes = set(node_ids)
        
        for _ in range(radius):
            new_nodes = set()
            for node_id in subgraph_nodes:
                if self.graph.has_node(node_id):
                    # Add neighbors
                    new_nodes.update(self.graph.neighbors(node_id))
                    new_nodes.update(self.graph.predecessors(node_id))
            subgraph_nodes.update(new_nodes)
        
        # Create subgraph
        return self.graph.subgraph(subgraph_nodes).copy()
    
    def reset_graph(self) -> None:
        """Reset the graph and all tracking data."""
        self.graph.clear()
        self.nodes.clear()
        self.edges.clear()
        self.document_entities.clear()
        self.processed_documents.clear()
        
        # Reset statistics except configuration-dependent ones
        self.stats = {
            "documents_processed": 0,
            "total_nodes": 0,
            "total_edges": 0,
            "construction_time": 0.0,
            "last_update_time": 0.0,
            "memory_usage_mb": 0.0,
            "pruning_operations": 0
        }
        
        logger.info("Graph reset completed")