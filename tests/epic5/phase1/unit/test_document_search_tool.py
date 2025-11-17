"""
Unit tests for DocumentSearchTool.

Tests cover:
- Retriever integration
- Result formatting
- Error handling
- Input validation
- Empty result handling
- Tool interface compliance

Test Strategy:
- Mock retriever for isolated testing
- Comprehensive coverage of search scenarios
- Validation of error handling (tools never raise exceptions)
- Verification of ToolResult structure
"""

import pytest
from typing import List
from unittest.mock import Mock, MagicMock

from src.components.query_processors.tools.implementations import DocumentSearchTool
from src.components.query_processors.tools import ToolResult, ToolParameter
from src.core.interfaces import Retriever, RetrievalResult, Document


class TestDocumentSearchToolBasics:
    """Test basic document search tool functionality."""

    def test_tool_initialization_with_retriever(self):
        """Test tool can be initialized with retriever."""
        mock_retriever = Mock(spec=Retriever)
        tool = DocumentSearchTool(retriever=mock_retriever)

        assert tool is not None
        assert tool.name == "search_documents"

    def test_tool_initialization_without_retriever(self):
        """Test tool can be initialized without retriever."""
        tool = DocumentSearchTool()

        assert tool is not None
        assert tool.name == "search_documents"

    def test_set_retriever(self):
        """Test setting retriever after initialization."""
        tool = DocumentSearchTool()
        mock_retriever = Mock(spec=Retriever)

        tool.set_retriever(mock_retriever)

        # Tool should now have retriever
        result = tool.execute(query="test")
        mock_retriever.retrieve.assert_called_once()

    def test_tool_name(self):
        """Test tool has correct name."""
        tool = DocumentSearchTool()
        assert tool.name == "search_documents"
        assert isinstance(tool.name, str)

    def test_tool_description(self):
        """Test tool has meaningful description."""
        tool = DocumentSearchTool()
        assert tool.description is not None
        assert len(tool.description) > 0
        assert "search" in tool.description.lower() or "document" in tool.description.lower()

    def test_get_parameters(self):
        """Test tool returns correct parameter definitions."""
        tool = DocumentSearchTool()
        params = tool.get_parameters()

        assert isinstance(params, list)
        assert len(params) == 2  # 'query' and 'num_results'

        # Check query parameter
        query_param = next((p for p in params if p.name == "query"), None)
        assert query_param is not None
        assert query_param.required is True

        # Check num_results parameter
        num_results_param = next((p for p in params if p.name == "num_results"), None)
        assert num_results_param is not None
        assert num_results_param.required is False


class TestDocumentSearchExecution:
    """Test search execution with various scenarios."""

    @pytest.fixture
    def mock_document(self) -> Document:
        """Create a mock document."""
        doc = Mock(spec=Document)
        doc.content = "This is a test document about machine learning."
        doc.source = "test.pdf"
        doc.metadata = {"page": 5}
        return doc

    @pytest.fixture
    def mock_retrieval_result(self, mock_document) -> RetrievalResult:
        """Create a mock retrieval result."""
        result = Mock(spec=RetrievalResult)
        result.document = mock_document
        result.score = 0.95
        return result

    @pytest.fixture
    def mock_retriever(self, mock_retrieval_result) -> Mock:
        """Create a mock retriever."""
        retriever = Mock(spec=Retriever)
        retriever.retrieve.return_value = [mock_retrieval_result]
        return retriever

    @pytest.fixture
    def search_tool(self, mock_retriever) -> DocumentSearchTool:
        """Create search tool with mock retriever."""
        return DocumentSearchTool(retriever=mock_retriever)

    def test_successful_search(self, search_tool, mock_retriever):
        """Test successful document search."""
        result = search_tool.execute(query="machine learning", num_results=5)

        assert result.success is True
        assert result.content is not None
        assert result.error is None

        # Verify retriever was called correctly
        mock_retriever.retrieve.assert_called_once_with(query="machine learning", k=5)

    def test_default_num_results(self, search_tool, mock_retriever):
        """Test default num_results parameter."""
        result = search_tool.execute(query="test")

        assert result.success is True

        # Should use default of 5
        mock_retriever.retrieve.assert_called_once_with(query="test", k=5)

    def test_custom_num_results(self, search_tool, mock_retriever):
        """Test custom num_results parameter."""
        result = search_tool.execute(query="test", num_results=10)

        assert result.success is True
        mock_retriever.retrieve.assert_called_once_with(query="test", k=10)

    def test_result_formatting(self, search_tool):
        """Test result formatting includes expected content."""
        result = search_tool.execute(query="test", num_results=5)

        assert result.success is True
        content = result.content

        # Check formatting includes key elements
        assert "Found" in content
        assert "document" in content.lower()
        assert "machine learning" in content  # From mock document
        assert "Score:" in content or "score:" in content.lower()

    def test_metadata_in_result(self, search_tool):
        """Test metadata is included in result."""
        result = search_tool.execute(query="test", num_results=5)

        assert result.success is True
        assert result.metadata is not None
        assert "query" in result.metadata
        assert result.metadata["query"] == "test"
        assert "num_results_requested" in result.metadata
        assert "num_results_found" in result.metadata


