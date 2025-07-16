"""
Unit Tests for Weaviate Backend (Epic 2 Task 2.7).

This module provides comprehensive unit tests for the Weaviate backend adapter
following the Epic 2 testing specification. Tests cover Weaviate operations,
hybrid search, schema management, and error handling.

Total Tests: 12 (Contributing to 60 unit tests requirement)
"""

import unittest
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock
import random

from src.components.retrievers.backends.weaviate_backend import (
    WeaviateBackend,
    WeaviateConnectionError,
)
from src.components.retrievers.backends.weaviate_config import WeaviateBackendConfig
from src.core.interfaces import Document

# Check if weaviate is available
try:
    import weaviate
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False


class TestWeaviateBackend(unittest.TestCase):
    """Test suite for Weaviate backend adapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = WeaviateBackendConfig()
        self.sample_documents = [
            Document(
                content="RISC-V is an open-source hardware instruction set architecture",
                metadata={"source_file": "riscv_intro.pdf", "page_number": 1},
                embedding=[random.random() for _ in range(384)],
            ),
            Document(
                content="The base integer instruction set has 32 registers",
                metadata={"source_file": "riscv_base.pdf", "page_number": 2},
                embedding=[random.random() for _ in range(384)],
            ),
        ]

    \1        if not WEAVIATE_AVAILABLE:\n            self.skipTest("Weaviate package not available")\n        \n        if not WEAVIATE_AVAILABLE:
            self.skipTest("Weaviate package not available")
        
        with patch(
            "src.components.retrievers.backends.weaviate_backend.WEAVIATE_AVAILABLE",
            True,
        ):
            backend = WeaviateBackend(self.mock_config)

            self.assertEqual(backend.config, self.mock_config)
            self.assertFalse(backend.is_connected)
            self.assertEqual(backend.stats["total_operations"], 0)

    \1        if not WEAVIATE_AVAILABLE:\n            self.skipTest("Weaviate package not available")\n        \n        with patch(
            "src.components.retrievers.backends.weaviate_backend.WEAVIATE_AVAILABLE",
            False,
        ):
            with self.assertRaises(ImportError):
                WeaviateBackend(self.mock_config)

    @patch("src.components.retrievers.backends.weaviate_backend.weaviate.Client")
    \1        if not WEAVIATE_AVAILABLE:\n            self.skipTest("Weaviate package not available")\n        \n        with patch(
            "src.components.retrievers.backends.weaviate_backend.WEAVIATE_AVAILABLE",
            True,
        ):
            mock_client = MagicMock()
            mock_client.is_ready.return_value = True
            mock_client_class.return_value = mock_client

            backend = WeaviateBackend(self.mock_config)
            backend._connect()

            self.assertTrue(backend.is_connected)
            self.assertEqual(backend.client, mock_client)
            mock_client.is_ready.assert_called_once()

    @patch("src.components.retrievers.backends.weaviate_backend.weaviate.Client")
    \1        if not WEAVIATE_AVAILABLE:\n            self.skipTest("Weaviate package not available")\n        \n        with patch(
            "src.components.retrievers.backends.weaviate_backend.WEAVIATE_AVAILABLE",
            True,
        ):
            mock_client = MagicMock()
            mock_client.is_ready.side_effect = Exception("Connection failed")
            mock_client_class.return_value = mock_client

            backend = WeaviateBackend(self.mock_config)

            with self.assertRaises(WeaviateConnectionError):
                backend._connect()

    \1        if not WEAVIATE_AVAILABLE:\n            self.skipTest("Weaviate package not available")\n        \n        with patch(
            "src.components.retrievers.backends.weaviate_backend.WEAVIATE_AVAILABLE",
            True,
        ):
            backend = WeaviateBackend(self.mock_config)
            backend.client = MagicMock()
            backend.client.schema.exists.return_value = False

            backend._ensure_schema()

            # Verify schema operations were called
            backend.client.schema.exists.assert_called()

    \1        if not WEAVIATE_AVAILABLE:\n            self.skipTest("Weaviate package not available")\n        \n        with patch(
            "src.components.retrievers.backends.weaviate_backend.WEAVIATE_AVAILABLE",
            True,
        ):
            backend = WeaviateBackend(self.mock_config)
            backend.client = MagicMock()
            backend.is_connected = True

            embedding_dim = 384
            backend.initialize_index(embedding_dim)

            # Check that the method completed without error
            self.assertTrue(backend.is_connected)

    \1        if not WEAVIATE_AVAILABLE:\n            self.skipTest("Weaviate package not available")\n        \n        with patch(
            "src.components.retrievers.backends.weaviate_backend.WEAVIATE_AVAILABLE",
            True,
        ):
            backend = WeaviateBackend(self.mock_config)
            backend.client = MagicMock()
            backend.is_connected = True

            # Mock batch operations
            mock_batch = MagicMock()
            backend.client.batch.configure.return_value = mock_batch
            backend.client.batch = mock_batch

            backend.add_documents(self.sample_documents)

            # Verify batch operations
            self.assertTrue(mock_batch.add_data_object.called)
            mock_batch.flush.assert_called()

    \1        if not WEAVIATE_AVAILABLE:\n            self.skipTest("Weaviate package not available")\n        \n        with patch(
            "src.components.retrievers.backends.weaviate_backend.WEAVIATE_AVAILABLE",
            True,
        ):
            backend = WeaviateBackend(self.mock_config)
            backend.client = MagicMock()
            backend.is_connected = True

            # Mock search results
            mock_result = {
                "data": {
                    "Get": {
                        "TechnicalDocument": [
                            {
                                "content": "RISC-V architecture",
                                "chunk_index": 0,
                                "_additional": {"certainty": 0.9},
                            },
                            {
                                "content": "Instruction set",
                                "chunk_index": 1,
                                "_additional": {"certainty": 0.8},
                            },
                        ]
                    }
                }
            }

            # Mock query builder
            mock_query = MagicMock()
            mock_query.do.return_value = mock_result
            backend.client.query.get.return_value.with_limit.return_value.with_near_vector.return_value = (
                mock_query
            )

            query_embedding = [random.random() for _ in range(384)]
            results = backend.search(query_embedding, k=5)

            self.assertEqual(len(results), 2)
            self.assertEqual(results[0], (0, 0.9))
            self.assertEqual(results[1], (1, 0.8))

    \1        if not WEAVIATE_AVAILABLE:\n            self.skipTest("Weaviate package not available")\n        \n        with patch(
            "src.components.retrievers.backends.weaviate_backend.WEAVIATE_AVAILABLE",
            True,
        ):
            backend = WeaviateBackend(self.mock_config)
            backend.client = MagicMock()
            backend.is_connected = True

            # Mock hybrid search results
            mock_result = {
                "data": {
                    "Get": {
                        "TechnicalDocument": [
                            {
                                "content": "RISC-V hybrid result",
                                "chunk_index": 0,
                                "_additional": {"score": 0.95},
                            }
                        ]
                    }
                }
            }

            # Mock query builder for hybrid search
            mock_query = MagicMock()
            mock_query.do.return_value = mock_result
            backend.client.query.get.return_value.with_limit.return_value.with_hybrid.return_value = (
                mock_query
            )

            query_embedding = [random.random() for _ in range(384)]
            results = backend.search(
                query_embedding, k=5, query_text="RISC-V architecture"
            )

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0], (0, 0.95))

    \1        if not WEAVIATE_AVAILABLE:\n            self.skipTest("Weaviate package not available")\n        \n        with patch(
            "src.components.retrievers.backends.weaviate_backend.WEAVIATE_AVAILABLE",
            True,
        ):
            backend = WeaviateBackend(self.mock_config)
            backend.client = MagicMock()
            backend.is_connected = True
            backend.client.is_ready.return_value = True

            health = backend.health_check()

            self.assertEqual(health["status"], "healthy")
            self.assertTrue(health["connected"])
            self.assertTrue(health["ready"])

    \1        if not WEAVIATE_AVAILABLE:\n            self.skipTest("Weaviate package not available")\n        \n        with patch(
            "src.components.retrievers.backends.weaviate_backend.WEAVIATE_AVAILABLE",
            True,
        ):
            backend = WeaviateBackend(self.mock_config)
            backend.client = MagicMock()
            backend.is_connected = False

            health = backend.health_check()

            self.assertEqual(health["status"], "unhealthy")
            self.assertFalse(health["connected"])

    \1        if not WEAVIATE_AVAILABLE:\n            self.skipTest("Weaviate package not available")\n        \n        with patch(
            "src.components.retrievers.backends.weaviate_backend.WEAVIATE_AVAILABLE",
            True,
        ):
            backend = WeaviateBackend(self.mock_config)

            # Simulate operations
            backend._update_stats("search", 0.1)
            backend._update_stats("index", 0.5)

            stats = backend.get_stats()

            self.assertEqual(stats["total_operations"], 2)
            self.assertEqual(stats["total_time"], 0.6)
            self.assertEqual(stats["avg_time"], 0.3)


if __name__ == "__main__":
    unittest.main()
