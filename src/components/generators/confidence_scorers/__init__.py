"""
Confidence scorers for answer generation.

This module provides various scoring methods to evaluate
the confidence and quality of generated answers.
"""

from .semantic_scorer import SemanticScorer

# Future scorers will be imported here
# from .perplexity_scorer import PerplexityScorer
# from .ensemble_scorer import EnsembleScorer

__all__ = [
    'SemanticScorer',
    # 'PerplexityScorer',
    # 'EnsembleScorer',
]

# Scorer registry for easy lookup
SCORER_REGISTRY = {
    'semantic': SemanticScorer,
    # 'perplexity': PerplexityScorer,
    # 'ensemble': EnsembleScorer,
}

def get_scorer_class(scorer_type: str):
    """
    Get confidence scorer class by type.
    
    Args:
        scorer_type: Scorer type name
        
    Returns:
        Scorer class
        
    Raises:
        ValueError: If scorer type not found
    """
    if scorer_type not in SCORER_REGISTRY:
        raise ValueError(f"Unknown confidence scorer: {scorer_type}. Available: {list(SCORER_REGISTRY.keys())}")
    return SCORER_REGISTRY[scorer_type]