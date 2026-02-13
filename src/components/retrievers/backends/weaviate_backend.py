"""
Weaviate backend adapter for advanced retriever.

This module provides an adapter for Weaviate vector database integration,
following the same pattern as other external service adapters in the system.
It handles Weaviate-specific operations, schema management, and hybrid search.

Uses weaviate-client v4 collection-based API.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import numpy as np

try:
    import weaviate
    from weaviate.classes.init import Auth, AdditionalConfig, Timeout
    from weaviate.classes.config import Property, DataType, Configure
    from weaviate.classes.query import MetadataQuery
    from weaviate.exceptions import WeaviateBaseError as WeaviateException
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False
    weaviate = None
    WeaviateException = Exception

from src.core.interfaces import Document

from .weaviate_config import WeaviateBackendConfig

logger = logging.getLogger(__name__)


class WeaviateConnectionError(Exception):
    """Raised when Weaviate connection fails."""
    pass


class WeaviateSchemaError(Exception):
    """Raised when Weaviate schema operations fail."""
    pass


class WeaviateBackend:
    """
    Weaviate backend adapter for advanced retriever.

    This adapter provides integration with Weaviate vector database,
    following the adapter pattern used for external services like Ollama.
    It handles schema management, document indexing, and hybrid search.

    Uses weaviate-client v4 collection-based API.
    """

    def __init__(self, config: Union[Dict[str, Any], WeaviateBackendConfig]):
        """
        Initialize Weaviate backend adapter.

        Args:
            config: Configuration dictionary or WeaviateBackendConfig instance

        Raises:
            ImportError: If weaviate-client is not installed
            WeaviateConnectionError: If connection fails
        """
        if not WEAVIATE_AVAILABLE:
            raise ImportError(
                "weaviate-client is required for Weaviate backend. "
                "Install with: pip install weaviate-client"
            )

        # Convert config if needed
        if isinstance(config, dict):
            self.config = WeaviateBackendConfig.from_dict(config)
        else:
            self.config = config

        # Initialize client and connection
        self.client: Optional[weaviate.WeaviateClient] = None
        self._collection = None
        self.is_connected = False
        self.schema_created = False

        # Performance tracking
        self.stats = {
            "total_operations": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "last_operation_time": 0.0,
            "search_count": 0,
            "add_count": 0,
            "error_count": 0,
            "connection_errors": 0,
            "schema_errors": 0
        }

        # Backend identification
        self.backend_type = "weaviate"
        self.backend_version = "v4-adapter"

        # Initialize connection
        self._connect()

        logger.info("Weaviate backend adapter initialized")

    def _connect(self) -> None:
        """
        Establish connection to Weaviate server.

        Raises:
            WeaviateConnectionError: If connection fails after retries
        """
        if not WEAVIATE_AVAILABLE or weaviate is None:
            raise WeaviateConnectionError("Weaviate package not available. Install with 'pip install weaviate-client'")

        for attempt in range(self.config.max_retries + 1):
            try:
                parsed = urlparse(self.config.connection.url)
                http_host = parsed.hostname or "localhost"
                http_port = parsed.port or 8080
                http_secure = parsed.scheme == "https"

                connect_kwargs = {
                    "http_host": http_host,
                    "http_port": http_port,
                    "http_secure": http_secure,
                    "grpc_host": http_host,
                    "grpc_port": self.config.connection.grpc_port,
                    "grpc_secure": http_secure,
                    "additional_config": AdditionalConfig(
                        timeout=Timeout(
                            query=self.config.connection.timeout,
                            insert=self.config.connection.timeout * 2,
                        )
                    ),
                }

                if self.config.connection.api_key:
                    connect_kwargs["auth_credentials"] = Auth.api_key(self.config.connection.api_key)

                if self.config.connection.additional_headers:
                    connect_kwargs["headers"] = self.config.connection.additional_headers

                self.client = weaviate.connect_to_custom(**connect_kwargs)

                # Test connection
                if self.client.is_ready():
                    self.is_connected = True
                    logger.info(f"Connected to Weaviate at {self.config.connection.url}")

                    # Create schema if needed
                    if self.config.auto_create_schema:
                        self._ensure_schema()

                    return
                else:
                    raise WeaviateConnectionError("Weaviate server not ready")

            except WeaviateConnectionError:
                raise
            except Exception as e:
                self.stats["connection_errors"] += 1
                logger.warning(f"Connection attempt {attempt + 1} failed: {str(e)}")

                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay_seconds * (2 ** attempt))
                else:
                    raise WeaviateConnectionError(f"Failed to connect to Weaviate after {self.config.max_retries + 1} attempts: {str(e)}")

    def _ensure_schema(self) -> None:
        """
        Ensure the required schema exists in Weaviate.

        Raises:
            WeaviateSchemaError: If schema creation fails
        """
        try:
            existing = self.client.collections.list_all()
            if self.config.schema.class_name in existing:
                self._collection = self.client.collections.get(self.config.schema.class_name)
                logger.info(f"Schema class '{self.config.schema.class_name}' already exists")
                self.schema_created = True
                return

            # Map v3-style property dicts to v4 Property objects
            datatype_map = {
                "text": DataType.TEXT,
                "int": DataType.INT,
                "date": DataType.DATE,
                "number": DataType.NUMBER,
                "boolean": DataType.BOOL,
            }
            v4_properties = []
            for prop in self.config.schema.properties:
                dt_str = prop["dataType"][0]  # v3 uses ["text"], v4 uses DataType.TEXT
                v4_properties.append(Property(
                    name=prop["name"],
                    data_type=datatype_map.get(dt_str, DataType.TEXT),
                    description=prop.get("description", ""),
                ))

            self.client.collections.create(
                name=self.config.schema.class_name,
                description=self.config.schema.description,
                properties=v4_properties,
                vectorizer_config=Configure.Vectorizer.none(),
            )
            self._collection = self.client.collections.get(self.config.schema.class_name)
            self.schema_created = True

            logger.info(f"Created schema class '{self.config.schema.class_name}'")

        except Exception as e:
            self.stats["schema_errors"] += 1
            error_msg = f"Failed to create schema: {str(e)}"
            logger.error(error_msg)
            raise WeaviateSchemaError(error_msg) from e

    def initialize_index(self, embedding_dim: int) -> None:
        """
        Initialize the Weaviate index with specified dimension.

        Args:
            embedding_dim: Dimension of the embedding vectors

        Note:
            Weaviate handles dimensionality automatically, but we validate
            that the connection is ready and schema exists.
        """
        start_time = time.time()

        try:
            if not self.is_connected:
                self._connect()

            if not self.schema_created and self.config.auto_create_schema:
                self._ensure_schema()

            logger.info(f"Weaviate backend ready for embeddings with dimension {embedding_dim}")

            elapsed_time = time.time() - start_time
            self._update_stats("initialize", elapsed_time)

        except Exception as e:
            self.stats["error_count"] += 1
            logger.error(f"Failed to initialize Weaviate backend: {str(e)}")
            raise RuntimeError(f"Weaviate backend initialization failed: {str(e)}") from e

    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the Weaviate index using batch operations.

        Args:
            documents: List of documents with embeddings to add
        """
        start_time = time.time()

        try:
            if not documents:
                raise ValueError("Cannot add empty document list")

            if not self.is_connected:
                self._connect()

            if self._collection is None:
                self._ensure_schema()

            # Validate embeddings
            for i, doc in enumerate(documents):
                if doc.embedding is None:
                    raise ValueError(f"Document {i} missing embedding")

            # Batch insert via collection
            with self._collection.batch.fixed_size(
                batch_size=self.config.batch.batch_size,
            ) as batch:
                for i, document in enumerate(documents):
                    properties = {
                        "content": document.content,
                        "source_file": document.metadata.get("source", "unknown"),
                        "chunk_index": document.metadata.get("chunk_index", i),
                        "page_number": document.metadata.get("page", 0),
                        "chunk_size": len(document.content),
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }

                    doc_uuid = str(uuid.uuid4())

                    batch.add_object(
                        properties=properties,
                        uuid=doc_uuid,
                        vector=document.embedding,
                    )

            elapsed_time = time.time() - start_time
            self._update_stats("add", elapsed_time)
            self.stats["add_count"] += len(documents)

            logger.info(f"Added {len(documents)} documents to Weaviate backend in {elapsed_time:.2f}s")

        except Exception as e:
            self.stats["error_count"] += 1
            logger.error(f"Failed to add documents to Weaviate backend: {str(e)}")
            raise RuntimeError(f"Weaviate backend add failed: {str(e)}") from e

    def search(self, query_embedding: np.ndarray, k: int = 5, query_text: Optional[str] = None) -> List[Tuple[int, float]]:
        """
        Search for similar documents using Weaviate.

        Args:
            query_embedding: Query vector
            k: Number of results to return
            query_text: Optional query text for hybrid search

        Returns:
            List of (document_index, score) tuples
        """
        start_time = time.time()

        try:
            if k <= 0:
                raise ValueError("k must be positive")

            if not self.is_connected:
                self._connect()

            if self._collection is None:
                self._ensure_schema()

            return_props = ["content", "source_file", "chunk_index"]

            if query_text and self.config.search.hybrid_search_enabled:
                response = self._collection.query.hybrid(
                    query=query_text,
                    alpha=self.config.search.alpha,
                    vector=query_embedding.tolist(),
                    limit=k,
                    return_properties=return_props,
                    return_metadata=MetadataQuery(score=True, distance=True),
                )
            else:
                response = self._collection.query.near_vector(
                    near_vector=query_embedding.tolist(),
                    limit=k,
                    return_properties=return_props,
                    return_metadata=MetadataQuery(distance=True, certainty=True),
                )

            results = []
            for i, obj in enumerate(response.objects):
                meta = obj.metadata
                score = None
                if meta.score is not None:
                    score = float(meta.score)
                elif meta.certainty is not None:
                    score = float(meta.certainty)
                elif meta.distance is not None:
                    score = 1.0 / (1.0 + float(meta.distance))

                if score is None:
                    score = 1.0 - (i * 0.1)

                doc_index = obj.properties.get("chunk_index", i)
                results.append((doc_index, score))

            elapsed_time = time.time() - start_time
            self._update_stats("search", elapsed_time)
            self.stats["search_count"] += 1

            logger.debug(f"Weaviate search returned {len(results)} results in {elapsed_time:.4f}s")

            return results

        except Exception as e:
            self.stats["error_count"] += 1
            logger.error(f"Weaviate backend search failed: {str(e)}")
            raise RuntimeError(f"Weaviate backend search failed: {str(e)}") from e

    def get_document_count(self) -> int:
        """
        Get the number of documents in the index.

        Returns:
            Number of indexed documents
        """
        try:
            if not self.is_connected or self._collection is None:
                return 0

            response = self._collection.aggregate.over_all(total_count=True)
            return response.total_count

        except Exception as e:
            logger.error(f"Failed to get document count: {str(e)}")
            return 0

    def is_trained(self) -> bool:
        """
        Check if the index is ready for use.

        Returns:
            True if index is ready, False otherwise
        """
        return self.is_connected and self.schema_created

    def clear(self) -> None:
        """Clear all documents from the index."""
        start_time = time.time()

        try:
            if not self.is_connected:
                logger.warning("Not connected to Weaviate, cannot clear")
                return

            # Delete the collection and recreate it
            self.client.collections.delete(self.config.schema.class_name)
            self._collection = None
            self.schema_created = False
            self._ensure_schema()

            elapsed_time = time.time() - start_time
            self._update_stats("clear", elapsed_time)

            logger.info("Weaviate backend cleared")

        except Exception as e:
            self.stats["error_count"] += 1
            logger.error(f"Failed to clear Weaviate backend: {str(e)}")
            raise RuntimeError(f"Weaviate backend clear failed: {str(e)}") from e

    def close(self) -> None:
        """Close the Weaviate client connection."""
        if self.client:
            self.client.close()
            self.is_connected = False

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about the backend.

        Returns:
            Dictionary with backend information
        """
        try:
            meta_info = {}
            if self.is_connected:
                try:
                    meta_info = self.client.get_meta()
                except Exception:
                    meta_info = {"error": "Could not retrieve meta info"}

            return {
                "backend_type": self.backend_type,
                "backend_version": self.backend_version,
                "is_connected": self.is_connected,
                "schema_created": self.schema_created,
                "document_count": self.get_document_count(),
                "weaviate_meta": meta_info,
                "stats": self.stats.copy(),
                "config": self.config.to_dict()
            }

        except Exception as e:
            return {
                "backend_type": self.backend_type,
                "error": str(e),
                "stats": self.stats.copy()
            }

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the backend.

        Returns:
            Dictionary with health status
        """
        try:
            is_healthy = True
            issues = []

            if not self.is_connected:
                is_healthy = False
                issues.append("Not connected to Weaviate")
            elif self.client and not self.client.is_ready():
                is_healthy = False
                issues.append("Weaviate server not ready")

            if not self.schema_created:
                is_healthy = False
                issues.append("Schema not created")

            error_rate = self.stats["error_count"] / max(1, self.stats["total_operations"])
            if error_rate > 0.1:
                is_healthy = False
                issues.append(f"High error rate: {error_rate:.2%}")

            doc_count = self.get_document_count()
            if doc_count == 0:
                issues.append("No documents indexed")

            return {
                "backend_type": "weaviate",
                "is_healthy": is_healthy,
                "issues": issues,
                "is_connected": self.is_connected,
                "schema_created": self.schema_created,
                "document_count": doc_count,
                "error_rate": error_rate,
                "total_operations": self.stats["total_operations"]
            }

        except Exception as e:
            return {
                "backend_type": "weaviate",
                "is_healthy": False,
                "issues": [f"Health check failed: {str(e)}"],
                "error": str(e)
            }

    def supports_hybrid_search(self) -> bool:
        """Check if backend supports hybrid search."""
        return True

    def supports_filtering(self) -> bool:
        """Check if backend supports metadata filtering."""
        return True

    def _update_stats(self, operation: str, elapsed_time: float) -> None:
        """Update performance statistics."""
        self.stats["total_operations"] += 1
        self.stats["total_time"] += elapsed_time
        self.stats["avg_time"] = self.stats["total_time"] / self.stats["total_operations"]
        self.stats["last_operation_time"] = elapsed_time

    def get_configuration(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return {
            "backend_type": "weaviate",
            "config": self.config.to_dict()
        }
