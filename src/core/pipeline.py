"""
RAG Pipeline - Legacy compatibility module.

This module now provides backward compatibility by delegating to the new
Platform Orchestrator architecture. The RAGPipeline class is deprecated
and will be removed in version 2.0.

Migration guide:
    Old: pipeline = RAGPipeline(config_path)
    New: orchestrator = PlatformOrchestrator(config_path)
"""

import warnings
from pathlib import Path

from .compatibility import RAGPipelineCompatibility

# Issue module-level deprecation warning when importing
warnings.filterwarnings('always', category=DeprecationWarning, module=__name__)


# Legacy class name for backward compatibility
class RAGPipeline(RAGPipelineCompatibility):
    """
    RAGPipeline - Deprecated legacy class.
    
    This class is maintained for backward compatibility only.
    Please migrate to PlatformOrchestrator for new code.
    
    Example migration:
        # Old code:
        pipeline = RAGPipeline("config.yaml")
        pipeline.index_document(Path("doc.pdf"))
        answer = pipeline.query("question")
        
        # New code:
        from core import PlatformOrchestrator
        orchestrator = PlatformOrchestrator("config.yaml")
        orchestrator.process_document(Path("doc.pdf"))
        answer = orchestrator.process_query("question")
    """
    pass