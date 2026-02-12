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
