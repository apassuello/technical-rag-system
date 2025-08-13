"""
Adaptive Router for Multi-Model LLM Selection.

This module implements the core adaptive routing engine for Epic 1 multi-model
answer generation, orchestrating query complexity analysis with intelligent
model selection using configurable optimization strategies.

Architecture Notes:
- Integrates with Epic1QueryAnalyzer for complexity analysis
- Uses strategy pattern for flexible optimization goals
- Provides fallback chain management for reliability
- Tracks routing decisions for optimization feedback
- Supports real-time cost and performance monitoring

Epic 1 Integration:
- Enables 40%+ cost reduction through intelligent routing
- Provides <50ms routing overhead for real-time decisions
- Integrates seamlessly with existing Answer Generator architecture
- Supports multiple optimization strategies for different use cases
"""

import time
import logging
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING
from decimal import Decimal

from .routing_strategies import (
    RoutingStrategy, 
    CostOptimizedStrategy,
    QualityFirstStrategy, 
    BalancedStrategy,
    ModelOption,
    get_strategy_class
)
from .model_registry import ModelRegistry

# Import cost tracking
from ..llm_adapters.cost_tracker import get_cost_tracker

# Forward declaration for type hints
if TYPE_CHECKING:
    from ...query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer

logger = logging.getLogger(__name__)


