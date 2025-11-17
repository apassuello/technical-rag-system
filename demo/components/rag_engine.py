"""
RAG Engine - Demo Wrapper for RAG Components

This module provides a simplified interface for the demo application,
wrapping the ComponentFactory and providing easy-to-use methods for
querying the RAG system with different strategies.
"""

import logging
import time
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import yaml

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.component_factory import ComponentFactory
from src.core.config import ConfigManager
from src.core.interfaces import Document, RetrievalResult, Answer

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result of a RAG query with performance metrics."""
    query: str
    answer: Optional[str]
    documents: List[Document]
    retrieval_results: List[RetrievalResult]
    performance: Dict[str, float]
    strategy: str
    metadata: Dict[str, Any]


class RAGEngine:
    """
    RAG Engine wrapper for demo application.

    Provides simplified interface for:
    - Loading components via ComponentFactory
    - Executing queries with different retrieval strategies
    - Collecting performance metrics
    - Managing multiple retrieval configurations
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize RAG engine.

        Args:
            config_path: Path to demo configuration file
        """
        self.config_path = config_path or str(
            Path(__file__).parent.parent / "config" / "demo_config.yaml"
        )

        # Load configuration
        self.config = self._load_config()

        # Initialize core components
        self.factory = ComponentFactory()
        self.embedder = None
        self.retrievers: Dict[str, Any] = {}  # Strategy name -> retriever instance
        self.answer_generator = None

        # Load documents and indices
        self.documents: List[Document] = []
        self.indices_loaded = False

        # Performance tracking
        self.query_history: List[QueryResult] = []

        logger.info(f"RAGEngine initialized with config: {self.config_path}")

    def _load_config(self) -> Dict[str, Any]:
        """Load demo configuration from YAML."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            raise

    def initialize(self) -> bool:
        """
        Initialize all components.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing RAG components...")

            # 1. Initialize embedder
            self._init_embedder()

            # 2. Load documents and indices
            self._load_documents()

            # 3. Initialize retrievers for each strategy
            self._init_retrievers()

            # 4. Initialize answer generator (optional for now)
            # self._init_answer_generator()

            logger.info("RAG Engine initialization complete")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}", exc_info=True)
            return False

    def _init_embedder(self) -> None:
        """Initialize embedder component."""
        try:
            embedder_config = self.config.get('embedder', {})

            # Extract embedder type and configuration
            embedder_type = embedder_config.get('type', 'modular')
            embedder_params = embedder_config.get('config', {})

            # Use ComponentFactory to create embedder with correct API
            self.embedder = self.factory.create_embedder(
                embedder_type,
                **embedder_params
            )

            logger.info("Embedder initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize embedder: {e}")
            raise

    def _load_documents(self) -> None:
        """Load documents from pickle file."""
        try:
            paths = self.config.get('paths', {})
            doc_file = Path(__file__).parent.parent.parent / paths.get(
                'documents_file', 'data/indices/documents.pkl'
            )

            if not doc_file.exists():
                logger.warning(f"Documents file not found: {doc_file}")
                logger.warning("Demo will run with limited functionality")
                return

            with open(doc_file, 'rb') as f:
                self.documents = pickle.load(f)

            self.indices_loaded = True
            logger.info(f"Loaded {len(self.documents)} documents from {doc_file}")

        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
            logger.warning("Demo will run with limited functionality")

    def _init_retrievers(self) -> None:
        """Initialize retrievers for each strategy."""
        try:
            strategies = self.config.get('retriever', {}).get('strategies', {})

            for strategy_name, strategy_config in strategies.items():
                try:
                    # Create retriever with this strategy config
                    # ModularUnifiedRetriever requires embedder + config
                    retriever = self.factory.create_retriever(
                        'modular_unified',
                        embedder=self.embedder,
                        **strategy_config
                    )

                    # Index documents if available
                    if self.indices_loaded and self.documents:
                        retriever.index_documents(self.documents)

                    self.retrievers[strategy_name] = retriever
                    logger.info(f"Initialized retriever for strategy: {strategy_name}")

                except Exception as e:
                    logger.error(f"Failed to initialize retriever for {strategy_name}: {e}")
                    continue

            logger.info(f"Initialized {len(self.retrievers)} retriever strategies")

        except Exception as e:
            logger.error(f"Failed to initialize retrievers: {e}")
            raise

    def query(
        self,
        query_text: str,
        strategy: str = "hybrid_rrf",
        top_k: int = 10,
        generate_answer: bool = False
    ) -> QueryResult:
        """
        Execute a RAG query with specified strategy.

        Args:
            query_text: The query string
            strategy: Retrieval strategy name (from config)
            top_k: Number of documents to retrieve
            generate_answer: Whether to generate an answer (not implemented yet)

        Returns:
            QueryResult with documents and performance metrics
        """
        start_time = time.time()
        performance = {}

        try:
            # 1. Embed query
            embed_start = time.time()
            query_embedding = self.embedder.embed_query(query_text)
            performance['embedding_ms'] = (time.time() - embed_start) * 1000

            # 2. Retrieve documents
            retrieval_start = time.time()
            retriever = self.retrievers.get(strategy)

            if not retriever:
                raise ValueError(f"Unknown strategy: {strategy}")

            retrieval_results = retriever.retrieve(
                query_text,
                top_k=top_k
            )
            performance['retrieval_ms'] = (time.time() - retrieval_start) * 1000

            # 3. Extract documents from results
            documents = [result.document for result in retrieval_results]

            # 4. Generate answer (placeholder for now)
            answer = None
            if generate_answer:
                # TODO: Implement answer generation
                answer = "Answer generation not yet implemented in demo"

            # Calculate total time
            performance['total_ms'] = (time.time() - start_time) * 1000

            # Create result
            result = QueryResult(
                query=query_text,
                answer=answer,
                documents=documents,
                retrieval_results=retrieval_results,
                performance=performance,
                strategy=strategy,
                metadata={
                    'top_k': top_k,
                    'num_results': len(documents),
                    'strategy_config': self.config['retriever']['strategies'][strategy]['name']
                }
            )

            # Store in history
            self.query_history.append(result)

            return result

        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)

            # Return empty result with error
            return QueryResult(
                query=query_text,
                answer=None,
                documents=[],
                retrieval_results=[],
                performance={'total_ms': (time.time() - start_time) * 1000},
                strategy=strategy,
                metadata={'error': str(e)}
            )

    def compare_strategies(
        self,
        query_text: str,
        strategies: Optional[List[str]] = None,
        top_k: int = 10
    ) -> Dict[str, QueryResult]:
        """
        Run the same query through multiple strategies for comparison.

        Args:
            query_text: The query string
            strategies: List of strategy names (defaults to all available)
            top_k: Number of documents to retrieve

        Returns:
            Dictionary mapping strategy name to QueryResult
        """
        if strategies is None:
            strategies = list(self.retrievers.keys())

        results = {}

        for strategy in strategies:
            if strategy in self.retrievers:
                results[strategy] = self.query(
                    query_text=query_text,
                    strategy=strategy,
                    top_k=top_k
                )
            else:
                logger.warning(f"Strategy not available: {strategy}")

        return results

    def get_available_strategies(self) -> List[str]:
        """Get list of available retrieval strategies."""
        return list(self.retrievers.keys())

    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            'total_documents': len(self.documents),
            'total_queries': len(self.query_history),
            'available_strategies': len(self.retrievers),
            'indices_loaded': self.indices_loaded,
            'avg_query_time_ms': (
                sum(q.performance.get('total_ms', 0) for q in self.query_history) /
                len(self.query_history)
            ) if self.query_history else 0,
            **self.config.get('demo', {}).get('stats', {})
        }

    def get_recent_queries(self, limit: int = 10) -> List[QueryResult]:
        """Get recent query history."""
        return self.query_history[-limit:]

    def get_component_health(self) -> Dict[str, bool]:
        """Get health status of components."""
        return {
            'embedder': self.embedder is not None,
            'retrievers': len(self.retrievers) > 0,
            'documents': self.indices_loaded,
            'answer_generator': self.answer_generator is not None
        }
