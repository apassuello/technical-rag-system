"""
A/B Testing Framework for Prompt Optimization.

This module provides systematic prompt optimization through A/B testing,
performance analysis, and automated prompt variation generation.
"""

import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import numpy as np
from collections import defaultdict
import logging

from .prompt_templates import QueryType, PromptTemplate, TechnicalPromptTemplates


class OptimizationMetric(Enum):
    """Metrics for evaluating prompt performance."""
    RESPONSE_TIME = "response_time"
    CONFIDENCE_SCORE = "confidence_score"
    CITATION_COUNT = "citation_count"
    ANSWER_LENGTH = "answer_length"
    TECHNICAL_ACCURACY = "technical_accuracy"
    USER_SATISFACTION = "user_satisfaction"


@dataclass
class PromptVariation:
    """Represents a prompt variation for A/B testing."""
    variation_id: str
    name: str
    description: str
    template: PromptTemplate
    query_type: QueryType
    created_at: float
    metadata: Dict[str, Any]


@dataclass
class TestResult:
    """Represents a single test result."""
    variation_id: str
    query: str
    query_type: QueryType
    response_time: float
    confidence_score: float
    citation_count: int
    answer_length: int
    technical_accuracy: Optional[float] = None
    user_satisfaction: Optional[float] = None
    timestamp: float = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ComparisonResult:
    """Results of A/B test comparison."""
    variation_a: str
    variation_b: str
    metric: OptimizationMetric
    a_mean: float
    b_mean: float
    improvement_percent: float
    p_value: float
    confidence_interval: Tuple[float, float]
    is_significant: bool
    sample_size: int
    recommendation: str


