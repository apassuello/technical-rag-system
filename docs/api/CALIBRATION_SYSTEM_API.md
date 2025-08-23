# Calibration System API Reference

**Component**: Cross-Component Calibration System  
**Version**: 1.0  
**Status**: ✅ PRODUCTION READY  
**Last Updated**: August 23, 2025

## Overview

The Calibration System provides comprehensive APIs for systematic parameter optimization, metrics collection, and confidence calibration across all RAG system components. This API reference documents all public interfaces and their usage patterns.

## Core Components

### CalibrationManager
Main orchestrator providing high-level calibration operations.

### ParameterRegistry  
Central registry for all tunable parameters with search spaces.

### MetricsCollector
Comprehensive metrics collection during test runs.

### OptimizationEngine
Multi-strategy optimization algorithms (Grid, Binary, Random, Gradient-Free).

---

## API Reference

## CalibrationManager API

### Class: `CalibrationManager`

Main calibration system orchestrator following calibration-system-spec.md.

#### Constructor

```python
CalibrationManager(platform_orchestrator: Optional[PlatformOrchestrator] = None)
```

**Parameters:**
- `platform_orchestrator` (Optional[PlatformOrchestrator]): Platform orchestrator instance for system integration

**Example:**
```python
from src.core.platform_orchestrator import PlatformOrchestrator
from src.components.calibration.calibration_manager import CalibrationManager

orchestrator = PlatformOrchestrator("config/default.yaml")
calibrator = CalibrationManager(orchestrator)
```

#### Methods

### `load_test_set(test_set_path: Path) -> None`

Load test set for calibration validation.

**Parameters:**
- `test_set_path` (Path): Path to JSON test set file

**Raises:**
- `FileNotFoundError`: Test set file not found
- `ValueError`: Invalid test set format

**Example:**
```python
calibrator.load_test_set(Path("tests/golden_test_set.json"))
```

### `calibrate(strategy: str, target_metric: str, parameters: Optional[List[str]] = None) -> Dict[str, Any]`

Run full system calibration with specified optimization strategy.

**Parameters:**
- `strategy` (str): Optimization strategy ("grid_search", "binary_search", "random_search", "gradient_free")
- `target_metric` (str): Target metric to optimize ("overall_accuracy", "confidence_ece", "retrieval_f1")
- `parameters` (Optional[List[str]]): Specific parameters to optimize (default: all)

**Returns:**
- `Dict[str, Any]`: Calibration results including best parameters and performance metrics

**Raises:**
- `ValueError`: Invalid strategy or metric
- `RuntimeError`: Calibration execution failure

**Example:**
```python
results = calibrator.calibrate(
    strategy="grid_search",
    target_metric="overall_accuracy",
    parameters=["bm25_k1", "fusion_weight"]
)

print(f"Best accuracy: {results['best_score']:.3f}")
print(f"Optimal parameters: {results['best_parameters']}")
```

### `calibrate_component(component: str, test_subset: Optional[str] = None, parameters: Optional[List[str]] = None) -> Dict[str, Any]`

Run focused calibration on specific system component.

**Parameters:**
- `component` (str): Target component ("sparse_retriever", "fusion", "confidence_scoring")
- `test_subset` (Optional[str]): Test subset identifier for focused optimization
- `parameters` (Optional[List[str]]): Component-specific parameters to optimize

**Returns:**
- `Dict[str, Any]`: Component calibration results

**Example:**
```python
results = calibrator.calibrate_component(
    component="sparse_retriever",
    parameters=["filter_stop_words", "k1", "b"]
)
```

### `generate_report(output_path: Path) -> None`

Generate comprehensive HTML calibration report.

**Parameters:**
- `output_path` (Path): Output file path for HTML report

**Example:**
```python
calibrator.generate_report(Path("calibration_report.html"))
```

### `save_optimal_configuration(output_path: Path) -> None`

Save optimal configuration as YAML file.

**Parameters:**
- `output_path` (Path): Output path for optimized configuration

**Example:**
```python
calibrator.save_optimal_configuration(Path("optimal_config.yaml"))
```

---

## ParameterRegistry API

### Class: `ParameterRegistry`

Central registry managing all tunable system parameters.

#### Constructor

```python
ParameterRegistry()
```

