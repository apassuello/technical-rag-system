"""Unit tests for SemanticReranker.

SemanticReranker wraps a sentence-transformers CrossEncoder for
query-document relevance scoring. The model is lazy-loaded on first
rerank() call, and the reranker degrades gracefully when
sentence_transformers is unavailable.
"""

import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from src.core.interfaces import Document
from src.components.retrievers.rerankers.semantic_reranker import SemanticReranker


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def default_config():
    return {
        "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "enabled": True,
        "batch_size": 32,
        "top_k": 10,
        "score_threshold": 0.0,
    }


@pytest.fixture
def reranker(default_config):
    return SemanticReranker(default_config)


@pytest.fixture
def sample_docs():
    return [
        Document(content="CPU architecture and instruction sets", metadata={"id": "d1"}),
        Document(content="Memory management in operating systems", metadata={"id": "d2"}),
        Document(content="Network protocols and communication", metadata={"id": "d3"}),
    ]


@pytest.fixture
def mock_cross_encoder():
    """Return a MagicMock that behaves like CrossEncoder."""
    ce = MagicMock()
    # predict returns numpy array of scores
    ce.predict.return_value = np.array([0.9, 0.3, 0.7])
    ce.device = "cpu"
    return ce


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestSemanticRerankerInit:
    """Constructor and config parsing."""

    def test_defaults_from_config(self, reranker, default_config):
        assert reranker.model_name == default_config["model"]
        assert reranker.enabled is True
        assert reranker.batch_size == 32
        assert reranker.top_k == 10
        assert reranker.score_threshold == 0.0

    def test_model_not_loaded_at_init(self, reranker):
        assert reranker.model is None
        assert reranker._model_loaded is False

    def test_minimal_config_uses_defaults(self):
        r = SemanticReranker({})
        assert r.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert r.enabled is True
        assert r.batch_size == 32

    def test_invalid_batch_size_raises(self):
        with pytest.raises(ValueError, match="batch_size must be positive"):
            SemanticReranker({"batch_size": 0})

    def test_invalid_top_k_raises(self):
        with pytest.raises(ValueError, match="top_k must be positive"):
            SemanticReranker({"top_k": -1})


# ---------------------------------------------------------------------------
# Lazy model loading
# ---------------------------------------------------------------------------

class TestModelLoading:
    """_load_model() lazy-loads CrossEncoder from sentence_transformers."""

    def test_load_model_sets_model(self, reranker, mock_cross_encoder):
        mock_module = MagicMock()
        mock_module.CrossEncoder.return_value = mock_cross_encoder

        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            reranker._load_model()

        assert reranker._model_loaded is True
        assert reranker.model is mock_cross_encoder

    def test_load_model_called_once(self, reranker, mock_cross_encoder):
        mock_module = MagicMock()
        mock_module.CrossEncoder.return_value = mock_cross_encoder

        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            reranker._load_model()
            reranker._load_model()  # second call should be a no-op

        mock_module.CrossEncoder.assert_called_once()

    def test_load_model_skipped_when_disabled(self):
        r = SemanticReranker({"enabled": False})
        r._load_model()
        assert r._model_loaded is True
        assert r.model is None

    def test_import_error_disables_reranker(self, reranker):
        # Remove sentence_transformers from sys.modules so the import fails
        with patch.dict("sys.modules", {"sentence_transformers": None}):
            reranker._load_model()

        assert reranker.enabled is False
        assert reranker._model_loaded is True
        assert reranker.model is None

    def test_generic_model_error_disables_reranker(self, reranker):
        mock_module = MagicMock()
        mock_module.CrossEncoder.side_effect = RuntimeError("CUDA OOM")

        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            reranker._load_model()

        assert reranker.enabled is False
        assert reranker._model_loaded is True


# ---------------------------------------------------------------------------
# rerank()
# ---------------------------------------------------------------------------

