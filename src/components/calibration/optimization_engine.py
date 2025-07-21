"""
Optimization engine for the calibration system.

Implements the optimization engine component from calibration-system-spec.md
for finding optimal parameter values using various search strategies.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Callable, Iterator
from dataclasses import dataclass
from enum import Enum
import numpy as np
from itertools import product
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Available optimization strategies."""
    GRID_SEARCH = "grid_search"
    BINARY_SEARCH = "binary_search"
    RANDOM_SEARCH = "random_search"
    GRADIENT_FREE = "gradient_free"


@dataclass
class OptimizationResult:
    """Result of parameter optimization."""
    best_parameters: Dict[str, Any]
    best_score: float
    optimization_history: List[Dict[str, Any]]
    total_evaluations: int
    optimization_time: float
    convergence_info: Dict[str, Any]


class OptimizationEngine:
    """
    Finds optimal parameter values using various search strategies.
    
    Implements the optimization strategies specified in calibration-system-spec.md:
    - Grid search for exhaustive parameter exploration
    - Binary search for single parameter optimization  
    - Random search for high-dimensional spaces
    - Gradient-free optimization for complex parameter interactions
    """

    def __init__(self, evaluation_function: Callable[[Dict[str, Any]], float]):
        """
        Initialize optimization engine.
        
        Args:
            evaluation_function: Function that takes parameters and returns quality score
        """
        self.evaluation_function = evaluation_function
        self.optimization_history: List[Dict[str, Any]] = []
        self.best_result: Optional[OptimizationResult] = None

    def optimize(
        self,
        parameter_space: Dict[str, List[Any]],
        target_metric: str = "overall_quality",
        strategy: OptimizationStrategy = OptimizationStrategy.GRID_SEARCH,
        max_evaluations: Optional[int] = None,
        convergence_threshold: float = 0.001,
        **strategy_kwargs
    ) -> OptimizationResult:
        """
        Optimize parameters using specified strategy.
        
        Args:
            parameter_space: Dictionary mapping parameter names to lists of values
            target_metric: Metric to optimize (maximize)
            strategy: Optimization strategy to use
            max_evaluations: Maximum number of evaluations
            convergence_threshold: Convergence threshold for iterative methods
            **strategy_kwargs: Additional arguments for specific strategies
            
        Returns:
            OptimizationResult with best parameters and optimization details
        """
        start_time = time.time()
        self.optimization_history = []

        logger.info(f"Starting optimization with {strategy.value} strategy")
        logger.info(f"Parameter space: {len(list(product(*parameter_space.values())))} combinations")

        if strategy == OptimizationStrategy.GRID_SEARCH:
            result = self._grid_search(parameter_space, target_metric, max_evaluations)
        elif strategy == OptimizationStrategy.BINARY_SEARCH:
            result = self._binary_search(parameter_space, target_metric, **strategy_kwargs)
        elif strategy == OptimizationStrategy.RANDOM_SEARCH:
            result = self._random_search(parameter_space, target_metric, max_evaluations, **strategy_kwargs)
        elif strategy == OptimizationStrategy.GRADIENT_FREE:
            result = self._gradient_free_search(parameter_space, target_metric, max_evaluations, convergence_threshold, **strategy_kwargs)
        else:
            raise ValueError(f"Unknown optimization strategy: {strategy}")

        optimization_time = time.time() - start_time
        
        # Create final result
        optimization_result = OptimizationResult(
            best_parameters=result["best_parameters"],
            best_score=result["best_score"],
            optimization_history=self.optimization_history,
            total_evaluations=len(self.optimization_history),
            optimization_time=optimization_time,
            convergence_info=result.get("convergence_info", {})
        )

        self.best_result = optimization_result
        logger.info(f"Optimization completed in {optimization_time:.2f}s with {len(self.optimization_history)} evaluations")
        logger.info(f"Best score: {result['best_score']:.4f}")

        return optimization_result

    def _grid_search(
        self, 
        parameter_space: Dict[str, List[Any]], 
        target_metric: str,
        max_evaluations: Optional[int] = None
    ) -> Dict[str, Any]:
        """Exhaustive grid search over parameter space."""
        param_names = list(parameter_space.keys())
        param_values = list(parameter_space.values())
        
        best_score = float('-inf')
        best_params = {}
        evaluations = 0
        
        # Generate all parameter combinations
        for param_combination in product(*param_values):
            if max_evaluations and evaluations >= max_evaluations:
                logger.info(f"Reached maximum evaluations limit: {max_evaluations}")
                break
                
            # Create parameter dictionary
            current_params = dict(zip(param_names, param_combination))
            
            # Evaluate
            try:
                score = self.evaluation_function(current_params)
                evaluations += 1
                
                # Track history
                self.optimization_history.append({
                    "evaluation": evaluations,
                    "parameters": current_params.copy(),
                    "score": score,
                    "is_best": score > best_score
                })
                
                # Update best
                if score > best_score:
                    best_score = score
                    best_params = current_params.copy()
                    logger.info(f"New best score: {score:.4f} with params: {current_params}")
                
            except Exception as e:
                logger.error(f"Evaluation failed for params {current_params}: {e}")
                continue
                
        return {
            "best_parameters": best_params,
            "best_score": best_score,
            "convergence_info": {"strategy": "grid_search", "total_combinations": evaluations}
        }

    def _binary_search(
        self, 
        parameter_space: Dict[str, List[Any]], 
        target_metric: str, 
        parameter_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Binary search for single parameter optimization."""
        if len(parameter_space) != 1 and parameter_name is None:
            raise ValueError("Binary search requires exactly one parameter or parameter_name to be specified")
        
        if parameter_name:
            if parameter_name not in parameter_space:
                raise ValueError(f"Parameter {parameter_name} not found in parameter space")
            search_param = parameter_name
            other_params = {k: v[0] for k, v in parameter_space.items() if k != parameter_name}
        else:
            search_param = list(parameter_space.keys())[0]
            other_params = {}
        
        search_values = parameter_space[search_param]
        if len(search_values) < 3:
            logger.warning("Binary search requires at least 3 values, falling back to grid search")
            return self._grid_search(parameter_space, target_metric)
        
        # Sort values for binary search
        sorted_values = sorted(search_values)
        left, right = 0, len(sorted_values) - 1
        
        best_score = float('-inf')
        best_params = {}
        evaluations = 0
        
        while left <= right:
            mid = (left + right) // 2
            current_value = sorted_values[mid]
            
            # Create parameter set
            current_params = other_params.copy()
            current_params[search_param] = current_value
            
            # Evaluate
            try:
                score = self.evaluation_function(current_params)
                evaluations += 1
                
                self.optimization_history.append({
                    "evaluation": evaluations,
                    "parameters": current_params.copy(),
                    "score": score,
                    "search_bounds": [sorted_values[left], sorted_values[right]],
                    "is_best": score > best_score
                })
                
                if score > best_score:
                    best_score = score
                    best_params = current_params.copy()
                    logger.info(f"Binary search: new best {score:.4f} at {search_param}={current_value}")
                
                # Decide search direction based on neighboring evaluations
                if mid > 0:
                    left_params = other_params.copy()
                    left_params[search_param] = sorted_values[mid-1]
                    left_score = self.evaluation_function(left_params)
                    evaluations += 1
                else:
                    left_score = float('-inf')
                
                if mid < len(sorted_values) - 1:
                    right_params = other_params.copy() 
                    right_params[search_param] = sorted_values[mid+1]
                    right_score = self.evaluation_function(right_params)
                    evaluations += 1
                else:
                    right_score = float('-inf')
                
                # Move towards better direction
                if left_score > right_score:
                    right = mid - 1
                else:
                    left = mid + 1
                
            except Exception as e:
                logger.error(f"Binary search evaluation failed: {e}")
                break
        
        return {
            "best_parameters": best_params,
            "best_score": best_score,
            "convergence_info": {"strategy": "binary_search", "evaluations": evaluations}
        }

    def _random_search(
        self, 
        parameter_space: Dict[str, List[Any]], 
        target_metric: str,
        max_evaluations: int = 100,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Random search over parameter space."""
        if seed is not None:
            np.random.seed(seed)
        
        param_names = list(parameter_space.keys())
        param_values = list(parameter_space.values())
        
        best_score = float('-inf')
        best_params = {}
        
        for evaluation in range(max_evaluations):
            # Randomly select parameter combination
            current_params = {}
            for name, values in zip(param_names, param_values):
                current_params[name] = np.random.choice(values)
            
            try:
                score = self.evaluation_function(current_params)
                
                self.optimization_history.append({
                    "evaluation": evaluation + 1,
                    "parameters": current_params.copy(),
                    "score": score,
                    "is_best": score > best_score
                })
                
                if score > best_score:
                    best_score = score
                    best_params = current_params.copy()
                    logger.info(f"Random search: new best {score:.4f} at evaluation {evaluation + 1}")
                
            except Exception as e:
                logger.error(f"Random search evaluation failed: {e}")
                continue
        
        return {
            "best_parameters": best_params,
            "best_score": best_score,
            "convergence_info": {"strategy": "random_search", "evaluations": max_evaluations}
        }

    def _gradient_free_search(
        self, 
        parameter_space: Dict[str, List[Any]], 
        target_metric: str,
        max_evaluations: int = 200,
        convergence_threshold: float = 0.001,
        population_size: int = 10
    ) -> Dict[str, Any]:
        """Gradient-free optimization using simple evolutionary approach."""
        param_names = list(parameter_space.keys())
        param_values = list(parameter_space.values())
        
        # Initialize population
        population = []
        for _ in range(population_size):
            individual = {}
            for name, values in zip(param_names, param_values):
                individual[name] = np.random.choice(values)
            population.append(individual)
        
        best_score = float('-inf')
        best_params = {}
        generations_without_improvement = 0
        generation = 0
        
        while len(self.optimization_history) < max_evaluations:
            generation += 1
            
            # Evaluate population
            generation_scores = []
            for individual in population:
                try:
                    score = self.evaluation_function(individual)
                    generation_scores.append((individual, score))
                    
                    self.optimization_history.append({
                        "evaluation": len(self.optimization_history) + 1,
                        "generation": generation,
                        "parameters": individual.copy(),
                        "score": score,
                        "is_best": score > best_score
                    })
                    
                    if score > best_score:
                        improvement = score - best_score
                        best_score = score
                        best_params = individual.copy()
                        generations_without_improvement = 0
                        logger.info(f"Gradient-free: gen {generation}, new best {score:.4f}, improvement {improvement:.4f}")
                    
                    if len(self.optimization_history) >= max_evaluations:
                        break
                        
                except Exception as e:
                    logger.error(f"Gradient-free evaluation failed: {e}")
                    continue
            
            if not generation_scores:
                break
                
            # Selection: keep top 50%
            generation_scores.sort(key=lambda x: x[1], reverse=True)
            survivors = [ind for ind, _ in generation_scores[:population_size//2]]
            
            # Reproduction: create offspring with mutations
            new_population = survivors.copy()
            while len(new_population) < population_size:
                parent = np.random.choice(survivors)
                child = parent.copy()
                
                # Mutate random parameter
                param_to_mutate = np.random.choice(param_names)
                child[param_to_mutate] = np.random.choice(parameter_space[param_to_mutate])
                
                new_population.append(child)
            
            population = new_population
            generations_without_improvement += 1
            
            # Check convergence
            if generations_without_improvement > 10:  # Early stopping
                logger.info(f"Gradient-free search converged after {generation} generations")
                break
        
        return {
            "best_parameters": best_params,
            "best_score": best_score,
            "convergence_info": {
                "strategy": "gradient_free", 
                "generations": generation,
                "final_population_size": len(population),
                "converged": generations_without_improvement > 10
            }
        }

    def get_optimization_summary(self) -> str:
        """Get human-readable summary of optimization results."""
        if not self.best_result:
            return "No optimization completed yet."
        
        result = self.best_result
        
        summary = [
            f"Optimization Results Summary",
            f"=" * 40,
            f"Best Score: {result.best_score:.4f}",
            f"Total Evaluations: {result.total_evaluations}",
            f"Optimization Time: {result.optimization_time:.2f}s",
            f"Evaluations/Second: {result.total_evaluations/result.optimization_time:.2f}",
            f"",
            f"Best Parameters:"
        ]
        
        for param, value in result.best_parameters.items():
            summary.append(f"  {param}: {value}")
        
        if result.convergence_info:
            summary.extend([
                f"",
                f"Convergence Info:",
                f"  Strategy: {result.convergence_info.get('strategy', 'unknown')}"
            ])
            
            for key, value in result.convergence_info.items():
                if key != 'strategy':
                    summary.append(f"  {key}: {value}")
        
        return "\n".join(summary)

    def export_optimization_results(self, output_path: Path) -> None:
        """Export optimization results to JSON."""
        if not self.best_result:
            logger.error("No optimization results to export")
            return
        
        try:
            export_data = {
                "best_parameters": self.best_result.best_parameters,
                "best_score": self.best_result.best_score,
                "total_evaluations": self.best_result.total_evaluations,
                "optimization_time": self.best_result.optimization_time,
                "convergence_info": self.best_result.convergence_info,
                "optimization_history": self.best_result.optimization_history
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Exported optimization results to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export optimization results: {e}")


if __name__ == "__main__":
    # Test optimization engine with mock evaluation function
    def mock_evaluation(params):
        """Mock evaluation function for testing."""
        # Simulate optimization of quadratic function
        x = params.get("param_x", 0)
        y = params.get("param_y", 0)
        
        # Optimal at x=5, y=3
        score = 100 - (x - 5)**2 - (y - 3)**2
        return max(0, score)  # Ensure non-negative
    
    # Test parameter space
    param_space = {
        "param_x": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "param_y": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    }
    
    engine = OptimizationEngine(mock_evaluation)
    
    # Test grid search
    result = engine.optimize(
        param_space,
        strategy=OptimizationStrategy.GRID_SEARCH,
        max_evaluations=50
    )
    
    print(engine.get_optimization_summary())