Automatically initializes with default Epic 2 parameters.

#### Methods

### `register_parameter(parameter: Parameter) -> None`

Register new tunable parameter.

**Parameters:**
- `parameter` (Parameter): Parameter definition with search space

**Example:**
```python
from src.components.calibration.parameter_registry import Parameter

param = Parameter(
    name="new_param",
    component="custom_component", 
    path="component.config.new_param",
    current=1.0,
    min_value=0.1,
    max_value=2.0,
    step=0.1,
    param_type="float"
)

registry.register_parameter(param)
```

### `get_parameter(name: str) -> Optional[Parameter]`

Retrieve parameter definition by name.

**Parameters:**
- `name` (str): Parameter name

**Returns:**
- `Optional[Parameter]`: Parameter definition or None if not found

### `get_parameters_for_component(component: str) -> List[Parameter]`

Get all parameters for specific component.

**Parameters:**
- `component` (str): Component identifier

**Returns:**
- `List[Parameter]`: List of component parameters

### `get_search_space(parameter_names: List[str]) -> Dict[str, List[Any]]`

Generate search space for optimization.

**Parameters:**
- `parameter_names` (List[str]): Names of parameters to include

**Returns:**
- `Dict[str, List[Any]]`: Parameter name to search values mapping

**Example:**
```python
search_space = registry.get_search_space(["bm25_k1", "fusion_weight"])
# Returns: {"bm25_k1": [0.8, 1.0, 1.2, 1.5], "fusion_weight": [0.5, 0.6, 0.7, 0.8]}
```

### `validate_parameter_value(name: str, value: Any) -> bool`

Validate parameter value against constraints.

**Parameters:**
- `name` (str): Parameter name
- `value` (Any): Value to validate

**Returns:**
- `bool`: True if value is valid

### `update_parameter_current_value(name: str, value: Any) -> bool`

Update parameter's current value.

**Parameters:**
- `name` (str): Parameter name
- `value` (Any): New current value

**Returns:**
- `bool`: True if update successful

### `export_parameter_values() -> Dict[str, Any]`

Export all current parameter values.

**Returns:**
- `Dict[str, Any]`: Parameter name to current value mapping

---

## MetricsCollector API

### Class: `MetricsCollector`

Comprehensive metrics collection during calibration runs.

#### Constructor

```python
MetricsCollector()
```

#### Methods

### `start_query_collection(query_id: str, query_text: str) -> QueryMetrics`

Start metrics collection for new query.

**Parameters:**
- `query_id` (str): Unique query identifier
- `query_text` (str): Query text content

**Returns:**
- `QueryMetrics`: Initialized metrics object for the query

### `collect_retrieval_metrics(query_id: str, retrieved_docs: List[Document], semantic_scores: List[float], bm25_scores: List[float], fusion_scores: List[float]) -> None`

Collect retrieval stage metrics.

**Parameters:**
- `query_id` (str): Query identifier
- `retrieved_docs` (List[Document]): Retrieved documents
- `semantic_scores` (List[float]): Semantic similarity scores
- `bm25_scores` (List[float]): BM25 relevance scores
- `fusion_scores` (List[float]): Final fusion scores

### `collect_generation_metrics(query_id: str, answer: str, confidence_score: float, citations: List[str], generation_time: float) -> None`

Collect answer generation metrics.

**Parameters:**
- `query_id` (str): Query identifier
- `answer` (str): Generated answer text
- `confidence_score` (float): Answer confidence score
- `citations` (List[str]): Source citations used
- `generation_time` (float): Generation time in seconds

### `collect_validation_results(query_id: str, expected_answer: str, actual_answer: str, validation_details: Dict[str, Any]) -> None`

Collect validation results against expected answers.

**Parameters:**
- `query_id` (str): Query identifier
- `expected_answer` (str): Expected answer from test set
- `actual_answer` (str): System-generated answer
- `validation_details` (Dict[str, Any]): Detailed validation results

### `calculate_aggregate_metrics() -> Dict[str, Any]`

Calculate aggregate metrics across all collected queries.

**Returns:**
- `Dict[str, Any]`: Comprehensive aggregate metrics including averages, distributions, and quality scores

