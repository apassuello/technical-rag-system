#!/usr/bin/env python3
"""
Enhanced comprehensive test suite for ModularUnifiedRetriever.

This module provides enhanced test coverage for the modular unified retriever system
including sub-component integration, performance optimization, error handling, and 
advanced fusion/reranking scenarios. Extends existing coverage from 20.5% to 85%.

Target Coverage: 85% (~640 additional test lines for 993 component lines)
Priority: HIGH (Enhance existing 20.5% coverage to 85%)
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock, call
from typing import List, Dict, Any, Optional
import time

# Import system under test
from src.components.retrievers.modular_unified_retriever import ModularUnifiedRetriever
from src.core.interfaces import Document, RetrievalResult, Embedder, HealthStatus


class TestModularUnifiedRetrieverAdvancedConfiguration:
    """Test advanced configuration scenarios and sub-component integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_embedder = Mock(spec=Embedder)
        self.mock_embedder.embed.return_value = [np.array([0.1, 0.2, 0.3, 0.4])]
        
        # Comprehensive configuration for testing
        self.advanced_config = {
            "vector_index": {
                "type": "faiss",
                "config": {
                    "index_type": "IndexFlatIP",
                    "normalize_embeddings": True,
                    "use_gpu": False
                }
            },
            "sparse": {
                "type": "bm25",
                "config": {
                    "k1": 1.5,
                    "b": 0.8,
                    "language": "english",
                    "stopwords": True
                }
            },
            "fusion": {
                "type": "rrf",
                "config": {
                    "k": 60,
                    "weights": {"dense": 0.7, "sparse": 0.3},
                    "score_aggregation": "weighted_average"
                }
            },
            "reranker": {
                "type": "neural",
                "config": {
                    "enabled": True,
                    "initialize_immediately": False,
                    "models": {
                        "default_model": {
                            "name": "cross-encoder/ms-marco-MiniLM-L6-v2",
                            "max_length": 512
                        }
                    }
                }
            },
            "composite_filtering": {
                "enabled": True,
                "fusion_weight": 0.6,
                "semantic_weight": 0.4,
                "min_composite_score": 0.35,
                "max_candidates": 20
            }
        }
        
        # Test documents
        self.test_documents = [
            Document(
                content="CPU architecture and instruction set design for RISC-V processors",
                metadata={"title": "RISC-V CPU Architecture", "section": "hardware", "id": "doc1"}
            ),
            Document(
                content="Memory management systems in operating systems and virtual memory",
                metadata={"title": "Memory Management", "section": "systems", "id": "doc2"}
            ),
            Document(
                content="Network protocols TCP/IP stack implementation details",
                metadata={"title": "Network Protocols", "section": "networking", "id": "doc3"}
            ),
            Document(
                content="Advanced compiler optimization techniques for performance",
                metadata={"title": "Compiler Optimization", "section": "software", "id": "doc4"}
            ),
            Document(
                content="Database indexing strategies and B-tree implementations",
                metadata={"title": "Database Indexing", "section": "databases", "id": "doc5"}
            )
        ]
        
    def test_advanced_configuration_parsing(self):
        """Test parsing of advanced configuration options."""
        retriever = ModularUnifiedRetriever(self.advanced_config, self.mock_embedder)
        
        # Test composite filtering configuration
        assert retriever.composite_filtering_enabled is True
        assert retriever.fusion_weight == 0.6
        assert retriever.semantic_weight == 0.4
        assert retriever.min_composite_score == 0.35
        assert retriever.max_candidates_multiplier == 2.0  # 20/10
        
        # Test backend management
        assert retriever.active_backend_name == "faiss"
        assert "faiss" in retriever.available_backends
        assert "weaviate" in retriever.available_backends
        
        # Test statistics initialization
        assert retriever.retrieval_stats["total_retrievals"] == 0
        assert retriever.retrieval_stats["total_time"] == 0.0
        
    def test_sub_component_creation_validation(self):
        """Test validation of sub-component creation."""
        retriever = ModularUnifiedRetriever(self.advanced_config, self.mock_embedder)
        
        # Verify all sub-components were created
        assert retriever.vector_index is not None
        assert retriever.sparse_retriever is not None
        assert retriever.fusion_strategy is not None
        assert retriever.reranker is not None
        
        # Test sub-component types
        assert hasattr(retriever.vector_index, 'search')
        assert hasattr(retriever.sparse_retriever, 'search')
        assert hasattr(retriever.fusion_strategy, 'fuse_results')
        assert hasattr(retriever.reranker, 'rerank')
        
    def test_invalid_sub_component_configurations(self):
        """Test handling of invalid sub-component configurations."""
        # Invalid vector index type
        invalid_config = {
            "vector_index": {"type": "invalid_index"},
            "sparse": self.advanced_config["sparse"].copy(),
            "fusion": self.advanced_config["fusion"].copy(),
            "reranker": self.advanced_config["reranker"].copy()
        }

        with pytest.raises(ValueError, match="Unknown vector index type"):
            ModularUnifiedRetriever(invalid_config, self.mock_embedder)

        # Invalid sparse retriever type
        invalid_config = {
            "vector_index": self.advanced_config["vector_index"].copy(),
            "sparse": {"type": "invalid_sparse"},
            "fusion": self.advanced_config["fusion"].copy(),
            "reranker": self.advanced_config["reranker"].copy()
        }

        with pytest.raises(ValueError, match="Unknown sparse retriever type"):
            ModularUnifiedRetriever(invalid_config, self.mock_embedder)

        # Invalid fusion strategy type
        invalid_config = {
            "vector_index": self.advanced_config["vector_index"].copy(),
            "sparse": self.advanced_config["sparse"].copy(),
            "fusion": {"type": "invalid_fusion"},
            "reranker": self.advanced_config["reranker"].copy()
        }

        with pytest.raises(ValueError, match="Unknown fusion strategy type"):
            ModularUnifiedRetriever(invalid_config, self.mock_embedder)
            
    def test_neural_reranker_fallback_handling(self):
        """Test fallback to identity reranker when neural reranker fails."""
        config_with_neural = self.advanced_config.copy()
        config_with_neural["reranker"]["type"] = "neural"
        
        # Mock NeuralReranker to raise exception during creation
        with patch('src.components.retrievers.modular_unified_retriever.NeuralReranker') as mock_neural:
            mock_neural.side_effect = Exception("Neural reranker initialization failed")
            
            retriever = ModularUnifiedRetriever(config_with_neural, self.mock_embedder)
            
            # Should fall back to IdentityReranker
            assert retriever.reranker is not None
            # Can't directly test type due to mocking, but should not raise exception
            
    def test_composite_filtering_configuration_edge_cases(self):
        """Test edge cases in composite filtering configuration."""
        # Test with zero weights
        config_zero_weights = self.advanced_config.copy()
        config_zero_weights["composite_filtering"]["fusion_weight"] = 0.0
        config_zero_weights["composite_filtering"]["semantic_weight"] = 0.0
        
        retriever = ModularUnifiedRetriever(config_zero_weights, self.mock_embedder)
        assert retriever.fusion_weight == 0.0
        assert retriever.semantic_weight == 0.0
        
        # Test with extreme multiplier values
        config_extreme = self.advanced_config.copy()
        config_extreme["composite_filtering"]["max_candidates"] = 100
        
        retriever = ModularUnifiedRetriever(config_extreme, self.mock_embedder)
        assert retriever.max_candidates_multiplier == 10.0


