"""Unit tests for RuleBasedAnalyzer.

RuleBasedAnalyzer is a pure function: takes a query string, returns QueryAnalysis.
No external deps, no ML models, no network calls.
"""

import pytest
from components.query_processors.analyzers.rule_based_analyzer import RuleBasedAnalyzer
from components.query_processors.base import QueryAnalysis


@pytest.fixture
def analyzer():
    return RuleBasedAnalyzer()


class TestRuleBasedAnalyzerBasic:
    """Core analyze() behavior."""

    def test_returns_query_analysis(self, analyzer):
        result = analyzer.analyze("What is Python?")
        assert isinstance(result, QueryAnalysis)

    def test_preserves_original_query(self, analyzer):
        result = analyzer.analyze("How to configure Docker?")
        assert result.query == "How to configure Docker?"

    def test_complexity_score_bounded(self, analyzer):
        result = analyzer.analyze("What is a variable?")
        assert 0.0 <= result.complexity_score <= 1.0

    def test_confidence_bounded(self, analyzer):
        result = analyzer.analyze("Explain inheritance in Python")
        assert 0.0 <= result.confidence <= 1.0

    def test_suggested_k_positive(self, analyzer):
        result = analyzer.analyze("What is REST?")
        assert result.suggested_k >= 1

    def test_empty_query_raises(self, analyzer):
        with pytest.raises((ValueError, RuntimeError)):
            analyzer.analyze("")

    def test_whitespace_only_raises(self, analyzer):
        with pytest.raises((ValueError, RuntimeError)):
            analyzer.analyze("   ")


class TestIntentClassification:
    """Intent detection via pattern matching."""

    def test_definition_intent(self, analyzer):
        result = analyzer.analyze("What is Kubernetes?")
        assert result.intent_category == "definition"

    def test_procedural_intent(self, analyzer):
        result = analyzer.analyze("How to deploy a Docker container?")
        assert result.intent_category == "procedural"

    def test_comparison_intent(self, analyzer):
        result = analyzer.analyze("Compare REST vs GraphQL advantages")
        assert result.intent_category == "comparison"

    def test_troubleshooting_intent(self, analyzer):
        result = analyzer.analyze("Why is my server not working? Error 500")
        assert result.intent_category == "troubleshooting"

    def test_general_intent_fallback(self, analyzer):
        result = analyzer.analyze("Python")
        assert result.intent_category == "general"


class TestTechnicalTermDetection:
    """Technical term extraction."""

    def test_detects_known_keywords(self, analyzer):
        result = analyzer.analyze("Configure the Docker API with JWT authentication")
        terms_lower = [t.lower() for t in result.technical_terms]
        assert "docker" in terms_lower or "api" in terms_lower
        assert "jwt" in terms_lower or "authentication" in terms_lower

    def test_no_terms_for_simple_query(self, analyzer):
        result = analyzer.analyze("Hello world")
        # May detect some terms from structure patterns; just ensure no crash
        assert isinstance(result.technical_terms, list)


class TestComplexityScoring:
    """Complexity heuristics."""

    def test_simple_query_low_complexity(self, analyzer):
        result = analyzer.analyze("What is a list?")
        assert result.complexity_score < 0.5
        assert result.complexity_level in ("simple", "medium")

    def test_complex_query_higher_complexity(self, analyzer):
        result = analyzer.analyze(
            "How to implement a distributed microservice architecture "
            "with authentication, authorization, and encryption "
            "for enterprise production deployment using Kubernetes and Docker?"
        )
        assert result.complexity_score > 0.3
        assert result.complexity_level in ("medium", "complex")

    def test_complexity_level_matches_score(self, analyzer):
        """complexity_level should be consistent with complexity_score."""
        result = analyzer.analyze("What is Python?")
        if result.complexity_score < 0.33:
            assert result.complexity_level == "simple"
        elif result.complexity_score < 0.67:
            assert result.complexity_level == "medium"
        else:
            assert result.complexity_level == "complex"


class TestMetadata:
    """Metadata in the returned QueryAnalysis."""

    def test_metadata_has_analyzer_type(self, analyzer):
        result = analyzer.analyze("What is FAISS?")
        assert result.metadata.get("analyzer_type") == "rule_based"

    def test_metadata_has_patterns_used(self, analyzer):
        result = analyzer.analyze("How to use Redis cache?")
        patterns = result.metadata.get("patterns_used", {})
        assert "intent_patterns" in patterns
        assert "technical_patterns" in patterns


class TestConfiguration:
    """Custom configuration."""

    def test_custom_technical_keywords(self):
        analyzer = RuleBasedAnalyzer(config={"technical_keywords": ["risc-v", "fpga"]})
        result = analyzer.analyze("What is RISC-V?")
        terms_lower = [t.lower() for t in result.technical_terms]
        assert "risc-v" in terms_lower

    def test_disabled_intent_classification(self):
        analyzer = RuleBasedAnalyzer(config={"enable_intent_classification": False})
        result = analyzer.analyze("What is Python?")
        # Should still return a valid QueryAnalysis
        assert isinstance(result, QueryAnalysis)

    def test_get_supported_features(self, analyzer):
        features = analyzer.get_supported_features()
        assert "intent_classification" in features
        assert "technical_term_detection" in features
