"""Unit tests for WeightedFusion score-based fusion strategy.

Covers constructor validation, score normalization, result fusion,
weight updates, normalization toggle, strategy info, individual
score breakdown, and score statistics.
"""

import pytest

from components.retrievers.fusion.weighted_fusion import WeightedFusion


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def default_fusion():
    """WeightedFusion with default 0.7/0.3 weights, normalize=True."""
    return WeightedFusion({"weights": {"dense": 0.7, "sparse": 0.3}, "normalize": True})


@pytest.fixture
def unnormalized_fusion():
    """WeightedFusion with normalize=False."""
    return WeightedFusion({"weights": {"dense": 0.6, "sparse": 0.4}, "normalize": False})


@pytest.fixture
def dense_results():
    return [(0, 0.95), (1, 0.80), (2, 0.60)]


@pytest.fixture
def sparse_results():
    return [(1, 0.90), (2, 0.70), (3, 0.50)]


# ---------------------------------------------------------------------------
# TestInit — constructor defaults, normalisation, validation
# ---------------------------------------------------------------------------


class TestInit:
    """Constructor validation and weight auto-normalization."""

    def test_default_weights_when_no_weights_key(self):
        """Missing 'weights' key should fall back to dense=0.7, sparse=0.3."""
        wf = WeightedFusion({})
        assert wf.dense_weight == pytest.approx(0.7)
        assert wf.sparse_weight == pytest.approx(0.3)

    def test_custom_weights_summing_to_one(self):
        """Weights that already sum to 1 should be kept as-is."""
        wf = WeightedFusion({"weights": {"dense": 0.5, "sparse": 0.5}})
        assert wf.dense_weight == pytest.approx(0.5)
        assert wf.sparse_weight == pytest.approx(0.5)

    def test_weight_normalization_when_sum_not_one(self):
        """Weights that don't sum to 1 should be re-normalized."""
        wf = WeightedFusion({"weights": {"dense": 0.8, "sparse": 0.6}})
        assert wf.dense_weight == pytest.approx(0.8 / 1.4)
        assert wf.sparse_weight == pytest.approx(0.6 / 1.4)
        assert wf.dense_weight + wf.sparse_weight == pytest.approx(1.0)

    def test_both_weights_zero_falls_back_to_defaults(self):
        """Both weights=0 should trigger fallback to 0.7/0.3."""
        wf = WeightedFusion({"weights": {"dense": 0.0, "sparse": 0.0}})
        assert wf.dense_weight == pytest.approx(0.7)
        assert wf.sparse_weight == pytest.approx(0.3)

    def test_dense_weight_over_one_raises(self):
        with pytest.raises(ValueError, match="dense_weight must be between 0 and 1"):
            WeightedFusion({"weights": {"dense": 1.5, "sparse": 0.3}})

    def test_dense_weight_negative_raises(self):
        with pytest.raises(ValueError, match="dense_weight must be between 0 and 1"):
            WeightedFusion({"weights": {"dense": -0.1, "sparse": 0.3}})

    def test_sparse_weight_over_one_raises(self):
        with pytest.raises(ValueError, match="sparse_weight must be between 0 and 1"):
            WeightedFusion({"weights": {"dense": 0.7, "sparse": 1.5}})

    def test_sparse_weight_negative_raises(self):
        with pytest.raises(ValueError, match="sparse_weight must be between 0 and 1"):
            WeightedFusion({"weights": {"dense": 0.7, "sparse": -0.1}})

    def test_normalize_default_true(self):
        wf = WeightedFusion({})
        assert wf.normalize is True

    def test_normalize_explicit_false(self):
        wf = WeightedFusion({"normalize": False})
        assert wf.normalize is False

    def test_config_stored(self):
        cfg = {"weights": {"dense": 0.5, "sparse": 0.5}, "normalize": False}
        wf = WeightedFusion(cfg)
        assert wf.config is cfg


# ---------------------------------------------------------------------------
# TestNormalizeScores — _normalize_scores edge cases
# ---------------------------------------------------------------------------