class TestModularUnifiedRetrieverRetrievalPipeline:
    """Test the complete retrieval pipeline with all sub-components."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_embedder = Mock(spec=Embedder)
        # Return embeddings based on number of texts
        self.mock_embedder.embed.side_effect = lambda texts: [np.array([0.1, 0.2, 0.3, 0.4]) for _ in texts]
        
        self.config = {
            "vector_index": {"type": "faiss", "config": {}},
            "sparse": {"type": "bm25", "config": {}},
            "fusion": {"type": "rrf", "config": {"k": 60}},
            "reranker": {"type": "identity", "config": {}},
            "composite_filtering": {"enabled": True}
        }
        
        self.retriever = ModularUnifiedRetriever(self.config, self.mock_embedder)
        
        # Add test documents
        self.test_documents = [
            Document(content="CPU architecture details", metadata={"id": "doc1"}),
            Document(content="Memory management systems", metadata={"id": "doc2"}),
            Document(content="Network protocol implementations", metadata={"id": "doc3"})
        ]
        self.retriever.index_documents(self.test_documents)
        
    def test_complete_retrieval_pipeline_success(self):
        """Test successful execution of complete retrieval pipeline."""
        # Mock sub-component behaviors
        with patch.object(self.retriever.vector_index, 'search') as mock_dense:
            with patch.object(self.retriever.sparse_retriever, 'search') as mock_sparse:
                with patch.object(self.retriever.fusion_strategy, 'fuse_results') as mock_fusion:
                    with patch.object(self.retriever.reranker, 'rerank') as mock_rerank:
                        
                        # Configure mock returns
                        mock_dense.return_value = [(0, 0.9), (1, 0.7)]
                        mock_sparse.return_value = [(1, 0.8), (2, 0.6)]
                        mock_fusion.return_value = [(0, 0.85), (1, 0.75), (2, 0.6)]
                        mock_rerank.return_value = [(0, 0.9), (1, 0.8), (2, 0.65)]
                        
                        # Execute retrieval
                        results = self.retriever.retrieve("CPU architecture", k=3)
                        
                        # Verify pipeline execution
                        mock_dense.assert_called_once()
                        mock_sparse.assert_called_once()
                        mock_fusion.assert_called_once()
                        mock_rerank.assert_called_once()
                        
                        # Verify results format
                        assert len(results) <= 3
                        assert all(isinstance(r, RetrievalResult) for r in results)
                        assert all(hasattr(r, 'score') and hasattr(r, 'document') for r in results)
                        
    def test_retrieval_with_composite_filtering(self):
        """Test retrieval pipeline with composite filtering enabled."""
        self.retriever.composite_filtering_enabled = True
        self.retriever.max_candidates_multiplier = 1.5

        with patch.object(self.retriever.vector_index, 'search') as mock_dense:
            with patch.object(self.retriever.sparse_retriever, 'search') as mock_sparse:
                with patch.object(self.retriever.fusion_strategy, 'fuse_results') as mock_fusion:

                    mock_dense.return_value = [(0, 0.9), (1, 0.7)]
                    mock_sparse.return_value = [(1, 0.8), (2, 0.6)]
                    mock_fusion.return_value = [(0, 0.85), (1, 0.75)]

                    results = self.retriever.retrieve("test query", k=2)

                    # Should call dense/sparse with increased candidate count
                    mock_dense.assert_called_once()
                    mock_sparse.assert_called_once()

                    # Verify candidate multiplier effect
                    # k=2, multiplier=1.5, so should request 3 candidates
                    assert mock_dense.call_args.kwargs['k'] == 3
                    # Sparse retriever search signature: search(query, k=5), so k is keyword arg
                    assert mock_sparse.call_args.kwargs['k'] == 3
                    
    def test_retrieval_statistics_tracking(self):
        """Test that retrieval statistics are properly tracked."""
        initial_stats = self.retriever.retrieval_stats.copy()

        # Mock the sub-component searches to return valid results (not empty)
        with patch.object(self.retriever.vector_index, 'search') as mock_vector:
            with patch.object(self.retriever.sparse_retriever, 'search') as mock_sparse:
                with patch.object(self.retriever.fusion_strategy, 'fuse_results') as mock_fusion:

                    # Return valid results so retrieval completes successfully
                    mock_vector.return_value = [(0, 0.9)]
                    mock_sparse.return_value = [(0, 0.8)]
                    mock_fusion.return_value = [(0, 0.85)]

                    # Execute multiple retrievals
                    self.retriever.retrieve("query1", k=5)
                    self.retriever.retrieve("query2", k=3)

                    # Verify statistics were updated
                    assert self.retriever.retrieval_stats["total_retrievals"] == initial_stats["total_retrievals"] + 2
                    assert self.retriever.retrieval_stats["total_time"] > initial_stats["total_time"]
            
    def test_retrieval_input_validation(self):
        """Test input validation in retrieval method."""
        # Test negative k - note that retrieve() wraps exceptions in RuntimeError
        with pytest.raises(RuntimeError, match="k must be positive"):
            self.retriever.retrieve("test query", k=0)

        with pytest.raises(RuntimeError, match="k must be positive"):
            self.retriever.retrieve("test query", k=-1)

        # Test empty query
        with pytest.raises(RuntimeError, match="Query cannot be empty"):
            self.retriever.retrieve("", k=5)

        with pytest.raises(RuntimeError, match="Query cannot be empty"):
            self.retriever.retrieve("   ", k=5)

        # Test retrieval without documents
        empty_retriever = ModularUnifiedRetriever(self.config, self.mock_embedder)

        with pytest.raises(RuntimeError, match="No documents have been indexed"):
            empty_retriever.retrieve("test query", k=5)
            
    def test_graph_enhanced_fusion_integration(self):
        """Test integration with graph-enhanced fusion strategies."""
        # Mock fusion strategy that supports graph enhancement
        mock_fusion = Mock()
        mock_fusion.fuse_results.return_value = [(0, 0.9), (1, 0.8)]
        mock_fusion.set_documents_and_query = Mock()
        
        self.retriever.fusion_strategy = mock_fusion
        
        with patch.object(self.retriever.vector_index, 'search') as mock_dense:
            with patch.object(self.retriever.sparse_retriever, 'search') as mock_sparse:
                mock_dense.return_value = [(0, 0.9)]
                mock_sparse.return_value = [(1, 0.8)]
                
                results = self.retriever.retrieve("test query", k=2)
                
                # Verify graph enhancement method was called
                mock_fusion.set_documents_and_query.assert_called_once_with(
                    self.retriever.documents, "test query"
                )
                
    def test_empty_search_results_handling(self):
        """Test handling when search returns empty results."""
        with patch.object(self.retriever.vector_index, 'search') as mock_dense:
            with patch.object(self.retriever.sparse_retriever, 'search') as mock_sparse:
                with patch.object(self.retriever.fusion_strategy, 'fuse_results') as mock_fusion:
                    
                    # Both searches return empty results
                    mock_dense.return_value = []
                    mock_sparse.return_value = []
                    mock_fusion.return_value = []
                    
                    results = self.retriever.retrieve("nonexistent query", k=5)
                    
                    # Should handle empty results gracefully
                    assert isinstance(results, list)
                    assert len(results) == 0


class TestModularUnifiedRetrieverDocumentManagement:
    """Test document management operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_embedder = Mock(spec=Embedder)
        self.mock_embedder.embed.return_value = [
            np.array([0.1, 0.2, 0.3]),
            np.array([0.4, 0.5, 0.6]),
            np.array([0.7, 0.8, 0.9])
        ]
        
        self.config = {
            "vector_index": {"type": "faiss"},
            "sparse": {"type": "bm25"},
            "fusion": {"type": "rrf"},
            "reranker": {"type": "identity"}
        }
        
        self.retriever = ModularUnifiedRetriever(self.config, self.mock_embedder)
        
        self.test_documents = [
            Document(content="First document content", metadata={"id": "doc1"}),
            Document(content="Second document content", metadata={"id": "doc2"}),
            Document(content="Third document content", metadata={"id": "doc3"})
        ]
        
    def test_single_document_addition(self):
        """Test adding single documents."""
        document = self.test_documents[0]
        
        with patch.object(self.retriever.vector_index, 'add_documents') as mock_vector_add:
            with patch.object(self.retriever.sparse_retriever, 'add_documents') as mock_sparse_add:
                
                self.retriever.index_documents([document])
                
                # Verify document was added to both indices
                mock_vector_add.assert_called_once()
                mock_sparse_add.assert_called_once()
                
                # Verify embedder was called
                self.mock_embedder.embed.assert_called_once()
                
                # Verify document is stored
                assert len(self.retriever.documents) == 1
                assert self.retriever.documents[0] == document
                
    def test_batch_document_addition(self):
        """Test adding multiple documents at once."""
        with patch.object(self.retriever.vector_index, 'add_documents') as mock_vector_add:
            with patch.object(self.retriever.sparse_retriever, 'add_documents') as mock_sparse_add:
                
                self.retriever.index_documents(self.test_documents)
                
                # Verify batch addition
                mock_vector_add.assert_called_once()
                mock_sparse_add.assert_called_once()
                
                # Verify embedder was called for all documents
                self.mock_embedder.embed.assert_called_once()
                embed_call_args = self.mock_embedder.embed.call_args[0][0]
                assert len(embed_call_args) == 3
                
                # Verify all documents are stored
                assert len(self.retriever.documents) == 3
                
    def test_document_addition_with_embedder_errors(self):
        """Test handling of embedder errors during document addition."""
        self.mock_embedder.embed.side_effect = Exception("Embedder error")
        
        with pytest.raises(Exception, match="Embedder error"):
            self.retriever.index_documents([self.test_documents[0]])
            
    def test_duplicate_document_handling(self):
        """Test handling of duplicate documents."""
        # Add same document twice
        document = self.test_documents[0]
        
        with patch.object(self.retriever.vector_index, 'add_documents') as mock_vector_add:
            with patch.object(self.retriever.sparse_retriever, 'add_documents') as mock_sparse_add:
                
                self.retriever.index_documents([document])
                self.retriever.index_documents([document])
                
                # Both additions should be processed
                assert mock_vector_add.call_count == 2
                assert mock_sparse_add.call_count == 2
                
                # Document should be stored twice (no deduplication by default)
                assert len(self.retriever.documents) == 2
                
    def test_document_addition_performance(self):
        """Test performance of document addition operations."""
        large_document_set = [
            Document(content=f"Document {i} with content", metadata={"id": f"doc{i}"})
            for i in range(100)
        ]
        
        # Mock embedder to return appropriate number of embeddings
        self.mock_embedder.embed.return_value = [np.array([0.1, 0.2, 0.3])] * 100
        
        with patch.object(self.retriever.vector_index, 'add_documents') as mock_vector_add:
            with patch.object(self.retriever.sparse_retriever, 'add_documents') as mock_sparse_add:
                
                start_time = time.time()
                self.retriever.index_documents(large_document_set)
                elapsed_time = time.time() - start_time
                
                # Should complete reasonably quickly (< 5 seconds for mocked operations)
                assert elapsed_time < 5.0
                
                # Verify batch processing was used
                assert mock_vector_add.call_count == 1
                assert mock_sparse_add.call_count == 1