class TestDocumentSearchErrorHandling:
    """Test error handling (tools never raise exceptions)."""

    def test_no_retriever_set(self):
        """Test error when retriever not set."""
        tool = DocumentSearchTool()
        result = tool.execute(query="test")

        assert result.success is False
        assert result.error is not None
        assert "retriever" in result.error.lower()

    def test_empty_query(self):
        """Test error on empty query."""
        mock_retriever = Mock(spec=Retriever)
        tool = DocumentSearchTool(retriever=mock_retriever)

        result = tool.execute(query="")

        assert result.success is False
        assert result.error is not None
        assert "empty" in result.error.lower()

    def test_whitespace_only_query(self):
        """Test error on whitespace-only query."""
        mock_retriever = Mock(spec=Retriever)
        tool = DocumentSearchTool(retriever=mock_retriever)

        result = tool.execute(query="   ")

        assert result.success is False
        assert result.error is not None

    def test_invalid_num_results_type(self):
        """Test error on invalid num_results type."""
        mock_retriever = Mock(spec=Retriever)
        tool = DocumentSearchTool(retriever=mock_retriever)

        # String that can be converted to int should work
        result = tool.execute(query="test", num_results="5")
        assert result.success is True

        # String that cannot be converted should fail
        result = tool.execute(query="test", num_results="invalid")
        assert result.success is False
        assert result.error is not None

    def test_num_results_too_small(self):
        """Test error on num_results < 1."""
        mock_retriever = Mock(spec=Retriever)
        tool = DocumentSearchTool(retriever=mock_retriever)

        result = tool.execute(query="test", num_results=0)

        assert result.success is False
        assert result.error is not None

    def test_num_results_too_large(self):
        """Test error on num_results > 20."""
        mock_retriever = Mock(spec=Retriever)
        tool = DocumentSearchTool(retriever=mock_retriever)

        result = tool.execute(query="test", num_results=100)

        assert result.success is False
        assert result.error is not None

    def test_retriever_value_error(self):
        """Test handling of retriever ValueError."""
        mock_retriever = Mock(spec=Retriever)
        mock_retriever.retrieve.side_effect = ValueError("Invalid query")
        tool = DocumentSearchTool(retriever=mock_retriever)

        result = tool.execute(query="test")

        assert result.success is False
        assert result.error is not None
        assert "invalid" in result.error.lower()

    def test_retriever_general_exception(self):
        """Test handling of general retriever exceptions."""
        mock_retriever = Mock(spec=Retriever)
        mock_retriever.retrieve.side_effect = RuntimeError("Connection failed")
        tool = DocumentSearchTool(retriever=mock_retriever)

        result = tool.execute(query="test")

        assert result.success is False
        assert result.error is not None


