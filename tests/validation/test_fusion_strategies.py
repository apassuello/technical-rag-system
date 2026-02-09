"""Tier 0: Fusion strategy validation.

Tests each fusion strategy (RRF, score_aware, graph_enhanced_rrf) by
creating a ModularUnifiedRetriever with that strategy and verifying
retrieval quality against the golden corpus. No LLM needed.

Spec references: SPEC-F1, SPEC-F2, SPEC-F3 in docs/specs/retriever-components.md
"""

import pytest
from .golden_corpus import GOLDEN_RETRIEVAL_CASES, ALL_CORPUS_TEXTS

pytestmark = [pytest.mark.validation, pytest.mark.requires_ml]


FUSION_CONFIGS = [
    pytest.param("rrf", {}, id="rrf-baseline"),
    pytest.param(
        "score_aware",
        {"score_weight": 0.6, "rank_weight": 0.3, "overlap_weight": 0.1, "k": 60},
        id="score-aware",
    ),
    pytest.param(
        "graph_enhanced_rrf",
        {
            "base_fusion": {"k": 60, "weights": {"dense": 0.7, "sparse": 0.3}},
            "graph_enhancement": {"enabled": True, "graph_weight": 0.1},
        },
        id="graph-enhanced-rrf",
    ),
]


class TestFusionStrategyRetrieval:
    """Each fusion strategy should retrieve the right documents."""

    @pytest.mark.parametrize("fusion_type,fusion_config", FUSION_CONFIGS)
    def test_top1_precision_across_strategies(
        self, make_retriever, index_golden_corpus, fusion_type, fusion_config
    ):
        """Every fusion strategy should get top-1 correct on golden cases."""
        retriever = make_retriever(fusion_type=fusion_type, fusion_config=fusion_config)
        index_golden_corpus(retriever)

        for case in GOLDEN_RETRIEVAL_CASES:
            results = retriever.retrieve(case["query"], k=3)
            assert len(results) > 0, f"No results for '{case['query']}' with {fusion_type}"
            expected = ALL_CORPUS_TEXTS[case["expected_top1_index"]]
            assert results[0].document.content == expected, (
                f"{fusion_type}: wrong top-1 for '{case['query']}'"
            )

    @pytest.mark.parametrize("fusion_type,fusion_config", FUSION_CONFIGS)
    def test_scores_are_valid(
        self, make_retriever, index_golden_corpus, fusion_type, fusion_config
    ):
        """All fusion strategies should produce non-negative, monotonic scores."""
        retriever = make_retriever(fusion_type=fusion_type, fusion_config=fusion_config)
        index_golden_corpus(retriever)

        results = retriever.retrieve("What is RISC-V?", k=4)
        scores = [r.score for r in results]

        assert all(s >= 0 for s in scores), f"{fusion_type}: negative scores {scores}"
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], f"{fusion_type}: not monotonic {scores}"

    @pytest.mark.parametrize("fusion_type,fusion_config", FUSION_CONFIGS)
    def test_off_topic_separation(
        self, make_retriever, index_golden_corpus, fusion_type, fusion_config
    ):
        """Off-topic weather doc should not outrank on-topic RISC-V docs."""
        retriever = make_retriever(fusion_type=fusion_type, fusion_config=fusion_config)
        index_golden_corpus(retriever)

        results = retriever.retrieve("What is RISC-V?", k=4)
        contents = [r.document.content for r in results]
        weather = ALL_CORPUS_TEXTS[3]

        if weather in contents:
            assert contents.index(weather) == len(results) - 1, (
                f"{fusion_type}: weather doc not ranked last"
            )


class TestFusionStrategyDifferences:
    """Verify fusion strategies produce meaningfully different results."""

    def test_score_distributions_differ(self, make_retriever, index_golden_corpus):
        """Score-aware and RRF should produce different score distributions."""
        rrf_retriever = make_retriever(fusion_type="rrf")
        index_golden_corpus(rrf_retriever)
        rrf_results = rrf_retriever.retrieve("What is RISC-V?", k=4)
        rrf_scores = [r.score for r in rrf_results]

        sa_retriever = make_retriever(
            fusion_type="score_aware",
            fusion_config={"score_weight": 0.6, "rank_weight": 0.3, "overlap_weight": 0.1},
        )
        index_golden_corpus(sa_retriever)
        sa_results = sa_retriever.retrieve("What is RISC-V?", k=4)
        sa_scores = [r.score for r in sa_results]

        # They may retrieve the same docs in the same order, but scores
        # should differ because the algorithms are fundamentally different
        assert rrf_scores != sa_scores, (
            "RRF and score_aware produced identical scores — are they really different?"
        )
