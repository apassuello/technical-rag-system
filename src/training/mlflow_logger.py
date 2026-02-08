"""
MLflow Logger - Centralized experiment tracking utilities.

This module provides convenient wrappers around MLflow for tracking
experiments, logging metrics, and managing model artifacts in the
RAG portfolio training pipeline.
"""

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional

import mlflow
import mlflow.pytorch
import mlflow.sklearn
import yaml

logger = logging.getLogger(__name__)


class MLflowConfig:
    """MLflow configuration manager."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize MLflow configuration.

        Args:
            config_path: Path to mlflow_config.yaml (optional)
        """
        if config_path is None:
            # Default config location
            config_path = Path(__file__).parent.parent.parent / "config" / "mlflow_config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load MLflow configuration from YAML."""
        if not self.config_path.exists():
            logger.warning(f"MLflow config not found at {self.config_path}, using defaults")
            return self._default_config()

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Environment-specific overrides
        env = os.getenv("ENVIRONMENT", "development")
        if "environments" in config and env in config["environments"]:
            self._merge_config(config, config["environments"][env])

        return config

    def _default_config(self) -> Dict[str, Any]:
        """Default MLflow configuration."""
        return {
            "mlflow": {
                "tracking": {"uri": "file:./mlruns"},
                "artifacts": {"location": "./mlartifacts"},
                "logging": {
                    "log_params": True,
                    "log_metrics": True,
                    "log_models": True,
                    "log_artifacts": True,
                }
            }
        }

    def _merge_config(self, base: Dict, override: Dict) -> None:
        """Merge override config into base config (in-place)."""
        for key, value in override.items():
            if isinstance(value, dict) and key in base:
                self._merge_config(base[key], value)
            else:
                base[key] = value

    @property
    def tracking_uri(self) -> str:
        """Get tracking URI with environment variable expansion."""
        uri = self.config["mlflow"]["tracking"]["uri"]
        # Expand environment variables
        if "${" in uri:
            for env_var in ["MLFLOW_TRACKING_URI"]:
                env_val = os.getenv(env_var)
                if env_val:
                    uri = uri.replace(f"${{{env_var}}}", env_val)
        return uri

    @property
    def artifact_location(self) -> str:
        """Get artifact storage location."""
        return self.config["mlflow"]["artifacts"]["location"]

    def get_experiment_config(self, experiment_key: str) -> Dict[str, Any]:
        """Get configuration for a specific experiment."""
        experiments = self.config["mlflow"].get("experiments", {})
        return experiments.get(experiment_key, {})


