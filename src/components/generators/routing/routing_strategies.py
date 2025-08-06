"""
Routing Strategies for Multi-Model LLM Selection.

This module implements the strategy pattern for different model selection
approaches in the Epic 1 multi-model routing system, enabling flexible
optimization based on cost, quality, or balanced objectives.

Architecture Notes:
- Strategy pattern for pluggable routing logic
- Each strategy implements query complexity → model mapping
- Cost calculation and optimization logic
- Fallback chain management
- Performance and quality considerations

Epic 1 Integration:
- Enables 40%+ cost reduction through intelligent routing
- Provides multiple optimization strategies for different use cases
- Supports real-time cost/quality tradeoff decisions
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod
from decimal import Decimal
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModelOption:
    """
    Model selection option with associated metadata.
    
    Attributes:
        provider: LLM provider (openai, mistral, ollama)
        model: Specific model name
        estimated_cost: Estimated cost for this query
        estimated_quality: Quality score (0.0-1.0)
        estimated_latency_ms: Expected latency in milliseconds
        confidence: Confidence in this selection (0.0-1.0)
        fallback_options: List of fallback models
    """
    provider: str
    model: str
    estimated_cost: Decimal
    estimated_quality: float
    estimated_latency_ms: float
    confidence: float = 1.0
    fallback_options: List[str] = None
    
    def __post_init__(self):
        if self.fallback_options is None:
            self.fallback_options = []


class RoutingStrategy(ABC):
    """
    Abstract base class for routing strategies.
    
    Each strategy implements different logic for selecting the optimal
    LLM model based on query complexity and optimization goals.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize routing strategy.
        
        Args:
            config: Strategy-specific configuration
        """
        self.config = config or {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    def select_model(self,
                     query_complexity: float,
                     complexity_level: str,
                     query_metadata: Optional[Dict[str, Any]] = None) -> ModelOption:
        """
        Select the optimal model for a given query.
        
        Args:
            query_complexity: Complexity score (0.0-1.0)
            complexity_level: Complexity level (simple, medium, complex)
            query_metadata: Additional query metadata
            
        Returns:
            ModelOption with selected model and metadata
        """
        pass
    
    @abstractmethod
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get information about this routing strategy.
        
        Returns:
            Dictionary with strategy information
        """
        pass