class TestRerank:
    """rerank(query, documents, initial_scores) -> List[(idx, score)]."""

    def test_rerank_sorts_by_cross_encoder_score(
        self, reranker, sample_docs, mock_cross_encoder
    ):
        mock_module = MagicMock()
        mock_module.CrossEncoder.return_value = mock_cross_encoder
        # Scores: doc0=0.9, doc1=0.3, doc2=0.7
        mock_cross_encoder.predict.return_value = np.array([0.9, 0.3, 0.7])

        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            results = reranker.rerank("CPU query", sample_docs, [0.5, 0.5, 0.5])

        indices = [idx for idx, _ in results]
        assert indices == [0, 2, 1]  # descending by score 0.9, 0.7, 0.3

    def test_rerank_returns_float_scores(
        self, reranker, sample_docs, mock_cross_encoder
    ):
        mock_module = MagicMock()
        mock_module.CrossEncoder.return_value = mock_cross_encoder

        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            results = reranker.rerank("query", sample_docs, [0.5, 0.5, 0.5])

        for idx, score in results:
            assert isinstance(idx, int)
            assert isinstance(score, float)

    def test_rerank_empty_docs_returns_empty(self, reranker):
        results = reranker.rerank("query", [], [])
        assert results == []

    def test_rerank_blank_query_returns_empty(self, reranker, sample_docs):
        results = reranker.rerank("   ", sample_docs, [0.5, 0.5, 0.5])
        assert results == []

    def test_rerank_disabled_returns_original_order(self, sample_docs):
        r = SemanticReranker({"enabled": False})
        initial = [0.8, 0.6, 0.4]
        results = r.rerank("query", sample_docs, initial)

        assert results == [(0, 0.8), (1, 0.6), (2, 0.4)]

    def test_rerank_score_threshold_filters(
        self, sample_docs, mock_cross_encoder
    ):
        r = SemanticReranker({"enabled": True, "score_threshold": 0.5})
        mock_module = MagicMock()
        mock_module.CrossEncoder.return_value = mock_cross_encoder
        # doc0=0.9 (above), doc1=0.3 (below), doc2=0.7 (above)
        mock_cross_encoder.predict.return_value = np.array([0.9, 0.3, 0.7])

        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            results = r.rerank("query", sample_docs, [0.5, 0.5, 0.5])

        returned_indices = {idx for idx, _ in results}
        assert 1 not in returned_indices  # score 0.3 < threshold 0.5

    def test_rerank_top_k_limits_reranked_docs(self, mock_cross_encoder):
        docs = [
            Document(content=f"doc {i}", metadata={"id": str(i)})
            for i in range(5)
        ]
        initial = [0.5] * 5
        r = SemanticReranker({"enabled": True, "top_k": 2})

        mock_module = MagicMock()
        mock_module.CrossEncoder.return_value = mock_cross_encoder
        # Only 2 docs sent to cross-encoder
        mock_cross_encoder.predict.return_value = np.array([0.8, 0.6])

        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            results = r.rerank("query", docs, initial)

        # Should include all 5 docs (2 reranked + 3 passthrough)
        assert len(results) == 5

    def test_rerank_batching(self, mock_cross_encoder):
        docs = [
            Document(content=f"doc {i}", metadata={"id": str(i)})
            for i in range(4)
        ]
        initial = [0.5] * 4
        r = SemanticReranker({"enabled": True, "batch_size": 2, "top_k": 4})

        mock_module = MagicMock()
        mock_module.CrossEncoder.return_value = mock_cross_encoder
        # Two batches of 2
        mock_cross_encoder.predict.side_effect = [
            np.array([0.9, 0.7]),
            np.array([0.5, 0.3]),
        ]

        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            results = r.rerank("query", docs, initial)

        assert mock_cross_encoder.predict.call_count == 2
        assert len(results) == 4

    def test_rerank_truncates_long_documents(
        self, reranker, mock_cross_encoder
    ):
        long_doc = Document(
            content="x" * 3000,
            metadata={"id": "long"},
        )
        mock_module = MagicMock()
        mock_module.CrossEncoder.return_value = mock_cross_encoder
        mock_cross_encoder.predict.return_value = np.array([0.5])

        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            reranker.rerank("query", [long_doc], [0.5])

        # Check that the text passed to predict was truncated
        call_args = mock_cross_encoder.predict.call_args[0][0]
        doc_text = call_args[0][1]
        assert len(doc_text) <= 2004  # 2000 + len("...")

    def test_rerank_predict_error_fallback(
        self, reranker, sample_docs, mock_cross_encoder
    ):
        mock_module = MagicMock()
        mock_module.CrossEncoder.return_value = mock_cross_encoder
        mock_cross_encoder.predict.side_effect = RuntimeError("inference error")

        initial = [0.8, 0.6, 0.4]
        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            results = reranker.rerank("query", sample_docs, initial)

        # Falls back to original scores
        assert results == [(0, 0.8), (1, 0.6), (2, 0.4)]


