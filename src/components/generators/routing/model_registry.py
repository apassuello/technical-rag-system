"""
Model Registry for Multi-Model LLM Selection.

This module provides a registry of available models with their capabilities,
costs, and performance characteristics for the Epic 1 multi-model routing system.
"""

from decimal import Decimal
from typing import List

from .routing_strategies import ModelOption


class ModelRegistry:
    """Registry of available models with their capabilities and costs."""
    
    def __init__(self):
        """Initialize model registry with available models."""
        self.models = {
            'simple': [
                ModelOption(
                    provider='ollama',
                    model='llama3.2:3b',
                    estimated_cost=Decimal('0.0000'),
                    estimated_quality=0.75,
                    estimated_latency_ms=100,
                    confidence=0.95,
                    fallback_options=[]
                ),
                ModelOption(
                    provider='mistral',
                    model='mistral-tiny',
                    estimated_cost=Decimal('0.00025'),
                    estimated_quality=0.78,
                    estimated_latency_ms=200,
                    confidence=0.90,
                    fallback_options=[]
                ),
            ],
            'medium': [
                ModelOption(
                    provider='ollama',
                    model='llama3.2:3b',
                    estimated_cost=Decimal('0.0000'),
                    estimated_quality=0.75,
                    estimated_latency_ms=150,
                    confidence=0.92,
                    fallback_options=[]
                ),
                ModelOption(
                    provider='mistral',
                    model='mistral-small',
                    estimated_cost=Decimal('0.001'),
                    estimated_quality=0.87,
                    estimated_latency_ms=300,
                    confidence=0.92,
                    fallback_options=[]
                ),
                ModelOption(
                    provider='openai',
                    model='gpt-3.5-turbo',
                    estimated_cost=Decimal('0.002'),
                    estimated_quality=0.88,
                    estimated_latency_ms=400,
                    confidence=0.93,
                    fallback_options=[]
                ),
            ],
            'complex': [
                ModelOption(
                    provider='ollama',
                    model='llama3.2:3b',
                    estimated_cost=Decimal('0.0000'),
                    estimated_quality=0.82,
                    estimated_latency_ms=200,
                    confidence=0.88,
                    fallback_options=[]
                ),
                ModelOption(
                    provider='mistral',
                    model='mistral-large',
                    estimated_cost=Decimal('0.016'),
                    estimated_quality=0.90,
                    estimated_latency_ms=500,
                    confidence=0.94,
                    fallback_options=[]
                ),
                ModelOption(
                    provider='openai',
                    model='gpt-4-turbo',
                    estimated_cost=Decimal('0.03'),
                    estimated_quality=0.95,
                    estimated_latency_ms=800,
                    confidence=0.95,
                    fallback_options=[]
                ),
            ]
        }
    
    def get_all_models(self) -> List[ModelOption]:
        """Get all available models."""
        all_models = []
        for tier_models in self.models.values():
            all_models.extend(tier_models)
        return all_models
    
    def get_models_for_complexity(self, complexity: str) -> List[ModelOption]:
        """Get models appropriate for complexity level."""
        return self.models.get(complexity.lower(), self.models['medium'])
    
    def get_models_within_budget(self, max_cost: Decimal) -> List[ModelOption]:
        """Get models within cost budget."""
        return [m for m in self.get_all_models() if m.estimated_cost <= max_cost]
    
    def get_model_by_provider(self, provider: str, model_name: str = None) -> List[ModelOption]:
        """Get models from specific provider."""
        all_models = self.get_all_models()
        provider_models = [m for m in all_models if m.provider == provider]
        
        if model_name:
            provider_models = [m for m in provider_models if m.model == model_name]
        
        return provider_models