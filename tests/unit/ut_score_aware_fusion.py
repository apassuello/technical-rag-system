"""
ScoreAwareFusion tests for absolute score preservation.

Verifies that ScoreAwareFusion passes through input scores without
per-query min-max normalization — the 'score-aware' in the name means
it preserves score magnitude.
"""
import pytest
from src.components.retrievers.fusion.score_aware_fusion import ScoreAwareFusion


class TestScoreAwareFusionAbsoluteScores:
    """Test that ScoreAwareFusion preserves absolute score semantics."""

    def setup_method(self):
        self.fusion = ScoreAwareFusion({
            "score_weight": 0.8,
            "rank_weight": 0.15,
            "overlap_weight": 0.05,
            "k": 10,
        })

    def test_tight_cluster_not_amplified(self):
        """Dense scores [0.82, 0.80, 0.79] should NOT become [1.0, 0.33, 0.0].

        Per-query min-max amplifies tiny differences. Absolute mode should
        produce fused scores that preserve the tight spread.
        """
        dense = [(0, 0.82), (1, 0.80), (2, 0.79)]
        sparse = [(0, 0.50), (1, 0.45)]  # both dense+sparse needed to trigger fusion
        fused = self.fusion.fuse_results(dense, sparse)
        scores = {idx: s for idx, s in fused}

        # Dense docs (0,1,2) should have tight output spread, not amplified by min-max
        dense_fused = [scores[i] for i in [0, 1, 2] if i in scores]
        spread = max(dense_fused) - min(dense_fused)
        assert spread < 0.10, (
            f"Tight input cluster should produce tight output. Got spread={spread:.3f}. "
            f"Scores: {scores}. If spread is ~0.4+, min-max normalization is still active."
        )

    def test_low_scores_stay_low(self):
        """If all dense scores are low (0.3, 0.25, 0.20), output should be low too.

        With min-max, 0.3 would become 1.0. With absolute mode, it stays ~0.24.
        """
        dense = [(0, 0.30), (1, 0.25), (2, 0.20)]
        sparse = [(0, 0.15), (1, 0.10)]  # both needed to trigger fusion
        fused = self.fusion.fuse_results(dense, sparse)
        top_score = fused[0][1]

        assert top_score < 0.5, (
            f"Low input scores should produce low output. Got {top_score:.3f}. "
            "If this is ~0.8+, min-max normalization is still active."
        )

    def test_normalize_scores_param_ignored(self):
        """The normalize_scores config param should be gone / ignored.

        Creating a fusion with normalize_scores=True should not change behavior.
        """
        fusion_with_param = ScoreAwareFusion({
            "score_weight": 0.8,
            "rank_weight": 0.15,
            "overlap_weight": 0.05,
            "k": 10,
            "normalize_scores": True,  # should be ignored
        })
        dense = [(0, 0.82), (1, 0.80), (2, 0.79)]
        sparse = []
        result_with = fusion_with_param.fuse_results(dense, sparse)
        result_without = self.fusion.fuse_results(dense, sparse)

        # Results should be identical — normalize_scores has no effect
        for (idx1, s1), (idx2, s2) in zip(result_with, result_without):
            assert idx1 == idx2
            assert abs(s1 - s2) < 1e-6, "normalize_scores param should have no effect"

    def test_overlap_bonus_adds_correctly(self):
        """Documents in both lists get gamma * 1.0 added."""
        dense = [(0, 0.80), (1, 0.70)]
        sparse = [(0, 0.60), (2, 0.50)]
        fused = self.fusion.fuse_results(dense, sparse)
        scores = {idx: s for idx, s in fused}

        # Doc 0 is in both lists → gets overlap bonus
        # Doc 1 is dense-only, doc 2 is sparse-only → no overlap bonus
        assert scores[0] > scores[1], "Overlapping doc should score higher"

    def test_empty_inputs(self):
        """Empty input lists handled gracefully."""
        assert self.fusion.fuse_results([], []) == []
        dense = [(0, 0.5)]
        assert self.fusion.fuse_results(dense, []) == dense
        assert self.fusion.fuse_results([], dense) == dense

    def test_k_parameter_affects_rank_boost(self):
        """Smaller k gives more rank discrimination."""
        fusion_k10 = ScoreAwareFusion({"score_weight": 0.0, "rank_weight": 1.0, "overlap_weight": 0.0, "k": 10})
        fusion_k60 = ScoreAwareFusion({"score_weight": 0.0, "rank_weight": 1.0, "overlap_weight": 0.0, "k": 60})

        dense = [(0, 0.9), (1, 0.8), (2, 0.7), (3, 0.6), (4, 0.5)]
        sparse = [(0, 0.5), (1, 0.4)]  # both needed to trigger fusion

        scores_k10 = [s for _, s in fusion_k10.fuse_results(dense, sparse)]
        scores_k60 = [s for _, s in fusion_k60.fuse_results(dense, sparse)]

        spread_k10 = scores_k10[0] - scores_k10[-1]
        spread_k60 = scores_k60[0] - scores_k60[-1]

        assert spread_k10 > spread_k60, "k=10 should give more rank discrimination than k=60"
