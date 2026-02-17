"""Tier 0: Query analyzer validation.

Tests all query analyzers produce valid QueryAnalysis results with
sensible complexity scores. No LLM or retriever needed.

Spec references: SPEC-A1 through SPEC-A4 in docs/specs/query-analyzers.md
"""

import pytest

pytestmark = [pytest.mark.validation]


SIMPLE_QUERIES = [
    "What is RISC-V?",
    "Define instruction set architecture.",
]

COMPLEX_QUERIES = [
    "Compare the performance implications of RISC-V vector extensions versus "
    "ARM SVE for machine learning workloads in edge computing, considering "
    "memory bandwidth constraints and power efficiency trade-offs.",
    "How does the RISC-V privilege architecture interact with hypervisor "
    "extensions to enable nested virtualization in multi-tenant cloud "
    "environments with hardware-enforced isolation guarantees?",
]


def _create_analyzer(analyzer_type: str):
    """Create an analyzer by type name using ComponentFactory."""
    from src.core.component_factory import ComponentFactory
    return ComponentFactory.create_query_analyzer(analyzer_type)


class TestAnalyzerContract:
    """All analyzers must satisfy the BaseQueryAnalyzer contract."""

    @pytest.mark.parametrize("analyzer_type", [
        "rule_based",
        "nlp",
        "epic1",
        pytest.param("epic1_ml", marks=pytest.mark.requires_ml),
    ])
    def test_returns_valid_analysis(self, analyzer_type):
        """Every analyzer should return a QueryAnalysis with required fields."""
        analyzer = _create_analyzer(analyzer_type)
        result = analyzer.analyze("What is RISC-V?")

        assert hasattr(result, "complexity_score"), "Missing complexity_score"
        assert hasattr(result, "complexity_level"), "Missing complexity_level"
        assert 0.0 <= result.complexity_score <= 1.0, (
            f"complexity_score {result.complexity_score} out of [0, 1]"
        )
        assert result.complexity_level in ("simple", "medium", "complex"), (
            f"Unknown complexity_level: {result.complexity_level}"
        )

    @pytest.mark.parametrize("analyzer_type", [
        "rule_based",
        "nlp",
        "epic1",
        pytest.param("epic1_ml", marks=[
            pytest.mark.requires_ml,
            pytest.mark.xfail(reason="Needs locally-trained Epic1 model weights", strict=False),
        ]),
    ])
    def test_simple_query_scores_below_complex(self, analyzer_type):
        """Simple queries should score lower complexity than complex ones."""
        analyzer = _create_analyzer(analyzer_type)

        simple_scores = [analyzer.analyze(q).complexity_score for q in SIMPLE_QUERIES]
        complex_scores = [analyzer.analyze(q).complexity_score for q in COMPLEX_QUERIES]

        avg_simple = sum(simple_scores) / len(simple_scores)
        avg_complex = sum(complex_scores) / len(complex_scores)

        assert avg_simple < avg_complex, (
            f"{analyzer_type}: simple avg ({avg_simple:.3f}) >= complex avg ({avg_complex:.3f})"
        )

    @pytest.mark.parametrize("analyzer_type", [
        "rule_based",
        "nlp",
        "epic1",
        # epic1_ml excluded: SPEC-A4 documents it as non-deterministic
        # (timestamps, performance timing, analysis count side effects)
    ])
    def test_deterministic_results(self, analyzer_type):
        """Same query should produce the same complexity score."""
        analyzer = _create_analyzer(analyzer_type)
        query = "What is RISC-V?"

        r1 = analyzer.analyze(query)
        r2 = analyzer.analyze(query)

        assert abs(r1.complexity_score - r2.complexity_score) < 1e-6, (
            f"{analyzer_type}: non-deterministic scores {r1.complexity_score} vs {r2.complexity_score}"
        )


class TestEpic1AnalyzerSpecific:
    """Epic1QueryAnalyzer-specific: model recommendation and cost estimation."""

    def test_epic1_provides_model_recommendation(self):
        """Epic1 analyzer should include model recommendation in metadata."""
        analyzer = _create_analyzer("epic1")
        result = analyzer.analyze("What is RISC-V?")

        epic1_meta = result.metadata.get("epic1_analysis", {})
        assert "recommended_model" in epic1_meta, "Missing model recommendation"
        assert "cost_estimate" in epic1_meta, "Missing cost estimate"

    def test_epic1_cost_estimates_ordered(self):
        """Complex queries should have higher cost estimates than simple ones."""
        analyzer = _create_analyzer("epic1")

        simple = analyzer.analyze("What is RISC-V?")
        complex_q = analyzer.analyze(COMPLEX_QUERIES[0])

        simple_cost = simple.metadata.get("epic1_analysis", {}).get("cost_estimate", 0)
        complex_cost = complex_q.metadata.get("epic1_analysis", {}).get("cost_estimate", 0)

        assert complex_cost >= simple_cost, (
            f"Complex cost ({complex_cost}) < simple cost ({simple_cost})"
        )
