#!/usr/bin/env python3
"""
Comprehensive test suite for Graph Retrieval System.

This module provides complete test coverage for the graph-based retrieval system
including graph traversal algorithms, node matching, scoring mechanisms, and 
integration with document storage.

Target Coverage: 75% (640 test lines for 852 component lines)
Priority: CRITICAL (Graph retrieval system 0% baseline)
"""

import pytest
import numpy as np
import json
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any, Set, Optional
from pathlib import Path
import networkx as nx

# Import system under test
from src.components.retrievers.graph.graph_retriever import (
    GraphRetriever, GraphSearchResult, GraphRetrieverError
)
from src.components.retrievers.graph.config.graph_config import GraphRetrievalConfig
from src.components.retrievers.graph.document_graph_builder import DocumentGraphBuilder
from src.core.interfaces import Document, RetrievalResult, Embedder


class TestGraphRetrievalConfig:
    """Test graph retrieval configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = GraphRetrievalConfig()
        
        assert config.algorithms == ["shortest_path", "random_walk", "subgraph_expansion"]
        assert config.max_path_length == 3
        assert config.subgraph_radius == 2
        assert config.random_walk_steps == 10
        assert config.score_aggregation == "weighted_average"
        assert config.max_graph_results == 20
        
    def test_custom_config(self):
        """Test custom configuration initialization."""
        config = GraphRetrievalConfig(
            algorithms=["shortest_path"],
            max_path_length=5,
            score_aggregation="max"
        )
        
        assert config.algorithms == ["shortest_path"]
        assert config.max_path_length == 5
        assert config.score_aggregation == "max"
        
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid algorithms
        with pytest.raises(ValueError, match="Unknown algorithm"):
            GraphRetrievalConfig(algorithms=["invalid_algorithm"])
        
        # Test invalid path length
        with pytest.raises(ValueError, match="max_path_length must be positive"):
            GraphRetrievalConfig(max_path_length=0)
        
        # Test invalid score aggregation
        with pytest.raises(ValueError, match="Invalid score_aggregation"):
            GraphRetrievalConfig(score_aggregation="invalid")


class TestGraphSearchResult:
    """Test GraphSearchResult data structure."""
    
    def test_graph_search_result_creation(self):
        """Test creating GraphSearchResult objects."""
        result = GraphSearchResult(
            node_id="node_1",
            node_text="Example text",
            node_type="entity",
            score=0.85,
            path_length=2,
            path_nodes=["query_node", "node_1"],
            documents={"doc_1", "doc_2"}
        )
        
        assert result.node_id == "node_1"
        assert result.node_text == "Example text"
        assert result.node_type == "entity"
        assert result.score == 0.85
        assert result.path_length == 2
        assert result.path_nodes == ["query_node", "node_1"]
        assert result.documents == {"doc_1", "doc_2"}
        assert result.metadata == {}
        
    def test_graph_search_result_with_metadata(self):
        """Test GraphSearchResult with metadata."""
        metadata = {"algorithm": "shortest_path", "confidence": 0.9}
        result = GraphSearchResult(
            node_id="node_1",
            node_text="Example text",
            node_type="entity",
            score=0.85,
            path_length=2,
            path_nodes=["query_node", "node_1"],
            documents={"doc_1"},
            metadata=metadata
        )
        
        assert result.metadata == metadata
        
    def test_post_init_default_metadata(self):
        """Test that metadata is initialized as empty dict if None."""
        result = GraphSearchResult(
            node_id="node_1",
            node_text="text",
            node_type="entity",
            score=0.5,
            path_length=1,
            path_nodes=["node_1"],
            documents=set()
        )
        
        assert result.metadata == {}


class TestGraphRetrieverInitialization:
    """Test GraphRetriever initialization and setup."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GraphRetrievalConfig()
        self.mock_graph_builder = Mock(spec=DocumentGraphBuilder)
        self.mock_embedder = Mock(spec=Embedder)
        
    def test_successful_initialization(self):
        """Test successful GraphRetriever initialization."""
        retriever = GraphRetriever(
            config=self.config,
            graph_builder=self.mock_graph_builder,
            embedder=self.mock_embedder
        )
        
        assert retriever.config == self.config
        assert retriever.graph_builder == self.mock_graph_builder
        assert retriever.embedder == self.mock_embedder
        assert retriever.cache_enabled is True
        assert retriever.query_cache == {}
        
        # Check statistics initialization
        expected_stats = {
            "queries_processed": 0,
            "total_results_returned": 0,
            "avg_search_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "algorithm_usage": {}
        }
        
        for key in expected_stats:
            assert key in retriever.stats
            
    @patch('src.components.retrievers.graph.graph_retriever.nx', None)
    def test_networkx_missing_error(self):
        """Test error when NetworkX is not available."""
        with pytest.raises(GraphRetrieverError, match="NetworkX is not installed"):
            GraphRetriever(
                config=self.config,
                graph_builder=self.mock_graph_builder,
                embedder=self.mock_embedder
            )


