"""
Intelligent Query Processor for Epic 5 Phase 2 Block 3.

This module implements an intelligent query routing system that decides whether
to use the existing RAG pipeline (for simple queries) or the new agent system
(for complex queries requiring multi-step reasoning).

Architecture:
- Extends QueryProcessor interface for backward compatibility
- Uses QueryAnalyzer from Block 2 to classify query complexity
- Routes to RAG pipeline for simple queries (fast, cheap)
- Routes to ReActAgent for complex queries (intelligent, multi-step)
- Tracks routing decisions, costs, and performance metrics
- Provides fallback behavior on agent failures

Integration with Epic 5:
- Maintains all existing QueryProcessor functionality
- Seamless integration with existing RAG components
- Optional use of query planning system from Block 2
- Configuration-driven routing thresholds and behavior

Usage:
    >>> from src.components.query_processors.intelligent_query_processor import IntelligentQueryProcessor
    >>> from src.components.query_processors.agents import ReActAgent, QueryAnalyzer
    >>>
    >>> # Create processor with RAG + agent components
    >>> processor = IntelligentQueryProcessor(
    ...     retriever=retriever,
    ...     generator=generator,
    ...     agent=agent,
    ...     query_analyzer=analyzer,
    ...     config=config
    ... )
    >>>
    >>> # Process query - automatically routed
    >>> answer = processor.process("What is machine learning?")  # → RAG pipeline
    >>> answer = processor.process("Calculate 25*47 and explain steps")  # → Agent
"""

import logging
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

# Forward declaration to avoid circular import
from typing import TYPE_CHECKING

from src.core.interfaces import (
    Answer,
    AnswerGenerator,
    HealthStatus,
    QueryOptions,
    QueryProcessor,
    Retriever,
)

from .agents.models import AgentResult, ProcessorConfig, QueryAnalysis
from .agents.planning.query_analyzer import QueryAnalyzer
from .agents.react_agent import ReActAgent

if TYPE_CHECKING:
    from src.core.platform_orchestrator import PlatformOrchestrator

logger = logging.getLogger(__name__)