class TestDocumentSearchEmptyResults:
    """Test handling of empty search results."""

    @pytest.fixture
    def empty_retriever(self) -> Mock:
        """Create retriever that returns no results."""
        retriever = Mock(spec=Retriever)
        retriever.retrieve.return_value = []
        return retriever

    def test_empty_results(self, empty_retriever):
        """Test handling of empty search results."""
        tool = DocumentSearchTool(retriever=empty_retriever)
        result = tool.execute(query="nonexistent query")

        assert result.success is True  # Empty results are not an error
        assert result.content is not None
        assert "No documents found" in result.content or "no documents" in result.content.lower()

    def test_empty_results_metadata(self, empty_retriever):
        """Test metadata for empty results."""
        tool = DocumentSearchTool(retriever=empty_retriever)
        result = tool.execute(query="test")

        assert result.metadata["num_results_found"] == 0


class TestDocumentSearchResultFormatting:
    """Test result formatting with various document types."""

    def test_multiple_results_formatting(self):
        """Test formatting of multiple search results."""
        # Create multiple mock results
        doc1 = Mock(spec=Document)
        doc1.content = "First document"
        doc1.source = "doc1.pdf"
        doc1.metadata = {"page": 1}

        doc2 = Mock(spec=Document)
        doc2.content = "Second document"
        doc2.source = "doc2.pdf"
        doc2.metadata = {"page": 2}

        result1 = Mock(spec=RetrievalResult)
        result1.document = doc1
        result1.score = 0.95

        result2 = Mock(spec=RetrievalResult)
        result2.document = doc2
        result2.score = 0.85

        mock_retriever = Mock(spec=Retriever)
        mock_retriever.retrieve.return_value = [result1, result2]

        tool = DocumentSearchTool(retriever=mock_retriever)
        result = tool.execute(query="test")

        assert result.success is True
        content = result.content

        # Check both results are included
        assert "First document" in content
        assert "Second document" in content
        assert "doc1.pdf" in content
        assert "doc2.pdf" in content

    def test_long_content_truncation(self):
        """Test long content is truncated."""
        doc = Mock(spec=Document)
        doc.content = "A" * 1000  # Very long content
        doc.source = "test.pdf"
        doc.metadata = {}

        result_obj = Mock(spec=RetrievalResult)
        result_obj.document = doc
        result_obj.score = 0.9

        mock_retriever = Mock(spec=Retriever)
        mock_retriever.retrieve.return_value = [result_obj]

        tool = DocumentSearchTool(retriever=mock_retriever)
        result = tool.execute(query="test")

        assert result.success is True
        # Content should be truncated with "..."
        assert "..." in result.content

    def test_document_with_section_metadata(self):
        """Test formatting with section metadata."""
        doc = Mock(spec=Document)
        doc.content = "Test content"
        doc.source = "test.pdf"
        doc.metadata = {"page": 5, "section": "Introduction"}

        result_obj = Mock(spec=RetrievalResult)
        result_obj.document = doc
        result_obj.score = 0.9

        mock_retriever = Mock(spec=Retriever)
        mock_retriever.retrieve.return_value = [result_obj]

        tool = DocumentSearchTool(retriever=mock_retriever)
        result = tool.execute(query="test")

        assert result.success is True
        content = result.content

        # Should include section information
        assert "Introduction" in content

    def test_document_without_metadata(self):
        """Test formatting with minimal document information."""
        doc = Mock(spec=Document)
        doc.content = "Test content"
        doc.source = None
        doc.metadata = {}

        result_obj = Mock(spec=RetrievalResult)
        result_obj.document = doc
        result_obj.score = 0.9

        mock_retriever = Mock(spec=Retriever)
        mock_retriever.retrieve.return_value = [result_obj]

        tool = DocumentSearchTool(retriever=mock_retriever)
        result = tool.execute(query="test")

        assert result.success is True
        # Should still format successfully
        assert "Test content" in result.content


