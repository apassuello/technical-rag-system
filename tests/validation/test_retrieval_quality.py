"""Tier 1: Retrieval quality validation.

Tests that the hybrid retriever (FAISS dense + BM25 sparse) returns the
correct documents for known queries. No LLM needed — tests retrieval only.
"""

import pytest
from .golden_corpus import GOLDEN_RETRIEVAL_CASES, ALL_CORPUS_TEXTS

pytestmark = [pytest.mark.validation, pytest.mark.requires_ml]


class TestRetrievalPrecision:
    """Validate that top-1 retrieved doc matches the expected golden doc."""

    @pytest.mark.parametrize(
        "case",
        GOLDEN_RETRIEVAL_CASES,
        ids=[c["query"][:40] for c in GOLDEN_RETRIEVAL_CASES],
    )
    def test_precision_at_1(self, indexed_orchestrator, case):
        """Top retrieved document should be the expected one."""
        retriever = indexed_orchestrator.get_component("retriever")
        results = retriever.retrieve(case["query"], k=3)

        assert len(results) > 0, "Retrieval should return at least 1 result"

        top_doc_content = results[0].document.content
        expected_content = ALL_CORPUS_TEXTS[case["expected_top1_index"]]
        assert top_doc_content == expected_content, (
            f"Top-1 doc mismatch for '{case['query']}'\n"
            f"Got: {top_doc_content[:80]}...\n"
            f"Expected: {expected_content[:80]}..."
        )

    def test_mrr_across_golden_cases(self, indexed_orchestrator):
        """Mean Reciprocal Rank across all golden cases should be >= 0.8."""
        retriever = indexed_orchestrator.get_component("retriever")
        reciprocal_ranks = []

        for case in GOLDEN_RETRIEVAL_CASES:
            results = retriever.retrieve(case["query"], k=4)
            expected = ALL_CORPUS_TEXTS[case["expected_top1_index"]]

            rr = 0.0
            for rank, result in enumerate(results, 1):
                if result.document.content == expected:
                    rr = 1.0 / rank
                    break
            reciprocal_ranks.append(rr)

        mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
        assert mrr >= 0.8, f"MRR {mrr:.2f} below threshold 0.8"


class TestRetrievalProperties:
    """Validate structural properties of retrieval results."""

    def test_scores_monotonically_decreasing(self, indexed_orchestrator):
        """Retrieved results should be sorted by score descending."""
        retriever = indexed_orchestrator.get_component("retriever")
        results = retriever.retrieve("What is RISC-V?", k=4)

        scores = [r.score for r in results]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], f"Scores not monotonic: {scores}"

    def test_result_count_bounded_by_k(self, indexed_orchestrator):
        """Should never return more results than k."""
        retriever = indexed_orchestrator.get_component("retriever")

        for k in (1, 2, 4):
            results = retriever.retrieve("RISC-V architecture", k=k)
            assert len(results) <= k, f"Got {len(results)} results for k={k}"

    def test_all_scores_non_negative(self, indexed_orchestrator):
        """All retrieval scores should be >= 0."""
        retriever = indexed_orchestrator.get_component("retriever")
        results = retriever.retrieve("instruction set extensions", k=4)

        for result in results:
            assert result.score >= 0, f"Negative score: {result.score}"

    def test_retrieval_determinism(self, indexed_orchestrator):
        """Same query should produce identical results across runs."""
        retriever = indexed_orchestrator.get_component("retriever")
        query = "What is RISC-V?"

        results_a = retriever.retrieve(query, k=3)
        results_b = retriever.retrieve(query, k=3)
        results_c = retriever.retrieve(query, k=3)

        for run_label, other in [("B", results_b), ("C", results_c)]:
            assert len(results_a) == len(other), f"Run {run_label} different count"
            for i, (a, o) in enumerate(zip(results_a, other)):
                assert a.document.content == o.document.content, (
                    f"Run {run_label} rank {i} content differs"
                )
                assert abs(a.score - o.score) < 1e-6, (
                    f"Run {run_label} rank {i} score differs: {a.score} vs {o.score}"
                )

    def test_off_topic_ranks_below_on_topic(self, indexed_orchestrator):
        """Off-topic weather doc should rank below RISC-V docs for RISC-V queries."""
        retriever = indexed_orchestrator.get_component("retriever")
        results = retriever.retrieve("What is RISC-V?", k=4)

        contents = [r.document.content for r in results]
        weather_text = ALL_CORPUS_TEXTS[3]  # OFF_TOPIC_WEATHER

        if weather_text in contents:
            weather_rank = contents.index(weather_text)
            assert weather_rank == len(results) - 1, (
                f"Off-topic doc at rank {weather_rank}, expected last"
            )