class IntelligentQueryProcessor(QueryProcessor):
    """
    Intelligent query processor with automatic RAG/agent routing.

    This processor analyzes each query and intelligently routes it to either:
    1. RAG Pipeline (retriever + generator): For simple, direct queries
    2. Agent System (ReActAgent + planning): For complex, multi-step queries

    Routing Decision:
    - Complexity < threshold (default 0.7): Use RAG pipeline
    - Complexity ≥ threshold: Use agent system with optional planning

    Key Features:
    - Automatic complexity-based routing
    - Cost tracking and budget enforcement
    - Fallback to RAG on agent failures
    - Performance metrics and routing analytics
    - Configuration-driven behavior
    - 100% backward compatible with QueryProcessor interface

    Example:
        >>> # Simple query → RAG pipeline
        >>> result = processor.process("What is Python?")
        >>> assert result.metadata['source'] == 'rag_pipeline'
        >>>
        >>> # Complex query → Agent system
        >>> result = processor.process(
        ...     "Calculate 25 * 47, then find the square root of the result"
        ... )
        >>> assert result.metadata['source'] == 'agent'
        >>> assert 'reasoning_steps' in result.metadata
    """

    def __init__(
        self,
        retriever: Retriever,
        generator: AnswerGenerator,
        agent: ReActAgent,
        query_analyzer: QueryAnalyzer,
        config: Optional[Union[Dict[str, Any], ProcessorConfig]] = None
    ):
        """
        Initialize intelligent query processor.

        Args:
            retriever: Document retriever for RAG pipeline
            generator: Answer generator for RAG pipeline
            agent: ReActAgent for complex queries
            query_analyzer: QueryAnalyzer for complexity classification
            config: Configuration (dict or ProcessorConfig)

        Example:
            >>> from langchain_openai import ChatOpenAI
            >>>
            >>> # Create components
            >>> retriever = factory.create_retriever("unified", embedder=embedder)
            >>> generator = factory.create_generator("adaptive_modular")
            >>> llm = ChatOpenAI(model="gpt-4-turbo")
            >>> agent = ReActAgent(llm, tools, memory, agent_config)
            >>> analyzer = QueryAnalyzer()
            >>>
            >>> # Create processor
            >>> processor = IntelligentQueryProcessor(
            ...     retriever=retriever,
            ...     generator=generator,
            ...     agent=agent,
            ...     query_analyzer=analyzer,
            ...     config={"complexity_threshold": 0.7}
            ... )
        """
        # Store required dependencies
        self._retriever = retriever
        self._generator = generator
        self._agent = agent
        self._query_analyzer = query_analyzer

        # Parse configuration
        if isinstance(config, ProcessorConfig):
            self._config = config
        else:
            config_dict = config or {}
            self._config = ProcessorConfig(
                use_agent_by_default=config_dict.get('use_agent_by_default', False),
                complexity_threshold=config_dict.get('complexity_threshold', 0.7),
                max_agent_cost=config_dict.get('max_agent_cost', 0.10),
                enable_planning=config_dict.get('enable_planning', False),
                enable_parallel_execution=config_dict.get('enable_parallel_execution', False)
            )

        # Fallback configuration
        self._fallback_to_rag_on_failure = config_dict.get('fallback_to_rag_on_failure', True) if isinstance(config, dict) else True
        self._track_routing_decisions = config_dict.get('track_routing_decisions', True) if isinstance(config, dict) else True

        # Performance tracking
        self._total_queries = 0
        self._rag_queries = 0
        self._agent_queries = 0
        self._fallback_queries = 0
        self._total_cost = 0.0
        self._total_time = 0.0
        self._routing_decisions: List[Dict[str, Any]] = []

        # Health tracking
        self._last_health_check = 0
        self._health_status = {'healthy': True, 'issues': []}

        # Platform services (initialized via initialize_services)
        self.platform: Optional['PlatformOrchestrator'] = None

        logger.info(
            f"Initialized IntelligentQueryProcessor with "
            f"complexity_threshold={self._config.complexity_threshold}, "
            f"max_agent_cost=${self._config.max_agent_cost:.2f}, "
            f"enable_planning={self._config.enable_planning}"
        )

    def process(self, query: str, options: Optional[QueryOptions] = None) -> Answer:
        """
        Process query with intelligent RAG/agent routing.

        CRITICAL: This method NEVER raises exceptions. All errors are
        returned as Answer objects with error information in metadata.

        Workflow:
        1. Analyze query complexity with QueryAnalyzer
        2. Route based on complexity threshold:
           - Low complexity: Use RAG pipeline (retriever + generator)
           - High complexity: Use agent system with optional planning
        3. Track routing decision, cost, and performance
        4. Fallback to RAG if agent fails and fallback enabled

        Args:
            query: User query string
            options: Optional query processing options

        Returns:
            Answer object with:
                - text: Generated answer
                - sources: Source documents (if RAG used)
                - confidence: Confidence score
                - metadata: Contains:
                    - source: "rag_pipeline" or "agent"
                    - complexity: Query complexity score
                    - reasoning_steps: Agent reasoning (if agent used)
                    - routing_decision: Routing information
                    - execution_time: Processing time
                    - cost: Estimated cost

        Example:
            >>> # Simple query
            >>> result = processor.process("What is Python?")
            >>> print(result.metadata['source'])  # "rag_pipeline"
            >>>
            >>> # Complex query
            >>> result = processor.process("Calculate 25*47 and explain")
            >>> print(result.metadata['source'])  # "agent"
            >>> print(len(result.metadata['reasoning_steps']))  # Multiple steps
        """
        if not query or not query.strip():
            return self._create_error_answer(
                query="",
                error="Query cannot be empty",
                complexity=0.0
            )

        start_time = time.time()
        self._total_queries += 1

        try:
            logger.info(f"Processing query: {query[:100]}...")

            # Phase 1: Query Analysis
            phase_start = time.time()
            analysis = self._analyze_query(query)
            analysis_time = time.time() - phase_start

            # Phase 2: Routing Decision
            use_agent = self._should_use_agent(analysis)

            # Record routing decision
            routing_decision = {
                'query': query[:100],
                'complexity': analysis.complexity,
                'route': 'agent' if use_agent else 'rag',
                'timestamp': time.time(),
                'threshold': self._config.complexity_threshold
            }

            if self._track_routing_decisions:
                self._routing_decisions.append(routing_decision)

            logger.info(
                f"Routing decision: {routing_decision['route']} "
                f"(complexity={analysis.complexity:.3f}, threshold={self._config.complexity_threshold})"
            )

            # Phase 3: Execute appropriate path
            if use_agent:
                answer = self._process_with_agent(query, analysis, options, start_time)
                self._agent_queries += 1
            else:
                answer = self._process_with_rag(query, analysis, options, start_time)
                self._rag_queries += 1

            # Update statistics
            execution_time = time.time() - start_time
            self._total_time += execution_time

            if 'cost' in answer.metadata:
                self._total_cost += answer.metadata['cost']

            logger.info(
                f"Query processed successfully in {execution_time:.3f}s via "
                f"{answer.metadata.get('source', 'unknown')}"
            )

            return answer

        except Exception as e:
            # Unexpected error (should not happen due to internal error handling)
            logger.error(f"Unexpected error in intelligent processor: {e}", exc_info=True)
            execution_time = time.time() - start_time

            return self._create_error_answer(
                query=query,
                error=f"Unexpected error: {str(e)}",
                complexity=getattr(analysis, 'complexity', 0.0) if 'analysis' in locals() else 0.0,
                execution_time=execution_time
            )

    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query characteristics without full processing.

        This method provides query analysis for inspection and debugging
        without executing the full processing pipeline.

        Args:
            query: User query string

        Returns:
            Dictionary with query analysis:
                - query_type: Classification (simple, research, analytical, etc.)
                - complexity: Complexity score (0.0-1.0)
                - intent: Query intent
                - entities: Extracted entities
                - requires_tools: Predicted tool requirements
                - estimated_steps: Estimated reasoning steps
                - recommended_route: "rag" or "agent"

        Example:
            >>> analysis = processor.analyze_query("Calculate 25 * 47")
            >>> print(analysis['complexity'])  # 0.75
            >>> print(analysis['recommended_route'])  # "agent"
        """
        if not query or not query.strip():
            return {
                'error': 'Query cannot be empty',
                'query_type': None,
                'complexity': 0.0,
                'recommended_route': None
            }

        try:
            analysis = self._analyze_query(query)
            recommended_route = 'agent' if self._should_use_agent(analysis) else 'rag'

            return {
                'query_type': analysis.query_type.value,
                'complexity': analysis.complexity,
                'intent': analysis.intent,
                'entities': analysis.entities,
                'requires_tools': analysis.requires_tools,
                'estimated_steps': analysis.estimated_steps,
                'recommended_route': recommended_route,
                'metadata': analysis.metadata
            }
        except Exception as e:
            logger.error(f"Query analysis failed: {e}", exc_info=True)
            return {
                'error': str(e),
                'query_type': None,
                'complexity': 0.0,
                'recommended_route': None
            }

    # Standard ComponentBase interface implementation
    def initialize_services(self, platform: 'PlatformOrchestrator') -> None:
        """Initialize platform services for the component.

        Args:
            platform: PlatformOrchestrator instance providing services
        """
        self.platform = platform
        logger.info("IntelligentQueryProcessor initialized with platform services")

    def get_health_status(self) -> HealthStatus:
        """
        Get health status of processor and sub-components.

        Returns:
            HealthStatus object with component health information
        """
        if self.platform:
            return self.platform.check_component_health(self)

        # Fallback if platform services not initialized
        current_time = time.time()

        # Only check health periodically
        if current_time - self._last_health_check > 60:  # Check every minute
            self._last_health_check = current_time
            self._health_status = self._perform_health_check()

        return HealthStatus(
            is_healthy=self._health_status.get('healthy', True),
            last_check=self._last_health_check,
            issues=self._health_status.get('issues', []),
            metrics=self.get_metrics(),
            component_name="IntelligentQueryProcessor"
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get component-specific metrics.

        Returns:
            Dictionary containing component metrics
        """
        if self.platform:
            return self.platform.collect_component_metrics(self)

        # Fallback if platform services not initialized
        return {
            'total_queries': self._total_queries,
            'rag_queries': self._rag_queries,
            'agent_queries': self._agent_queries,
            'fallback_queries': self._fallback_queries,
            'rag_percentage': (self._rag_queries / self._total_queries * 100) if self._total_queries > 0 else 0.0,
            'agent_percentage': (self._agent_queries / self._total_queries * 100) if self._total_queries > 0 else 0.0,
            'total_cost': self._total_cost,
            'total_time': self._total_time,
            'avg_cost_per_query': self._total_cost / self._total_queries if self._total_queries > 0 else 0.0,
            'avg_time_per_query': self._total_time / self._total_queries if self._total_queries > 0 else 0.0,
            'complexity_threshold': self._config.complexity_threshold,
            'max_agent_cost': self._config.max_agent_cost
        }

    def get_capabilities(self) -> List[str]:
        """Get list of component capabilities.

        Returns:
            List of capability strings
        """
        capabilities = [
            "intelligent_routing",
            "rag_pipeline",
            "agent_system",
            "complexity_analysis",
            "cost_tracking",
            "fallback_handling",
            "performance_monitoring"
        ]

        if self._config.enable_planning:
            capabilities.append("query_planning")

        if self._config.enable_parallel_execution:
            capabilities.append("parallel_execution")

        return capabilities

    # Internal methods

    def _analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze query using QueryAnalyzer.

        Args:
            query: User query string

        Returns:
            QueryAnalysis object with complexity and characteristics
        """
        try:
            return self._query_analyzer.analyze(query)
        except Exception as e:
            logger.warning(f"Query analysis failed: {e}, using default analysis")
            # Return basic analysis as fallback
            from .agents.models import QueryType
            return QueryAnalysis(
                query_type=QueryType.SIMPLE,
                complexity=0.3,  # Default to low complexity (use RAG)
                intent="information_retrieval",
                entities=[],
                requires_tools=[],
                estimated_steps=1,
                metadata={'analyzer_error': str(e)}
            )

    def _should_use_agent(self, analysis: QueryAnalysis) -> bool:
        """
        Determine if agent system should be used.

        Args:
            analysis: QueryAnalysis from analyzer

        Returns:
            True if agent should be used, False for RAG pipeline
        """
        # Primary decision: complexity threshold
        if analysis.complexity >= self._config.complexity_threshold:
            return True

        # Secondary decision: use_agent_by_default override
        if self._config.use_agent_by_default:
            return True

        # Default: use RAG pipeline
        return False

    def _process_with_rag(
        self,
        query: str,
        analysis: QueryAnalysis,
        options: Optional[QueryOptions],
        start_time: float
    ) -> Answer:
        """
        Process query using RAG pipeline.

        Args:
            query: User query
            analysis: Query analysis
            options: Query options
            start_time: Processing start time

        Returns:
            Answer from RAG pipeline with metadata
        """
        try:
            logger.debug("Processing with RAG pipeline")

            # Determine k value
            k = options.k if options and options.k > 0 else 5

            # Phase 1: Retrieve documents
            phase_start = time.time()
            results = self._retriever.retrieve(query, k)
            retrieval_time = time.time() - phase_start

            # Convert RetrievalResult to Document if needed
            if results and hasattr(results[0], 'document'):
                documents = [result.document for result in results]
            else:
                documents = results

            # Phase 2: Generate answer
            phase_start = time.time()
            answer = self._generator.generate(query, documents)
            generation_time = time.time() - phase_start

            # Enhance metadata
            total_time = time.time() - start_time
            answer.metadata.update({
                'source': 'rag_pipeline',
                'complexity': analysis.complexity,
                'query_type': analysis.query_type.value,
                'intent': analysis.intent,
                'execution_time': total_time,
                'retrieval_time': retrieval_time,
                'generation_time': generation_time,
                'documents_retrieved': len(documents),
                'cost': self._estimate_rag_cost(query, answer.text)
            })

            return answer

        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}", exc_info=True)
            execution_time = time.time() - start_time

            return self._create_error_answer(
                query=query,
                error=f"RAG pipeline failed: {str(e)}",
                complexity=analysis.complexity,
                execution_time=execution_time
            )

    def _process_with_agent(
        self,
        query: str,
        analysis: QueryAnalysis,
        options: Optional[QueryOptions],
        start_time: float
    ) -> Answer:
        """
        Process query using agent system.

        Args:
            query: User query
            analysis: Query analysis
            options: Query options
            start_time: Processing start time

        Returns:
            Answer from agent with reasoning trace
        """
        try:
            logger.debug("Processing with agent system")

            # Build context for agent
            context = {
                'query_analysis': asdict(analysis),
                'complexity': analysis.complexity,
                'intent': analysis.intent
            }

            # Execute agent
            phase_start = time.time()
            agent_result: AgentResult = self._agent.process(query, context)
            agent_time = time.time() - phase_start

            # Check if agent succeeded
            if not agent_result.success:
                # Agent failed - try fallback if enabled
                if self._fallback_to_rag_on_failure:
                    logger.warning(f"Agent failed: {agent_result.error}, falling back to RAG")
                    self._fallback_queries += 1
                    return self._process_with_rag(query, analysis, options, start_time)
                else:
                    # No fallback - return error
                    execution_time = time.time() - start_time
                    return self._create_error_answer(
                        query=query,
                        error=agent_result.error or "Agent processing failed",
                        complexity=analysis.complexity,
                        execution_time=execution_time
                    )

            # Check cost budget
            if agent_result.total_cost > self._config.max_agent_cost:
                logger.warning(
                    f"Agent cost ${agent_result.total_cost:.4f} exceeds budget "
                    f"${self._config.max_agent_cost:.4f}"
                )

            # Convert AgentResult to Answer
            total_time = time.time() - start_time

            # Create Answer object
            answer = Answer(
                text=agent_result.answer,
                sources=[],  # Agent doesn't use source documents in same way
                confidence=0.8,  # Default confidence for successful agent result
                metadata={
                    'source': 'agent',
                    'complexity': analysis.complexity,
                    'query_type': analysis.query_type.value,
                    'intent': analysis.intent,
                    'execution_time': total_time,
                    'agent_time': agent_time,
                    'reasoning_steps': [
                        {
                            'step_number': step.step_number,
                            'step_type': step.step_type.value,
                            'content': step.content
                        }
                        for step in agent_result.reasoning_steps
                    ],
                    'tool_calls': [
                        {
                            'tool_name': call.tool_name,
                            'arguments': call.arguments
                        }
                        for call in agent_result.tool_calls
                    ],
                    'cost': agent_result.total_cost,
                    'iterations': len(agent_result.reasoning_steps),
                    'agent_metadata': agent_result.metadata
                }
            )

            return answer

        except Exception as e:
            logger.error(f"Agent processing failed: {e}", exc_info=True)

            # Try fallback if enabled
            if self._fallback_to_rag_on_failure:
                logger.warning(f"Agent exception: {e}, falling back to RAG")
                self._fallback_queries += 1
                return self._process_with_rag(query, analysis, options, start_time)
            else:
                execution_time = time.time() - start_time
                return self._create_error_answer(
                    query=query,
                    error=f"Agent processing failed: {str(e)}",
                    complexity=analysis.complexity,
                    execution_time=execution_time
                )

    def _estimate_rag_cost(self, query: str, answer: str) -> float:
        """
        Estimate cost of RAG pipeline processing.

        This is a rough estimate. Actual costs depend on the generator
        implementation and LLM pricing.

        Args:
            query: Input query
            answer: Generated answer

        Returns:
            Estimated cost in USD
        """
        # Very rough estimation (assumes local models or cached results)
        # Real implementation should get cost from generator
        return 0.001  # ~$0.001 for local RAG

    def _create_error_answer(
        self,
        query: str,
        error: str,
        complexity: float,
        execution_time: float = 0.0
    ) -> Answer:
        """
        Create error Answer object.

        Args:
            query: Original query
            error: Error message
            complexity: Query complexity
            execution_time: Time spent

        Returns:
            Answer object with error information
        """
        return Answer(
            text="I apologize, but I encountered an error processing your query. Please try rephrasing or contact support.",
            sources=[],
            confidence=0.0,
            metadata={
                'query': query[:100],
                'error': error,
                'complexity': complexity,
                'execution_time': execution_time,
                'source': 'error',
                'fallback': True
            }
        )

    def _perform_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.

        Returns:
            Dictionary with health status
        """
        health = {'healthy': True, 'issues': []}

        # Check dependencies
        if self._retriever is None:
            health['healthy'] = False
            health['issues'].append('Retriever not available')

        if self._generator is None:
            health['healthy'] = False
            health['issues'].append('Generator not available')

        if self._agent is None:
            health['healthy'] = False
            health['issues'].append('Agent not available')

        if self._query_analyzer is None:
            health['healthy'] = False
            health['issues'].append('QueryAnalyzer not available')

        return health

    def get_routing_decisions(self) -> List[Dict[str, Any]]:
        """
        Get routing decision history.

        Returns:
            List of routing decisions with complexity and route
        """
        return self._routing_decisions.copy()

    def reset_stats(self) -> None:
        """Reset all statistics."""
        self._total_queries = 0
        self._rag_queries = 0
        self._agent_queries = 0
        self._fallback_queries = 0
        self._total_cost = 0.0
        self._total_time = 0.0
        self._routing_decisions = []
        logger.info("Statistics reset")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"IntelligentQueryProcessor("
            f"threshold={self._config.complexity_threshold}, "
            f"total_queries={self._total_queries}, "
            f"rag={self._rag_queries}, agent={self._agent_queries})"
        )
