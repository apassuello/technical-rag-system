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
        self.query_analyzer = None  # Epic1 query analyzer
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

            # 4. Initialize Epic1 query analyzer (optional)
            self._init_query_analyzer()

            # 5. Initialize answer generator (optional)
            self._init_answer_generator()

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

    def _init_query_analyzer(self) -> None:
        """Initialize Epic1 query analyzer for ML-based classification."""
        try:
            if 'query_analyzer' not in self.config:
                logger.info("Query analyzer not configured, skipping...")
                return

            analyzer_config = self.config['query_analyzer']
            analyzer_type = analyzer_config.get('type', 'epic1')
            analyzer_params = analyzer_config.get('config', {})

            # Create Epic1 query analyzer
            self.query_analyzer = self.factory.create_query_analyzer(
                analyzer_type,
                config=analyzer_params
            )

            logger.info(f"Query analyzer initialized: {analyzer_type}")

        except Exception as e:
            logger.error(f"Failed to initialize query analyzer: {e}")
            logger.warning("Demo will run without query classification")

    def _init_answer_generator(self) -> None:
        """Initialize answer generator for LLM-based generation."""
        try:
            if 'answer_generator' not in self.config:
                logger.info("Answer generator not configured, skipping...")
                return

            gen_config = self.config['answer_generator']
            gen_type = gen_config.get('type', 'answer_generator')
            gen_params = gen_config.get('config', {})

            # Create answer generator
            self.answer_generator = self.factory.create_generator(
                gen_type,
                **gen_params
            )

            # Set embedder for semantic confidence scoring
            if self.embedder and hasattr(self.answer_generator, 'set_embedder'):
                self.answer_generator.set_embedder(self.embedder)

            logger.info(f"Answer generator initialized: {gen_type}")

        except Exception as e:
            logger.error(f"Failed to initialize answer generator: {e}")
            logger.warning("Demo will run without answer generation")

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

    def query_with_classification(
        self,
        query_text: str,
        strategy: str = "hybrid_rrf",
        top_k: Optional[int] = None,
        use_recommended_model: bool = True
    ) -> Dict[str, Any]:
        """
        Execute RAG query with Epic1 classification and answer generation.

        This method:
        1. Analyzes the query with Epic1QueryAnalyzer (complexity classification)
        2. Retrieves documents with complexity-aware top-k
        3. Generates answer with recommended model

        Args:
            query_text: The query string
            strategy: Retrieval strategy name (from config)
            top_k: Number of documents to retrieve (None = use Epic1 suggestion)
            use_recommended_model: Whether to use Epic1's model recommendation

        Returns:
            Dictionary with results including query analysis, retrieval, and answer
        """
        start_time = time.time()
        result = {
            'query': query_text,
            'strategy': strategy,
            'performance': {},
            'metadata': {}
        }

        try:
            # Step 1: Query Analysis (Epic1)
            query_analysis = None
            epic1_metadata = {}

            if self.query_analyzer:
                analysis_start = time.time()
                try:
                    query_analysis = self.query_analyzer.analyze(query_text)
                    epic1_metadata = query_analysis.metadata.get('epic1_analysis', {})
                    result['performance']['analysis_ms'] = (time.time() - analysis_start) * 1000
                    logger.info(
                        f"Query classified as {epic1_metadata.get('complexity_level', 'unknown')} "
                        f"(confidence: {epic1_metadata.get('complexity_confidence', 0):.2f})"
                    )
                except Exception as e:
                    logger.error(f"Query analysis failed: {e}")
                    query_analysis = None

            # Determine actual top-k (use Epic1 suggestion if available)
            if top_k is None and query_analysis:
                actual_top_k = query_analysis.suggested_k
                result['metadata']['top_k_source'] = 'epic1_suggested'
            elif top_k is not None:
                actual_top_k = top_k
                result['metadata']['top_k_source'] = 'user_specified'
            else:
                actual_top_k = self.config.get('demo_settings', {}).get('default_top_k', 10)
                result['metadata']['top_k_source'] = 'default'

            # Step 2: Retrieval
            retrieval_start = time.time()
            query_result = self.query(
                query_text=query_text,
                strategy=strategy,
                top_k=actual_top_k,
                generate_answer=False
            )
            result['performance']['retrieval_ms'] = (time.time() - retrieval_start) * 1000

            # Copy retrieval results
            result['documents'] = query_result.documents
            result['retrieval_results'] = query_result.retrieval_results
            result['performance'].update(query_result.performance)

            # Step 3: Answer Generation
            if self.answer_generator and query_result.documents:
                generation_start = time.time()
                try:
                    # TODO: Update generator model based on Epic1 recommendation
                    # For now, use default model
                    recommended_model = epic1_metadata.get('recommended_model')
                    if use_recommended_model and recommended_model:
                        logger.info(f"Using Epic1 recommended model: {recommended_model}")
                        # Note: Model switching would require updating LLM client config
                        # This is a future enhancement

                    answer = self.answer_generator.generate(
                        query_text,
                        query_result.documents
                    )

                    result['answer'] = answer.text
                    result['answer_confidence'] = answer.confidence
                    result['answer_metadata'] = answer.metadata
                    result['performance']['generation_ms'] = (time.time() - generation_start) * 1000

                    logger.info(
                        f"Generated answer (confidence: {answer.confidence:.2f}) in "
                        f"{result['performance']['generation_ms']:.1f}ms"
                    )

                except Exception as e:
                    logger.error(f"Answer generation failed: {e}")
                    result['answer'] = None
                    result['answer_error'] = str(e)

            # Step 4: Add Epic1 Analysis Metadata
            if query_analysis and epic1_metadata:
                result['query_analysis'] = {
                    'complexity_level': epic1_metadata.get('complexity_level', 'unknown'),
                    'complexity_score': query_analysis.complexity_score,
                    'complexity_confidence': epic1_metadata.get('complexity_confidence', 0.0),
                    'recommended_model': epic1_metadata.get('recommended_model', 'default'),
                    'model_provider': epic1_metadata.get('model_provider', 'unknown'),
                    'routing_confidence': epic1_metadata.get('routing_confidence', 0.0),
                    'suggested_k': query_analysis.suggested_k,
                    'intent_category': query_analysis.intent_category,
                    'technical_terms': query_analysis.technical_terms,
                    'entities': query_analysis.entities,
                    'cost_estimate': epic1_metadata.get('cost_estimate', 0.0),
                    'latency_estimate': epic1_metadata.get('latency_estimate', 0.0),
                    'full_metadata': epic1_metadata
                }

            # Calculate total time
            result['performance']['total_ms'] = (time.time() - start_time) * 1000
            result['metadata']['has_query_analysis'] = query_analysis is not None
            result['metadata']['has_answer'] = 'answer' in result
            result['metadata']['num_documents'] = len(result.get('documents', []))

            return result

        except Exception as e:
            logger.error(f"Query with classification failed: {e}", exc_info=True)
            result['error'] = str(e)
            result['performance']['total_ms'] = (time.time() - start_time) * 1000
            return result

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
            'query_analyzer': self.query_analyzer is not None,
            'answer_generator': self.answer_generator is not None
        }
