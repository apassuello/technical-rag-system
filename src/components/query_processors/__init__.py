"""
Query Processor Components Module.

This module provides a complete implementation of the Query Processor component
following the established modular architecture patterns. The Query Processor
orchestrates the query execution workflow through configurable sub-components.

Key Components:
- QueryProcessor: Main orchestrator interface
- QueryAnalyzer: Extract query characteristics and optimize parameters
- ContextSelector: Select optimal documents within token limits  
- ResponseAssembler: Format consistent responses with citations

Architecture:
- Modular design with swappable sub-components
- Configuration-driven component selection
- Direct implementations for algorithms (minimal adapters)
- Comprehensive error handling and metrics

Usage Example:
    from src.components.query_processors import ModularQueryProcessor
    from src.components.query_processors.analyzers import NLPAnalyzer
    from src.components.query_processors.selectors import MMRSelector
    from src.components.query_processors.assemblers import RichAssembler
    
    # Create sub-components
    analyzer = NLPAnalyzer()
    selector = MMRSelector() 
    assembler = RichAssembler()
    
    # Create query processor
    processor = ModularQueryProcessor(
        retriever=retriever,
        generator=generator,
        analyzer=analyzer,
        selector=selector,
        assembler=assembler
    )
    
    # Process query
    answer = processor.process("What is RISC-V?")

Configuration Example:
    query_processor:
      type: "modular"
      analyzer:
        implementation: "nlp"
        config:
          model: "en_core_web_sm"
          extract_entities: true
      selector:
        implementation: "mmr"
        config:
          lambda_param: 0.5
          max_tokens: 2048
      assembler:
        implementation: "rich"
        config:
          include_sources: true
          format_citations: true
"""

from .base import (
    # Core interfaces
    QueryProcessor,
    QueryAnalyzer, 
    ContextSelector,
    ResponseAssembler,
    
    # Data structures
    QueryAnalysis,
    ContextSelection,
    QueryProcessorConfig,
    
    # Utilities
    validate_config,
    QueryProcessorMetrics
)

# Main implementation
from .modular_query_processor import ModularQueryProcessor

# Sub-component implementations
from .analyzers import NLPAnalyzer, RuleBasedAnalyzer
from .selectors import MMRSelector, TokenLimitSelector  
from .assemblers import StandardAssembler, RichAssembler

__all__ = [
    # Interfaces
    'QueryProcessor',
    'QueryAnalyzer',
    'ContextSelector', 
    'ResponseAssembler',
    
    # Data structures
    'QueryAnalysis',
    'ContextSelection',
    'QueryProcessorConfig',
    
    # Utilities
    'validate_config',
    'QueryProcessorMetrics',
    
    # Main implementation
    'ModularQueryProcessor',
    
    # Sub-component implementations
    'NLPAnalyzer',
    'RuleBasedAnalyzer', 
    'MMRSelector',
    'TokenLimitSelector',
    'StandardAssembler',
    'RichAssembler'
]

# Version information
__version__ = "1.0.0"
__author__ = "RAG Portfolio Project"
__description__ = "Modular Query Processor implementation following Swiss engineering standards"