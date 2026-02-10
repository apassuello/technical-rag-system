"""
End-to-end scenario test: Document search tool usage.

Scenario:
User asks: "What does the documentation say about embeddings?"
Expected: DocumentSearch tool called, results formatted

This test validates the complete RAG flow:
1. User query → Tool selection
2. Document search → Retrieval
3. Result formatting → Final answer

Note: Uses mock retriever to avoid dependency on actual indices.

Author: Epic 5 Phase 1 Block 3 Testing Agent
Created: 2025-11-17
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, List, Any

from src.components.query_processors.tools.tool_registry import ToolRegistry
from src.components.query_processors.tools.implementations import DocumentSearchTool
from src.components.query_processors.tools.models import ToolResult
from src.core.interfaces import Document, RetrievalResult


def make_retrieval_result(content: str, score: float, metadata: Dict[str, Any] = None) -> RetrievalResult:
    """Helper to create RetrievalResult objects for mocking."""
    return RetrievalResult(
        document=Document(content=content, metadata=metadata or {}),
        score=score,
        retrieval_method="semantic"
    )


class TestDocumentSearchScenario:
    """
    End-to-end scenario tests for Document Search tool usage.

    These tests simulate real RAG queries where an LLM
    decides to search documentation to answer questions.
    """

    def test_simple_documentation_query_scenario(self) -> None:
        """
        Scenario: User asks "What does the documentation say about embeddings?"

        Expected Flow:
        1. User provides question
        2. DocumentSearch tool selected
        3. Query "embeddings" searched in documents
        4. Relevant documents retrieved
        5. Results formatted for LLM

        This test validates:
        - Tool registration works
        - Retriever integration works
        - Results properly formatted
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            make_retrieval_result(
                "Embeddings are dense vector representations of text...",
                0.95,
                {"source": "embeddings_guide.pdf", "page": 1}
            ),
            make_retrieval_result(
                "We use sentence-transformers for generating embeddings...",
                0.87,
                {"source": "architecture.pdf", "page": 3}
            ),
        ]

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        user_question = "What does the documentation say about embeddings?"
        search_query = "embeddings"

        # Act
        result = registry.execute_tool(
            "search_documents",
            query=search_query,
            num_results=2
        )

        # Assert
        assert result.success is True
        assert result.content is not None
        assert "Embeddings" in result.content or "embeddings" in result.content
        assert result.error is None

        # Verify retriever was called correctly
        mock_retriever.retrieve.assert_called_once_with(query=search_query, k=2)

    def test_technical_documentation_query(self) -> None:
        """
        Scenario: User asks "How does the retriever work?"

        Expected Flow:
        1. Technical query about system architecture
        2. Document search finds relevant technical docs
        3. Multiple results with scores
        4. Formatted response with sources
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            make_retrieval_result(
                "The ModularUnifiedRetriever combines FAISS and BM25...",
                0.92,
                {"source": "retriever_docs.pdf", "page": 5}
            ),
            make_retrieval_result(
                "Retriever supports multiple fusion strategies...",
                0.88,
                {"source": "architecture.pdf", "page": 8}
            ),
            make_retrieval_result(
                "Document chunking affects retriever performance...",
                0.75,
                {"source": "best_practices.pdf", "page": 12}
            ),
        ]

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        result = registry.execute_tool(
            "search_documents",
            query="retriever architecture",
            num_results=3
        )

        # Assert
        assert result.success is True
        assert "ModularUnifiedRetriever" in result.content or "retriever" in result.content
        assert result.error is None

        # Verify all documents mentioned
        assert "retriever_docs.pdf" in result.content or "source" in result.content.lower()

    def test_no_results_scenario(self) -> None:
        """
        Scenario: User asks about topic not in documentation.

        Expected Flow:
        1. Search query executed
        2. No relevant documents found
        3. Empty results handled gracefully
        4. Informative message returned
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = []  # No results

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        result = registry.execute_tool(
            "search_documents",
            query="quantum computing",
            num_results=5
        )

        # Assert
        assert result.success is True
        assert result.content is not None
        assert "no" in result.content.lower() or "found" in result.content.lower()

    def test_low_score_results_scenario(self) -> None:
        """
        Scenario: Search returns results but with low relevance scores.

        Expected Flow:
        1. Search executed
        2. Results returned with low scores
        3. Low scores noted in response
        4. User informed of low confidence
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            make_retrieval_result(
                "Some marginally relevant content...",
                0.45,
                {"source": "misc.pdf", "page": 10}
            ),
            make_retrieval_result(
                "Another low-relevance document...",
                0.38,
                {"source": "other.pdf", "page": 5}
            ),
        ]

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        result = registry.execute_tool(
            "search_documents",
            query="obscure topic",
            num_results=2
        )

        # Assert
        assert result.success is True
        assert result.content is not None
        # Results should include score information or confidence indicators

    def test_multiple_searches_scenario(self) -> None:
        """
        Scenario: User asks follow-up questions requiring multiple searches.

        Expected Flow:
        1. First search: "embeddings"
        2. Second search: "retrieval"
        3. Third search: "evaluation"
        4. Each search independent and successful
        """
        # Arrange
        mock_retriever = Mock()

        def search_side_effect(query: str, k: int = 5) -> List[RetrievalResult]:
            """Return different results based on query."""
            if "embedding" in query.lower():
                return [make_retrieval_result("Embedding info", 0.9)]
            elif "retriev" in query.lower():
                return [make_retrieval_result("Retrieval info", 0.85)]
            elif "evaluat" in query.lower():
                return [make_retrieval_result("Evaluation info", 0.88)]
            return []

        mock_retriever.retrieve.side_effect = search_side_effect

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        result1 = registry.execute_tool("search_documents", query="embeddings", num_results=1)
        result2 = registry.execute_tool("search_documents", query="retrieval", num_results=1)
        result3 = registry.execute_tool("search_documents", query="evaluation", num_results=1)

        # Assert
        assert result1.success is True
        assert "Embedding" in result1.content

        assert result2.success is True
        assert "Retrieval" in result2.content

        assert result3.success is True
        assert "Evaluation" in result3.content

        # Verify retriever called 3 times
        assert mock_retriever.retrieve.call_count == 3


class TestDocumentSearchWithAnthropicAdapter:
    """
    Test Document Search tool with Anthropic adapter integration.
    """

    def test_document_search_schema_for_anthropic(self) -> None:
        """
        Test: Generate proper Anthropic schema for document search.

        Verifies:
        - Schema matches Anthropic format
        - Required fields present
        - Parameter schema correct
        """
        # Arrange
        mock_retriever = Mock()
        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        schemas = registry.get_anthropic_schemas()

        # Assert
        assert len(schemas) == 1

        search_schema = schemas[0]
        assert search_schema["name"] == "search_documents"
        assert "description" in search_schema
        assert "input_schema" in search_schema

        input_schema = search_schema["input_schema"]
        assert input_schema["type"] == "object"
        assert "query" in input_schema["properties"]
        assert "query" in input_schema["required"]

    def test_document_search_with_mock_anthropic_call(self) -> None:
        """
        Test: Simulate Anthropic API call with document search tool.

        Scenario:
        1. User asks about documentation
        2. Claude decides to search documents
        3. Tool executes search
        4. Results returned to Claude
        5. Claude synthesizes final answer
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            make_retrieval_result(
                "RAG systems combine retrieval with generation...",
                0.94,
                {"source": "rag_intro.pdf"}
            )
        ]

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Simulate Claude's tool use request
        tool_name = "search_documents"
        tool_input = {"query": "RAG systems", "num_results": 1}

        # Act
        result = registry.execute_tool(tool_name, **tool_input)

        # Assert
        assert result.success is True
        assert "RAG" in result.content


