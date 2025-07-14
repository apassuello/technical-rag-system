"""
Epic 2 Validation Test Suite.

This package provides comprehensive validation for all Epic 2 Advanced Retriever
implementations, including:

- Multi-backend infrastructure validation (FAISS/Weaviate)
- Graph-based retrieval validation (entities, relationships, graph search)
- Neural reranking validation (cross-encoder quality and performance)
- Complete 4-stage pipeline integration testing
- Performance benchmarking (<700ms latency target)
- Quality enhancement validation (>20% improvement)
- Portfolio readiness assessment (90-95% score target)

The validation suite follows Swiss engineering standards for comprehensive
testing and quality assurance.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

__version__ = "1.0.0"
__epic__ = "Epic 2 Complete Validation"
__status__ = "Production Ready"

# Import main validation classes
from .test_multi_backend_validation import MultiBackendValidator
from .test_graph_integration_validation import GraphIntegrationValidator
from .test_neural_reranking_validation import NeuralRerankingValidator
from .test_epic2_integration_validation import Epic2IntegrationValidator
from .test_epic2_performance_validation import Epic2PerformanceValidator
from .test_epic2_quality_validation import Epic2QualityValidator

__all__ = [
    "MultiBackendValidator",
    "GraphIntegrationValidator",
    "NeuralRerankingValidator",
    "Epic2IntegrationValidator",
    "Epic2PerformanceValidator",
    "Epic2QualityValidator",
]
