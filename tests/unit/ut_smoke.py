"""
Smoke tests for Epic1QueryAnalyzer.

Validates instantiation, complexity classification, and query-type handling
using the same config and queries from the original smoke test, but as
proper parametrized pytest cases with exact assertions.
"""

import pytest

from src.components.query_processors.analyzers import Epic1QueryAnalyzer


# -- Shared config fixture ---------------------------------------------------

ANALYZER_CONFIG = {
    "feature_extractor": {
        "technical_terms": {"domains": ["ml", "rag"], "min_term_length": 3}
    },
    "complexity_classifier": {
        "weights": {
            "length": 0.20,
            "syntactic": 0.25,
            "vocabulary": 0.30,
            "question": 0.15,
            "ambiguity": 0.10,
        },
        "thresholds": {"simple": 0.35, "complex": 0.70},
    },
    "model_recommender": {
        "strategy": "balanced",
        "model_mappings": {
            "simple": {
                "provider": "local",
                "model": "qwen2.5-1.5b-instruct",
                "max_cost_per_query": 0.001,
                "avg_latency_ms": 500,
            },
            "medium": {
                "provider": "mistral",
                "model": "mistral-small",
                "max_cost_per_query": 0.01,
                "avg_latency_ms": 1000,
            },
            "complex": {
                "provider": "openai",
                "model": "gpt-4-turbo",
                "max_cost_per_query": 0.10,
                "avg_latency_ms": 2000,
            },
        },
    },
}


@pytest.fixture(scope="module")
def analyzer():
    """Create a shared Epic1QueryAnalyzer for all tests in this module."""
    return Epic1QueryAnalyzer(ANALYZER_CONFIG)


# -- Instantiation -----------------------------------------------------------


def test_analyzer_instantiation(analyzer):
    """Epic1QueryAnalyzer can be created from a valid config."""
    assert analyzer is not None
    assert isinstance(analyzer, Epic1QueryAnalyzer)


# -- Complexity classification -----------------------------------------------


@pytest.mark.parametrize(
    "query, expected_level",
    [
        ("What is RAG?", "simple"),
        ("How does transformer attention work?", "simple"),
        (
            "Implement a hybrid retrieval system with BM25 and dense embeddings",
            "medium",
        ),
    ],
    ids=["short-definition", "short-explanation", "multi-concept-imperative"],
)
def test_complexity_classification(analyzer, query, expected_level):
    """Analyzer returns the exact expected complexity level for each query."""
    analysis = analyzer.analyze(query)
    epic1 = analysis.metadata["epic1_analysis"]

    assert epic1["complexity_level"] == expected_level


@pytest.mark.parametrize(
    "query, expected_level",
    [
        ("What is RAG?", "simple"),
        ("How does transformer attention work?", "simple"),
        (
            "Implement a hybrid retrieval system with BM25 and dense embeddings",
            "medium",
        ),
    ],
    ids=["short-definition", "short-explanation", "multi-concept-imperative"],
)
def test_complexity_score_within_threshold(analyzer, query, expected_level):
    """Complexity score is consistent with its level and the configured thresholds."""
    analysis = analyzer.analyze(query)
    score = analysis.metadata["epic1_analysis"]["complexity_score"]

    if expected_level == "simple":
        assert score < 0.35
    elif expected_level == "medium":
        assert 0.35 <= score < 0.70
    else:
        assert score >= 0.70


# -- Model recommendation follows level -------------------------------------


@pytest.mark.parametrize(
    "query, expected_provider",
    [
        ("What is RAG?", "local"),
        ("How does transformer attention work?", "local"),
        (
            "Implement a hybrid retrieval system with BM25 and dense embeddings",
            "mistral",
        ),
    ],
    ids=["short-definition", "short-explanation", "multi-concept-imperative"],
)
def test_recommended_model_provider(analyzer, query, expected_provider):
    """Recommended model provider matches the complexity level mapping."""
    analysis = analyzer.analyze(query)
    epic1 = analysis.metadata["epic1_analysis"]

    assert epic1["model_provider"] == expected_provider


# -- Query-type handling (intent / suggested_k) ------------------------------


@pytest.mark.parametrize(
    "query, expected_intent, expected_k",
    [
        ("What is RAG?", "definition", 3),
        ("How does transformer attention work?", "explanation", 3),
        (
            "Implement a hybrid retrieval system with BM25 and dense embeddings",
            "statement",
            5,
        ),
    ],
    ids=["what-question", "how-question", "imperative-statement"],
)
def test_query_type_handling(analyzer, query, expected_intent, expected_k):
    """Analyzer maps question types to correct intent categories and suggested k."""
    analysis = analyzer.analyze(query)

    assert analysis.intent_category == expected_intent
    assert analysis.suggested_k == expected_k