class CostOptimizedStrategy(RoutingStrategy):
    """
    Cost-optimized routing strategy.
    
    This strategy prioritizes cost minimization while maintaining
    acceptable quality levels. It aggressively routes queries to
    the cheapest models that can handle the complexity.
    
    Model Mapping:
    - Simple (0.0-0.35): Ollama (free/local)
    - Medium (0.35-0.75): Mistral Small (cost-effective)
    - Complex (0.75-1.0): GPT-3.5-turbo (avoid GPT-4 when possible)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Cost optimization thresholds
        self.simple_threshold = self.config.get('simple_threshold', 0.35)
        self.complex_threshold = self.config.get('complex_threshold', 0.75)
        self.max_cost_per_query = Decimal(str(self.config.get('max_cost_per_query', '0.010')))
        
        # Model preferences (cheapest to most expensive)
        self.model_tiers = {
            'simple': [
                {'provider': 'ollama', 'model': 'llama3.2:3b', 'cost_per_1k': Decimal('0.0000')},
                {'provider': 'mistral', 'model': 'mistral-tiny', 'cost_per_1k': Decimal('0.00025')},
            ],
            'medium': [
                {'provider': 'ollama', 'model': 'llama3.1:8b', 'cost_per_1k': Decimal('0.0000')},
                {'provider': 'mistral', 'model': 'mistral-small', 'cost_per_1k': Decimal('0.002')},
                {'provider': 'openai', 'model': 'gpt-3.5-turbo', 'cost_per_1k': Decimal('0.0015')},
            ],
            'complex': [
                {'provider': 'mistral', 'model': 'mistral-medium', 'cost_per_1k': Decimal('0.00540')},
                {'provider': 'openai', 'model': 'gpt-3.5-turbo', 'cost_per_1k': Decimal('0.0015')},
                {'provider': 'openai', 'model': 'gpt-4-turbo', 'cost_per_1k': Decimal('0.020')},
            ]
        }
    
    def select_model(self,
                     query_complexity: float,
                     complexity_level: str,
                     query_metadata: Optional[Dict[str, Any]] = None) -> ModelOption:
        """Select the most cost-effective model for the query complexity."""
        
        # Determine complexity tier
        if query_complexity < self.simple_threshold:
            tier = 'simple'
        elif query_complexity < self.complex_threshold:
            tier = 'medium'
        else:
            tier = 'complex'
        
        # Get model options for this tier
        model_options = self.model_tiers.get(tier, self.model_tiers['medium'])
        
        # Estimate tokens (rough approximation)
        estimated_tokens = self._estimate_tokens(query_metadata)
        
        # Select cheapest model within cost budget
        for model_info in model_options:
            estimated_cost = (estimated_tokens / 1000) * model_info['cost_per_1k']
            
            if estimated_cost <= self.max_cost_per_query:
                # Build fallback chain
                fallback_options = [
                    f"{opt['provider']}/{opt['model']}" 
                    for opt in model_options[1:3]  # Next 2 options
                ]
                
                return ModelOption(
                    provider=model_info['provider'],
                    model=model_info['model'],
                    estimated_cost=estimated_cost,
                    estimated_quality=self._estimate_quality(tier, model_info),
                    estimated_latency_ms=self._estimate_latency(model_info),
                    confidence=0.9,  # High confidence for cost optimization
                    fallback_options=fallback_options
                )
        
        # If no model fits budget, use cheapest option
        cheapest = model_options[0]
        estimated_cost = (estimated_tokens / 1000) * cheapest['cost_per_1k']
        
        logger.warning(f"Selected model exceeds cost budget: ${estimated_cost:.4f}")
        
        return ModelOption(
            provider=cheapest['provider'],
            model=cheapest['model'],
            estimated_cost=estimated_cost,
            estimated_quality=self._estimate_quality(tier, cheapest),
            estimated_latency_ms=self._estimate_latency(cheapest),
            confidence=0.7,  # Lower confidence due to budget constraint
            fallback_options=[f"{opt['provider']}/{opt['model']}" for opt in model_options[1:2]]
        )
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get cost optimization strategy information."""
        return {
            'name': 'Cost Optimized',
            'description': 'Minimize costs while maintaining acceptable quality',
            'optimization_goal': 'cost',
            'simple_threshold': self.simple_threshold,
            'complex_threshold': self.complex_threshold,
            'max_cost_per_query': float(self.max_cost_per_query),
            'expected_cost_reduction': '50-70%',
            'quality_tradeoff': 'Minimal for simple queries, moderate for complex'
        }
    
    def _estimate_tokens(self, query_metadata: Optional[Dict[str, Any]]) -> int:
        """Estimate token usage based on query metadata."""
        if not query_metadata:
            return 1000  # Default estimate
        
        # Use query length and context size if available
        query_length = query_metadata.get('query_length', 50)
        context_docs = query_metadata.get('context_docs', 3)
        
        # Rough estimation: query + context + response
        prompt_tokens = query_length * 1.3 + context_docs * 200  # Rough approximation
        completion_tokens = 200  # Conservative estimate
        
        return int(prompt_tokens + completion_tokens)
    
    def _estimate_quality(self, tier: str, model_info: Dict[str, Any]) -> float:
        """Estimate quality score for model selection."""
        # Quality estimates based on model capabilities
        quality_map = {
            'ollama': {'simple': 0.85, 'medium': 0.75, 'complex': 0.65},
            'mistral': {'simple': 0.90, 'medium': 0.85, 'complex': 0.80},
            'openai': {'simple': 0.95, 'medium': 0.90, 'complex': 0.95}
        }
        
        provider = model_info['provider']
        return quality_map.get(provider, {}).get(tier, 0.75)
    
    def _estimate_latency(self, model_info: Dict[str, Any]) -> float:
        """Estimate response latency in milliseconds."""
        # Latency estimates based on provider and deployment
        latency_map = {
            'ollama': 2000,    # Local inference, slower but free
            'mistral': 1500,   # Fast cloud API
            'openai': 1000     # Fastest cloud API
        }
        
        return latency_map.get(model_info['provider'], 1500)


