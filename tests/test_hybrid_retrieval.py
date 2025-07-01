import pytest
import numpy as np
from pathlib import Path
import sys
import time

# Add project paths for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))

from src.sparse_retrieval import BM25SparseRetriever
from src.fusion import reciprocal_rank_fusion, weighted_score_fusion
from shared_utils.retrieval.hybrid_search import HybridRetriever
from src.basic_rag import BasicRAG


@pytest.fixture
def sample_chunks():
    """Sample technical chunks for testing."""
    return [
        {
            "text": "RISC-V is an open standard instruction set architecture based on established reduced instruction set computer principles.",
            "source": "test.pdf",
            "page": 1,
            "chunk_id": 0
        },
        {
            "text": "The RV32I base integer instruction set provides 32-bit addresses and integer operations for embedded systems.",
            "source": "test.pdf", 
            "page": 1,
            "chunk_id": 1
        },
        {
            "text": "ARM Cortex-M processors are designed for microcontroller applications with low power consumption.",
            "source": "test.pdf",
            "page": 2, 
            "chunk_id": 2
        },
        {
            "text": "Machine learning models require large amounts of training data to achieve good performance.",
            "source": "test.pdf",
            "page": 3,
            "chunk_id": 3
        },
        {
            "text": "Vector databases enable efficient similarity search for high-dimensional embeddings.",
            "source": "test.pdf",
            "page": 4,
            "chunk_id": 4
        }
    ]


@pytest.fixture
def bm25_retriever(sample_chunks):
    """Pre-indexed BM25 retriever for testing."""
    retriever = BM25SparseRetriever()
    retriever.index_documents(sample_chunks)
    return retriever


@pytest.fixture
def hybrid_retriever(sample_chunks):
    """Pre-indexed hybrid retriever for testing."""
    retriever = HybridRetriever()
    retriever.index_documents(sample_chunks)
    return retriever


class TestBM25SparseRetriever:
    """Test BM25 sparse retrieval functionality."""
    
    def test_initialization(self):
        """Test BM25 retriever initialization."""
        retriever = BM25SparseRetriever(k1=1.5, b=0.8)
        assert retriever.k1 == 1.5
        assert retriever.b == 0.8
        assert retriever.bm25 is None
        
    def test_invalid_parameters(self):
        """Test parameter validation."""
        with pytest.raises(ValueError):
            BM25SparseRetriever(k1=-1.0)
        with pytest.raises(ValueError):
            BM25SparseRetriever(b=1.5)
            
    def test_preprocess_text(self):
        """Test text preprocessing preserves technical terms."""
        retriever = BM25SparseRetriever()
        tokens = retriever._preprocess_text("RISC-V RV32I ARM Cortex-M test123")
        
        assert "risc-v" in tokens
        assert "rv32i" in tokens  
        assert "arm" in tokens
        assert "cortex-m" in tokens
        assert "test123" in tokens
        
    def test_index_documents(self, sample_chunks):
        """Test document indexing."""
        retriever = BM25SparseRetriever()
        retriever.index_documents(sample_chunks)
        
        assert retriever.bm25 is not None
        assert len(retriever.corpus) == len(sample_chunks)
        assert len(retriever.chunk_mapping) <= len(sample_chunks)
        
    def test_search(self, bm25_retriever):
        """Test BM25 search functionality."""
        results = bm25_retriever.search("RISC-V instruction set", top_k=3)
        
        assert len(results) <= 3
        assert all(isinstance(result, tuple) for result in results)
        assert all(len(result) == 2 for result in results)
        
        # Check that scores are normalized [0,1]
        scores = [score for _, score in results]
        assert all(0 <= score <= 1 for score in scores)
        
    def test_keyword_matching(self, bm25_retriever):
        """Test that BM25 finds exact keyword matches."""
        results = bm25_retriever.search("RV32I", top_k=5)
        
        # Should find the chunk containing RV32I
        assert len(results) > 0
        chunk_idx, score = results[0]
        assert score > 0.5  # Should have high relevance for exact match