class MLflowLogger:
    """
    Convenient wrapper for MLflow tracking.

    Handles experiment setup, metric logging, and model registration
    with sensible defaults and error handling.
    """

    def __init__(self, config: Optional[MLflowConfig] = None):
        """
        Initialize MLflow logger.

        Args:
            config: MLflow configuration (creates default if None)
        """
        self.config = config or MLflowConfig()
        self._setup_mlflow()
        self._active_run = None

    def _setup_mlflow(self) -> None:
        """Configure MLflow tracking."""
        mlflow.set_tracking_uri(self.config.tracking_uri)
        logger.info(f"MLflow tracking URI: {self.config.tracking_uri}")

    @contextmanager
    def start_run(
        self,
        experiment_name: str,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        nested: bool = False
    ):
        """
        Context manager for MLflow runs.

        Args:
            experiment_name: Name of MLflow experiment
            run_name: Optional name for this run
            tags: Optional tags for the run
            nested: Whether this is a nested run

        Yields:
            MLflow run object

        Example:
            >>> with mlflow_logger.start_run("my-experiment", run_name="test-1"):
            >>>     mlflow_logger.log_param("learning_rate", 0.001)
            >>>     mlflow_logger.log_metric("accuracy", 0.95)
        """
        # Set or create experiment
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(experiment_name)
                logger.info(f"Created MLflow experiment: {experiment_name}")
            else:
                experiment_id = experiment.experiment_id
        except Exception as e:
            logger.error(f"Failed to set experiment: {e}")
            raise

        mlflow.set_experiment(experiment_name)

        # Start run
        try:
            run = mlflow.start_run(run_name=run_name, nested=nested)
            self._active_run = run

            # Log tags
            if tags:
                for key, value in tags.items():
                    mlflow.set_tag(key, value)

            logger.info(f"Started MLflow run: {run.info.run_name} (ID: {run.info.run_id})")

            yield run

        finally:
            # End run
            if self._active_run:
                mlflow.end_run()
                self._active_run = None
                logger.info("Ended MLflow run")

    def log_params(self, params: Dict[str, Any]) -> None:
        """
        Log multiple parameters.

        Args:
            params: Dictionary of parameter name -> value
        """
        if not self.config.config["mlflow"]["logging"]["log_params"]:
            return

        try:
            for key, value in params.items():
                mlflow.log_param(key, value)
        except Exception as e:
            logger.warning(f"Failed to log params: {e}")

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """
        Log multiple metrics.

        Args:
            metrics: Dictionary of metric name -> value
            step: Optional step number (for time series)
        """
        if not self.config.config["mlflow"]["logging"]["log_metrics"]:
            return

        try:
            for key, value in metrics.items():
                mlflow.log_metric(key, value, step=step)
        except Exception as e:
            logger.warning(f"Failed to log metrics: {e}")

    def log_model(
        self,
        model: Any,
        artifact_path: str,
        registered_model_name: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log model to MLflow.

        Args:
            model: PyTorch or sklearn model
            artifact_path: Path within run's artifact directory
            registered_model_name: Name for model registry (optional)
            **kwargs: Additional arguments for log_model
        """
        if not self.config.config["mlflow"]["logging"]["log_models"]:
            logger.info("Model logging disabled, skipping")
            return

        try:
            # Detect model type and use appropriate logger
            model_type = type(model).__module__

            if "torch" in model_type:
                mlflow.pytorch.log_model(
                    model,
                    artifact_path,
                    registered_model_name=registered_model_name,
                    **kwargs
                )
            elif "sklearn" in model_type:
                mlflow.sklearn.log_model(
                    model,
                    artifact_path,
                    registered_model_name=registered_model_name,
                    **kwargs
                )
            else:
                logger.warning(f"Unknown model type: {model_type}, using generic logging")
                mlflow.pyfunc.log_model(
                    artifact_path,
                    python_model=model,
                    registered_model_name=registered_model_name,
                    **kwargs
                )

            logger.info(f"Logged model to {artifact_path}")
            if registered_model_name:
                logger.info(f"Registered model as: {registered_model_name}")

        except Exception as e:
            logger.error(f"Failed to log model: {e}")
            raise

    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None) -> None:
        """
        Log file or directory as artifact.

        Args:
            local_path: Local file/directory path
            artifact_path: Optional path within artifact directory
        """
        if not self.config.config["mlflow"]["logging"]["log_artifacts"]:
            return

        try:
            if Path(local_path).is_dir():
                mlflow.log_artifacts(local_path, artifact_path)
            else:
                mlflow.log_artifact(local_path, artifact_path)
            logger.info(f"Logged artifact: {local_path}")
        except Exception as e:
            logger.warning(f"Failed to log artifact: {e}")

    def log_dict(self, dictionary: Dict[str, Any], filename: str) -> None:
        """
        Log dictionary as JSON artifact.

        Args:
            dictionary: Dictionary to log
            filename: Filename for the JSON file
        """
        try:
            mlflow.log_dict(dictionary, filename)
            logger.info(f"Logged dictionary as: {filename}")
        except Exception as e:
            logger.warning(f"Failed to log dictionary: {e}")


# Global logger instance (can be imported and reused)
_default_logger: Optional[MLflowLogger] = None


def get_mlflow_logger() -> MLflowLogger:
    """
    Get or create global MLflow logger instance.

    Returns:
        MLflowLogger instance

    Example:
        >>> from src.training.mlflow_logger import get_mlflow_logger
        >>> logger = get_mlflow_logger()
        >>> with logger.start_run("my-experiment"):
        >>>     logger.log_params({"lr": 0.001})
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = MLflowLogger()
    return _default_logger
