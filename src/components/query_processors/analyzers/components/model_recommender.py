"""
Model Recommender for Epic 1 Query Analysis.

This module recommends optimal LLM models based on query complexity
and routing strategy, enabling cost-effective multi-model deployments.

Architecture Notes:
- Strategy pattern for different optimization goals
- Cost and latency estimation
- Fallback chain support
- Configuration-driven model mappings
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from config.llm_providers import LOCAL

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Available routing strategies."""
    COST_OPTIMIZED = "cost_optimized"
    QUALITY_FIRST = "quality_first"
    BALANCED = "balanced"
    LATENCY_OPTIMIZED = "latency_optimized"


@dataclass
class ModelRecommendation:
    """Result of model recommendation."""
    model: str  # Full model identifier (provider:model)
    provider: str  # Model provider (ollama, openai, mistral, etc.)
    model_name: str  # Specific model name
    complexity_level: str  # Query complexity level
    confidence: float  # Confidence in recommendation (0.0-1.0)
    cost_estimate: float  # Estimated cost per query
    latency_estimate: int  # Estimated latency in milliseconds
    fallback_chain: List[str]  # Alternative models if primary fails
    reasoning: str  # Human-readable explanation


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    provider: str
    model: str
    max_cost_per_query: float
    avg_latency_ms: int
    quality_score: float = 0.5  # Relative quality (0.0-1.0)
    max_tokens: int = 2048
    supports_streaming: bool = False


