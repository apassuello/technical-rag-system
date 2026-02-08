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

import logging
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

# Import cost tracking
from ..llm_adapters.cost_tracker import get_cost_tracker
from .model_registry import ModelRegistry
from .routing_strategies import (
    BalancedStrategy,
    CostOptimizedStrategy,
    ModelOption,
    QualityFirstStrategy,
    RoutingStrategy,
)

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
                 enable_fallback: bool = False,  # Legacy parameter name - production default
                 fallback_on_failure: bool = None,  # New parameter name
                 enable_cost_tracking: bool = True,
                 enable_availability_testing: bool = False,  # Production default
                 availability_check_mode: str = "startup",  # startup/scheduled/per_request
                 availability_cache_ttl: int = 3600):
        """
        Initialize adaptive router.
        
        Args:
            default_strategy: Default routing strategy to use
            query_analyzer: Epic1QueryAnalyzer instance for complexity analysis
            config: Router configuration
            enable_fallback: Whether to enable fallback chain management (legacy)
            fallback_on_failure: Whether to enable fallback on actual failures
            enable_cost_tracking: Whether to track routing costs
            enable_availability_testing: Whether to test model availability
            availability_check_mode: When to check availability (startup/scheduled/per_request)
            availability_cache_ttl: TTL for availability cache in seconds
        """
        self.config = config or {}
        self.default_strategy = default_strategy
        self.query_analyzer = query_analyzer
        
        # Handle backward compatibility for fallback parameter
        if fallback_on_failure is not None:
            self.fallback_on_failure = fallback_on_failure
        else:
            self.fallback_on_failure = enable_fallback  # Use legacy parameter
        
        # For backward compatibility, keep enable_fallback reference
        self.enable_fallback = self.fallback_on_failure
        
        self.enable_cost_tracking = enable_cost_tracking
        self.enable_availability_testing = enable_availability_testing
        self.availability_check_mode = availability_check_mode
        self.availability_cache_ttl = availability_cache_ttl
        
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
        
        # Production availability cache with configurable TTL
        self._availability_cache: Dict[str, Dict[str, Any]] = {}
        self._availability_cache_ttl = availability_cache_ttl
        
        # Legacy circuit breaker state (maintained for compatibility)
        self._adapter_availability_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_expiry_seconds = 300  # 5 minutes cache
        self._max_failures_before_cache = 3  # Cache failures after 3 attempts
        
        # Setup availability cache if enabled
        if self.enable_availability_testing and self.availability_check_mode == "startup":
            self._setup_availability_cache()
        
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
                raise ValueError(f"Unknown strategy: {strategy_name}")
            
            strategy = self.strategies[strategy_name]
            
            # 3. Prepare query metadata for strategy
            enhanced_metadata = self._prepare_query_metadata(
                query, query_metadata, context_documents, complexity_result
            )
            # Add original query to metadata for fallback tracking
            enhanced_metadata['original_query'] = query
            
            # 4. Get available models for this complexity
            available_models = self.model_registry.get_models_for_complexity(complexity_level)
            
            # 5. Select model using strategy with fallback chain consideration
            selected_model = self._select_model_with_fallback_preference(
                strategy, complexity_result, available_models
            )
            
            # Handle case where no model is selected (empty registry)
            if selected_model is None:
                logger.warning("No model selected by strategy - possibly empty model registry")
                return None
            
            # 6. Apply production model selection (no per-query network calls)
            final_model, fallback_used = self._production_model_selection(selected_model, enhanced_metadata)
            
            # 7. Create routing decision with alternatives
            decision_time_ms = (time.time() - start_time) * 1000
            
            # Populate alternatives_considered
            alternatives = [m for m in available_models if m != final_model]
            
            routing_decision = RoutingDecision(
                selected_model=final_model,
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
            
            # Set fallback tracking attributes
            routing_decision.fallback_used = fallback_used
            routing_decision.original_query = query
            
            # 8. Track routing decision
            self._track_routing_decision(routing_decision)
            
            # 9. Log routing decision
            logger.info(
                f"Routed query (complexity={query_complexity:.3f}, level={complexity_level}) "
                f"to {final_model.provider}/{final_model.model} "
                f"via {strategy_name} strategy in {decision_time_ms:.1f}ms"
                f"{' (fallback used)' if fallback_used else ''}"
            )
            
            return routing_decision
            
        except ValueError as e:
            # Let ValueError pass through directly (expected for invalid strategies)
            logger.error(f"Query routing failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Query routing failed: {str(e)}")
            raise RuntimeError(f"Failed to route query: {str(e)}") from e
    
    def setup_availability_cache(self) -> Dict[str, bool]:
        """
        One-time availability testing during startup (production deployment).
        
        This method performs comprehensive availability testing once during
        initialization, caching results to eliminate per-query network calls.
        
        Returns:
            Dictionary mapping model keys to availability status
        """
        availability_results = {}
        all_models = self.model_registry.get_all_models()
        
        logger.info(f"Testing availability for {len(all_models)} models during startup...")
        start_time = time.time()
        
        for model in all_models:
            cache_key = f"{model.provider}/{model.model}"
            try:
                # Use existing availability test method but cache results
                response = self._attempt_model_request(model, "Availability test", None)
                is_available = response is not None
                
                self._availability_cache[cache_key] = {
                    'available': is_available,
                    'timestamp': time.time(),
                    'tested_at_startup': True,
                    'last_error': None if is_available else 'Failed startup availability test'
                }
                availability_results[cache_key] = is_available
                
            except Exception as e:
                self._availability_cache[cache_key] = {
                    'available': False,
                    'timestamp': time.time(),
                    'tested_at_startup': True,
                    'last_error': str(e)
                }
                availability_results[cache_key] = False
        
        setup_time = (time.time() - start_time) * 1000
        available_count = sum(availability_results.values())
        
        logger.info(
            f"Availability testing complete: {available_count}/{len(all_models)} "
            f"models available in {setup_time:.1f}ms"
        )
        
        return availability_results
    
    def _setup_availability_cache(self) -> None:
        """Internal method to setup availability cache during initialization."""
        try:
            self.setup_availability_cache()
        except Exception as e:
            logger.warning(f"Startup availability testing failed: {e}")
            # Continue with empty cache - fallback to per-request testing if needed
    
    def _get_cached_availability(self, cache_key: str) -> Optional[Dict]:
        """
        Fast cached availability lookup with TTL checking.
        
        Args:
            cache_key: Model cache key (provider/model)
            
        Returns:
            Cached availability data or None if expired/missing
        """
        if cache_key not in self._availability_cache:
            return None
        
        cached_entry = self._availability_cache[cache_key]
        current_time = time.time()
        cache_age = current_time - cached_entry['timestamp']
        
        # Check if cache has expired
        if cache_age > self._availability_cache_ttl:
            logger.debug(f"Availability cache expired for {cache_key} (age: {cache_age:.1f}s)")
            return None
        
        return cached_entry
    
    def _production_model_selection(self, 
                                    selected_model: ModelOption, 
                                    query_metadata: Dict[str, Any]) -> Tuple[ModelOption, bool]:
        """
        Production-optimized model selection with zero per-query network calls.
        
        This method uses cached availability data for routing decisions,
        falling back to actual failure handling only when requests fail.
        
        Args:
            selected_model: Initially selected model from strategy
            query_metadata: Query metadata for fallback decisions
            
        Returns:
            Tuple of (final_model, fallback_used)
        """
        # For per-request mode or when fallbacks are explicitly enabled, use legacy method
        # This ensures backward compatibility with tests that set enable_fallback = True
        if (self.availability_check_mode == "per_request" or 
            self.fallback_on_failure):
            return self._test_and_fallback_model_selection(selected_model, query_metadata)
        
        # Skip availability testing in production mode (both availability testing 
        # and fallback are disabled)
        if not self.enable_availability_testing:
            return selected_model, False
        
        # Production mode: use cached availability
        cache_key = f"{selected_model.provider}/{selected_model.model}"
        cached_availability = self._get_cached_availability(cache_key)
        
        # If model is cached as available, use it directly
        if cached_availability and cached_availability.get('available', False):
            logger.debug(f"Using cached available model: {cache_key}")
            return selected_model, False
        
        # If model is cached as unavailable, find immediate fallback
        if cached_availability and not cached_availability.get('available', True):
            logger.debug(f"Model {cache_key} cached as unavailable, finding fallback")
            fallback_model = self._get_immediate_fallback(selected_model)
            if fallback_model:
                return fallback_model, True
        
        # No cache data or fallback failed - return original model
        # Actual failure will be handled during request execution
        return selected_model, False
    
    def _get_immediate_fallback(self, failed_model: ModelOption) -> Optional[ModelOption]:
        """
        Deterministic fallback without testing - uses cached availability.
        
        Args:
            failed_model: The model that failed or is cached as unavailable
            
        Returns:
            Available fallback model or None if no suitable fallback found
        """
        fallback_models = self._get_fallback_models(failed_model)
        
        # Find first available fallback from cache
        for fallback_model in fallback_models:
            cache_key = f"{fallback_model.provider}/{fallback_model.model}"
            cached_availability = self._get_cached_availability(cache_key)
            
            # If cached as available, use it
            if cached_availability and cached_availability.get('available', False):
                logger.info(f"Selected cached available fallback: {cache_key}")
                return fallback_model
            
            # If no cache data, assume available (optimistic fallback)
            if cached_availability is None:
                logger.info(f"Selected uncached fallback (assumed available): {cache_key}")
                return fallback_model
        
        # All fallbacks are cached as unavailable
        logger.warning("No cached available fallback found - returning None")
        return None

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
            'fallback_on_failure': self.fallback_on_failure,
            'availability_testing_enabled': self.enable_availability_testing,
            'availability_check_mode': self.availability_check_mode,
            'availability_cache_ttl': self.availability_cache_ttl,
            'availability_cache_entries': len(self._availability_cache),
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
    
    def configure_fallback_chain(self, fallback_chain: List[Any]) -> None:
        """Configure fallback chain for test compatibility."""
        self.fallback_chain = fallback_chain
        logger.info(f"Configured fallback chain with {len(fallback_chain)} options")

    def _attempt_model_request(self, model_option: Any, query: str, context: Optional[Any] = None) -> Optional[Any]:
        """
        Attempt model request with comprehensive error handling and circuit breaker pattern.
        
        This method creates the appropriate adapter and makes a real API call
        to test model availability. Implements defensive programming with
        graceful degradation under all failure conditions, including a circuit
        breaker pattern to avoid repeated authentication failures.
        
        Args:
            model_option: ModelOption to attempt
            query: Query to send to model
            context: Optional context for the request
            
        Returns:
            Response object on success, None on authentication/availability failures
            
        Raises:
            Exception: Only for unexpected errors that indicate system problems
        """
        # Check circuit breaker cache to avoid repeated failures
        cache_key = f"{model_option.provider}/{model_option.model}"
        current_time = time.time()
        
        if cache_key in self._adapter_availability_cache:
            cache_entry = self._adapter_availability_cache[cache_key]
            cache_age = current_time - cache_entry['timestamp']
            
            # If cached as unavailable and not expired, skip attempt
            if not cache_entry['available'] and cache_age < self._cache_expiry_seconds:
                logger.debug(f"Skipping {cache_key} due to circuit breaker (cached as unavailable)")
                return None
        
        try:
            # Import adapter classes dynamically to avoid circular imports
            from ..base import GenerationParams
            from ..llm_adapters import get_adapter_class
            from ..llm_adapters.base_adapter import (
                AuthenticationError,
                ModelNotFoundError,
                RateLimitError,
            )
            
            # Get adapter class for provider
            adapter_class = get_adapter_class(model_option.provider)
            if not adapter_class:
                logger.warning(f"No adapter available for provider: {model_option.provider}")
                return None
                
            # Create adapter configuration
            config = {
                'model_name': model_option.model,
                'config': {
                    'temperature': 0.1,  # Low temperature for availability test
                    'max_tokens': 10    # Minimal tokens for quick test
                },
                'timeout': 10.0  # Short timeout for quick failure detection
            }
            
            # Create adapter instance
            adapter = adapter_class(**config)
            
            # Create minimal generation parameters for test
            test_params = GenerationParams(
                temperature=0.1,
                max_tokens=10,
                top_p=None,
                stop_sequences=None
            )
            
            # Attempt minimal request to test availability
            test_prompt = "Test"  # Minimal prompt for availability check
            response = adapter._make_request(test_prompt, test_params)
            
            if response:
                logger.debug(f"Model {model_option.provider}/{model_option.model} availability confirmed")
                # Update cache with successful result
                self._adapter_availability_cache[cache_key] = {
                    'available': True,
                    'timestamp': current_time,
                    'last_error': None
                }
                return response
            else:
                logger.warning(f"Model {model_option.provider}/{model_option.model} returned empty response")
                # Update cache with failure
                self._update_failure_cache(cache_key, current_time, "Empty response")
                return None
                
        except AuthenticationError as e:
            # Authentication failures should not retry - fall back to local models
            logger.warning(f"Authentication failed for {model_option.provider}/{model_option.model}: {e}")
            self._update_failure_cache(cache_key, current_time, f"Authentication error: {str(e)}")
            return None
            
        except ModelNotFoundError as e:
            # Model not found - don't retry this model
            logger.warning(f"Model not found {model_option.provider}/{model_option.model}: {e}")
            self._update_failure_cache(cache_key, current_time, f"Model not found: {str(e)}")
            return None
            
        except RateLimitError as e:
            # Rate limit - could retry later but for availability test, treat as unavailable
            logger.warning(f"Rate limited for {model_option.provider}/{model_option.model}: {e}")
            # Use shorter cache for rate limits (they're temporary)
            self._update_failure_cache(cache_key, current_time, f"Rate limited: {str(e)}", cache_duration=60)
            return None
            
        except ImportError as e:
            # Missing dependencies for adapter
            logger.warning(f"Adapter dependencies missing for {model_option.provider}: {e}")
            self._update_failure_cache(cache_key, current_time, f"Missing dependencies: {str(e)}")
            return None
            
        except (ConnectionError, TimeoutError, OSError) as e:
            # Network/connectivity issues
            logger.warning(f"Network error for {model_option.provider}/{model_option.model}: {e}")
            # Use shorter cache for network errors (they're often temporary)
            self._update_failure_cache(cache_key, current_time, f"Network error: {str(e)}", cache_duration=120)
            return None
            
        except Exception as e:
            # Catch-all for unexpected errors - log but don't crash
            error_str = str(e).lower()
            
            # Handle common API errors gracefully
            if any(keyword in error_str for keyword in ['404', '503', 'unavailable', 'connection']):
                logger.warning(f"Service unavailable for {model_option.provider}/{model_option.model}: {e}")
                self._update_failure_cache(cache_key, current_time, f"Service unavailable: {str(e)}", cache_duration=120)
                return None
            elif any(keyword in error_str for keyword in ['401', '403', 'unauthorized', 'forbidden']):
                logger.warning(f"Authorization failed for {model_option.provider}/{model_option.model}: {e}")
                self._update_failure_cache(cache_key, current_time, f"Authorization failed: {str(e)}")
                return None
            else:
                # Unexpected error - log and treat as unavailable for graceful degradation
                logger.error(f"Unexpected error testing {model_option.provider}/{model_option.model}: {e}")
                self._update_failure_cache(cache_key, current_time, f"Unexpected error: {str(e)}")
                return None
    
    def _update_failure_cache(self, cache_key: str, timestamp: float, error_message: str, cache_duration: int = None) -> None:
        """
        Update the adapter availability cache with failure information.
        
        Args:
            cache_key: The cache key for the adapter
            timestamp: Current timestamp
            error_message: Description of the error
            cache_duration: Override cache duration in seconds
        """
        cache_duration = cache_duration or self._cache_expiry_seconds
        
        # Get current failure count if exists
        current_entry = self._adapter_availability_cache.get(cache_key, {})
        failure_count = current_entry.get('failure_count', 0) + 1
        
        self._adapter_availability_cache[cache_key] = {
            'available': False,
            'timestamp': timestamp,
            'last_error': error_message,
            'failure_count': failure_count,
            'cache_duration': cache_duration
        }
        
        logger.debug(f"Updated failure cache for {cache_key}: {failure_count} failures, cached for {cache_duration}s")
    
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
        enhanced['context_documents'] = context_documents  # Store actual context for fallback
        
        # Add complexity information
        enhanced.update(complexity_result)
        
        # Add timestamp for tracking
        enhanced['routing_timestamp'] = time.time()
        
        return enhanced
    
    def _select_model_with_fallback_preference(self,
                                               strategy: 'RoutingStrategy',
                                               query_analysis: Dict[str, Any],
                                               available_models: List['ModelOption']) -> Optional['ModelOption']:
        """
        Select model with fallback chain preference consideration.
        
        If a fallback chain is configured, prefer the first model from the chain
        if it's available for the current complexity level. Otherwise, use normal
        strategy selection.
        
        Args:
            strategy: The routing strategy to use
            query_analysis: Query complexity analysis results
            available_models: Available models for this complexity level
            
        Returns:
            Selected ModelOption or None if no suitable model found
        """
        logger.debug(f"_select_model_with_fallback_preference called with fallback_chain={self.fallback_chain}")
        
        # If fallback chain is configured, try to use the first model as primary
        if self.fallback_chain:
            primary_provider, primary_model_name = self.fallback_chain[0]
            logger.debug(f"Trying to select primary model from fallback chain: {primary_provider}/{primary_model_name}")
            
            # Check if the primary model from fallback chain is available for this complexity
            for model in available_models:
                if model.provider == primary_provider and model.model == primary_model_name:
                    logger.info(f"Selected primary model from fallback chain: {primary_provider}/{primary_model_name}")
                    return model
            
            # If primary from fallback chain isn't available, check if we can find it in other complexity levels
            # and if it's reasonable to use for this query
            all_models = self.model_registry.get_all_models()
            for model in all_models:
                if model.provider == primary_provider and model.model == primary_model_name:
                    # Found the model, but it's not in the current complexity level
                    # Check if it's reasonable to use (e.g., using a complex model for simple query is okay)
                    complexity_level = query_analysis.get('complexity_level', 'medium').lower()
                    if self._is_model_suitable_for_complexity(model, complexity_level):
                        logger.info(f"Selected primary model from fallback chain (cross-complexity): {primary_provider}/{primary_model_name}")
                        return model
            
            # If model not found in registry at all, create a dynamic ModelOption for fallback chain testing
            # This allows fallback chains to reference models not in the registry (useful for testing)
            if primary_provider and primary_model_name:
                logger.info(f"Creating dynamic model for fallback chain: {primary_provider}/{primary_model_name}")
                from decimal import Decimal

                from .routing_strategies import ModelOption
                dynamic_model = ModelOption(
                    provider=primary_provider,
                    model=primary_model_name,
                    estimated_cost=Decimal('0.001'),  # Default cost for unknown models
                    estimated_quality=0.8,  # Default quality
                    estimated_latency_ms=1000,  # Default latency
                    confidence=0.7,
                    fallback_options=[]
                )
                return dynamic_model
        
        # Fallback to normal strategy selection
        logger.debug("Using normal strategy selection")
        return strategy.select_model(query_analysis, available_models)
    
    def _is_model_suitable_for_complexity(self, model: 'ModelOption', complexity_level: str) -> bool:
        """
        Check if a model is suitable for a given complexity level.
        
        Generally, higher-capability models can handle lower complexity tasks,
        but not vice versa (to avoid using inadequate models for complex tasks).
        
        Args:
            model: The model to check
            complexity_level: Target complexity level ('simple', 'medium', 'complex')
            
        Returns:
            True if model is suitable for the complexity level
        """
        # Get all models to determine where this model typically fits
        all_models = self.model_registry.get_all_models()
        
        # Check which complexity tiers this model appears in
        model_tiers = []
        for tier, models in [('simple', self.model_registry.get_models_for_complexity('simple')),
                            ('medium', self.model_registry.get_models_for_complexity('medium')),
                            ('complex', self.model_registry.get_models_for_complexity('complex'))]:
            for tier_model in models:
                if tier_model.provider == model.provider and tier_model.model == model.model:
                    model_tiers.append(tier)
                    break
        
        # If model appears in the target tier, it's suitable
        if complexity_level in model_tiers:
            return True
        
        # If model appears in higher tiers than target, it's suitable (overkill but okay)
        tier_hierarchy = {'simple': 0, 'medium': 1, 'complex': 2}
        target_level = tier_hierarchy.get(complexity_level, 1)
        
        for tier in model_tiers:
            if tier_hierarchy.get(tier, 1) >= target_level:
                return True
                
        # Model doesn't appear in suitable tiers
        return False

    def _test_and_fallback_model_selection(self,
                                           selected_model: ModelOption,
                                           query_metadata: Dict[str, Any]) -> Tuple[ModelOption, bool]:
        """
        Test model availability and apply fallback logic if needed.
        
        This is the main integration point that tests the primary model selection
        and activates fallback logic if the model is unavailable.
        
        Args:
            selected_model: Initially selected model from strategy
            query_metadata: Query metadata for fallback decisions
            
        Returns:
            Tuple of (final_model, fallback_used)
        """
        if not self.fallback_on_failure:
            return selected_model, False
        
        # Extract query and context for testing
        query = query_metadata.get('original_query', 'test query')
        context_documents = query_metadata.get('context_documents')
        
        # Test primary model availability
        try:
            response = self._attempt_model_request(selected_model, query, context_documents)
            if response is not None:
                logger.debug(f"Primary model {selected_model.provider}/{selected_model.model} available")
                return selected_model, False
        except Exception as e:
            logger.warning(f"Primary model {selected_model.provider}/{selected_model.model} unavailable: {e}")
            # Continue to fallback logic
        
        # Primary model failed - apply fallback logic
        return self._apply_fallback_logic(selected_model, query_metadata)

    def _apply_fallback_logic(self,
                              selected_model: ModelOption,
                              query_metadata: Dict[str, Any]) -> Tuple[ModelOption, bool]:
        """
        Apply fallback logic to find an available model.
        
        This method tries fallback models in order until one succeeds or all options are exhausted.
        Note: This method assumes the primary model has already failed.
        
        Args:
            selected_model: Initially selected model (already failed)
            query_metadata: Query metadata for fallback decisions
            
        Returns:
            Tuple of (final_model, fallback_used=True) or raises RuntimeError
        """
        # Extract query and context for fallback attempts
        query = query_metadata.get('original_query', 'test query')
        context_documents = query_metadata.get('context_documents')
        
        # Get fallback options
        fallback_options = self._get_fallback_models(selected_model)
        
        for fallback_model in fallback_options:
            try:
                response = self._attempt_model_request(fallback_model, query, context_documents)
                if response is not None:
                    logger.info(f"Fallback successful: {fallback_model.provider}/{fallback_model.model}")
                    return fallback_model, True
            except Exception as e:
                logger.warning(f"Fallback model {fallback_model.provider}/{fallback_model.model} failed: {e}")
                continue
        
        # All fallbacks exhausted - raise exception
        logger.error("All fallback options exhausted")
        raise RuntimeError("All fallback models failed - no available models for query")
    
    def _get_fallback_models(self, primary_model: ModelOption) -> List[ModelOption]:
        """
        Get fallback models for a primary model with guaranteed local fallback.
        
        This method implements a robust fallback strategy that ensures graceful
        degradation by always including local models as the final fallback option.
        
        Args:
            primary_model: The primary model that failed
            
        Returns:
            List of fallback ModelOption objects, guaranteed to include local fallback
        """
        fallback_models = []
        
        # Step 1: Use configured fallback chain if available
        if self.fallback_chain:
            for provider, model_name in self.fallback_chain:
                if provider != primary_model.provider:  # Don't fallback to same provider
                    fallback_model = self._create_fallback_model_option(provider, model_name)
                    if fallback_model:
                        fallback_models.append(fallback_model)
        
        # Step 2: Use model's built-in fallback options
        if primary_model.fallback_options:
            for fallback_spec in primary_model.fallback_options:
                if '/' in fallback_spec:
                    provider, model_name = fallback_spec.split('/', 1)
                    fallback_model = self._create_fallback_model_option(provider, model_name)
                    if fallback_model:
                        fallback_models.append(fallback_model)
        
        # Step 3: Add intelligent fallback based on provider failure patterns
        if primary_model.provider in ['openai', 'mistral']:
            # For external APIs that failed, try other external APIs first, then local
            if primary_model.provider == 'openai':
                # Try Mistral as intermediate fallback before going local
                mistral_fallback = self._create_fallback_model_option('mistral', 'mistral-small')
                if mistral_fallback and mistral_fallback not in fallback_models:
                    fallback_models.append(mistral_fallback)
            elif primary_model.provider == 'mistral':
                # Try OpenAI as intermediate fallback before going local
                openai_fallback = self._create_fallback_model_option('openai', 'gpt-3.5-turbo')
                if openai_fallback and openai_fallback not in fallback_models:
                    fallback_models.append(openai_fallback)
        
        # Step 4: ALWAYS ensure we have a local model as final fallback
        # This is critical for 99% recovery rate requirement
        ollama_models = [
            'llama3.2:3b',  # Primary local fallback
            'llama3.2:1b',  # Backup if 3b not available
        ]
        
        for ollama_model in ollama_models:
            if primary_model.provider != 'ollama' or primary_model.model != ollama_model:
                ollama_fallback = self._create_fallback_model_option('ollama', ollama_model)
                if ollama_fallback and ollama_fallback not in fallback_models:
                    fallback_models.append(ollama_fallback)
                    break  # Only add one Ollama model to avoid duplicates
        
        # Step 5: If still no fallbacks, create emergency local fallback
        if not fallback_models:
            emergency_fallback = self._create_emergency_local_fallback()
            if emergency_fallback:
                fallback_models.append(emergency_fallback)
        
        logger.debug(f"Created {len(fallback_models)} fallback options for {primary_model.provider}/{primary_model.model}")
        return fallback_models
    
    def _create_fallback_model_option(self, provider: str, model_name: str) -> Optional[ModelOption]:
        """
        Create a ModelOption for a fallback model.
        
        Args:
            provider: Provider name (e.g., 'ollama', 'mistral')
            model_name: Model name (e.g., 'llama3.2:3b', 'mistral-small')
            
        Returns:
            ModelOption or None if creation fails
        """
        try:
            # Try to get model from registry first
            all_models = self.model_registry.get_all_models()
            for model in all_models:
                if model.provider == provider and model.model == model_name:
                    return model
            
            # Create basic fallback model if not in registry
            from decimal import Decimal
            return ModelOption(
                provider=provider,
                model=model_name,
                estimated_cost=Decimal('0.001'),  # Assume low cost for fallbacks
                estimated_quality=0.7,  # Assume decent quality
                estimated_latency_ms=1000,  # Assume higher latency
                confidence=0.8,
                fallback_options=[]
            )
        except Exception as e:
            logger.error(f"Failed to create fallback model option for {provider}/{model_name}: {e}")
            return None
    
    def _create_emergency_local_fallback(self) -> Optional[ModelOption]:
        """
        Create emergency local fallback when all other options have failed.
        
        This method creates a guaranteed local fallback using the most basic
        configuration possible, ensuring the system never fails completely.
        
        Returns:
            ModelOption for emergency local fallback, or None if creation fails
        """
        try:
            from decimal import Decimal

            from .routing_strategies import ModelOption
            
            # Create minimal Ollama fallback with conservative settings
            emergency_fallback = ModelOption(
                provider='ollama',
                model='llama3.2:3b',  # Most common local model
                estimated_cost=Decimal('0.00'),  # Free local model
                estimated_quality=0.6,  # Conservative quality estimate
                estimated_latency_ms=3000.0,  # Conservative latency estimate
                confidence=0.7,  # Moderate confidence
                fallback_options=[]  # No further fallbacks - this is the end of the line
            )
            
            logger.info("Created emergency local fallback to ensure graceful degradation")
            return emergency_fallback
            
        except Exception as e:
            logger.critical(f"Failed to create emergency local fallback: {e}")
            # This should never happen, but if it does, return None
            # The calling code will handle this gracefully
            return None
    
    def handle_actual_request_failure(self, model_option: ModelOption, error: Exception) -> None:
        """
        Handle actual request failure to update availability cache.
        
        This method is called by Epic1AnswerGenerator when an actual model request fails,
        allowing the router to update its cached availability information without
        doing preemptive availability testing.
        
        Args:
            model_option: The model that failed during actual request
            error: The error that occurred during the request
        """
        try:
            cache_key = f"{model_option.provider}/{model_option.model}"
            current_time = time.time()
            error_message = str(error)
            
            # Determine cache duration based on error type
            cache_duration = self._cache_expiry_seconds  # Default 5 minutes
            
            # Shorter cache for temporary issues
            if any(keyword in error_message.lower() for keyword in ['rate limit', '429', 'timeout']):
                cache_duration = 120  # 2 minutes for temporary issues
            
            # Longer cache for authentication/model not found
            elif any(keyword in error_message.lower() for keyword in ['401', '403', '404', 'authentication', 'not found']):
                cache_duration = 600  # 10 minutes for persistent issues
            
            # Update cache with failure information
            self._update_failure_cache(cache_key, current_time, error_message, cache_duration)
            
            logger.info(f"Updated availability cache after actual failure: {cache_key} -> unavailable "
                       f"(cached for {cache_duration}s due to: {error_message[:100]})")
            
        except Exception as cache_error:
            logger.warning(f"Failed to update availability cache after request failure: {cache_error}")
    
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