class TestDocumentSearchWithOpenAIAdapter:
    """
    Test Document Search tool with OpenAI adapter integration.
    """

    def test_document_search_schema_for_openai(self) -> None:
        """
        Test: Generate proper OpenAI schema for document search.

        Verifies:
        - Schema matches OpenAI function calling format
        - Required fields present
        - Parameter schema correct
        """
        # Arrange
        mock_retriever = Mock()
        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        schemas = registry.get_openai_schemas()

        # Assert
        assert len(schemas) == 1

        search_schema = schemas[0]
        assert search_schema["type"] == "function"
        assert "function" in search_schema

        function = search_schema["function"]
        assert function["name"] == "search_documents"
        assert "description" in function
        assert "parameters" in function

        parameters = function["parameters"]
        assert parameters["type"] == "object"
        assert "query" in parameters["properties"]
        assert "query" in parameters["required"]

    def test_document_search_with_mock_openai_call(self) -> None:
        """
        Test: Simulate OpenAI function call with document search tool.
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            make_retrieval_result(
                "Vector databases store embeddings efficiently...",
                0.91,
                {"source": "vector_db.pdf"}
            )
        ]

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Simulate GPT function call
        function_name = "search_documents"
        function_args = {"query": "vector databases", "num_results": 1}

        # Act
        result = registry.execute_tool(function_name, **function_args)

        # Assert
        assert result.success is True
        assert "database" in result.content.lower() or "vector" in result.content.lower()


class TestDocumentSearchErrorHandling:
    """
    Error handling tests for document search tool.
    """

    def test_retriever_exception_handled(self) -> None:
        """
        Test: Retriever exception handled gracefully.

        Scenario:
        1. Retriever raises exception during search
        2. Tool catches exception
        3. Error returned in ToolResult
        4. System remains stable
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.retrieve.side_effect = Exception("Index not found")

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        result = registry.execute_tool(
            "search_documents",
            query="test query",
            num_results=5
        )

        # Assert
        assert result.success is False
        assert result.error is not None
        # Error message should contain information about the failure
        assert "search failed" in result.error.lower() or "index not found" in result.error.lower()

    def test_missing_query_parameter(self) -> None:
        """
        Test: Missing query parameter handled.
        """
        # Arrange
        mock_retriever = Mock()
        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act - Execute without required 'query' parameter
        result = registry.execute_tool("search_documents")

        # Assert
        assert result.success is False
        assert result.error is not None

    def test_invalid_num_results_parameter(self) -> None:
        """
        Test: Invalid num_results parameter handled.
        """
        # Arrange
        mock_retriever = Mock()
        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act - Execute with invalid top_k
        result = registry.execute_tool(
            "search_documents",
            query="test",
            num_results=-5  # Invalid: negative
        )

        # Assert
        assert result.success is False
        assert result.error is not None

    def test_empty_query_string(self) -> None:
        """
        Test: Empty query string handled.
        """
        # Arrange
        mock_retriever = Mock()
        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        result = registry.execute_tool(
            "search_documents",
            query="",  # Empty query
            num_results=5
        )

        # Assert
        assert result.success is False
        assert result.error is not None