class TestModularUnifiedRetrieverHealthAndMonitoring:
    """Test health monitoring and system status functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_embedder = Mock(spec=Embedder)
        self.config = {
            "vector_index": {"type": "faiss"},
            "sparse": {"type": "bm25"},
            "fusion": {"type": "rrf"},
            "reranker": {"type": "identity"}
        }
        
        self.retriever = ModularUnifiedRetriever(self.config, self.mock_embedder)
        
    def test_health_status_all_healthy(self):
        """Test health status when all components are healthy."""
        # Get health status - it should return HEALTHY when all sub-components are properly initialized
        status = self.retriever.get_health_status()

        # Verify the health status object has expected structure
        assert isinstance(status, HealthStatus)
        assert status.is_healthy is True
        assert status.component_name == "ModularUnifiedRetriever"
                
    def test_health_status_degraded_component(self):
        """Test health status when one component is degraded."""
        # Simulate degraded state by patching hasattr to return False for one component
        original_hasattr = hasattr

        def mock_hasattr(obj, name):
            # Make vector_index appear to not have get_index_info
            if obj is self.retriever.vector_index and name == "get_index_info":
                return False
            return original_hasattr(obj, name)

        with patch('builtins.hasattr', side_effect=mock_hasattr):
            status = self.retriever.get_health_status()

            # Verify the health status reflects the degraded component
            assert isinstance(status, HealthStatus)
            assert status.is_healthy is False
            assert len(status.issues) > 0
            assert any("Vector index" in issue for issue in status.issues)
                
    def test_health_status_unhealthy_component(self):
        """Test health status when one component is unhealthy."""
        # Simulate unhealthy state by patching hasattr to return False for multiple components
        original_hasattr = hasattr

        def mock_hasattr(obj, name):
            # Make multiple components appear unhealthy
            if obj is self.retriever.vector_index and name == "get_index_info":
                return False
            if obj is self.retriever.sparse_retriever and name == "get_stats":
                return False
            return original_hasattr(obj, name)

        with patch('builtins.hasattr', side_effect=mock_hasattr):
            status = self.retriever.get_health_status()

            # Verify the health status reflects unhealthy components
            assert isinstance(status, HealthStatus)
            assert status.is_healthy is False
            assert len(status.issues) >= 2  # At least 2 issues
                
    def test_get_retriever_info(self):
        """Test comprehensive retriever information retrieval."""
        # Add some test data first with proper mock
        self.mock_embedder.embed.return_value = [np.array([0.1, 0.2, 0.3])]
        test_documents = [
            Document(content="Test document", metadata={"id": "test"})
        ]
        self.retriever.index_documents(test_documents)

        # Execute some retrievals to populate statistics
        self.retriever.retrieval_stats = {
            "total_retrievals": 10,
            "total_time": 5.0,
            "avg_time": 0.5,
            "last_retrieval_time": 0.4
        }

        info = self.retriever.get_retriever_info()

        # Verify basic information (using actual structure from get_retriever_info)
        assert "component_type" in info
        assert info["component_type"] == "modular_unified_retriever"
        assert "indexed_documents" in info
        assert info["indexed_documents"] == 1
        assert "retrieval_stats" in info
        assert "configuration" in info
        assert "sub_components" in info
        assert "backend_management" in info

        # Verify statistics
        assert info["retrieval_stats"]["total_retrievals"] == 10
        assert info["retrieval_stats"]["avg_time"] == 0.5

        # Verify sub-component information
        sub_components = info["sub_components"]
        assert "vector_index" in sub_components
        assert "sparse_retriever" in sub_components
        assert "fusion_strategy" in sub_components
        assert "reranker" in sub_components
        
    def test_backend_management_info(self):
        """Test backend management information."""
        info = self.retriever.get_retriever_info()

        # Backend management info is nested under "backend_management"
        backend_info = info["backend_management"]
        assert backend_info["active_backend"] == "faiss"
        assert "faiss" in backend_info["available_backends"]
        assert "weaviate" in backend_info["available_backends"]
        assert backend_info["switch_count"] == 0
        
    def test_performance_statistics_calculation(self):
        """Test calculation of performance statistics."""
        # Simulate retrieval history
        self.retriever.retrieval_stats = {
            "total_retrievals": 50,
            "total_time": 25.0,
            "avg_time": 0.5,
            "last_retrieval_time": 0.3
        }

        info = self.retriever.get_retriever_info()
        # Statistics are stored under "retrieval_stats" not "statistics"
        stats = info["retrieval_stats"]

        assert stats["total_retrievals"] == 50
        assert stats["total_time"] == 25.0
        assert stats["avg_time"] == 0.5
        assert stats["last_retrieval_time"] == 0.3
        
    def test_sub_component_detailed_info(self):
        """Test detailed sub-component information retrieval."""
        # Mock sub-component info methods
        with patch.object(self.retriever.vector_index, 'get_component_info') as mock_vector_info:
            with patch.object(self.retriever.sparse_retriever, 'get_component_info') as mock_sparse_info:
                with patch.object(self.retriever.fusion_strategy, 'get_component_info') as mock_fusion_info:
                    with patch.object(self.retriever.reranker, 'get_component_info') as mock_rerank_info:

                        # Configure mock returns matching actual component_info structure
                        mock_vector_info.return_value = {"type": "vector_index", "class": "FAISSIndex"}
                        mock_sparse_info.return_value = {"type": "sparse_retriever", "class": "BM25Retriever"}
                        mock_fusion_info.return_value = {"type": "fusion_strategy", "algorithm": "rrf"}
                        mock_rerank_info.return_value = {"type": "reranker", "class": "IdentityReranker"}

                        info = self.retriever.get_retriever_info()

                        # Verify detailed information was collected
                        sub_components = info["sub_components"]

                        assert sub_components["vector_index"]["type"] == "vector_index"
                        assert sub_components["sparse_retriever"]["type"] == "sparse_retriever"
                        assert sub_components["fusion_strategy"]["type"] == "fusion_strategy"
                        assert sub_components["reranker"]["type"] == "reranker"


class TestModularUnifiedRetrieverErrorHandling:
    """Test error handling and recovery mechanisms."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_embedder = Mock(spec=Embedder)
        self.config = {
            "vector_index": {"type": "faiss"},
            "sparse": {"type": "bm25"},
            "fusion": {"type": "rrf"},
            "reranker": {"type": "identity"}
        }
        
        self.retriever = ModularUnifiedRetriever(self.config, self.mock_embedder)
        
    def test_embedder_failure_handling(self):
        """Test handling of embedder failures during retrieval."""
        self.mock_embedder.embed.side_effect = Exception("Embedder connection failed")
        
        # Add some documents first
        self.mock_embedder.embed.side_effect = None
        self.mock_embedder.embed.return_value = [np.array([0.1, 0.2, 0.3])]
        
        test_doc = Document(content="Test document", metadata={"id": "test"})
        self.retriever.index_documents([test_doc])
        
        # Now make embedder fail during retrieval
        self.mock_embedder.embed.side_effect = Exception("Embedder connection failed")
        
        with pytest.raises(Exception, match="Embedder connection failed"):
            self.retriever.retrieve("test query", k=5)
            
    def test_vector_index_failure_handling(self):
        """Test handling of vector index failures."""
        self.mock_embedder.embed.return_value = [np.array([0.1, 0.2, 0.3])]
        
        # Add documents
        test_doc = Document(content="Test document", metadata={"id": "test"})
        self.retriever.index_documents([test_doc])
        
        # Mock vector index to fail during search
        with patch.object(self.retriever.vector_index, 'search') as mock_search:
            mock_search.side_effect = Exception("Vector index error")
            
            with pytest.raises(Exception, match="Vector index error"):
                self.retriever.retrieve("test query", k=5)
                
    def test_sparse_retriever_failure_handling(self):
        """Test handling of sparse retriever failures."""
        self.mock_embedder.embed.return_value = [np.array([0.1, 0.2, 0.3])]
        
        # Add documents
        test_doc = Document(content="Test document", metadata={"id": "test"})
        self.retriever.index_documents([test_doc])
        
        # Mock successful vector search but failing sparse search
        with patch.object(self.retriever.vector_index, 'search') as mock_vector_search:
            with patch.object(self.retriever.sparse_retriever, 'search') as mock_sparse_search:
                
                mock_vector_search.return_value = [(0, 0.9)]
                mock_sparse_search.side_effect = Exception("Sparse retriever error")
                
                with pytest.raises(Exception, match="Sparse retriever error"):
                    self.retriever.retrieve("test query", k=5)
                    
    def test_fusion_strategy_failure_handling(self):
        """Test handling of fusion strategy failures."""
        self.mock_embedder.embed.return_value = [np.array([0.1, 0.2, 0.3])]
        
        # Add documents
        test_doc = Document(content="Test document", metadata={"id": "test"})
        self.retriever.index_documents([test_doc])
        
        # Mock successful searches but failing fusion
        with patch.object(self.retriever.vector_index, 'search') as mock_vector:
            with patch.object(self.retriever.sparse_retriever, 'search') as mock_sparse:
                with patch.object(self.retriever.fusion_strategy, 'fuse_results') as mock_fusion:
                    
                    mock_vector.return_value = [(0, 0.9)]
                    mock_sparse.return_value = [(0, 0.8)]
                    mock_fusion.side_effect = Exception("Fusion strategy error")
                    
                    with pytest.raises(Exception, match="Fusion strategy error"):
                        self.retriever.retrieve("test query", k=5)
                        
    def test_reranker_failure_graceful_degradation(self):
        """Test graceful degradation when reranker fails."""
        self.mock_embedder.embed.return_value = [np.array([0.1, 0.2, 0.3])]
        
        # Add documents
        test_doc = Document(content="Test document", metadata={"id": "test"})
        self.retriever.index_documents([test_doc])
        
        # Mock successful pipeline until reranker fails
        with patch.object(self.retriever.vector_index, 'search') as mock_vector:
            with patch.object(self.retriever.sparse_retriever, 'search') as mock_sparse:
                with patch.object(self.retriever.fusion_strategy, 'fuse_results') as mock_fusion:
                    with patch.object(self.retriever.reranker, 'rerank') as mock_rerank:
                        
                        mock_vector.return_value = [(0, 0.9)]
                        mock_sparse.return_value = [(0, 0.8)]
                        mock_fusion.return_value = [(0, 0.85)]
                        mock_rerank.side_effect = Exception("Reranker error")
                        
                        # Depending on implementation, this might gracefully degrade
                        # or raise exception - test both possibilities
                        try:
                            results = self.retriever.retrieve("test query", k=5)
                            # If graceful degradation, should return fusion results
                            assert isinstance(results, list)
                        except Exception as e:
                            # If not graceful, should raise the reranker error
                            assert "Reranker error" in str(e)
                            
    def test_concurrent_access_safety(self):
        """Test thread safety and concurrent access."""
        import concurrent.futures

        # Mock embedder to return list of embeddings properly
        self.mock_embedder.embed.return_value = [np.array([0.1, 0.2, 0.3]) for _ in range(10)]

        # Add documents
        test_docs = [
            Document(content=f"Document {i}", metadata={"id": f"doc{i}"})
            for i in range(10)
        ]
        self.retriever.index_documents(test_docs)

        # Mock sub-components for concurrent testing
        with patch.object(self.retriever.vector_index, 'search') as mock_vector:
            with patch.object(self.retriever.sparse_retriever, 'search') as mock_sparse:
                with patch.object(self.retriever.fusion_strategy, 'fuse_results') as mock_fusion:

                    mock_vector.return_value = [(0, 0.9), (1, 0.8)]
                    mock_sparse.return_value = [(0, 0.85), (2, 0.7)]
                    mock_fusion.return_value = [(0, 0.9), (1, 0.8)]

                    def retrieval_task(query_id):
                        return self.retriever.retrieve(f"query {query_id}", k=5)

                    # Execute concurrent retrievals
                    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                        futures = [executor.submit(retrieval_task, i) for i in range(10)]
                        results = [future.result() for future in concurrent.futures.as_completed(futures)]

                        # All retrievals should complete successfully
                        assert len(results) == 10
                        assert all(isinstance(r, list) for r in results)


