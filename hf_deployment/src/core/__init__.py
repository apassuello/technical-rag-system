"""
Core module for Epic 2 HF Deployment.

This module provides the core interfaces and factory for Epic 2 components
in the HF deployment package.
"""

from .interfaces import (
    Document,
    RetrievalResult,
    Answer,
    ComponentBase,
    Retriever,
    HealthStatus
)

from .component_factory import ComponentFactory, epic2_factory

__all__ = [
    'Document',
    'RetrievalResult', 
    'Answer',
    'ComponentBase',
    'Retriever',
    'HealthStatus',
    'ComponentFactory',
    'epic2_factory'
]