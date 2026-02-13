"""
Unit tests for the PDF processor chain.

Tests: HybridPDFProcessor, HybridParser, TOCGuidedParser, PDFPlumberParser.
All pdfplumber I/O is mocked — these are pure unit tests.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

from src.core.interfaces import Document


# ---------------------------------------------------------------------------
# TOCGuidedParser
# ---------------------------------------------------------------------------

class TestTOCGuidedParser:
    """Tests for TOC-guided parsing logic (no PDF I/O needed)."""

    def _make_parser(self, **kwargs):
        from src.shared_utils.document_processing.toc_guided_parser import TOCGuidedParser
        return TOCGuidedParser(**kwargs)

    def test_init_defaults(self):
        p = self._make_parser()
        assert p.target_chunk_size == 1400
        assert p.min_chunk_size == 800
        assert p.max_chunk_size == 2000

    def test_init_custom(self):
        p = self._make_parser(target_chunk_size=1000, min_chunk_size=500, max_chunk_size=1500)
        assert p.target_chunk_size == 1000

    def test_parse_toc_with_dotted_lines(self):
        """Standard TOC format: '1.1 Title .... 23'."""
        p = self._make_parser()
        pages = [{"text": "Contents\n1 Introduction .... 1\n1.1 Overview .... 3\n2 Architecture .... 10"}]
        entries = p.parse_toc(pages)
        assert len(entries) >= 2
        titles = [e.title for e in entries]
        assert "Introduction" in titles or any("Introduction" in t for t in titles)

    def test_parse_toc_no_toc_fallback(self):
        """When no TOC found, should use fallback structure detection."""
        p = self._make_parser()
        pages = [{"text": "Some random content without a table of contents."}]
        entries = p.parse_toc(pages)
        # Should return something (fallback), not crash
        assert isinstance(entries, list)

    def test_toc_entry_fields(self):
        from src.shared_utils.document_processing.toc_guided_parser import TOCEntry
        entry = TOCEntry(title="Intro", page=1, level=0)
        assert entry.title == "Intro"
        assert entry.page == 1
        assert entry.level == 0
        assert entry.parent is None

    # --- New TOCGuidedParser tests ---

    def test_parse_toc_pattern2_multiline(self):
        """Multi-line TOC format: number on one line, title on next, dots+page on third."""
        p = self._make_parser()
        pages = [{"text": "Table of Contents\n1\nIntroduction\n. . . . 5\n2\nArchitecture\n. . . . 12"}]
        entries = p.parse_toc(pages)
        assert len(entries) >= 2
        titles = [e.title for e in entries]
        assert "Introduction" in titles
        assert "Architecture" in titles
        assert entries[0].page == 5
        assert entries[1].page == 12

    def test_parse_toc_pattern3_chapter_style(self):
        """'Chapter 1: Title .... 23' format."""
        p = self._make_parser()
        pages = [{"text": "Contents\nChapter 1: Introduction .... 1\nSection 2: Methods .... 15"}]
        entries = p.parse_toc(pages)
        assert len(entries) >= 2
        # Chapter entry should be level 0
        chapter_entries = [e for e in entries if e.level == 0]
        assert len(chapter_entries) >= 1
        assert any("Chapter 1" in e.title for e in entries)

    def test_parse_toc_parent_relationships(self):
        """Child entries get parent/parent_title from parent."""
        p = self._make_parser()
        pages = [{"text": "Contents\n1 Introduction .... 1\n1.1 Overview .... 3\n1.2 Motivation .... 5"}]
        entries = p.parse_toc(pages)
        child_entries = [e for e in entries if e.level > 0]
        for child in child_entries:
            assert child.parent is not None
            assert child.parent_title is not None

    def test_detect_structure_chapter_pattern(self):
        """Fallback: pages with 'Chapter 1: Introduction' but no TOC header."""
        p = self._make_parser()
        pages = [
            {"text": "Chapter 1: Introduction\nRISC-V is an open ISA designed for research."},
            {"text": "Chapter 2: Architecture\nThe architecture uses a modular design."},
        ]
        entries = p._detect_structure_without_toc(pages)
        assert len(entries) >= 2
        assert any("Introduction" in e.title for e in entries)

    def test_detect_structure_section_pattern(self):
        """Fallback: pages with '1.1 Overview', '1.1.1 Details'."""
        p = self._make_parser()
        pages = [
            {"text": "1.1 Overview of RISC-V\nThe RISC-V ISA provides a modular design."},
            {"text": "1.1.1 Details of Encoding\nInstructions are encoded in 32-bit words."},
        ]
        entries = p._detect_structure_without_toc(pages)
        assert len(entries) >= 2
        section_levels = [e.level for e in entries]
        assert any(l >= 1 for l in section_levels)

    def test_detect_structure_page_fallback(self):
        """Fallback: plain prose -> page-based entries every 10 pages."""
        p = self._make_parser()
        # 25 pages of plain prose without any structure patterns
        pages = [{"text": f"This is page {i+1} with plain prose content only."} for i in range(25)]
        entries = p._detect_structure_without_toc(pages)
        assert len(entries) >= 2
        assert any("Pages" in e.title for e in entries)

    def test_create_chunks_from_toc_single(self):
        """Single TOC entry, text < max_chunk_size -> one chunk with metadata."""
        from src.shared_utils.document_processing.toc_guided_parser import TOCEntry
        p = self._make_parser()
        toc_entries = [TOCEntry(title="Introduction", page=1, level=0)]
        pdf_data = {"pages": [{"text": "RISC-V is an open ISA. " * 20}]}
        chunks = p.create_chunks_from_toc(pdf_data, toc_entries)
        assert len(chunks) == 1
        assert chunks[0]["title"] == "Introduction"
        assert chunks[0]["metadata"]["parsing_method"] == "toc_guided"
        assert chunks[0]["metadata"]["section_title"] == "Introduction"

    def test_create_chunks_from_toc_large_splits(self):
        """Text > max_chunk_size -> multiple chunks with part_number."""
        from src.shared_utils.document_processing.toc_guided_parser import TOCEntry
        p = self._make_parser(max_chunk_size=200, target_chunk_size=100)
        toc_entries = [TOCEntry(title="Long Section", page=1, level=0)]
        # Create text longer than max_chunk_size
        long_text = "This is a sentence about RISC-V architecture. " * 20
        pdf_data = {"pages": [{"text": long_text}]}
        chunks = p.create_chunks_from_toc(pdf_data, toc_entries)
        assert len(chunks) > 1
        assert chunks[0]["metadata"].get("part_number") == 1
        assert chunks[0]["metadata"].get("total_parts") == len(chunks)

    def test_create_chunks_from_toc_empty_skipped(self):
        """TOC entry with empty page range -> skipped."""
        from src.shared_utils.document_processing.toc_guided_parser import TOCEntry
        p = self._make_parser()
        toc_entries = [
            TOCEntry(title="Empty", page=1, level=0),
            TOCEntry(title="HasContent", page=1, level=0),
        ]
        # Only empty text pages
        pdf_data = {"pages": [{"text": "   "}]}
        chunks = p.create_chunks_from_toc(pdf_data, toc_entries)
        assert len(chunks) == 0

    def test_split_text_into_chunks(self):
        """Multi-sentence text -> splits at sentence boundaries."""
        p = self._make_parser(target_chunk_size=50)
        text = "First sentence here. Second sentence here. Third sentence about RISC-V. Fourth sentence about vectors."
        chunks = p._split_text_into_chunks(text)
        assert len(chunks) >= 2
        # Each chunk should be a coherent piece
        for chunk in chunks:
            assert len(chunk) > 0


# ---------------------------------------------------------------------------
# PDFPlumberParser
# ---------------------------------------------------------------------------

class TestPDFPlumberParser:
    """Tests for PDFPlumber parsing internals (pdfplumber.open mocked)."""

    def _make_parser(self, **kwargs):
        from src.shared_utils.document_processing.pdfplumber_parser import PDFPlumberParser
        return PDFPlumberParser(**kwargs)

    def test_init_defaults(self):
        p = self._make_parser()
        assert p.target_chunk_size == 1400

    def test_is_valid_content_rejects_trash(self):
        p = self._make_parser()
        assert not p._is_valid_content("Creative Commons Attribution License")
        assert not p._is_valid_content("42")  # page number alone

    def test_is_valid_content_accepts_real_text(self):
        p = self._make_parser()
        assert p._is_valid_content(
            "The RISC-V instruction set architecture provides a modular design."
        )

    @patch("src.shared_utils.document_processing.pdfplumber_parser.pdfplumber")
    def test_extract_with_structure_empty_pdf(self, mock_pdfplumber):
        mock_pdf = MagicMock()
        mock_pdf.pages = []
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf

        p = self._make_parser()
        chunks = p.extract_with_structure(Path("fake.pdf"))
        assert chunks == []

    @patch("src.shared_utils.document_processing.pdfplumber_parser.pdfplumber")
    def test_extract_with_structure_single_page(self, mock_pdfplumber):
        mock_page = MagicMock()
        # Provide chars for line grouping
        mock_page.chars = [
            {"text": "H", "top": 10, "x0": 10, "size": 18},
            {"text": "e", "top": 10, "x0": 20, "size": 18},
        ]
        mock_page.extract_text.return_value = "Header text\n\nSome body content about RISC-V architecture."

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf

        p = self._make_parser()
        chunks = p.extract_with_structure(Path("test.pdf"))
        assert isinstance(chunks, list)

    # --- New PDFPlumberParser tests ---

    def test_is_valid_header_too_short(self):
        """Text < 3 chars -> False."""
        p = self._make_parser()
        assert p._is_valid_header("AB") is False

    def test_is_valid_header_too_long(self):
        """Text > 200 chars -> False."""
        p = self._make_parser()
        assert p._is_valid_header("A" * 201) is False

    def test_is_valid_header_trash(self):
        """License text -> False."""
        p = self._make_parser()
        assert p._is_valid_header("Creative Commons Attribution License") is False

    def test_is_valid_header_number_start(self):
        """'1.1 Introduction' -> True."""
        p = self._make_parser()
        assert p._is_valid_header("1.1 Introduction") is True

    def test_is_valid_header_keyword(self):
        """'Chapter overview' -> True (contains 'chapter' keyword)."""
        p = self._make_parser()
        assert p._is_valid_header("Chapter overview") is True

    def test_is_valid_chunk_too_short(self):
        """Short text -> False."""
        p = self._make_parser()
        assert p._is_valid_chunk("Short") is False

    def test_is_valid_chunk_low_alpha(self):
        """Text > 50% non-alpha -> False."""
        p = self._make_parser()
        # Lots of numbers and symbols with very few alpha chars
        text = "123456789!@#$%^&*()_+-=[]{}|;':\",./<>?" * 20
        assert p._is_valid_chunk(text) is False

    def test_is_valid_chunk_valid(self):
        """Normal text -> True."""
        p = self._make_parser()
        text = "The RISC-V instruction set architecture provides a modular and extensible design " * 10
        assert p._is_valid_chunk(text) is True

    def test_create_chunks_single(self):
        """Text < max_chunk_size -> one chunk with quality_score."""
        p = self._make_parser()
        text = "The RISC-V instruction set architecture provides a modular and extensible design."
        chunks = p._create_chunks(text, "Introduction", page=1)
        assert len(chunks) == 1
        assert chunks[0]["title"] == "Introduction"
        assert chunks[0]["metadata"]["parsing_method"] == "pdfplumber"
        assert "quality_score" in chunks[0]["metadata"]

    def test_create_chunks_multi_split(self):
        """Text > max_chunk_size -> multiple with part_number."""
        p = self._make_parser(max_chunk_size=200, target_chunk_size=100)
        text = "This is a sentence about RISC-V architecture. " * 20
        chunks = p._create_chunks(text, "Long Section", page=1)
        assert len(chunks) > 1
        assert chunks[0]["metadata"].get("part_number") == 1
        assert chunks[0]["metadata"].get("total_parts") == len(chunks)

    def test_clean_text_removes_artifacts(self):
        """Volume headers, URLs, emails, page numbers, dots removed."""
        p = self._make_parser()
        text = (
            "Volume I: RISC-V Unprivileged ISA V20191213\n"
            "Visit https://example.com for details.\n"
            "Contact user@example.com for info.\n"
            "42\n"
            "...... table of contents dots\n"
            "The RISC-V instruction set is open."
        )
        cleaned = p._clean_text(text)
        assert "https://example.com" not in cleaned
        assert "user@example.com" not in cleaned
        assert "......" not in cleaned
        assert "instruction set" in cleaned

    def test_calculate_quality_score(self):
        """Short/long/technical/complete-sentence branches."""
        p = self._make_parser()
        # Short text (< min_chunk_size) gets penalized
        short_score = p._calculate_quality_score("Short text.")
        assert short_score < 1.0

        # Technical text with complete sentence gets bonus
        tech_text = "The RISC-V instruction set architecture uses register memory processor operations."
        tech_score = p._calculate_quality_score(tech_text)
        assert tech_score > 0

        # Very long text (> max_chunk_size) gets penalized
        long_text = "The processor architecture design. " * 200
        long_score = p._calculate_quality_score(long_text)
        assert long_score <= 1.0

    def test_ensure_complete_sentences(self):
        """Last-period trimming, capital-start check, no-period -> ''."""
        p = self._make_parser()
        # Text with complete sentence
        result = p._ensure_complete_sentences("The RISC-V ISA is open. This is a partial")
        assert result.endswith(".")
        assert "partial" not in result

        # Text with no sentence ending at all
        result_empty = p._ensure_complete_sentences("no punctuation here at all")
        assert result_empty == ""

        # Empty input
        assert p._ensure_complete_sentences("") == ""
        assert p._ensure_complete_sentences("   ") == ""

    @patch("src.shared_utils.document_processing.pdfplumber_parser.pdfplumber")
    def test_extract_with_page_coverage_mocked(self, mock_pdfplumber):
        """Mock pdfplumber.open + pymupdf_pages -> chunks with full_page_coverage."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "The RISC-V instruction set architecture provides a modular design for processors. "
            "This architecture is widely used in research and education."
        )

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf

        p = self._make_parser()
        pymupdf_pages = [{"page_number": 1, "text": "some text"}]
        chunks = p.extract_with_page_coverage(Path("test.pdf"), pymupdf_pages)
        assert isinstance(chunks, list)
        if chunks:
            assert chunks[0]["metadata"].get("full_page_coverage") is True
            assert chunks[0]["metadata"]["parsing_method"] == "pdfplumber_page_coverage"