# ---------------------------------------------------------------------------
# Enable / disable toggle
# ---------------------------------------------------------------------------

class TestEnableDisable:
    """enable(), disable(), is_enabled() state management."""

    def test_disable(self, reranker):
        reranker.disable()
        assert reranker.is_enabled() is False

    def test_enable(self):
        r = SemanticReranker({"enabled": False})
        r.enable()
        assert r.is_enabled() is True

    def test_toggle_round_trip(self, reranker):
        reranker.disable()
        assert reranker.is_enabled() is False
        reranker.enable()
        assert reranker.is_enabled() is True


# ---------------------------------------------------------------------------
# Utility methods
# ---------------------------------------------------------------------------

class TestUtilityMethods:
    """set_top_k, set_score_threshold, get_reranker_info, get_model_info, predict_scores."""

    def test_set_top_k(self, reranker):
        reranker.set_top_k(20)
        assert reranker.top_k == 20

    def test_set_top_k_invalid(self, reranker):
        with pytest.raises(ValueError, match="top_k must be positive"):
            reranker.set_top_k(0)

    def test_set_score_threshold(self, reranker):
        reranker.set_score_threshold(0.5)
        assert reranker.score_threshold == 0.5

    def test_get_reranker_info(self, reranker):
        info = reranker.get_reranker_info()
        assert info["model"] == reranker.model_name
        assert info["enabled"] is True
        assert info["batch_size"] == 32
        assert info["top_k"] == 10
        assert info["model_loaded"] is False

    def test_get_reranker_info_includes_device_when_loaded(
        self, reranker, mock_cross_encoder
    ):
        mock_module = MagicMock()
        mock_module.CrossEncoder.return_value = mock_cross_encoder

        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            reranker._load_model()

        info = reranker.get_reranker_info()
        assert "model_device" in info

    def test_get_model_info_not_loaded(self, reranker):
        info = reranker.get_model_info()
        assert info["status"] == "not_loaded"

    def test_get_model_info_loaded(self, reranker, mock_cross_encoder):
        mock_module = MagicMock()
        mock_module.CrossEncoder.return_value = mock_cross_encoder

        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            reranker._load_model()

        info = reranker.get_model_info()
        assert info["status"] == "loaded"
        assert info["model_name"] == reranker.model_name

    def test_predict_scores_disabled_returns_zeros(self, sample_docs):
        r = SemanticReranker({"enabled": False})
        scores = r.predict_scores("query", sample_docs)
        assert scores == [0.0, 0.0, 0.0]

    def test_predict_scores_with_model(
        self, reranker, sample_docs, mock_cross_encoder
    ):
        mock_module = MagicMock()
        mock_module.CrossEncoder.return_value = mock_cross_encoder
        mock_cross_encoder.predict.return_value = np.array([0.9, 0.7, 0.5])

        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            scores = reranker.predict_scores("query", sample_docs)

        assert len(scores) == 3
        assert all(isinstance(s, float) for s in scores)
        assert scores == [0.9, 0.7, 0.5]

    def test_predict_scores_error_returns_zeros(
        self, reranker, sample_docs, mock_cross_encoder
    ):
        mock_module = MagicMock()
        mock_module.CrossEncoder.return_value = mock_cross_encoder
        mock_cross_encoder.predict.side_effect = RuntimeError("fail")

        with patch.dict("sys.modules", {"sentence_transformers": mock_module}):
            scores = reranker.predict_scores("query", sample_docs)

        assert scores == [0.0, 0.0, 0.0]

    def test_get_component_info(self, reranker):
        info = reranker.get_component_info()
        assert info["type"] == "reranker"
        assert info["class"] == "SemanticReranker"