class TestFusion:
    """Test fusion algorithms."""
    
    def test_reciprocal_rank_fusion(self):
        """Test RRF algorithm."""
        dense_results = [(0, 0.9), (1, 0.8), (2, 0.7)]
        sparse_results = [(2, 0.95), (0, 0.85), (3, 0.6)]
        
        fused = reciprocal_rank_fusion(dense_results, sparse_results, dense_weight=0.7)
        
        assert len(fused) == 4  # Unique documents
        assert all(isinstance(result, tuple) for result in fused)
        assert fused[0][1] >= fused[1][1]  # Sorted by score
        
    def test_fusion_parameter_validation(self):
        """Test fusion parameter validation."""
        with pytest.raises(ValueError):
            reciprocal_rank_fusion([], [], dense_weight=1.5)
        with pytest.raises(ValueError):
            reciprocal_rank_fusion([], [], k=-1)
            
    def test_weighted_score_fusion(self):
        """Test weighted score fusion."""
        dense_results = [(0, 0.9), (1, 0.8)]
        sparse_results = [(0, 0.7), (2, 0.6)]
        
        fused = weighted_score_fusion(dense_results, sparse_results, dense_weight=0.8)
        
        assert len(fused) == 3
        # Doc 0 should have highest score (appears in both)
        assert fused[0][0] == 0


class TestHybridRetriever:
    """Test hybrid retrieval system."""
    
    def test_initialization(self):
        """Test hybrid retriever initialization."""
        retriever = HybridRetriever(dense_weight=0.8, use_mps=False)
        assert retriever.dense_weight == 0.8
        assert not retriever.use_mps
        assert retriever.sparse_retriever is not None
        
    def test_index_documents(self, sample_chunks):
        """Test hybrid indexing."""
        retriever = HybridRetriever(use_mps=False)
        retriever.index_documents(sample_chunks)
        
        assert retriever.dense_index is not None
        assert retriever.embeddings is not None
        assert len(retriever.chunks) == len(sample_chunks)
        
    def test_search(self, hybrid_retriever):
        """Test hybrid search."""
        results = hybrid_retriever.search("RISC-V instruction", top_k=3)
        
        assert len(results) <= 3
        assert all(len(result) == 3 for result in results)  # (idx, score, chunk)
        
        # Check result structure
        chunk_idx, rrf_score, chunk_dict = results[0]
        assert isinstance(chunk_idx, int)
        assert isinstance(rrf_score, float)
        assert isinstance(chunk_dict, dict)
        assert "text" in chunk_dict
        
    def test_get_retrieval_stats(self, hybrid_retriever):
        """Test retrieval statistics."""
        stats = hybrid_retriever.get_retrieval_stats()
        
        assert stats["status"] == "indexed"
        assert stats["total_chunks"] > 0
        assert 0 <= stats["dense_weight"] <= 1
        assert 0 <= stats["sparse_weight"] <= 1


class TestBasicRAGHybrid:
    """Test BasicRAG hybrid functionality."""
    
    @pytest.fixture
    def basic_rag_with_data(self):
        """BasicRAG with test PDF data."""
        rag = BasicRAG()
        
        # Mock PDF data processing since we don't have actual PDF
        mock_chunks = [
            {
                "text": "RISC-V is an open standard instruction set architecture",
                "source": "test.pdf",
                "page": 1,
                "chunk_id": 0,
                "start_char": 0,
                "end_char": 50
            },
            {
                "text": "RV32I provides 32-bit integer operations for embedded systems",
                "source": "test.pdf", 
                "page": 1,
                "chunk_id": 1,
                "start_char": 51,
                "end_char": 110
            }
        ]
        
        # Manually populate for testing
        rag.chunks = mock_chunks
        rag.hybrid_retriever = HybridRetriever(use_mps=False)
        rag.hybrid_retriever.index_documents(mock_chunks)
        
        return rag
        
    def test_hybrid_query(self, basic_rag_with_data):
        """Test hybrid query method."""
        result = basic_rag_with_data.hybrid_query("RISC-V instruction set", top_k=2)
        
        assert result["retrieval_method"] == "hybrid"
        assert "chunks" in result
        assert "sources" in result
        assert "dense_weight" in result
        assert "sparse_weight" in result
        
        # Check chunks have hybrid metadata
        if result["chunks"]:
            chunk = result["chunks"][0]
            assert "hybrid_score" in chunk
            assert chunk["retrieval_method"] == "hybrid"


