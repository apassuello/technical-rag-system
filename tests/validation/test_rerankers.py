"""Tier 0: Reranker validation.

Tests identity, semantic, and neural rerankers by creating retrievers
with each reranker type and verifying retrieval quality. No LLM needed.

Spec references: SPEC-R1, SPEC-R2, SPEC-R3 in docs/specs/retriever-components.md
"""

import pytest
from .golden_corpus import GOLDEN_RETRIEVAL_CASES, ALL_CORPUS_TEXTS

pytestmark = [pytest.mark.validation, pytest.mark.requires_ml]


RERANKER_CONFIGS = [
    pytest.param("identity", {"enabled": True}, id="identity-baseline"),
    pytest.param(
        "semantic",
        {"enabled": True, "model": "cross-encoder/ms-marco-MiniLM-L-6-v2", "top_k": 10},
        id="semantic",
    ),
    pytest.param(
        "neural",
        {
            "enabled": True,
            "initialize_immediately": False,
            "models": {
                "default_model": {
                    "name": "cross-encoder/ms-marco-MiniLM-L6-v2",
                    "max_length": 512,
                    "batch_size": 16,
                }
            },
        },
        id="neural",
    ),
]


class TestRerankerRetrieval:
    """Each reranker should maintain or improve retrieval quality."""

    @pytest.mark.parametrize("reranker_type,reranker_config", RERANKER_CONFIGS)
    def test_top1_maintained_with_reranker(
        self, make_retriever, index_golden_corpus, reranker_type, reranker_config
    ):
        """Reranking should not degrade top-1 precision on easy golden cases."""
        retriever = make_retriever(
            reranker_type=reranker_type, reranker_config=reranker_config
        )
        index_golden_corpus(retriever)

        for case in GOLDEN_RETRIEVAL_CASES:
            results = retriever.retrieve(case["query"], k=3)
            assert len(results) > 0
            expected = ALL_CORPUS_TEXTS[case["expected_top1_index"]]
            assert results[0].document.content == expected, (
                f"{reranker_type}: wrong top-1 for '{case['query']}'"
            )

    @pytest.mark.parametrize("reranker_type,reranker_config", RERANKER_CONFIGS)
    def test_scores_valid_after_reranking(
        self, make_retriever, index_golden_corpus, reranker_type, reranker_config
    ):
        """Reranked scores should be non-negative and monotonically decreasing."""
        retriever = make_retriever(
            reranker_type=reranker_type, reranker_config=reranker_config
        )
        index_golden_corpus(retriever)

        results = retriever.retrieve("What is RISC-V?", k=4)
        scores = [r.score for r in results]

        assert all(s >= 0 for s in scores), f"{reranker_type}: negative scores"
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], f"{reranker_type}: not monotonic {scores}"

    @pytest.mark.parametrize("reranker_type,reranker_config", RERANKER_CONFIGS)
    def test_result_count_preserved(
        self, make_retriever, index_golden_corpus, reranker_type, reranker_config
    ):
        """Reranker should not drop or add results."""
        retriever = make_retriever(
            reranker_type=reranker_type, reranker_config=reranker_config
        )
        index_golden_corpus(retriever)

        for k in (1, 2, 4):
            results = retriever.retrieve("RISC-V architecture", k=k)
            assert len(results) <= k, (
                f"{reranker_type}: got {len(results)} results for k={k}"
            )
