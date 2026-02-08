"""Component implementations for the modular RAG system."""

# Import all component modules to trigger auto-registration
from . import embedders, generators, processors, query_processors, retrievers

__all__ = [
    'processors',
    'embedders', 
    'retrievers',
    'generators',
    'query_processors'
]