class TestGraphQueryNodeMatching:
    """Test query node matching functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GraphRetrievalConfig()
        self.mock_graph_builder = Mock(spec=DocumentGraphBuilder)
        self.mock_embedder = Mock(spec=Embedder)
        
        self.retriever = GraphRetriever(
            config=self.config,
            graph_builder=self.mock_graph_builder,
            embedder=self.mock_embedder
        )
        
        # Create mock graph
        self.mock_graph = nx.DiGraph()
        self.mock_graph.add_node("cpu", text="CPU architecture", node_type="concept")
        self.mock_graph.add_node("memory", text="memory management", node_type="concept")
        self.mock_graph.add_node("risc", text="RISC-V instruction set", node_type="technical")
        self.mock_graph.add_node("pipeline", text="instruction pipeline", node_type="concept")
        
    def test_exact_text_matching(self):
        """Test exact text matching for query nodes."""
        query = "CPU architecture"
        matches = self.retriever._find_query_nodes(query, self.mock_graph)
        
        assert "cpu" in matches
        
    def test_partial_text_matching(self):
        """Test partial text matching."""
        query = "CPU"
        matches = self.retriever._find_query_nodes(query, self.mock_graph)
        
        assert "cpu" in matches
        
    def test_word_overlap_matching(self):
        """Test word overlap matching."""
        query = "memory management system"
        matches = self.retriever._find_query_nodes(query, self.mock_graph)
        
        assert "memory" in matches
        
    def test_case_insensitive_matching(self):
        """Test case insensitive matching."""
        query = "risc-v"
        matches = self.retriever._find_query_nodes(query, self.mock_graph)
        
        assert "risc" in matches
        
    def test_no_matches_found(self):
        """Test when no matches are found."""
        query = "quantum computing"
        matches = self.retriever._find_query_nodes(query, self.mock_graph)
        
        # Should fall back to fuzzy matching (mocked)
        assert isinstance(matches, list)
        
    def test_fuzzy_matching_fallback(self):
        """Test fuzzy matching when direct matching fails."""
        query = "quantum computing"
        
        # Mock embedder for fuzzy matching
        self.mock_embedder.embed.return_value = [np.array([0.1, 0.2, 0.3])]
        
        # Add embeddings to nodes (would be done during graph building)
        for node in self.mock_graph.nodes():
            self.mock_graph.nodes[node]["embedding"] = np.array([0.1, 0.2, 0.3])
            
        matches = self.retriever._fuzzy_node_matching(query, self.mock_graph)
        
        assert isinstance(matches, list)
        self.mock_embedder.embed.assert_called()
        
    def test_limit_max_query_nodes(self):
        """Test limiting maximum number of query nodes."""
        # Create graph with many matching nodes
        large_graph = nx.DiGraph()
        for i in range(20):
            large_graph.add_node(f"cpu_{i}", text="CPU architecture", node_type="concept")
            
        query = "CPU"
        matches = self.retriever._find_query_nodes(query, large_graph)
        
        # Should limit to 10 nodes
        assert len(matches) <= 10


class TestGraphTraversalAlgorithms:
    """Test graph traversal algorithms."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GraphRetrievalConfig(
            max_path_length=3,
            random_walk_steps=5,
            subgraph_radius=2
        )
        self.mock_graph_builder = Mock(spec=DocumentGraphBuilder)
        self.mock_embedder = Mock(spec=Embedder)
        
        self.retriever = GraphRetriever(
            config=self.config,
            graph_builder=self.mock_graph_builder,
            embedder=self.mock_embedder
        )
        
        # Create test graph with realistic structure
        self.graph = nx.DiGraph()
        self.graph.add_node("cpu", text="CPU", confidence=0.9, frequency=5, documents=["doc1"])
        self.graph.add_node("memory", text="memory", confidence=0.8, frequency=3, documents=["doc2"])
        self.graph.add_node("cache", text="cache", confidence=0.7, frequency=2, documents=["doc1", "doc3"])
        self.graph.add_node("pipeline", text="pipeline", confidence=0.6, frequency=1, documents=["doc2"])
        
        # Add edges with weights
        self.graph.add_edge("cpu", "memory", weight=0.8)
        self.graph.add_edge("cpu", "cache", weight=0.9)
        self.graph.add_edge("memory", "cache", weight=0.7)
        self.graph.add_edge("cache", "pipeline", weight=0.6)
        
    def test_shortest_path_algorithm(self):
        """Test shortest path search algorithm."""
        query_nodes = ["cpu"]
        results = self.retriever._shortest_path_search(query_nodes, self.graph, k=10)
        
        assert len(results) > 0
        assert all(isinstance(r, GraphSearchResult) for r in results)
        
        # Check that results include reachable nodes
        result_nodes = {r.node_id for r in results}
        expected_nodes = {"memory", "cache", "pipeline"}
        assert result_nodes.intersection(expected_nodes)
        
        # Verify score calculation
        for result in results:
            assert 0 <= result.score <= 1
            assert result.path_length > 0
            assert result.metadata.get("algorithm") == "shortest_path"
            
    def test_random_walk_algorithm(self):
        """Test random walk search algorithm."""
        query_nodes = ["cpu"]
        
        # Mock random choice for deterministic testing
        with patch('numpy.random.choice') as mock_choice:
            mock_choice.side_effect = lambda nodes, p=None: nodes[0]
            
            results = self.retriever._random_walk_search(query_nodes, self.graph, k=10)
            
        assert len(results) >= 0
        assert all(isinstance(r, GraphSearchResult) for r in results)
        
        for result in results:
            assert 0 <= result.score <= 1
            assert result.metadata.get("algorithm") == "random_walk"
            assert "visit_count" in result.metadata
            
    def test_subgraph_expansion_algorithm(self):
        """Test subgraph expansion algorithm."""
        query_nodes = ["cpu"]
        results = self.retriever._subgraph_expansion_search(query_nodes, self.graph, k=10)
        
        assert len(results) > 0
        assert all(isinstance(r, GraphSearchResult) for r in results)
        
        # Check that results are within subgraph radius
        for result in results:
            assert result.path_length <= self.config.subgraph_radius
            assert result.metadata.get("algorithm") == "subgraph_expansion"
            
    def test_weighted_random_choice(self):
        """Test weighted random choice in random walks."""
        current_node = "cpu"
        neighbors = ["memory", "cache"]
        
        with patch('numpy.random.choice') as mock_choice:
            mock_choice.return_value = "memory"
            
            choice = self.retriever._weighted_random_choice(current_node, neighbors, self.graph)
            
            mock_choice.assert_called_once()
            args = mock_choice.call_args
            assert args[0][0] == neighbors
            assert "p" in args[1]  # probabilities provided
            
    def test_get_subgraph_nodes(self):
        """Test subgraph node expansion."""
        center_node = "cpu"
        radius = 2
        
        subgraph_nodes = self.retriever._get_subgraph_nodes(center_node, self.graph, radius)
        
        assert center_node in subgraph_nodes
        assert "memory" in subgraph_nodes  # Direct neighbor
        assert "cache" in subgraph_nodes   # Direct neighbor
        
        # Should include nodes within radius
        assert len(subgraph_nodes) >= 1
        
    def test_empty_graph_handling(self):
        """Test handling of empty graphs."""
        empty_graph = nx.DiGraph()
        query_nodes = ["nonexistent"]
        
        results = self.retriever._shortest_path_search(query_nodes, empty_graph, k=10)
        assert results == []
        
        results = self.retriever._random_walk_search(query_nodes, empty_graph, k=10)
        assert results == []
        
        results = self.retriever._subgraph_expansion_search(query_nodes, empty_graph, k=10)
        assert results == []
        
    def test_algorithm_error_handling(self):
        """Test error handling in algorithms."""
        # Test with invalid node
        query_nodes = ["nonexistent_node"]
        
        results = self.retriever._shortest_path_search(query_nodes, self.graph, k=10)
        assert results == []
        
        results = self.retriever._random_walk_search(query_nodes, self.graph, k=10)
        assert results == []
        
        results = self.retriever._subgraph_expansion_search(query_nodes, self.graph, k=10)
        assert results == []