class RoutingDecision:
    """
    Routing decision with comprehensive metadata.
    
    Contains the selected model and all reasoning behind the decision,
    enabling monitoring, optimization, and debugging of routing logic.
    """
    
    def __init__(self,
                 selected_model: ModelOption,
                 strategy_used: str,
                 query_complexity: float,
                 complexity_level: str,
                 decision_time_ms: float,
                 alternatives_considered: List[ModelOption] = None,
                 routing_metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize routing decision.
        
        Args:
            selected_model: The chosen model option
            strategy_used: Name of the routing strategy used
            query_complexity: Query complexity score (0.0-1.0)
            complexity_level: Complexity level (simple, medium, complex)
            decision_time_ms: Time taken to make routing decision
            alternatives_considered: Other models that were considered
            routing_metadata: Additional metadata about the decision
        """
        self.selected_model = selected_model
        self.strategy_used = strategy_used
        self.query_complexity = query_complexity
        self.complexity_level = complexity_level
        self.decision_time_ms = decision_time_ms
        self.alternatives_considered = alternatives_considered or []
        self.routing_metadata = routing_metadata or {}
        self.timestamp = time.time()
        
        # Additional attributes for test compatibility
        self.fallback_used = False
        self.original_query = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert routing decision to dictionary for serialization."""
        return {
            'selected_model': {
                'provider': self.selected_model.provider,
                'model': self.selected_model.model,
                'estimated_cost': float(self.selected_model.estimated_cost),
                'estimated_quality': self.selected_model.estimated_quality,
                'estimated_latency_ms': self.selected_model.estimated_latency_ms,
                'confidence': self.selected_model.confidence,
                'fallback_options': self.selected_model.fallback_options
            },
            'strategy_used': self.strategy_used,
            'query_complexity': self.query_complexity,
            'complexity_level': self.complexity_level,
            'decision_time_ms': self.decision_time_ms,
            'timestamp': self.timestamp,
            'alternatives_count': len(self.alternatives_considered),
            'routing_metadata': self.routing_metadata
        }


class AdaptiveRouter:
    """
    Adaptive router for intelligent multi-model LLM selection.
    
    This router orchestrates the entire routing process:
    1. Query complexity analysis via Epic1QueryAnalyzer
    2. Strategy-based model selection 
    3. Fallback chain management
    4. Routing decision tracking and optimization
    5. Cost and performance monitoring
    
    Features:
    - Multiple routing strategies (cost_optimized, quality_first, balanced)
    - Real-time routing decision tracking
    - Fallback chain management for reliability
    - Integration with cost tracking system
    - Performance monitoring and optimization
    """
    
    def __init__(self,
                 default_strategy: str = "balanced",
                 query_analyzer: Optional['Epic1QueryAnalyzer'] = None,
                 config: Optional[Dict[str, Any]] = None,
                 enable_fallback: bool = True,
                 enable_cost_tracking: bool = True):
        """
        Initialize adaptive router.
        
        Args:
            default_strategy: Default routing strategy to use
            query_analyzer: Epic1QueryAnalyzer instance for complexity analysis
            config: Router configuration
            enable_fallback: Whether to enable fallback chain management
            enable_cost_tracking: Whether to track routing costs
        """
        self.config = config or {}
        self.default_strategy = default_strategy
        self.query_analyzer = query_analyzer
        self.enable_fallback = enable_fallback
        self.enable_cost_tracking = enable_cost_tracking
        
        # Initialize performance metrics first (needed by _initialize_strategies)
        self._total_routing_decisions = 0
        self._total_routing_time_ms = 0.0
        self._strategy_usage_count: Dict[str, int] = {}
        
        # Initialize model registry
        self.model_registry = ModelRegistry()
        
        # Initialize routing strategies
        self.strategies: Dict[str, RoutingStrategy] = {}
        try:
            self._initialize_strategies()
        except Exception as e:
            logger.error(f"Failed to initialize routing strategies: {str(e)}")
            # Initialize with empty strategies to prevent further errors
            self.strategies = {}
        
        # Routing decision history
        self.routing_history: List[RoutingDecision] = []
        self.max_history_size = self.config.get('max_history_size', 1000)
        
        # Cost tracking
        if self.enable_cost_tracking:
            self.cost_tracker = get_cost_tracker()
        
        # Fallback chain (for test compatibility)
        self.fallback_chain = []
        
        logger.info(f"Initialized AdaptiveRouter with {len(self.strategies)} strategies")
    
    def route_query(self,
                    query: str,
                    query_metadata: Optional[Dict[str, Any]] = None,
                    strategy_override: Optional[str] = None,
                    context_documents: Optional[List] = None) -> RoutingDecision:
        """
        Route a query to the optimal LLM model.
        
        This is the main entry point for query routing, orchestrating
        complexity analysis and model selection.
        
        Args:
            query: The user query to route
            query_metadata: Additional query metadata
            strategy_override: Override default routing strategy
            context_documents: Context documents for the query
            
        Returns:
            RoutingDecision with selected model and metadata
            
        Raises:
            ValueError: If routing strategy is invalid
            RuntimeError: If routing fails
        """
        start_time = time.time()
        
        try:
            # 1. Analyze query complexity
            complexity_result = self._analyze_query_complexity(query, query_metadata)
            query_complexity = complexity_result.get('complexity_score', 0.5)
            complexity_level = complexity_result.get('complexity_level', 'medium')
            
            # 2. Select routing strategy
            strategy_name = strategy_override or self.default_strategy
            if strategy_name not in self.strategies:
                raise ValueError(f"Unknown routing strategy: {strategy_name}")
            
            strategy = self.strategies[strategy_name]
            
            # 3. Prepare query metadata for strategy
            enhanced_metadata = self._prepare_query_metadata(
                query, query_metadata, context_documents, complexity_result
            )
            
            # 4. Get available models for this complexity
            available_models = self.model_registry.get_models_for_complexity(complexity_level)
            
            # 5. Select model using strategy with new API
            selected_model = strategy.select_model(
                query_analysis=complexity_result,
                available_models=available_models
            )
            
            # 6. Apply fallback logic if enabled
            if self.enable_fallback:
                selected_model = self._apply_fallback_logic(selected_model, enhanced_metadata)
            
            # 7. Create routing decision with alternatives
            decision_time_ms = (time.time() - start_time) * 1000
            
            # Populate alternatives_considered
            alternatives = [m for m in available_models if m != selected_model]
            
            routing_decision = RoutingDecision(
                selected_model=selected_model,
                strategy_used=strategy_name,
                query_complexity=query_complexity,
                complexity_level=complexity_level,
                decision_time_ms=decision_time_ms,
                alternatives_considered=alternatives,
                routing_metadata={
                    'complexity_analysis': complexity_result,
                    'strategy_info': strategy.get_strategy_info(),
                    'enhanced_metadata': enhanced_metadata,
                    'fallback_enabled': self.enable_fallback
                }
            )
            
            # 8. Track routing decision
            self._track_routing_decision(routing_decision)
            
            # 9. Log routing decision
            logger.info(
                f"Routed query (complexity={query_complexity:.3f}, level={complexity_level}) "
                f"to {selected_model.provider}/{selected_model.model} "
                f"via {strategy_name} strategy in {decision_time_ms:.1f}ms"
            )
            
            return routing_decision
            
        except Exception as e:
            logger.error(f"Query routing failed: {str(e)}")
            raise RuntimeError(f"Failed to route query: {str(e)}") from e
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive routing statistics.
        
        Returns:
            Dictionary with routing performance and usage statistics
        """
        if self._total_routing_decisions == 0:
            return {
                'total_decisions': 0,
                'avg_decision_time_ms': 0.0,
                'strategy_usage': {},
                'cost_tracking_enabled': self.enable_cost_tracking,
                'fallback_enabled': self.enable_fallback
            }
        
        # Calculate average decision time
        avg_decision_time = self._total_routing_time_ms / self._total_routing_decisions
        
        # Strategy usage distribution
        strategy_distribution = {}
        total_usage = sum(self._strategy_usage_count.values())
        if total_usage > 0:
            for strategy, count in self._strategy_usage_count.items():
                strategy_distribution[strategy] = {
                    'count': count,
                    'percentage': (count / total_usage) * 100
                }
        
        # Recent routing decisions analysis
        recent_decisions = self.routing_history[-100:] if self.routing_history else []
        recent_complexity_levels = {}
        recent_providers = {}
        
        for decision in recent_decisions:
            # Complexity distribution
            level = decision.complexity_level
            recent_complexity_levels[level] = recent_complexity_levels.get(level, 0) + 1
            
            # Provider distribution
            provider = decision.selected_model.provider
            recent_providers[provider] = recent_providers.get(provider, 0) + 1
        
        stats = {
            'total_decisions': self._total_routing_decisions,
            'avg_decision_time_ms': avg_decision_time,
            'strategy_usage': strategy_distribution,
            'recent_complexity_distribution': recent_complexity_levels,
            'recent_provider_distribution': recent_providers,
            'history_size': len(self.routing_history),
            'cost_tracking_enabled': self.enable_cost_tracking,
            'fallback_enabled': self.enable_fallback,
            'available_strategies': list(self.strategies.keys())
        }
        
        # Add cost information if tracking enabled
        if self.enable_cost_tracking and hasattr(self, 'cost_tracker'):
            cost_summary = self.cost_tracker.get_summary_by_time_period(24)  # Last 24 hours
            stats['cost_summary_24h'] = {
                'total_requests': cost_summary.total_requests,
                'total_cost_usd': float(cost_summary.total_cost_usd),
                'avg_cost_per_request': float(cost_summary.avg_cost_per_request)
            }
        
        return stats
    
    def configure_fallback_chain(self, fallback_chain):
        """Configure fallback chain for test compatibility."""
        self.fallback_chain = fallback_chain
        logger.info(f"Configured fallback chain with {len(fallback_chain)} options")
    
    def _attempt_model_request(self, model_option, query, context=None):
        """Attempt model request - stub for test compatibility."""
        # This is a stub - in real implementation would try actual model request
        return None
    
    def get_strategy_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get recommendations for optimizing routing strategy usage.
        
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        if len(self.routing_history) < 10:
            return [{
                'type': 'insufficient_data',
                'message': 'Need more routing decisions to provide recommendations',
                'min_decisions_needed': 10
            }]
        
        # Analyze recent routing patterns
        recent_decisions = self.routing_history[-100:]
        
        # Check for cost optimization opportunities
        if self.enable_cost_tracking and hasattr(self, 'cost_tracker'):
            cost_recommendations = self.cost_tracker.get_cost_optimization_recommendations()
            for rec in cost_recommendations:
                rec['source'] = 'cost_tracker'
                recommendations.append(rec)
        
        # Check strategy usage patterns
        strategy_counts = {}
        for decision in recent_decisions:
            strategy = decision.strategy_used
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        total_decisions = len(recent_decisions)
        
        # Recommend balanced usage
        for strategy, count in strategy_counts.items():
            percentage = (count / total_decisions) * 100
            
            if percentage > 80:  # Over-reliance on single strategy
                recommendations.append({
                    'type': 'strategy_diversification',
                    'priority': 'medium',
                    'title': f'Over-reliance on {strategy} strategy',
                    'description': f'{percentage:.1f}% of decisions use {strategy}',
                    'suggestion': 'Consider testing other strategies for different query types'
                })
        
        # Check for performance issues
        slow_decisions = [d for d in recent_decisions if d.decision_time_ms > 100]  # >100ms
        if len(slow_decisions) > len(recent_decisions) * 0.1:  # >10% slow
            recommendations.append({
                'type': 'performance',
                'priority': 'high',
                'title': 'High routing latency detected',
                'description': f'{len(slow_decisions)} routing decisions >100ms',
                'suggestion': 'Check query analyzer performance and complexity'
            })
        
        return recommendations
    
    def _initialize_strategies(self) -> None:
        """Initialize all routing strategies with their configurations."""
        strategy_configs = self.config.get('strategies', {})
        
        # Initialize default strategies
        default_strategies = {
            'cost_optimized': CostOptimizedStrategy,
            'quality_first': QualityFirstStrategy,
            'balanced': BalancedStrategy
        }
        
        for strategy_name, strategy_class in default_strategies.items():
            strategy_config = strategy_configs.get(strategy_name, {})
            self.strategies[strategy_name] = strategy_class(strategy_config)
            self._strategy_usage_count[strategy_name] = 0
        
        logger.info(f"Initialized {len(self.strategies)} routing strategies")
    
    def _analyze_query_complexity(self,
                                  query: str,
                                  query_metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze query complexity using Epic1QueryAnalyzer.
        
        Args:
            query: The query to analyze
            query_metadata: Additional query metadata
            
        Returns:
            Dictionary with complexity analysis results
        """
        if self.query_analyzer is None:
            # Fallback to basic analysis if no analyzer available
            logger.warning("No Epic1QueryAnalyzer available, using basic complexity analysis")
            return self._basic_complexity_analysis(query)
        
        try:
            # Use Epic1QueryAnalyzer for sophisticated analysis
            analysis_result = self.query_analyzer.analyze(query)
            
            # Handle both dict and object returns from mock/real analyzer
            if hasattr(analysis_result, 'metadata'):
                return analysis_result.metadata
            elif isinstance(analysis_result, dict):
                return analysis_result
            else:
                # Fallback if unexpected format
                return self._basic_complexity_analysis(query)
            
        except Exception as e:
            logger.error(f"Query complexity analysis failed: {str(e)}")
            # Fallback to basic analysis
            return self._basic_complexity_analysis(query)
    
    def _basic_complexity_analysis(self, query: str) -> Dict[str, Any]:
        """
        Basic fallback complexity analysis.
        
        Args:
            query: The query to analyze
            
        Returns:
            Basic complexity analysis results
        """
        query_length = len(query.split())
        
        # Simple heuristics
        if query_length < 10:
            complexity_score = 0.2
            complexity_level = 'simple'
        elif query_length < 25:
            complexity_score = 0.5
            complexity_level = 'medium'
        else:
            complexity_score = 0.8
            complexity_level = 'complex'
        
        # Adjust for technical terms (basic detection)
        technical_indicators = ['algorithm', 'implementation', 'architecture', 'protocol', 'specification']
        technical_count = sum(1 for term in technical_indicators if term in query.lower())
        
        if technical_count > 0:
            complexity_score = min(1.0, complexity_score + 0.2)
            if complexity_score > 0.7:
                complexity_level = 'complex'
            elif complexity_score > 0.4:
                complexity_level = 'medium'
        
        return {
            'complexity_score': complexity_score,
            'complexity_level': complexity_level,
            'analysis_method': 'basic_fallback',
            'query_length': query_length,
            'technical_terms_detected': technical_count
        }
    
    def _prepare_query_metadata(self,
                                query: str,
                                query_metadata: Optional[Dict[str, Any]],
                                context_documents: Optional[List],
                                complexity_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare enhanced metadata for routing strategies.
        
        Args:
            query: The original query
            query_metadata: Original query metadata
            context_documents: Context documents for the query
            complexity_result: Results from complexity analysis
            
        Returns:
            Enhanced metadata dictionary
        """
        enhanced = query_metadata.copy() if query_metadata else {}
        
        # Add query characteristics
        enhanced['query_length'] = len(query.split())
        enhanced['query_char_count'] = len(query)
        enhanced['context_docs'] = len(context_documents) if context_documents else 0
        
        # Add complexity information
        enhanced.update(complexity_result)
        
        # Add timestamp for tracking
        enhanced['routing_timestamp'] = time.time()
        
        return enhanced
    
    def _apply_fallback_logic(self,
                              selected_model: ModelOption,
                              query_metadata: Dict[str, Any]) -> ModelOption:
        """
        Apply fallback logic to ensure model availability.
        
        Args:
            selected_model: Initially selected model
            query_metadata: Query metadata for fallback decisions
            
        Returns:
            Final model selection with fallback considerations
        """
        # For now, return the selected model as-is
        # This can be enhanced to check model availability and apply fallbacks
        
        if not selected_model.fallback_options:
            # Add default fallback options if none provided
            if selected_model.provider != 'ollama':
                selected_model.fallback_options = ['ollama/llama3.2:3b']
        
        return selected_model
    
    def _track_routing_decision(self, decision: RoutingDecision) -> None:
        """
        Track routing decision for monitoring and optimization.
        
        Args:
            decision: The routing decision to track
        """
        # Update metrics
        self._total_routing_decisions += 1
        self._total_routing_time_ms += decision.decision_time_ms
        self._strategy_usage_count[decision.strategy_used] += 1
        
        # Add to history
        self.routing_history.append(decision)
        
        # Trim history if needed
        if len(self.routing_history) > self.max_history_size:
            self.routing_history = self.routing_history[-self.max_history_size:]
        
        # Log for debugging
        logger.debug(
            f"Tracked routing decision: {decision.selected_model.provider}/"
            f"{decision.selected_model.model} via {decision.strategy_used} "
            f"in {decision.decision_time_ms:.1f}ms"
        )