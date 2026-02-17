"""
Tests for NeuralReranker's internal ScoreFusion.

Verifies sigmoid normalization for cross-encoder logits and pass-through
for retrieval scores.
"""
import pytest
import math
from unittest.mock import MagicMock
from src.components.retrievers.rerankers.utils.score_fusion import (
    ScoreFusion, ScoreNormalizer, NormalizationConfig, WeightsConfig,
)
from src.core.interfaces import Document


class TestScoreNormalizerSigmoid:
    """Test sigmoid normalization for cross-encoder logits."""

    def test_sigmoid_maps_zero_to_half(self):
        normalizer = ScoreNormalizer(NormalizationConfig(method="sigmoid"))
        result = normalizer.normalize([0.0])
        assert abs(result[0] - 0.5) < 0.01, "sigmoid(0) should be ~0.5"

    def test_sigmoid_maps_positive_logit_high(self):
        normalizer = ScoreNormalizer(NormalizationConfig(method="sigmoid"))
        result = normalizer.normalize([3.0])
        assert result[0] > 0.9, "sigmoid(3) should be > 0.9"

    def test_sigmoid_maps_negative_logit_low(self):
        normalizer = ScoreNormalizer(NormalizationConfig(method="sigmoid"))
        result = normalizer.normalize([-3.0])
        assert result[0] < 0.1, "sigmoid(-3) should be < 0.1"

    def test_sigmoid_is_monotonic(self):
        normalizer = ScoreNormalizer(NormalizationConfig(method="sigmoid"))
        logits = [-5.0, -2.0, 0.0, 2.0, 5.0]
        result = normalizer.normalize(logits)
        assert result == sorted(result), "sigmoid should be monotonically increasing"

    def test_sigmoid_is_absolute_not_relative(self):
        """Same logit value should produce same output regardless of other values."""
        normalizer = ScoreNormalizer(NormalizationConfig(method="sigmoid"))
        batch1 = normalizer.normalize([2.0, 5.0, 8.0])
        batch2 = normalizer.normalize([2.0, -1.0, -5.0])
        # The score for logit=2.0 should be the same in both batches
        assert abs(batch1[0] - batch2[0]) < 0.01, (
            f"sigmoid(2.0) should be the same regardless of batch: {batch1[0]} vs {batch2[0]}"
        )


class TestScoreNormalizerNone:
    """Test pass-through normalization."""

    def test_none_returns_input_unchanged(self):
        normalizer = ScoreNormalizer(NormalizationConfig(method="none"))
        scores = [0.3, 0.5, 0.7]
        result = normalizer.normalize(scores)
        assert result == scores, "none normalization should return input unchanged"


class TestScoreFusionIntegration:
    """Test the full ScoreFusion pipeline with new defaults."""

    def test_default_normalization_is_sigmoid_for_neural(self):
        """Default ScoreFusion should use sigmoid, not min-max."""
        fusion = ScoreFusion(method="weighted")
        assert fusion.normalization.method == "sigmoid", (
            f"Default normalization should be sigmoid, got {fusion.normalization.method}"
        )

    def test_weighted_fusion_combines_absolute_scores(self):
        """Weighted fusion of pass-through retrieval + sigmoid neural."""
        fusion = ScoreFusion(
            method="weighted",
            weights=WeightsConfig(retrieval_score=0.3, neural_score=0.7),
            normalization=NormalizationConfig(method="sigmoid"),
        )
        docs = [MagicMock(spec=Document) for _ in range(3)]

        retrieval_scores = [0.6, 0.5, 0.4]  # Already absolute from ScoreAwareFusion
        neural_scores = [3.0, 1.0, -2.0]    # Raw cross-encoder logits

        fused = fusion.fuse_scores(retrieval_scores, neural_scores, "test query", docs)

        # sigmoid(3.0) ~ 0.953, sigmoid(1.0) ~ 0.731, sigmoid(-2.0) ~ 0.119
        # fused[0] = 0.3 * 0.6 + 0.7 * 0.953 ~ 0.847
        # fused[1] = 0.3 * 0.5 + 0.7 * 0.731 ~ 0.662
        # fused[2] = 0.3 * 0.4 + 0.7 * 0.119 ~ 0.203
        assert fused[0] > 0.7, f"Good retrieval + high logit should score high, got {fused[0]}"
        assert fused[2] < 0.4, f"Low retrieval + negative logit should score low, got {fused[2]}"
        assert fused[0] > fused[1] > fused[2], "Scores should preserve ordering"