class QualityFirstStrategy(RoutingStrategy):
    """
    Quality-first routing strategy.
    
    This strategy prioritizes response quality over cost, selecting
    the highest-quality models available for each complexity level.
    
    Model Mapping:
    - Simple (0.0-0.40): GPT-3.5-turbo (good quality, reasonable cost)
    - Medium (0.40-0.70): GPT-4-turbo or Mistral Large
    - Complex (0.70-1.0): GPT-4-turbo (best available quality)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Quality optimization thresholds
        self.simple_threshold = self.config.get('simple_threshold', 0.40)
        self.complex_threshold = self.config.get('complex_threshold', 0.70)
        self.min_quality_score = self.config.get('min_quality_score', 0.85)
        
        # Model preferences (highest quality to lowest)
        self.model_tiers = {
            'simple': [
                {'provider': 'openai', 'model': 'gpt-3.5-turbo', 'quality': 0.90, 'cost_per_1k': Decimal('0.0015')},
                {'provider': 'mistral', 'model': 'mistral-small', 'quality': 0.85, 'cost_per_1k': Decimal('0.002')},
                {'provider': 'ollama', 'model': 'llama3.1:8b', 'quality': 0.80, 'cost_per_1k': Decimal('0.0000')},
            ],
            'medium': [
                {'provider': 'openai', 'model': 'gpt-4-turbo', 'quality': 0.95, 'cost_per_1k': Decimal('0.020')},
                {'provider': 'mistral', 'model': 'mistral-large', 'quality': 0.90, 'cost_per_1k': Decimal('0.016')},
                {'provider': 'openai', 'model': 'gpt-3.5-turbo', 'quality': 0.85, 'cost_per_1k': Decimal('0.0015')},
            ],
            'complex': [
                {'provider': 'openai', 'model': 'gpt-4-turbo', 'quality': 0.95, 'cost_per_1k': Decimal('0.020')},
                {'provider': 'mistral', 'model': 'mistral-large', 'quality': 0.88, 'cost_per_1k': Decimal('0.016')},
                {'provider': 'openai', 'model': 'gpt-3.5-turbo', 'quality': 0.82, 'cost_per_1k': Decimal('0.0015')},
            ]
        }
    
    def select_model(self,
                     query_complexity: float,
                     complexity_level: str,
                     query_metadata: Optional[Dict[str, Any]] = None) -> ModelOption:
        """Select the highest quality model for the query complexity."""
        
        # Determine complexity tier
        if query_complexity < self.simple_threshold:
            tier = 'simple'
        elif query_complexity < self.complex_threshold:
            tier = 'medium'
        else:
            tier = 'complex'
        
        # Get model options for this tier
        model_options = self.model_tiers.get(tier, self.model_tiers['complex'])
        
        # Estimate tokens
        estimated_tokens = self._estimate_tokens(query_metadata)
        
        # Select highest quality model above minimum threshold
        for model_info in model_options:
            if model_info['quality'] >= self.min_quality_score:
                estimated_cost = (estimated_tokens / 1000) * model_info['cost_per_1k']
                
                # Build fallback chain with other high-quality options
                fallback_options = [
                    f"{opt['provider']}/{opt['model']}" 
                    for opt in model_options[1:3]
                    if opt['quality'] >= self.min_quality_score - 0.1
                ]
                
                return ModelOption(
                    provider=model_info['provider'],
                    model=model_info['model'],
                    estimated_cost=estimated_cost,
                    estimated_quality=model_info['quality'],
                    estimated_latency_ms=self._estimate_latency(model_info),
                    confidence=0.95,  # High confidence for quality-first
                    fallback_options=fallback_options
                )
        
        # Fallback to best available option
        best_option = model_options[0]
        estimated_cost = (estimated_tokens / 1000) * best_option['cost_per_1k']
        
        return ModelOption(
            provider=best_option['provider'],
            model=best_option['model'],
            estimated_cost=estimated_cost,
            estimated_quality=best_option['quality'],
            estimated_latency_ms=self._estimate_latency(best_option),
            confidence=0.8,  # Lower confidence due to quality constraint
            fallback_options=[f"{opt['provider']}/{opt['model']}" for opt in model_options[1:2]]
        )
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get quality-first strategy information."""
        return {
            'name': 'Quality First',
            'description': 'Prioritize highest quality responses regardless of cost',
            'optimization_goal': 'quality',
            'simple_threshold': self.simple_threshold,
            'complex_threshold': self.complex_threshold,
            'min_quality_score': self.min_quality_score,
            'expected_cost_increase': '30-50%',
            'quality_benefit': 'Maximum quality for all query types'
        }
    
    def _estimate_tokens(self, query_metadata: Optional[Dict[str, Any]]) -> int:
        """Estimate token usage - same logic as cost optimization."""
        if not query_metadata:
            return 1000
        
        query_length = query_metadata.get('query_length', 50)
        context_docs = query_metadata.get('context_docs', 3)
        
        prompt_tokens = query_length * 1.3 + context_docs * 200
        completion_tokens = 200
        
        return int(prompt_tokens + completion_tokens)
    
    def _estimate_latency(self, model_info: Dict[str, Any]) -> float:
        """Estimate response latency."""
        latency_map = {
            'ollama': 2500,    # Local inference, can be slower for large models
            'mistral': 1200,   # Fast cloud API  
            'openai': 800      # Fastest cloud API
        }
        
        return latency_map.get(model_info['provider'], 1200)