class TestDocumentSearchToolInterface:
    """Test tool interface compliance."""

    @pytest.fixture
    def mock_retriever(self) -> Mock:
        """Create mock retriever."""
        doc = Mock(spec=Document)
        doc.content = "Test"
        doc.source = "test.pdf"
        doc.metadata = {}

        result = Mock(spec=RetrievalResult)
        result.document = doc
        result.score = 0.9

        retriever = Mock(spec=Retriever)
        retriever.retrieve.return_value = [result]
        return retriever

    def test_execute_safe_method(self, mock_retriever):
        """Test execute_safe method works correctly."""
        tool = DocumentSearchTool(retriever=mock_retriever)
        result = tool.execute_safe(query="test")

        assert isinstance(result, ToolResult)
        assert result.success is True

    def test_execute_safe_with_validation_error(self, mock_retriever):
        """Test execute_safe handles validation errors."""
        tool = DocumentSearchTool(retriever=mock_retriever)
        result = tool.execute_safe()  # Missing required parameter

        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.error is not None

    def test_anthropic_schema_generation(self, mock_retriever):
        """Test Anthropic schema generation."""
        tool = DocumentSearchTool(retriever=mock_retriever)
        schema = tool.to_anthropic_schema()

        assert "name" in schema
        assert schema["name"] == "search_documents"
        assert "description" in schema
        assert "input_schema" in schema
        assert "properties" in schema["input_schema"]
        assert "query" in schema["input_schema"]["properties"]
        assert "num_results" in schema["input_schema"]["properties"]

    def test_openai_schema_generation(self, mock_retriever):
        """Test OpenAI schema generation."""
        tool = DocumentSearchTool(retriever=mock_retriever)
        schema = tool.to_openai_schema()

        assert "type" in schema
        assert schema["type"] == "function"
        assert "function" in schema
        assert "name" in schema["function"]
        assert schema["function"]["name"] == "search_documents"

    def test_get_stats(self, mock_retriever):
        """Test statistics tracking."""
        tool = DocumentSearchTool(retriever=mock_retriever)

        # Execute searches
        tool.execute_safe(query="test1")
        tool.execute_safe(query="test2")

        stats = tool.get_stats()

        assert "name" in stats
        assert stats["name"] == "search_documents"
        assert "executions" in stats
        assert stats["executions"] == 2

    def test_reset_stats(self, mock_retriever):
        """Test statistics reset."""
        tool = DocumentSearchTool(retriever=mock_retriever)

        tool.execute_safe(query="test")
        stats = tool.get_stats()
        assert stats["executions"] == 1

        tool.reset_stats()
        stats = tool.get_stats()
        assert stats["executions"] == 0


class TestDocumentSearchInputValidation:
    """Test input validation and sanitization."""

    @pytest.fixture
    def mock_retriever(self) -> Mock:
        """Create mock retriever."""
        retriever = Mock(spec=Retriever)
        retriever.retrieve.return_value = []
        return retriever

    def test_query_whitespace_trimming(self, mock_retriever):
        """Test query whitespace is trimmed."""
        tool = DocumentSearchTool(retriever=mock_retriever)
        result = tool.execute(query="  test query  ")

        assert result.success is True
        # Verify trimmed query was passed to retriever
        mock_retriever.retrieve.assert_called_once_with(query="test query", k=5)

    def test_num_results_string_conversion(self, mock_retriever):
        """Test num_results string is converted to int."""
        tool = DocumentSearchTool(retriever=mock_retriever)
        result = tool.execute(query="test", num_results="7")

        assert result.success is True
        mock_retriever.retrieve.assert_called_once_with(query="test", k=7)

    def test_parameter_validation(self, mock_retriever):
        """Test parameter validation."""
        tool = DocumentSearchTool(retriever=mock_retriever)

        # Valid parameters
        valid, error = tool.validate_parameters(query="test", num_results=5)
        assert valid is True
        assert error is None

        # Missing required parameter
        valid, error = tool.validate_parameters(num_results=5)
        assert valid is False
        assert "query" in error.lower()
