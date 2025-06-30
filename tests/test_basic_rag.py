import pytest
from pathlib import Path
from src.basic_rag import BasicRAG


def test_basic_rag_initialization():
    """Test BasicRAG initialization."""
    rag = BasicRAG()
    assert rag.index is None
    assert len(rag.chunks) == 0
    assert rag.embedding_dim == 384


def test_basic_rag_index_document():
    """Test document indexing with real PDF."""
    rag = BasicRAG()
    pdf_path = Path("data/test/riscv-base-instructions.pdf")
    
    if not pdf_path.exists():
        pytest.skip("Test PDF not found")
    
    num_chunks = rag.index_document(pdf_path)
    
    assert num_chunks > 0
    assert rag.index is not None
    assert len(rag.chunks) == num_chunks
    assert rag.index.ntotal == num_chunks
    
    # Check chunk metadata
    first_chunk = rag.chunks[0]
    assert "text" in first_chunk
    assert "source" in first_chunk
    assert "chunk_id" in first_chunk
    assert str(pdf_path) == first_chunk["source"]


def test_basic_rag_query():
    """Test querying with real PDF content."""
    rag = BasicRAG()
    pdf_path = Path("data/test/riscv-base-instructions.pdf")
    
    if not pdf_path.exists():
        pytest.skip("Test PDF not found")
    
    # Index document
    rag.index_document(pdf_path)
    
    # Query
    result = rag.query("What is RISC-V?", top_k=3)
    
    assert "question" in result
    assert "chunks" in result
    assert "sources" in result
    assert result["question"] == "What is RISC-V?"
    assert len(result["chunks"]) <= 3
    assert len(result["sources"]) > 0
    
    # Check chunk structure
    if result["chunks"]:
        chunk = result["chunks"][0]
        assert "text" in chunk
        assert "similarity_score" in chunk
        assert "source" in chunk


def test_basic_rag_empty_query():
    """Test querying empty RAG system."""
    rag = BasicRAG()
    result = rag.query("test question")
    
    assert result["question"] == "test question"
    assert result["chunks"] == []
    assert result["sources"] == []