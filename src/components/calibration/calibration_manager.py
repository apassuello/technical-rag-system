"""
Calibration manager for systematic parameter optimization.

Implements the main calibration manager from calibration-system-spec.md that
orchestrates parameter optimization, metrics collection, and system calibration.
"""

import logging
import time
import tempfile
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import yaml
from datetime import datetime

from .parameter_registry import ParameterRegistry, Parameter
from .metrics_collector import MetricsCollector, QueryMetrics
from .optimization_engine import OptimizationEngine, OptimizationStrategy, OptimizationResult
from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Document

logger = logging.getLogger(__name__)


class CalibrationManager:
    """
    Main calibration system orchestrator following calibration-system-spec.md.
    
    Provides systematic parameter optimization and confidence calibration through:
    - Parameter registry management
    - Automated metrics collection  
    - Multi-strategy optimization
    - Configuration generation
    - Quality validation
    """

    def __init__(self, platform_orchestrator: Optional[PlatformOrchestrator] = None):
        """
        Initialize calibration manager.
        
        Args:
            platform_orchestrator: Optional platform orchestrator instance
        """
        self.platform_orchestrator = platform_orchestrator
        self.parameter_registry = ParameterRegistry()
        self.metrics_collector = MetricsCollector()
        self.optimization_results: Dict[str, OptimizationResult] = {}
        self.calibration_history: List[Dict[str, Any]] = []
        
        # Golden test set for calibration
        self.test_queries: List[Dict[str, Any]] = []
        
    def load_test_set(self, test_set_path: Path) -> None:
        """Load golden test set for calibration."""
        try:
            with open(test_set_path, 'r') as f:
                test_data = yaml.safe_load(f)
                
            if 'test_cases' in test_data:
                self.test_queries = test_data['test_cases']
            else:
                # Assume entire file is list of test cases
                self.test_queries = test_data if isinstance(test_data, list) else []
                
            logger.info(f"Loaded {len(self.test_queries)} test queries from {test_set_path}")
            
        except Exception as e:
            logger.error(f"Failed to load test set from {test_set_path}: {e}")
            # Create basic test set if loading fails
            self._create_basic_test_set()

    def _create_basic_test_set(self) -> None:
        """Create basic test set for calibration."""
        self.test_queries = [
            {
                "test_id": "TC001",
                "category": "factual_simple",
                "query": "What is RISC-V?",
                "expected_behavior": {
                    "should_answer": True,
                    "min_confidence": 0.7,
                    "max_confidence": 0.95,
                    "must_contain_terms": ["instruction set", "open"],
                    "must_not_contain": ["ARM", "x86"],
                    "min_citations": 1
                }
            },
            {
                "test_id": "TC002", 
                "category": "technical_complex",
                "query": "How does RISC-V instruction encoding differ from ARM?",
                "expected_behavior": {
                    "should_answer": True,
                    "min_confidence": 0.5,
                    "max_confidence": 0.8,
                    "must_contain_terms": ["instruction", "encoding", "RISC-V"],
                    "min_citations": 2
                }
            },
            {
                "test_id": "TC003",
                "category": "edge_case",
                "query": "RISC-V quantum computing applications",
                "expected_behavior": {
                    "should_answer": True,
                    "max_confidence": 0.6,
                    "must_contain_terms": ["RISC-V"],
                    "min_citations": 1
                }
            }
        ]
        logger.info("Created basic test set with 3 test queries")

    def calibrate(
        self,
        test_set: Optional[Path] = None,
        strategy: OptimizationStrategy = OptimizationStrategy.GRID_SEARCH,
        target_metric: str = "overall_accuracy",
        parameters_to_optimize: Optional[List[str]] = None,
        max_evaluations: Optional[int] = None,
        base_config: Optional[Path] = None
    ) -> OptimizationResult:
        """
        Run full calibration following calibration-system-spec.md workflow.
        
        Args:
            test_set: Path to golden test set (optional, uses basic set if None)
            strategy: Optimization strategy to use
            target_metric: Metric to optimize
            parameters_to_optimize: List of parameter names to optimize (optional)
            max_evaluations: Maximum evaluations for optimization
            base_config: Base configuration file to use
            
        Returns:
            OptimizationResult with best parameters and performance data
        """
        logger.info("Starting full calibration process")
        
        # Load test set
        if test_set:
            self.load_test_set(test_set)
        elif not self.test_queries:
            self._create_basic_test_set()
        
        # Determine parameters to optimize
        if parameters_to_optimize is None:
            # Use key parameters identified as most impactful
            parameters_to_optimize = [
                "bm25_k1", "bm25_b", "rrf_k", 
                "dense_weight", "sparse_weight",
                "score_aware_score_weight", "score_aware_rank_weight"
            ]
        
        # Generate search space
        search_space = self.parameter_registry.get_search_space(parameters_to_optimize)
        logger.info(f"Optimizing {len(parameters_to_optimize)} parameters with {len(list(search_space.values())[0]) if search_space else 0} combinations")
        
        # Create evaluation function
        evaluation_func = self._create_evaluation_function(base_config, target_metric)
        
        # Run optimization
        engine = OptimizationEngine(evaluation_func)
        result = engine.optimize(
            search_space,
            target_metric=target_metric,
            strategy=strategy,
            max_evaluations=max_evaluations
        )
        
        # Store results
        self.optimization_results[f"{strategy.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"] = result
        
        # Update parameter registry with best values
        for param_name, value in result.best_parameters.items():
            self.parameter_registry.update_parameter_current_value(param_name, value)
        
        logger.info(f"Calibration completed. Best score: {result.best_score:.4f}")
        logger.info(f"Best parameters: {result.best_parameters}")
        
        return result

    def calibrate_component(
        self,
        component: str,
        test_subset: Optional[str] = None,
        parameters: Optional[List[str]] = None,
        strategy: OptimizationStrategy = OptimizationStrategy.GRID_SEARCH
    ) -> OptimizationResult:
        """
        Run focused calibration on specific component.
        
        Args:
            component: Component name to focus calibration on
            test_subset: Subset of test queries to use (optional)  
            parameters: Specific parameters to optimize (optional)
            strategy: Optimization strategy
            
        Returns:
            OptimizationResult for component-specific optimization
        """
        logger.info(f"Starting component calibration for: {component}")
        
        # Get component parameters
        component_params = self.parameter_registry.get_parameters_for_component(component)
        if parameters:
            # Filter to specified parameters
            param_names = [p.name for p in component_params if p.name in parameters]
        else:
            param_names = [p.name for p in component_params]
            
        if not param_names:
            logger.warning(f"No parameters found for component {component}")
            return None
        
        # Filter test queries if subset specified
        test_queries = self.test_queries
        if test_subset:
            test_queries = [q for q in self.test_queries if q.get("category") == test_subset]
            
        logger.info(f"Using {len(test_queries)} test queries for component calibration")
        
        # Run targeted calibration
        search_space = self.parameter_registry.get_search_space(param_names)
        evaluation_func = self._create_evaluation_function(target_queries=test_queries)
        
        engine = OptimizationEngine(evaluation_func)
        result = engine.optimize(search_space, strategy=strategy)
        
        # Store component-specific result
        self.optimization_results[f"{component}_{strategy.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"] = result
        
        return result

    def _create_evaluation_function(
        self, 
        base_config: Optional[Path] = None,
        target_metric: str = "overall_accuracy",
        target_queries: Optional[List[Dict[str, Any]]] = None
    ) -> Callable[[Dict[str, Any]], float]:
        """Create evaluation function for parameter optimization."""
        
        def evaluate_parameters(parameters: Dict[str, Any]) -> float:
            """Evaluate parameter configuration and return quality score."""
            try:
                # Create temporary config with new parameters
                config_path = self._create_config_with_parameters(parameters, base_config)
                
                # Initialize platform orchestrator with new config
                po = PlatformOrchestrator(str(config_path))
                
                # Use provided queries or default test set
                queries_to_test = target_queries if target_queries else self.test_queries
                
                # Run evaluation on test queries
                total_score = 0.0
                valid_evaluations = 0
                
                for test_case in queries_to_test:
                    try:
                        # Execute query
                        query = test_case["query"]
                        expected = test_case.get("expected_behavior", {})
                        
                        start_time = time.time()
                        result = po.process_query(query)
                        execution_time = time.time() - start_time
                        
                        # Collect metrics
                        metrics = self.metrics_collector.start_query_collection(
                            test_case.get("test_id", f"eval_{valid_evaluations}"), 
                            query
                        )
                        
                        # Extract result data
                        answer = result.answer if hasattr(result, 'answer') else str(result)
                        confidence = result.confidence if hasattr(result, 'confidence') else 0.5
                        citations = result.citations if hasattr(result, 'citations') else []
                        
                        # Collect metrics
                        self.metrics_collector.collect_generation_metrics(
                            metrics, answer, confidence, execution_time, citations
                        )
                        
                        actual_results = {
                            "confidence": confidence,
                            "answer": answer,
                            "citations": citations
                        }
                        
                        self.metrics_collector.collect_validation_results(
                            metrics, expected, actual_results
                        )
                        
                        # Calculate score based on target metric
                        if target_metric == "overall_accuracy":
                            score = self._calculate_overall_accuracy(metrics)
                        elif target_metric == "confidence_ece":
                            score = 1.0 - self._calculate_confidence_ece(metrics)  # Lower ECE is better
                        elif target_metric == "retrieval_f1":
                            score = self._calculate_retrieval_f1(metrics)
                        else:
                            # Default to validation quality
                            score = metrics.validation_results.get("answer_quality_score", 0.0)
                        
                        total_score += score
                        valid_evaluations += 1
                        
                    except Exception as e:
                        logger.error(f"Evaluation failed for query '{test_case.get('query', 'unknown')}': {e}")
                        continue
                
                # Calculate average score
                final_score = total_score / valid_evaluations if valid_evaluations > 0 else 0.0
                
                # Clean up temporary config
                try:
                    config_path.unlink()
                except:
                    pass
                
                return final_score
                
            except Exception as e:
                logger.error(f"Parameter evaluation failed: {e}")
                return 0.0
        
        return evaluate_parameters

    def _create_config_with_parameters(
        self, 
        parameters: Dict[str, Any], 
        base_config: Optional[Path] = None
    ) -> Path:
        """Create temporary configuration file with specified parameters."""
        
        # Load base config
        if base_config and base_config.exists():
            with open(base_config, 'r') as f:
                config = yaml.safe_load(f)
        else:
            # Use default config structure
            config = {
                "document_processor": {"type": "hybrid_pdf", "config": {"chunk_size": 1024}},
                "embedder": {"type": "modular", "config": {}},
                "retriever": {"type": "modular_unified", "config": {}},
                "answer_generator": {"type": "adaptive_modular", "config": {}}
            }
        
        # Apply parameter updates
        for param_name, value in parameters.items():
            param = self.parameter_registry.get_parameter(param_name)
            if param:
                # Update config using parameter path
                self._update_nested_config(config, param.path, value)
            else:
                logger.warning(f"Parameter {param_name} not found in registry")
        
        # Write temporary config file
        temp_file = Path(tempfile.mktemp(suffix='.yaml'))
        with open(temp_file, 'w') as f:
            yaml.dump(config, f, indent=2)
        
        return temp_file

    def _update_nested_config(self, config: Dict[str, Any], path: str, value: Any) -> None:
        """Update nested configuration using dot-separated path."""
        parts = path.split('.')
        current = config
        
        # Navigate to parent
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set final value
        current[parts[-1]] = value

    def _calculate_overall_accuracy(self, metrics: QueryMetrics) -> float:
        """Calculate overall accuracy score."""
        validation = metrics.validation_results
        
        # Weight different validation aspects
        weights = {
            "meets_expectations": 0.4,
            "confidence_in_range": 0.2, 
            "contains_required_terms": 0.2,
            "has_citations": 0.2
        }
        
        score = 0.0
        for aspect, weight in weights.items():
            if validation.get(aspect, False):
                score += weight
                
        return score

    def _calculate_confidence_ece(self, metrics: QueryMetrics) -> float:
        """Calculate Expected Calibration Error for confidence."""
        # Simplified ECE calculation - would need more data for full ECE
        confidence = metrics.generation_metrics.get("confidence_score", 0.5)
        actual_correctness = 1.0 if metrics.validation_results.get("meets_expectations", False) else 0.0
        
        return abs(confidence - actual_correctness)

    def _calculate_retrieval_f1(self, metrics: QueryMetrics) -> float:
        """Calculate retrieval F1 score."""
        # Simplified F1 based on retrieval metrics
        docs_retrieved = metrics.retrieval_metrics.get("documents_retrieved", 0)
        avg_score = metrics.retrieval_metrics.get("avg_semantic_score", 0.0)
        
        # Simple heuristic: good retrieval has both sufficient docs and high scores
        precision = avg_score
        recall = min(1.0, docs_retrieved / 5.0)  # Assume 5 docs is good recall
        
        if precision + recall == 0:
            return 0.0
            
        return 2 * (precision * recall) / (precision + recall)

    def generate_report(self, output_path: Path) -> None:
        """Generate comprehensive calibration report."""
        try:
            # Aggregate all results
            report_data = {
                "calibration_summary": {
                    "timestamp": datetime.now().isoformat(),
                    "total_optimizations": len(self.optimization_results),
                    "parameters_optimized": len(self.parameter_registry.parameters),
                    "test_queries_used": len(self.test_queries)
                },
                "parameter_registry": {
                    "parameters": {
                        name: {
                            "current": param.current,
                            "component": param.component,
                            "description": param.description,
                            "impacts": param.impacts
                        }
                        for name, param in self.parameter_registry.parameters.items()
                    }
                },
                "optimization_results": {
                    name: {
                        "best_score": result.best_score,
                        "best_parameters": result.best_parameters,
                        "total_evaluations": result.total_evaluations,
                        "optimization_time": result.optimization_time
                    }
                    for name, result in self.optimization_results.items()
                },
                "metrics_summary": self.metrics_collector.calculate_aggregate_metrics(),
                "recommendations": self._generate_recommendations()
            }
            
            # Write HTML report
            html_content = self._generate_html_report(report_data)
            with open(output_path, 'w') as f:
                f.write(html_content)
                
            logger.info(f"Generated calibration report: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on calibration results."""
        recommendations = []
        
        if not self.optimization_results:
            recommendations.append("No optimization results available. Run calibration first.")
            return recommendations
            
        # Find best performing configuration
        best_result = max(self.optimization_results.values(), key=lambda x: x.best_score)
        
        recommendations.extend([
            f"Best configuration achieved {best_result.best_score:.3f} score",
            f"Consider deploying parameters: {best_result.best_parameters}",
            f"Total optimization time: {best_result.optimization_time:.1f}s"
        ])
        
        # Parameter-specific recommendations
        best_params = best_result.best_parameters
        
        if "bm25_b" in best_params:
            b_value = best_params["bm25_b"]
            if b_value < 0.3:
                recommendations.append(f"BM25 b={b_value} suggests documents have varying lengths - good choice")
            elif b_value > 0.7:
                recommendations.append(f"BM25 b={b_value} may over-penalize longer documents")
        
        if "rrf_k" in best_params:
            k_value = best_params["rrf_k"]
            if k_value < 20:
                recommendations.append(f"RRF k={k_value} provides high score discrimination")
            elif k_value > 80:
                recommendations.append(f"RRF k={k_value} may compress scores too much")
        
        return recommendations

    def _generate_html_report(self, data: Dict[str, Any]) -> str:
        """Generate HTML calibration report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>RAG System Calibration Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 30px 0; }}
                .metric {{ background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 3px; }}
                .param-table {{ border-collapse: collapse; width: 100%; }}
                .param-table th, .param-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .param-table th {{ background-color: #f2f2f2; }}
                .recommendation {{ background-color: #e8f4fd; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>RAG System Calibration Report</h1>
                <p>Generated: {data['calibration_summary']['timestamp']}</p>
                <p>Total Optimizations: {data['calibration_summary']['total_optimizations']}</p>
                <p>Parameters Optimized: {data['calibration_summary']['parameters_optimized']}</p>
            </div>
            
            <div class="section">
                <h2>Optimization Results</h2>
        """
        
        for name, result in data['optimization_results'].items():
            html += f"""
                <div class="metric">
                    <h3>{name}</h3>
                    <p><strong>Best Score:</strong> {result['best_score']:.4f}</p>
                    <p><strong>Evaluations:</strong> {result['total_evaluations']}</p>
                    <p><strong>Time:</strong> {result['optimization_time']:.2f}s</p>
                    <p><strong>Best Parameters:</strong></p>
                    <ul>
            """
            
            for param, value in result['best_parameters'].items():
                html += f"<li>{param}: {value}</li>"
            
            html += "</ul></div>"
        
        html += """
            </div>
            
            <div class="section">
                <h2>Current Parameter Configuration</h2>
                <table class="param-table">
                    <tr>
                        <th>Parameter</th>
                        <th>Current Value</th>
                        <th>Component</th>
                        <th>Description</th>
                    </tr>
        """
        
        for name, param in data['parameter_registry']['parameters'].items():
            html += f"""
                    <tr>
                        <td>{name}</td>
                        <td>{param['current']}</td>
                        <td>{param['component']}</td>
                        <td>{param.get('description', 'N/A')}</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
        """
        
        for rec in data['recommendations']:
            html += f'<div class="recommendation">{rec}</div>'
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html

    def save_optimal_configuration(self, output_path: Path, optimization_name: Optional[str] = None) -> None:
        """Save optimal configuration based on calibration results."""
        if not self.optimization_results:
            logger.error("No optimization results available")
            return
            
        # Get best result
        if optimization_name and optimization_name in self.optimization_results:
            result = self.optimization_results[optimization_name]
        else:
            result = max(self.optimization_results.values(), key=lambda x: x.best_score)
        
        # Generate optimal config
        optimal_config = self._create_config_with_parameters(result.best_parameters)
        
        # Copy to output path with metadata
        with open(optimal_config, 'r') as f:
            config_content = f.read()
        
        header = f"""# Optimal RAG Configuration
# Generated by Calibration System
# Timestamp: {datetime.now().isoformat()}
# Best Score: {result.best_score:.4f}
# Total Evaluations: {result.total_evaluations}
# Optimization Time: {result.optimization_time:.2f}s

"""
        
        with open(output_path, 'w') as f:
            f.write(header + config_content)
        
        # Clean up temp file
        optimal_config.unlink()
        
        logger.info(f"Saved optimal configuration to {output_path}")


if __name__ == "__main__":
    # Test calibration manager
    manager = CalibrationManager()
    
    print("Calibration Manager Test")
    print("=" * 40)
    
    # Show parameter registry
    print(manager.parameter_registry.get_parameter_summary())
    
    # Test basic functionality
    print(f"\nTest queries loaded: {len(manager.test_queries)}")
    
    if manager.test_queries:
        print("Sample query:", manager.test_queries[0]["query"])