class TestNormalizeScores:
    """Edge cases for the private _normalize_scores method."""

    def test_empty_list(self, default_fusion):
        assert default_fusion._normalize_scores([]) == []

    def test_single_result_range_zero(self, default_fusion):
        """Single result has zero range; should return as-is."""
        result = default_fusion._normalize_scores([(0, 0.5)])
        assert result == [(0, 0.5)]

    def test_equal_scores_returned_unchanged(self, default_fusion):
        """All equal scores produce zero range; returned unchanged."""
        data = [(0, 0.7), (1, 0.7), (2, 0.7)]
        assert default_fusion._normalize_scores(data) == data

    def test_normal_range_maps_to_zero_one(self, default_fusion):
        """Scores spanning a range should be mapped to [0, 1]."""
        data = [(0, 0.2), (1, 0.6), (2, 1.0)]
        normalized = default_fusion._normalize_scores(data)
        scores_by_id = dict(normalized)
        assert scores_by_id[0] == pytest.approx(0.0)   # min -> 0
        assert scores_by_id[1] == pytest.approx(0.5)   # mid -> 0.5
        assert scores_by_id[2] == pytest.approx(1.0)   # max -> 1

    def test_two_results_normalize_to_zero_and_one(self, default_fusion):
        data = [(5, 3.0), (10, 7.0)]
        normalized = default_fusion._normalize_scores(data)
        scores_by_id = dict(normalized)
        assert scores_by_id[5] == pytest.approx(0.0)
        assert scores_by_id[10] == pytest.approx(1.0)

    def test_preserves_document_ids(self, default_fusion):
        data = [(42, 0.1), (99, 0.9)]
        normalized = default_fusion._normalize_scores(data)
        ids = {doc_id for doc_id, _ in normalized}
        assert ids == {42, 99}

    def test_negative_scores(self, default_fusion):
        """Negative score range should still normalize correctly."""
        data = [(0, -10.0), (1, -5.0), (2, 0.0)]
        normalized = default_fusion._normalize_scores(data)
        scores_by_id = dict(normalized)
        assert scores_by_id[0] == pytest.approx(0.0)
        assert scores_by_id[2] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# TestFuseResults — core fusion logic
# ---------------------------------------------------------------------------


class TestFuseResults:
    """Core fusion logic with various input combinations."""

    def test_both_empty(self, default_fusion):
        assert default_fusion.fuse_results([], []) == []

    def test_dense_only_returns_copy(self, default_fusion, dense_results):
        result = default_fusion.fuse_results(dense_results, [])
        assert result == dense_results
        assert result is not dense_results

    def test_sparse_only_returns_copy(self, default_fusion, sparse_results):
        result = default_fusion.fuse_results([], sparse_results)
        assert result == sparse_results
        assert result is not sparse_results

    def test_all_doc_ids_present(self, default_fusion, dense_results, sparse_results):
        """All doc ids from both sources should appear in output."""
        result = default_fusion.fuse_results(dense_results, sparse_results)
        result_ids = {doc_id for doc_id, _ in result}
        assert result_ids == {0, 1, 2, 3}

    def test_results_sorted_descending(self, default_fusion, dense_results, sparse_results):
        result = default_fusion.fuse_results(dense_results, sparse_results)
        scores = [s for _, s in result]
        assert scores == sorted(scores, reverse=True)

    def test_output_is_list_of_tuples(self, default_fusion, dense_results, sparse_results):
        result = default_fusion.fuse_results(dense_results, sparse_results)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_deterministic(self, default_fusion, dense_results, sparse_results):
        r1 = default_fusion.fuse_results(dense_results, sparse_results)
        r2 = default_fusion.fuse_results(dense_results, sparse_results)
        assert r1 == r2

    def test_overlapping_docs_weighted_correctly(self):
        """Documents in both lists get weighted combination after normalization."""
        wf = WeightedFusion({"weights": {"dense": 0.7, "sparse": 0.3}})
        dense = [(0, 1.0), (1, 0.5)]
        sparse = [(0, 0.5), (1, 1.0)]
        results = wf.fuse_results(dense, sparse)
        scores = dict(results)
        # After normalisation: dense[0]=1.0, dense[1]=0.0; sparse[0]=0.0, sparse[1]=1.0
        # final[0] = 0.7*1.0 + 0.3*0.0 = 0.7
        # final[1] = 0.7*0.0 + 0.3*1.0 = 0.3
        assert scores[0] == pytest.approx(0.7)
        assert scores[1] == pytest.approx(0.3)

    def test_exact_score_no_normalize(self):
        """Verify exact weighted-sum calculation with normalize=False."""
        wf = WeightedFusion({"weights": {"dense": 0.6, "sparse": 0.4}, "normalize": False})
        dense = [(0, 0.8)]
        sparse = [(0, 0.5)]
        result = wf.fuse_results(dense, sparse)
        expected = wf.dense_weight * 0.8 + wf.sparse_weight * 0.5
        assert result[0][1] == pytest.approx(expected)

    def test_disjoint_docs_no_normalize(self):
        """Doc in only one list gets zero for the other source."""
        wf = WeightedFusion({"weights": {"dense": 0.6, "sparse": 0.4}, "normalize": False})
        dense = [(0, 1.0)]
        sparse = [(1, 1.0)]
        result = wf.fuse_results(dense, sparse)
        scores = dict(result)
        assert scores[0] == pytest.approx(wf.dense_weight * 1.0)
        assert scores[1] == pytest.approx(wf.sparse_weight * 1.0)

    def test_normalize_flag_affects_output(self):
        """Toggling normalize should change fused scores."""
        dense = [(0, 10.0), (1, 5.0)]
        sparse = [(0, 20.0), (1, 15.0)]
        wf_norm = WeightedFusion({"weights": {"dense": 0.5, "sparse": 0.5}, "normalize": True})
        wf_raw = WeightedFusion({"weights": {"dense": 0.5, "sparse": 0.5}, "normalize": False})
        r_norm = dict(wf_norm.fuse_results(dense, sparse))
        r_raw = dict(wf_raw.fuse_results(dense, sparse))
        # Raw scores can exceed 1.0; normalized cannot
        assert r_raw[0] > 1.0
        assert r_norm[0] <= 1.0


