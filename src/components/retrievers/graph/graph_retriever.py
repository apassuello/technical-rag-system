"""
Graph retriever for Epic 2 Week 2.

This module provides graph-based retrieval capabilities using NetworkX graphs
to find relevant documents through graph traversal algorithms including
shortest path, random walk, and subgraph expansion strategies.
"""

import logging
import time
import random
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

try:
    import networkx as nx
    import numpy as np
except ImportError:
    nx = None
    np = None

from src.core.interfaces import Document, RetrievalResult, Embedder
from .config.graph_config import GraphRetrievalConfig
from .document_graph_builder import DocumentGraphBuilder

logger = logging.getLogger(__name__)


@dataclass
class GraphSearchResult:
    """Represents a graph-based search result."""
    node_id: str
    node_text: str
    node_type: str
    score: float
    path_length: int
    path_nodes: List[str]
    documents: Set[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class GraphRetrieverError(Exception):
    """Raised when graph retrieval operations fail."""
    pass


class GraphRetriever:
    """
    Graph-based document retriever using knowledge graphs.
    
    This class provides sophisticated graph retrieval capabilities by:
    - Converting queries to graph node matches
    - Executing graph traversal algorithms (shortest path, random walk, subgraph expansion)
    - Scoring nodes based on relevance and graph structure
    - Converting graph results back to document retrievals
    
    Algorithms supported:
    - shortest_path: Find shortest paths between query nodes and all other nodes
    - random_walk: Perform random walks starting from query nodes
    - subgraph_expansion: Expand subgraphs around query nodes
    """
    
    def __init__(self, config: GraphRetrievalConfig, graph_builder: DocumentGraphBuilder, embedder: Embedder):
        """
        Initialize the graph retriever.
        
        Args:
            config: Graph retrieval configuration
            graph_builder: Document graph builder for graph access
            embedder: Embedder for query processing
        """
        if nx is None:
            raise GraphRetrieverError("NetworkX is not installed. Install with: pip install networkx")
        
        self.config = config
        self.graph_builder = graph_builder
        self.embedder = embedder
        
        # Cache for query processing
        self.query_cache = {}
        self.cache_enabled = True
        
        # Statistics
        self.stats = {
            "queries_processed": 0,
            "total_results_returned": 0,
            "avg_search_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "algorithm_usage": defaultdict(int)
        }
        
        logger.info(f"GraphRetriever initialized with algorithms: {self.config.algorithms}")
    
    def retrieve(self, query: str, k: int = 10, algorithm: Optional[str] = None) -> List[RetrievalResult]:
        """
        Retrieve documents using graph-based search.
        
        Args:
            query: Search query string
            k: Number of results to return
            algorithm: Specific algorithm to use (optional)
            
        Returns:
            List of retrieval results sorted by relevance score
        """
        start_time = time.time()
        
        try:
            # Check cache
            cache_key = f"{query}_{k}_{algorithm}"
            if self.cache_enabled and cache_key in self.query_cache:
                self.stats["cache_hits"] += 1
                return self.query_cache[cache_key]
            
            self.stats["cache_misses"] += 1
            
            # Get graph
            graph = self.graph_builder.get_graph()
            if not graph or graph.number_of_nodes() == 0:
                logger.warning("No graph available for retrieval")
                return []
            
            # Find query nodes (entities matching the query)
            query_nodes = self._find_query_nodes(query, graph)
            if not query_nodes:
                logger.info(f"No matching graph nodes found for query: {query}")
                return []
            
            logger.info(f"Found {len(query_nodes)} query nodes for: {query}")
            
            # Execute graph search algorithms
            all_results = []
            algorithms_to_use = [algorithm] if algorithm else self.config.algorithms
            
            for algo in algorithms_to_use:
                if algo not in ["shortest_path", "random_walk", "subgraph_expansion"]:
                    logger.warning(f"Unknown algorithm: {algo}")
                    continue
                
                algo_results = self._execute_algorithm(algo, query_nodes, graph, k)
                all_results.extend(algo_results)
                self.stats["algorithm_usage"][algo] += 1
            
            # Aggregate and score results
            final_results = self._aggregate_results(all_results, k)
            
            # Convert to RetrievalResult objects
            retrieval_results = self._convert_to_retrieval_results(final_results, query)
            
            # Cache results
            if self.cache_enabled and len(self.query_cache) < 1000:  # Limit cache size
                self.query_cache[cache_key] = retrieval_results
            
            # Update statistics
            search_time = time.time() - start_time
            self.stats["queries_processed"] += 1
            self.stats["total_results_returned"] += len(retrieval_results)
            self.stats["avg_search_time"] = (
                (self.stats["avg_search_time"] * (self.stats["queries_processed"] - 1) + search_time) /
                self.stats["queries_processed"]
            )
            
            logger.info(f"Graph retrieval completed in {search_time:.3f}s ({len(retrieval_results)} results)")
            
            return retrieval_results
            
        except Exception as e:
            logger.error(f"Graph retrieval failed: {str(e)}")
            raise GraphRetrieverError(f"Failed to retrieve documents: {str(e)}") from e
    
    def _find_query_nodes(self, query: str, graph: nx.DiGraph) -> List[str]:
        """
        Find graph nodes that match the query.
        
        Args:
            query: Search query string
            graph: NetworkX graph
            
        Returns:
            List of matching node IDs
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        matching_nodes = []
        
        for node_id in graph.nodes():
            node_data = graph.nodes[node_id]
            node_text = node_data.get("text", "").lower()
            
            # Exact text match
            if query_lower in node_text or node_text in query_lower:
                matching_nodes.append(node_id)
                continue
            
            # Word overlap match
            node_words = set(node_text.split())
            overlap = len(query_words & node_words)
            
            if overlap > 0 and overlap / len(query_words) > 0.3:  # 30% word overlap
                matching_nodes.append(node_id)
        
        # If no direct matches, try fuzzy matching
        if not matching_nodes:
            matching_nodes = self._fuzzy_node_matching(query, graph)
        
        return matching_nodes[:10]  # Limit to prevent excessive computation
    
    def _fuzzy_node_matching(self, query: str, graph: nx.DiGraph) -> List[str]:
        """Perform fuzzy matching to find relevant nodes."""
        query_embedding = self.embedder.embed([query])[0]
        
        node_similarities = []
        for node_id in graph.nodes():
            node_data = graph.nodes[node_id]
            node_text = node_data.get("text", "")
            
            if node_text:
                try:
                    node_embedding = self.embedder.embed([node_text])[0]
                    similarity = np.dot(query_embedding, node_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(node_embedding)
                    )
                    node_similarities.append((node_id, similarity))
                except Exception as e:
                    logger.debug(f"Failed to compute similarity for node {node_id}: {str(e)}")
        
        # Sort by similarity and return top matches
        node_similarities.sort(key=lambda x: x[1], reverse=True)
        threshold = 0.5  # Minimum similarity threshold
        
        return [node_id for node_id, sim in node_similarities if sim > threshold][:5]
    
    def _execute_algorithm(self, algorithm: str, query_nodes: List[str], 
                          graph: nx.DiGraph, k: int) -> List[GraphSearchResult]:
        """
        Execute a specific graph search algorithm.
        
        Args:
            algorithm: Algorithm name
            query_nodes: Starting nodes for search
            graph: NetworkX graph
            k: Number of results to find
            
        Returns:
            List of graph search results
        """
        if algorithm == "shortest_path":
            return self._shortest_path_search(query_nodes, graph, k)
        elif algorithm == "random_walk":
            return self._random_walk_search(query_nodes, graph, k)
        elif algorithm == "subgraph_expansion":
            return self._subgraph_expansion_search(query_nodes, graph, k)
        else:
            logger.warning(f"Unknown algorithm: {algorithm}")
            return []
    
    def _shortest_path_search(self, query_nodes: List[str], graph: nx.DiGraph, k: int) -> List[GraphSearchResult]:
        """Find nodes using shortest path distances from query nodes."""
        results = []
        
        for query_node in query_nodes:
            if not graph.has_node(query_node):
                continue
            
            try:
                # Compute shortest paths to all nodes
                if graph.is_directed():
                    path_lengths = nx.single_source_shortest_path_length(
                        graph, query_node, cutoff=self.config.max_path_length
                    )
                else:
                    path_lengths = nx.single_source_shortest_path_length(
                        graph.to_undirected(), query_node, cutoff=self.config.max_path_length
                    )
                
                for target_node, path_length in path_lengths.items():
                    if target_node == query_node:
                        continue
                    
                    # Calculate score based on path length and node properties
                    node_data = graph.nodes[target_node]
                    base_score = node_data.get("confidence", 0.5)
                    frequency_score = min(node_data.get("frequency", 1) / 10.0, 1.0)
                    
                    # Decrease score with path length
                    path_penalty = (self.config.max_path_length - path_length + 1) / self.config.max_path_length
                    score = (base_score * 0.5 + frequency_score * 0.3 + path_penalty * 0.2)
                    
                    result = GraphSearchResult(
                        node_id=target_node,
                        node_text=node_data.get("text", ""),
                        node_type=node_data.get("node_type", ""),
                        score=score,
                        path_length=path_length,
                        path_nodes=[query_node, target_node],  # Simplified path
                        documents=set(node_data.get("documents", [])),
                        metadata={"algorithm": "shortest_path", "query_node": query_node}
                    )
                    results.append(result)
                    
            except Exception as e:
                logger.warning(f"Shortest path search failed for node {query_node}: {str(e)}")
        
        return results
    
    def _random_walk_search(self, query_nodes: List[str], graph: nx.DiGraph, k: int) -> List[GraphSearchResult]:
        """Find nodes using random walks from query nodes."""
        results = []
        node_visit_counts = defaultdict(int)
        
        for query_node in query_nodes:
            if not graph.has_node(query_node):
                continue
            
            # Perform multiple random walks
            for _ in range(self.config.random_walk_steps):
                current_node = query_node
                walk_length = 0
                max_walk_length = min(10, self.config.max_path_length * 2)
                
                while walk_length < max_walk_length:
                    # Get neighbors
                    if graph.is_directed():
                        neighbors = list(graph.successors(current_node))
                    else:
                        neighbors = list(graph.neighbors(current_node))
                    
                    if not neighbors:
                        break
                    
                    # Choose next node based on edge weights
                    next_node = self._weighted_random_choice(current_node, neighbors, graph)
                    node_visit_counts[next_node] += 1
                    
                    current_node = next_node
                    walk_length += 1
        
        # Convert visit counts to results
        for node_id, visit_count in node_visit_counts.items():
            if node_id in query_nodes:
                continue
            
            node_data = graph.nodes[node_id]
            
            # Score based on visit frequency and node properties
            visit_score = min(visit_count / 5.0, 1.0)  # Normalize visit count
            base_score = node_data.get("confidence", 0.5)
            frequency_score = min(node_data.get("frequency", 1) / 10.0, 1.0)
            
            score = visit_score * 0.5 + base_score * 0.3 + frequency_score * 0.2
            
            result = GraphSearchResult(
                node_id=node_id,
                node_text=node_data.get("text", ""),
                node_type=node_data.get("node_type", ""),
                score=score,
                path_length=1,  # Simplified for random walk
                path_nodes=[],  # Path not tracked in random walk
                documents=set(node_data.get("documents", [])),
                metadata={"algorithm": "random_walk", "visit_count": visit_count}
            )
            results.append(result)
        
        return results
    
    def _subgraph_expansion_search(self, query_nodes: List[str], graph: nx.DiGraph, k: int) -> List[GraphSearchResult]:
        """Find nodes by expanding subgraphs around query nodes."""
        results = []
        expanded_nodes = set()
        
        # Expand around each query node
        for query_node in query_nodes:
            if not graph.has_node(query_node):
                continue
            
            # Get subgraph around query node
            subgraph_nodes = self._get_subgraph_nodes(query_node, graph, self.config.subgraph_radius)
            
            for node_id in subgraph_nodes:
                if node_id in query_nodes or node_id in expanded_nodes:
                    continue
                
                expanded_nodes.add(node_id)
                node_data = graph.nodes[node_id]
                
                # Calculate distance from query node
                try:
                    if graph.is_directed():
                        distance = nx.shortest_path_length(graph, query_node, node_id)
                    else:
                        distance = nx.shortest_path_length(graph.to_undirected(), query_node, node_id)
                except nx.NetworkXNoPath:
                    distance = self.config.subgraph_radius + 1  # Beyond radius
                
                # Score based on distance and node properties
                node_degree = graph.degree(node_id)
                base_score = node_data.get("confidence", 0.5)
                centrality_score = min(node_degree / 10.0, 1.0)
                
                # Decrease score with distance
                distance_penalty = max(0, (self.config.subgraph_radius - distance + 1) / self.config.subgraph_radius)
                score = base_score * 0.4 + centrality_score * 0.3 + distance_penalty * 0.3
                
                result = GraphSearchResult(
                    node_id=node_id,
                    node_text=node_data.get("text", ""),
                    node_type=node_data.get("node_type", ""),
                    score=score,
                    path_length=distance,
                    path_nodes=[query_node, node_id],
                    documents=set(node_data.get("documents", [])),
                    metadata={"algorithm": "subgraph_expansion", "query_node": query_node, "degree": node_degree}
                )
                results.append(result)
        
        return results
    
    def _weighted_random_choice(self, current_node: str, neighbors: List[str], graph: nx.DiGraph) -> str:
        """Choose next node in random walk based on edge weights."""
        if not neighbors:
            return current_node
        
        # Get edge weights
        weights = []
        for neighbor in neighbors:
            edge_data = graph.get_edge_data(current_node, neighbor, default={})
            weight = edge_data.get("weight", 1.0)
            weights.append(weight)
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            probabilities = [w / total_weight for w in weights]
        else:
            probabilities = [1.0 / len(neighbors)] * len(neighbors)
        
        # Choose based on probabilities
        return np.random.choice(neighbors, p=probabilities)
    
    def _get_subgraph_nodes(self, center_node: str, graph: nx.DiGraph, radius: int) -> Set[str]:
        """Get all nodes within radius distance from center node."""
        nodes = {center_node}
        current_level = {center_node}
        
        for _ in range(radius):
            next_level = set()
            for node in current_level:
                if graph.is_directed():
                    neighbors = set(graph.successors(node)) | set(graph.predecessors(node))
                else:
                    neighbors = set(graph.neighbors(node))
                next_level.update(neighbors)
            
            nodes.update(next_level)
            current_level = next_level - nodes  # Only new nodes for next iteration
        
        return nodes
    
    def _aggregate_results(self, results: List[GraphSearchResult], k: int) -> List[GraphSearchResult]:
        """Aggregate results from multiple algorithms."""
        # Group results by node
        node_results = defaultdict(list)
        for result in results:
            node_results[result.node_id].append(result)
        
        # Aggregate scores for each node
        aggregated_results = []
        for node_id, node_result_list in node_results.items():
            # Combine scores based on configuration
            if self.config.score_aggregation == "max":
                best_result = max(node_result_list, key=lambda r: r.score)
                aggregated_score = best_result.score
            elif self.config.score_aggregation == "average":
                aggregated_score = sum(r.score for r in node_result_list) / len(node_result_list)
            elif self.config.score_aggregation == "weighted_average":
                # Weight by algorithm performance (simplified)
                weights = {"shortest_path": 0.4, "random_walk": 0.3, "subgraph_expansion": 0.3}
                total_weight = 0
                weighted_sum = 0
                for result in node_result_list:
                    algo = result.metadata.get("algorithm", "shortest_path")
                    weight = weights.get(algo, 0.33)
                    weighted_sum += result.score * weight
                    total_weight += weight
                aggregated_score = weighted_sum / total_weight if total_weight > 0 else 0
            else:
                aggregated_score = max(r.score for r in node_result_list)
            
            # Use the best result as template and update score
            best_result = max(node_result_list, key=lambda r: r.score)
            best_result.score = aggregated_score
            
            # Merge documents from all results
            all_documents = set()
            for result in node_result_list:
                all_documents.update(result.documents)
            best_result.documents = all_documents
            
            aggregated_results.append(best_result)
        
        # Sort by score and return top k
        aggregated_results.sort(key=lambda r: r.score, reverse=True)
        return aggregated_results[:k]
    
    def _convert_to_retrieval_results(self, graph_results: List[GraphSearchResult], 
                                    query: str) -> List[RetrievalResult]:
        """Convert graph search results to retrieval results."""
        retrieval_results = []
        
        # Get all documents mentioned in results
        all_document_ids = set()
        for result in graph_results:
            all_document_ids.update(result.documents)
        
        # Get actual document objects (simplified - in practice you'd have a document store)
        # For now, create placeholder documents
        document_scores = defaultdict(float)
        document_details = {}
        
        for result in graph_results:
            for doc_id in result.documents:
                # Aggregate scores for documents
                document_scores[doc_id] += result.score
                if doc_id not in document_details:
                    document_details[doc_id] = {
                        "nodes": [],
                        "node_types": [],
                        "algorithms": []
                    }
                
                document_details[doc_id]["nodes"].append(result.node_text)
                document_details[doc_id]["node_types"].append(result.node_type)
                document_details[doc_id]["algorithms"].append(result.metadata.get("algorithm", "unknown"))
        
        # Create retrieval results
        for doc_id, score in sorted(document_scores.items(), key=lambda x: x[1], reverse=True):
            # Create a placeholder document (in practice, retrieve from document store)
            from src.core.interfaces import Document
            document = Document(
                content=f"Document {doc_id}",  # Placeholder
                metadata={
                    "id": doc_id,
                    "graph_nodes": document_details[doc_id]["nodes"],
                    "graph_node_types": document_details[doc_id]["node_types"],
                    "graph_algorithms": document_details[doc_id]["algorithms"]
                }
            )
            
            retrieval_result = RetrievalResult(
                document=document,
                score=float(score),
                retrieval_method="graph_based"
            )
            retrieval_results.append(retrieval_result)
        
        return retrieval_results[:self.config.max_graph_results]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get graph retrieval statistics.
        
        Returns:
            Dictionary with retrieval statistics
        """
        stats = self.stats.copy()
        
        # Add algorithm usage percentages
        total_usage = sum(self.stats["algorithm_usage"].values())
        if total_usage > 0:
            stats["algorithm_usage_percentages"] = {
                algo: (count / total_usage) * 100
                for algo, count in self.stats["algorithm_usage"].items()
            }
        else:
            stats["algorithm_usage_percentages"] = {}
        
        # Cache statistics
        total_queries = stats["cache_hits"] + stats["cache_misses"]
        if total_queries > 0:
            stats["cache_hit_rate"] = (stats["cache_hits"] / total_queries) * 100
        else:
            stats["cache_hit_rate"] = 0.0
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear the query cache."""
        self.query_cache.clear()
        logger.info("Query cache cleared")
    
    def reset_statistics(self) -> None:
        """Reset retrieval statistics."""
        self.stats = {
            "queries_processed": 0,
            "total_results_returned": 0,
            "avg_search_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "algorithm_usage": defaultdict(int)
        }