class BalancedStrategy(RoutingStrategy):
    """
    Balanced routing strategy.
    
    This strategy optimizes for the best cost/quality tradeoff,
    providing good quality at reasonable costs across all
    complexity levels.
    
    Model Mapping:
    - Simple (0.0-0.35): Ollama or Mistral Tiny
    - Medium (0.35-0.70): Mistral Small or GPT-3.5-turbo
    - Complex (0.70-1.0): GPT-4-turbo or Mistral Large based on cost/quality ratio
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Balanced optimization parameters
        self.simple_threshold = self.config.get('simple_threshold', 0.35)
        self.complex_threshold = self.config.get('complex_threshold', 0.70)
        self.cost_weight = self.config.get('cost_weight', 0.4)  # 40% cost, 60% quality
        self.quality_weight = self.config.get('quality_weight', 0.6)
        self.max_cost_per_query = Decimal(str(self.config.get('max_cost_per_query', '0.020')))
        
        # Model options with cost/quality scores
        self.model_options = {
            'simple': [
                {'provider': 'ollama', 'model': 'llama3.2:3b', 'quality': 0.80, 'cost_per_1k': Decimal('0.0000'), 'score': 0.0},
                {'provider': 'mistral', 'model': 'mistral-tiny', 'quality': 0.82, 'cost_per_1k': Decimal('0.00025'), 'score': 0.0},
                {'provider': 'openai', 'model': 'gpt-3.5-turbo', 'quality': 0.90, 'cost_per_1k': Decimal('0.0015'), 'score': 0.0},
            ],
            'medium': [
                {'provider': 'ollama', 'model': 'llama3.1:8b', 'quality': 0.78, 'cost_per_1k': Decimal('0.0000'), 'score': 0.0},
                {'provider': 'mistral', 'model': 'mistral-small', 'quality': 0.85, 'cost_per_1k': Decimal('0.002'), 'score': 0.0},
                {'provider': 'openai', 'model': 'gpt-3.5-turbo', 'quality': 0.87, 'cost_per_1k': Decimal('0.0015'), 'score': 0.0},
                {'provider': 'mistral', 'model': 'mistral-medium', 'quality': 0.88, 'cost_per_1k': Decimal('0.00540'), 'score': 0.0},
            ],
            'complex': [
                {'provider': 'mistral', 'model': 'mistral-large', 'quality': 0.88, 'cost_per_1k': Decimal('0.016'), 'score': 0.0},
                {'provider': 'openai', 'model': 'gpt-3.5-turbo', 'quality': 0.85, 'cost_per_1k': Decimal('0.0015'), 'score': 0.0},
                {'provider': 'openai', 'model': 'gpt-4-turbo', 'quality': 0.95, 'cost_per_1k': Decimal('0.020'), 'score': 0.0},
            ]
        }
        
        # Calculate balanced scores for each model
        self._calculate_balanced_scores()
    
    def select_model(self,
                     query_complexity: float,
                     complexity_level: str,
                     query_metadata: Optional[Dict[str, Any]] = None) -> ModelOption:
        """Select the best balanced cost/quality model."""
        
        # Determine complexity tier
        if query_complexity < self.simple_threshold:
            tier = 'simple'
        elif query_complexity < self.complex_threshold:
            tier = 'medium'
        else:
            tier = 'complex'
        
        # Get model options for this tier
        model_options = self.model_options.get(tier, self.model_options['medium'])
        
        # Estimate tokens
        estimated_tokens = self._estimate_tokens(query_metadata)
        
        # Select model with best balanced score within budget
        best_option = None
        best_score = -1
        
        for model_info in model_options:
            estimated_cost = (estimated_tokens / 1000) * model_info['cost_per_1k']
            
            # Check budget constraint
            if estimated_cost <= self.max_cost_per_query:
                if model_info['score'] > best_score:
                    best_score = model_info['score']
                    best_option = model_info
        
        # If no model within budget, use best scoring option anyway
        if best_option is None:
            best_option = max(model_options, key=lambda x: x['score'])
            logger.warning(f"Selected model may exceed budget: {best_option['provider']}/{best_option['model']}")
        
        estimated_cost = (estimated_tokens / 1000) * best_option['cost_per_1k']
        
        # Build fallback chain with other good options
        fallback_options = [
            f"{opt['provider']}/{opt['model']}" 
            for opt in sorted(model_options, key=lambda x: x['score'], reverse=True)[1:3]
        ]
        
        return ModelOption(
            provider=best_option['provider'],
            model=best_option['model'],
            estimated_cost=estimated_cost,
            estimated_quality=best_option['quality'],
            estimated_latency_ms=self._estimate_latency(best_option),
            confidence=0.85,  # Good confidence for balanced approach
            fallback_options=fallback_options
        )
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get balanced strategy information."""
        return {
            'name': 'Balanced',
            'description': 'Optimize cost/quality tradeoff for best overall value',
            'optimization_goal': 'balanced',
            'cost_weight': self.cost_weight,
            'quality_weight': self.quality_weight,
            'simple_threshold': self.simple_threshold,
            'complex_threshold': self.complex_threshold,
            'max_cost_per_query': float(self.max_cost_per_query),
            'expected_cost_reduction': '25-40%',
            'quality_tradeoff': 'Minimal - smart tradeoffs based on query complexity'
        }
    
    def _calculate_balanced_scores(self) -> None:
        """Calculate balanced scores for all model options."""
        # Find min/max values for normalization across all tiers
        all_models = []
        for tier_models in self.model_options.values():
            all_models.extend(tier_models)
        
        min_cost = min(float(model['cost_per_1k']) for model in all_models if model['cost_per_1k'] > 0) or 0.0001
        max_cost = max(float(model['cost_per_1k']) for model in all_models)
        min_quality = min(model['quality'] for model in all_models)
        max_quality = max(model['quality'] for model in all_models)
        
        # Calculate normalized scores
        for tier_models in self.model_options.values():
            for model in tier_models:
                cost = float(model['cost_per_1k'])
                quality = model['quality']
                
                # Normalize cost (lower is better) and quality (higher is better)
                if cost == 0:  # Free models (ollama)
                    normalized_cost = 1.0  # Best cost score
                else:
                    normalized_cost = 1.0 - ((cost - min_cost) / (max_cost - min_cost))
                
                normalized_quality = (quality - min_quality) / (max_quality - min_quality)
                
                # Calculate balanced score
                model['score'] = (
                    self.cost_weight * normalized_cost + 
                    self.quality_weight * normalized_quality
                )
    
    def _estimate_tokens(self, query_metadata: Optional[Dict[str, Any]]) -> int:
        """Estimate token usage."""
        if not query_metadata:
            return 1000
        
        query_length = query_metadata.get('query_length', 50)
        context_docs = query_metadata.get('context_docs', 3)
        
        prompt_tokens = query_length * 1.3 + context_docs * 200
        completion_tokens = 200
        
        return int(prompt_tokens + completion_tokens)
    
    def _estimate_latency(self, model_info: Dict[str, Any]) -> float:
        """Estimate response latency."""
        latency_map = {
            'ollama': 2000,
            'mistral': 1300,
            'openai': 900
        }
        
        return latency_map.get(model_info['provider'], 1300)


# Strategy registry for easy lookup
STRATEGY_REGISTRY = {
    'cost_optimized': CostOptimizedStrategy,
    'quality_first': QualityFirstStrategy,
    'balanced': BalancedStrategy,
}


def get_strategy_class(strategy_name: str) -> type:
    """
    Get strategy class by name.
    
    Args:
        strategy_name: Strategy name
        
    Returns:
        Strategy class
        
    Raises:
        ValueError: If strategy not found
    """
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(
            f"Unknown routing strategy: {strategy_name}. "
            f"Available: {list(STRATEGY_REGISTRY.keys())}"
        )
    return STRATEGY_REGISTRY[strategy_name]