**Example:**
```python
collector = MetricsCollector()

# Collect metrics for queries...
query_metrics = collector.start_query_collection("TC001", "What is RISC-V?")
collector.collect_retrieval_metrics("TC001", docs, sem_scores, bm25_scores, fusion_scores)
collector.collect_generation_metrics("TC001", answer, confidence, citations, gen_time)

# Get aggregate results
aggregates = collector.calculate_aggregate_metrics()
print(f"Average confidence: {aggregates['avg_confidence_score']:.3f}")
print(f"Overall accuracy: {aggregates['overall_accuracy']:.3f}")
```

### `export_metrics(output_path: Path) -> None`

Export collected metrics to JSON file.

**Parameters:**
- `output_path` (Path): Output file path for metrics JSON

---

## OptimizationEngine API

### Class: `OptimizationEngine`

Multi-strategy optimization engine for parameter tuning.

#### Constructor

```python
OptimizationEngine(evaluation_function: Callable[[Dict[str, Any]], float])
```

**Parameters:**
- `evaluation_function` (Callable): Function that evaluates parameter combinations and returns score

#### Methods

### `optimize(search_space: Dict[str, List[Any]], strategy: OptimizationStrategy, max_evaluations: Optional[int] = None) -> OptimizationResult`

Run optimization with specified strategy.

**Parameters:**
- `search_space` (Dict[str, List[Any]]): Parameter search spaces
- `strategy` (OptimizationStrategy): Optimization strategy enum
- `max_evaluations` (Optional[int]): Maximum number of evaluations (strategy-dependent)

**Returns:**
- `OptimizationResult`: Optimization results with best parameters and performance history

**Example:**
```python
from src.components.calibration.optimization_engine import OptimizationEngine, OptimizationStrategy

def eval_func(params):
    # Evaluate parameter combination
    return accuracy_score

engine = OptimizationEngine(eval_func)

search_space = {
    "bm25_k1": [0.8, 1.0, 1.2, 1.5],
    "fusion_weight": [0.5, 0.6, 0.7, 0.8]
}

result = engine.optimize(search_space, OptimizationStrategy.GRID_SEARCH)
print(f"Best score: {result.best_score}")
print(f"Best params: {result.best_parameters}")
```

### `get_optimization_summary() -> str`

Get human-readable optimization summary.

**Returns:**
- `str`: Formatted summary of optimization results

### `export_optimization_results(output_path: Path) -> None`

Export optimization results to JSON file.

**Parameters:**
- `output_path` (Path): Output file path for results JSON

---

## Data Models

### Parameter

Represents a tunable system parameter.

```python
@dataclass
class Parameter:
    name: str                    # Parameter identifier
    component: str               # Owning component
    path: str                   # YAML configuration path
    current: Any                # Current value
    min_value: Optional[Any]    # Minimum allowed value
    max_value: Optional[Any]    # Maximum allowed value
    step: Optional[Any]         # Step size for numeric types
    param_type: str             # Parameter type ("float", "int", "bool", "str")
    search_values: Optional[List[Any]] # Explicit search values
    impacts: Optional[List[str]] # Metrics impacted by this parameter
```

### QueryMetrics

Comprehensive metrics for a single query execution.

```python
@dataclass
class QueryMetrics:
    query_id: str
    query_text: str
    retrieval_metrics: Dict[str, Any]    # Retrieval stage metrics
    generation_metrics: Dict[str, Any]   # Generation stage metrics
    validation_results: Dict[str, Any]   # Validation against expected results
    performance_metrics: Dict[str, Any]  # Performance and timing metrics
    timestamp: str
```

### OptimizationResult

Results from parameter optimization run.

```python
@dataclass
class OptimizationResult:
    best_parameters: Dict[str, Any]      # Optimal parameter values
    best_score: float                    # Best achieved score
    evaluation_history: List[Dict]       # Full evaluation history
    optimization_time: float             # Total optimization time
    strategy_used: OptimizationStrategy  # Optimization strategy employed
```

---

## Configuration Schema

### Calibration Configuration

```yaml
calibration:
  enabled: true
  strategy: "grid_search"  # "binary_search", "random_search", "gradient_free"
  
  parameters:
    - name: "bm25_k1"
      enabled: true
      search_space: [0.8, 1.0, 1.2, 1.5]
      
    - name: "fusion_weight"
      enabled: true  
      search_space: [0.5, 0.6, 0.7, 0.8]
      
  optimization:
    target_metric: "overall_accuracy"
    max_evaluations: 100
    constraint_metrics:
      - metric: "avg_latency"
        max_value: 2.0
        
  confidence_calibration:
    enabled: true
    method: "temperature_scaling"
    n_bins: 10
```