class PromptOptimizer:
    """
    A/B testing framework for systematic prompt optimization.
    
    Features:
    - Automated prompt variation generation
    - Performance metric tracking
    - Statistical significance testing
    - Recommendation engine
    - Persistence and experiment tracking
    """
    
    def __init__(self, experiment_dir: str = "experiments"):
        """
        Initialize the prompt optimizer.
        
        Args:
            experiment_dir: Directory to store experiment data
        """
        self.experiment_dir = Path(experiment_dir)
        self.experiment_dir.mkdir(exist_ok=True)
        
        self.variations: Dict[str, PromptVariation] = {}
        self.test_results: List[TestResult] = []
        self.active_experiments: Dict[str, List[str]] = {}
        
        # Load existing experiments
        self._load_experiments()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def create_variation(
        self,
        base_template: PromptTemplate,
        query_type: QueryType,
        variation_name: str,
        modifications: Dict[str, str],
        description: str = ""
    ) -> str:
        """
        Create a new prompt variation.
        
        Args:
            base_template: Base template to modify
            query_type: Type of query this variation is for
            variation_name: Human-readable name
            modifications: Dict of template field modifications
            description: Description of the variation
            
        Returns:
            Variation ID
        """
        variation_id = f"{query_type.value}_{variation_name}_{int(time.time())}"
        
        # Create modified template
        modified_template = PromptTemplate(
            system_prompt=modifications.get("system_prompt", base_template.system_prompt),
            context_format=modifications.get("context_format", base_template.context_format),
            query_format=modifications.get("query_format", base_template.query_format),
            answer_guidelines=modifications.get("answer_guidelines", base_template.answer_guidelines)
        )
        
        variation = PromptVariation(
            variation_id=variation_id,
            name=variation_name,
            description=description,
            template=modified_template,
            query_type=query_type,
            created_at=time.time(),
            metadata=modifications
        )
        
        self.variations[variation_id] = variation
        self._save_variation(variation)
        
        self.logger.info(f"Created variation: {variation_id}")
        return variation_id
    
    def create_temperature_variations(
        self,
        base_query_type: QueryType,
        temperatures: List[float] = [0.3, 0.5, 0.7, 0.9]
    ) -> List[str]:
        """
        Create variations with different temperature settings.
        
        Args:
            base_query_type: Query type to create variations for
            temperatures: List of temperature values to test
            
        Returns:
            List of variation IDs
        """
        base_template = TechnicalPromptTemplates.get_template_for_query("")
        if base_query_type != QueryType.GENERAL:
            template_map = {
                QueryType.DEFINITION: TechnicalPromptTemplates.get_definition_template,
                QueryType.IMPLEMENTATION: TechnicalPromptTemplates.get_implementation_template,
                QueryType.COMPARISON: TechnicalPromptTemplates.get_comparison_template,
                QueryType.SPECIFICATION: TechnicalPromptTemplates.get_specification_template,
                QueryType.CODE_EXAMPLE: TechnicalPromptTemplates.get_code_example_template,
                QueryType.HARDWARE_CONSTRAINT: TechnicalPromptTemplates.get_hardware_constraint_template,
                QueryType.TROUBLESHOOTING: TechnicalPromptTemplates.get_troubleshooting_template,
            }
            base_template = template_map[base_query_type]()
        
        variation_ids = []
        for temp in temperatures:
            temp_modification = {
                "system_prompt": base_template.system_prompt + f"\n\nGenerate responses with temperature={temp} (creativity level).",
                "answer_guidelines": base_template.answer_guidelines + f"\n\nAdjust response creativity to temperature={temp}."
            }
            
            variation_id = self.create_variation(
                base_template=base_template,
                query_type=base_query_type,
                variation_name=f"temp_{temp}",
                modifications=temp_modification,
                description=f"Temperature variation with {temp} creativity level"
            )
            variation_ids.append(variation_id)
        
        return variation_ids
    
    def create_length_variations(
        self,
        base_query_type: QueryType,
        length_styles: List[str] = ["concise", "detailed", "comprehensive"]
    ) -> List[str]:
        """
        Create variations with different response length preferences.
        
        Args:
            base_query_type: Query type to create variations for
            length_styles: List of length styles to test
            
        Returns:
            List of variation IDs
        """
        base_template = TechnicalPromptTemplates.get_template_for_query("")
        if base_query_type != QueryType.GENERAL:
            template_map = {
                QueryType.DEFINITION: TechnicalPromptTemplates.get_definition_template,
                QueryType.IMPLEMENTATION: TechnicalPromptTemplates.get_implementation_template,
                QueryType.COMPARISON: TechnicalPromptTemplates.get_comparison_template,
                QueryType.SPECIFICATION: TechnicalPromptTemplates.get_specification_template,
                QueryType.CODE_EXAMPLE: TechnicalPromptTemplates.get_code_example_template,
                QueryType.HARDWARE_CONSTRAINT: TechnicalPromptTemplates.get_hardware_constraint_template,
                QueryType.TROUBLESHOOTING: TechnicalPromptTemplates.get_troubleshooting_template,
            }
            base_template = template_map[base_query_type]()
        
        length_prompts = {
            "concise": "Be concise and focus on essential information only. Aim for 2-3 sentences per point.",
            "detailed": "Provide detailed explanations with examples. Aim for comprehensive coverage.",
            "comprehensive": "Provide exhaustive detail with multiple examples, edge cases, and related concepts."
        }
        
        variation_ids = []
        for style in length_styles:
            length_modification = {
                "answer_guidelines": base_template.answer_guidelines + f"\n\nResponse style: {length_prompts[style]}"
            }
            
            variation_id = self.create_variation(
                base_template=base_template,
                query_type=base_query_type,
                variation_name=f"length_{style}",
                modifications=length_modification,
                description=f"Length variation with {style} response style"
            )
            variation_ids.append(variation_id)
        
        return variation_ids
    
    def create_citation_variations(
        self,
        base_query_type: QueryType,
        citation_styles: List[str] = ["minimal", "standard", "extensive"]
    ) -> List[str]:
        """
        Create variations with different citation requirements.
        
        Args:
            base_query_type: Query type to create variations for
            citation_styles: List of citation styles to test
            
        Returns:
            List of variation IDs
        """
        base_template = TechnicalPromptTemplates.get_template_for_query("")
        if base_query_type != QueryType.GENERAL:
            template_map = {
                QueryType.DEFINITION: TechnicalPromptTemplates.get_definition_template,
                QueryType.IMPLEMENTATION: TechnicalPromptTemplates.get_implementation_template,
                QueryType.COMPARISON: TechnicalPromptTemplates.get_comparison_template,
                QueryType.SPECIFICATION: TechnicalPromptTemplates.get_specification_template,
                QueryType.CODE_EXAMPLE: TechnicalPromptTemplates.get_code_example_template,
                QueryType.HARDWARE_CONSTRAINT: TechnicalPromptTemplates.get_hardware_constraint_template,
                QueryType.TROUBLESHOOTING: TechnicalPromptTemplates.get_troubleshooting_template,
            }
            base_template = template_map[base_query_type]()
        
        citation_prompts = {
            "minimal": "Use [chunk_X] citations only for direct quotes or specific claims.",
            "standard": "Include [chunk_X] citations for each major point or claim.",
            "extensive": "Provide [chunk_X] citations for every statement. Use multiple citations per point where relevant."
        }
        
        variation_ids = []
        for style in citation_styles:
            citation_modification = {
                "answer_guidelines": base_template.answer_guidelines + f"\n\nCitation style: {citation_prompts[style]}"
            }
            
            variation_id = self.create_variation(
                base_template=base_template,
                query_type=base_query_type,
                variation_name=f"citation_{style}",
                modifications=citation_modification,
                description=f"Citation variation with {style} citation requirements"
            )
            variation_ids.append(variation_id)
        
        return variation_ids
    
    def setup_experiment(
        self,
        experiment_name: str,
        variation_ids: List[str],
        test_queries: List[str]
    ) -> str:
        """
        Set up a new A/B test experiment.
        
        Args:
            experiment_name: Name of the experiment
            variation_ids: List of variation IDs to test
            test_queries: List of test queries
            
        Returns:
            Experiment ID
        """
        experiment_id = f"exp_{experiment_name}_{int(time.time())}"
        
        experiment_config = {
            "experiment_id": experiment_id,
            "name": experiment_name,
            "variation_ids": variation_ids,
            "test_queries": test_queries,
            "created_at": time.time(),
            "status": "active"
        }
        
        self.active_experiments[experiment_id] = variation_ids
        
        # Save experiment config
        experiment_file = self.experiment_dir / f"{experiment_id}.json"
        with open(experiment_file, 'w') as f:
            json.dump(experiment_config, f, indent=2)
        
        self.logger.info(f"Created experiment: {experiment_id}")
        return experiment_id
    
    def record_test_result(
        self,
        variation_id: str,
        query: str,
        query_type: QueryType,
        response_time: float,
        confidence_score: float,
        citation_count: int,
        answer_length: int,
        technical_accuracy: Optional[float] = None,
        user_satisfaction: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a test result for analysis.
        
        Args:
            variation_id: ID of the variation tested
            query: The query that was tested
            query_type: Type of the query
            response_time: Response time in seconds
            confidence_score: Confidence score (0-1)
            citation_count: Number of citations in response
            answer_length: Length of answer in characters
            technical_accuracy: Optional technical accuracy score (0-1)
            user_satisfaction: Optional user satisfaction score (0-1)
            metadata: Optional additional metadata
        """
        result = TestResult(
            variation_id=variation_id,
            query=query,
            query_type=query_type,
            response_time=response_time,
            confidence_score=confidence_score,
            citation_count=citation_count,
            answer_length=answer_length,
            technical_accuracy=technical_accuracy,
            user_satisfaction=user_satisfaction,
            metadata=metadata or {}
        )
        
        self.test_results.append(result)
        self._save_test_result(result)
        
        self.logger.info(f"Recorded test result for variation: {variation_id}")
    
    def analyze_variations(
        self,
        variation_a: str,
        variation_b: str,
        metric: OptimizationMetric,
        min_samples: int = 10
    ) -> ComparisonResult:
        """
        Analyze performance difference between two variations.
        
        Args:
            variation_a: First variation ID
            variation_b: Second variation ID
            metric: Metric to compare
            min_samples: Minimum samples required for analysis
            
        Returns:
            Comparison result with statistical analysis
        """
        # Filter results for each variation
        results_a = [r for r in self.test_results if r.variation_id == variation_a]
        results_b = [r for r in self.test_results if r.variation_id == variation_b]
        
        if len(results_a) < min_samples or len(results_b) < min_samples:
            raise ValueError(f"Insufficient samples. Need at least {min_samples} for each variation.")
        
        # Extract metric values
        values_a = self._extract_metric_values(results_a, metric)
        values_b = self._extract_metric_values(results_b, metric)
        
        # Calculate statistics
        mean_a = np.mean(values_a)
        mean_b = np.mean(values_b)
        
        # Calculate improvement percentage
        improvement = ((mean_b - mean_a) / mean_a) * 100
        
        # Simple t-test (normally would use scipy.stats.ttest_ind)
        # For now, using basic statistical comparison
        std_a = np.std(values_a)
        std_b = np.std(values_b)
        n_a = len(values_a)
        n_b = len(values_b)
        
        # Basic p-value estimation (simplified)
        pooled_std = np.sqrt(((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2))
        t_stat = (mean_b - mean_a) / (pooled_std * np.sqrt(1/n_a + 1/n_b))
        p_value = 2 * (1 - abs(t_stat) / (abs(t_stat) + 1))  # Rough approximation
        
        # Confidence interval (simplified)
        margin_of_error = 1.96 * pooled_std * np.sqrt(1/n_a + 1/n_b)
        ci_lower = (mean_b - mean_a) - margin_of_error
        ci_upper = (mean_b - mean_a) + margin_of_error
        
        # Determine significance
        is_significant = p_value < 0.05
        
        # Generate recommendation
        if is_significant:
            if improvement > 0:
                recommendation = f"Variation B shows significant improvement ({improvement:.1f}%). Recommend adopting variation B."
            else:
                recommendation = f"Variation A shows significant improvement ({-improvement:.1f}%). Recommend keeping variation A."
        else:
            recommendation = f"No significant difference detected (p={p_value:.3f}). More data needed or variations are equivalent."
        
        return ComparisonResult(
            variation_a=variation_a,
            variation_b=variation_b,
            metric=metric,
            a_mean=mean_a,
            b_mean=mean_b,
            improvement_percent=improvement,
            p_value=p_value,
            confidence_interval=(ci_lower, ci_upper),
            is_significant=is_significant,
            sample_size=min(n_a, n_b),
            recommendation=recommendation
        )
    
    def get_best_variation(
        self,
        query_type: QueryType,
        metric: OptimizationMetric,
        min_samples: int = 10
    ) -> Optional[str]:
        """
        Get the best performing variation for a query type and metric.
        
        Args:
            query_type: Type of query
            metric: Metric to optimize for
            min_samples: Minimum samples required
            
        Returns:
            Best variation ID or None if insufficient data
        """
        # Filter results by query type
        relevant_results = [r for r in self.test_results if r.query_type == query_type]
        
        # Group by variation
        variation_performance = defaultdict(list)
        for result in relevant_results:
            variation_performance[result.variation_id].append(result)
        
        # Calculate mean performance for each variation
        best_variation = None
        best_score = None
        
        for variation_id, results in variation_performance.items():
            if len(results) >= min_samples:
                values = self._extract_metric_values(results, metric)
                mean_score = np.mean(values)
                
                if best_score is None or mean_score > best_score:
                    best_score = mean_score
                    best_variation = variation_id
        
        return best_variation
    
    def generate_optimization_report(
        self,
        experiment_id: str,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive optimization report.
        
        Args:
            experiment_id: Experiment to analyze
            output_file: Optional file to save report
            
        Returns:
            Report dictionary
        """
        if experiment_id not in self.active_experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        variation_ids = self.active_experiments[experiment_id]
        experiment_results = [r for r in self.test_results if r.variation_id in variation_ids]
        
        if not experiment_results:
            raise ValueError(f"No results found for experiment {experiment_id}")
        
        # Analyze each metric
        metrics = [
            OptimizationMetric.RESPONSE_TIME,
            OptimizationMetric.CONFIDENCE_SCORE,
            OptimizationMetric.CITATION_COUNT,
            OptimizationMetric.ANSWER_LENGTH
        ]
        
        report = {
            "experiment_id": experiment_id,
            "variations_tested": len(variation_ids),
            "total_tests": len(experiment_results),
            "analysis_date": time.time(),
            "metric_analysis": {},
            "recommendations": []
        }
        
        # Analyze each metric across variations
        for metric in metrics:
            metric_data = {}
            for variation_id in variation_ids:
                var_results = [r for r in experiment_results if r.variation_id == variation_id]
                if var_results:
                    values = self._extract_metric_values(var_results, metric)
                    metric_data[variation_id] = {
                        "mean": np.mean(values),
                        "std": np.std(values),
                        "count": len(values)
                    }
            
            report["metric_analysis"][metric.value] = metric_data
        
        # Generate recommendations
        for metric in metrics:
            best_variation = self.get_best_variation(
                query_type=QueryType.GENERAL,  # Could be made more specific
                metric=metric,
                min_samples=5
            )
            if best_variation:
                report["recommendations"].append({
                    "metric": metric.value,
                    "best_variation": best_variation,
                    "variation_name": self.variations[best_variation].name
                })
        
        # Save report if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
        
        return report
    
    def _extract_metric_values(self, results: List[TestResult], metric: OptimizationMetric) -> List[float]:
        """Extract metric values from test results."""
        values = []
        for result in results:
            if metric == OptimizationMetric.RESPONSE_TIME:
                values.append(result.response_time)
            elif metric == OptimizationMetric.CONFIDENCE_SCORE:
                values.append(result.confidence_score)
            elif metric == OptimizationMetric.CITATION_COUNT:
                values.append(float(result.citation_count))
            elif metric == OptimizationMetric.ANSWER_LENGTH:
                values.append(float(result.answer_length))
            elif metric == OptimizationMetric.TECHNICAL_ACCURACY and result.technical_accuracy is not None:
                values.append(result.technical_accuracy)
            elif metric == OptimizationMetric.USER_SATISFACTION and result.user_satisfaction is not None:
                values.append(result.user_satisfaction)
        
        return values
    
    def _load_experiments(self) -> None:
        """Load existing experiments from disk."""
        if not self.experiment_dir.exists():
            return
        
        for file_path in self.experiment_dir.glob("*.json"):
            if file_path.name.startswith("exp_"):
                with open(file_path, 'r') as f:
                    config = json.load(f)
                    self.active_experiments[config["experiment_id"]] = config["variation_ids"]
        
        # Load variations and results
        for file_path in self.experiment_dir.glob("variation_*.json"):
            with open(file_path, 'r') as f:
                var_data = json.load(f)
                variation = PromptVariation(**var_data)
                self.variations[variation.variation_id] = variation
        
        for file_path in self.experiment_dir.glob("result_*.json"):
            with open(file_path, 'r') as f:
                result_data = json.load(f)
                result = TestResult(**result_data)
                self.test_results.append(result)
    
    def _save_variation(self, variation: PromptVariation) -> None:
        """Save variation to disk."""
        file_path = self.experiment_dir / f"variation_{variation.variation_id}.json"
        var_dict = asdict(variation)
        
        # Convert template to dict
        var_dict["template"] = asdict(variation.template)
        var_dict["query_type"] = variation.query_type.value
        
        with open(file_path, 'w') as f:
            json.dump(var_dict, f, indent=2)
    
    def _save_test_result(self, result: TestResult) -> None:
        """Save test result to disk."""
        file_path = self.experiment_dir / f"result_{int(result.timestamp)}.json"
        result_dict = asdict(result)
        result_dict["query_type"] = result.query_type.value
        
        with open(file_path, 'w') as f:
            json.dump(result_dict, f, indent=2)


# Example usage
if __name__ == "__main__":
    # Initialize optimizer
    optimizer = PromptOptimizer()
    
    # Create temperature variations for implementation queries
    temp_variations = optimizer.create_temperature_variations(
        base_query_type=QueryType.IMPLEMENTATION,
        temperatures=[0.3, 0.7]
    )
    
    # Create length variations for definition queries
    length_variations = optimizer.create_length_variations(
        base_query_type=QueryType.DEFINITION,
        length_styles=["concise", "detailed"]
    )
    
    # Setup experiment
    test_queries = [
        "How do I implement a timer interrupt in RISC-V?",
        "What is the difference between machine mode and user mode?",
        "Configure GPIO pins for input/output operations"
    ]
    
    experiment_id = optimizer.setup_experiment(
        experiment_name="temperature_vs_length",
        variation_ids=temp_variations + length_variations,
        test_queries=test_queries
    )
    
    print(f"Created experiment: {experiment_id}")
    print(f"Variations: {len(temp_variations + length_variations)}")
    print(f"Test queries: {len(test_queries)}")