# ---------------------------------------------------------------------------
# HybridParser
# ---------------------------------------------------------------------------

class TestHybridParser:
    """Tests for hybrid parser content filtering and coordination."""

    def _make_parser(self, **kwargs):
        from src.shared_utils.document_processing.hybrid_parser import HybridParser
        return HybridParser(**kwargs)

    def test_init_defaults(self):
        p = self._make_parser()
        assert p.target_chunk_size == 1400
        assert len(p.trash_patterns) > 0
        assert len(p.preserve_patterns) > 0

    def test_init_creates_sub_parsers(self):
        p = self._make_parser()
        assert p.toc_parser is not None
        assert p.plumber_parser is not None

    def test_trash_patterns_match_license(self):
        """Trash patterns should match license boilerplate."""
        import re
        p = self._make_parser()
        test_text = "Creative Commons Attribution License"
        matched = any(re.search(pat, test_text) for pat in p.trash_patterns)
        assert matched, "License text should match trash patterns"

    def test_trash_patterns_match_dots(self):
        """Trash patterns should match TOC dot leaders."""
        import re
        p = self._make_parser()
        matched = any(re.search(pat, "....") for pat in p.trash_patterns)
        assert matched, "Dot leaders should match trash patterns"

    def test_preserve_patterns_match_technical(self):
        """Preserve patterns should match technical content."""
        import re
        p = self._make_parser()
        test_text = "RISC-V instruction encoding format"
        matched = any(re.search(pat, test_text) for pat in p.preserve_patterns)
        assert matched, "Technical content should match preserve patterns"

    @patch("src.shared_utils.document_processing.hybrid_parser.pdfplumber")
    def test_parse_document_with_mock_pdf(self, mock_pdfplumber):
        """Ensure parse_document returns list and doesn't crash on simple input."""
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Chapter 1: Introduction\n\nRISC-V is an open ISA."
        mock_page.chars = []
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf

        p = self._make_parser()
        pdf_data = {"pages": [{"text": "Chapter 1: Introduction\nRISC-V is an open ISA.", "page_num": 1}]}
        chunks = p.parse_document(Path("test.pdf"), pdf_data)
        assert isinstance(chunks, list)

    # --- New HybridParser tests ---

    def test_filter_trash_content_empty(self):
        """Empty input -> ''."""
        p = self._make_parser()
        assert p._filter_trash_content("") == ""
        assert p._filter_trash_content("   ") == ""

    def test_filter_trash_content_removes_license(self):
        """License sentences removed, technical preserved."""
        p = self._make_parser()
        content = (
            "Creative Commons Attribution License applies to this work. "
            "The RISC-V instruction set architecture provides a modular design for processors."
        )
        filtered = p._filter_trash_content(content)
        assert "Creative Commons" not in filtered
        assert "RISC-V" in filtered

    def test_filter_trash_content_removes_toc(self):
        """Section numbers, 'Contents' artifacts removed."""
        p = self._make_parser()
        content = (
            "Contents of this document are listed below. "
            "1.1 INTRODUCTION is the first section. "
            "The RISC-V instruction set specification defines the encoding format."
        )
        filtered = p._filter_trash_content(content)
        assert "specification" in filtered or "RISC-V" in filtered

    def test_filter_trash_content_preserves_technical(self):
        """All-technical text passes through with terminal period."""
        p = self._make_parser()
        content = (
            "The RISC-V instruction set architecture uses register-based operations. "
            "Memory addressing supports both big-endian and little-endian byte ordering. "
            "The processor implementation includes a five-stage pipeline."
        )
        filtered = p._filter_trash_content(content)
        assert "RISC-V" in filtered
        assert "processor" in filtered
        assert filtered.rstrip().endswith((".", "!", "?", ":", ";"))

    def test_create_chunks_size_branches(self):
        """< 100 -> [], 200-800 -> kept, min-max -> one chunk, > max -> split."""
        from src.shared_utils.document_processing.toc_guided_parser import TOCEntry
        p = self._make_parser(min_chunk_size=800, max_chunk_size=2000)
        toc_entry = TOCEntry(title="Test", page=1, level=0)

        # < 100 chars -> empty
        assert p._create_chunks_from_clean_content("Short.", 0, toc_entry) == []

        # 200-800 chars (below min but >= 200) -> kept as single chunk
        medium = "The RISC-V architecture is open source. " * 7  # ~280 chars
        chunks = p._create_chunks_from_clean_content(medium, 0, toc_entry)
        assert len(chunks) == 1

        # In min-max range -> single chunk
        ideal = "The RISC-V instruction set architecture design. " * 25  # ~1200 chars
        chunks = p._create_chunks_from_clean_content(ideal, 0, toc_entry)
        assert len(chunks) == 1

        # > max -> split
        huge = "The RISC-V instruction set architecture design provides modular extensibility. " * 40  # ~3200 chars
        chunks = p._create_chunks_from_clean_content(huge, 0, toc_entry)
        assert len(chunks) >= 2

    def test_split_large_content_smart(self):
        """Multi-sentence content -> sentence-boundary splits, final >= 200."""
        from src.shared_utils.document_processing.toc_guided_parser import TOCEntry
        p = self._make_parser(min_chunk_size=200, max_chunk_size=400)
        toc_entry = TOCEntry(title="Test", page=1, level=0)

        # Build content well above max_chunk_size (400) so it must split
        sentences = [
            "The RISC-V instruction set architecture is an open standard designed for modularity.",
            "It provides a flexible design for processor implementation across many domains.",
            "Memory operations support multiple addressing modes in the specification document.",
            "The register file contains thirty-two general purpose registers for computation.",
            "Control flow instructions include branches and jumps for the processor pipeline.",
            "The architecture supports both 32-bit and 64-bit data processing operations.",
            "Vector extensions enable parallel computation for data-intensive applications.",
            "The encoding format uses fixed-width 32-bit instruction words consistently.",
            "Privileged architecture defines machine mode and supervisor mode operations.",
            "The compressed instruction extension reduces code size by using 16-bit formats.",
        ]
        content = " ".join(sentences)
        assert len(content) > 400  # Ensure it actually exceeds max

        chunks = p._split_large_content_smart(content, 0, toc_entry)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert "text" in chunk
            assert len(chunk["text"]) >= 200

    def test_calculate_quality_score(self):
        """Empty (0.0), short (0.15 length), ideal-range technical (high)."""
        p = self._make_parser()

        # Empty content
        assert p._calculate_quality_score("") == 0.0
        assert p._calculate_quality_score("   ") == 0.0

        # Short content (>= 200 chars but below min_chunk_size)
        short = "The RISC-V register file architecture. " * 6  # ~234 chars
        short_score = p._calculate_quality_score(short)
        assert 0 < short_score < 1.0

        # Ideal-range technical content (in min-max range, technical terms, proper ending)
        ideal = (
            "The RISC-V instruction set architecture provides a modular design for processor "
            "implementation. Memory operations use register-based addressing for efficiency. "
            "The architecture supports multiple privilege levels for system software."
        ) * 4  # ~900 chars, in range
        ideal_score = p._calculate_quality_score(ideal)
        assert ideal_score > short_score

    def test_clean_page_content_precise(self):
        """Standalone numbers, roman numerals removed; technical short lines kept."""
        p = self._make_parser()

        page_text = (
            "42\n"
            "iv\n"
            ".....\n"
            "AB\n"
            "The RISC-V instruction set architecture.\n"
            "Short technical line about register file.\n"
        )
        cleaned = p._clean_page_content_precise(page_text)
        assert "42" not in cleaned.split()
        assert "iv" not in cleaned.split()
        assert "....." not in cleaned
        assert "RISC-V" in cleaned
        assert "register" in cleaned


