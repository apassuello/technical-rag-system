"""Unit tests for QueryAnalysis.final_score field."""

import pytest
from src.components.query_processors.base import QueryAnalysis


pytestmark = [pytest.mark.unit]


class TestQueryAnalysisFinalScore:
    """Verify QueryAnalysis carries final_score from ML analysis."""

    def test_final_score_defaults_to_none(self):
        """QueryAnalysis without final_score should default to None."""
        qa = QueryAnalysis(query="test")
        assert qa.final_score is None

    def test_final_score_round_trips(self):
        """QueryAnalysis should preserve final_score when set."""
        qa = QueryAnalysis(query="test", final_score=0.72)
        assert qa.final_score == 0.72

    def test_final_score_zero_is_not_none(self):
        """final_score=0.0 is a valid score, not None."""
        qa = QueryAnalysis(query="test", final_score=0.0)
        assert qa.final_score == 0.0
        assert qa.final_score is not None


class TestEpic1MLAnalyzerFinalScorePassthrough:
    """Verify Epic1MLAnalyzer passes final_score through to QueryAnalysis."""

    def test_convert_preserves_final_score(self):
        """_convert_to_query_analysis should map AnalysisResult.final_score to QueryAnalysis.final_score."""
        from src.components.query_processors.analyzers.ml_views.view_result import (
            AnalysisResult,
            ComplexityLevel,
        )
        from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer

        # Create analyzer with minimal config
        analyzer = Epic1MLAnalyzer.__new__(Epic1MLAnalyzer)
        analyzer.logger = __import__('logging').getLogger('test')

        ml_result = AnalysisResult(
            query="What is RISC-V?",
            view_results={},
            final_score=0.72,
            final_complexity=ComplexityLevel.COMPLEX,
            confidence=0.85,
        )

        qa = analyzer._convert_to_query_analysis(ml_result)
        assert qa.final_score == 0.72
        assert qa.complexity_score == 0.72
