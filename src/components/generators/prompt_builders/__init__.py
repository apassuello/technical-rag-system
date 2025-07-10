"""
Prompt builders for answer generation.

This module provides various prompt building strategies for constructing
effective prompts from queries and context documents.
"""

from .simple_prompt import SimplePromptBuilder

# Future builders will be imported here
# from .chain_of_thought import ChainOfThoughtPromptBuilder
# from .few_shot import FewShotPromptBuilder

__all__ = [
    'SimplePromptBuilder',
    # 'ChainOfThoughtPromptBuilder',
    # 'FewShotPromptBuilder',
]

# Builder registry for easy lookup
BUILDER_REGISTRY = {
    'simple': SimplePromptBuilder,
    # 'chain_of_thought': ChainOfThoughtPromptBuilder,
    # 'few_shot': FewShotPromptBuilder,
}

def get_builder_class(builder_type: str):
    """
    Get prompt builder class by type.
    
    Args:
        builder_type: Builder type name
        
    Returns:
        Builder class
        
    Raises:
        ValueError: If builder type not found
    """
    if builder_type not in BUILDER_REGISTRY:
        raise ValueError(f"Unknown prompt builder: {builder_type}. Available: {list(BUILDER_REGISTRY.keys())}")
    return BUILDER_REGISTRY[builder_type]