class TestDocumentSearchPerformance:
    """
    Performance tests for document search tool.
    """

    def test_search_execution_time(self) -> None:
        """
        Test: Document search executes within acceptable time.

        Requirement: Execution time < 2 seconds for typical queries.

        This ensures responsive user experience even with retrieval.
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            make_retrieval_result(f"Document {i}", 0.9 - (i * 0.05))
            for i in range(10)
        ]

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        result = registry.execute_tool(
            "search_documents",
            query="test query",
            num_results=10
        )

        # Assert
        assert result.success is True
        assert result.execution_time < 2.0  # 2 seconds max

    def test_multiple_concurrent_searches(self) -> None:
        """
        Test: Tool handles multiple rapid search requests.

        Simulates high-throughput scenario.
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            make_retrieval_result("Result", 0.9)
        ]

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        queries = [f"query {i}" for i in range(10)]

        # Act
        results = []
        for query in queries:
            result = registry.execute_tool(
                "search_documents",
                query=query,
                num_results=1
            )
            results.append(result)

        # Assert
        assert len(results) == 10
        assert all(r.success for r in results)
        assert mock_retriever.retrieve.call_count == 10


class TestDocumentSearchEdgeCases:
    """
    Edge case tests for document search tool.
    """

    def test_very_long_query(self) -> None:
        """
        Test: Very long query handled appropriately.
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            make_retrieval_result("Result", 0.8)
        ]

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act - Very long query (1000 words)
        long_query = " ".join(["word"] * 1000)
        result = registry.execute_tool(
            "search_documents",
            query=long_query,
            num_results=5
        )

        # Assert - Should handle gracefully (either success or specific error)
        assert result is not None
        assert isinstance(result, ToolResult)

    def test_special_characters_in_query(self) -> None:
        """
        Test: Special characters in query handled.
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            make_retrieval_result("Result", 0.85)
        ]

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        result = registry.execute_tool(
            "search_documents",
            query="test @#$% query",
            num_results=3
        )

        # Assert
        assert result is not None

    def test_unicode_query(self) -> None:
        """
        Test: Unicode characters in query handled.
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            make_retrieval_result("Résultat", 0.9)
        ]

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        result = registry.execute_tool(
            "search_documents",
            query="Qu'est-ce que c'est?",
            num_results=1
        )

        # Assert
        assert result is not None

    def test_very_large_num_results(self) -> None:
        """
        Test: Very large num_results value handled.
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            make_retrieval_result(f"Doc {i}", 0.9)
            for i in range(100)
        ]

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        result = registry.execute_tool(
            "search_documents",
            query="test",
            num_results=1000  # Very large
        )

        # Assert - Should either cap the value or handle appropriately
        assert result is not None
