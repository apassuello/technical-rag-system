"""Component implementations for the modular RAG system."""

# Import all component modules to trigger auto-registration
from . import processors
from . import embedders
from . import vector_stores
from . import retrievers
from . import generators

__all__ = [
    'processors',
    'embedders', 
    'vector_stores',
    'retrievers',
    'generators'
]