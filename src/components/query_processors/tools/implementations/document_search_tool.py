"""
Document search tool for RAG system integration.

Provides LLMs with the ability to search through the RAG system's
document collection using semantic and hybrid search.

Architecture:
- Integrates with existing Retriever component
- Formats results for LLM consumption
- NEVER raises exceptions (returns errors in ToolResult)
- Comprehensive result formatting
- Clear error messages for LLM understanding

Usage:
    >>> from src.components.query_processors.tools.implementations import DocumentSearchTool
    >>> from src.components.retrievers import ModularUnifiedRetriever
    >>>
    >>> # Create retriever and tool
    >>> retriever = ModularUnifiedRetriever(config, embedder)
    >>> search_tool = DocumentSearchTool(retriever)
    >>>
    >>> # Execute search
    >>> result = search_tool.execute(
    ...     query="What is machine learning?",
    ...     num_results=5
    ... )
    >>> print(result.content)  # Formatted search results
"""

from typing import List, Optional
import logging

from ..base_tool import BaseTool
from ..models import ToolParameter, ToolParameterType, ToolResult

# Import Retriever interface
from src.core.interfaces import Retriever, RetrievalResult


logger = logging.getLogger(__name__)


class DocumentSearchTool(BaseTool):
    """
    Document search tool for RAG system.

    Searches the RAG system's document collection using the configured
    Retriever component. Results are formatted clearly for LLM consumption.

    Features:
    - Semantic search integration
    - Configurable number of results
    - Clear result formatting with relevance scores
    - Empty result handling
    - Comprehensive error handling

    Example:
        >>> tool = DocumentSearchTool(retriever)
        >>> result = tool.execute(query="neural networks", num_results=3)
        >>> if result.success:
        ...     print(result.content)
        ...     # Output:
        ...     # Found 3 documents:
        ...     #
        ...     # 1. [Score: 0.92]
        ...     # Source: neural_networks.pdf (page 5)
        ...     # Content: Neural networks are computational models...
        ...     #
        ...     # 2. [Score: 0.88]
        ...     # ...
    """

    def __init__(self, retriever: Optional[Retriever] = None):
        """
        Initialize document search tool.

        Args:
            retriever: Retriever component for searching documents.
                      If None, tool will return error when executed.

        Note:
            Retriever can be set after initialization using set_retriever()
            to support lazy initialization patterns.
        """
        super().__init__()
        self._retriever = retriever
        self._logger.info("Initialized DocumentSearchTool")

    def set_retriever(self, retriever: Retriever) -> None:
        """
        Set or update the retriever component.

        Args:
            retriever: Retriever component to use for searches

        Example:
            >>> tool = DocumentSearchTool()
            >>> tool.set_retriever(my_retriever)
        """
        self._retriever = retriever
        self._logger.info(f"Set retriever: {type(retriever).__name__}")

    @property
    def name(self) -> str:
        """
        Tool name.

        Returns:
            "search_documents"
        """
        return "search_documents"

    @property
    def description(self) -> str:
        """
        Tool description for LLM.

        Returns:
            Clear description of search capabilities and when to use it
        """
        return (
            "Search through the technical documentation collection using semantic search. "
            "Finds relevant documents and passages based on the meaning of your query. "
            "Returns the most relevant documents with their content, source information, "
            "and relevance scores. "
            "Use this tool when you need to find information in the documentation to answer questions."
        )

    def get_parameters(self) -> List[ToolParameter]:
        """
        Get tool parameter definitions.

        Returns:
            List of parameters: query (required), num_results (optional)
        """
        return [
            ToolParameter(
                name="query",
                type=ToolParameterType.STRING,
                description=(
                    "Search query text. Can be a question or keywords. "
                    "The search uses semantic understanding to find relevant documents. "
                    "Example: 'What is the purpose of attention mechanisms?'"
                ),
                required=True
            ),
            ToolParameter(
                name="num_results",
                type=ToolParameterType.INTEGER,
                description=(
                    "Number of results to return (1-20). "
                    "Default is 5. Use fewer results for focused searches, "
                    "more results for comprehensive searches."
                ),
                required=False,
                default=5
            )
        ]

    def execute(self, query: str, num_results: int = 5) -> ToolResult:
        """
        Execute document search.

        Args:
            query: Search query text
            num_results: Number of results to return (default: 5)

        Returns:
            ToolResult with:
            - success=True, content=formatted results on success
            - success=False, error=description on failure

        Example:
            >>> result = tool.execute(
            ...     query="transformer architecture",
            ...     num_results=3
            ... )
            >>> if result.success:
            ...     print(result.content)
        """
        try:
            # Validate retriever is set
            if self._retriever is None:
                return ToolResult(
                    success=False,
                    error="Search tool not properly initialized: retriever not set"
                )

            # Validate input
            if not query or not query.strip():
                return ToolResult(
                    success=False,
                    error="Query cannot be empty"
                )

            query = query.strip()

            # Validate num_results
            if not isinstance(num_results, int):
                try:
                    num_results = int(num_results)
                except (ValueError, TypeError):
                    return ToolResult(
                        success=False,
                        error=f"num_results must be an integer, got: {type(num_results).__name__}"
                    )

            if num_results < 1:
                return ToolResult(
                    success=False,
                    error="num_results must be at least 1"
                )

            if num_results > 20:
                return ToolResult(
                    success=False,
                    error="num_results cannot exceed 20 (too many results may not be useful)"
                )

            # Log execution
            self._logger.debug(f"Searching documents: query='{query}', k={num_results}")

            # Execute retrieval
            try:
                results = self._retriever.retrieve(query=query, k=num_results)
            except ValueError as e:
                return ToolResult(
                    success=False,
                    error=f"Invalid search parameters: {str(e)}"
                )
            except Exception as e:
                self._logger.error(f"Retrieval error: {e}", exc_info=True)
                return ToolResult(
                    success=False,
                    error=f"Search failed: {str(e)}"
                )

            # Handle empty results
            if not results:
                return ToolResult(
                    success=True,
                    content=f"No documents found for query: '{query}'",
                    metadata={
                        "query": query,
                        "num_results_requested": num_results,
                        "num_results_found": 0
                    }
                )

            # Format results for LLM
            formatted_results = self._format_results(query, results)

            self._logger.debug(f"Search completed: found {len(results)} results")

            return ToolResult(
                success=True,
                content=formatted_results,
                metadata={
                    "query": query,
                    "num_results_requested": num_results,
                    "num_results_found": len(results),
                    "avg_score": sum(r.score for r in results) / len(results) if results else 0.0
                }
            )

        except Exception as e:
            # This should never happen (all exceptions should be caught above)
            # But we handle it anyway for absolute safety
            self._logger.error(f"Unexpected error in document search: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )

    def _format_results(self, query: str, results: List[RetrievalResult]) -> str:
        """
        Format retrieval results for LLM consumption.

        Args:
            query: Original search query
            results: List of retrieval results

        Returns:
            Formatted string with all results
        """
        lines = [f"Found {len(results)} relevant document(s) for query: '{query}'"]
        lines.append("")  # Empty line for readability

        for idx, result in enumerate(results, 1):
            # Header with score
            lines.append(f"{idx}. [Relevance Score: {result.score:.2f}]")

            # Source information
            source_info = self._format_source(result)
            if source_info:
                lines.append(f"   Source: {source_info}")

            # Content (truncate if very long)
            content = result.document.content
            if len(content) > 500:
                content = content[:497] + "..."

            lines.append(f"   Content: {content}")

            # Add separator between results (except after last one)
            if idx < len(results):
                lines.append("")  # Empty line between results

        return "\n".join(lines)

    def _format_source(self, result: RetrievalResult) -> str:
        """
        Format source information from retrieval result.

        Args:
            result: Retrieval result

        Returns:
            Formatted source string
        """
        doc = result.document
        source_parts = []

        # Add source file if available
        if hasattr(doc, 'source') and doc.source:
            source_parts.append(doc.source)

        # Add page number if available
        if hasattr(doc, 'metadata') and doc.metadata:
            page = doc.metadata.get('page')
            if page is not None:
                source_parts.append(f"page {page}")

            # Add section if available
            section = doc.metadata.get('section')
            if section:
                source_parts.append(f"section: {section}")

        if source_parts:
            return ", ".join(source_parts)
        else:
            return "Unknown source"
