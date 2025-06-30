import pytest
from shared_utils.document_processing.chunker import chunk_technical_text


def test_chunk_technical_text():
    """Test chunking with technical content."""
    # Use actual extracted text from your PDF parser
    sample_text = """
    The RISC-V Instruction Set Architecture (ISA) is based on reduced instruction set computer (RISC) principles. 
    The RISC-V ISA is defined as a base integer ISA, which must be present in any implementation, plus optional extensions to the base ISA. 
    The base integer ISAs are very similar to that of the early RISC processors except with no branch delay slots and with support for optional variable-length instruction encoding.
    A RISC-V processor can support one or more base integer ISAs and zero or more extensions.
    The base integer instruction sets are named RV32I, RV64I, and RV128I.
    """

    chunks = chunk_technical_text(sample_text, chunk_size=200, overlap=30)

    # Test basic structure
    assert len(chunks) >= 3  # Should produce multiple chunks
    assert all(isinstance(chunk, dict) for chunk in chunks)

    # Test required fields
    required_fields = [
        "text",
        "start_char",
        "end_char",
        "chunk_id",
        "word_count",
        "sentence_complete",
    ]
    for chunk in chunks:
        for field in required_fields:
            assert field in chunk

    # Test content integrity
    assert all(len(chunk["text"]) <= 250 for chunk in chunks)  # Allow some flexibility
    assert all(chunk["word_count"] > 0 for chunk in chunks)

    # Test sentence completeness (most chunks should end with complete sentences)
    complete_sentences = sum(1 for chunk in chunks if chunk["sentence_complete"])
    assert complete_sentences >= len(chunks) // 2

    # Test overlap works
    if len(chunks) > 1:
        # Should have some text overlap between consecutive chunks
        assert chunks[0]["end_char"] > chunks[1]["start_char"]


def test_chunk_preserves_sentences():
    """Test that chunking doesn't break mid-sentence."""
    text = "First sentence. Second sentence with technical terms like CPU and RAM. Third sentence."

    chunks = chunk_technical_text(text, chunk_size=50, overlap=10)

    # No chunk should end with incomplete sentence (unless forced by size)
    for chunk in chunks:
        if chunk["sentence_complete"]:
            assert chunk["text"].strip().endswith((".", "!", "?", ":", ";"))
