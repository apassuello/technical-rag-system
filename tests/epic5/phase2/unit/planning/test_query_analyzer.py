"""
Unit tests for QueryAnalyzer.

Tests query classification, complexity estimation, intent extraction,
and tool prediction.
"""

import pytest
from src.components.query_processors.agents.planning.query_analyzer import QueryAnalyzer
from src.components.query_processors.agents.models import QueryType


class TestQueryAnalyzer:
    """Test suite for QueryAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> QueryAnalyzer:
        """Create QueryAnalyzer instance."""
        return QueryAnalyzer()

    # Query Type Classification Tests

    def test_simple_query(self, analyzer: QueryAnalyzer) -> None:
        """Test simple query classification."""
        query = "What is machine learning?"
        analysis = analyzer.analyze(query)

        assert analysis.query_type == QueryType.SIMPLE
        assert analysis.complexity < 0.5
        assert analysis.estimated_steps == 1

    def test_research_query(self, analyzer: QueryAnalyzer) -> None:
        """Test research query classification."""
        query = "Research recent papers on transformer architectures"
        analysis = analyzer.analyze(query)

        assert analysis.query_type == QueryType.RESEARCH
        assert "document_search" in analysis.requires_tools
        assert analysis.complexity > 0.3

    def test_analytical_query(self, analyzer: QueryAnalyzer) -> None:
        """Test analytical query classification."""
        query = "Calculate the average of 10, 20, 30, 40, 50"
        analysis = analyzer.analyze(query)

        assert analysis.query_type == QueryType.ANALYTICAL
        assert "calculator" in analysis.requires_tools
        assert analysis.intent == "calculation"

    def test_code_query(self, analyzer: QueryAnalyzer) -> None:
        """Test code-related query classification."""
        query = "Debug this function that has a syntax error"
        analysis = analyzer.analyze(query)

        assert analysis.query_type == QueryType.CODE
        assert "code_analyzer" in analysis.requires_tools
        assert "code_debug" in analysis.intent

    def test_multi_step_query(self, analyzer: QueryAnalyzer) -> None:
        """Test multi-step query classification."""
        query = "First search for ML papers, and then calculate average citations"
        analysis = analyzer.analyze(query)

        assert analysis.query_type == QueryType.MULTI_STEP
        assert analysis.complexity > 0.6
        assert analysis.estimated_steps >= 3

    # Complexity Estimation Tests

    def test_complexity_short_query(self, analyzer: QueryAnalyzer) -> None:
        """Test complexity for short query."""
        query = "What?"
        analysis = analyzer.analyze(query)

        assert 0.0 <= analysis.complexity <= 0.3

    def test_complexity_medium_query(self, analyzer: QueryAnalyzer) -> None:
        """Test complexity for medium query."""
        query = "What is the difference between supervised and unsupervised learning?"
        analysis = analyzer.analyze(query)

        assert 0.2 <= analysis.complexity <= 0.6

    def test_complexity_long_query(self, analyzer: QueryAnalyzer) -> None:
        """Test complexity for long query."""
        query = (
            "Research recent papers on transformer architectures from 2024, "
            "calculate the average number of citations for each paper, "
            "and then analyze which topics are trending based on citation patterns. "
            "Compare these trends with 2023 data and summarize the findings."
        )
        analysis = analyzer.analyze(query)

        assert analysis.complexity > 0.7

    def test_complexity_multiple_questions(self, analyzer: QueryAnalyzer) -> None:
        """Test complexity with multiple questions."""
        query = "What is ML? How does it work? Why is it useful?"
        analysis = analyzer.analyze(query)

        assert analysis.complexity > 0.4  # Multiple questions increase complexity

    # Intent Extraction Tests

    def test_intent_information_retrieval(self, analyzer: QueryAnalyzer) -> None:
        """Test information retrieval intent."""
        query = "What is deep learning?"
        analysis = analyzer.analyze(query)

        assert analysis.intent == "information_retrieval"

    def test_intent_analysis(self, analyzer: QueryAnalyzer) -> None:
        """Test analysis intent."""
        query = "Why do neural networks work better than traditional ML?"
        analysis = analyzer.analyze(query)

        assert analysis.intent == "analysis"

    def test_intent_calculation(self, analyzer: QueryAnalyzer) -> None:
        """Test calculation intent."""
        query = "Calculate 25 * 47 + 100"
        analysis = analyzer.analyze(query)

        assert analysis.intent == "calculation"

    # Entity Extraction Tests

    def test_entity_extraction_capitalized(self, analyzer: QueryAnalyzer) -> None:
        """Test entity extraction for capitalized words."""
        query = "What is PyTorch and how does it compare to TensorFlow?"
        analysis = analyzer.analyze(query)

        assert len(analysis.entities) > 0
        # Should extract "PyTorch" and "TensorFlow"

    def test_entity_extraction_numbers(self, analyzer: QueryAnalyzer) -> None:
        """Test entity extraction for numbers."""
        query = "Calculate 25 * 47 and add 100"
        analysis = analyzer.analyze(query)

        assert "25" in analysis.entities or "47" in analysis.entities or "100" in analysis.entities

    def test_entity_extraction_empty(self, analyzer: QueryAnalyzer) -> None:
        """Test entity extraction with no entities."""
        query = "what is this about"
        analysis = analyzer.analyze(query)

        # Should not extract common words
        assert all(e.lower() not in ["what", "is", "this", "about"] for e in analysis.entities)

    # Tool Prediction Tests

    def test_tool_prediction_calculator(self, analyzer: QueryAnalyzer) -> None:
        """Test calculator tool prediction."""
        query = "Calculate the sum of 1, 2, 3, 4, 5"
        analysis = analyzer.analyze(query)

        assert "calculator" in analysis.requires_tools

    def test_tool_prediction_document_search(self, analyzer: QueryAnalyzer) -> None:
        """Test document search tool prediction."""
        query = "Find information about neural networks"
        analysis = analyzer.analyze(query)

        assert "document_search" in analysis.requires_tools

    def test_tool_prediction_code_analyzer(self, analyzer: QueryAnalyzer) -> None:
        """Test code analyzer tool prediction."""
        query = "Analyze this code for errors"
        analysis = analyzer.analyze(query)

        assert "code_analyzer" in analysis.requires_tools

    def test_tool_prediction_multiple(self, analyzer: QueryAnalyzer) -> None:
        """Test multiple tool prediction."""
        query = "Search for papers and calculate the average citations"
        analysis = analyzer.analyze(query)

        assert "document_search" in analysis.requires_tools
        assert "calculator" in analysis.requires_tools

    # Step Estimation Tests

    def test_step_estimation_simple(self, analyzer: QueryAnalyzer) -> None:
        """Test step estimation for simple query."""
        query = "What is AI?"
        analysis = analyzer.analyze(query)

        assert analysis.estimated_steps == 1

    def test_step_estimation_complex(self, analyzer: QueryAnalyzer) -> None:
        """Test step estimation for complex query."""
        query = "Research papers, calculate average, and analyze trends"
        analysis = analyzer.analyze(query)

        assert analysis.estimated_steps >= 3

    def test_step_estimation_multi_step(self, analyzer: QueryAnalyzer) -> None:
        """Test step estimation for multi-step query."""
        query = "First do A, and then do B, after that do C"
        analysis = analyzer.analyze(query)

        assert analysis.estimated_steps >= 4  # Multi-step adds +2

    # Edge Cases

    def test_empty_query(self, analyzer: QueryAnalyzer) -> None:
        """Test analysis with empty query."""
        query = ""
        analysis = analyzer.analyze(query)

        assert analysis.query_type == QueryType.SIMPLE
        assert analysis.complexity == 0.0
        assert analysis.estimated_steps == 1

    def test_whitespace_query(self, analyzer: QueryAnalyzer) -> None:
        """Test analysis with whitespace-only query."""
        query = "   "
        analysis = analyzer.analyze(query)

        assert analysis.query_type == QueryType.SIMPLE
        assert analysis.complexity < 0.2

    def test_very_long_query(self, analyzer: QueryAnalyzer) -> None:
        """Test analysis with very long query."""
        query = "word " * 200  # 200 words
        analysis = analyzer.analyze(query)

        assert analysis.complexity > 0.5
        assert len(analysis.metadata["query_length"]) > 1000

    # Metadata Tests

    def test_metadata_includes_query_length(self, analyzer: QueryAnalyzer) -> None:
        """Test that metadata includes query length."""
        query = "What is machine learning?"
        analysis = analyzer.analyze(query)

        assert "query_length" in analysis.metadata
        assert analysis.metadata["query_length"] == len(query)

    def test_metadata_includes_word_count(self, analyzer: QueryAnalyzer) -> None:
        """Test that metadata includes word count."""
        query = "What is machine learning?"
        analysis = analyzer.analyze(query)

        assert "word_count" in analysis.metadata
        assert analysis.metadata["word_count"] == 4

    def test_metadata_includes_question_marks(self, analyzer: QueryAnalyzer) -> None:
        """Test that metadata includes question mark count."""
        query = "What is this? How does it work?"
        analysis = analyzer.analyze(query)

        assert "question_marks" in analysis.metadata
        assert analysis.metadata["question_marks"] == 2
