"""
Test fixtures and utilities for PlatformOrchestrator testing.

Provides common test setup, mock configurations, and utility functions
for comprehensive PlatformOrchestrator test coverage.
"""

import pytest
import tempfile
import yaml
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List

from src.core.interfaces import Document, Answer, RetrievalResult, HealthStatus, ComponentMetrics
from src.core.platform_orchestrator import (
    PlatformOrchestrator,
    ComponentHealthServiceImpl,
    SystemAnalyticsServiceImpl,
    ABTestingServiceImpl,
    ConfigurationServiceImpl,
    BackendManagementServiceImpl
)


@pytest.fixture
def temp_config_dir():
    """Create temporary directory for test configurations."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def valid_config_file(temp_config_dir):
    """Create valid configuration file for testing."""
    config = {
        "document_processor": {
            "type": "hybrid_pdf",
            "config": {"chunk_size": 1000, "overlap": 100}
        },
        "embedder": {
            "type": "sentence_transformer",
            "config": {"model": "test-model", "device": "cpu"}
        },
        "retriever": {
            "type": "modular_unified",
            "config": {"dense_weight": 0.7, "sparse_weight": 0.3}
        },
        "answer_generator": {
            "type": "adaptive",
            "config": {"model": "test-generator", "temperature": 0.1}
        },
        "global_settings": {
            "platform": {
                "name": "test-platform",
                "environment": "test"
            },
            "logging": {
                "level": "INFO"
            }
        }
    }
    
    config_path = Path(temp_config_dir) / "test_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    return config_path


@pytest.fixture
def invalid_config_file(temp_config_dir):
    """Create invalid configuration file for error testing."""
    config = {
        "document_processor": {
            "type": "nonexistent_type"
            # Missing config section
        }
    }
    
    config_path = Path(temp_config_dir) / "invalid_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    return config_path


@pytest.fixture
def mock_component_factory():
    """Mock ComponentFactory with all required components."""
    with patch('src.core.platform_orchestrator.ComponentFactory') as mock_factory:
        # Create mock components
        mock_processor = Mock()
        mock_processor.process.return_value = [
            Document(content="Test content", metadata={"id": "1", "source": "test.pdf"})
        ]
        mock_processor.health_check.return_value = {"healthy": True}
        mock_processor.get_configuration.return_value = {"chunk_size": 1000}
        
        mock_embedder = Mock()
        mock_embedder.embed.return_value = [[0.1] * 384]
        mock_embedder.health_check.return_value = {"healthy": True}
        mock_embedder.get_configuration.return_value = {"model": "test-model"}
        
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            RetrievalResult(
                document=Document(content="Retrieved content", metadata={"id": "2"}),
                score=0.9,
                retrieval_method="hybrid"
            )
        ]
        mock_retriever.index_documents.return_value = None
        mock_retriever.clear.return_value = None
        mock_retriever.health_check.return_value = {"healthy": True}
        mock_retriever.get_configuration.return_value = {"dense_weight": 0.7}
        
        mock_generator = Mock()
        mock_generator.generate.return_value = Answer(
            text="Test answer",
            sources=[],
            confidence=0.8,
            metadata={"model": "test-generator"}
        )
        mock_generator.health_check.return_value = {"healthy": True}
        mock_generator.get_configuration.return_value = {"model": "test-generator"}
        
        # Configure factory to return mocks
        mock_factory.create_processor.return_value = mock_processor
        mock_factory.create_embedder.return_value = mock_embedder
        mock_factory.create_retriever.return_value = mock_retriever
        mock_factory.create_generator.return_value = mock_generator
        
        # Store references for assertions
        mock_factory.mock_processor = mock_processor
        mock_factory.mock_embedder = mock_embedder
        mock_factory.mock_retriever = mock_retriever
        mock_factory.mock_generator = mock_generator
        
        yield mock_factory


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        Document(
            content="This is the first test document with technical content.",
            metadata={"id": "doc1", "source": "test1.pdf", "page": 1}
        ),
        Document(
            content="This is the second test document about machine learning.",
            metadata={"id": "doc2", "source": "test2.pdf", "page": 1}
        ),
        Document(
            content="This is the third test document discussing algorithms.",
            metadata={"id": "doc3", "source": "test3.pdf", "page": 2}
        )
    ]


@pytest.fixture
def sample_retrieval_results(sample_documents):
    """Create sample retrieval results for testing."""
    return [
        RetrievalResult(
            document=sample_documents[0],
            score=0.95,
            retrieval_method="dense"
        ),
        RetrievalResult(
            document=sample_documents[1],
            score=0.87,
            retrieval_method="hybrid"
        ),
        RetrievalResult(
            document=sample_documents[2],
            score=0.76,
            retrieval_method="sparse"
        )
    ]


@pytest.fixture
def health_service():
    """Create ComponentHealthServiceImpl instance."""
    return ComponentHealthServiceImpl()


@pytest.fixture
def analytics_service():
    """Create SystemAnalyticsServiceImpl instance."""
    return SystemAnalyticsServiceImpl()


@pytest.fixture
def ab_testing_service():
    """Create ABTestingServiceImpl instance."""
    return ABTestingServiceImpl()


@pytest.fixture
def backend_management_service():
    """Create BackendManagementServiceImpl instance."""
    return BackendManagementServiceImpl()


@pytest.fixture
def mock_config_manager():
    """Mock ConfigManager for configuration service testing."""
    mock_manager = Mock()
    mock_manager.config.document_processor.type = "hybrid_pdf"
    mock_manager.config.document_processor.config = {"chunk_size": 1000, "overlap": 100}
    mock_manager.config.embedder.type = "sentence_transformer"
    mock_manager.config.embedder.config = {"model": "test-model"}
    mock_manager.config.retriever.type = "unified"
    mock_manager.config.retriever.config = {"dense_weight": 0.7}
    mock_manager.config.answer_generator.type = "ollama"
    mock_manager.config.answer_generator.config = {"model": "test-generator"}
    mock_manager.config.global_settings = {"environment": "development"}
    mock_manager.reload.return_value = None
    return mock_manager


@pytest.fixture
def configuration_service(mock_config_manager):
    """Create ConfigurationServiceImpl instance."""
    return ConfigurationServiceImpl(mock_config_manager)


class MockComponent:
    """Mock component for testing service implementations."""
    
    def __init__(self, name: str = "MockComponent", healthy: bool = True):
        self.name = name
        self.healthy = healthy
        self._config = {"test_param": "test_value"}
        
    def health_check(self) -> Dict[str, Any]:
        """Mock health check."""
        return {
            "healthy": self.healthy,
            "component": self.name,
            "last_check": time.time()
        }
        
    def get_configuration(self) -> Dict[str, Any]:
        """Mock configuration getter."""
        return self._config
        
    def update_configuration(self, config: Dict[str, Any]) -> None:
        """Mock configuration setter."""
        self._config.update(config)


@pytest.fixture
def mock_component():
    """Create mock component for testing."""
    return MockComponent()


@pytest.fixture
def failing_mock_component():
    """Create failing mock component for error testing."""
    return MockComponent("FailingComponent", healthy=False)


def create_test_file(temp_dir: Path, filename: str, content: str = "Test content") -> Path:
    """Utility function to create test files."""
    file_path = temp_dir / filename
    file_path.write_text(content)
    return file_path


def assert_health_status(health_status: HealthStatus, expected_healthy: bool = True):
    """Utility to assert health status properties."""
    assert isinstance(health_status, HealthStatus)
    assert health_status.is_healthy == expected_healthy
    assert isinstance(health_status.last_check, (int, float))
    assert isinstance(health_status.issues, list)
    assert isinstance(health_status.metrics, dict)
    assert isinstance(health_status.component_name, str)


def assert_component_metrics(metrics: ComponentMetrics):
    """Utility to assert component metrics properties."""
    assert isinstance(metrics, ComponentMetrics)
    assert hasattr(metrics, 'response_time')
    assert hasattr(metrics, 'success_rate')
    assert hasattr(metrics, 'error_count')


def create_performance_metrics(
    response_time: float = 0.1,
    success_rate: float = 1.0,
    error_count: int = 0,
    **kwargs
) -> Dict[str, Any]:
    """Create test performance metrics."""
    return {
        "response_time": response_time,
        "success_rate": success_rate,
        "error_count": error_count,
        "timestamp": time.time(),
        **kwargs
    }