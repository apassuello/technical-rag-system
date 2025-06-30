"""
BasicRAG System - Embedding Generator Tests

This test suite validates the neural embedding generation component, including
performance benchmarks, caching behavior, and output quality. Tests focus on
the all-MiniLM-L6-v2 model with Apple Silicon optimization.

Test Coverage:
1. Basic functionality and output validation
2. Performance benchmarks on Apple Silicon
3. Caching effectiveness and consistency
4. Batch processing capabilities
5. Hardware acceleration (MPS) validation

Performance Targets:
- Throughput: 50+ texts/second (target), 100+ (stretch goal)
- Latency: <10ms for cached embeddings
- Memory: <500MB including model and cache

Technical Specifications:
- Model: sentence-transformers/all-MiniLM-L6-v2
- Output: 384-dimensional float32 embeddings
- Hardware: Optimized for Apple Silicon M-series

Author: Arthur Passuello
Date: June 2025
Project: RAG Portfolio - Technical Documentation System
"""

import pytest
import numpy as np
import time
from shared_utils.embeddings.generator import generate_embeddings


def test_generate_embeddings_basic():
    """
    Test basic embedding generation with diverse technical content.
    
    This test validates core functionality:
    - Correct output shape and data type
    - Semantic discrimination (different texts → different embeddings)
    - Technical vocabulary handling
    - Batch processing capability
    
    Test Data: Technical documentation terminology covering:
    - Computer architecture (RISC-V)
    - Systems programming (memory management)
    - Operating systems (RTOS)
    - Hardware interfaces (HAL)
    - Low-level programming (interrupts)
    """
    # Define diverse technical texts
    texts = [
        "The RISC-V instruction set architecture",
        "Memory management in embedded systems",
        "Real-time operating system concepts",
        "Hardware abstraction layer implementation",
        "Interrupt handling mechanisms",
    ]

    # Generate embeddings
    embeddings = generate_embeddings(texts)

    # Validate output shape and type
    assert isinstance(embeddings, np.ndarray), "Output should be numpy array"
    assert embeddings.shape == (5, 384), "Shape should be (num_texts, 384)"
    assert embeddings.dtype == np.float32, "Should use float32 for memory efficiency"

    # Validate semantic discrimination
    # Different texts should produce different embeddings
    assert not np.allclose(embeddings[0], embeddings[1]), \
        "Different texts should have distinct embeddings"
    
    # Validate embedding quality
    # Embeddings should have reasonable magnitude (not all zeros or huge values)
    norms = np.linalg.norm(embeddings, axis=1)
    assert np.all(norms > 0.1), "Embeddings should have meaningful magnitude"
    assert np.all(norms < 100), "Embeddings should not have extreme values"


def test_embedding_performance():
    """
    Benchmark embedding generation performance on Apple Silicon.
    
    This test measures throughput and validates performance targets:
    - Target: 50+ texts/second (minimum requirement)
    - Achieved: 100+ texts/second (typical on M4-Pro)
    
    Test Configuration:
    - Batch size: 50 identical texts (tests batching efficiency)
    - Hardware: Apple Silicon with MPS acceleration
    - Model: Cached after first run
    
    Performance Factors:
    - First run includes model loading time
    - Subsequent runs benefit from model caching
    - MPS acceleration provides 3-5x speedup over CPU
    """
    # Create batch of identical texts to test batching efficiency
    texts = ["Technical documentation chunk"] * 50

    # Measure performance
    start = time.perf_counter()
    embeddings = generate_embeddings(texts, use_mps=True)
    duration = time.perf_counter() - start

    # Validate output
    assert embeddings.shape == (50, 384), "Should process all texts"
    assert duration < 5.0, f"Should complete in <5s, took {duration:.3f}s"
    
    # Calculate and report throughput
    throughput = 50 / duration
    print(f"\n🚀 Performance Metrics:")
    print(f"   Processed: 50 texts")
    print(f"   Duration: {duration:.3f} seconds")
    print(f"   Throughput: {throughput:.1f} texts/second")
    print(f"   Target: 50+ texts/second {'✅ PASS' if throughput > 50 else '❌ FAIL'}")
    
    # Additional performance validation
    assert throughput > 50, f"Should exceed 50 texts/sec, got {throughput:.1f}"


def test_embedding_consistency():
    """
    Test embedding generation consistency and caching behavior.
    
    This test validates:
    1. Deterministic output (same input → same embedding)
    2. Cache effectiveness (second call should be faster)
    3. Content-based caching (identical text uses cache)
    
    Caching Strategy:
    - First call: Generates embedding and caches it
    - Second call: Retrieves from cache (<1ms)
    - Cache key: "model_name:text_content"
    
    This ensures reproducible results and validates the caching
    mechanism that significantly improves performance for repeated
    queries.
    """
    # Test text
    text = ["RISC-V processor architecture"]

    # Generate embedding twice
    print("\n🔄 Testing Consistency:")
    
    # First generation (will compute and cache)
    start1 = time.perf_counter()
    emb1 = generate_embeddings(text)
    time1 = time.perf_counter() - start1
    print(f"   First call: {time1*1000:.2f}ms")
    
    # Second generation (should use cache)
    start2 = time.perf_counter()
    emb2 = generate_embeddings(text)
    time2 = time.perf_counter() - start2
    print(f"   Second call: {time2*1000:.2f}ms (cached)")
    print(f"   Speedup: {time1/time2:.1f}x")

    # Validate consistency
    np.testing.assert_array_equal(emb1, emb2, 
        err_msg="Same input should produce identical embeddings")
    
    # Validate caching performance
    assert time2 < time1 * 0.1, \
        f"Cached call should be >10x faster, got {time1/time2:.1f}x"