class ModelRecommender:
    """
    Recommends optimal models based on complexity and routing strategy.
    
    This sub-component maps query complexity levels to appropriate LLM models,
    considering cost, quality, and latency constraints based on the selected
    routing strategy.
    
    Strategies:
    - cost_optimized: Minimize cost while maintaining acceptable quality
    - quality_first: Always use best model for complexity level
    - balanced: Balance between cost and quality (default)
    - latency_optimized: Minimize response time
    
    Configuration:
    - strategy: Routing strategy to use
    - model_mappings: Models for each complexity level
    - fallback_chains: Alternative models if primary fails
    - cost_multipliers: Adjust cost estimates by provider
    """
    
    # Default model mappings by complexity level
    DEFAULT_MODEL_MAPPINGS = {
        'simple': ModelConfig(
            provider='local',
            model=LOCAL.model,
            max_cost_per_query=0.001,
            avg_latency_ms=500,
            quality_score=0.6
        ),
        'medium': ModelConfig(
            provider='mistral',
            model='mistral-small',
            max_cost_per_query=0.01,
            avg_latency_ms=1000,
            quality_score=0.75
        ),
        'complex': ModelConfig(
            provider='openai',
            model='gpt-4-turbo',
            max_cost_per_query=0.10,
            avg_latency_ms=2000,
            quality_score=0.95
        )
    }
    
    # Strategy-specific model overrides
    STRATEGY_OVERRIDES = {
        RoutingStrategy.COST_OPTIMIZED: {
            'simple': f'local:{LOCAL.model}',
            'medium': 'mistral:mistral-tiny',
            'complex': 'openai:gpt-3.5-turbo'
        },
        RoutingStrategy.QUALITY_FIRST: {
            'simple': 'mistral:mistral-small',
            'medium': 'openai:gpt-3.5-turbo',
            'complex': 'openai:gpt-4-turbo'
        },
        RoutingStrategy.LATENCY_OPTIMIZED: {
            'simple': f'local:{LOCAL.model}',
            'medium': f'local:{LOCAL.model}',
            'complex': 'openai:gpt-3.5-turbo'
        }
    }
    
    # Default fallback chains
    DEFAULT_FALLBACK_CHAINS = {
        'simple': [
            f'local:{LOCAL.model}',
            'mistral:mistral-tiny',
            'openai:gpt-3.5-turbo'
        ],
        'medium': [
            'mistral:mistral-small',
            'openai:gpt-3.5-turbo',
            'anthropic:claude-3-haiku'
        ],
        'complex': [
            'openai:gpt-4-turbo',
            'anthropic:claude-3-opus',
            'openai:gpt-4'
        ]
    }
    
    # Cost multipliers for token estimation (per 1K tokens)
    COST_PER_1K_TOKENS = {
        'local': 0.0,  # Local, no cost
        'mistral': {
            'mistral-tiny': 0.00025,
            'mistral-small': 0.001,
            'mistral-medium': 0.0027
        },
        'openai': {
            'gpt-3.5-turbo': 0.002,
            'gpt-4-turbo': 0.03,
            'gpt-4': 0.06
        },
        'anthropic': {
            'claude-3-haiku': 0.0008,
            'claude-3-sonnet': 0.015,
            'claude-3-opus': 0.075
        }
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize model recommender.
        
        Args:
            config: Configuration dictionary with:
                - strategy: Routing strategy (default: balanced)
                - model_mappings: Custom model configurations
                - fallback_chains: Custom fallback chains
                - cost_multipliers: Adjust cost estimates
        """
        self.config = config or {}

        # Load routing strategy
        strategy_name = self.config.get('strategy', 'balanced')
        try:
            self._strategy_enum = RoutingStrategy(strategy_name)
        except ValueError:
            logger.warning(f"Unknown strategy {strategy_name}, using balanced")
            self._strategy_enum = RoutingStrategy.BALANCED

        # Expose strategy as string for test compatibility
        self.strategy = self._strategy_enum.value
        
        # Load model mappings
        self.model_mappings = self._load_model_mappings()
        
        # Load fallback chains
        self.fallback_chains = self.config.get(
            'fallback_chains', 
            self.DEFAULT_FALLBACK_CHAINS.copy()
        )
        
        # Cost adjustment factors
        self.cost_multipliers = self.config.get('cost_multipliers', {})
        
        logger.info(f"Initialized ModelRecommender with strategy: {self.strategy}")
    
    def _load_model_mappings(self) -> Dict[str, ModelConfig]:
        """
        Load model mappings from configuration or defaults.
        
        Returns:
            Dictionary mapping complexity levels to ModelConfig
        """
        mappings = {}
        
        # Start with defaults
        for level, default_config in self.DEFAULT_MODEL_MAPPINGS.items():
            mappings[level] = default_config
        
        # Apply custom configurations
        custom_mappings = self.config.get('model_mappings', {})
        for level, config_dict in custom_mappings.items():
            if isinstance(config_dict, dict):
                mappings[level] = ModelConfig(**config_dict)
        
        return mappings
    
    def recommend(
        self,
        complexity_level_or_dict,
        complexity_score_or_features=None,
        confidence: Optional[float] = None,
        features: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Recommend model based on complexity level and scores.

        Supports two calling conventions:
            1. recommend('simple', 0.2, 0.9) — positional args
            2. recommend({'level': 'simple', 'score': 0.2, 'confidence': 0.9}, features) — dict

        Returns:
            Dictionary with model recommendation details
        """
        if isinstance(complexity_level_or_dict, dict):
            # Old dict-based API
            classification = complexity_level_or_dict
            level = classification.get('level', classification.get('complexity_level', 'medium'))
            complexity_score = classification.get('score', classification.get('complexity_score', 0.5))
            classification_confidence = classification.get('confidence', 0.5)
            features = complexity_score_or_features  # second arg is features in old API
        else:
            # New positional API
            level = complexity_level_or_dict
            complexity_score = complexity_score_or_features if complexity_score_or_features is not None else 0.5
            classification_confidence = confidence if confidence is not None else 0.5
        
        # Get base model for complexity level
        model_config = self._get_model_for_level(level)
        
        # Apply strategy-specific adjustments
        model_config = self._apply_strategy(model_config, level, features)
        
        # Calculate routing confidence
        routing_confidence = self._calculate_routing_confidence(
            classification_confidence,
            complexity_score
        )
        
        # Estimate cost and latency
        cost_estimate = self._estimate_cost(model_config, features)
        latency_estimate = self._estimate_latency(model_config, features)
        
        # Get fallback chain
        fallback_chain = self._get_fallback_chain(level, model_config)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            level,
            model_config,
            self._strategy_enum,
            complexity_score
        )
        
        # Build full model identifier
        full_model = f"{model_config.provider}:{model_config.model}"

        # Return dictionary for test compatibility
        return {
            'model': full_model,
            'provider': model_config.provider,
            'model_name': model_config.model,
            'complexity_level': level,
            'confidence': routing_confidence,
            'cost_estimate': cost_estimate,
            'latency_estimate': latency_estimate,
            'fallback_models': fallback_chain,
            'strategy_used': self.strategy,
            'reasoning': reasoning
        }
    
    def _get_model_for_level(self, level: str) -> ModelConfig:
        """
        Get base model configuration for complexity level.
        
        Args:
            level: Complexity level (simple/medium/complex)
            
        Returns:
            ModelConfig for the level
        """
        return self.model_mappings.get(level, self.model_mappings['medium'])
    
    def _apply_strategy(
        self, 
        base_config: ModelConfig,
        level: str,
        features: Optional[Dict[str, Any]] = None
    ) -> ModelConfig:
        """
        Apply strategy-specific model selection.
        
        Args:
            base_config: Base model configuration
            level: Complexity level
            features: Optional features for advanced routing
            
        Returns:
            Adjusted ModelConfig based on strategy
        """
        # Check for strategy overrides
        if self._strategy_enum in self.STRATEGY_OVERRIDES:
            overrides = self.STRATEGY_OVERRIDES[self._strategy_enum]
            if level in overrides:
                # Parse override model string
                model_str = overrides[level]
                provider, model = model_str.split(':', 1)
                
                # Create new config with override
                return ModelConfig(
                    provider=provider,
                    model=model,
                    max_cost_per_query=self._get_model_cost(provider, model),
                    avg_latency_ms=self._get_model_latency(provider, model),
                    quality_score=self._get_model_quality(provider, model)
                )
        
        # Additional strategy-specific logic
        if self._strategy_enum == RoutingStrategy.COST_OPTIMIZED:
            # Consider downgrading if features suggest simpler query
            if features and features.get('composite_features', {}).get('is_simple_lookup'):
                return self._get_model_for_level('simple')
        
        elif self._strategy_enum == RoutingStrategy.QUALITY_FIRST:
            # Consider upgrading if features suggest complexity
            if features and features.get('composite_features', {}).get('requires_deep_understanding'):
                return self._get_model_for_level('complex')
        
        return base_config
    
    def _calculate_routing_confidence(
        self,
        classification_confidence: float,
        complexity_score: float
    ) -> float:
        """
        Calculate confidence in routing decision.
        
        Args:
            classification_confidence: Confidence from classifier
            complexity_score: Raw complexity score
            
        Returns:
            Routing confidence (0.0-1.0)
        """
        # Base confidence from classification
        base_confidence = classification_confidence
        
        # Adjust based on strategy alignment
        strategy_adjustment = 0.0
        
        if self._strategy_enum == RoutingStrategy.BALANCED:
            # Balanced strategy has high confidence in middle ranges
            if 0.3 < complexity_score < 0.7:
                strategy_adjustment = 0.05
        elif self._strategy_enum == RoutingStrategy.COST_OPTIMIZED:
            # Cost strategy has high confidence for simple queries
            if complexity_score < 0.4:
                strategy_adjustment = 0.08
        elif self._strategy_enum == RoutingStrategy.QUALITY_FIRST:
            # Quality strategy has high confidence for complex queries
            if complexity_score > 0.6:
                strategy_adjustment = 0.08
        
        return min(1.0, base_confidence + strategy_adjustment)
    
    def _estimate_cost(
        self,
        model_config: ModelConfig,
        features: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Estimate cost per query.
        
        Args:
            model_config: Model configuration
            features: Optional features for token estimation
            
        Returns:
            Estimated cost in dollars
        """
        # Get base cost
        base_cost = model_config.max_cost_per_query
        
        # Adjust based on estimated tokens
        if features:
            # Estimate tokens from query length
            word_count = features.get('length_features', {}).get('word_count', 10)
            estimated_tokens = word_count * 1.5  # Rough estimate
            
            # Look up per-token cost
            provider = model_config.provider
            model = model_config.model
            
            if provider in self.COST_PER_1K_TOKENS:
                provider_costs = self.COST_PER_1K_TOKENS[provider]
                if isinstance(provider_costs, dict):
                    token_cost = provider_costs.get(model, 0.001)
                else:
                    token_cost = provider_costs
                
                # Calculate cost (input + output tokens)
                estimated_cost = (estimated_tokens * 2 / 1000) * token_cost
                
                # Apply cost multiplier if configured
                multiplier = self.cost_multipliers.get(provider, 1.0)
                estimated_cost *= multiplier
                
                return min(base_cost, estimated_cost)
        
        return base_cost
    
    def _estimate_latency(
        self,
        model_config: ModelConfig,
        features: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Estimate response latency.
        
        Args:
            model_config: Model configuration
            features: Optional features for latency adjustment
            
        Returns:
            Estimated latency in milliseconds
        """
        base_latency = model_config.avg_latency_ms
        
        # Adjust based on query complexity
        if features:
            complexity_features = features.get('composite_features', {})
            
            # Longer queries take more time
            if complexity_features.get('structural_complexity', 0) > 0.7:
                base_latency = int(base_latency * 1.3)
            
            # Technical queries may require more processing
            if complexity_features.get('technical_depth', 0) > 0.6:
                base_latency = int(base_latency * 1.2)
        
        return base_latency
    
    def _get_fallback_chain(
        self,
        level: str,
        primary_config: ModelConfig
    ) -> List[str]:
        """
        Get fallback model chain.
        
        Args:
            level: Complexity level
            primary_config: Primary model configuration
            
        Returns:
            List of fallback model identifiers
        """
        # Get default chain for level
        default_chain = self.fallback_chains.get(level, [])
        
        # Filter out primary model
        primary_model = f"{primary_config.provider}:{primary_config.model}"
        fallback_chain = [m for m in default_chain if m != primary_model]
        
        # Ensure at least one fallback
        if not fallback_chain and default_chain:
            fallback_chain = default_chain[:1]
        
        return fallback_chain
    
    def _get_model_cost(self, provider: str, model: str) -> float:
        """Get estimated cost for a model."""
        if provider in self.COST_PER_1K_TOKENS:
            provider_costs = self.COST_PER_1K_TOKENS[provider]
            if isinstance(provider_costs, dict):
                return provider_costs.get(model, 0.01)
            return provider_costs
        return 0.01  # Default cost
    
    def _get_model_latency(self, provider: str, model: str) -> int:
        """Get estimated latency for a model."""
        # Rough estimates based on provider and model size
        latency_map = {
            'local': 500,  # Local, fast
            'mistral': 1000,  # API, moderate
            'openai': 1500,  # API, varies
            'anthropic': 2000  # API, generally slower
        }
        
        base_latency = latency_map.get(provider, 1500)
        
        # Adjust for model size
        if 'tiny' in model or '3b' in model:
            return int(base_latency * 0.7)
        elif 'small' in model or '7b' in model:
            return base_latency
        elif 'turbo' in model:
            return int(base_latency * 1.2)
        elif 'gpt-4' in model or 'opus' in model:
            return int(base_latency * 1.5)
        
        return base_latency
    
    def _get_model_quality(self, provider: str, model: str) -> float:
        """Get quality score for a model."""
        # Rough quality estimates
        quality_map = {
            LOCAL.model: 0.6,
            'mistral-tiny': 0.65,
            'mistral-small': 0.75,
            'gpt-3.5-turbo': 0.85,
            'gpt-4-turbo': 0.95,
            'gpt-4': 0.97,
            'claude-3-haiku': 0.8,
            'claude-3-sonnet': 0.9,
            'claude-3-opus': 0.98
        }
        
        return quality_map.get(model, 0.7)
    
    def _generate_reasoning(
        self,
        level: str,
        model_config: ModelConfig,
        strategy: RoutingStrategy,
        complexity_score: float
    ) -> str:
        """
        Generate human-readable reasoning for recommendation.
        
        Args:
            level: Complexity level
            model_config: Selected model configuration
            strategy: Routing strategy used
            complexity_score: Raw complexity score
            
        Returns:
            Reasoning string
        """
        model_name = f"{model_config.provider}:{model_config.model}"
        
        reasoning = f"Selected {model_name} for {level} query (score: {complexity_score:.2f}). "
        
        # Strategy-specific reasoning
        if strategy == RoutingStrategy.COST_OPTIMIZED:
            reasoning += f"Cost-optimized selection with estimated cost ${model_config.max_cost_per_query:.3f}."
        elif strategy == RoutingStrategy.QUALITY_FIRST:
            reasoning += f"Quality-first selection with quality score {model_config.quality_score:.2f}."
        elif strategy == RoutingStrategy.LATENCY_OPTIMIZED:
            reasoning += f"Latency-optimized selection with ~{model_config.avg_latency_ms}ms response time."
        else:
            reasoning += "Balanced selection considering cost, quality, and latency."
        
        return reasoning
    
    def recommend_model(
        self, 
        complexity_score: float, 
        complexity_level: str, 
        strategy: str = 'balanced'
    ) -> str:
        """
        Recommend model based on complexity score and level.
        
        This method provides a simplified interface for the Epic1MLAnalyzer
        that returns just the model identifier string.
        
        Args:
            complexity_score: Complexity score (0.0-1.0)
            complexity_level: Complexity level ('simple', 'medium', 'complex')
            strategy: Routing strategy ('balanced', 'cost_optimized', etc.)
            
        Returns:
            Model identifier string (e.g., 'local:qwen2.5-1.5b-instruct')
        """
        # Create classification dictionary for internal recommend method
        classification = {
            'level': complexity_level,
            'score': complexity_score,
            'confidence': 0.8  # Default confidence
        }
        
        # Create features dictionary with basic info
        features = {
            'length_features': {
                'word_count': max(10, int(complexity_score * 50))  # Rough estimate
            },
            'composite_features': {
                'structural_complexity': complexity_score,
                'technical_depth': complexity_score * 0.8,
                'is_simple_lookup': complexity_score < 0.3,
                'requires_deep_understanding': complexity_score > 0.7
            }
        }
        
        # Temporarily update strategy if different from default
        original_strategy = self.strategy
        try:
            if strategy != self.strategy:
                try:
                    self._strategy_enum = RoutingStrategy(strategy)
                    self.strategy = self._strategy_enum.value
                except ValueError:
                    logger.warning(f"Unknown strategy {strategy}, using {original_strategy}")
            
            # Get full recommendation
            recommendation = self.recommend(classification, features)
            
            # Return just the model identifier
            return recommendation['model']
            
        finally:
            # Restore original strategy
            self.strategy = original_strategy
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get recommender configuration statistics."""
        return {
            'strategy': self.strategy,
            'model_mappings': {
                level: f"{config.provider}:{config.model}"
                for level, config in self.model_mappings.items()
            },
            'fallback_chains': self.fallback_chains,
            'available_strategies': [s.value for s in RoutingStrategy]
        }