"""
Epic 2 Validation Test Suite.

This package provides comprehensive validation for all Epic 2 Advanced Retriever
implementations, including:

- Configuration-driven feature activation validation
- Sub-component integration testing within ModularUnifiedRetriever
- Neural reranking validation (cross-encoder quality and performance)
- Graph enhancement validation (graph-enhanced fusion)
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

# Import main validation classes (NEW test suite)
from .test_epic2_configuration_validation_new import Epic2ConfigurationValidator
from .test_epic2_subcomponent_integration_new import Epic2SubComponentIntegrationValidator
from .test_epic2_performance_validation_new import Epic2PerformanceValidator
from .test_epic2_quality_validation_new import Epic2QualityValidator
from .test_epic2_pipeline_validation_new import Epic2PipelineValidator

__all__ = [
    "Epic2ConfigurationValidator",
    "Epic2SubComponentIntegrationValidator", 
    "Epic2PerformanceValidator",
    "Epic2QualityValidator",
    "Epic2PipelineValidator",
]
