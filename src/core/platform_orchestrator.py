"""
Platform Orchestrator - System lifecycle and platform integration.

This component manages the system lifecycle, component initialization,
and platform-specific adaptations with factory-based architecture.
It uses ComponentFactory for direct component instantiation with optimal performance.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from .interfaces import (
    Document, Answer, RetrievalResult, 
    ComponentHealthService, SystemAnalyticsService, ABTestingService, 
    ConfigurationService, BackendManagementService,
    HealthStatus, ComponentMetrics, ExperimentAssignment, ExperimentResult, BackendStatus
)
from .config import ConfigManager, PipelineConfig
from .component_factory import ComponentFactory

logger = logging.getLogger(__name__)


class ComponentHealthServiceImpl(ComponentHealthService):
    """Implementation of ComponentHealthService for universal health monitoring."""
    
    def __init__(self):
        """Initialize the health service."""
        self.monitored_components: Dict[str, Any] = {}
        self.health_history: Dict[str, List[HealthStatus]] = {}
        self.failure_counts: Dict[str, int] = {}
        self.last_health_checks: Dict[str, float] = {}
        self.health_check_interval = 30.0  # seconds
        
    def check_component_health(self, component: Any) -> HealthStatus:
        """Check the health of a component.
        
        Args:
            component: Component instance to check
            
        Returns:
            HealthStatus object with health information
        """
        component_name = type(component).__name__
        current_time = time.time()
        
        # Rate limit health checks
        if (component_name in self.last_health_checks and 
            current_time - self.last_health_checks[component_name] < self.health_check_interval):
            # Return cached health status
            if component_name in self.health_history and self.health_history[component_name]:
                return self.health_history[component_name][-1]
        
        health_status = HealthStatus(
            is_healthy=True,
            last_check=current_time,
            issues=[],
            metrics={},
            component_name=component_name
        )
        
        try:
            # Check 1: Required methods exist
            required_methods = self._get_required_methods(component_name)
            missing_methods = []
            for method in required_methods:
                if not hasattr(component, method):
                    missing_methods.append(method)
            
            if missing_methods:
                health_status.is_healthy = False
                health_status.issues.append(f"Missing required methods: {missing_methods}")
            
            # Check 2: Component-specific health validation
            if hasattr(component, 'health_check'):
                try:
                    component_health = component.health_check()
                    health_status.metrics.update(component_health)
                    if not component_health.get("healthy", True):
                        health_status.is_healthy = False
                        health_status.issues.append("Component-specific health check failed")
                except Exception as e:
                    health_status.is_healthy = False
                    health_status.issues.append(f"Health check error: {str(e)}")
            
            # Check 3: Basic functionality test
            try:
                if hasattr(component, 'get_configuration'):
                    config = component.get_configuration()
                    if not isinstance(config, dict):
                        health_status.is_healthy = False
                        health_status.issues.append("Invalid configuration response")
                    else:
                        health_status.metrics["config_size"] = len(config)
            except Exception as e:
                health_status.is_healthy = False
                health_status.issues.append(f"Configuration check error: {str(e)}")
            
            # Check 4: Memory usage (if available)
            try:
                import psutil
                import os
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                health_status.metrics["memory_mb"] = round(memory_mb, 1)
                
                if memory_mb > 1024:  # 1GB warning
                    health_status.issues.append(f"High memory usage: {memory_mb:.1f}MB")
                if memory_mb > 2048:  # 2GB critical
                    health_status.is_healthy = False
                    health_status.issues.append(f"Critical memory usage: {memory_mb:.1f}MB")
            except ImportError:
                health_status.metrics["memory_monitoring"] = "unavailable"
        
        except Exception as e:
            health_status.is_healthy = False
            health_status.issues.append(f"Health check exception: {str(e)}")
        
        # Store health history
        if component_name not in self.health_history:
            self.health_history[component_name] = []
        self.health_history[component_name].append(health_status)
        
        # Keep only last 10 health checks
        if len(self.health_history[component_name]) > 10:
            self.health_history[component_name] = self.health_history[component_name][-10:]
        
        self.last_health_checks[component_name] = current_time
        
        return health_status
    
    def monitor_component_health(self, component: Any) -> None:
        """Start monitoring a component's health.
        
        Args:
            component: Component instance to monitor
        """
        component_name = type(component).__name__
        self.monitored_components[component_name] = component
        
        # Perform initial health check
        health_status = self.check_component_health(component)
        
        logger.info(f"Started monitoring component: {component_name}, healthy: {health_status.is_healthy}")
    
    def report_component_failure(self, component: Any, error: Exception) -> None:
        """Report a component failure.
        
        Args:
            component: Component that failed
            error: Exception that occurred
        """
        component_name = type(component).__name__
        
        # Track failure count
        if component_name not in self.failure_counts:
            self.failure_counts[component_name] = 0
        self.failure_counts[component_name] += 1
        
        # Create failure health status
        failure_status = HealthStatus(
            is_healthy=False,
            last_check=time.time(),
            issues=[f"Component failure: {str(error)}"],
            metrics={
                "failure_count": self.failure_counts[component_name],
                "error_type": type(error).__name__
            },
            component_name=component_name
        )
        
        # Store in health history
        if component_name not in self.health_history:
            self.health_history[component_name] = []
        self.health_history[component_name].append(failure_status)
        
        logger.error(f"Component failure reported: {component_name}, error: {str(error)}")
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get a summary of system health.
        
        Returns:
            Dictionary with system health information
        """
        summary = {
            "overall_healthy": True,
            "total_components": len(self.monitored_components),
            "healthy_components": 0,
            "unhealthy_components": 0,
            "component_status": {},
            "total_failures": sum(self.failure_counts.values()),
            "timestamp": time.time()
        }
        
        for component_name, component in self.monitored_components.items():
            health_status = self.check_component_health(component)
            
            summary["component_status"][component_name] = {
                "healthy": health_status.is_healthy,
                "issues": health_status.issues,
                "metrics": health_status.metrics,
                "last_check": health_status.last_check,
                "failure_count": self.failure_counts.get(component_name, 0)
            }
            
            if health_status.is_healthy:
                summary["healthy_components"] += 1
            else:
                summary["unhealthy_components"] += 1
                summary["overall_healthy"] = False
        
        return summary
    
    def _get_required_methods(self, component_name: str) -> List[str]:
        """Get required methods for a component type.
        
        Args:
            component_name: Name of the component type
            
        Returns:
            List of required method names
        """
        required_methods = {
            "DocumentProcessor": ["process"],
            "ModularDocumentProcessor": ["process"],
            "Embedder": ["embed", "embedding_dim"],
            "ModularEmbedder": ["embed", "embedding_dim"],
            "VectorStore": ["add", "search"],
            "Retriever": ["retrieve"],
            "ModularUnifiedRetriever": ["retrieve"],
            # "AdvancedRetriever": ["retrieve"],  # Removed - functionality moved to ModularUnifiedRetriever
            "AnswerGenerator": ["generate"]
        }
        
        return required_methods.get(component_name, [])


