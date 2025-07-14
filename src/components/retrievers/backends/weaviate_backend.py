"""
Weaviate backend adapter for advanced retriever.

This module provides an adapter for Weaviate vector database integration,
following the same pattern as other external service adapters in the system.
It handles Weaviate-specific operations, schema management, and hybrid search.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

try:
    import weaviate
    from weaviate import Client
    from weaviate.exceptions import WeaviateException
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False
    weaviate = None
    Client = None
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
    
    Features:
    - Automatic schema creation and management
    - Hybrid search (vector + keyword)
    - Batch operations for performance
    - Comprehensive error handling with fallbacks
    - Performance monitoring and statistics
    - Health checking and diagnostics
    
    The adapter follows external service patterns:
    - Connection management with retries
    - Service-specific error handling
    - Configuration-driven behavior
    - Comprehensive logging and monitoring
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
        self.client: Optional[Client] = None
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
        self.backend_version = "adapter"
        
        # Initialize connection
        self._connect()
        
        logger.info("Weaviate backend adapter initialized")
    
    def _connect(self) -> None:
        """
        Establish connection to Weaviate server.
        
        Raises:
            WeaviateConnectionError: If connection fails after retries
        """
        for attempt in range(self.config.max_retries + 1):
            try:
                # Create client with configuration
                client_config = {
                    'url': self.config.connection.url,
                    'timeout_config': weaviate.TimeoutConfig(
                        query=self.config.connection.timeout,
                        insert=self.config.connection.timeout * 2
                    ),
                    'startup_period': self.config.connection.startup_period
                }
                
                # Add authentication if provided
                if self.config.connection.api_key:
                    client_config['auth_client_secret'] = weaviate.AuthApiKey(
                        api_key=self.config.connection.api_key
                    )
                
                # Add additional headers
                if self.config.connection.additional_headers:
                    client_config['additional_headers'] = self.config.connection.additional_headers
                
                self.client = weaviate.Client(**client_config)
                
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
                    
            except Exception as e:
                self.stats["connection_errors"] += 1
                logger.warning(f"Connection attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay_seconds * (2 ** attempt))  # Exponential backoff
                else:
                    raise WeaviateConnectionError(f"Failed to connect to Weaviate after {self.config.max_retries + 1} attempts: {str(e)}")
    
    def _ensure_schema(self) -> None:
        """
        Ensure the required schema exists in Weaviate.
        
        Raises:
            WeaviateSchemaError: If schema creation fails
        """
        try:
            # Check if class already exists
            existing_schema = self.client.schema.get()
            class_names = [cls['class'] for cls in existing_schema.get('classes', [])]
            
            if self.config.schema.class_name in class_names:
                logger.info(f"Schema class '{self.config.schema.class_name}' already exists")
                self.schema_created = True
                return
            
            # Create new class
            class_definition = {
                "class": self.config.schema.class_name,
                "description": self.config.schema.description,
                "vectorizer": "none",  # We provide our own embeddings
                "vectorIndexConfig": self.config.schema.vector_index_config,
                "properties": self.config.schema.properties
            }
            
            self.client.schema.create_class(class_definition)
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
            
            # Validate embedding dimension (informational)
            logger.info(f"Weaviate backend ready for embeddings with dimension {embedding_dim}")
            
            # Update stats
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
            
            # Validate embeddings
            for i, doc in enumerate(documents):
                if doc.embedding is None:
                    raise ValueError(f"Document {i} missing embedding")
            
            # Batch insert
            with self.client.batch(
                batch_size=self.config.batch.batch_size,
                num_workers=self.config.batch.num_workers,
                connection_error_retries=self.config.batch.connection_error_retries,
                timeout_retries=self.config.batch.timeout_retries,
                callback=self._batch_callback if self.config.batch.callback_period else None
            ) as batch:
                
                for i, document in enumerate(documents):
                    # Prepare document properties
                    properties = {
                        "content": document.content,
                        "source_file": document.metadata.get("source", "unknown"),
                        "chunk_index": document.metadata.get("chunk_index", i),
                        "page_number": document.metadata.get("page", 0),
                        "chunk_size": len(document.content),
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # Add additional metadata
                    for key, value in document.metadata.items():
                        if key not in properties and isinstance(value, (str, int, float, bool)):
                            properties[key] = value
                    
                    # Generate UUID for document
                    doc_uuid = str(uuid.uuid4())
                    
                    # Add to batch
                    batch.add_data_object(
                        data_object=properties,
                        class_name=self.config.schema.class_name,
                        uuid=doc_uuid,
                        vector=document.embedding
                    )
            
            # Update stats
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
            
            # Build query
            query_builder = (
                self.client.query
                .get(self.config.schema.class_name, ["content", "source_file", "chunk_index"])
                .with_limit(k)
            )
            
            # Use hybrid search if text query provided and enabled
            if query_text and self.config.search.hybrid_search_enabled:
                query_builder = query_builder.with_hybrid(
                    query=query_text,
                    alpha=self.config.search.alpha,
                    vector=query_embedding.tolist()
                )
            else:
                # Pure vector search
                query_builder = query_builder.with_near_vector({
                    "vector": query_embedding.tolist(),
                    "certainty": self.config.search.certainty_threshold
                })
            
            # Add additional search parameters
            if self.config.search.autocut > 0:
                query_builder = query_builder.with_autocut(self.config.search.autocut)
            
            # Execute query
            result = query_builder.do()
            
            # Process results
            results = []
            if 'data' in result and 'Get' in result['data']:
                class_results = result['data']['Get'].get(self.config.schema.class_name, [])
                
                for i, item in enumerate(class_results):
                    # Extract score
                    if '_additional' in item:
                        if 'score' in item['_additional']:
                            score = float(item['_additional']['score'])
                        elif 'certainty' in item['_additional']:
                            score = float(item['_additional']['certainty'])
                        elif 'distance' in item['_additional']:
                            # Convert distance to similarity score
                            distance = float(item['_additional']['distance'])
                            score = 1.0 / (1.0 + distance)
                        else:
                            score = 1.0 - (i * 0.1)  # Default decreasing score
                    else:
                        score = 1.0 - (i * 0.1)  # Default decreasing score
                    
                    # Use chunk_index if available, otherwise use position
                    doc_index = item.get('chunk_index', i)
                    results.append((doc_index, score))
            
            # Update stats
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
            if not self.is_connected:
                return 0
            
            result = (
                self.client.query
                .aggregate(self.config.schema.class_name)
                .with_meta_count()
                .do()
            )
            
            if 'data' in result and 'Aggregate' in result['data']:
                aggregate_data = result['data']['Aggregate'].get(self.config.schema.class_name, [])
                if aggregate_data:
                    return aggregate_data[0].get('meta', {}).get('count', 0)
            
            return 0
            
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
            
            # Delete all objects of the class
            self.client.batch.delete_objects(
                class_name=self.config.schema.class_name,
                where={
                    "operator": "Like",
                    "path": ["content"],
                    "valueText": "*"
                }
            )
            
            # Update stats
            elapsed_time = time.time() - start_time
            self._update_stats("clear", elapsed_time)
            
            logger.info("Weaviate backend cleared")
            
        except Exception as e:
            self.stats["error_count"] += 1
            logger.error(f"Failed to clear Weaviate backend: {str(e)}")
            raise RuntimeError(f"Weaviate backend clear failed: {str(e)}") from e
    
    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about the backend.
        
        Returns:
            Dictionary with backend information
        """
        try:
            # Get Weaviate meta info
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
            
            # Check connection
            if not self.is_connected:
                is_healthy = False
                issues.append("Not connected to Weaviate")
            elif self.client and not self.client.is_ready():
                is_healthy = False
                issues.append("Weaviate server not ready")
            
            # Check schema
            if not self.schema_created:
                is_healthy = False
                issues.append("Schema not created")
            
            # Check error rate
            error_rate = self.stats["error_count"] / max(1, self.stats["total_operations"])
            if error_rate > 0.1:  # More than 10% errors
                is_healthy = False
                issues.append(f"High error rate: {error_rate:.2%}")
            
            # Check if we have documents
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
        """
        Check if backend supports hybrid search.
        
        Returns:
            True for Weaviate (supports vector + keyword search)
        """
        return True
    
    def supports_filtering(self) -> bool:
        """
        Check if backend supports metadata filtering.
        
        Returns:
            True for Weaviate (supports where filters)
        """
        return True
    
    def _update_stats(self, operation: str, elapsed_time: float) -> None:
        """
        Update performance statistics.
        
        Args:
            operation: Name of the operation
            elapsed_time: Time taken for the operation
        """
        self.stats["total_operations"] += 1
        self.stats["total_time"] += elapsed_time
        self.stats["avg_time"] = self.stats["total_time"] / self.stats["total_operations"]
        self.stats["last_operation_time"] = elapsed_time
    
    def _batch_callback(self, results: Dict[str, Any]) -> None:
        """
        Callback for batch operations.
        
        Args:
            results: Batch operation results
        """
        if results:
            logger.debug(f"Batch operation completed: {len(results)} items processed")
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get the current configuration.
        
        Returns:
            Configuration dictionary
        """
        return {
            "backend_type": "weaviate",
            "config": self.config.to_dict()
        }