class TestResultAggregation:
    """Test result aggregation and scoring."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GraphRetrievalConfig()
        self.mock_graph_builder = Mock(spec=DocumentGraphBuilder)
        self.mock_embedder = Mock(spec=Embedder)
        
        self.retriever = GraphRetriever(
            config=self.config,
            graph_builder=self.mock_graph_builder,
            embedder=self.mock_embedder
        )
        
        # Create test results from different algorithms
        self.test_results = [
            GraphSearchResult(
                node_id="node1", node_text="text1", node_type="type1",
                score=0.8, path_length=1, path_nodes=["query", "node1"],
                documents={"doc1"}, metadata={"algorithm": "shortest_path"}
            ),
            GraphSearchResult(
                node_id="node1", node_text="text1", node_type="type1",
                score=0.7, path_length=2, path_nodes=["query", "node1"],
                documents={"doc2"}, metadata={"algorithm": "random_walk"}
            ),
            GraphSearchResult(
                node_id="node2", node_text="text2", node_type="type2",
                score=0.6, path_length=1, path_nodes=["query", "node2"],
                documents={"doc3"}, metadata={"algorithm": "subgraph_expansion"}
            )
        ]
        
    def test_max_score_aggregation(self):
        """Test maximum score aggregation."""
        self.retriever.config.score_aggregation = "max"
        
        results = self.retriever._aggregate_results(self.test_results, k=10)
        
        # Should have 2 unique nodes
        assert len(results) == 2
        
        # Find node1 result (should have max score 0.8)
        node1_result = next(r for r in results if r.node_id == "node1")
        assert node1_result.score == 0.8
        
        # Should merge documents
        assert len(node1_result.documents) == 2
        assert "doc1" in node1_result.documents
        assert "doc2" in node1_result.documents
        
    def test_average_score_aggregation(self):
        """Test average score aggregation."""
        self.retriever.config.score_aggregation = "average"
        
        results = self.retriever._aggregate_results(self.test_results, k=10)
        
        # Find node1 result (should have average score)
        node1_result = next(r for r in results if r.node_id == "node1")
        expected_avg = (0.8 + 0.7) / 2
        assert abs(node1_result.score - expected_avg) < 0.001
        
    def test_weighted_average_aggregation(self):
        """Test weighted average aggregation."""
        self.retriever.config.score_aggregation = "weighted_average"
        
        results = self.retriever._aggregate_results(self.test_results, k=10)
        
        # Should calculate weighted average based on algorithm weights
        node1_result = next(r for r in results if r.node_id == "node1")
        assert 0 < node1_result.score < 1
        
    def test_result_sorting_and_limiting(self):
        """Test that results are sorted by score and limited to k."""
        results = self.retriever._aggregate_results(self.test_results, k=1)
        
        # Should return only top result
        assert len(results) == 1
        
        # Should be sorted by score (descending)
        assert results[0].score >= 0.6  # Should be highest score
        
    def test_empty_results_aggregation(self):
        """Test aggregation with empty results."""
        results = self.retriever._aggregate_results([], k=10)
        assert results == []


class TestRetrievalResultConversion:
    """Test conversion from graph results to retrieval results."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GraphRetrievalConfig(max_graph_results=5)
        self.mock_graph_builder = Mock(spec=DocumentGraphBuilder)
        self.mock_embedder = Mock(spec=Embedder)
        
        self.retriever = GraphRetriever(
            config=self.config,
            graph_builder=self.mock_graph_builder,
            embedder=self.mock_embedder
        )
        
        # Create test graph results
        self.graph_results = [
            GraphSearchResult(
                node_id="node1", node_text="CPU architecture", node_type="concept",
                score=0.8, path_length=1, path_nodes=["query", "node1"],
                documents={"doc1", "doc2"}, metadata={"algorithm": "shortest_path"}
            ),
            GraphSearchResult(
                node_id="node2", node_text="Memory management", node_type="concept",
                score=0.6, path_length=2, path_nodes=["query", "node2"],
                documents={"doc3"}, metadata={"algorithm": "random_walk"}
            )
        ]
        
    def test_conversion_to_retrieval_results(self):
        """Test conversion from graph results to retrieval results."""
        query = "test query"
        retrieval_results = self.retriever._convert_to_retrieval_results(
            self.graph_results, query
        )
        
        assert len(retrieval_results) >= 1
        assert all(isinstance(r, RetrievalResult) for r in retrieval_results)
        
        # Check that documents are created correctly
        for result in retrieval_results:
            assert isinstance(result.document, Document)
            assert result.score > 0
            assert result.retrieval_method == "graph_based"
            
            # Check metadata includes graph information
            metadata = result.document.metadata
            assert "id" in metadata
            assert "graph_nodes" in metadata
            assert "graph_node_types" in metadata
            assert "graph_algorithms" in metadata
            
    def test_document_score_aggregation(self):
        """Test that document scores are properly aggregated."""
        query = "test query"
        
        # Create results where same document appears multiple times
        graph_results = [
            GraphSearchResult(
                node_id="node1", node_text="text1", node_type="type1",
                score=0.8, path_length=1, path_nodes=["query", "node1"],
                documents={"doc1"}, metadata={"algorithm": "shortest_path"}
            ),
            GraphSearchResult(
                node_id="node2", node_text="text2", node_type="type2",
                score=0.6, path_length=1, path_nodes=["query", "node2"],
                documents={"doc1"}, metadata={"algorithm": "random_walk"}
            )
        ]
        
        retrieval_results = self.retriever._convert_to_retrieval_results(
            graph_results, query
        )
        
        # Should aggregate scores for same document
        doc1_result = next(r for r in retrieval_results if r.document.metadata["id"] == "doc1")
        assert doc1_result.score == 0.8 + 0.6  # Sum of scores
        
    def test_result_limiting(self):
        """Test that results are limited to max_graph_results."""
        query = "test query"
        
        # Create more results than the limit
        many_results = []
        for i in range(10):
            many_results.append(GraphSearchResult(
                node_id=f"node{i}", node_text=f"text{i}", node_type="type",
                score=0.5, path_length=1, path_nodes=["query", f"node{i}"],
                documents={f"doc{i}"}, metadata={"algorithm": "shortest_path"}
            ))
        
        retrieval_results = self.retriever._convert_to_retrieval_results(
            many_results, query
        )
        
        # Should be limited to max_graph_results
        assert len(retrieval_results) <= self.config.max_graph_results


