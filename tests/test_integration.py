import pytest
import numpy as np
import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))

from shared_utils.document_processing.pdf_parser import extract_text_with_metadata
from shared_utils.document_processing.chunker import chunk_technical_text
from shared_utils.embeddings.generator import generate_embeddings


def test_full_pipeline():
    """Test complete document processing pipeline."""
    pdf_path = Path("data/test/riscv-base-instructions.pdf")

    # Step 1: Extract text
    doc_data = extract_text_with_metadata(pdf_path)
    assert len(doc_data["text"]) > 1000

    # Step 2: Chunk text - use default parameters that work with sentence boundary enforcement
    chunks = chunk_technical_text(doc_data["text"], chunk_size=1400, overlap=200)
    assert len(chunks) > 10  # Should produce many chunks

    # Step 3: Generate embeddings
    chunk_texts = [chunk["text"] for chunk in chunks]
    embeddings = generate_embeddings(chunk_texts)

    assert embeddings.shape[0] == len(chunks)
    assert embeddings.shape[1] == 384

    print(f"Pipeline processed {len(chunks)} chunks in total")
    return {"chunks": chunks, "embeddings": embeddings}


def test_pipeline_performance():
    """Test end-to-end performance."""
    import time

    pdf_path = Path("data/test/riscv-base-instructions.pdf")

    start = time.perf_counter()

    # Full pipeline
    doc_data = extract_text_with_metadata(pdf_path)
    chunks = chunk_technical_text(doc_data["text"])
    chunk_texts = [chunk["text"] for chunk in chunks[:100]]  # Limit for test
    embeddings = generate_embeddings(chunk_texts)

    duration = time.perf_counter() - start

    print(f"Processed {len(chunk_texts)} chunks in {duration:.2f}s")
    assert duration < 10.0  # Should complete quickly
