"""
Adaptive Routing Engine for Multi-Model LLM Selection.

This module provides intelligent routing logic for Epic 1 multi-model answer
generation, enabling cost-effective model selection based on query complexity
analysis and optimization strategies.

Architecture Notes:
- Strategy pattern for different optimization goals
- Query complexity to model mapping logic
- Fallback chains for reliability
- Cost-aware routing decisions
- Performance monitoring integration

Available Components:
- AdaptiveRouter: Main routing orchestrator
- RoutingStrategy: Strategy pattern implementations  
- ModelSelector: Model selection logic
- FallbackManager: Reliability and failover handling
"""

from .adaptive_router import AdaptiveRouter, RoutingDecision
from .routing_strategies import (
    RoutingStrategy,
    CostOptimizedStrategy, 
    QualityFirstStrategy,
    BalancedStrategy,
    ModelOption
)

__all__ = [
    'AdaptiveRouter',
    'RoutingDecision',
    'RoutingStrategy',
    'CostOptimizedStrategy',
    'QualityFirstStrategy', 
    'BalancedStrategy',
    'ModelOption'
]