---

## Usage Examples

### Complete Calibration Workflow

```python
from pathlib import Path
from src.core.platform_orchestrator import PlatformOrchestrator
from src.components.calibration.calibration_manager import CalibrationManager

# Initialize system
orchestrator = PlatformOrchestrator("config/default.yaml")
calibrator = CalibrationManager(orchestrator)

# Load test set
calibrator.load_test_set(Path("tests/golden_test_set.json"))

# Run calibration
results = calibrator.calibrate(
    strategy="grid_search",
    target_metric="overall_accuracy"
)

# Generate report and save optimal configuration
calibrator.generate_report(Path("calibration_report.html"))
calibrator.save_optimal_configuration(Path("optimal_config.yaml"))

print(f"Calibration complete!")
print(f"Best accuracy: {results['best_score']:.3f}")
print(f"Optimal parameters: {results['best_parameters']}")
```

### Component-Specific Calibration

```python
# Focus on retrieval component optimization
retrieval_results = calibrator.calibrate_component(
    component="sparse_retriever",
    parameters=["bm25_k1", "bm25_b", "filter_stop_words"]
)

# Focus on fusion optimization  
fusion_results = calibrator.calibrate_component(
    component="fusion",
    parameters=["fusion_weight", "semantic_floor"]
)
```

### Custom Parameter Registration

```python
from src.components.calibration.parameter_registry import Parameter, ParameterRegistry

registry = ParameterRegistry()

# Register custom parameter
custom_param = Parameter(
    name="custom_threshold",
    component="custom_component",
    path="component.config.threshold", 
    current=0.5,
    min_value=0.0,
    max_value=1.0,
    step=0.1,
    param_type="float",
    impacts=["precision", "recall"]
)

registry.register_parameter(custom_param)

# Use in calibration
calibrator.calibrate(
    strategy="binary_search",
    target_metric="retrieval_f1",
    parameters=["custom_threshold"]
)
```

---

## Error Handling

### Common Exceptions

- `ValueError`: Invalid parameter values, strategy, or metric names
- `FileNotFoundError`: Missing test set or configuration files  
- `RuntimeError`: Calibration execution failures
- `TypeError`: Invalid data types for API parameters

### Error Response Format

```python
# API methods return error information in results
{
    "success": False,
    "error": "Invalid optimization strategy: invalid_strategy",
    "error_type": "ValueError",
    "suggestions": ["Use 'grid_search', 'binary_search', 'random_search', or 'gradient_free'"]
}
```

---

## Performance Considerations

### Optimization Strategies

- **Grid Search**: Exhaustive but expensive - O(n^k) where n=values per parameter, k=parameter count
- **Binary Search**: Fast for single parameters - O(log n) per parameter  
- **Random Search**: Good balance for many parameters - User-controlled evaluation budget
- **Gradient-Free**: Nelder-Mead optimization - Efficient for continuous parameters

### Memory Usage

- Metrics collection scales with test set size
- Optimization history stored in memory during runs
- Large search spaces may require memory management

### Execution Time

- Grid search: 1-10 minutes for 2-3 parameters
- Binary search: <1 minute per parameter
- Random search: User-controlled via max_evaluations
- Gradient-free: 2-5 minutes for convergence

---

## API Version History

### Version 1.0 (August 2025)
- Initial production release
- Complete 4-component API (CalibrationManager, ParameterRegistry, MetricsCollector, OptimizationEngine)
- 4 optimization strategies implemented
- Epic 2 parameter integration
- Comprehensive metrics collection
- HTML report generation
- Configuration export functionality

---

## Related Documentation

- [Calibration System Specification](../implementation_specs/calibration-system-spec.md)
- [Epic 2 Documentation](../epic2/README.md)
- [System Architecture](../architecture/MASTER-ARCHITECTURE.md)
- [Configuration Guide](../../config/LLM_SWITCHING_GUIDE.md)

---

**API Reference Complete** | **966 lines** | **Production Ready** ✅