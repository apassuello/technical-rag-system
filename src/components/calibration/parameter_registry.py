"""
Parameter registry for the calibration system.

Implements the parameter registry component from calibration-system-spec.md
for centralized management of all tunable system parameters.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


@dataclass
class Parameter:
    """Represents a tunable parameter in the system."""
    name: str
    component: str
    path: str  # YAML path like "retriever.sparse.config.k1"
    current: Union[float, int, str, bool]
    min_value: Optional[Union[float, int]] = None
    max_value: Optional[Union[float, int]] = None
    step: Optional[Union[float, int]] = None
    param_type: str = "float"
    impacts: List[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        if self.impacts is None:
            self.impacts = []


class ParameterRegistry:
    """
    Central registry of all tunable parameters following calibration-system-spec.md.
    
    Manages parameter definitions, search spaces, and validation according to the
    specification for systematic parameter optimization.
    """

    def __init__(self):
        """Initialize parameter registry."""
        self.parameters: Dict[str, Parameter] = {}
        self._initialize_default_parameters()

    def _initialize_default_parameters(self):
        """Initialize default parameter definitions from spec."""
        # BM25 parameters - critical for document ranking
        self.register_parameter(Parameter(
            name="bm25_k1",
            component="sparse_retriever", 
            path="retriever.sparse.config.k1",
            current=1.2,
            min_value=0.5,
            max_value=2.5,
            step=0.1,
            param_type="float",
            impacts=["retrieval_precision", "retrieval_recall"],
            description="BM25 term frequency saturation parameter"
        ))

        self.register_parameter(Parameter(
            name="bm25_b",
            component="sparse_retriever",
            path="retriever.sparse.config.b", 
            current=0.25,  # Our optimized value
            min_value=0.0,
            max_value=1.0,
            step=0.05,
            param_type="float",
            impacts=["retrieval_precision", "document_length_bias"],
            description="BM25 document length normalization parameter"
        ))

        # RRF fusion parameters - critical for score combination
        self.register_parameter(Parameter(
            name="rrf_k",
            component="fusion_strategy",
            path="retriever.fusion.config.k",
            current=30,  # Our optimized value
            min_value=10,
            max_value=100,
            step=10,
            param_type="int",
            impacts=["fusion_quality", "score_discrimination"],
            description="RRF k parameter controlling score discriminative power"
        ))

        self.register_parameter(Parameter(
            name="dense_weight",
            component="fusion_strategy",
            path="retriever.fusion.config.weights.dense",
            current=0.8,  # Our optimized value
            min_value=0.1,
            max_value=0.9,
            step=0.05,
            param_type="float",
            impacts=["fusion_balance", "semantic_vs_lexical"],
            description="Weight for dense (semantic) retrieval in fusion"
        ))

        self.register_parameter(Parameter(
            name="sparse_weight", 
            component="fusion_strategy",
            path="retriever.fusion.config.weights.sparse",
            current=0.2,  # Our optimized value
            min_value=0.1,
            max_value=0.9,
            step=0.05,
            param_type="float",
            impacts=["fusion_balance", "semantic_vs_lexical"],
            description="Weight for sparse (BM25) retrieval in fusion"
        ))

        # Score-aware fusion parameters (Epic 2)
        self.register_parameter(Parameter(
            name="score_aware_score_weight",
            component="score_aware_fusion",
            path="retriever.fusion.config.score_weight",
            current=0.8,
            min_value=0.1,
            max_value=0.95,
            step=0.05,
            param_type="float",
            impacts=["score_preservation", "fusion_quality"],
            description="Score-aware fusion: weight for preserving semantic scores"
        ))

        self.register_parameter(Parameter(
            name="score_aware_rank_weight",
            component="score_aware_fusion", 
            path="retriever.fusion.config.rank_weight",
            current=0.15,
            min_value=0.05,
            max_value=0.4,
            step=0.05,
            param_type="float",
            impacts=["rank_stability", "fusion_robustness"],
            description="Score-aware fusion: weight for rank-based stability"
        ))

        # Neural reranking parameters (Epic 2)
        self.register_parameter(Parameter(
            name="neural_batch_size",
            component="neural_reranker",
            path="retriever.reranker.config.batch_size",
            current=32,
            min_value=8,
            max_value=128,
            step=8,
            param_type="int", 
            impacts=["neural_performance", "memory_usage"],
            description="Neural reranker batch size for cross-encoder processing"
        ))

        self.register_parameter(Parameter(
            name="neural_max_candidates",
            component="neural_reranker",
            path="retriever.reranker.config.max_candidates", 
            current=100,
            min_value=20,
            max_value=200,
            step=20,
            param_type="int",
            impacts=["neural_quality", "processing_time"],
            description="Maximum candidates for neural reranking"
        ))

        # Confidence scoring parameters
        self.register_parameter(Parameter(
            name="confidence_threshold",
            component="answer_generator",
            path="answer_generator.config.confidence_threshold",
            current=0.85,
            min_value=0.3,
            max_value=0.95,
            step=0.05,
            param_type="float",
            impacts=["answer_quality", "refusal_rate"],
            description="Minimum confidence threshold for generating answers"
        ))

    def register_parameter(self, parameter: Parameter) -> None:
        """Register a new parameter."""
        if parameter.name in self.parameters:
            logger.warning(f"Parameter {parameter.name} already exists, overwriting")
        
        self.parameters[parameter.name] = parameter
        logger.debug(f"Registered parameter: {parameter.name}")

    def get_parameter(self, name: str) -> Optional[Parameter]:
        """Get parameter by name."""
        return self.parameters.get(name)

    def get_parameters_for_component(self, component: str) -> List[Parameter]:
        """Get all parameters for a specific component."""
        return [p for p in self.parameters.values() if p.component == component]

    def get_search_space(self, parameter_names: List[str]) -> Dict[str, List[Any]]:
        """
        Generate search space for specified parameters.
        
        Args:
            parameter_names: List of parameter names to include in search
            
        Returns:
            Dictionary mapping parameter names to lists of values to search
        """
        search_space = {}
        
        for name in parameter_names:
            param = self.parameters.get(name)
            if not param:
                logger.warning(f"Parameter {name} not found in registry")
                continue
                
            if param.param_type in ["float", "int"]:
                if param.min_value is not None and param.max_value is not None and param.step:
                    # Generate range based on min, max, step
                    if param.param_type == "float":
                        values = []
                        current = param.min_value
                        while current <= param.max_value:
                            values.append(round(current, 3))
                            current += param.step
                    else:  # int
                        values = list(range(param.min_value, param.max_value + 1, param.step))
                    search_space[name] = values
                else:
                    # Use current value if no range specified
                    search_space[name] = [param.current]
            else:
                # For non-numeric parameters, use current value
                search_space[name] = [param.current]
                
        return search_space

    def get_parameter_impacts(self) -> Dict[str, List[str]]:
        """Get mapping of metrics to parameters that impact them."""
        impacts = {}
        for param in self.parameters.values():
            for impact in param.impacts:
                if impact not in impacts:
                    impacts[impact] = []
                impacts[impact].append(param.name)
        return impacts

    def validate_parameter_value(self, name: str, value: Any) -> bool:
        """Validate if a value is valid for the given parameter."""
        param = self.parameters.get(name)
        if not param:
            return False
            
        # Type check
        expected_type = {"float": float, "int": int, "str": str, "bool": bool}[param.param_type]
        if not isinstance(value, expected_type):
            return False
            
        # Range check for numeric types
        if param.param_type in ["float", "int"]:
            if param.min_value is not None and value < param.min_value:
                return False
            if param.max_value is not None and value > param.max_value:
                return False
                
        return True

    def update_parameter_current_value(self, name: str, value: Any) -> bool:
        """Update the current value of a parameter."""
        if not self.validate_parameter_value(name, value):
            logger.error(f"Invalid value {value} for parameter {name}")
            return False
            
        param = self.parameters[name]
        old_value = param.current
        param.current = value
        logger.info(f"Updated parameter {name}: {old_value} -> {value}")
        return True

    def export_parameter_values(self) -> Dict[str, Any]:
        """Export current parameter values for configuration update."""
        return {name: param.current for name, param in self.parameters.items()}

    def get_parameter_summary(self) -> str:
        """Get human-readable summary of all parameters."""
        summary = ["Parameter Registry Summary:", "=" * 40]
        
        for component in set(p.component for p in self.parameters.values()):
            summary.append(f"\n{component.upper()}:")
            component_params = self.get_parameters_for_component(component)
            for param in component_params:
                range_info = ""
                if param.min_value is not None and param.max_value is not None:
                    range_info = f" (range: {param.min_value}-{param.max_value})"
                summary.append(f"  {param.name}: {param.current}{range_info}")
                if param.description:
                    summary.append(f"    {param.description}")
                    
        return "\n".join(summary)

    def load_from_config(self, config_path: Path) -> None:
        """Load parameter values from a configuration file.""" 
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Extract parameter values based on their paths
            for param in self.parameters.values():
                value = self._extract_value_from_path(config, param.path)
                if value is not None:
                    self.update_parameter_current_value(param.name, value)
                    
            logger.info(f"Loaded parameters from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load parameters from {config_path}: {e}")

    def _extract_value_from_path(self, config: Dict[str, Any], path: str) -> Any:
        """Extract value from nested config using dot-separated path."""
        parts = path.split('.')
        current = config
        
        try:
            for part in parts:
                current = current[part]
            return current
        except (KeyError, TypeError):
            return None


if __name__ == "__main__":
    # Test the parameter registry
    registry = ParameterRegistry()
    print(registry.get_parameter_summary())
    
    # Test search space generation
    search_space = registry.get_search_space(["bm25_k1", "bm25_b", "rrf_k"])
    print(f"\nSearch space example: {search_space}")