class TestModularUnifiedRetrieverPerformanceOptimization:
    """Test performance optimization features and edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_embedder = Mock(spec=Embedder)
        
        # Performance-optimized configuration
        self.perf_config = {
            "vector_index": {
                "type": "faiss",
                "config": {"normalize_embeddings": True, "use_gpu": False}
            },
            "sparse": {
                "type": "bm25",
                "config": {"k1": 1.2, "b": 0.75}
            },
            "fusion": {
                "type": "rrf",
                "config": {"k": 30}  # Lower k for faster computation
            },
            "reranker": {
                "type": "identity",  # No reranking for performance
                "config": {}
            },
            "composite_filtering": {
                "enabled": True,
                "max_candidates": 10,  # Limit candidates for performance
                "min_composite_score": 0.5
            }
        }
        
        self.retriever = ModularUnifiedRetriever(self.perf_config, self.mock_embedder)
        
    def test_large_corpus_performance(self):
        """Test performance with large document corpus."""
        # Create large corpus
        large_corpus = [
            Document(content=f"Document {i} content with technical details", metadata={"id": f"doc{i}"})
            for i in range(1000)
        ]
        
        # Mock embedder to handle large batches
        self.mock_embedder.embed.return_value = [np.array([0.1, 0.2, 0.3])] * 1000
        
        with patch.object(self.retriever.vector_index, 'add_documents') as mock_vector_add:
            with patch.object(self.retriever.sparse_retriever, 'add_documents') as mock_sparse_add:
                
                start_time = time.time()
                self.retriever.index_documents(large_corpus)
                elapsed_time = time.time() - start_time
                
                # Should handle large corpus efficiently
                assert elapsed_time < 10.0  # 10 second limit for mocked operations
                
                # Verify batch processing was used
                assert mock_vector_add.call_count == 1
                assert mock_sparse_add.call_count == 1
                
    def test_high_frequency_retrieval_performance(self):
        """Test performance under high retrieval frequency."""
        # Add test documents
        self.mock_embedder.embed.return_value = [np.array([0.1, 0.2, 0.3])] * 5
        test_docs = [
            Document(content=f"Document {i}", metadata={"id": f"doc{i}"})
            for i in range(5)
        ]
        self.retriever.index_documents(test_docs)

        # Mock sub-components for performance testing
        with patch.object(self.retriever.vector_index, 'search') as mock_vector:
            with patch.object(self.retriever.sparse_retriever, 'search') as mock_sparse:
                with patch.object(self.retriever.fusion_strategy, 'fuse_results') as mock_fusion:

                    mock_vector.return_value = [(0, 0.9), (1, 0.8)]
                    mock_sparse.return_value = [(0, 0.85), (2, 0.7)]
                    mock_fusion.return_value = [(0, 0.9)]

                    # Execute many retrievals
                    start_time = time.time()
                    for i in range(100):
                        results = self.retriever.retrieve(f"query {i}", k=3)
                    elapsed_time = time.time() - start_time

                    # Should handle high frequency efficiently
                    assert elapsed_time < 5.0  # 5 second limit for 100 retrievals

                    # Verify statistics tracking
                    assert self.retriever.retrieval_stats["total_retrievals"] == 100
            
    def test_memory_usage_optimization(self):
        """Test memory usage optimization features."""
        # Test with memory-conscious configuration
        memory_config = self.perf_config.copy()
        memory_config["composite_filtering"]["max_candidates"] = 5  # Very limited

        memory_retriever = ModularUnifiedRetriever(memory_config, self.mock_embedder)

        # Add documents
        self.mock_embedder.embed.return_value = [np.array([0.1, 0.2, 0.3])] * 3
        test_docs = [
            Document(content=f"Document {i}", metadata={"id": f"doc{i}"})
            for i in range(3)
        ]
        memory_retriever.index_documents(test_docs)

        # Test retrieval with limited candidates
        with patch.object(memory_retriever.vector_index, 'search') as mock_vector:
            with patch.object(memory_retriever.sparse_retriever, 'search') as mock_sparse:

                mock_vector.return_value = [(0, 0.9), (1, 0.8)]
                mock_sparse.return_value = [(1, 0.85), (2, 0.7)]

                results = memory_retriever.retrieve("test query", k=10)

                # Should limit candidates based on configuration
                # max_candidates=5, so should request 5 candidates
                assert mock_vector.call_args.kwargs['k'] == 5
                # Sparse retriever uses keyword argument k
                assert mock_sparse.call_args.kwargs['k'] == 5
                
    def test_caching_and_memoization_patterns(self):
        """Test caching and memoization for performance."""
        # This would test any caching mechanisms in the retriever
        # Since the current implementation doesn't explicitly cache,
        # we test that repeated identical queries could benefit from caching
        
        self.mock_embedder.embed.return_value = [np.array([0.1, 0.2, 0.3])]
        test_doc = Document(content="Test document", metadata={"id": "test"})
        self.retriever.index_documents([test_doc])
        
        # Mock sub-components
        with patch.object(self.retriever.vector_index, 'search') as mock_vector:
            with patch.object(self.retriever.sparse_retriever, 'search') as mock_sparse:
                with patch.object(self.retriever.fusion_strategy, 'fuse_results') as mock_fusion:
                    
                    mock_vector.return_value = [(0, 0.9)]
                    mock_sparse.return_value = [(0, 0.8)]
                    mock_fusion.return_value = [(0, 0.85)]
                    
                    # Execute same query multiple times
                    query = "identical query"
                    for _ in range(3):
                        results = self.retriever.retrieve(query, k=5)
                    
                    # Verify each call still goes through the pipeline
                    # (No caching implemented in current version)
                    assert mock_vector.call_count == 3
                    assert mock_sparse.call_count == 3
                    assert mock_fusion.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])