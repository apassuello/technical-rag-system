"""Unit tests for WeaviateBackend v4 API migration.

These tests mock the weaviate client to verify v4 API calls
without requiring a running Weaviate server.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import numpy as np

from components.retrievers.backends.weaviate_config import (
    WeaviateBackendConfig,
    WeaviateConnectionConfig,
)

pytestmark = [pytest.mark.unit]


def _make_backend(mock_connect):
    """Create a WeaviateBackend with mocked connection.

    Bypasses __init__'s _connect() by patching weaviate.connect_to_custom
    to return a mock client that reports ready + empty collections.
    """
    mock_client = MagicMock()
    mock_client.is_ready.return_value = True
    mock_client.collections.list_all.return_value = {}
    # Make collections.create return None (success)
    mock_client.collections.create.return_value = None
    # Make collections.get return a mock collection
    mock_collection = MagicMock()
    mock_client.collections.get.return_value = mock_collection
    mock_connect.return_value = mock_client

    from components.retrievers.backends.weaviate_backend import WeaviateBackend

    config = WeaviateBackendConfig()
    backend = WeaviateBackend(config)
    return backend, mock_client, mock_collection


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendConnection:
    """Verify connect_to_custom() is called with correct args."""

    def test_connect_default_config(self, mock_weaviate_module):
        """Default config should connect to localhost:8080 with gRPC on 50051."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_client.collections.get.return_value = MagicMock()
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        config = WeaviateBackendConfig()
        backend = WeaviateBackend(config)

        call_kwargs = mock_weaviate_module.connect_to_custom.call_args
        assert call_kwargs.kwargs["http_host"] == "localhost"
        assert call_kwargs.kwargs["http_port"] == 8080
        assert call_kwargs.kwargs["http_secure"] is False
        assert call_kwargs.kwargs["grpc_host"] == "localhost"
        assert call_kwargs.kwargs["grpc_port"] == 50051
        assert call_kwargs.kwargs["grpc_secure"] is False
        assert backend.is_connected is True

    def test_connect_custom_url(self, mock_weaviate_module):
        """Custom URL should parse host/port correctly."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_client.collections.get.return_value = MagicMock()
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        config = WeaviateBackendConfig(
            connection=WeaviateConnectionConfig(
                url="https://weaviate.example.com:9090",
                grpc_port=50052,
            )
        )
        backend = WeaviateBackend(config)

        call_kwargs = mock_weaviate_module.connect_to_custom.call_args
        assert call_kwargs.kwargs["http_host"] == "weaviate.example.com"
        assert call_kwargs.kwargs["http_port"] == 9090
        assert call_kwargs.kwargs["http_secure"] is True
        assert call_kwargs.kwargs["grpc_port"] == 50052
        assert call_kwargs.kwargs["grpc_secure"] is True

    def test_connect_with_api_key(self, mock_weaviate_module):
        """API key should be passed as auth_credentials."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_client.collections.get.return_value = MagicMock()
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        config = WeaviateBackendConfig(
            connection=WeaviateConnectionConfig(api_key="test-key-123")
        )
        backend = WeaviateBackend(config)

        call_kwargs = mock_weaviate_module.connect_to_custom.call_args
        assert "auth_credentials" in call_kwargs.kwargs

    def test_connect_not_ready_raises(self, mock_weaviate_module):
        """Should raise WeaviateConnectionError if server not ready."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = False
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import (
            WeaviateBackend,
            WeaviateConnectionError,
        )

        config = WeaviateBackendConfig(max_retries=0)
        with pytest.raises(WeaviateConnectionError, match="not ready"):
            WeaviateBackend(config)


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendSchema:
    """Verify schema creation uses v4 collections API."""

    def test_schema_created_when_not_exists(self, mock_weaviate_module):
        """Should call collections.create() when class doesn't exist."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_collection = MagicMock()
        mock_client.collections.get.return_value = mock_collection
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        backend = WeaviateBackend(WeaviateBackendConfig())

        mock_client.collections.create.assert_called_once()
        create_kwargs = mock_client.collections.create.call_args
        assert create_kwargs.kwargs["name"] == "TechnicalDocument"
        assert backend.schema_created is True

    def test_schema_skipped_when_exists(self, mock_weaviate_module):
        """Should skip creation when class already exists."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {"TechnicalDocument": MagicMock()}
        mock_collection = MagicMock()
        mock_client.collections.get.return_value = mock_collection
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        backend = WeaviateBackend(WeaviateBackendConfig())

        mock_client.collections.create.assert_not_called()
        mock_client.collections.get.assert_called_with("TechnicalDocument")
        assert backend.schema_created is True


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendAddDocuments:
    """Verify batch.add_object() calls with v4 API."""

    def test_add_documents_uses_collection_batch(self, mock_weaviate_module):
        """Should use collection.batch.fixed_size() context manager."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_collection = MagicMock()
        mock_batch = MagicMock()
        mock_collection.batch.fixed_size.return_value.__enter__ = MagicMock(return_value=mock_batch)
        mock_collection.batch.fixed_size.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.collections.get.return_value = mock_collection
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend
        from src.core.interfaces import Document

        backend = WeaviateBackend(WeaviateBackendConfig())

        docs = [
            Document(
                content="Test document 1",
                metadata={"source": "test.pdf", "chunk_index": 0},
                embedding=[0.1] * 384,
            ),
            Document(
                content="Test document 2",
                metadata={"source": "test.pdf", "chunk_index": 1},
                embedding=[0.2] * 384,
            ),
        ]
        backend.add_documents(docs)

        mock_collection.batch.fixed_size.assert_called_once()
        assert mock_batch.add_object.call_count == 2

        # Verify first call properties
        first_call = mock_batch.add_object.call_args_list[0]
        assert first_call.kwargs["properties"]["content"] == "Test document 1"
        assert first_call.kwargs["properties"]["source_file"] == "test.pdf"
        assert first_call.kwargs["vector"] == [0.1] * 384

    def test_add_empty_raises(self, mock_weaviate_module):
        """Should raise ValueError for empty document list."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_client.collections.get.return_value = MagicMock()
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        backend = WeaviateBackend(WeaviateBackendConfig())
        with pytest.raises(RuntimeError, match="Cannot add empty"):
            backend.add_documents([])

    def test_add_missing_embedding_raises(self, mock_weaviate_module):
        """Should raise ValueError for doc without embedding."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_client.collections.get.return_value = MagicMock()
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend
        from src.core.interfaces import Document

        backend = WeaviateBackend(WeaviateBackendConfig())
        with pytest.raises(RuntimeError, match="missing embedding"):
            backend.add_documents([Document(content="no embedding", metadata={})])


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendSearch:
    """Verify search uses v4 collection query API."""

    def _make_search_backend(self, mock_weaviate_module):
        """Helper: create backend with mock collection for search tests."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_collection = MagicMock()
        mock_client.collections.get.return_value = mock_collection
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        backend = WeaviateBackend(WeaviateBackendConfig())
        return backend, mock_collection

    def test_hybrid_search(self, mock_weaviate_module):
        """Should call collection.query.hybrid() when query_text provided."""
        backend, mock_collection = self._make_search_backend(mock_weaviate_module)

        # Mock response
        mock_obj = MagicMock()
        mock_obj.metadata.score = 0.95
        mock_obj.metadata.certainty = None
        mock_obj.metadata.distance = None
        mock_obj.properties = {"chunk_index": 0}
        mock_response = MagicMock()
        mock_response.objects = [mock_obj]
        mock_collection.query.hybrid.return_value = mock_response

        query_vec = np.random.rand(384).astype(np.float32)
        results = backend.search(query_vec, k=5, query_text="test query")

        mock_collection.query.hybrid.assert_called_once()
        call_kwargs = mock_collection.query.hybrid.call_args.kwargs
        assert call_kwargs["query"] == "test query"
        assert call_kwargs["limit"] == 5
        assert len(results) == 1
        assert results[0] == (0, 0.95)

    def test_vector_search_without_text(self, mock_weaviate_module):
        """Should call collection.query.near_vector() without query_text."""
        backend, mock_collection = self._make_search_backend(mock_weaviate_module)

        mock_obj = MagicMock()
        mock_obj.metadata.score = None
        mock_obj.metadata.certainty = 0.85
        mock_obj.metadata.distance = None
        mock_obj.properties = {"chunk_index": 2}
        mock_response = MagicMock()
        mock_response.objects = [mock_obj]
        mock_collection.query.near_vector.return_value = mock_response

        query_vec = np.random.rand(384).astype(np.float32)
        results = backend.search(query_vec, k=3)

        mock_collection.query.near_vector.assert_called_once()
        call_kwargs = mock_collection.query.near_vector.call_args.kwargs
        assert call_kwargs["limit"] == 3
        assert results[0] == (2, 0.85)

    def test_search_distance_fallback(self, mock_weaviate_module):
        """Should convert distance to score when score/certainty not available."""
        backend, mock_collection = self._make_search_backend(mock_weaviate_module)

        mock_obj = MagicMock()
        mock_obj.metadata.score = None
        mock_obj.metadata.certainty = None
        mock_obj.metadata.distance = 0.5
        mock_obj.properties = {"chunk_index": 1}
        mock_response = MagicMock()
        mock_response.objects = [mock_obj]
        mock_collection.query.near_vector.return_value = mock_response

        query_vec = np.random.rand(384).astype(np.float32)
        results = backend.search(query_vec, k=5)

        expected_score = 1.0 / (1.0 + 0.5)
        assert abs(results[0][1] - expected_score) < 1e-6

    def test_search_invalid_k_raises(self, mock_weaviate_module):
        """Should raise RuntimeError for k <= 0."""
        backend, _ = self._make_search_backend(mock_weaviate_module)
        with pytest.raises(RuntimeError, match="k must be positive"):
            backend.search(np.zeros(384), k=0)


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendDocumentCount:
    """Verify document count uses v4 aggregate API."""

    def test_document_count(self, mock_weaviate_module):
        """Should call collection.aggregate.over_all(total_count=True)."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_collection = MagicMock()
        mock_aggregate_response = MagicMock()
        mock_aggregate_response.total_count = 42
        mock_collection.aggregate.over_all.return_value = mock_aggregate_response
        mock_client.collections.get.return_value = mock_collection
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        backend = WeaviateBackend(WeaviateBackendConfig())
        count = backend.get_document_count()

        mock_collection.aggregate.over_all.assert_called_once_with(total_count=True)
        assert count == 42

    def test_document_count_not_connected(self, mock_weaviate_module):
        """Should return 0 when not connected."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_client.collections.get.return_value = MagicMock()
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        backend = WeaviateBackend(WeaviateBackendConfig())
        backend.is_connected = False
        assert backend.get_document_count() == 0


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendClear:
    """Verify clear uses delete + recreate pattern."""

    def test_clear_deletes_and_recreates(self, mock_weaviate_module):
        """Should delete collection then recreate schema."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        # First list_all: empty (initial schema create)
        # Second list_all: empty (after clear, recreate)
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_collection = MagicMock()
        mock_client.collections.get.return_value = mock_collection
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        backend = WeaviateBackend(WeaviateBackendConfig())

        # Reset mocks after init
        mock_client.collections.delete.reset_mock()
        mock_client.collections.create.reset_mock()

        backend.clear()

        mock_client.collections.delete.assert_called_once_with("TechnicalDocument")
        mock_client.collections.create.assert_called_once()
        assert backend.schema_created is True


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendHealthCheck:
    """Verify health check uses v4 is_ready()."""

    def test_healthy_backend(self, mock_weaviate_module):
        """Connected backend with schema should report healthy."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_collection = MagicMock()
        mock_aggregate_response = MagicMock()
        mock_aggregate_response.total_count = 10
        mock_collection.aggregate.over_all.return_value = mock_aggregate_response
        mock_client.collections.get.return_value = mock_collection
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        backend = WeaviateBackend(WeaviateBackendConfig())
        health = backend.health_check()

        assert health["is_healthy"] is True
        assert health["is_connected"] is True
        assert health["schema_created"] is True

    def test_unhealthy_when_not_ready(self, mock_weaviate_module):
        """Should report unhealthy when server becomes not ready."""
        mock_client = MagicMock()
        # Ready during connect, not ready during health check
        mock_client.is_ready.side_effect = [True, False]
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_collection = MagicMock()
        mock_aggregate_response = MagicMock()
        mock_aggregate_response.total_count = 0
        mock_collection.aggregate.over_all.return_value = mock_aggregate_response
        mock_client.collections.get.return_value = mock_collection
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        backend = WeaviateBackend(WeaviateBackendConfig())
        health = backend.health_check()

        assert health["is_healthy"] is False
        assert "Weaviate server not ready" in health["issues"]


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendClose:
    """Verify close() method."""

    def test_close_disconnects(self, mock_weaviate_module):
        """close() should call client.close() and set is_connected=False."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_client.collections.get.return_value = MagicMock()
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        backend = WeaviateBackend(WeaviateBackendConfig())
        assert backend.is_connected is True

        backend.close()

        mock_client.close.assert_called_once()
        assert backend.is_connected is False

    def test_close_no_client(self, mock_weaviate_module):
        """close() should be safe when client is None."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_client.collections.get.return_value = MagicMock()
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        backend = WeaviateBackend(WeaviateBackendConfig())
        backend.client = None
        backend.close()  # Should not raise
        # is_connected unchanged since client was None
        assert backend.is_connected is True


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendInitializeIndex:
    """Verify initialize_index() validation and reconnect logic."""

    def test_initialize_index_connected(self, mock_weaviate_module):
        """Should succeed when already connected with schema."""
        backend, mock_client, mock_collection = _make_backend(mock_weaviate_module.connect_to_custom)
        backend.initialize_index(384)
        assert backend.stats["total_operations"] >= 1

    def test_initialize_index_reconnects(self, mock_weaviate_module):
        """Should reconnect if not connected."""
        backend, mock_client, mock_collection = _make_backend(mock_weaviate_module.connect_to_custom)
        backend.is_connected = False
        # _connect is called during init already; override so reconnect works
        backend.is_connected = False
        # The method calls _connect() which calls connect_to_custom again
        backend.initialize_index(384)
        # After reconnect through _connect, is_connected should be True
        assert backend.is_connected is True


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendIsTrained:
    """Verify is_trained() checks."""

    def test_is_trained_when_connected_and_schema(self, mock_weaviate_module):
        """Should return True when connected and schema created."""
        backend, _, _ = _make_backend(mock_weaviate_module.connect_to_custom)
        assert backend.is_trained() is True

    def test_is_trained_not_connected(self, mock_weaviate_module):
        """Should return False when not connected."""
        backend, _, _ = _make_backend(mock_weaviate_module.connect_to_custom)
        backend.is_connected = False
        assert backend.is_trained() is False

    def test_is_trained_no_schema(self, mock_weaviate_module):
        """Should return False when schema not created."""
        backend, _, _ = _make_backend(mock_weaviate_module.connect_to_custom)
        backend.schema_created = False
        assert backend.is_trained() is False


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendGetBackendInfo:
    """Verify get_backend_info() returns expected structure."""

    def test_get_backend_info_connected(self, mock_weaviate_module):
        """Should return full info when connected."""
        backend, mock_client, mock_collection = _make_backend(mock_weaviate_module.connect_to_custom)
        mock_client.get_meta.return_value = {"version": "1.28.0"}
        mock_aggregate = MagicMock()
        mock_aggregate.total_count = 5
        mock_collection.aggregate.over_all.return_value = mock_aggregate

        info = backend.get_backend_info()

        assert info["backend_type"] == "weaviate"
        assert info["backend_version"] == "v4-adapter"
        assert info["is_connected"] is True
        assert info["schema_created"] is True
        assert info["document_count"] == 5
        assert info["weaviate_meta"]["version"] == "1.28.0"

    def test_get_backend_info_meta_error(self, mock_weaviate_module):
        """Should handle get_meta() failure gracefully."""
        backend, mock_client, mock_collection = _make_backend(mock_weaviate_module.connect_to_custom)
        mock_client.get_meta.side_effect = Exception("meta unavailable")
        mock_aggregate = MagicMock()
        mock_aggregate.total_count = 0
        mock_collection.aggregate.over_all.return_value = mock_aggregate

        info = backend.get_backend_info()

        assert info["weaviate_meta"]["error"] == "Could not retrieve meta info"

    def test_get_backend_info_not_connected(self, mock_weaviate_module):
        """Should return empty meta when disconnected."""
        backend, mock_client, _ = _make_backend(mock_weaviate_module.connect_to_custom)
        backend.is_connected = False

        info = backend.get_backend_info()

        assert info["is_connected"] is False
        assert info["weaviate_meta"] == {}
        assert info["document_count"] == 0


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendGetConfiguration:
    """Verify get_configuration() return structure."""

    def test_get_configuration(self, mock_weaviate_module):
        """Should return backend_type and config dict."""
        backend, _, _ = _make_backend(mock_weaviate_module.connect_to_custom)
        config = backend.get_configuration()
        assert config["backend_type"] == "weaviate"
        assert "config" in config


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendCapabilities:
    """Verify capability flags."""

    def test_supports_hybrid_search(self, mock_weaviate_module):
        """Should always return True."""
        backend, _, _ = _make_backend(mock_weaviate_module.connect_to_custom)
        assert backend.supports_hybrid_search() is True

    def test_supports_filtering(self, mock_weaviate_module):
        """Should always return True."""
        backend, _, _ = _make_backend(mock_weaviate_module.connect_to_custom)
        assert backend.supports_filtering() is True


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendRetry:
    """Verify retry/backoff logic in _connect()."""

    def test_connect_retries_on_transient_error(self, mock_weaviate_module):
        """Should retry on non-WeaviateConnectionError exceptions."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_client.collections.get.return_value = MagicMock()

        # First call raises transient error, second call succeeds
        mock_weaviate_module.connect_to_custom.side_effect = [
            ConnectionError("transient failure"),
            mock_client,
        ]

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        config = WeaviateBackendConfig(max_retries=1, retry_delay_seconds=0.0)
        backend = WeaviateBackend(config)

        assert backend.is_connected is True
        assert mock_weaviate_module.connect_to_custom.call_count == 2
        assert backend.stats["connection_errors"] == 1

    def test_connect_exhausts_retries(self, mock_weaviate_module):
        """Should raise WeaviateConnectionError after exhausting retries."""
        mock_weaviate_module.connect_to_custom.side_effect = ConnectionError("down")

        from components.retrievers.backends.weaviate_backend import (
            WeaviateBackend,
            WeaviateConnectionError,
        )

        config = WeaviateBackendConfig(max_retries=1, retry_delay_seconds=0.0)
        with pytest.raises(WeaviateConnectionError, match="Failed to connect"):
            WeaviateBackend(config)

        # initial attempt + 1 retry = 2 calls
        assert mock_weaviate_module.connect_to_custom.call_count == 2


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendHealthCheckExtended:
    """Verify additional health_check branches."""

    def test_health_check_disconnected(self, mock_weaviate_module):
        """Should report unhealthy when is_connected=False."""
        backend, mock_client, _ = _make_backend(mock_weaviate_module.connect_to_custom)
        backend.is_connected = False

        health = backend.health_check()

        assert health["is_healthy"] is False
        assert "Not connected to Weaviate" in health["issues"]

    def test_health_check_schema_not_created(self, mock_weaviate_module):
        """Should flag schema_created=False as unhealthy."""
        backend, mock_client, mock_collection = _make_backend(mock_weaviate_module.connect_to_custom)
        backend.schema_created = False
        mock_client.is_ready.return_value = True
        mock_aggregate = MagicMock()
        mock_aggregate.total_count = 0
        mock_collection.aggregate.over_all.return_value = mock_aggregate

        health = backend.health_check()

        assert health["is_healthy"] is False
        assert "Schema not created" in health["issues"]

    def test_health_check_high_error_rate(self, mock_weaviate_module):
        """Should flag high error rate."""
        backend, mock_client, mock_collection = _make_backend(mock_weaviate_module.connect_to_custom)
        mock_client.is_ready.return_value = True
        mock_aggregate = MagicMock()
        mock_aggregate.total_count = 10
        mock_collection.aggregate.over_all.return_value = mock_aggregate

        # Simulate high error rate: 5 errors out of 10 ops
        backend.stats["error_count"] = 5
        backend.stats["total_operations"] = 10

        health = backend.health_check()

        assert health["is_healthy"] is False
        assert any("error rate" in i.lower() for i in health["issues"])

    def test_health_check_exception(self, mock_weaviate_module):
        """Should return fallback dict on exception."""
        backend, mock_client, _ = _make_backend(mock_weaviate_module.connect_to_custom)
        # Force is_ready to raise inside health_check
        mock_client.is_ready.side_effect = RuntimeError("boom")

        health = backend.health_check()

        assert health["is_healthy"] is False
        assert "boom" in health["error"]


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendSearchScoreFallback:
    """Verify search score fallback when no metadata scores available."""

    def test_search_no_score_metadata(self, mock_weaviate_module):
        """Should use positional fallback when no score/certainty/distance."""
        backend, mock_client, mock_collection = _make_backend(mock_weaviate_module.connect_to_custom)

        mock_obj1 = MagicMock()
        mock_obj1.metadata.score = None
        mock_obj1.metadata.certainty = None
        mock_obj1.metadata.distance = None
        mock_obj1.properties = {"chunk_index": 0}

        mock_obj2 = MagicMock()
        mock_obj2.metadata.score = None
        mock_obj2.metadata.certainty = None
        mock_obj2.metadata.distance = None
        mock_obj2.properties = {"chunk_index": 1}

        mock_response = MagicMock()
        mock_response.objects = [mock_obj1, mock_obj2]
        mock_collection.query.near_vector.return_value = mock_response

        query_vec = np.random.rand(384).astype(np.float32)
        results = backend.search(query_vec, k=5)

        assert len(results) == 2
        # Positional fallback: 1.0 - (i * 0.1)
        assert results[0] == (0, 1.0)
        assert results[1] == (1, 0.9)


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendClearNotConnected:
    """Verify clear() early return when disconnected."""

    def test_clear_when_disconnected(self, mock_weaviate_module):
        """Should return without error when not connected."""
        backend, mock_client, _ = _make_backend(mock_weaviate_module.connect_to_custom)
        backend.is_connected = False

        mock_client.collections.delete.reset_mock()
        backend.clear()  # Should not raise

        mock_client.collections.delete.assert_not_called()


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendDocumentCountException:
    """Verify get_document_count() exception path."""

    def test_document_count_exception_returns_zero(self, mock_weaviate_module):
        """Should return 0 on aggregate exception."""
        backend, _, mock_collection = _make_backend(mock_weaviate_module.connect_to_custom)
        mock_collection.aggregate.over_all.side_effect = RuntimeError("aggregate failed")

        count = backend.get_document_count()
        assert count == 0


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendTimestamps:
    """Verify timestamps are RFC3339-compliant (include timezone)."""

    def test_document_properties_use_rfc3339_timestamps(self, mock_weaviate_module):
        """Verify created_at timestamps include timezone for RFC3339 compliance."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_collection = MagicMock()
        mock_batch = MagicMock()
        mock_collection.batch.fixed_size.return_value.__enter__ = MagicMock(return_value=mock_batch)
        mock_collection.batch.fixed_size.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.collections.get.return_value = mock_collection
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend
        from src.core.interfaces import Document

        backend = WeaviateBackend(WeaviateBackendConfig())
        docs = [
            Document(
                content="Test document",
                metadata={"source": "test.pdf", "chunk_index": 0},
                embedding=[0.1] * 384,
            ),
        ]
        backend.add_documents(docs)

        props = mock_batch.add_object.call_args.kwargs["properties"]
        created_at = props["created_at"]
        assert "+" in created_at or "Z" in created_at, (
            f"created_at '{created_at}' lacks timezone suffix; not RFC3339 compliant"
        )


@patch("components.retrievers.backends.weaviate_backend.weaviate")
class TestWeaviateBackendDictConfig:
    """Verify WeaviateBackend accepts a dict config."""

    def test_dict_config_converted(self, mock_weaviate_module):
        """Should convert dict to WeaviateBackendConfig."""
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_client.collections.list_all.return_value = {}
        mock_client.collections.create.return_value = None
        mock_client.collections.get.return_value = MagicMock()
        mock_weaviate_module.connect_to_custom.return_value = mock_client

        from components.retrievers.backends.weaviate_backend import WeaviateBackend

        backend = WeaviateBackend({"connection": {"url": "http://localhost:8080"}})
        assert backend.is_connected is True
        assert isinstance(backend.config, WeaviateBackendConfig)


# ---------------------------------------------------------------------------
# Known bugs — xfail-documented
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    reason="WeaviateBackend uses weaviate-client v3 API; needs v3→v4 migration",
    strict=False,
)
@pytest.mark.requires_weaviate
def test_weaviate_backend_v4_native_api():
    """WeaviateBackend still uses v3 Client() constructor and query builder.

    The v4 client uses connect_to_local()/connect_to_custom() and a
    collections-based API. This test documents the migration gap.
    """
    import weaviate

    # v4 API: should use connect_to_local, not Client()
    assert hasattr(weaviate, "connect_to_local"), "weaviate-client v4 required"

    from components.retrievers.backends.weaviate_backend import WeaviateBackend

    # The backend's __init__ should not reference weaviate.Client (v3)
    import inspect

    source = inspect.getsource(WeaviateBackend.__init__)
    assert "weaviate.Client(" not in source, "Still using v3 weaviate.Client()"
