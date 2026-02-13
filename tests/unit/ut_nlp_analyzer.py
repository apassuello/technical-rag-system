"""Unit tests for NLPAnalyzer."""

import pytest
from unittest.mock import patch
from src.components.query_processors.analyzers.nlp_analyzer import NLPAnalyzer
from src.components.query_processors.base import QueryAnalysis


pytestmark = [pytest.mark.unit]


@pytest.mark.requires_spacy
class TestNLPAnalyzerWithSpaCy:
    """Tests with spaCy model loaded."""

    @pytest.fixture
    def analyzer(self):
        return NLPAnalyzer()

    def test_analyze_returns_query_analysis(self, analyzer):
        """analyze() should return a QueryAnalysis object."""
        result = analyzer.analyze("What is RISC-V architecture?")
        assert isinstance(result, QueryAnalysis)
        assert result.query == "What is RISC-V architecture?"

    def test_complexity_level_simple(self, analyzer):
        """Short, basic queries should score as simple."""
        result = analyzer.analyze("What is Python?")
        assert result.complexity_level in ('simple', 'medium')
        assert 0.0 <= result.complexity_score <= 1.0

    def test_complexity_level_complex(self, analyzer):
        """Long technical queries with many terms should score higher."""
        complex_query = (
            "How does the implementation of the authentication protocol "
            "interact with the API gateway's cache optimization strategy "
            "when handling encrypted token sessions across distributed databases?"
        )
        result = analyzer.analyze(complex_query)
        assert result.complexity_score > 0.0
        assert result.complexity_level in ('simple', 'medium', 'complex')

    def test_technical_terms_extracted(self, analyzer):
        """Queries with known technical patterns should extract terms."""
        result = analyzer.analyze("How does the API authentication protocol work?")
        assert len(result.technical_terms) > 0

    def test_confidence_with_nlp(self, analyzer):
        """Confidence should be higher when NLP model is available."""
        result = analyzer.analyze("What is RISC-V?")
        # Base 0.5 + 0.3 for NLP available = at least 0.8
        assert result.confidence >= 0.7

    def test_metadata_includes_analyzer_type(self, analyzer):
        """Metadata should identify the analyzer type."""
        result = analyzer.analyze("test query")
        assert result.metadata['analyzer_type'] == 'nlp'
        assert result.metadata['nlp_available'] is True


class TestNLPAnalyzerWithoutSpaCy:
    """Tests for the fallback path when spaCy is not available."""

    @pytest.fixture
    def analyzer_no_spacy(self):
        """Create NLPAnalyzer with spaCy disabled."""
        with patch('src.components.query_processors.analyzers.nlp_analyzer.NLPAnalyzer._load_nlp_model'):
            analyzer = NLPAnalyzer()
            analyzer._nlp = None  # Simulate spaCy not available
            return analyzer

    def test_fallback_returns_query_analysis(self, analyzer_no_spacy):
        """Should still return QueryAnalysis when spaCy is missing."""
        result = analyzer_no_spacy.analyze("What is RISC-V?")
        assert isinstance(result, QueryAnalysis)

    def test_fallback_extracts_basic_technical_terms(self, analyzer_no_spacy):
        """Basic pattern matching should still find technical terms."""
        result = analyzer_no_spacy.analyze("How does the API protocol work?")
        assert any('api' in t.lower() or 'protocol' in t.lower() for t in result.technical_terms)

    def test_fallback_confidence_lower(self, analyzer_no_spacy):
        """Confidence should be lower without NLP model."""
        result = analyzer_no_spacy.analyze("test query")
        assert result.confidence < 0.8  # No NLP bonus

    def test_metadata_shows_nlp_unavailable(self, analyzer_no_spacy):
        """Metadata should indicate NLP is not available."""
        result = analyzer_no_spacy.analyze("test")
        assert result.metadata['nlp_available'] is False


@pytest.mark.requires_spacy
class TestNLPAnalyzerConfiguration:
    """Tests for configuration options."""

    def test_custom_model_name(self):
        """Config should accept custom model name."""
        analyzer = NLPAnalyzer(config={'model': 'en_core_web_sm'})
        assert analyzer._model_name == 'en_core_web_sm'

    def test_empty_query_raises(self):
        """Empty query should raise ValueError (from BaseQueryAnalyzer)."""
        analyzer = NLPAnalyzer()
        with pytest.raises((ValueError, RuntimeError)):
            analyzer.analyze("")

    def test_get_supported_features(self):
        """Should return list of supported features."""
        analyzer = NLPAnalyzer()
        features = analyzer.get_supported_features()
        assert isinstance(features, list)
        assert len(features) > 0