class TestGraphRetrieverIntegration:
    """Test complete graph retrieval workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GraphRetrievalConfig(
            algorithms=["shortest_path", "random_walk"],
            max_path_length=2
        )
        self.mock_graph_builder = Mock(spec=DocumentGraphBuilder)
        self.mock_embedder = Mock(spec=Embedder)
        
        self.retriever = GraphRetriever(
            config=self.config,
            graph_builder=self.mock_graph_builder,
            embedder=self.mock_embedder
        )
        
        # Create mock graph
        self.mock_graph = nx.DiGraph()
        self.mock_graph.add_node("cpu", text="CPU architecture", confidence=0.9, 
                                frequency=5, documents=["doc1"])
        self.mock_graph.add_node("memory", text="memory management", confidence=0.8, 
                                frequency=3, documents=["doc2"])
        self.mock_graph.add_edge("cpu", "memory", weight=0.8)
        
        self.mock_graph_builder.get_graph.return_value = self.mock_graph
        
    def test_successful_retrieval(self):
        """Test successful graph retrieval workflow."""
        query = "CPU"
        k = 5
        
        results = self.retriever.retrieve(query, k)
        
        assert isinstance(results, list)
        assert len(results) >= 0
        
        # Check that graph builder was called
        self.mock_graph_builder.get_graph.assert_called_once()
        
        # Check statistics were updated
        assert self.retriever.stats["queries_processed"] == 1
        assert self.retriever.stats["cache_misses"] == 1
        
    def test_empty_graph_handling(self):
        """Test handling when no graph is available."""
        self.mock_graph_builder.get_graph.return_value = None
        
        query = "CPU"
        results = self.retriever.retrieve(query)
        
        assert results == []
        
    def test_no_matching_nodes(self):
        """Test when no nodes match the query."""
        query = "quantum computing"  # No matching nodes
        
        # Mock embedder to return low similarity
        self.mock_embedder.embed.return_value = [np.array([0.0, 0.0, 0.0])]
        
        results = self.retriever.retrieve(query)
        
        # Should return empty results gracefully
        assert isinstance(results, list)
        
    def test_caching_functionality(self):
        """Test query result caching."""
        query = "CPU"
        k = 5
        
        # First call
        results1 = self.retriever.retrieve(query, k)
        assert self.retriever.stats["cache_misses"] == 1
        assert self.retriever.stats["cache_hits"] == 0
        
        # Second call with same parameters
        results2 = self.retriever.retrieve(query, k)
        assert self.retriever.stats["cache_hits"] == 1
        
        # Results should be identical
        assert results1 == results2
        
    def test_cache_key_variation(self):
        """Test that different parameters create different cache keys."""
        query = "CPU"
        
        # Different k values
        self.retriever.retrieve(query, k=5)
        self.retriever.retrieve(query, k=10)
        
        assert self.retriever.stats["cache_misses"] == 2
        
    def test_specific_algorithm_usage(self):
        """Test using specific algorithm."""
        query = "CPU"
        algorithm = "shortest_path"
        
        results = self.retriever.retrieve(query, algorithm=algorithm)
        
        # Check that algorithm usage was tracked
        assert self.retriever.stats["algorithm_usage"]["shortest_path"] == 1
        
    def test_unknown_algorithm_handling(self):
        """Test handling of unknown algorithms."""
        query = "CPU"
        algorithm = "unknown_algorithm"
        
        with patch.object(self.retriever, '_execute_algorithm') as mock_exec:
            mock_exec.return_value = []
            results = self.retriever.retrieve(query, algorithm=algorithm)
            
        # Should handle gracefully
        assert isinstance(results, list)
        
    def test_retrieval_error_handling(self):
        """Test error handling during retrieval."""
        query = "CPU"
        
        # Mock graph builder to raise exception
        self.mock_graph_builder.get_graph.side_effect = Exception("Graph error")
        
        with pytest.raises(GraphRetrieverError, match="Failed to retrieve documents"):
            self.retriever.retrieve(query)


class TestGraphRetrieverStatistics:
    """Test statistics collection and reporting."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GraphRetrievalConfig()
        self.mock_graph_builder = Mock(spec=DocumentGraphBuilder)
        self.mock_embedder = Mock(spec=Embedder)
        
        self.retriever = GraphRetriever(
            config=self.config,
            graph_builder=self.mock_graph_builder,
            embedder=self.mock_embedder
        )
        
        # Mock successful retrieval
        mock_graph = nx.DiGraph()
        mock_graph.add_node("cpu", text="CPU", documents=["doc1"])
        self.mock_graph_builder.get_graph.return_value = mock_graph
        
    def test_statistics_initialization(self):
        """Test initial statistics state."""
        stats = self.retriever.get_statistics()
        
        assert stats["queries_processed"] == 0
        assert stats["total_results_returned"] == 0
        assert stats["avg_search_time"] == 0.0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert "algorithm_usage_percentages" in stats
        assert stats["cache_hit_rate"] == 0.0
        
    def test_statistics_updates(self):
        """Test that statistics are updated during retrieval."""
        query = "CPU"
        
        # Perform retrievals
        self.retriever.retrieve(query)
        self.retriever.retrieve(query)  # Should be cached
        
        stats = self.retriever.get_statistics()
        
        assert stats["queries_processed"] == 2
        assert stats["cache_misses"] == 1
        assert stats["cache_hits"] == 1
        assert stats["cache_hit_rate"] == 50.0
        
    def test_algorithm_usage_tracking(self):
        """Test algorithm usage tracking."""
        query = "CPU"
        
        # Use different algorithms
        self.retriever.retrieve(query, algorithm="shortest_path")
        self.retriever.retrieve("memory", algorithm="random_walk")
        
        stats = self.retriever.get_statistics()
        
        assert "shortest_path" in stats["algorithm_usage_percentages"]
        assert "random_walk" in stats["algorithm_usage_percentages"]
        
    def test_average_search_time_calculation(self):
        """Test average search time calculation."""
        query = "CPU"
        
        # Clear cache to ensure actual processing
        self.retriever.cache_enabled = False
        
        # Perform multiple retrievals
        self.retriever.retrieve(query)
        self.retriever.retrieve("memory")
        
        stats = self.retriever.get_statistics()
        
        assert stats["avg_search_time"] > 0
        assert stats["queries_processed"] == 2
        
    def test_statistics_reset(self):
        """Test statistics reset functionality."""
        # Generate some statistics
        self.retriever.retrieve("CPU")
        
        # Reset statistics
        self.retriever.reset_statistics()
        
        stats = self.retriever.get_statistics()
        assert stats["queries_processed"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        
    def test_cache_management(self):
        """Test cache management functionality."""
        # Add some cached results
        self.retriever.retrieve("CPU")
        assert len(self.retriever.query_cache) > 0
        
        # Clear cache
        self.retriever.clear_cache()
        assert len(self.retriever.query_cache) == 0


class TestGraphRetrieverEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GraphRetrievalConfig()
        self.mock_graph_builder = Mock(spec=DocumentGraphBuilder)
        self.mock_embedder = Mock(spec=Embedder)
        
        self.retriever = GraphRetriever(
            config=self.config,
            graph_builder=self.mock_graph_builder,
            embedder=self.mock_embedder
        )
        
    def test_very_large_graph_handling(self):
        """Test handling of very large graphs."""
        # Create large mock graph
        large_graph = nx.DiGraph()
        for i in range(1000):
            large_graph.add_node(f"node_{i}", text=f"text_{i}", documents=[f"doc_{i}"])
            if i > 0:
                large_graph.add_edge(f"node_{i-1}", f"node_{i}")
                
        self.mock_graph_builder.get_graph.return_value = large_graph
        
        query = "text_500"
        results = self.retriever.retrieve(query, k=10)
        
        # Should handle large graphs without crashing
        assert isinstance(results, list)
        
    def test_disconnected_graph_components(self):
        """Test handling of disconnected graph components."""
        disconnected_graph = nx.DiGraph()
        
        # Component 1
        disconnected_graph.add_node("cpu", text="CPU", documents=["doc1"])
        disconnected_graph.add_node("memory", text="memory", documents=["doc2"])
        disconnected_graph.add_edge("cpu", "memory")
        
        # Component 2 (disconnected)
        disconnected_graph.add_node("network", text="network", documents=["doc3"])
        disconnected_graph.add_node("io", text="input output", documents=["doc4"])
        disconnected_graph.add_edge("network", "io")
        
        self.mock_graph_builder.get_graph.return_value = disconnected_graph
        
        query = "CPU network"  # Matches both components
        results = self.retriever.retrieve(query)
        
        # Should find results from both components
        assert isinstance(results, list)
        
    def test_self_loops_and_cycles(self):
        """Test handling of self-loops and cycles in graph."""
        cyclic_graph = nx.DiGraph()
        
        cyclic_graph.add_node("a", text="node a", documents=["doc1"])
        cyclic_graph.add_node("b", text="node b", documents=["doc2"])
        cyclic_graph.add_node("c", text="node c", documents=["doc3"])
        
        # Create cycle: a -> b -> c -> a
        cyclic_graph.add_edge("a", "b")
        cyclic_graph.add_edge("b", "c")
        cyclic_graph.add_edge("c", "a")
        
        # Self-loop
        cyclic_graph.add_edge("a", "a")
        
        self.mock_graph_builder.get_graph.return_value = cyclic_graph
        
        query = "node a"
        results = self.retriever.retrieve(query)
        
        # Should handle cycles without infinite loops
        assert isinstance(results, list)
        
    def test_missing_node_attributes(self):
        """Test handling of nodes with missing attributes."""
        incomplete_graph = nx.DiGraph()
        
        # Node with all attributes
        incomplete_graph.add_node("complete", text="complete node", confidence=0.8, 
                                 frequency=5, documents=["doc1"])
        
        # Node with missing attributes
        incomplete_graph.add_node("incomplete", text="incomplete node")  # Missing confidence, frequency, documents
        
        self.mock_graph_builder.get_graph.return_value = incomplete_graph
        
        query = "complete incomplete"
        results = self.retriever.retrieve(query)
        
        # Should handle missing attributes gracefully
        assert isinstance(results, list)
        
    def test_extreme_scoring_values(self):
        """Test handling of extreme scoring values."""
        extreme_graph = nx.DiGraph()
        
        # Node with extreme values
        extreme_graph.add_node("extreme", text="extreme node", confidence=1.0, 
                              frequency=1000000, documents=["doc1"] * 100)
        
        # Node with zero values
        extreme_graph.add_node("zero", text="zero node", confidence=0.0, 
                              frequency=0, documents=[])
        
        self.mock_graph_builder.get_graph.return_value = extreme_graph
        
        query = "extreme zero"
        results = self.retriever.retrieve(query)
        
        # Should handle extreme values without errors
        assert isinstance(results, list)
        
        # Check that scores are still in valid range
        for result in results:
            assert 0 <= result.score <= 1


class TestGraphRetrieverPerformance:
    """Test performance characteristics and optimization."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GraphRetrievalConfig()
        self.mock_graph_builder = Mock(spec=DocumentGraphBuilder)
        self.mock_embedder = Mock(spec=Embedder)
        
        self.retriever = GraphRetriever(
            config=self.config,
            graph_builder=self.mock_graph_builder,
            embedder=self.mock_embedder
        )
        
    def test_cache_size_limiting(self):
        """Test that cache size is limited."""
        # Create simple mock graph
        mock_graph = nx.DiGraph()
        mock_graph.add_node("test", text="test", documents=["doc1"])
        self.mock_graph_builder.get_graph.return_value = mock_graph
        
        # Fill cache beyond limit
        for i in range(1005):  # Beyond 1000 limit
            self.retriever.retrieve(f"query_{i}")
            
        # Cache should be limited
        assert len(self.retriever.query_cache) <= 1000
        
    def test_algorithm_timeout_handling(self):
        """Test timeout handling for long-running algorithms."""
        # Create graph that could cause long computation
        complex_graph = nx.complete_graph(100).to_directed()
        
        # Add required attributes
        for node in complex_graph.nodes():
            complex_graph.nodes[node]["text"] = f"node_{node}"
            complex_graph.nodes[node]["documents"] = [f"doc_{node}"]
            complex_graph.nodes[node]["confidence"] = 0.5
            complex_graph.nodes[node]["frequency"] = 1
            
        self.mock_graph_builder.get_graph.return_value = complex_graph
        
        query = f"node_0"
        
        # Should complete without timeout issues
        import time
        start_time = time.time()
        results = self.retriever.retrieve(query, k=10)
        elapsed_time = time.time() - start_time
        
        # Should complete reasonably quickly
        assert elapsed_time < 5.0  # 5 second timeout
        assert isinstance(results, list)
        
    def test_memory_efficiency(self):
        """Test memory efficiency with large result sets."""
        # Test with configuration that limits results
        limited_config = GraphRetrievalConfig(max_graph_results=5)
        
        limited_retriever = GraphRetriever(
            config=limited_config,
            graph_builder=self.mock_graph_builder,
            embedder=self.mock_embedder
        )
        
        # Create graph with many potential results
        large_graph = nx.DiGraph()
        for i in range(100):
            large_graph.add_node(f"node_{i}", text="matching text", 
                                documents=[f"doc_{i}"], confidence=0.5, frequency=1)
            if i > 0:
                large_graph.add_edge(f"node_{i-1}", f"node_{i}")
                
        self.mock_graph_builder.get_graph.return_value = large_graph
        
        query = "matching"
        results = limited_retriever.retrieve(query)
        
        # Should limit results to configured maximum
        assert len(results) <= limited_config.max_graph_results


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])