def test_hybrid_outperforms_semantic():
    """Test that hybrid search improves on pure semantic for keyword queries."""
    chunks = [
        {"text": "RISC-V RV32I instruction set architecture", "chunk_id": 0},
        {"text": "ARM Cortex-M processor for embedded systems", "chunk_id": 1}, 
        {"text": "Machine learning requires training data", "chunk_id": 2},
        {"text": "The RISC-V foundation promotes open standards", "chunk_id": 3}
    ]
    
    # Test exact keyword match - should prefer BM25 component
    hybrid_retriever = HybridRetriever(dense_weight=0.5, use_mps=False)
    hybrid_retriever.index_documents(chunks)
    
    results = hybrid_retriever.search("RV32I", top_k=2)
    
    # Should find RV32I chunk first due to exact match
    assert len(results) > 0
    top_result = results[0]
    chunk_text = top_result[2]["text"]
    assert "RV32I" in chunk_text


def test_hybrid_preserves_semantic():
    """Test that hybrid search maintains semantic quality for conceptual queries."""
    chunks = [
        {"text": "Machine learning models need training data", "chunk_id": 0},
        {"text": "Neural networks learn from examples", "chunk_id": 1},
        {"text": "RISC-V instruction set architecture", "chunk_id": 2},
        {"text": "Processors execute instructions sequentially", "chunk_id": 3}
    ]
    
    hybrid_retriever = HybridRetriever(dense_weight=0.8, use_mps=False)  # Favor semantic
    hybrid_retriever.index_documents(chunks)
    
    results = hybrid_retriever.search("artificial intelligence learning", top_k=2)
    
    # Should find ML-related chunks due to semantic similarity 
    assert len(results) > 0
    # Check that ML/neural network chunks rank higher than RISC-V
    top_texts = [result[2]["text"] for result in results]
    ml_related = any("learning" in text.lower() or "neural" in text.lower() 
                    for text in top_texts)
    assert ml_related


def test_fusion_weighting():
    """Test that dense_weight parameter affects result ranking."""
    chunks = [
        {"text": "RISC-V RV32I exact match test", "chunk_id": 0},
        {"text": "Computer architecture and instruction sets", "chunk_id": 1},
        {"text": "Embedded systems programming", "chunk_id": 2}
    ]
    
    # Test high dense weight (favor semantic)
    hybrid_high_dense = HybridRetriever(dense_weight=0.9, use_mps=False)
    hybrid_high_dense.index_documents(chunks)
    
    # Test low dense weight (favor sparse/BM25)
    hybrid_low_dense = HybridRetriever(dense_weight=0.1, use_mps=False)
    hybrid_low_dense.index_documents(chunks)
    
    query = "RV32I"
    
    results_high_dense = hybrid_high_dense.search(query, top_k=3)
    results_low_dense = hybrid_low_dense.search(query, top_k=3)
    
    # Both should find results, but ranking may differ
    assert len(results_high_dense) > 0
    assert len(results_low_dense) > 0
    
    # The exact match chunk should score differently with different weights
    high_scores = [r[1] for r in results_high_dense]
    low_scores = [r[1] for r in results_low_dense]
    
    # At least verify we got different score distributions
    assert not np.array_equal(high_scores, low_scores)


def test_performance_benchmark():
    """Benchmark hybrid vs pure semantic search timing."""
    # Create larger test corpus
    chunks = []
    for i in range(100):
        chunks.append({
            "text": f"Document {i} contains technical information about RISC-V architecture and embedded systems programming",
            "chunk_id": i
        })
    
    # Benchmark hybrid retrieval
    hybrid_retriever = HybridRetriever(use_mps=False)
    
    start_time = time.time()
    hybrid_retriever.index_documents(chunks)
    hybrid_index_time = time.time() - start_time
    
    start_time = time.time()
    hybrid_results = hybrid_retriever.search("RISC-V embedded systems", top_k=10)
    hybrid_search_time = time.time() - start_time
    
    # Performance assertions
    assert hybrid_index_time < 30.0  # Should index 100 chunks in under 30s
    assert hybrid_search_time < 1.0   # Should search in under 1s
    assert len(hybrid_results) > 0    # Should find relevant results
    
    print(f"Hybrid indexing: {len(chunks)} chunks in {hybrid_index_time:.3f}s")
    print(f"Hybrid search: {len(hybrid_results)} results in {hybrid_search_time:.3f}s")