class SystemAnalyticsServiceImpl(SystemAnalyticsService):
    """Implementation of SystemAnalyticsService for universal analytics collection."""
    
    def __init__(self):
        """Initialize the analytics service."""
        self.component_metrics: Dict[str, List[ComponentMetrics]] = {}
        self.system_metrics_history: List[Dict[str, Any]] = []
        self.performance_tracking: Dict[str, Dict[str, Any]] = {}
        self.analytics_enabled = True
        
    def collect_component_metrics(self, component: Any) -> ComponentMetrics:
        """Collect metrics from a component.
        
        Args:
            component: Component instance to collect metrics from
            
        Returns:
            ComponentMetrics object with collected metrics
        """
        component_name = type(component).__name__
        component_type = component.__class__.__module__.split('.')[-1]
        
        metrics = ComponentMetrics(
            component_name=component_name,
            component_type=component_type,
            timestamp=time.time(),
            performance_metrics={},
            resource_usage={},
            error_count=0,
            success_count=0
        )
        
        try:
            # Collect performance metrics
            if hasattr(component, 'get_stats'):
                stats = component.get_stats()
                if isinstance(stats, dict):
                    metrics.performance_metrics.update(stats)
            
            # Collect configuration info
            if hasattr(component, 'get_configuration'):
                config = component.get_configuration()
                if isinstance(config, dict):
                    metrics.performance_metrics["config_complexity"] = len(config)
                    metrics.performance_metrics["has_config"] = True
            
            # Collect resource usage
            try:
                import psutil
                import os
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                metrics.resource_usage = {
                    "memory_rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                    "memory_vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads()
                }
            except (ImportError, psutil.AccessDenied):
                metrics.resource_usage = {"monitoring": "unavailable"}
            
            # Get success/error counts from performance tracking
            if component_name in self.performance_tracking:
                tracking_data = self.performance_tracking[component_name]
                metrics.success_count = tracking_data.get("success_count", 0)
                metrics.error_count = tracking_data.get("error_count", 0)
            
            # Store metrics history
            if component_name not in self.component_metrics:
                self.component_metrics[component_name] = []
            self.component_metrics[component_name].append(metrics)
            
            # Keep only last 100 metrics per component
            if len(self.component_metrics[component_name]) > 100:
                self.component_metrics[component_name] = self.component_metrics[component_name][-100:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics from {component_name}: {str(e)}")
            metrics.error_count += 1
            return metrics
    
    def aggregate_system_metrics(self) -> Dict[str, Any]:
        """Aggregate metrics across all components.
        
        Returns:
            Dictionary with system-wide metrics
        """
        aggregated_metrics = {
            "timestamp": time.time(),
            "total_components": len(self.component_metrics),
            "components": {},
            "system_summary": {
                "total_success_count": 0,
                "total_error_count": 0,
                "average_memory_mb": 0,
                "total_memory_mb": 0,
                "average_cpu_percent": 0
            }
        }
        
        total_memory = 0
        total_cpu = 0
        component_count = 0
        
        for component_name, metrics_list in self.component_metrics.items():
            if not metrics_list:
                continue
            
            # Get latest metrics for this component
            latest_metrics = metrics_list[-1]
            
            component_summary = {
                "name": component_name,
                "type": latest_metrics.component_type,
                "success_count": latest_metrics.success_count,
                "error_count": latest_metrics.error_count,
                "last_updated": latest_metrics.timestamp,
                "resource_usage": latest_metrics.resource_usage,
                "performance_metrics": latest_metrics.performance_metrics,
                "metrics_history_count": len(metrics_list)
            }
            
            aggregated_metrics["components"][component_name] = component_summary
            
            # Add to system totals
            aggregated_metrics["system_summary"]["total_success_count"] += latest_metrics.success_count
            aggregated_metrics["system_summary"]["total_error_count"] += latest_metrics.error_count
            
            # Add memory and CPU if available
            if "memory_rss_mb" in latest_metrics.resource_usage:
                memory_mb = latest_metrics.resource_usage["memory_rss_mb"]
                total_memory += memory_mb
                component_count += 1
            
            if "cpu_percent" in latest_metrics.resource_usage:
                total_cpu += latest_metrics.resource_usage["cpu_percent"]
        
        # Calculate averages
        if component_count > 0:
            aggregated_metrics["system_summary"]["average_memory_mb"] = round(total_memory / component_count, 2)
            aggregated_metrics["system_summary"]["total_memory_mb"] = round(total_memory, 2)
            aggregated_metrics["system_summary"]["average_cpu_percent"] = round(total_cpu / component_count, 2)
        
        # Store in history
        self.system_metrics_history.append(aggregated_metrics)
        
        # Keep only last 50 system metrics
        if len(self.system_metrics_history) > 50:
            self.system_metrics_history = self.system_metrics_history[-50:]
        
        return aggregated_metrics
    
    def track_component_performance(self, component: Any, metrics: Dict[str, Any]) -> None:
        """Track performance metrics for a component.
        
        Args:
            component: Component instance
            metrics: Performance metrics to track
        """
        component_name = type(component).__name__
        
        if component_name not in self.performance_tracking:
            self.performance_tracking[component_name] = {
                "success_count": 0,
                "error_count": 0,
                "total_operations": 0,
                "average_latency": 0,
                "last_operation_time": 0,
                "performance_history": []
            }
        
        tracking_data = self.performance_tracking[component_name]
        
        # Update counts
        if metrics.get("success", False):
            tracking_data["success_count"] += 1
        else:
            tracking_data["error_count"] += 1
        
        tracking_data["total_operations"] += 1
        tracking_data["last_operation_time"] = time.time()
        
        # Update latency
        if "latency_ms" in metrics:
            latency = metrics["latency_ms"]
            current_avg = tracking_data["average_latency"]
            total_ops = tracking_data["total_operations"]
            
            # Calculate new average
            tracking_data["average_latency"] = (current_avg * (total_ops - 1) + latency) / total_ops
        
        # Store performance history
        performance_record = {
            "timestamp": time.time(),
            "metrics": metrics.copy(),
            "component_name": component_name
        }
        
        tracking_data["performance_history"].append(performance_record)
        
        # Keep only last 100 performance records
        if len(tracking_data["performance_history"]) > 100:
            tracking_data["performance_history"] = tracking_data["performance_history"][-100:]
        
        logger.debug(f"Tracked performance for {component_name}: {metrics}")
    
    def generate_analytics_report(self) -> Dict[str, Any]:
        """Generate a comprehensive analytics report.
        
        Returns:
            Dictionary with analytics report
        """
        report = {
            "report_timestamp": time.time(),
            "report_period": "current_session",
            "system_overview": {},
            "component_performance": {},
            "trends": {},
            "recommendations": []
        }
        
        # Get current system metrics
        system_metrics = self.aggregate_system_metrics()
        report["system_overview"] = system_metrics["system_summary"]
        
        # Component performance analysis
        for component_name, tracking_data in self.performance_tracking.items():
            total_ops = tracking_data["total_operations"]
            if total_ops > 0:
                success_rate = tracking_data["success_count"] / total_ops
                error_rate = tracking_data["error_count"] / total_ops
                
                component_performance = {
                    "component_name": component_name,
                    "total_operations": total_ops,
                    "success_rate": round(success_rate, 3),
                    "error_rate": round(error_rate, 3),
                    "average_latency_ms": round(tracking_data["average_latency"], 2),
                    "last_operation": tracking_data["last_operation_time"]
                }
                
                report["component_performance"][component_name] = component_performance
                
                # Add recommendations based on performance
                if error_rate > 0.1:  # More than 10% error rate
                    report["recommendations"].append(
                        f"High error rate detected in {component_name}: {error_rate:.1%}"
                    )
                
                if tracking_data["average_latency"] > 1000:  # More than 1 second
                    report["recommendations"].append(
                        f"High latency detected in {component_name}: {tracking_data['average_latency']:.0f}ms"
                    )
        
        # Memory usage analysis
        if "total_memory_mb" in system_metrics["system_summary"]:
            total_memory = system_metrics["system_summary"]["total_memory_mb"]
            if total_memory > 1024:  # More than 1GB
                report["recommendations"].append(
                    f"High memory usage detected: {total_memory:.1f}MB"
                )
        
        # Trend analysis (if we have historical data)
        if len(self.system_metrics_history) > 1:
            recent_metrics = self.system_metrics_history[-5:]  # Last 5 measurements
            
            # Calculate error trend
            error_counts = [m["system_summary"]["total_error_count"] for m in recent_metrics]
            if len(error_counts) > 1:
                error_trend = error_counts[-1] - error_counts[0]
                report["trends"]["error_trend"] = error_trend
                
                if error_trend > 0:
                    report["recommendations"].append("Error count is increasing over time")
        
        return report


class ABTestingServiceImpl(ABTestingService):
    """Implementation of ABTestingService for universal A/B testing."""
    
    def __init__(self):
        """Initialize the A/B testing service."""
        self.experiments: Dict[str, Dict[str, Any]] = {}
        self.assignments: Dict[str, ExperimentAssignment] = {}  # session_id -> assignment
        self.results: Dict[str, List[ExperimentResult]] = {}  # experiment_id -> results
        self.active_experiments: Dict[str, bool] = {}
        
    def assign_experiment(self, context: Dict[str, Any]) -> ExperimentAssignment:
        """Assign a user to an experiment.
        
        Args:
            context: Context information for assignment
            
        Returns:
            ExperimentAssignment object
        """
        session_id = context.get("session_id", "default")
        
        # Check if we already have an assignment for this session
        if session_id in self.assignments:
            return self.assignments[session_id]
        
        # Find an active experiment
        active_experiments = [exp_id for exp_id, active in self.active_experiments.items() if active]
        
        if not active_experiments:
            # No active experiments, return control variant
            assignment = ExperimentAssignment(
                experiment_id="control",
                variant="control",
                assignment_time=time.time(),
                context=context
            )
            self.assignments[session_id] = assignment
            return assignment
        
        # Simple round-robin assignment for now
        # In production, you might want more sophisticated assignment logic
        experiment_id = active_experiments[0]  # Take first active experiment
        experiment_config = self.experiments.get(experiment_id, {})
        
        # Get variants from experiment config
        variants = experiment_config.get("variants", ["control", "treatment"])
        
        # Simple hash-based assignment for consistency
        import hashlib
        hash_input = f"{session_id}_{experiment_id}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        variant_index = hash_value % len(variants)
        selected_variant = variants[variant_index]
        
        assignment = ExperimentAssignment(
            experiment_id=experiment_id,
            variant=selected_variant,
            assignment_time=time.time(),
            context=context
        )
        
        self.assignments[session_id] = assignment
        
        logger.info(f"Assigned session {session_id} to experiment {experiment_id}, variant {selected_variant}")
        
        return assignment
    
    def track_experiment_outcome(self, experiment_id: str, variant: str, outcome: Dict[str, Any]) -> None:
        """Track the outcome of an experiment.
        
        Args:
            experiment_id: Unique experiment identifier
            variant: Variant that was tested
            outcome: Outcome data
        """
        result = ExperimentResult(
            experiment_id=experiment_id,
            variant=variant,
            outcome=outcome,
            timestamp=time.time(),
            success=outcome.get("success", True)
        )
        
        if experiment_id not in self.results:
            self.results[experiment_id] = []
        
        self.results[experiment_id].append(result)
        
        # Keep only last 1000 results per experiment
        if len(self.results[experiment_id]) > 1000:
            self.results[experiment_id] = self.results[experiment_id][-1000:]
        
        logger.debug(f"Tracked outcome for experiment {experiment_id}, variant {variant}: {outcome}")
    
    def get_experiment_results(self, experiment_name: str) -> List[ExperimentResult]:
        """Get results for an experiment.
        
        Args:
            experiment_name: Name of the experiment
            
        Returns:
            List of experiment results
        """
        return self.results.get(experiment_name, [])
    
    def configure_experiment(self, experiment_config: Dict[str, Any]) -> None:
        """Configure a new experiment.
        
        Args:
            experiment_config: Configuration for the experiment
        """
        experiment_id = experiment_config.get("experiment_id")
        if not experiment_id:
            raise ValueError("experiment_id is required in experiment configuration")
        
        # Default experiment configuration
        default_config = {
            "experiment_id": experiment_id,
            "name": experiment_config.get("name", experiment_id),
            "description": experiment_config.get("description", ""),
            "variants": experiment_config.get("variants", ["control", "treatment"]),
            "traffic_allocation": experiment_config.get("traffic_allocation", 1.0),  # 100% traffic
            "start_time": experiment_config.get("start_time", time.time()),
            "end_time": experiment_config.get("end_time", time.time() + 86400 * 7),  # 7 days default
            "success_metrics": experiment_config.get("success_metrics", ["conversion"]),
            "created_at": time.time(),
            "status": "configured"
        }
        
        # Merge with provided config
        final_config = {**default_config, **experiment_config}
        
        self.experiments[experiment_id] = final_config
        
        # Check if experiment should be active
        current_time = time.time()
        if (final_config["start_time"] <= current_time <= final_config["end_time"]):
            self.active_experiments[experiment_id] = True
            logger.info(f"Experiment {experiment_id} is now active")
        else:
            self.active_experiments[experiment_id] = False
            logger.info(f"Experiment {experiment_id} configured but not active")
    
    def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """Get status and results for an experiment.
        
        Args:
            experiment_id: Unique experiment identifier
            
        Returns:
            Dictionary with experiment status
        """
        if experiment_id not in self.experiments:
            return {"error": f"Experiment {experiment_id} not found"}
        
        experiment_config = self.experiments[experiment_id]
        results = self.results.get(experiment_id, [])
        
        # Calculate basic statistics
        stats = {
            "total_assignments": len([a for a in self.assignments.values() if a.experiment_id == experiment_id]),
            "total_outcomes": len(results),
            "variant_stats": {}
        }
        
        # Group results by variant
        variant_groups = {}
        for result in results:
            variant = result.variant
            if variant not in variant_groups:
                variant_groups[variant] = []
            variant_groups[variant].append(result)
        
        # Calculate stats per variant
        for variant, variant_results in variant_groups.items():
            success_count = sum(1 for r in variant_results if r.success)
            total_count = len(variant_results)
            
            stats["variant_stats"][variant] = {
                "total_outcomes": total_count,
                "success_count": success_count,
                "success_rate": success_count / total_count if total_count > 0 else 0,
                "average_outcome": self._calculate_average_outcome(variant_results)
            }
        
        return {
            "experiment_id": experiment_id,
            "config": experiment_config,
            "is_active": self.active_experiments.get(experiment_id, False),
            "statistics": stats,
            "last_updated": time.time()
        }
    
    def _calculate_average_outcome(self, results: List[ExperimentResult]) -> Dict[str, float]:
        """Calculate average outcome metrics.
        
        Args:
            results: List of experiment results
            
        Returns:
            Dictionary with average metrics
        """
        if not results:
            return {}
        
        # Extract numeric metrics from outcomes
        numeric_metrics = {}
        for result in results:
            for key, value in result.outcome.items():
                if isinstance(value, (int, float)):
                    if key not in numeric_metrics:
                        numeric_metrics[key] = []
                    numeric_metrics[key].append(value)
        
        # Calculate averages
        averages = {}
        for metric, values in numeric_metrics.items():
            if values:
                averages[metric] = sum(values) / len(values)
        
        return averages
    
    def stop_experiment(self, experiment_id: str) -> None:
        """Stop an active experiment.
        
        Args:
            experiment_id: Unique experiment identifier
        """
        if experiment_id in self.active_experiments:
            self.active_experiments[experiment_id] = False
            
            if experiment_id in self.experiments:
                self.experiments[experiment_id]["status"] = "stopped"
                self.experiments[experiment_id]["end_time"] = time.time()
            
            logger.info(f"Stopped experiment {experiment_id}")
    
    def get_all_experiments(self) -> Dict[str, Dict[str, Any]]:
        """Get all configured experiments.
        
        Returns:
            Dictionary with all experiments
        """
        return {
            "experiments": self.experiments,
            "active_experiments": self.active_experiments,
            "total_assignments": len(self.assignments),
            "total_results": sum(len(results) for results in self.results.values())
        }


class ConfigurationServiceImpl(ConfigurationService):
    """Implementation of ConfigurationService for universal configuration management."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize the configuration service.
        
        Args:
            config_manager: ConfigManager instance for configuration access
        """
        self.config_manager = config_manager
        self.config_cache: Dict[str, Dict[str, Any]] = {}
        self.config_history: List[Dict[str, Any]] = []
        self.feature_flags: Dict[str, bool] = {}
        self.dynamic_configs: Dict[str, Any] = {}
        
        # Initialize with current configuration
        self._load_current_config()
    
    def _load_current_config(self) -> None:
        """Load current configuration from config manager."""
        try:
            config = self.config_manager.config
            
            # Cache component configurations
            self.config_cache["document_processor"] = {
                "type": config.document_processor.type,
                "config": config.document_processor.config
            }
            
            self.config_cache["embedder"] = {
                "type": config.embedder.type,
                "config": config.embedder.config
            }
            
            self.config_cache["retriever"] = {
                "type": config.retriever.type,
                "config": config.retriever.config
            }
            
            self.config_cache["answer_generator"] = {
                "type": config.answer_generator.type,
                "config": config.answer_generator.config
            }
            
            # Cache vector store if present
            if hasattr(config, 'vector_store') and config.vector_store:
                self.config_cache["vector_store"] = {
                    "type": config.vector_store.type,
                    "config": config.vector_store.config
                }
            
            # Cache global settings
            self.config_cache["global_settings"] = config.global_settings
            
            # Load feature flags from global settings
            if hasattr(config, 'global_settings') and config.global_settings:
                self.feature_flags = config.global_settings.get("feature_flags", {})
            
            logger.info("Configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            raise
    
    def get_component_config(self, component_name: str) -> Dict[str, Any]:
        """Get configuration for a component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            Dictionary with component configuration
        """
        if component_name not in self.config_cache:
            raise KeyError(f"Component '{component_name}' not found in configuration")
        
        config = self.config_cache[component_name].copy()
        
        # Apply any dynamic configuration overrides
        if component_name in self.dynamic_configs:
            config.update(self.dynamic_configs[component_name])
        
        return config
    
    def update_component_config(self, component_name: str, config: Dict[str, Any]) -> None:
        """Update configuration for a component.
        
        Args:
            component_name: Name of the component
            config: New configuration
        """
        # Store the update in dynamic configs (runtime changes)
        if component_name not in self.dynamic_configs:
            self.dynamic_configs[component_name] = {}
        
        self.dynamic_configs[component_name].update(config)
        
        # Record configuration change
        change_record = {
            "timestamp": time.time(),
            "component": component_name,
            "changes": config,
            "type": "update"
        }
        
        self.config_history.append(change_record)
        
        # Keep only last 100 configuration changes
        if len(self.config_history) > 100:
            self.config_history = self.config_history[-100:]
        
        logger.info(f"Updated configuration for {component_name}: {config}")
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate a configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required component types
        required_components = ["document_processor", "embedder", "retriever", "answer_generator"]
        
        for component in required_components:
            if component not in config:
                errors.append(f"Missing required component: {component}")
                continue
            
            component_config = config[component]
            
            # Check for required fields
            if "type" not in component_config:
                errors.append(f"Component {component} missing 'type' field")
            
            if "config" not in component_config:
                errors.append(f"Component {component} missing 'config' field")
            
            # Component-specific validation
            if component == "document_processor":
                valid_types = ["hybrid_pdf", "processor_hybrid_pdf", "modular"]
                if component_config.get("type") not in valid_types:
                    errors.append(f"Invalid document processor type: {component_config.get('type')}")
            
            elif component == "embedder":
                valid_types = ["sentence_transformer", "modular"]
                if component_config.get("type") not in valid_types:
                    errors.append(f"Invalid embedder type: {component_config.get('type')}")
            
            elif component == "retriever":
                valid_types = ["unified", "modular_unified"]
                if component_config.get("type") not in valid_types:
                    errors.append(f"Invalid retriever type: {component_config.get('type')}")
            
            elif component == "answer_generator":
                valid_types = ["ollama", "openai", "modular"]
                if component_config.get("type") not in valid_types:
                    errors.append(f"Invalid answer generator type: {component_config.get('type')}")
        
        # Validate global settings if present
        if "global_settings" in config:
            global_settings = config["global_settings"]
            
            # Check for environment settings
            if "environment" in global_settings:
                valid_envs = ["development", "staging", "production"]
                if global_settings["environment"] not in valid_envs:
                    errors.append(f"Invalid environment: {global_settings['environment']}")
            
            # Check logging level
            if "logging_level" in global_settings:
                valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                if global_settings["logging_level"] not in valid_levels:
                    errors.append(f"Invalid logging level: {global_settings['logging_level']}")
        
        return errors
    
    def get_system_configuration(self) -> Dict[str, Any]:
        """Get the complete system configuration.
        
        Returns:
            Dictionary with system configuration
        """
        system_config = {
            "components": self.config_cache.copy(),
            "feature_flags": self.feature_flags,
            "dynamic_configs": self.dynamic_configs,
            "configuration_history": self.config_history,
            "last_updated": time.time()
        }
        
        return system_config
    
    def get_feature_flag(self, flag_name: str, default: bool = False) -> bool:
        """Get a feature flag value.
        
        Args:
            flag_name: Name of the feature flag
            default: Default value if flag not found
            
        Returns:
            Boolean value of the feature flag
        """
        return self.feature_flags.get(flag_name, default)
    
    def set_feature_flag(self, flag_name: str, value: bool) -> None:
        """Set a feature flag value.
        
        Args:
            flag_name: Name of the feature flag
            value: Boolean value to set
        """
        old_value = self.feature_flags.get(flag_name)
        self.feature_flags[flag_name] = value
        
        # Record the change
        change_record = {
            "timestamp": time.time(),
            "feature_flag": flag_name,
            "old_value": old_value,
            "new_value": value,
            "type": "feature_flag_update"
        }
        
        self.config_history.append(change_record)
        
        logger.info(f"Feature flag {flag_name} set to {value}")
    
    def reload_configuration(self) -> None:
        """Reload configuration from the config manager."""
        try:
            # Reload from config manager
            self.config_manager.reload()
            
            # Clear cache and reload
            self.config_cache.clear()
            self._load_current_config()
            
            # Record reload
            change_record = {
                "timestamp": time.time(),
                "type": "configuration_reload",
                "message": "Configuration reloaded from file"
            }
            
            self.config_history.append(change_record)
            
            logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {str(e)}")
            raise
    
    def get_configuration_history(self) -> List[Dict[str, Any]]:
        """Get configuration change history.
        
        Returns:
            List of configuration change records
        """
        return self.config_history.copy()
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export current configuration for backup/sharing.
        
        Returns:
            Dictionary with exportable configuration
        """
        return {
            "exported_at": time.time(),
            "base_configuration": self.config_cache,
            "feature_flags": self.feature_flags,
            "dynamic_configs": self.dynamic_configs,
            "version": "1.0"
        }
    
    def import_configuration(self, imported_config: Dict[str, Any]) -> None:
        """Import configuration from backup/sharing.
        
        Args:
            imported_config: Configuration to import
        """
        try:
            # Validate imported configuration
            errors = self.validate_configuration(imported_config.get("base_configuration", {}))
            if errors:
                raise ValueError(f"Invalid imported configuration: {errors}")
            
            # Apply imported configuration
            if "base_configuration" in imported_config:
                self.config_cache.update(imported_config["base_configuration"])
            
            if "feature_flags" in imported_config:
                self.feature_flags.update(imported_config["feature_flags"])
            
            if "dynamic_configs" in imported_config:
                self.dynamic_configs.update(imported_config["dynamic_configs"])
            
            # Record import
            change_record = {
                "timestamp": time.time(),
                "type": "configuration_import",
                "imported_from": imported_config.get("exported_at", "unknown"),
                "version": imported_config.get("version", "unknown")
            }
            
            self.config_history.append(change_record)
            
            logger.info("Configuration imported successfully")
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {str(e)}")
            raise


class BackendManagementServiceImpl(BackendManagementService):
    """Implementation of BackendManagementService for universal backend management."""
    
    def __init__(self):
        """Initialize the backend management service."""
        self.registered_backends: Dict[str, Dict[str, Any]] = {}
        self.backend_status: Dict[str, BackendStatus] = {}
        self.component_backends: Dict[str, str] = {}  # component_id -> backend_name
        self.migration_history: List[Dict[str, Any]] = []
        
        # Initialize with default backends
        self._register_default_backends()
    
    def _register_default_backends(self) -> None:
        """Register default backends (FAISS, etc.)."""
        # FAISS vector backend
        faiss_config = {
            "backend_name": "faiss",
            "backend_type": "vector_store",
            "description": "FAISS local vector store",
            "capabilities": ["vector_search", "local_storage", "fast_indexing"],
            "config": {
                "index_type": "IndexFlatIP",
                "metric": "inner_product",
                "normalize_vectors": True
            },
            "health_check_enabled": True,
            "last_health_check": 0
        }
        
        self.registered_backends["faiss"] = faiss_config
        self.backend_status["faiss"] = BackendStatus(
            backend_name="faiss",
            is_available=True,
            last_check=time.time(),
            health_metrics={"type": "local", "ready": True}
        )
        
        # Weaviate backend (if available)
        weaviate_config = {
            "backend_name": "weaviate",
            "backend_type": "vector_store",
            "description": "Weaviate cloud vector store",
            "capabilities": ["vector_search", "cloud_storage", "graph_queries"],
            "config": {
                "url": "http://localhost:8080",
                "timeout": 30,
                "additional_headers": {}
            },
            "health_check_enabled": True,
            "last_health_check": 0
        }
        
        self.registered_backends["weaviate"] = weaviate_config
        self.backend_status["weaviate"] = BackendStatus(
            backend_name="weaviate",
            is_available=False,  # Assume not available until health check
            last_check=time.time(),
            health_metrics={"type": "cloud", "ready": False},
            error_message="Not tested yet"
        )
        
        logger.info("Default backends registered: faiss, weaviate")
    
    def register_backend(self, backend_name: str, backend_config: Dict[str, Any]) -> None:
        """Register a new backend.
        
        Args:
            backend_name: Name of the backend
            backend_config: Configuration for the backend
        """
        required_fields = ["backend_type", "description", "capabilities", "config"]
        for field in required_fields:
            if field not in backend_config:
                raise ValueError(f"Backend config missing required field: {field}")
        
        # Prepare backend configuration
        full_config = {
            "backend_name": backend_name,
            "registered_at": time.time(),
            "health_check_enabled": backend_config.get("health_check_enabled", True),
            "last_health_check": 0,
            **backend_config
        }
        
        self.registered_backends[backend_name] = full_config
        
        # Initialize backend status
        self.backend_status[backend_name] = BackendStatus(
            backend_name=backend_name,
            is_available=False,  # Will be determined by health check
            last_check=time.time(),
            health_metrics={"registered": True}
        )
        
        logger.info(f"Registered backend: {backend_name} ({backend_config['backend_type']})")
    
    def switch_component_backend(self, component: Any, backend_name: str) -> None:
        """Switch a component to a different backend.
        
        Args:
            component: Component to switch
            backend_name: Name of the target backend
        """
        if backend_name not in self.registered_backends:
            raise ValueError(f"Backend '{backend_name}' not registered")
        
        backend_config = self.registered_backends[backend_name]
        backend_status = self.backend_status[backend_name]
        
        # Check if backend is available
        if not backend_status.is_available:
            # Perform health check before switching
            current_status = self.get_backend_status(backend_name)
            if not current_status.is_available:
                raise RuntimeError(f"Backend '{backend_name}' is not available: {current_status.error_message}")
        
        component_name = type(component).__name__
        component_id = f"{component_name}_{id(component)}"
        
        # Record current backend for migration tracking
        old_backend = self.component_backends.get(component_id, "unknown")
        
        try:
            # Attempt to switch backend
            if hasattr(component, 'switch_backend'):
                # Component has built-in backend switching
                component.switch_backend(backend_name, backend_config["config"])
            elif hasattr(component, 'reconfigure'):
                # Component supports reconfiguration
                component.reconfigure(backend_config["config"])
            else:
                # Log that switch is not directly supported
                logger.warning(f"Component {component_name} does not support direct backend switching")
                # Still record the intended backend assignment
            
            # Update component backend mapping
            self.component_backends[component_id] = backend_name
            
            # Record migration
            migration_record = {
                "timestamp": time.time(),
                "component_id": component_id,
                "component_name": component_name,
                "from_backend": old_backend,
                "to_backend": backend_name,
                "success": True,
                "migration_type": "switch"
            }
            
            self.migration_history.append(migration_record)
            
            # Keep only last 100 migrations
            if len(self.migration_history) > 100:
                self.migration_history = self.migration_history[-100:]
            
            logger.info(f"Switched {component_name} from {old_backend} to {backend_name}")
            
        except Exception as e:
            # Record failed migration
            migration_record = {
                "timestamp": time.time(),
                "component_id": component_id,
                "component_name": component_name,
                "from_backend": old_backend,
                "to_backend": backend_name,
                "success": False,
                "error": str(e),
                "migration_type": "switch"
            }
            
            self.migration_history.append(migration_record)
            
            logger.error(f"Failed to switch {component_name} to {backend_name}: {e}")
            raise RuntimeError(f"Backend switch failed: {e}") from e
    
    def get_backend_status(self, backend_name: str) -> BackendStatus:
        """Get status information for a backend.
        
        Args:
            backend_name: Name of the backend
            
        Returns:
            BackendStatus object with status information
        """
        if backend_name not in self.registered_backends:
            return BackendStatus(
                backend_name=backend_name,
                is_available=False,
                error_message="Backend not registered"
            )
        
        backend_config = self.registered_backends[backend_name]
        current_time = time.time()
        
        # Check if we need to perform a health check
        last_check = backend_config.get("last_health_check", 0)
        health_check_interval = 30.0  # 30 seconds
        
        if (current_time - last_check > health_check_interval and 
            backend_config.get("health_check_enabled", True)):
            
            # Perform health check
            health_status = self._perform_health_check(backend_name, backend_config)
            
            # Update backend status
            self.backend_status[backend_name] = health_status
            self.registered_backends[backend_name]["last_health_check"] = current_time
        
        return self.backend_status[backend_name]
    
    def _perform_health_check(self, backend_name: str, backend_config: Dict[str, Any]) -> BackendStatus:
        """Perform health check for a backend.
        
        Args:
            backend_name: Name of the backend
            backend_config: Backend configuration
            
        Returns:
            BackendStatus object with health check results
        """
        health_metrics = {"check_time": time.time()}
        is_available = True
        error_message = None
        
        try:
            backend_type = backend_config["backend_type"]
            
            if backend_type == "vector_store":
                if backend_name == "faiss":
                    # FAISS health check - always available (local)
                    health_metrics.update({
                        "type": "local",
                        "storage": "memory",
                        "ready": True
                    })
                elif backend_name == "weaviate":
                    # Weaviate health check - check connection
                    config = backend_config["config"]
                    url = config.get("url", "http://localhost:8080")
                    
                    try:
                        import requests
                        response = requests.get(f"{url}/v1/meta", timeout=5)
                        if response.status_code == 200:
                            health_metrics.update({
                                "type": "cloud",
                                "url": url,
                                "response_time_ms": response.elapsed.total_seconds() * 1000,
                                "ready": True
                            })
                        else:
                            is_available = False
                            error_message = f"Weaviate returned status {response.status_code}"
                    except ImportError:
                        is_available = False
                        error_message = "requests library not available"
                    except Exception as e:
                        is_available = False
                        error_message = f"Connection failed: {str(e)}"
            
            else:
                # Unknown backend type
                health_metrics["type"] = "unknown"
                logger.warning(f"Unknown backend type for health check: {backend_type}")
        
        except Exception as e:
            is_available = False
            error_message = f"Health check failed: {str(e)}"
            health_metrics["error"] = str(e)
        
        return BackendStatus(
            backend_name=backend_name,
            is_available=is_available,
            last_check=time.time(),
            health_metrics=health_metrics,
            error_message=error_message
        )
    
    def migrate_component_data(self, component: Any, from_backend: str, to_backend: str) -> None:
        """Migrate component data between backends.
        
        Args:
            component: Component to migrate
            from_backend: Source backend name
            to_backend: Target backend name
        """
        if from_backend not in self.registered_backends:
            raise ValueError(f"Source backend '{from_backend}' not registered")
        
        if to_backend not in self.registered_backends:
            raise ValueError(f"Target backend '{to_backend}' not registered")
        
        component_name = type(component).__name__
        component_id = f"{component_name}_{id(component)}"
        
        try:
            # Check if component supports data migration
            if hasattr(component, 'migrate_data'):
                # Component has built-in data migration
                component.migrate_data(from_backend, to_backend)
            elif hasattr(component, 'export_data') and hasattr(component, 'import_data'):
                # Component supports export/import pattern
                data = component.export_data(from_backend)
                component.import_data(to_backend, data)
            else:
                # Manual migration guidance
                logger.warning(f"Component {component_name} does not support automatic data migration")
                logger.info(f"Manual migration required from {from_backend} to {to_backend}")
                # Still switch the backend assignment
                self.component_backends[component_id] = to_backend
            
            # Record successful migration
            migration_record = {
                "timestamp": time.time(),
                "component_id": component_id,
                "component_name": component_name,
                "from_backend": from_backend,
                "to_backend": to_backend,
                "success": True,
                "migration_type": "data_migration",
                "data_migrated": True
            }
            
            self.migration_history.append(migration_record)
            
            logger.info(f"Migrated {component_name} data from {from_backend} to {to_backend}")
            
        except Exception as e:
            # Record failed migration
            migration_record = {
                "timestamp": time.time(),
                "component_id": component_id,
                "component_name": component_name,
                "from_backend": from_backend,
                "to_backend": to_backend,
                "success": False,
                "error": str(e),
                "migration_type": "data_migration"
            }
            
            self.migration_history.append(migration_record)
            
            logger.error(f"Failed to migrate {component_name} data: {e}")
            raise RuntimeError(f"Data migration failed: {e}") from e
    
    def get_all_backends(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered backends.
        
        Returns:
            Dictionary with all backend information
        """
        backends_info = {}
        
        for backend_name, backend_config in self.registered_backends.items():
            status = self.get_backend_status(backend_name)
            
            backends_info[backend_name] = {
                "config": backend_config,
                "status": {
                    "is_available": status.is_available,
                    "last_check": status.last_check,
                    "health_metrics": status.health_metrics,
                    "error_message": status.error_message
                },
                "assigned_components": [
                    comp_id for comp_id, backend in self.component_backends.items() 
                    if backend == backend_name
                ]
            }
        
        return backends_info
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get backend migration history.
        
        Returns:
            List of migration records
        """
        return self.migration_history.copy()
    
    def unregister_backend(self, backend_name: str) -> None:
        """Unregister a backend.
        
        Args:
            backend_name: Name of the backend to unregister
        """
        if backend_name not in self.registered_backends:
            logger.warning(f"Backend '{backend_name}' not registered")
            return
        
        # Check if any components are using this backend
        using_components = [
            comp_id for comp_id, backend in self.component_backends.items() 
            if backend == backend_name
        ]
        
        if using_components:
            raise RuntimeError(f"Cannot unregister backend '{backend_name}': "
                             f"still in use by components: {using_components}")
        
        # Remove backend
        del self.registered_backends[backend_name]
        if backend_name in self.backend_status:
            del self.backend_status[backend_name]
        
        logger.info(f"Unregistered backend: {backend_name}")
    
    def check_component_backend_health(self, component: Any) -> None:
        """Check backend health for a component and switch if necessary (migrated from AdvancedRetriever).
        
        Args:
            component: Component to check backend health for
        """
        component_name = type(component).__name__
        component_id = f"{component_name}_{id(component)}"
        
        # Get current backend for this component
        current_backend = self.component_backends.get(component_id)
        if not current_backend:
            # No backend assigned yet - try to detect from component
            if hasattr(component, 'active_backend_name'):
                current_backend = component.active_backend_name
                self.component_backends[component_id] = current_backend
            else:
                logger.warning(f"Component {component_name} has no backend assigned")
                return
        
        try:
            # Check health of current backend
            backend_status = self.get_backend_status(current_backend)
            
            if not backend_status.is_available:
                logger.warning(
                    f"Backend {current_backend} for {component_name} is unhealthy: "
                    f"{backend_status.error_message}"
                )
                self._consider_backend_switch_for_component(component, current_backend)
        except Exception as e:
            logger.error(f"Backend health check failed for {component_name}: {str(e)}")
    
    def _consider_backend_switch_for_component(self, component: Any, failing_backend: str) -> None:
        """Consider switching to fallback backend for a component.
        
        Args:
            component: Component to switch backend for
            failing_backend: Name of the failing backend
        """
        component_name = type(component).__name__
        
        # Get fallback backend if available
        fallback_backend = None
        if hasattr(component, 'fallback_backend_name'):
            fallback_backend = component.fallback_backend_name
        
        # If no fallback configured, try to find available backend
        if not fallback_backend:
            for backend_name in self.registered_backends:
                if backend_name != failing_backend:
                    status = self.get_backend_status(backend_name)
                    if status.is_available:
                        fallback_backend = backend_name
                        break
        
        if not fallback_backend:
            logger.error(f"No fallback backend available for {component_name}")
            return
        
        if fallback_backend == failing_backend:
            logger.warning(f"Fallback backend same as failing backend for {component_name}")
            return
        
        try:
            logger.info(f"Switching {component_name} from {failing_backend} to {fallback_backend}")
            
            # Use the existing switch_component_backend method
            self.switch_component_backend(component, fallback_backend)
            
            # Update component's backend references if supported
            if hasattr(component, 'active_backend_name'):
                old_backend = component.active_backend_name
                component.active_backend_name = fallback_backend
                
                # Update fallback to previous active if supported
                if hasattr(component, 'fallback_backend_name'):
                    component.fallback_backend_name = old_backend
            
            logger.info(f"Successfully switched {component_name} to {fallback_backend}")
            
        except Exception as e:
            logger.error(f"Failed to switch {component_name} backend: {str(e)}")
    
    def monitor_component_backends(self, components: List[Any]) -> Dict[str, Any]:
        """Monitor backend health for multiple components.
        
        Args:
            components: List of components to monitor
            
        Returns:
            Dictionary with monitoring results
        """
        monitoring_results = {
            "timestamp": time.time(),
            "components_checked": len(components),
            "healthy_components": 0,
            "unhealthy_components": 0,
            "backend_switches": 0,
            "component_status": {}
        }
        
        for component in components:
            component_name = type(component).__name__
            component_id = f"{component_name}_{id(component)}"
            
            try:
                # Check backend health
                self.check_component_backend_health(component)
                
                # Get current backend status
                current_backend = self.component_backends.get(component_id, "unknown")
                backend_status = self.get_backend_status(current_backend) if current_backend != "unknown" else None
                
                component_status = {
                    "backend": current_backend,
                    "healthy": backend_status.is_available if backend_status else False,
                    "last_check": backend_status.last_check if backend_status else 0,
                    "error": backend_status.error_message if backend_status and backend_status.error_message else None
                }
                
                monitoring_results["component_status"][component_name] = component_status
                
                if component_status["healthy"]:
                    monitoring_results["healthy_components"] += 1
                else:
                    monitoring_results["unhealthy_components"] += 1
                    
            except Exception as e:
                logger.error(f"Error monitoring {component_name}: {str(e)}")
                monitoring_results["component_status"][component_name] = {
                    "backend": "unknown",
                    "healthy": False,
                    "error": str(e)
                }
                monitoring_results["unhealthy_components"] += 1
        
        return monitoring_results


class PlatformOrchestrator:
    """
    Platform Orchestrator manages system lifecycle and platform integration.
    
    Responsibilities:
    - Component initialization and dependency injection
    - Configuration management
    - Platform-specific adaptations (cloud, on-premise, edge)
    - System health monitoring
    - Resource management
    - API exposure and routing
    
    This class uses the ComponentFactory for direct component instantiation
    during Phase 3, providing improved performance while maintaining backward compatibility.
    """
    
    def __init__(self, config_path: Path):
        """
        Initialize platform orchestrator with configuration.
        
        Args:
            config_path: Path to YAML configuration file
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration is invalid
        """
        # Convert string to Path if needed
        if isinstance(config_path, str):
            config_path = Path(config_path)
            
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        self.config_path = config_path
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        
        # Component storage
        self._components: Dict[str, Any] = {}
        self._initialized = False
        
        # Phase 2: Track architecture type for compatibility
        self._using_unified_retriever = False
        self._retriever_type = None
        
        # Initialize system services
        self.health_service = ComponentHealthServiceImpl()
        self.analytics_service = SystemAnalyticsServiceImpl()
        self.ab_testing_service = ABTestingServiceImpl()
        self.configuration_service = ConfigurationServiceImpl(self.config_manager)
        self.backend_management_service = BackendManagementServiceImpl()
        
        # Initialize system
        self._initialize_system()
        
        logger.info(f"Platform Orchestrator initialized with config: {config_path}")
    
    def _initialize_system(self) -> None:
        """
        Initialize all system components with Phase 3 direct wiring.
        
        This method uses ComponentFactory for direct component instantiation,
        supporting both legacy and unified architectures with improved performance.
        """
        logger.info("Initializing RAG system components...")
        
        try:
            # Create document processor using factory
            proc_config = self.config.document_processor
            self._components['document_processor'] = ComponentFactory.create_processor(
                proc_config.type,
                **proc_config.config
            )
            logger.debug(f"Document processor initialized: {proc_config.type}")
            
            # Create embedder using factory
            emb_config = self.config.embedder
            self._components['embedder'] = ComponentFactory.create_embedder(
                emb_config.type,
                **emb_config.config
            )
            logger.debug(f"Embedder initialized: {emb_config.type}")
            
            # Phase 3: Architecture detection with factory-based instantiation
            ret_config = self.config.retriever
            if ret_config.type in ["unified", "modular_unified"]:
                # Phase 2: Use unified retriever (no separate vector store needed)
                self._components['retriever'] = ComponentFactory.create_retriever(
                    ret_config.type,
                    embedder=self._components['embedder'],
                    **ret_config.config
                )
                logger.info(f"Phase 3: Unified retriever initialized: {ret_config.type}")
                
                # Mark that we're using unified architecture
                self._using_unified_retriever = True
                self._retriever_type = ret_config.type
                
            else:
                # Phase 1: Legacy architecture with separate vector store and retriever
                vs_config = self.config.vector_store
                if vs_config is None:
                    raise RuntimeError("Legacy architecture requires vector_store configuration")
                
                self._components['vector_store'] = ComponentFactory.create_vector_store(
                    vs_config.type,
                    **vs_config.config
                )
                logger.debug(f"Vector store initialized: {vs_config.type}")
                
                self._components['retriever'] = ComponentFactory.create_retriever(
                    ret_config.type,
                    vector_store=self._components['vector_store'],
                    embedder=self._components['embedder'],
                    **ret_config.config
                )
                logger.debug(f"Retriever initialized: {ret_config.type}")
                
                # Mark that we're using legacy architecture
                self._using_unified_retriever = False
                self._retriever_type = ret_config.type
            
            # Create answer generator using factory
            gen_config = self.config.answer_generator
            self._components['answer_generator'] = ComponentFactory.create_generator(
                gen_config.type,
                config=gen_config.config
            )
            logger.debug(f"Answer generator initialized: {gen_config.type}")
            
            # Note: Query processor will be created in the next step
            # For now, we'll handle query processing directly
            
            # Register all components with health service
            for component_name, component in self._components.items():
                self.health_service.monitor_component_health(component)
            
            self._initialized = True
            logger.info("System initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            raise RuntimeError(f"System initialization failed: {str(e)}") from e
    
    def process_document(self, file_path: Path) -> int:
        """
        Process and index a document.
        
        This method orchestrates the document processing workflow:
        1. Process document into chunks
        2. Generate embeddings for chunks
        3. Store chunks and embeddings in vector store
        
        Args:
            file_path: Path to document file
            
        Returns:
            Number of document chunks created
            
        Raises:
            FileNotFoundError: If document file doesn't exist
            RuntimeError: If processing fails
        """
        if not self._initialized:
            raise RuntimeError("System not initialized")
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")
        
        logger.info(f"Processing document: {file_path}")
        
        try:
            # Process document using existing component
            processor = self._components['document_processor']
            documents = processor.process(file_path)
            
            if not documents:
                logger.warning(f"No documents created from {file_path}")
                return 0
            
            logger.debug(f"Created {len(documents)} document chunks")
            
            # Generate embeddings using existing component
            embedder = self._components['embedder']
            texts = [doc.content for doc in documents]
            embeddings = embedder.embed(texts)
            
            # Add embeddings to documents
            for doc, embedding in zip(documents, embeddings):
                doc.embedding = embedding
            
            # Phase 2: Handle unified vs legacy architecture
            retriever = self._components['retriever']
            
            if self._using_unified_retriever:
                # Phase 2: Direct indexing in unified retriever
                retriever.index_documents(documents)
                logger.debug(f"Indexed documents in unified retriever")
            else:
                # Phase 1: Legacy architecture - store in vector store first
                vector_store = self._components['vector_store']
                vector_store.add(documents)
                
                # Then index in retriever if it supports it
                if hasattr(retriever, 'index_documents'):
                    retriever.index_documents(documents)
                
                logger.debug(f"Indexed documents in legacy vector store + retriever")
            
            logger.info(f"Successfully indexed {len(documents)} chunks from {file_path}")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Failed to process document {file_path}: {str(e)}")
            raise RuntimeError(f"Document processing failed: {str(e)}") from e
    
    def process_documents(self, file_paths: List[Path]) -> Dict[str, int]:
        """
        Process multiple documents and return chunk counts.
        
        Args:
            file_paths: List of paths to document files
            
        Returns:
            Dictionary mapping file paths to chunk counts
        """
        if not self._initialized:
            raise RuntimeError("System not initialized")
        
        results = {}
        failed_files = []
        
        logger.info(f"Processing {len(file_paths)} documents...")
        
        for file_path in file_paths:
            try:
                chunk_count = self.process_document(file_path)
                results[str(file_path)] = chunk_count
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {str(e)}")
                failed_files.append(str(file_path))
                results[str(file_path)] = 0
        
        if failed_files:
            logger.warning(f"Failed to process {len(failed_files)} files: {failed_files}")
        
        total_chunks = sum(results.values())
        logger.info(f"Batch processing complete: {total_chunks} total chunks from {len(file_paths)} files")
        
        return results
    
    def index_documents(self, documents: List[Document]) -> int:
        """
        Directly index pre-created Document objects into the retrieval system.
        
        This method allows bypassing file processing when you already have
        Document objects (e.g., from testing, external processing, etc.).
        
        Args:
            documents: List of Document objects to index
            
        Returns:
            Number of documents successfully indexed
            
        Raises:
            RuntimeError: If system not initialized or indexing fails
        """
        if not self._initialized:
            raise RuntimeError("System not initialized")
        
        if not documents:
            logger.warning("No documents provided for indexing")
            return 0
        
        logger.info(f"Indexing {len(documents)} pre-created documents...")
        
        try:
            # Generate embeddings for documents that don't have them
            embedder = self._components['embedder']
            documents_needing_embeddings = [doc for doc in documents if doc.embedding is None]
            
            if documents_needing_embeddings:
                logger.debug(f"Generating embeddings for {len(documents_needing_embeddings)} documents")
                texts = [doc.content for doc in documents_needing_embeddings]
                embeddings = embedder.embed(texts)
                
                # Add embeddings to documents
                for doc, embedding in zip(documents_needing_embeddings, embeddings):
                    doc.embedding = embedding
            
            # Index documents based on architecture
            retriever = self._components['retriever']
            
            if self._using_unified_retriever:
                # Phase 4: Direct indexing in unified retriever
                retriever.index_documents(documents)
                logger.debug(f"Indexed documents in unified retriever")
            else:
                # Legacy architecture - store in vector store first
                vector_store = self._components['vector_store']
                vector_store.add(documents)
                
                # Then index in retriever if it supports it
                if hasattr(retriever, 'index_documents'):
                    retriever.index_documents(documents)
                
                logger.debug(f"Indexed documents in legacy vector store + retriever")
            
            logger.info(f"Successfully indexed {len(documents)} documents")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Failed to index documents: {str(e)}")
            raise RuntimeError(f"Document indexing failed: {str(e)}") from e
    
    def process_query(self, query: str, k: int = 5) -> Answer:
        """
        Process a query and return an answer.
        
        This method orchestrates the query processing workflow:
        1. Retrieve relevant documents
        2. Generate answer from query and context
        
        Note: In Phase 1, this directly implements query processing.
        In Phase 3, this will delegate to the QueryProcessor component.
        
        Args:
            query: User query string
            k: Number of documents to retrieve for context
            
        Returns:
            Answer object with generated text, sources, and metadata
            
        Raises:
            ValueError: If query is empty or k is invalid
            RuntimeError: If query processing fails
        """
        if not self._initialized:
            raise RuntimeError("System not initialized")
        
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        if k <= 0:
            raise ValueError("k must be positive")
        
        logger.info(f"Processing query: {query[:100]}...")
        
        try:
            # Retrieve relevant documents using existing component
            retriever = self._components['retriever']
            results = retriever.retrieve(query, k)
            
            if not results:
                logger.warning(f"No relevant documents found for query: {query}")
                return Answer(
                    text="No relevant information found for your query.",
                    sources=[],
                    confidence=0.0,
                    metadata={
                        "query": query,
                        "retrieved_docs": 0,
                        "orchestrator": "PlatformOrchestrator"
                    }
                )
            
            logger.debug(f"Retrieved {len(results)} relevant documents")
            
            # Extract documents from results
            context_docs = [r.document for r in results]
            
            # Generate answer using existing component
            generator = self._components['answer_generator']
            answer = generator.generate(query, context_docs)
            
            # Add orchestrator metadata
            answer.metadata.update({
                "query": query,
                "retrieved_docs": len(results),
                "retrieval_scores": [r.score for r in results],
                "retrieval_methods": [r.retrieval_method for r in results],
                "orchestrator": "PlatformOrchestrator"
            })
            
            logger.info(f"Generated answer with confidence: {answer.confidence}")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to process query: {str(e)}")
            raise RuntimeError(f"Query processing failed: {str(e)}") from e
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health information.
        
        Returns:
            Dictionary with system health metrics and component status
        """
        health = {
            "status": "healthy" if self._initialized else "unhealthy",
            "initialized": self._initialized,
            "architecture": self._determine_system_architecture(),
            "config_path": str(self.config_path),
            "components": {},
            "platform": self.config.global_settings.get("platform", {})
        }
        
        # Phase 4: Enhanced factory and performance monitoring
        try:
            from .component_factory import ComponentFactory
            health["factory_info"] = ComponentFactory.get_available_components()
            health["performance_metrics"] = ComponentFactory.get_performance_metrics()
            health["cache_stats"] = ComponentFactory.get_cache_stats()
        except ImportError:
            pass  # Factory not available
        
        if self._initialized:
            # Get component status
            for name, component in self._components.items():
                component_info = {
                    "type": type(component).__name__,
                    "module": type(component).__module__,
                    "healthy": True,  # Will be updated by health checks
                    "factory_managed": True,  # Phase 3: All components now factory-managed
                    "created_at": getattr(component, '_created_at', None),
                    "last_used": getattr(component, '_last_used', None),
                    "health_checks": {}
                }
                
                # Phase 4: Enhanced component health validation
                component_info["healthy"] = self._validate_component_health(component, component_info["health_checks"])
                
                # Add component-specific health info if available
                if hasattr(component, 'get_stats'):
                    try:
                        component_info["stats"] = component.get_stats()
                    except Exception as e:
                        component_info["healthy"] = False
                        component_info["error"] = str(e)
                elif hasattr(component, 'get_configuration'):
                    component_info["config"] = component.get_configuration()
                elif hasattr(component, 'get_model_info'):
                    component_info["config"] = component.get_model_info()
                
                health["components"][name] = component_info
        
        # Phase 4: Add deployment readiness check
        health["deployment_readiness"] = self._check_deployment_readiness()
        
        return health
    
    def _validate_component_health(self, component: Any, health_checks: Dict[str, Any]) -> bool:
        """
        Validate component health with comprehensive checks.
        
        Args:
            component: Component to validate
            health_checks: Dictionary to store health check results
            
        Returns:
            True if component is healthy, False otherwise
        """
        overall_healthy = True
        
        # Check 1: Required methods exist
        required_methods = {
            "DocumentProcessor": ["process"],
            "Embedder": ["embed", "embedding_dim"],
            "VectorStore": ["add", "search"],
            "Retriever": ["retrieve"],
            "AnswerGenerator": ["generate"]
        }
        
        component_type = type(component).__name__
        if component_type in required_methods:
            missing_methods = []
            for method in required_methods[component_type]:
                if not hasattr(component, method):
                    missing_methods.append(method)
                    overall_healthy = False
            
            health_checks["required_methods"] = {
                "passed": len(missing_methods) == 0,
                "missing": missing_methods
            }
        
        # Check 2: Component-specific health validation
        if hasattr(component, 'health_check'):
            try:
                component_health = component.health_check()
                health_checks["component_specific"] = {
                    "passed": component_health.get("healthy", True),
                    "details": component_health
                }
                if not component_health.get("healthy", True):
                    overall_healthy = False
            except Exception as e:
                health_checks["component_specific"] = {
                    "passed": False,
                    "error": str(e)
                }
                overall_healthy = False
        
        # Check 3: Memory usage validation (if available)
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            health_checks["memory"] = {
                "current_mb": round(memory_mb, 1),
                "within_limits": memory_mb < 2048  # 2GB limit
            }
            if memory_mb > 2048:
                overall_healthy = False
        except ImportError:
            health_checks["memory"] = {"available": False}
        
        # Check 4: Configuration validation
        if hasattr(component, 'get_configuration'):
            try:
                config = component.get_configuration()
                health_checks["configuration"] = {
                    "passed": isinstance(config, dict),
                    "config_size": len(config) if isinstance(config, dict) else 0
                }
            except Exception as e:
                health_checks["configuration"] = {
                    "passed": False,
                    "error": str(e)
                }
                overall_healthy = False
        
        return overall_healthy
    
    def _check_deployment_readiness(self) -> Dict[str, Any]:
        """
        Check system readiness for cloud deployment.
        
        Returns:
            Dictionary with deployment readiness assessment
        """
        readiness = {
            "ready": True,
            "score": 100,
            "checks": {},
            "recommendations": []
        }
        
        # Check 1: All components initialized
        if not self._initialized:
            readiness["ready"] = False
            readiness["score"] -= 50
            readiness["checks"]["initialization"] = {
                "passed": False,
                "message": "System not initialized"
            }
        else:
            readiness["checks"]["initialization"] = {
                "passed": True,
                "message": "System fully initialized"
            }
        
        # Check 2: Memory usage within limits
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > 1024:  # 1GB warning threshold
                readiness["score"] -= 20
                readiness["recommendations"].append("Memory usage high - consider optimization")
            
            readiness["checks"]["memory"] = {
                "passed": memory_mb < 2048,  # 2GB hard limit
                "current_mb": round(memory_mb, 1),
                "limit_mb": 2048
            }
            
            if memory_mb >= 2048:
                readiness["ready"] = False
                readiness["score"] -= 30
                
        except ImportError:
            readiness["checks"]["memory"] = {
                "passed": False,
                "message": "Memory monitoring not available"
            }
            readiness["score"] -= 10
        
        # Check 3: Configuration validation
        try:
            errors = self.validate_configuration()
            if errors:
                readiness["ready"] = False
                readiness["score"] -= 40
                readiness["checks"]["configuration"] = {
                    "passed": False,
                    "errors": errors
                }
            else:
                readiness["checks"]["configuration"] = {
                    "passed": True,
                    "message": "Configuration valid"
                }
        except Exception as e:
            readiness["ready"] = False
            readiness["score"] -= 40
            readiness["checks"]["configuration"] = {
                "passed": False,
                "error": str(e)
            }
        
        # Check 4: Performance metrics
        try:
            from .component_factory import ComponentFactory
            metrics = ComponentFactory.get_performance_metrics()
            cache_stats = ComponentFactory.get_cache_stats()
            
            # Check if we have reasonable performance
            slow_components = []
            for comp_type, stats in metrics.items():
                if stats.get("average_time", 0) > 5.0:  # 5 second threshold
                    slow_components.append(comp_type)
            
            if slow_components:
                readiness["score"] -= 15
                readiness["recommendations"].append(f"Slow components detected: {slow_components}")
            
            readiness["checks"]["performance"] = {
                "passed": len(slow_components) == 0,
                "metrics": {
                    "tracked_components": len(metrics),
                    "cache_usage": f"{cache_stats['cache_size']}/{cache_stats['max_size']}",
                    "slow_components": slow_components
                }
            }
            
        except ImportError:
            readiness["checks"]["performance"] = {
                "passed": False,
                "message": "Performance monitoring not available"
            }
            readiness["score"] -= 10
        
        # Check 5: Environment variables for production
        prod_env_vars = ["RAG_ENV", "RAG_LOG_LEVEL"]
        missing_env_vars = [var for var in prod_env_vars if not os.getenv(var)]
        
        if missing_env_vars:
            readiness["score"] -= 5
            readiness["recommendations"].append(f"Consider setting: {missing_env_vars}")
        
        readiness["checks"]["environment"] = {
            "passed": len(missing_env_vars) == 0,
            "missing_vars": missing_env_vars,
            "current_env": self.config.global_settings.get("platform", "unknown")
        }
        
        # Final score adjustment
        readiness["score"] = max(0, readiness["score"])
        
        # Add readiness level
        if readiness["score"] >= 90:
            readiness["level"] = "production_ready"
        elif readiness["score"] >= 70:
            readiness["level"] = "staging_ready"
        elif readiness["score"] >= 50:
            readiness["level"] = "development_ready"
        else:
            readiness["level"] = "not_ready"
        
        return readiness
    
    def _determine_system_architecture(self) -> str:
        """
        Determine the overall system architecture based on component types.
        
        Returns:
            String describing the current system architecture
        """
        if not self._initialized:
            return "uninitialized"
        
        # Check component types to determine architecture level
        component_types = {}
        for name, component in self._components.items():
            component_types[name] = type(component).__name__
        
        # Determine architecture based on modular component usage
        modular_components = 0
        total_components = 0
        
        # Check each major component for modular architecture
        if 'document_processor' in component_types:
            total_components += 1
            if component_types['document_processor'] == 'ModularDocumentProcessor':
                modular_components += 1
        
        if 'embedder' in component_types:
            total_components += 1
            if component_types['embedder'] == 'ModularEmbedder':
                modular_components += 1
        
        if 'retriever' in component_types:
            total_components += 1
            if component_types['retriever'] in ['ModularUnifiedRetriever']:
                modular_components += 1
        
        if 'answer_generator' in component_types:
            total_components += 1
            if component_types['answer_generator'] == 'AnswerGenerator':  # This is already modular
                modular_components += 1
        
        # Determine architecture level
        if total_components == 0:
            return "no_components"
        
        modular_percentage = modular_components / total_components
        
        if modular_percentage >= 1.0:
            return "modular"  # All components are modular
        elif modular_percentage >= 0.75:
            return "mostly_modular"  # 3/4 or more components are modular
        elif modular_percentage >= 0.5:
            return "hybrid"  # Half of components are modular
        elif self._using_unified_retriever:
            return "unified"  # Using unified retriever but not fully modular
        else:
            return "legacy"  # Legacy architecture
    
    def get_component(self, name: str) -> Optional[Any]:
        """
        Get a specific component for testing/debugging.
        
        Args:
            name: Component name
            
        Returns:
            Component instance or None if not found
        """
        return self._components.get(name)
    
    def clear_index(self) -> None:
        """
        Clear all indexed documents from the vector store.
        
        This method resets the vector store to its initial state.
        """
        if not self._initialized:
            raise RuntimeError("System not initialized")
        
        vector_store = self._components['vector_store']
        vector_store.clear()
        
        # Also clear retriever if it has separate state
        retriever = self._components['retriever']
        if hasattr(retriever, 'clear'):
            retriever.clear()
        
        logger.info("System index cleared")
    
    def reload_config(self) -> None:
        """
        Reload configuration and reinitialize components.
        
        This method allows for dynamic configuration changes without
        creating a new orchestrator instance.
        
        Raises:
            RuntimeError: If reinitialization fails
        """
        logger.info("Reloading system configuration...")
        
        try:
            # Reload configuration
            self.config_manager = ConfigManager(self.config_path)
            self.config = self.config_manager.config
            
            # Clear existing components
            self._components.clear()
            self._initialized = False
            
            # Reinitialize components
            self._initialize_system()
            
            logger.info("System configuration reloaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {str(e)}")
            raise RuntimeError(f"Configuration reload failed: {str(e)}") from e
    
    def validate_configuration(self) -> List[str]:
        """
        Validate the current configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Create configuration dict for factory validation
            config_dict = {
                'document_processor': {
                    'type': self.config.document_processor.type,
                    'config': self.config.document_processor.config
                },
                'embedder': {
                    'type': self.config.embedder.type,
                    'config': self.config.embedder.config
                },
                'retriever': {
                    'type': self.config.retriever.type,
                    'config': self.config.retriever.config
                },
                'answer_generator': {
                    'type': self.config.answer_generator.type,
                    'config': self.config.answer_generator.config
                }
            }
            
            # Add vector_store if present (optional for unified architecture)
            if self.config.vector_store is not None:
                config_dict['vector_store'] = {
                    'type': self.config.vector_store.type,
                    'config': self.config.vector_store.config
                }
            
            # Use factory validation
            errors = ComponentFactory.validate_configuration(config_dict)
            
        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")
        
        return errors
    
    # System Service Access Methods
    
    def check_component_health(self, component_name: str) -> HealthStatus:
        """Check the health of a specific component.
        
        Args:
            component_name: Name of the component to check
            
        Returns:
            HealthStatus object with health information
            
        Raises:
            KeyError: If component not found
        """
        if component_name not in self._components:
            raise KeyError(f"Component '{component_name}' not found")
        
        component = self._components[component_name]
        return self.health_service.check_component_health(component)
    
    def check_component_health(self, component: Any) -> HealthStatus:
        """Check health of a component object.
        
        Args:
            component: Component instance to check
            
        Returns:
            HealthStatus object with health information
        """
        return self.health_service.check_component_health(component)
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get a comprehensive system health summary.
        
        Returns:
            Dictionary with system health information
        """
        return self.health_service.get_system_health_summary()
    
    def report_component_failure(self, component_name: str, error: Exception) -> None:
        """Report a failure for a specific component.
        
        Args:
            component_name: Name of the component that failed
            error: Exception that occurred
            
        Raises:
            KeyError: If component not found
        """
        if component_name not in self._components:
            raise KeyError(f"Component '{component_name}' not found")
        
        component = self._components[component_name]
        self.health_service.report_component_failure(component, error)
    
    def collect_component_metrics(self, component_name: str) -> ComponentMetrics:
        """Collect metrics from a specific component.
        
        Args:
            component_name: Name of the component to collect metrics from
            
        Returns:
            ComponentMetrics object with collected metrics
            
        Raises:
            KeyError: If component not found
        """
        if component_name not in self._components:
            raise KeyError(f"Component '{component_name}' not found")
        
        component = self._components[component_name]
        return self.analytics_service.collect_component_metrics(component)
    
    def get_system_analytics_summary(self) -> Dict[str, Any]:
        """Get system-wide analytics summary.
        
        Returns:
            Dictionary with system analytics
        """
        return self.analytics_service.aggregate_system_metrics()
    
    def track_component_performance(self, component_name: str, metrics: Dict[str, Any]) -> None:
        """Track performance metrics for a specific component.
        
        Args:
            component_name: Name of the component
            metrics: Performance metrics to track
            
        Raises:
            KeyError: If component not found
        """
        if component_name not in self._components:
            raise KeyError(f"Component '{component_name}' not found")
        
        component = self._components[component_name]
        self.analytics_service.track_component_performance(component, metrics)
    
    def track_component_performance(self, component: Any, operation: str, metrics: Dict[str, Any]) -> None:
        """Track performance metrics for a component object.
        
        Args:
            component: Component instance
            operation: Operation type (e.g., 'query_processing', 'embedding_generation')
            metrics: Performance metrics to track
        """
        # Create combined metrics with operation type
        combined_metrics = {
            "operation": operation,
            **metrics
        }
        self.analytics_service.track_component_performance(component, combined_metrics)
    
    def generate_analytics_report(self) -> Dict[str, Any]:
        """Generate a comprehensive analytics report.
        
        Returns:
            Dictionary with analytics report
        """
        return self.analytics_service.generate_analytics_report()
    
    def assign_experiment(self, context: Dict[str, Any]) -> ExperimentAssignment:
        """Assign a user to an experiment.
        
        Args:
            context: Context information for assignment
            
        Returns:
            ExperimentAssignment object
        """
        return self.ab_testing_service.assign_experiment(context)
    
    def track_experiment_outcome(self, experiment_id: str, variant: str, outcome: Dict[str, Any]) -> None:
        """Track the outcome of an experiment.
        
        Args:
            experiment_id: Unique experiment identifier
            variant: Variant that was tested
            outcome: Outcome data
        """
        self.ab_testing_service.track_experiment_outcome(experiment_id, variant, outcome)
    
    def get_experiment_results(self, experiment_name: str) -> List[ExperimentResult]:
        """Get results for an experiment.
        
        Args:
            experiment_name: Name of the experiment
            
        Returns:
            List of experiment results
        """
        return self.ab_testing_service.get_experiment_results(experiment_name)
    
    def configure_experiment(self, experiment_config: Dict[str, Any]) -> None:
        """Configure a new experiment.
        
        Args:
            experiment_config: Configuration for the experiment
        """
        self.ab_testing_service.configure_experiment(experiment_config)
    
    def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """Get status and results for an experiment.
        
        Args:
            experiment_id: Unique experiment identifier
            
        Returns:
            Dictionary with experiment status
        """
        return self.ab_testing_service.get_experiment_status(experiment_id)
    
    def get_all_experiments(self) -> Dict[str, Dict[str, Any]]:
        """Get all configured experiments.
        
        Returns:
            Dictionary with all experiments
        """
        return self.ab_testing_service.get_all_experiments()
    
    def get_component_configuration(self, component_name: str) -> Dict[str, Any]:
        """Get configuration for a component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            Dictionary with component configuration
        """
        return self.configuration_service.get_component_config(component_name)
    
    def update_component_configuration(self, component_name: str, config: Dict[str, Any]) -> None:
        """Update configuration for a component.
        
        Args:
            component_name: Name of the component
            config: New configuration
        """
        self.configuration_service.update_component_config(component_name, config)
    
    def update_component_configuration(self, component: Any, config: Dict[str, Any]) -> None:
        """Update configuration for a component object.
        
        Args:
            component: Component instance
            config: New configuration
        """
        component_name = type(component).__name__
        self.configuration_service.update_component_config(component_name, config)
    
    def get_system_configuration(self) -> Dict[str, Any]:
        """Get the complete system configuration.
        
        Returns:
            Dictionary with system configuration
        """
        return self.configuration_service.get_system_configuration()
    
    def get_feature_flag(self, flag_name: str, default: bool = False) -> bool:
        """Get a feature flag value.
        
        Args:
            flag_name: Name of the feature flag
            default: Default value if flag not found
            
        Returns:
            Boolean value of the feature flag
        """
        return self.configuration_service.get_feature_flag(flag_name, default)
    
    def set_feature_flag(self, flag_name: str, value: bool) -> None:
        """Set a feature flag value.
        
        Args:
            flag_name: Name of the feature flag
            value: Boolean value to set
        """
        self.configuration_service.set_feature_flag(flag_name, value)
    
    def reload_system_configuration(self) -> None:
        """Reload configuration from file."""
        self.configuration_service.reload_configuration()
    
    def register_backend(self, backend_name: str, backend_config: Dict[str, Any]) -> None:
        """Register a new backend.
        
        Args:
            backend_name: Name of the backend
            backend_config: Configuration for the backend
        """
        self.backend_management_service.register_backend(backend_name, backend_config)
    
    def switch_component_backend(self, component_name: str, backend_name: str) -> None:
        """Switch a component to a different backend.
        
        Args:
            component_name: Name of the component to switch
            backend_name: Name of the target backend
            
        Raises:
            KeyError: If component not found
        """
        if component_name not in self._components:
            raise KeyError(f"Component '{component_name}' not found")
        
        component = self._components[component_name]
        self.backend_management_service.switch_component_backend(component, backend_name)
    
    def switch_component_backend(self, component: Any, backend_name: str) -> None:
        """Switch a component object to a different backend.
        
        Args:
            component: Component instance
            backend_name: Name of the target backend
        """
        self.backend_management_service.switch_component_backend(component, backend_name)
    
    def initialize_component_services(self, component: Any) -> None:
        """Initialize platform services for a component.
        
        Args:
            component: Component instance that needs service initialization
        """
        if hasattr(component, 'initialize_services'):
            component.initialize_services(self)
        else:
            logger.warning(f"Component {type(component).__name__} does not support service initialization")
    
    def get_backend_status(self, backend_name: str) -> BackendStatus:
        """Get status information for a backend.
        
        Args:
            backend_name: Name of the backend
            
        Returns:
            BackendStatus object with status information
        """
        return self.backend_management_service.get_backend_status(backend_name)
    
    def migrate_component_data(self, component_name: str, from_backend: str, to_backend: str) -> None:
        """Migrate component data between backends.
        
        Args:
            component_name: Name of the component to migrate
            from_backend: Source backend name
            to_backend: Target backend name
            
        Raises:
            KeyError: If component not found
        """
        if component_name not in self._components:
            raise KeyError(f"Component '{component_name}' not found")
        
        component = self._components[component_name]
        self.backend_management_service.migrate_component_data(component, from_backend, to_backend)
    
    def get_all_backends(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered backends.
        
        Returns:
            Dictionary with all backend information
        """
        return self.backend_management_service.get_all_backends()
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get backend migration history.
        
        Returns:
            List of migration records
        """
        return self.backend_management_service.get_migration_history()
    
    def check_component_backend_health(self, component: Any) -> None:
        """Check backend health for a component and switch if necessary.
        
        Args:
            component: Component to check backend health for
        """
        return self.backend_management_service.check_component_backend_health(component)
    
    def monitor_component_backends(self, components: List[Any]) -> Dict[str, Any]:
        """Monitor backend health for multiple components.
        
        Args:
            components: List of components to monitor
            
        Returns:
            Dictionary with monitoring results
        """
        return self.backend_management_service.monitor_component_backends(components)
    
    def __str__(self) -> str:
        """String representation of the orchestrator."""
        return f"PlatformOrchestrator(config={self.config_path}, initialized={self._initialized})"
    
    def __repr__(self) -> str:
        """Detailed representation of the orchestrator."""
        return (f"PlatformOrchestrator(config_path={self.config_path}, "
                f"initialized={self._initialized}, "
                f"components={list(self._components.keys())})")