# ---------------------------------------------------------------------------
# TestUpdateWeights — dynamic weight changes
# ---------------------------------------------------------------------------


class TestUpdateWeights:

    def test_valid_update(self, default_fusion):
        default_fusion.update_weights(0.4, 0.6)
        assert default_fusion.dense_weight == pytest.approx(0.4)
        assert default_fusion.sparse_weight == pytest.approx(0.6)

    def test_normalization_on_update(self, default_fusion):
        default_fusion.update_weights(0.8, 0.4)
        assert default_fusion.dense_weight + default_fusion.sparse_weight == pytest.approx(1.0)
        assert default_fusion.dense_weight == pytest.approx(0.8 / 1.2)

    def test_negative_dense_raises(self, default_fusion):
        with pytest.raises(ValueError, match="dense_weight must be between 0 and 1"):
            default_fusion.update_weights(-0.1, 0.5)

    def test_over_one_dense_raises(self, default_fusion):
        with pytest.raises(ValueError, match="dense_weight must be between 0 and 1"):
            default_fusion.update_weights(1.1, 0.5)

    def test_negative_sparse_raises(self, default_fusion):
        with pytest.raises(ValueError, match="sparse_weight must be between 0 and 1"):
            default_fusion.update_weights(0.5, -0.2)

    def test_over_one_sparse_raises(self, default_fusion):
        with pytest.raises(ValueError, match="sparse_weight must be between 0 and 1"):
            default_fusion.update_weights(0.5, 1.5)

    def test_both_zero_raises(self, default_fusion):
        with pytest.raises(ValueError, match="At least one weight must be positive"):
            default_fusion.update_weights(0.0, 0.0)

    def test_one_zero_one_positive(self, default_fusion):
        """One weight at zero is valid; the positive one normalizes to 1.0."""
        default_fusion.update_weights(0.0, 0.6)
        assert default_fusion.dense_weight == pytest.approx(0.0)
        assert default_fusion.sparse_weight == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# TestSetNormalize — simple toggle
# ---------------------------------------------------------------------------


class TestSetNormalize:

    def test_toggle_off(self, default_fusion):
        assert default_fusion.normalize is True
        default_fusion.set_normalize(False)
        assert default_fusion.normalize is False

    def test_toggle_on(self, unnormalized_fusion):
        assert unnormalized_fusion.normalize is False
        unnormalized_fusion.set_normalize(True)
        assert unnormalized_fusion.normalize is True

    def test_idempotent(self, default_fusion):
        default_fusion.set_normalize(True)
        assert default_fusion.normalize is True


# ---------------------------------------------------------------------------
# TestStrategyInfo — returned dict shape and values
# ---------------------------------------------------------------------------


class TestStrategyInfo:

    def test_returns_dict(self, default_fusion):
        info = default_fusion.get_strategy_info()
        assert isinstance(info, dict)

    def test_expected_keys(self, default_fusion):
        info = default_fusion.get_strategy_info()
        assert info["algorithm"] == "weighted_score_fusion"
        assert "dense_weight" in info
        assert "sparse_weight" in info
        assert "normalize" in info
        assert "parameters" in info

    def test_parameters_sub_dict(self, default_fusion):
        info = default_fusion.get_strategy_info()
        params = info["parameters"]
        assert params["weights"]["dense"] == default_fusion.dense_weight
        assert params["weights"]["sparse"] == default_fusion.sparse_weight
        assert params["normalize"] == default_fusion.normalize

    def test_reflects_updated_weights(self, default_fusion):
        default_fusion.update_weights(0.3, 0.7)
        info = default_fusion.get_strategy_info()
        assert info["dense_weight"] == pytest.approx(0.3)
        assert info["sparse_weight"] == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# TestCalculateIndividualScores — debug breakdown
