"""
Tests for the UnifiedRetriever component (Phase 2 Architecture).

This test suite validates the unified retriever that consolidates
FAISSVectorStore and HybridRetriever functionality into a single component.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.components.retrievers.unified_retriever import UnifiedRetriever
from src.core.interfaces import Document, RetrievalResult, Embedder


class MockEmbedder(Embedder):
    """Mock embedder for testing."""
    
    def embed(self, texts):
        # Return random embeddings for testing
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]
    
    def embedding_dim(self):
        return 4


class TestUnifiedRetriever:
    """Test suite for UnifiedRetriever component."""
    
    @pytest.fixture
    def mock_embedder(self):
        """Create a mock embedder."""
        return MockEmbedder()
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents with embeddings."""
        docs = [
            Document(
                content="RISC-V is an open standard instruction set architecture.",
                metadata={"source": "riscv_intro.pdf", "page": 1},
                embedding=[0.1, 0.2, 0.3, 0.4]
            ),
            Document(
                content="Vector extensions provide SIMD capabilities.",
                metadata={"source": "vector_spec.pdf", "page": 5},
                embedding=[0.2, 0.3, 0.4, 0.5]
            ),
            Document(
                content="Memory management in RISC-V systems.",
                metadata={"source": "memory_guide.pdf", "page": 12},
                embedding=[0.3, 0.4, 0.5, 0.6]
            )
        ]
        return docs
    
    @pytest.fixture
    def unified_retriever(self, mock_embedder):
        """Create a UnifiedRetriever instance."""
        return UnifiedRetriever(
            embedder=mock_embedder,
            dense_weight=0.7,
            embedding_dim=4,
            index_type="IndexFlatIP"
        )
    
    def test_initialization(self, mock_embedder):
        """Test unified retriever initialization."""
        retriever = UnifiedRetriever(
            embedder=mock_embedder,
            dense_weight=0.8,
            embedding_dim=4
        )
        
        assert retriever.embedder == mock_embedder
        assert retriever.dense_weight == 0.8
        assert abs(retriever.sparse_weight - 0.2) < 1e-10
        assert retriever.embedding_dim == 4
        assert retriever.index_type == "IndexFlatIP"
        assert retriever.normalize_embeddings == True
        assert retriever.index is None
        assert len(retriever.documents) == 0
    
    def test_index_documents_success(self, unified_retriever, sample_documents):
        """Test successful document indexing."""
        unified_retriever.index_documents(sample_documents)
        
        assert len(unified_retriever.documents) == 3
        assert unified_retriever.index is not None
        assert unified_retriever.index.ntotal == 3
        assert len(unified_retriever._chunks_cache) == 3
    
    def test_index_documents_empty_list(self, unified_retriever):
        """Test indexing with empty document list."""
        with pytest.raises(ValueError, match="Cannot index empty document list"):
            unified_retriever.index_documents([])
    
    def test_index_documents_missing_embeddings(self, unified_retriever):
        """Test indexing documents without embeddings."""
        docs = [
            Document(
                content="Test document without embedding",
                metadata={"source": "test.pdf"}
                # No embedding
            )
        ]
        
        with pytest.raises(ValueError, match="Document 0 is missing embedding"):
            unified_retriever.index_documents(docs)
    
    def test_index_documents_wrong_embedding_dimension(self, unified_retriever):
        """Test indexing documents with wrong embedding dimension."""
        docs = [
            Document(
                content="Test document with wrong embedding",
                metadata={"source": "test.pdf"},
                embedding=[0.1, 0.2]  # Wrong dimension (2 instead of 4)
            )
        ]
        
        with pytest.raises(ValueError, match="Document 0 embedding dimension 2"):
            unified_retriever.index_documents(docs)
    
    @patch('src.components.retrievers.unified_retriever.OriginalHybridRetriever')
    def test_retrieve_success(self, mock_hybrid_class, unified_retriever, sample_documents):
        """Test successful document retrieval."""
        # Setup mock hybrid retriever
        mock_hybrid = Mock()
        mock_hybrid.search.return_value = [
            (0, 0.9, {"text": "RISC-V is an open standard", "chunk_id": 0}),
            (1, 0.7, {"text": "Vector extensions provide", "chunk_id": 1})
        ]
        mock_hybrid_class.return_value = mock_hybrid
        
        # Create fresh retriever to use the mock
        retriever = UnifiedRetriever(
            embedder=MockEmbedder(),
            embedding_dim=4
        )
        retriever.index_documents(sample_documents)
        
        results = retriever.retrieve("What is RISC-V?", k=2)
        
        assert len(results) == 2
        assert all(isinstance(r, RetrievalResult) for r in results)
        assert results[0].score == 0.9
        assert results[1].score == 0.7
        assert results[0].retrieval_method == "unified_hybrid_rrf"
    
    def test_retrieve_empty_query(self, unified_retriever, sample_documents):
        """Test retrieval with empty query."""
        unified_retriever.index_documents(sample_documents)
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            unified_retriever.retrieve("", k=5)
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            unified_retriever.retrieve("   ", k=5)
    
    def test_retrieve_invalid_k(self, unified_retriever, sample_documents):
        """Test retrieval with invalid k parameter."""
        unified_retriever.index_documents(sample_documents)
        
        with pytest.raises(ValueError, match="k must be positive"):
            unified_retriever.retrieve("test query", k=0)
        
        with pytest.raises(ValueError, match="k must be positive"):
            unified_retriever.retrieve("test query", k=-1)
    
    def test_retrieve_no_documents_indexed(self, unified_retriever):
        """Test retrieval when no documents are indexed."""
        with pytest.raises(RuntimeError, match="No documents have been indexed"):
            unified_retriever.retrieve("test query", k=5)
    
    def test_get_retrieval_stats(self, unified_retriever, sample_documents):
        """Test retrieval statistics."""
        unified_retriever.index_documents(sample_documents)
        
        stats = unified_retriever.get_retrieval_stats()
        
        assert stats["component_type"] == "unified_retriever"
        assert stats["indexed_documents"] == 3
        assert stats["dense_weight"] == 0.7
        assert abs(stats["sparse_weight"] - 0.3) < 1e-10
        assert stats["retrieval_type"] == "unified_hybrid_dense_sparse"
        assert stats["embedding_dim"] == 4
        assert stats["faiss_total_vectors"] == 3
        assert stats["faiss_is_trained"] == True
    
    def test_get_configuration(self, unified_retriever):
        """Test configuration retrieval."""
        config = unified_retriever.get_configuration()
        
        assert config["dense_weight"] == 0.7
        assert abs(config["sparse_weight"] - 0.3) < 1e-10
        assert config["embedding_dim"] == 4
        assert config["index_type"] == "IndexFlatIP"
        assert config["normalize_embeddings"] == True
    
    def test_supports_batch_queries(self, unified_retriever):
        """Test batch query support."""
        assert unified_retriever.supports_batch_queries() == False
    
    def test_clear_index(self, unified_retriever, sample_documents):
        """Test index clearing."""
        unified_retriever.index_documents(sample_documents)
        assert len(unified_retriever.documents) == 3
        assert unified_retriever.index is not None
        
        unified_retriever.clear_index()
        
        assert len(unified_retriever.documents) == 0
        assert unified_retriever.index is None
        assert len(unified_retriever._chunks_cache) == 0
        assert unified_retriever._next_doc_id == 0
    
    def test_get_document_count(self, unified_retriever, sample_documents):
        """Test document count retrieval."""
        assert unified_retriever.get_document_count() == 0
        
        unified_retriever.index_documents(sample_documents)
        assert unified_retriever.get_document_count() == 3
    
    def test_get_faiss_info(self, unified_retriever, sample_documents):
        """Test FAISS index information."""
        unified_retriever.index_documents(sample_documents)
        
        info = unified_retriever.get_faiss_info()
        
        assert info["index_type"] == "IndexFlatIP"
        assert info["embedding_dim"] == 4
        assert info["normalize_embeddings"] == True
        assert info["document_count"] == 3
        assert info["is_trained"] == True
        assert info["total_vectors"] == 3
        assert "index_size_bytes" in info
    
    def test_faiss_index_types(self, mock_embedder, sample_documents):
        """Test different FAISS index types."""
        # Test IndexFlatIP
        retriever_ip = UnifiedRetriever(
            embedder=mock_embedder,
            embedding_dim=4,
            index_type="IndexFlatIP"
        )
        retriever_ip.index_documents(sample_documents)
        assert retriever_ip.index is not None
        
        # Test IndexFlatL2
        retriever_l2 = UnifiedRetriever(
            embedder=mock_embedder,
            embedding_dim=4,
            index_type="IndexFlatL2"
        )
        retriever_l2.index_documents(sample_documents)
        assert retriever_l2.index is not None
    
    def test_unsupported_index_type(self, mock_embedder, sample_documents):
        """Test unsupported FAISS index type."""
        retriever = UnifiedRetriever(
            embedder=mock_embedder,
            embedding_dim=4,
            index_type="UnsupportedIndex"
        )
        
        with pytest.raises(ValueError, match="Unsupported FAISS index type"):
            retriever.index_documents(sample_documents)
    
    def test_embedding_normalization(self, mock_embedder):
        """Test embedding normalization."""
        retriever = UnifiedRetriever(
            embedder=mock_embedder,
            embedding_dim=4,
            normalize_embeddings=True
        )
        
        # Test normalization
        embeddings = np.array([[1.0, 2.0, 3.0, 4.0], [2.0, 4.0, 6.0, 8.0]])
        normalized = retriever._normalize_embeddings(embeddings)
        
        # Check that vectors are normalized (magnitude = 1)
        norms = np.linalg.norm(normalized, axis=1)
        np.testing.assert_array_almost_equal(norms, [1.0, 1.0])
    
    def test_doc_id_generation(self, unified_retriever):
        """Test automatic document ID generation."""
        docs = [
            Document(
                content="Doc 1",
                metadata={"source": "test1.pdf"},
                embedding=[0.1, 0.2, 0.3, 0.4]
            ),
            Document(
                content="Doc 2", 
                metadata={"source": "test2.pdf"},
                embedding=[0.2, 0.3, 0.4, 0.5]
            )
        ]
        
        unified_retriever.index_documents(docs)
        
        # Check that doc_ids were added to metadata
        assert "doc_id" in unified_retriever.documents[0].metadata
        assert "doc_id" in unified_retriever.documents[1].metadata
        assert unified_retriever.documents[0].metadata["doc_id"] == "0"
        assert unified_retriever.documents[1].metadata["doc_id"] == "1"


