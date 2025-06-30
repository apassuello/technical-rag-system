import pytest
import numpy as np
from shared_utils.embeddings.generator import generate_embeddings


def test_generate_embeddings_basic():
    """Test embedding generation with technical content."""
    texts = [
        "The RISC-V instruction set architecture",
        "Memory management in embedded systems",
        "Real-time operating system concepts",
        "Hardware abstraction layer implementation",
        "Interrupt handling mechanisms",
    ]

    embeddings = generate_embeddings(texts)

    # Test shape and type
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (5, 384)  # all-MiniLM-L6-v2 dimension
    assert embeddings.dtype == np.float32

    # Test uniqueness (different texts should have different embeddings)
    assert not np.allclose(embeddings[0], embeddings[1])


def test_embedding_performance():
    """Test performance with larger batch."""
    texts = ["Technical documentation chunk"] * 50

    import time

    start = time.perf_counter()
    embeddings = generate_embeddings(texts, use_mps=True)
    duration = time.perf_counter() - start

    assert embeddings.shape == (50, 384)
    assert duration < 5.0  # Should complete in under 5 seconds
    print(f"Embedded 50 texts in {duration:.3f}s ({50/duration:.1f} texts/sec)")


def test_embedding_consistency():
    """Test that same input produces same output."""
    text = ["RISC-V processor architecture"]

    emb1 = generate_embeddings(text)
    emb2 = generate_embeddings(text)

    np.testing.assert_array_equal(emb1, emb2)