# ---------------------------------------------------------------------------


class TestCalculateIndividualScores:

    def test_all_docs_present(self, default_fusion, dense_results, sparse_results):
        scores = default_fusion.calculate_individual_scores(dense_results, sparse_results)
        assert set(scores.keys()) == {0, 1, 2, 3}

    def test_score_components_structure(self, default_fusion, dense_results, sparse_results):
        scores = default_fusion.calculate_individual_scores(dense_results, sparse_results)
        for doc_id, components in scores.items():
            for key in ("dense", "sparse", "weighted_dense", "weighted_sparse", "total"):
                assert key in components
            assert components["total"] == pytest.approx(
                components["weighted_dense"] + components["weighted_sparse"]
            )

    def test_weighted_values_match_weights(self, default_fusion):
        """weighted_dense == dense_weight * normalized_dense_score."""
        dense = [(0, 1.0)]
        sparse = [(0, 0.5)]
        scores = default_fusion.calculate_individual_scores(dense, sparse)
        # single item normalization: range=0 so returned as-is
        assert scores[0]["weighted_dense"] == pytest.approx(default_fusion.dense_weight * 1.0)
        assert scores[0]["weighted_sparse"] == pytest.approx(default_fusion.sparse_weight * 0.5)

    def test_missing_doc_gets_zero(self, unnormalized_fusion):
        """Doc only in dense should have sparse=0."""
        dense = [(0, 0.8)]
        sparse = [(1, 0.6)]
        scores = unnormalized_fusion.calculate_individual_scores(dense, sparse)
        assert scores[0]["sparse"] == pytest.approx(0.0)
        assert scores[1]["dense"] == pytest.approx(0.0)

    def test_respects_normalize_flag(self):
        dense = [(0, 2.0), (1, 4.0)]
        sparse = [(0, 10.0), (1, 20.0)]
        wf_norm = WeightedFusion({"weights": {"dense": 0.5, "sparse": 0.5}, "normalize": True})
        wf_raw = WeightedFusion({"weights": {"dense": 0.5, "sparse": 0.5}, "normalize": False})
        s_norm = wf_norm.calculate_individual_scores(dense, sparse)
        s_raw = wf_raw.calculate_individual_scores(dense, sparse)
        # Raw dense score for doc 1 should be 4.0; normalized should be 1.0
        assert s_raw[1]["dense"] == pytest.approx(4.0)
        assert s_norm[1]["dense"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# TestGetScoreStatistics — statistics dict
# ---------------------------------------------------------------------------


class TestGetScoreStatistics:

    def test_both_sources(self, default_fusion, dense_results, sparse_results):
        stats = default_fusion.get_score_statistics(dense_results, sparse_results)
        assert "dense" in stats
        assert "sparse" in stats
        for key in ("min", "max", "mean", "count"):
            assert key in stats["dense"]
            assert key in stats["sparse"]

    def test_dense_stats_correct(self, default_fusion):
        dense = [(0, 0.2), (1, 0.4), (2, 0.6)]
        stats = default_fusion.get_score_statistics(dense, [])
        assert "dense" in stats
        assert "sparse" not in stats
        assert stats["dense"]["min"] == pytest.approx(0.2)
        assert stats["dense"]["max"] == pytest.approx(0.6)
        assert stats["dense"]["mean"] == pytest.approx(0.4)
        assert stats["dense"]["count"] == 3

    def test_sparse_stats_correct(self, default_fusion):
        sparse = [(0, 1.0), (1, 3.0)]
        stats = default_fusion.get_score_statistics([], sparse)
        assert "sparse" in stats
        assert "dense" not in stats
        assert stats["sparse"]["min"] == pytest.approx(1.0)
        assert stats["sparse"]["max"] == pytest.approx(3.0)
        assert stats["sparse"]["mean"] == pytest.approx(2.0)
        assert stats["sparse"]["count"] == 2

    def test_both_empty(self, default_fusion):
        stats = default_fusion.get_score_statistics([], [])
        assert stats == {}

    def test_single_element(self, default_fusion):
        stats = default_fusion.get_score_statistics([(0, 0.5)], [])
        assert stats["dense"]["min"] == stats["dense"]["max"] == stats["dense"]["mean"]
        assert stats["dense"]["count"] == 1