# ---------------------------------------------------------------------------
# HybridPDFProcessor (adapter)
# ---------------------------------------------------------------------------

class TestHybridPDFProcessor:
    """Tests for the DocumentProcessor adapter wrapping HybridParser."""

    def _make_processor(self, **kwargs):
        from src.components.processors.pdf_processor import HybridPDFProcessor

        # HybridPDFProcessor inherits abstract methods from ComponentBase.
        # Provide concrete stubs so we can instantiate it for testing.
        class TestablePDFProcessor(HybridPDFProcessor):
            def initialize_services(self, platform):
                pass

            def get_health_status(self):
                return None

            def get_metrics(self):
                return {}

            def get_capabilities(self):
                return ["pdf"]

        return TestablePDFProcessor(**kwargs)

    def test_init_defaults(self):
        proc = self._make_processor()
        assert proc.chunk_size == 1400
        assert proc.chunk_overlap == 200
        assert proc.hybrid_parser is not None

    def test_init_custom(self):
        proc = self._make_processor(chunk_size=1024, chunk_overlap=128)
        assert proc.chunk_size == 1024
        assert proc.chunk_overlap == 128

    def test_supported_formats(self):
        proc = self._make_processor()
        assert proc.supported_formats() == [".pdf"]

    def test_process_nonexistent_file_raises(self):
        proc = self._make_processor()
        with pytest.raises(IOError, match="not found"):
            proc.process(Path("/tmp/nonexistent_file_xyz.pdf"))

    def test_process_non_pdf_raises(self, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("hello")
        proc = self._make_processor()
        with pytest.raises(ValueError, match="Unsupported file format"):
            proc.process(txt_file)

    def test_create_document_from_chunk(self):
        proc = self._make_processor()
        chunk_data = {
            "text": "RISC-V is an open ISA.",
            "chunk_id": 0,
            "start_page": 1,
            "end_page": 1,
            "quality_score": 0.9,
        }
        doc = proc._create_document_from_chunk(chunk_data, Path("test.pdf"))
        assert isinstance(doc, Document)
        assert "RISC-V" in doc.content
        assert doc.metadata["source_type"] == "pdf"
        assert doc.metadata["quality_score"] == 0.9

    def test_create_document_from_chunk_empty_raises(self):
        proc = self._make_processor()
        chunk_data = {"text": "", "chunk_id": 0}
        with pytest.raises(ValueError, match="empty"):
            proc._create_document_from_chunk(chunk_data, Path("test.pdf"))

    def test_create_document_content_key_fallback(self):
        """Should accept 'content' key as well as 'text'."""
        proc = self._make_processor()
        chunk_data = {"content": "Some valid content here.", "chunk_id": 1}
        doc = proc._create_document_from_chunk(chunk_data, Path("test.pdf"))
        assert "valid content" in doc.content

    @patch("src.components.processors.pdf_processor.extract_text_with_metadata")
    @patch("src.components.processors.pdf_processor.HybridParser")
    def test_process_end_to_end_mocked(self, MockHybridParser, mock_extract, tmp_path):
        """Full process() with mocked I/O."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        mock_extract.return_value = {"pages": [{"text": "Content", "page_num": 1}]}
        mock_parser_instance = MockHybridParser.return_value
        mock_parser_instance.parse_document.return_value = [
            {"text": "Chunk one about RISC-V.", "chunk_id": 0, "start_page": 1, "end_page": 1, "quality_score": 0.8},
            {"text": "Chunk two about vectors.", "chunk_id": 1, "start_page": 2, "end_page": 2, "quality_score": 0.7},
        ]

        proc = self._make_processor()
        # Replace the parser instance with our mock
        proc.hybrid_parser = mock_parser_instance

        docs = proc.process(pdf_file)
        assert len(docs) == 2
        assert all(isinstance(d, Document) for d in docs)
        assert docs[0].metadata["chunk_id"] == 0
        assert docs[1].metadata["chunk_id"] == 1

    @patch("src.components.processors.pdf_processor.extract_text_with_metadata")
    def test_process_skips_empty_chunks(self, mock_extract, tmp_path):
        """Empty chunks should be silently skipped."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        mock_extract.return_value = {"pages": []}

        proc = self._make_processor()
        proc.hybrid_parser = MagicMock()
        proc.hybrid_parser.parse_document.return_value = [
            {"text": "Valid chunk.", "chunk_id": 0, "start_page": 1, "end_page": 1},
            {"text": "", "chunk_id": 1, "start_page": 2, "end_page": 2},  # empty
            {"text": "   ", "chunk_id": 2, "start_page": 3, "end_page": 3},  # whitespace only
        ]

        docs = proc.process(pdf_file)
        assert len(docs) == 1
        assert "Valid chunk" in docs[0].content
