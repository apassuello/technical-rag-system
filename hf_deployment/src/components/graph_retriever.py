"""
Self-contained Graph Enhancement for HF Deployment.

Simplified implementation of graph-based retrieval enhancement without 
external dependencies from the main project. Uses NetworkX for graph operations.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict

try:
    import networkx as nx
    import spacy
    GRAPH_LIBRARIES_AVAILABLE = True
except ImportError:
    nx = None
    spacy = None
    GRAPH_LIBRARIES_AVAILABLE = False

from .base_reranker import Document

logger = logging.getLogger(__name__)


class GraphRetriever:
    """
    Self-contained graph-based document relationship enhancement.
    
    This implementation provides graph analysis capabilities for understanding
    document relationships and enhancing retrieval through entity linking.
    
    Features:
    - Document relationship mapping using NetworkX
    - Entity extraction with spaCy
    - Graph-based document scoring
    - Simple entity linking across documents
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize graph retriever.
        
        Args:
            config: Configuration dictionary with graph settings
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        
        # Graph configuration
        self.similarity_threshold = config.get("similarity_threshold", 0.65)
        self.max_connections_per_document = config.get("max_connections_per_document", 15)
        self.use_pagerank = config.get("use_pagerank", True)
        self.pagerank_damping = config.get("pagerank_damping", 0.85)
        self.max_graph_hops = config.get("max_graph_hops", 3)
        self.graph_weight_decay = config.get("graph_weight_decay", 0.5)
        
        # Components
        self.graph = None
        self.nlp = None
        self._initialized = False
        
        # Statistics
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "graph_nodes": 0,
            "graph_edges": 0,
            "entities_extracted": 0
        }
        
        # Check availability
        if not GRAPH_LIBRARIES_AVAILABLE:
            logger.warning("NetworkX or spaCy not available, disabling graph enhancement")
            self.enabled = False
        
        # Initialize if enabled
        if self.enabled:
            self._initialize_components()
        
        logger.info(f"GraphRetriever initialized, enabled={self.enabled}")
    
    def _initialize_components(self):
        """Initialize graph and NLP components."""
        try:
            # Initialize graph
            self.graph = nx.Graph()
            
            # Initialize spaCy model for entity extraction
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy English model not found, using basic tokenization")
                self.nlp = None
            
            self._initialized = True
            logger.info("Graph components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize graph components: {e}")
            self.enabled = False
            self._initialized = False
    
    def build_document_graph(self, documents: List[Document]):
        """
        Build a graph from documents using entity extraction and similarity.
        
        Args:
            documents: List of documents to build graph from
        """
        if not self.enabled or not self._initialized:
            return
        
        try:
            # Clear existing graph
            self.graph.clear()
            
            # Extract entities from each document
            doc_entities = {}
            for i, doc in enumerate(documents):
                entities = self._extract_entities(doc.content)
                doc_id = f"doc_{i}"
                
                # Add document node
                self.graph.add_node(doc_id, 
                                  type="document", 
                                  content=doc.content,
                                  metadata=doc.metadata,
                                  entities=entities)
                
                doc_entities[doc_id] = entities
                
                # Add entity nodes and connections
                for entity in entities:
                    entity_id = f"entity_{entity.lower().replace(' ', '_')}"
                    
                    # Add entity node if not exists
                    if not self.graph.has_node(entity_id):
                        self.graph.add_node(entity_id, type="entity", text=entity)
                    
                    # Connect document to entity
                    self.graph.add_edge(doc_id, entity_id, weight=1.0)
            
            # Connect documents with shared entities
            doc_ids = [f"doc_{i}" for i in range(len(documents))]
            for i, doc_id1 in enumerate(doc_ids):
                for j, doc_id2 in enumerate(doc_ids[i+1:], i+1):
                    shared_entities = set(doc_entities[doc_id1]) & set(doc_entities[doc_id2])
                    if shared_entities:
                        # Weight based on number of shared entities
                        weight = len(shared_entities) / max(len(doc_entities[doc_id1]), 
                                                           len(doc_entities[doc_id2]))
                        if weight >= self.similarity_threshold:
                            self.graph.add_edge(doc_id1, doc_id2, 
                                              weight=weight, 
                                              shared_entities=list(shared_entities))
            
            # Update stats
            self.stats["graph_nodes"] = self.graph.number_of_nodes()
            self.stats["graph_edges"] = self.graph.number_of_edges()
            self.stats["entities_extracted"] = sum(len(entities) for entities in doc_entities.values())
            
            logger.debug(f"Built graph with {self.stats['graph_nodes']} nodes and {self.stats['graph_edges']} edges")
            
        except Exception as e:
            logger.error(f"Failed to build document graph: {e}")
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        Extract entities from text using spaCy or simple heuristics.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        try:
            if self.nlp:
                # Use spaCy for entity extraction
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ in ["ORG", "PERSON", "GPE", "PRODUCT", "TECH"]:
                        entities.append(ent.text)
            else:
                # Simple fallback: extract capitalized words and phrases
                words = text.split()
                for i, word in enumerate(words):
                    if word[0].isupper() and len(word) > 2:
                        # Check for multi-word entities
                        entity = word
                        for j in range(i+1, min(i+3, len(words))):
                            if words[j][0].isupper():
                                entity += " " + words[j]
                            else:
                                break
                        entities.append(entity)
            
            # Remove duplicates and short entities
            entities = list(set([e for e in entities if len(e) > 2]))
            
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
        
        return entities
    
    def enhance_retrieval_scores(
        self, 
        query: str, 
        documents: List[Document], 
        initial_scores: List[float]
    ) -> List[float]:
        """
        Enhance retrieval scores using graph-based relationships.
        
        Args:
            query: Search query
            documents: List of documents
            initial_scores: Initial retrieval scores
            
        Returns:
            Enhanced scores incorporating graph relationships
        """
        self.stats["total_queries"] += 1
        
        try:
            if not self.enabled or not self._initialized or not documents:
                return initial_scores
            
            # Build graph if not already built
            if self.graph.number_of_nodes() == 0:
                self.build_document_graph(documents)
            
            # Extract query entities
            query_entities = self._extract_entities(query)
            if not query_entities:
                return initial_scores
            
            # Calculate graph-based scores
            enhanced_scores = initial_scores.copy()
            
            for i, doc in enumerate(documents):
                doc_id = f"doc_{i}"
                if not self.graph.has_node(doc_id):
                    continue
                
                # Calculate graph score based on:
                # 1. Direct entity matches
                # 2. Graph connectivity (PageRank if enabled)
                # 3. Neighbor relationships
                
                graph_score = 0.0
                
                # Direct entity match score
                doc_entities = self.graph.nodes[doc_id].get("entities", [])
                entity_matches = len(set(query_entities) & set(doc_entities))
                if entity_matches > 0:
                    graph_score += entity_matches / len(query_entities)
                
                # PageRank score if enabled
                if self.use_pagerank and self.graph.number_of_edges() > 0:
                    try:
                        pagerank_scores = nx.pagerank(self.graph, damping=self.pagerank_damping)
                        graph_score += pagerank_scores.get(doc_id, 0.0) * 10  # Scale up PageRank
                    except:
                        pass  # Skip if PageRank fails
                
                # Neighbor connectivity score
                neighbors = list(self.graph.neighbors(doc_id))
                connected_entities = [n for n in neighbors if self.graph.nodes[n]["type"] == "entity"]
                query_entity_neighbors = [e for e in connected_entities 
                                        if self.graph.nodes[e]["text"] in query_entities]
                if query_entity_neighbors:
                    graph_score += len(query_entity_neighbors) * 0.5
                
                # Combine with initial score
                if graph_score > 0:
                    # Weighted combination: 70% original score, 30% graph score
                    enhanced_scores[i] = initial_scores[i] * 0.7 + graph_score * 0.3
            
            self.stats["successful_queries"] += 1
            logger.debug(f"Enhanced scores using graph relationships")
            
            return enhanced_scores
            
        except Exception as e:
            self.stats["failed_queries"] += 1
            logger.error(f"Graph enhancement failed: {e}")
            return initial_scores
    
    def get_document_connections(self, doc_index: int, documents: List[Document]) -> Dict[str, Any]:
        """
        Get graph connections for a specific document.
        
        Args:
            doc_index: Index of the document
            documents: List of all documents
            
        Returns:
            Dictionary with connection information
        """
        if not self.enabled or not self._initialized:
            return {"connections": 0, "related_docs": [], "entities": []}
        
        try:
            doc_id = f"doc_{doc_index}"
            if not self.graph.has_node(doc_id):
                return {"connections": 0, "related_docs": [], "entities": []}
            
            # Get connected documents
            related_docs = []
            for neighbor in self.graph.neighbors(doc_id):
                if self.graph.nodes[neighbor]["type"] == "document":
                    neighbor_index = int(neighbor.split("_")[1])
                    edge_data = self.graph.edges[doc_id, neighbor]
                    related_docs.append({
                        "index": neighbor_index,
                        "weight": edge_data.get("weight", 0.0),
                        "shared_entities": edge_data.get("shared_entities", [])
                    })
            
            # Get connected entities
            entities = []
            for neighbor in self.graph.neighbors(doc_id):
                if self.graph.nodes[neighbor]["type"] == "entity":
                    entities.append(self.graph.nodes[neighbor]["text"])
            
            return {
                "connections": len(related_docs),
                "related_docs": related_docs,
                "entities": entities
            }
            
        except Exception as e:
            logger.error(f"Failed to get document connections: {e}")
            return {"connections": 0, "related_docs": [], "entities": []}
    
    def is_enabled(self) -> bool:
        """Check if graph enhancement is enabled."""
        return self.enabled and self._initialized
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph retriever statistics."""
        stats = self.stats.copy()
        stats.update({
            "enabled": self.enabled,
            "initialized": self._initialized,
            "graph_libraries_available": GRAPH_LIBRARIES_AVAILABLE,
            "nlp_model_available": self.nlp is not None
        })
        return stats
    
    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "graph_nodes": 0,
            "graph_edges": 0,
            "entities_extracted": 0
        }