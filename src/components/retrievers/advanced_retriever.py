"""
Advanced Retriever for Epic 2 Implementation.

This module provides an advanced retriever that extends the ModularUnifiedRetriever
with multi-backend support, hybrid search strategies, neural reranking, and real-time
analytics. It maintains backward compatibility while adding sophisticated features.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

from src.core.interfaces import Retriever, Document, RetrievalResult, Embedder
from .modular_unified_retriever import ModularUnifiedRetriever
from .backends.faiss_backend import FAISSBackend
from .backends.weaviate_backend import WeaviateBackend
from .config.advanced_config import AdvancedRetrieverConfig
from .backends.migration.faiss_to_weaviate import FAISSToWeaviateMigrator

# Graph components (Epic 2 Week 2)
from .graph.config.graph_config import GraphConfig
from .graph.entity_extraction import EntityExtractor
from .graph.document_graph_builder import DocumentGraphBuilder
from .graph.relationship_mapper import RelationshipMapper
from .graph.graph_retriever import GraphRetriever
from .graph.graph_analytics import GraphAnalytics

# Neural Reranking components (Epic 2 Week 3)
from .reranking.neural_reranker import NeuralReranker
from .reranking.config.reranking_config import EnhancedNeuralRerankingConfig

logger = logging.getLogger(__name__)


class AdvancedRetrievalError(Exception):
    """Raised when advanced retrieval operations fail."""

    pass


class AdvancedRetriever(ModularUnifiedRetriever):
    """
    Advanced retriever with multi-backend support and sophisticated features.

    This retriever extends the ModularUnifiedRetriever to provide:
    - Multiple vector database backends (FAISS, Weaviate)
    - Hot-swapping between backends with health monitoring
    - Advanced hybrid search strategies
    - Knowledge graph integration (Epic 2 Week 2)
    - Neural reranking capabilities (future)
    - Real-time analytics and monitoring
    - A/B testing framework (future)

    The implementation follows the existing architecture patterns while
    adding Epic 2 enhancements. It maintains full backward compatibility
    with the ModularUnifiedRetriever interface.

    Features in this implementation:
    - ✅ Multi-backend support (FAISS + Weaviate)
    - ✅ Backend health monitoring and fallbacks
    - ✅ Migration tools between backends
    - ✅ Enhanced hybrid search (dense + sparse + graph)
    - ✅ Graph-based retrieval (Epic 2 Week 2)
    - 🔄 Neural reranking (framework ready)
    - ✅ Performance analytics with graph metrics
    - 🔄 A/B testing (framework ready)
    """

    def __init__(
        self, config: Union[Dict[str, Any], AdvancedRetrieverConfig], embedder: Embedder
    ):
        """
        Initialize the advanced retriever.

        Args:
            config: Configuration dictionary or AdvancedRetrieverConfig instance
            embedder: Embedder component for query encoding
        """
        # Convert config if needed
        if isinstance(config, dict):
            self.advanced_config = AdvancedRetrieverConfig.from_dict(config)
        else:
            self.advanced_config = config

        # Initialize parent with base configuration
        base_config = self._extract_base_config()
        super().__init__(base_config, embedder)

        # Advanced components
        self.backends: Dict[str, Any] = {}
        self.active_backend_name = self.advanced_config.backends.primary_backend
        self.fallback_backend_name = self.advanced_config.backends.fallback_backend

        # Performance tracking
        self.advanced_stats = {
            "backend_switches": 0,
            "fallback_activations": 0,
            "total_advanced_retrievals": 0,
            "backend_health_checks": 0,
            "last_health_check": 0,
            "migration_count": 0,
        }

        # Analytics collector
        self.analytics_enabled = self.advanced_config.analytics.enabled
        self.query_analytics: List[Dict[str, Any]] = []

        # Graph components (Epic 2 Week 2)
        self.graph_config = None
        self.entity_extractor = None
        self.graph_builder = None
        self.relationship_mapper = None
        self.graph_retriever = None
        self.graph_analytics = None

        # Neural Reranking components (Epic 2 Week 3)
        self.neural_reranker = None

        # Initialize backends (including graph if enabled)
        self._initialize_backends()

        # Set up health monitoring
        if self.advanced_config.backends.enable_hot_swap:
            self._setup_health_monitoring()

        logger.info(
            f"Advanced retriever initialized with backend: {self.active_backend_name}"
        )
        logger.info(f"Enabled features: {self.advanced_config.get_enabled_features()}")

    def _extract_base_config(self) -> Dict[str, Any]:
        """Extract base configuration for ModularUnifiedRetriever."""
        return {
            "vector_index": {
                "type": "faiss",
                "config": self.advanced_config.backends.faiss,
            },
            "sparse": {
                "type": "bm25",
                "config": {
                    "k1": 1.2,
                    "b": 0.75,
                    "lowercase": True,
                    "preserve_technical_terms": True,
                },
            },
            "fusion": {
                "type": self.advanced_config.hybrid_search.fusion_method,
                "config": {
                    "k": self.advanced_config.hybrid_search.rrf_k,
                    "weights": {
                        "dense": self.advanced_config.hybrid_search.dense_weight,
                        "sparse": self.advanced_config.hybrid_search.sparse_weight,
                    },
                },
            },
            "reranker": {"type": "identity", "config": {"enabled": True}},
        }

    def _initialize_backends(self) -> None:
        """Initialize all configured backends."""
        # Initialize FAISS backend (wraps existing functionality)
        faiss_config = {"faiss": self.advanced_config.backends.faiss}
        self.backends["faiss"] = FAISSBackend(faiss_config)

        # Initialize Weaviate backend if enabled
        if (
            self.advanced_config.feature_flags.get("weaviate_backend", False)
            and self.advanced_config.backends.weaviate
        ):

            try:
                self.backends["weaviate"] = WeaviateBackend(
                    self.advanced_config.backends.weaviate
                )
                logger.info("Weaviate backend initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Weaviate backend: {str(e)}")
                if self.active_backend_name == "weaviate":
                    logger.info("Falling back to FAISS backend")
                    self.active_backend_name = "faiss"

        # Validate active backend
        if self.active_backend_name not in self.backends:
            raise AdvancedRetrievalError(
                f"Active backend '{self.active_backend_name}' not available"
            )

        # Initialize graph components if enabled
        self._initialize_graph_components()

        # Initialize neural reranking if enabled
        self._initialize_neural_reranking()

    def _initialize_graph_components(self) -> None:
        """Initialize graph-based retrieval components."""
        try:
            # Check if graph retrieval is enabled
            graph_enabled = hasattr(
                self.advanced_config, "graph_retrieval"
            ) and getattr(self.advanced_config.graph_retrieval, "enabled", False)

            if not graph_enabled:
                logger.info("Graph retrieval disabled in configuration")
                return

            # Get graph configuration and convert to proper GraphConfig
            graph_retrieval_config = getattr(
                self.advanced_config, "graph_retrieval", {}
            )

            # If it's a simple GraphRetrievalConfig object, convert to full GraphConfig
            if hasattr(graph_retrieval_config, "enabled") and not isinstance(
                graph_retrieval_config, dict
            ):
                # Create full GraphConfig with defaults
                graph_config_dict = {
                    "enabled": graph_retrieval_config.enabled,
                    "builder": {
                        "implementation": "networkx",
                        "config": {
                            "node_types": [
                                "concept",
                                "protocol",
                                "architecture",
                                "extension",
                            ],
                            "relationship_types": [
                                "implements",
                                "extends",
                                "requires",
                                "conflicts",
                            ],
                            "max_graph_size": 10000,
                        },
                    },
                    "entity_extraction": {
                        "implementation": "spacy",
                        "config": {
                            "model": "en_core_web_sm",
                            "entity_types": ["TECH", "PROTOCOL", "ARCH"],
                            "confidence_threshold": 0.8,
                            "batch_size": 32,
                        },
                    },
                    "relationship_detection": {
                        "implementation": "semantic",
                        "config": {
                            "similarity_threshold": getattr(
                                graph_retrieval_config, "similarity_threshold", 0.7
                            ),
                            "relationship_model": "sentence_transformer",
                            "max_relationships_per_node": 20,
                        },
                    },
                    "retrieval": {
                        "algorithms": [
                            "shortest_path",
                            "random_walk",
                            "subgraph_expansion",
                        ],
                        "max_graph_results": 10,
                        "max_path_length": getattr(
                            graph_retrieval_config, "max_graph_hops", 3
                        ),
                        "score_aggregation": "weighted_average",
                    },
                    "analytics": {
                        "enabled": True,
                        "collect_graph_metrics": True,
                        "collect_retrieval_metrics": True,
                        "enable_visualization": False,
                    },
                }
                self.graph_config = GraphConfig.from_dict(graph_config_dict)
            elif isinstance(graph_retrieval_config, dict):
                self.graph_config = GraphConfig.from_dict(graph_retrieval_config)
            else:
                # Assume it's already a GraphConfig
                self.graph_config = graph_retrieval_config

            # Initialize entity extractor
            self.entity_extractor = EntityExtractor(self.graph_config.entity_extraction)

            # Initialize graph builder
            self.graph_builder = DocumentGraphBuilder(
                self.graph_config.builder, self.entity_extractor
            )

            # Initialize relationship mapper
            self.relationship_mapper = RelationshipMapper(
                self.graph_config.relationship_detection
            )

            # Initialize graph retriever
            self.graph_retriever = GraphRetriever(
                self.graph_config.retrieval, self.graph_builder, self.embedder
            )

            # Initialize graph analytics if enabled
            if self.graph_config.analytics.enabled:
                self.graph_analytics = GraphAnalytics(self.graph_config.analytics)

            # Add graph as a backend
            self.backends["graph"] = self.graph_retriever

            logger.info("Graph retrieval components initialized successfully")

        except Exception as e:
            logger.warning(f"Failed to initialize graph components: {str(e)}")
            logger.info("Continuing without graph functionality")

    def _initialize_neural_reranking(self) -> None:
        """Initialize neural reranking components."""
        try:
            # Check if neural reranking is enabled
            if not self.advanced_config.neural_reranking.enabled:
                logger.info("Neural reranking disabled in configuration")
                return

            # Convert base config to enhanced config for backward compatibility
            import dataclasses

            if hasattr(self.advanced_config.neural_reranking, "__dict__"):
                # If it's a dataclass, convert to dict
                neural_config_dict = dataclasses.asdict(
                    self.advanced_config.neural_reranking
                )
            else:
                # If it's already a dict or other mapping
                neural_config_dict = dict(self.advanced_config.neural_reranking)

            enhanced_config = EnhancedNeuralRerankingConfig.from_base_config(
                neural_config_dict
            )

            # Initialize neural reranker
            self.neural_reranker = NeuralReranker(enhanced_config)

            logger.info("Neural reranking components initialized successfully")

        except Exception as e:
            logger.warning(f"Failed to initialize neural reranking: {str(e)}")
            logger.info("Continuing without neural reranking functionality")
            self.neural_reranker = None

    def _setup_health_monitoring(self) -> None:
        """Set up backend health monitoring."""
        logger.info("Health monitoring enabled for backend hot-swapping")
        # Health monitoring implementation would go here
        # For now, we set up the framework

    def retrieve(self, query: str, k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve relevant documents using advanced modular hybrid search.

        This method extends the base modular retriever with:
        - Multi-backend support with automatic fallback
        - Graph-based retrieval as additional signal
        - Enhanced neural reranking capabilities
        - Advanced analytics collection

        Maintains architectural compliance with 4 sub-component structure:
        1. Vector Index (enhanced with multiple backends)
        2. Sparse Retriever (BM25 with technical optimization)
        3. Fusion Strategy (enhanced to handle graph signals)
        4. Reranker (enhanced with neural capabilities)

        Args:
            query: Search query string
            k: Number of results to return

        Returns:
            List of retrieval results sorted by relevance score
        """
        start_time = time.time()

        try:
            # Pre-retrieval analytics
            if self.analytics_enabled:
                self._collect_query_start_analytics(query, k)

            # Check backend health and switch if needed
            if self.advanced_config.backends.enable_hot_swap:
                self._check_and_switch_backend()

            # Use enhanced modular retrieval with graph and neural capabilities
            results = self._enhanced_modular_retrieval(query, k)

            # Post-retrieval analytics
            if self.analytics_enabled:
                elapsed_time = time.time() - start_time
                self._collect_query_completion_analytics(
                    query, k, results, elapsed_time, self.active_backend_name
                )

            return results

        except Exception as e:
            logger.error(f"Advanced retrieval failed: {str(e)}")

            # Try fallback to parent implementation as last resort
            if not isinstance(e, AdvancedRetrievalError):
                logger.info("Attempting fallback to base ModularUnifiedRetriever")
                try:
                    return super().retrieve(query, k)
                except Exception:
                    pass

            raise RuntimeError(f"Advanced retrieval failed: {str(e)}") from e

    def _enhanced_modular_retrieval(self, query: str, k: int) -> List[RetrievalResult]:
        """
        Enhanced modular retrieval maintaining architectural compliance.
        
        Uses the existing 4 sub-component structure:
        1. Vector Index - enhanced with backend switching
        2. Sparse Retriever - maintains existing BM25 implementation
        3. Fusion Strategy - enhanced to include graph signals
        4. Reranker - enhanced with neural capabilities
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of retrieval results
        """
        start_time = time.time()
        
        try:
            # Validation (from parent class)
            if k <= 0:
                raise ValueError("k must be positive")
            if not query.strip():
                raise ValueError("Query cannot be empty")
            if not self.documents:
                raise RuntimeError("No documents have been indexed")
            
            # 1. Generate query embeddings (same as parent)
            query_embedding = np.array(self.embedder.embed([query])[0])
            
            # 2. Enhanced dense vector search (Sub-component 1: Vector Index)
            dense_results = self._enhanced_dense_search(query_embedding, k*2)
            
            # 3. Sparse keyword search (Sub-component 2: Sparse Retriever - unchanged)
            sparse_results = self.sparse_retriever.search(query, k=k*2)
            
            # 4. Graph-based retrieval (additional signal for fusion)
            graph_results = self._get_graph_retrieval_signals(query, k)
            
            # 5. Enhanced fusion (Sub-component 3: Fusion Strategy with graph)
            fused_results = self._enhanced_fusion_with_graph(dense_results, sparse_results, graph_results)
            
            # 6. Enhanced reranking (Sub-component 4: Reranker with neural capabilities)
            final_results = self._enhanced_neural_reranking(query, fused_results, k)
            
            # Update performance stats
            elapsed_time = time.time() - start_time
            self.retrieval_stats["total_retrievals"] += 1
            self.retrieval_stats["total_time"] += elapsed_time
            self.retrieval_stats["avg_time"] = (
                self.retrieval_stats["total_time"] / self.retrieval_stats["total_retrievals"]
            )
            self.retrieval_stats["last_retrieval_time"] = elapsed_time
            
            return final_results
            
        except Exception as e:
            logger.error(f"Enhanced modular retrieval failed: {str(e)}")
            raise RuntimeError(f"Enhanced modular retrieval failed: {str(e)}") from e

    def _enhanced_dense_search(self, query_embedding: np.ndarray, k: int) -> List[Tuple[int, float]]:
        """Enhanced dense search with backend switching support."""
        try:
            if self.active_backend_name == "weaviate" and "weaviate" in self.backends:
                # Use Weaviate backend for dense search
                weaviate_results = self._retrieve_with_weaviate_vectors(query_embedding, k)
                return self._convert_retrieval_results_to_index_format(weaviate_results)
            else:
                # Use default FAISS vector index (existing sub-component)
                return self.vector_index.search(query_embedding, k=k)
        except Exception as e:
            logger.warning(f"Enhanced dense search failed, using fallback: {str(e)}")
            # Fallback to base vector index
            return self.vector_index.search(query_embedding, k=k)

    def _get_graph_retrieval_signals(self, query: str, k: int) -> List[RetrievalResult]:
        """Get graph retrieval signals to enhance fusion (architecture compliant)."""
        try:
            # Check if graph retrieval is enabled and available
            if not self.graph_retriever:
                logger.debug("Graph retrieval not available")
                return []
            
            # Get graph-based results as additional signals
            graph_results = self.graph_retriever.retrieve(query, k=k)
            
            # Track analytics if enabled
            if self.graph_analytics:
                self.graph_analytics.track_query(
                    query=query,
                    results_count=len(graph_results),
                    latency_ms=0.0,
                    algorithm_used="graph_modular_integration",
                    success=True
                )
            
            return graph_results
            
        except Exception as e:
            logger.warning(f"Graph retrieval signals failed: {str(e)}")
            # Track failed query
            if self.graph_analytics:
                self.graph_analytics.track_query(
                    query=query,
                    results_count=0,
                    latency_ms=0.0,
                    algorithm_used="graph_modular_integration",
                    success=False
                )
            return []

    def _enhanced_fusion_with_graph(
        self, 
        dense_results: List[Tuple[int, float]], 
        sparse_results: List[Tuple[int, float]], 
        graph_results: List[RetrievalResult]
    ) -> List[Tuple[int, float]]:
        """Enhanced fusion strategy incorporating graph signals (Sub-component 3)."""
        try:
            # First, use existing fusion strategy for dense + sparse (maintains architecture)
            base_fused = self.fusion_strategy.fuse_results(dense_results, sparse_results)
            
            # Now enhance with graph signals if available
            if not graph_results:
                return base_fused
            
            # Convert graph results to index format
            graph_index_results = self._convert_retrieval_results_to_index_format(graph_results)
            
            # Create a score map for efficient lookup
            base_scores = {doc_idx: score for doc_idx, score in base_fused}
            graph_scores = {doc_idx: score for doc_idx, score in graph_index_results}
            
            # Enhanced fusion: combine base fusion with graph signals
            enhanced_results = {}
            
            # Start with base fused results
            for doc_idx, score in base_fused:
                enhanced_results[doc_idx] = score
            
            # Boost scores for documents also found by graph retrieval
            graph_boost = 0.2  # Configurable boost factor
            for doc_idx, graph_score in graph_scores:
                if doc_idx in enhanced_results:
                    # Boost existing documents found by graph
                    enhanced_results[doc_idx] += graph_score * graph_boost
                else:
                    # Add new graph-found documents with weighted score
                    enhanced_results[doc_idx] = graph_score * graph_boost
            
            # Sort by enhanced score and return as list of tuples
            sorted_results = sorted(enhanced_results.items(), key=lambda x: x[1], reverse=True)
            
            return sorted_results
            
        except Exception as e:
            logger.error(f"Enhanced fusion with graph failed: {str(e)}")
            # Fallback to base fusion
            return self.fusion_strategy.fuse_results(dense_results, sparse_results)

    def _enhanced_neural_reranking(self, query: str, fused_results: List[Tuple[int, float]], k: int) -> List[RetrievalResult]:
        """Enhanced reranking with neural capabilities (Sub-component 4)."""
        try:
            # First apply existing reranking if enabled
            if self.reranker.is_enabled() and fused_results:
                # Prepare documents and scores for existing reranker
                top_candidates = fused_results[:k*2]  # Rerank top candidates
                candidate_documents = [self.documents[idx] for idx, _ in top_candidates]
                candidate_scores = [score for _, score in top_candidates]
                
                reranked_results = self.reranker.rerank(query, candidate_documents, candidate_scores)
                
                # Update final results with reranked scores
                reranked_final = []
                for local_idx, reranked_score in reranked_results:
                    if local_idx < len(top_candidates):
                        original_idx = top_candidates[local_idx][0]
                        reranked_final.append((original_idx, reranked_score))
                
                # Add remaining documents that weren't reranked
                reranked_indices = {top_candidates[local_idx][0] for local_idx, _ in reranked_results 
                                   if local_idx < len(top_candidates)}
                for doc_idx, score in fused_results:
                    if doc_idx not in reranked_indices:
                        reranked_final.append((doc_idx, score))
                
                # Sort by final score and limit to k
                reranked_final.sort(key=lambda x: x[1], reverse=True)
                base_final = reranked_final[:k*2]  # Get more for neural reranking
            else:
                # No base reranking, use fused results directly
                base_final = fused_results[:k*2]
            
            # Apply neural reranking if available
            base_retrieval_results = []
            for doc_idx, score in base_final:
                if doc_idx < len(self.documents):
                    document = self.documents[doc_idx]
                    retrieval_result = RetrievalResult(
                        document=document,
                        score=float(score),
                        retrieval_method="advanced_modular_hybrid"
                    )
                    base_retrieval_results.append(retrieval_result)
            
            # Apply neural reranking enhancement
            neural_enhanced_results = self._apply_neural_reranking(query, base_retrieval_results)
            
            return neural_enhanced_results[:k]  # Return final k results
            
        except Exception as e:
            logger.error(f"Enhanced neural reranking failed: {str(e)}")
            # Fallback to basic result conversion
            final_results = []
            for doc_idx, score in fused_results[:k]:
                if doc_idx < len(self.documents):
                    document = self.documents[doc_idx]
                    retrieval_result = RetrievalResult(
                        document=document,
                        score=float(score),
                        retrieval_method="advanced_modular_fallback"
                    )
                    final_results.append(retrieval_result)
            return final_results

    def _retrieve_with_weaviate_vectors(self, query_embedding: np.ndarray, k: int) -> List[RetrievalResult]:
        """Retrieve using Weaviate backend with vector input."""
        try:
            backend = self.backends["weaviate"]
            search_results = backend.search(query_embedding=query_embedding, k=k, query_text=None)
            
            # Convert to RetrievalResult objects
            retrieval_results = []
            for doc_idx, score in search_results:
                if doc_idx < len(self.documents):
                    document = self.documents[doc_idx]
                    retrieval_result = RetrievalResult(
                        document=document,
                        score=float(score),
                        retrieval_method="advanced_weaviate_vector"
                    )
                    retrieval_results.append(retrieval_result)
            
            return retrieval_results
        except Exception as e:
            logger.error(f"Weaviate vector retrieval failed: {str(e)}")
            return []

    def _convert_retrieval_results_to_index_format(self, results: List[RetrievalResult]) -> List[Tuple[int, float]]:
        """Convert RetrievalResult objects to (index, score) tuples."""
        index_results = []
        for result in results:
            # Find document index in self.documents
            try:
                doc_index = next(i for i, doc in enumerate(self.documents) if doc.content == result.document.content)
                index_results.append((doc_index, result.score))
            except StopIteration:
                # Document not found in indexed documents, skip
                continue
        return index_results

    def _retrieve_with_weaviate(
        self, query: str, k: int, backend: WeaviateBackend
    ) -> List[RetrievalResult]:
        """
        Perform retrieval using Weaviate backend.

        Args:
            query: Search query
            k: Number of results
            backend: Weaviate backend instance

        Returns:
            List of retrieval results
        """
        # Generate query embedding
        query_embedding = np.array(self.embedder.embed([query])[0])

        # Perform search (hybrid if supported)
        search_results = backend.search(
            query_embedding=query_embedding,
            k=k,
            query_text=query if backend.supports_hybrid_search() else None,
        )

        # Convert to RetrievalResult objects
        retrieval_results = []
        for doc_idx, score in search_results:
            if doc_idx < len(self.documents):
                document = self.documents[doc_idx]
                retrieval_result = RetrievalResult(
                    document=document,
                    score=float(score),
                    retrieval_method=f"advanced_weaviate_{'hybrid' if backend.supports_hybrid_search() else 'vector'}",
                )
                retrieval_results.append(retrieval_result)

        return retrieval_results

    def _apply_neural_reranking(
        self, query: str, results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        Apply neural reranking to retrieval results (4th stage).

        Args:
            query: Search query
            results: Initial retrieval results

        Returns:
            Reranked results
        """
        # Skip if neural reranking is disabled or not available
        if not self.neural_reranker or not results:
            return results

        try:
            start_time = time.time()

            # Convert RetrievalResults to Documents and scores
            documents = []
            initial_scores = []

            for result in results:
                documents.append(result.document)
                initial_scores.append(result.score)

            # Apply neural reranking
            reranked_indices_scores = self.neural_reranker.rerank(
                query=query, documents=documents, initial_scores=initial_scores
            )

            # Convert back to RetrievalResults with updated scores
            reranked_results = []
            for doc_idx, new_score in reranked_indices_scores:
                if doc_idx < len(results):
                    original_result = results[doc_idx]
                    # Handle metadata gracefully (RetrievalResult may not have metadata)
                    original_metadata = getattr(original_result, "metadata", {})

                    reranked_result = RetrievalResult(
                        document=original_result.document,
                        score=new_score,
                        retrieval_method=f"{original_result.retrieval_method}_neural_reranked",
                    )
                    reranked_results.append(reranked_result)

            # Update advanced stats
            neural_latency = (time.time() - start_time) * 1000
            self.advanced_stats["total_advanced_retrievals"] += 1

            logger.debug(
                f"Neural reranking completed in {neural_latency:.1f}ms, "
                f"processed {len(documents)} documents"
            )

            # Log performance warning if too slow
            if neural_latency > self.advanced_config.neural_reranking.max_latency_ms:
                logger.warning(
                    f"Neural reranking took {neural_latency:.1f}ms, "
                    f"exceeding target of {self.advanced_config.neural_reranking.max_latency_ms}ms"
                )

            return reranked_results

        except Exception as e:
            logger.error(f"Neural reranking failed: {str(e)}")
            # Return original results on failure
            return results

    def index_documents(self, documents: List[Document]) -> None:
        """
        Index documents in all active backends.

        Args:
            documents: List of documents to index
        """
        if not documents:
            raise ValueError("Cannot index empty document list")

        # Call parent method (ModularUnifiedRetriever)
        super().index_documents(documents)

        # Index in graph components if enabled
        if hasattr(self, "graph_retriever") and self.graph_retriever is not None:
            try:
                # Use graph builder to build/update the graph with new documents
                if hasattr(self, "graph_builder") and self.graph_builder is not None:
                    self.graph_builder.build_graph(documents)
                    logger.debug("Documents indexed in graph builder")
                else:
                    logger.debug("Graph builder not available, skipping graph indexing")
            except Exception as e:
                logger.error(f"Failed to index documents in graph builder: {str(e)}")
                # Continue execution - graph indexing failure shouldn't break main indexing

        logger.debug(
            f"Successfully indexed {len(documents)} documents in AdvancedRetriever"
        )

    def migrate_backend(self, target_backend: str) -> Dict[str, Any]:
        """
        Migrate data from current backend to target backend.

        Args:
            target_backend: Name of target backend

        Returns:
            Dictionary with migration results
        """
        if target_backend not in self.backends:
            raise ValueError(f"Target backend '{target_backend}' not available")

        if target_backend == self.active_backend_name:
            return {"success": True, "message": "Already using target backend"}

        logger.info(
            f"Starting migration from {self.active_backend_name} to {target_backend}"
        )

        try:
            if self.active_backend_name == "faiss" and target_backend == "weaviate":
                # FAISS to Weaviate migration
                faiss_backend = self.backends["faiss"]
                weaviate_backend = self.backends["weaviate"]

                migrator = FAISSToWeaviateMigrator(
                    faiss_backend=faiss_backend,
                    weaviate_backend=weaviate_backend,
                    validation_enabled=True,
                )

                result = migrator.migrate(
                    documents=self.documents,
                    preserve_faiss=True,  # Keep FAISS as fallback
                )

                if result["success"]:
                    self.active_backend_name = target_backend
                    self.advanced_stats["migration_count"] += 1
                    logger.info("Migration completed successfully")

                return result

            else:
                return {
                    "success": False,
                    "error": f"Migration from {self.active_backend_name} to {target_backend} not implemented",
                }

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_backend_status(self) -> Dict[str, Any]:
        """
        Get status of all backends.

        Returns:
            Dictionary with backend status information
        """
        status = {
            "active_backend": self.active_backend_name,
            "fallback_backend": self.fallback_backend_name,
            "backends": {},
        }

        for backend_name, backend in self.backends.items():
            try:
                health = backend.health_check()
                info = backend.get_backend_info()

                status["backends"][backend_name] = {
                    "health": health,
                    "info": info,
                    "is_active": backend_name == self.active_backend_name,
                }
            except Exception as e:
                status["backends"][backend_name] = {
                    "error": str(e),
                    "is_active": backend_name == self.active_backend_name,
                }

        return status

    def get_advanced_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics for advanced retriever.

        Returns:
            Dictionary with advanced statistics
        """
        base_stats = super().get_retrieval_stats()

        stats = {
            **base_stats,
            "advanced_stats": self.advanced_stats.copy(),
            "backend_status": self.get_backend_status(),
            "enabled_features": self.advanced_config.get_enabled_features(),
            "analytics": {
                "enabled": self.analytics_enabled,
                "query_count": len(self.query_analytics),
                "latest_queries": (
                    self.query_analytics[-5:] if self.query_analytics else []
                ),
            },
        }

        # Add graph statistics if available
        if self.graph_builder:
            stats["graph_stats"] = self.graph_builder.get_graph_statistics()

        if self.graph_retriever:
            stats["graph_retrieval_stats"] = self.graph_retriever.get_statistics()

        if self.graph_analytics:
            stats["graph_analytics_stats"] = self.graph_analytics.get_statistics()
            stats["graph_report"] = self.graph_analytics.generate_report()

        return stats

    def _check_and_switch_backend(self) -> None:
        """Check backend health and switch if necessary."""
        current_time = time.time()

        # Rate limit health checks
        if (
            current_time - self.advanced_stats["last_health_check"]
            < self.advanced_config.backends.health_check_interval_seconds
        ):
            return

        try:
            active_backend = self.backends[self.active_backend_name]
            health = active_backend.health_check()

            if not health.get("is_healthy", True):
                logger.warning(
                    f"Active backend {self.active_backend_name} unhealthy: {health.get('issues', [])}"
                )
                self._consider_backend_switch(None)

            self.advanced_stats["last_health_check"] = current_time
            self.advanced_stats["backend_health_checks"] += 1

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")

    def _consider_backend_switch(self, error: Optional[Exception]) -> None:
        """Consider switching to fallback backend."""
        if (
            not self.fallback_backend_name
            or self.fallback_backend_name not in self.backends
        ):
            return

        try:
            fallback_backend = self.backends[self.fallback_backend_name]
            fallback_health = fallback_backend.health_check()

            if fallback_health.get("is_healthy", False):
                logger.info(
                    f"Switching from {self.active_backend_name} to {self.fallback_backend_name}"
                )

                # Swap backends
                self.active_backend_name, self.fallback_backend_name = (
                    self.fallback_backend_name,
                    self.active_backend_name,
                )

                self.advanced_stats["backend_switches"] += 1

        except Exception as e:
            logger.error(f"Backend switch consideration failed: {str(e)}")

    def _collect_query_start_analytics(self, query: str, k: int) -> None:
        """Collect analytics at query start."""
        analytics_entry = {
            "timestamp": time.time(),
            "query": query,
            "k": k,
            "backend": self.active_backend_name,
        }

        # Keep only recent entries to prevent memory growth
        max_entries = 1000
        if len(self.query_analytics) >= max_entries:
            self.query_analytics = self.query_analytics[-max_entries // 2 :]

        self.query_analytics.append(analytics_entry)

    def _collect_query_completion_analytics(
        self,
        query: str,
        k: int,
        results: List[RetrievalResult],
        elapsed_time: float,
        method: str,
    ) -> None:
        """Collect analytics at query completion."""
        if self.query_analytics:
            # Update the latest entry
            latest_entry = self.query_analytics[-1]
            update_data = {
                "completion_time": time.time(),
                "elapsed_time": elapsed_time,
                "results_count": len(results),
                "method": method,
                "success": True,
            }
            
            latest_entry.update(update_data)

    def get_configuration(self) -> Dict[str, Any]:
        """
        Get the current configuration of the advanced retriever.

        Returns:
            Dictionary with configuration parameters
        """
        base_config = super().get_configuration()

        return {
            **base_config,
            "advanced_config": self.advanced_config.to_dict(),
            "active_backend": self.active_backend_name,
            "fallback_backend": self.fallback_backend_name,
            "available_backends": list(self.backends.keys()),
        }
