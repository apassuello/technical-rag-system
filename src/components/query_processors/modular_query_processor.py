"""
Modular Query Processor Implementation.

This module implements the main Query Processor orchestrator that coordinates
the complete query workflow through modular sub-components.

Key Features:
- Configurable sub-component architecture
- Complete query workflow orchestration
- Comprehensive error handling and fallbacks
- Performance monitoring and metrics
- Production-ready reliability
"""

import time
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from .base import (
    QueryProcessor, QueryAnalysis, ContextSelection, QueryProcessorConfig,
    QueryProcessorMetrics, validate_config
)
from .analyzers import QueryAnalyzer, NLPAnalyzer, RuleBasedAnalyzer
from .selectors import ContextSelector, MMRSelector, TokenLimitSelector
from .assemblers import ResponseAssembler, StandardAssembler, RichAssembler
from src.core.interfaces import Answer, QueryOptions, Document, Retriever, AnswerGenerator

logger = logging.getLogger(__name__)


class ModularQueryProcessor(QueryProcessor):
    """
    Modular query processor orchestrating the complete query workflow.
    
    This processor implements the QueryProcessor interface while providing
    a modular architecture where analysis, selection, and assembly strategies
    can be configured independently.
    
    Workflow:
    1. Query Analysis - Extract characteristics and optimize parameters
    2. Document Retrieval - Use retriever with optimized parameters  
    3. Context Selection - Choose optimal documents within token limits
    4. Answer Generation - Generate response using selected context
    5. Response Assembly - Format final Answer with metadata
    
    Features:
    - Configuration-driven sub-component selection
    - Comprehensive error handling and fallbacks
    - Performance metrics and monitoring
    - Graceful degradation on component failures
    - Production-ready reliability
    """
    
    def __init__(
        self,
        retriever: Retriever,
        generator: AnswerGenerator,
        analyzer: Optional[QueryAnalyzer] = None,
        selector: Optional[ContextSelector] = None,
        assembler: Optional[ResponseAssembler] = None,
        config: Optional[Union[Dict[str, Any], QueryProcessorConfig]] = None
    ):
        """
        Initialize modular query processor with dependencies and configuration.
        
        Args:
            retriever: Document retriever instance
            generator: Answer generator instance
            analyzer: Query analyzer (will create default if None)
            selector: Context selector (will create default if None)
            assembler: Response assembler (will create default if None)
            config: Configuration dictionary or QueryProcessorConfig
        """
        # Store required dependencies
        self._retriever = retriever
        self._generator = generator
        
        # Parse configuration
        if isinstance(config, QueryProcessorConfig):
            self._config = config
        else:
            config_dict = config or {}
            self._config = self._create_config_from_dict(config_dict)
        
        # Validate configuration
        config_errors = validate_config(self._config.__dict__)
        if config_errors:
            logger.warning(f"Configuration issues found: {config_errors}")
        
        # Initialize sub-components
        self._analyzer = analyzer or self._create_default_analyzer()
        self._selector = selector or self._create_default_selector()
        self._assembler = assembler or self._create_default_assembler()
        
        # Initialize metrics tracking
        self._metrics = QueryProcessorMetrics()
        
        # Health tracking
        self._last_health_check = 0
        self._health_status = {'healthy': True, 'issues': []}
        
        logger.info(f"Initialized ModularQueryProcessor with {self._get_component_summary()}")
    
    def process(self, query: str, options: Optional[QueryOptions] = None) -> Answer:
        """
        Process a query end-to-end and return a complete answer.
        
        Args:
            query: User query string
            options: Optional query processing options
            
        Returns:
            Complete Answer object with text, sources, and metadata
            
        Raises:
            ValueError: If query is empty or options are invalid
            RuntimeError: If processing pipeline fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Parse options
        processed_options = self._parse_query_options(options)
        
        start_time = time.time()
        phase_times = {}
        
        try:
            logger.info(f"Processing query: {query[:100]}...")
            
            # Phase 1: Query Analysis
            phase_start = time.time()
            query_analysis = self._run_query_analysis(query)
            phase_times['analysis'] = time.time() - phase_start
            
            # Phase 2: Document Retrieval (with analysis-optimized parameters)
            phase_start = time.time()
            retrieval_results = self._run_document_retrieval(query, query_analysis, processed_options)
            phase_times['retrieval'] = time.time() - phase_start
            
            # Phase 3: Context Selection
            phase_start = time.time()
            context_selection = self._run_context_selection(query, retrieval_results, processed_options, query_analysis)
            phase_times['selection'] = time.time() - phase_start
            
            # Phase 4: Answer Generation
            phase_start = time.time()
            answer_result = self._run_answer_generation(query, context_selection, processed_options)
            phase_times['generation'] = time.time() - phase_start
            
            # Phase 5: Response Assembly
            phase_start = time.time()
            final_answer = self._run_response_assembly(query, answer_result, context_selection, query_analysis)
            phase_times['assembly'] = time.time() - phase_start
            
            # Record successful processing
            total_time = time.time() - start_time
            self._metrics.record_query(True, total_time, phase_times)
            
            logger.info(f"Query processed successfully in {total_time:.3f}s")
            return final_answer
            
        except Exception as e:
            # Record failed processing
            total_time = time.time() - start_time
            self._metrics.record_query(False, total_time, phase_times)
            
            logger.error(f"Query processing failed after {total_time:.3f}s: {e}")
            
            # Attempt graceful fallback
            if self._config.enable_fallback:
                try:
                    fallback_answer = self._create_fallback_answer(query, str(e))
                    logger.info("Created fallback answer after processing failure")
                    return fallback_answer
                except Exception as fallback_error:
                    logger.error(f"Fallback answer creation also failed: {fallback_error}")
            
            raise RuntimeError(f"Query processing failed: {e}") from e
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze query characteristics without full processing.
        
        Args:
            query: User query string
            
        Returns:
            QueryAnalysis with extracted characteristics
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        return self._run_query_analysis(query)
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of query processor and sub-components.
        
        Returns:
            Dictionary with health information
        """
        current_time = time.time()
        
        # Only check health periodically to avoid overhead
        if current_time - self._last_health_check > 60:  # Check every minute
            self._last_health_check = current_time
            self._health_status = self._perform_health_check()
        
        # Add performance metrics
        health_info = self._health_status.copy()
        health_info['performance_metrics'] = self._metrics.get_stats()
        health_info['last_check'] = self._last_health_check
        
        return health_info
    
    def configure(self, config: QueryProcessorConfig) -> None:
        """
        Configure the query processor and all sub-components.
        
        Args:
            config: Complete configuration object
        """
        self._config = config
        
        # Reconfigure sub-components
        if hasattr(self._analyzer, 'configure'):
            self._analyzer.configure(config.analyzer_config)
        
        if hasattr(self._selector, 'configure'):
            self._selector.configure(config.selector_config)
        
        if hasattr(self._assembler, 'configure'):
            self._assembler.configure(config.assembler_config)
        
        logger.info("Query processor reconfigured successfully")
    
    # Internal workflow methods
    
    def _run_query_analysis(self, query: str) -> QueryAnalysis:
        """Run query analysis phase with error handling."""
        try:
            return self._analyzer.analyze(query)
        except Exception as e:
            logger.warning(f"Query analysis failed, using basic analysis: {e}")
            # Create basic analysis as fallback
            return QueryAnalysis(
                query=query,
                complexity_score=0.5,
                technical_terms=[],
                entities=[],
                intent_category="general",
                suggested_k=self._config.default_k,
                confidence=0.3,
                metadata={'analyzer_fallback': True, 'error': str(e)}
            )
    
    def _run_document_retrieval(
        self, 
        query: str, 
        query_analysis: QueryAnalysis, 
        options: Dict[str, Any]
    ) -> List[Document]:
        """Run document retrieval phase with analysis optimization."""
        try:
            # Use analyzed suggested_k if available, otherwise use options
            retrieval_k = query_analysis.suggested_k if query_analysis.suggested_k > 0 else options['k']
            
            # Call retriever
            results = self._retriever.retrieve(query, retrieval_k)
            
            # Convert RetrievalResult objects to Documents if needed
            if results and hasattr(results[0], 'document'):
                documents = [result.document for result in results]
                # Preserve scores in documents
                for i, result in enumerate(results):
                    if hasattr(result, 'score'):
                        documents[i].score = result.score
                return documents
            else:
                # Already Document objects
                return results
            
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            # Return empty list as fallback
            return []
    
    def _run_context_selection(
        self,
        query: str,
        documents: List[Document],
        options: Dict[str, Any],
        query_analysis: QueryAnalysis
    ) -> ContextSelection:
        """Run context selection phase with error handling."""
        try:
            return self._selector.select(
                query=query,
                documents=documents,
                max_tokens=options['max_tokens'],
                query_analysis=query_analysis
            )
        except Exception as e:
            logger.warning(f"Context selection failed, using simple selection: {e}")
            # Simple fallback selection
            return self._create_fallback_context_selection(documents, options['max_tokens'])
    
    def _run_answer_generation(
        self,
        query: str,
        context: ContextSelection,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run answer generation phase with error handling."""
        try:
            # Generate answer using selected context
            answer = self._generator.generate(query, context.selected_documents)
            
            # Package result with metadata
            return {
                'answer': answer,
                'generation_metadata': {
                    'model': getattr(self._generator, 'model_name', 'unknown'),
                    'provider': getattr(self._generator, 'provider', 'unknown'),
                    'generation_time': getattr(answer, 'generation_time', 0.0) if hasattr(answer, 'generation_time') else 0.0,
                    'temperature': options.get('temperature', 0.7)
                }
            }
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            raise RuntimeError(f"Answer generation failed: {e}") from e
    
    def _run_response_assembly(
        self,
        query: str,
        answer_result: Dict[str, Any],
        context: ContextSelection,
        query_analysis: QueryAnalysis
    ) -> Answer:
        """Run response assembly phase with error handling."""
        try:
            answer = answer_result['answer']
            generation_metadata = answer_result.get('generation_metadata', {})
            
            return self._assembler.assemble(
                query=query,
                answer_text=answer.text,
                context=context,
                confidence=answer.confidence,
                query_analysis=query_analysis,
                generation_metadata=generation_metadata
            )
        except Exception as e:
            logger.warning(f"Response assembly failed, using basic assembly: {e}")
            # Create basic Answer as fallback
            answer = answer_result['answer']
            return Answer(
                text=answer.text,
                sources=context.selected_documents[:3],  # Limit sources
                confidence=answer.confidence,
                metadata={
                    'query': query,
                    'assembler_fallback': True,
                    'error': str(e)
                }
            )
    
    # Utility methods
    
    def _parse_query_options(self, options: Optional[QueryOptions]) -> Dict[str, Any]:
        """Parse and validate query options."""
        if options is None:
            return {
                'k': self._config.default_k,
                'max_tokens': self._config.max_tokens,
                'temperature': 0.7,
                'stream': False,
                'rerank': True
            }
        
        return {
            'k': options.k if options.k > 0 else self._config.default_k,
            'max_tokens': options.max_tokens if options.max_tokens > 0 else self._config.max_tokens,
            'temperature': options.temperature,
            'stream': options.stream,
            'rerank': options.rerank
        }
    
    def _create_config_from_dict(self, config_dict: Dict[str, Any]) -> QueryProcessorConfig:
        """Create QueryProcessorConfig from dictionary."""
        return QueryProcessorConfig(
            analyzer_type=config_dict.get('analyzer_type', 'nlp'),
            analyzer_config=config_dict.get('analyzer_config', {}),
            selector_type=config_dict.get('selector_type', 'mmr'),
            selector_config=config_dict.get('selector_config', {}),
            assembler_type=config_dict.get('assembler_type', 'rich'),
            assembler_config=config_dict.get('assembler_config', {}),
            default_k=config_dict.get('default_k', 5),
            max_tokens=config_dict.get('max_tokens', 2048),
            enable_fallback=config_dict.get('enable_fallback', True),
            timeout_seconds=config_dict.get('timeout_seconds', 30.0)
        )
    
    def _create_default_analyzer(self) -> QueryAnalyzer:
        """Create default query analyzer based on configuration."""
        analyzer_type = self._config.analyzer_type
        
        if analyzer_type == 'nlp':
            return NLPAnalyzer(self._config.analyzer_config)
        elif analyzer_type == 'rule_based':
            return RuleBasedAnalyzer(self._config.analyzer_config)
        else:
            logger.warning(f"Unknown analyzer type {analyzer_type}, using NLP analyzer")
            return NLPAnalyzer()
    
    def _create_default_selector(self) -> ContextSelector:
        """Create default context selector based on configuration."""
        selector_type = self._config.selector_type
        
        if selector_type == 'mmr':
            return MMRSelector(self._config.selector_config)
        elif selector_type == 'token_limit':
            return TokenLimitSelector(self._config.selector_config)
        else:
            logger.warning(f"Unknown selector type {selector_type}, using MMR selector")
            return MMRSelector()
    
    def _create_default_assembler(self) -> ResponseAssembler:
        """Create default response assembler based on configuration."""
        assembler_type = self._config.assembler_type
        
        if assembler_type == 'rich':
            return RichAssembler(self._config.assembler_config)
        elif assembler_type == 'standard':
            return StandardAssembler(self._config.assembler_config)
        else:
            logger.warning(f"Unknown assembler type {assembler_type}, using rich assembler")
            return RichAssembler()
    
    def _create_fallback_context_selection(self, documents: List[Document], max_tokens: int) -> ContextSelection:
        """Create simple fallback context selection."""
        if not documents:
            return ContextSelection(
                selected_documents=[],
                total_tokens=0,
                selection_strategy="fallback",
                metadata={'reason': 'no_documents_available'}
            )
        
        # Simple token-based selection
        selected = []
        total_tokens = 0
        
        for doc in documents[:5]:  # Limit to first 5 documents
            doc_tokens = len(doc.content.split())  # Simple word count estimation
            if total_tokens + doc_tokens <= max_tokens * 0.8:  # 80% safety margin
                selected.append(doc)
                total_tokens += doc_tokens
            else:
                break
        
        return ContextSelection(
            selected_documents=selected,
            total_tokens=total_tokens,
            selection_strategy="fallback",
            metadata={'selection_method': 'simple_token_based'}
        )
    
    def _create_fallback_answer(self, query: str, error_message: str) -> Answer:
        """Create fallback answer when processing fails."""
        return Answer(
            text="I apologize, but I encountered an issue processing your query. Please try rephrasing your question or contact support if the problem persists.",
            sources=[],
            confidence=0.0,
            metadata={
                'query': query,
                'fallback': True,
                'error': error_message,
                'timestamp': time.time()
            }
        )
    
    def _perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of all components."""
        health = {'healthy': True, 'issues': []}
        
        # Check dependencies
        if self._retriever is None:
            health['healthy'] = False
            health['issues'].append('Retriever not available')
        
        if self._generator is None:
            health['healthy'] = False
            health['issues'].append('Generator not available')
        
        # Check sub-components
        components = {
            'analyzer': self._analyzer,
            'selector': self._selector,
            'assembler': self._assembler
        }
        
        for name, component in components.items():
            if component is None:
                health['healthy'] = False
                health['issues'].append(f'{name} not available')
            elif hasattr(component, 'get_health_status'):
                try:
                    component_health = component.get_health_status()
                    if not component_health.get('healthy', True):
                        health['issues'].append(f'{name}: {component_health}')
                except Exception as e:
                    health['issues'].append(f'{name} health check failed: {e}')
        
        return health
    
    def _get_component_summary(self) -> str:
        """Get summary of configured components."""
        return (
            f"analyzer={self._analyzer.__class__.__name__}, "
            f"selector={self._selector.__class__.__name__}, "
            f"assembler={self._assembler.__class__.__name__}"
        )
    
    def get_sub_components(self) -> Dict[str, Any]:
        """
        Get information about sub-components for ComponentFactory logging.
        
        Returns:
            Dictionary with sub-component information
        """
        return {
            'analyzer': {
                'type': self._config.analyzer_type,
                'class': self._analyzer.__class__.__name__,
                'module': self._analyzer.__class__.__module__
            },
            'selector': {
                'type': self._config.selector_type,
                'class': self._selector.__class__.__name__,
                'module': self._selector.__class__.__module__
            },
            'assembler': {
                'type': self._config.assembler_type,
                'class': self._assembler.__class__.__name__,
                'module': self._assembler.__class__.__module__
            }
        }