class TestUnifiedRetrieverIntegration:
    """Integration tests for UnifiedRetriever."""
    
    @pytest.fixture
    def real_documents(self):
        """Create realistic documents for integration testing."""
        return [
            Document(
                content="RISC-V is a free and open instruction set architecture (ISA) "
                       "enabling a new era of processor innovation through open standard collaboration.",
                metadata={"source": "riscv_overview.pdf", "page": 1, "section": "Introduction"},
                embedding=[0.1, 0.2, 0.3, 0.4]
            ),
            Document(
                content="The RISC-V vector extension provides a standardized way to express "
                       "data-parallel computations in a portable and efficient manner.",
                metadata={"source": "vector_extension.pdf", "page": 15, "section": "Vector Operations"},
                embedding=[0.15, 0.25, 0.35, 0.45]
            ),
            Document(
                content="Memory management units (MMUs) in RISC-V processors handle virtual "
                       "to physical address translation and memory protection.",
                metadata={"source": "memory_management.pdf", "page": 42, "section": "MMU Design"},
                embedding=[0.2, 0.3, 0.4, 0.5]
            )
        ]
    
    def test_end_to_end_retrieval(self, real_documents):
        """Test complete end-to-end retrieval workflow."""
        embedder = MockEmbedder()
        retriever = UnifiedRetriever(
            embedder=embedder,
            dense_weight=0.6,
            embedding_dim=4,
            normalize_embeddings=True
        )
        
        # Index documents
        retriever.index_documents(real_documents)
        
        # Verify indexing
        assert retriever.get_document_count() == 3
        stats = retriever.get_retrieval_stats()
        assert stats["indexed_documents"] == 3
        assert stats["faiss_total_vectors"] == 3
        
        # Test configuration
        config = retriever.get_configuration()
        assert config["dense_weight"] == 0.6
        assert config["sparse_weight"] == 0.4
    
    def test_multiple_index_cycles(self, real_documents):
        """Test multiple index/clear cycles."""
        embedder = MockEmbedder()
        retriever = UnifiedRetriever(embedder=embedder, embedding_dim=4)
        
        # First cycle
        retriever.index_documents(real_documents)
        assert retriever.get_document_count() == 3
        
        # Clear and second cycle
        retriever.clear_index()
        assert retriever.get_document_count() == 0
        
        retriever.index_documents(real_documents[:2])
        assert retriever.get_document_count() == 2
    
    def test_error_handling_robustness(self):
        """Test error handling in various scenarios."""
        embedder = MockEmbedder()
        retriever = UnifiedRetriever(embedder=embedder, embedding_dim=4)
        
        # Test query before indexing
        with pytest.raises(RuntimeError):
            retriever.retrieve("test", k=1)
        
        # Test invalid queries
        docs = [Document("test", embedding=[0.1, 0.2, 0.3, 0.4])]
        retriever.index_documents(docs)
        
        with pytest.raises(ValueError):
            retriever.retrieve("", k=1)
        
        with pytest.raises(ValueError):
            retriever.retrieve("test", k=0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])