import pytest
import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))

from shared_utils.document_processing.pdf_parser import extract_text_with_metadata

def test_extract_text_with_metadata():
    """Test PDF text extraction with RISC-V specification file."""
    pdf_path = Path("data/test/riscv-base-instructions.pdf")
    
    result = extract_text_with_metadata(pdf_path)
    
    # Check return structure
    assert isinstance(result, dict)
    assert "text" in result
    assert "pages" in result
    assert "metadata" in result
    assert "page_count" in result
    assert "extraction_time" in result
    
    # Validate content
    assert isinstance(result["text"], str)
    assert len(result["text"]) > 0
    assert isinstance(result["pages"], list)
    assert len(result["pages"]) == result["page_count"]
    assert result["page_count"] > 0
    assert isinstance(result["extraction_time"], float)
    assert result["extraction_time"] > 0
    
    # Check page structure
    for page in result["pages"]:
        assert "page_number" in page
        assert "text" in page
        assert "char_count" in page
        assert isinstance(page["page_number"], int)
        assert isinstance(page["text"], str)
        assert isinstance(page["char_count"], int)

def test_extract_nonexistent_file():
    """Test handling of non-existent PDF file."""
    pdf_path = Path("nonexistent.pdf")
    
    with pytest.raises(FileNotFoundError):
        extract_text_with_metadata(pdf_path)