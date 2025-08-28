"""Component implementations for the modular RAG system."""

# Import all component modules to trigger auto-registration
from . import processors
from . import embedders
from . import retrievers
from . import generators
from . import query_processors

__all__ = [
    'processors',
    'embedders', 
    'retrievers',
    'generators',
    'query_processors'
]