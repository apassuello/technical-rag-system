"""
BasicRAG System - Core Integration Tests

This test suite validates the complete BasicRAG system functionality, including
document indexing, semantic search, and edge case handling. Tests use real PDF
documents to ensure production-like behavior.

Test Strategy:
- Unit tests for individual component behaviors
- Integration tests for end-to-end workflows
- Real document testing with RISC-V technical documentation
- Edge case validation (empty index, missing files, etc.)

Test Data:
- Primary test document: riscv-base-instructions.pdf
- Document characteristics: 97 pages of technical documentation
- Expected behaviors: High-quality semantic search results

Performance Expectations:
- Document indexing: <60 seconds for test PDF
- Query response: <100ms for indexed documents
- Memory usage: <500MB during testing

Coverage Areas:
1. System initialization and state management
2. Document indexing pipeline validation
3. Semantic search accuracy and relevance
4. Error handling and edge cases

Author: Arthur Passuello
Date: June 2025
Project: RAG Portfolio - Technical Documentation System
"""

import pytest
import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))

from src.basic_rag import BasicRAG


def test_basic_rag_initialization():
    """
    Test BasicRAG system initialization and default state.
    
    This test validates that the RAG system initializes correctly with:
    - Uninitialized FAISS index (lazy loading pattern)
    - Empty chunk storage
    - Correct embedding dimensions for all-MiniLM-L6-v2
    
    Test Rationale:
    - Ensures clean slate for document indexing
    - Validates memory-efficient lazy initialization
    - Confirms compatibility with embedding model
    """
    # Create new RAG instance
    rag = BasicRAG()
    
    # Validate initial state
    assert rag.index is None, "FAISS index should not be initialized until first document"
    assert len(rag.chunks) == 0, "Chunk storage should be empty initially"
    assert rag.embedding_dim == 768, "Should match all-mpnet-base-v2 dimensions"


def test_basic_rag_index_document():
    """
    Test end-to-end document indexing with real PDF.
    
    This integration test validates the complete indexing pipeline:
    1. PDF text extraction
    2. Text chunking with overlap
    3. Embedding generation
    4. FAISS index creation and population
    5. Metadata storage and alignment
    
    Test Document: RISC-V Base Instructions Manual
    - Technical documentation with ~97 pages
    - Tests handling of complex formatting
    - Validates chunk quality on real technical content
    
    Assertions:
    - Successful chunk generation (>0 chunks)
    - FAISS index initialization and population
    - Metadata completeness and accuracy
    - Chunk count consistency across components
    """
    # Initialize system
    rag = BasicRAG()
    pdf_path = Path("data/test/riscv-base-instructions.pdf")
    
    # Skip test if PDF not available (CI environments)
    if not pdf_path.exists():
        pytest.skip("Test PDF not found - skipping integration test")
    
    # Execute document indexing
    num_chunks = rag.index_document(pdf_path)
    
    # Validate indexing results
    assert num_chunks > 0, "Should generate multiple chunks from 97-page PDF"
    assert rag.index is not None, "FAISS index should be initialized after first document"
    assert len(rag.chunks) == num_chunks, "Chunk storage count should match returned count"
    assert rag.index.ntotal == num_chunks, "FAISS index size should match chunk count"
    
    # Validate chunk metadata structure
    first_chunk = rag.chunks[0]
    assert "text" in first_chunk, "Chunk should contain text content"
    assert "source" in first_chunk, "Chunk should track source document"
    assert "chunk_id" in first_chunk, "Chunk should have unique identifier"
    assert str(pdf_path) == first_chunk["source"], "Source path should be preserved"
    
    # Additional metadata validation
    assert "start_char" in first_chunk, "Should track chunk position"
    assert "end_char" in first_chunk, "Should track chunk end position"
    assert first_chunk["chunk_id"] == 0, "First chunk should have ID 0"


def test_basic_rag_query():
    """
    Test semantic search functionality with real technical queries.
    
    This test validates the retrieval component of RAG:
    1. Document indexing for search preparation
    2. Query embedding generation
    3. FAISS similarity search
    4. Result ranking and metadata retrieval
    5. Source document tracking
    
    Test Query: "What is RISC-V?"
    - Tests understanding of technical concepts
    - Validates semantic similarity (not just keyword matching)
    - Expects relevant chunks from introduction/overview sections
    
    Assertions:
    - Correct result structure
    - Relevance of returned chunks
    - Similarity score presence
    - Source tracking accuracy
    """
    # Initialize and prepare system
    rag = BasicRAG()
    pdf_path = Path("data/test/riscv-base-instructions.pdf")
    
    # Skip if test data unavailable
    if not pdf_path.exists():
        pytest.skip("Test PDF not found - skipping query test")
    
    # Index document for searching
    rag.index_document(pdf_path)
    
    # Execute semantic search query
    result = rag.query("What is RISC-V?", top_k=3)
    
    # Validate result structure
    assert "question" in result, "Result should echo the question"
    assert "chunks" in result, "Result should contain chunks list"
    assert "sources" in result, "Result should contain sources list"
    assert result["question"] == "What is RISC-V?", "Question should be preserved exactly"
    assert len(result["chunks"]) <= 3, "Should respect top_k limit"
    assert len(result["sources"]) > 0, "Should identify source documents"
    
    # Validate chunk quality and metadata
    if result["chunks"]:
        chunk = result["chunks"][0]
        assert "text" in chunk, "Chunk should contain text content"
        assert "similarity_score" in chunk, "Chunk should have similarity score"
        assert "source" in chunk, "Chunk should track source document"
        
        # Validate score range
        assert 0 <= chunk["similarity_score"] <= 1, "Cosine similarity should be in [0,1]"
        
        # Semantic relevance check (top result should mention RISC)
        assert "RISC" in chunk["text"] or "risc" in chunk["text"].lower(), \
            "Top result should be semantically relevant to RISC-V query"


def test_basic_rag_empty_query():
    """
    Test edge case: querying an empty RAG system.
    
    This test validates graceful handling of queries when no documents
    have been indexed. This is a common edge case in production systems
    during initialization or after index clearing.
    
    Expected Behavior:
    - No exceptions raised
    - Empty but valid result structure
    - Original question preserved
    - Empty chunks and sources lists
    
    This ensures the system fails gracefully rather than crashing when
    users attempt searches before indexing documents.
    """
    # Create fresh RAG instance (no documents indexed)
    rag = BasicRAG()
    
    # Attempt query on empty system
    result = rag.query("test question")
    
    # Validate graceful failure
    assert result["question"] == "test question", "Should preserve original question"
    assert result["chunks"] == [], "Should return empty chunks list"
    assert result["sources"] == [], "Should return empty sources list"
    
    # Ensure consistent behavior with different parameters
    result_with_topk = rag.query("another test", top_k=10)
    assert result_with_topk["chunks"] == [], "Should handle top_k on empty index"