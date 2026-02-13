"""
Conftest for unit tests (tests/unit/).

Consolidated from:
- tests/unit/test_platform_orchestrator_suite/conftest.py
- tests/epic5/phase2/unit/conftest.py (autouse → named fixture)
- tests/epic1/phase2/conftest.py (selected fixtures)
- tests/epic1/ml_infrastructure/conftest.py (sys.path for fixtures/)
"""

import os
import sys
import time
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from src.core.interfaces import (
    Answer,
    ComponentMetrics,
    Document,
    HealthStatus,
    RetrievalResult,
)
from src.core.platform_orchestrator import (
    ComponentHealthServiceImpl,
    ConfigurationServiceImpl,
    PlatformOrchestrator,
    SystemAnalyticsServiceImpl,
)

# Add fixtures/ directory to sys.path so ML infrastructure tests can
# ``from fixtures.mock_memory import ...`` etc.
_FIXTURES_DIR = Path(__file__).parent / "fixtures"
if str(_FIXTURES_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_FIXTURES_DIR.parent))


# ---------------------------------------------------------------------------
# Epic 1 Phase 2 test data (previously in tests/epic1/phase2/__init__.py)
# ---------------------------------------------------------------------------
from .epic1_phase2_data import (
    COST_VALIDATION,
    EXPECTED_ROUTING,
    PERFORMANCE_TARGETS,
    REQUIRED_ENV_VARS,
    TEST_DATA,
)


# ---------------------------------------------------------------------------
# Platform Orchestrator Suite fixtures
# (from tests/unit/test_platform_orchestrator_suite/conftest.py)
# ---------------------------------------------------------------------------


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
            "config": {"chunk_size": 1000, "overlap": 100},
        },
        "embedder": {
            "type": "sentence_transformer",
            "config": {"model": "test-model", "device": "cpu"},
        },
        "retriever": {
            "type": "modular_unified",
            "config": {"dense_weight": 0.7, "sparse_weight": 0.3},
        },
        "answer_generator": {
            "type": "adaptive",
            "config": {"model": "test-generator", "temperature": 0.1},
        },
        "global_settings": {
            "platform": {"name": "test-platform", "environment": "test"},
            "logging": {"level": "INFO"},
        },
    }
    config_path = Path(temp_config_dir) / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path


@pytest.fixture
def invalid_config_file(temp_config_dir):
    """Create invalid configuration file for error testing."""
    config = {"document_processor": {"type": "nonexistent_type"}}
    config_path = Path(temp_config_dir) / "invalid_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path


@pytest.fixture
def mock_component_factory():
    """Mock ComponentFactory with all required components."""
    with patch("src.core.platform_orchestrator.ComponentFactory") as mock_factory:
        mock_processor = Mock()
        mock_processor.name = "document_processor"
        mock_processor.process.return_value = [
            Document(content="Test content", metadata={"id": "1", "source": "test.pdf"})
        ]
        mock_processor.health_check.return_value = {"healthy": True}
        mock_processor.get_configuration.return_value = {"chunk_size": 1000}

        mock_embedder = Mock()
        mock_embedder.name = "embedder"
        mock_embedder.embed.return_value = [[0.1] * 384]
        mock_embedder.health_check.return_value = {"healthy": True}
        mock_embedder.get_configuration.return_value = {"model": "test-model"}

        mock_retriever = Mock()
        mock_retriever.name = "retriever"
        mock_retriever.retrieve.return_value = [
            RetrievalResult(
                document=Document(content="Retrieved content", metadata={"id": "2"}),
                score=0.9,
                retrieval_method="hybrid",
            )
        ]
        mock_retriever.index_documents.return_value = None
        mock_retriever.clear.return_value = None
        mock_retriever.health_check.return_value = {"healthy": True}
        mock_retriever.get_configuration.return_value = {"dense_weight": 0.7}

        mock_generator = Mock()
        mock_generator.name = "answer_generator"
        mock_generator.generate.return_value = Answer(
            text="Test answer",
            sources=[],
            confidence=0.8,
            metadata={"model": "test-generator"},
        )
        mock_generator.health_check.return_value = {"healthy": True}
        mock_generator.get_configuration.return_value = {"model": "test-generator"}

        mock_query_processor = MagicMock()
        mock_query_processor.name = "query_processor"
        mock_query_processor.health_check.return_value = {"healthy": True}
        mock_query_processor.get_configuration.return_value = {"type": "modular"}

        mock_factory.create_processor.return_value = mock_processor
        mock_factory.create_embedder.return_value = mock_embedder
        mock_factory.create_retriever.return_value = mock_retriever
        mock_factory.create_generator.return_value = mock_generator
        mock_factory.create_query_processor.return_value = mock_query_processor
        mock_factory.validate_configuration.return_value = []

        mock_factory.mock_processor = mock_processor
        mock_factory.mock_embedder = mock_embedder
        mock_factory.mock_retriever = mock_retriever
        mock_factory.mock_generator = mock_generator
        mock_factory.mock_query_processor = mock_query_processor

        yield mock_factory


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        Document(
            content="This is the first test document with technical content.",
            metadata={"id": "doc1", "source": "test1.pdf", "page": 1},
        ),
        Document(
            content="This is the second test document about machine learning.",
            metadata={"id": "doc2", "source": "test2.pdf", "page": 1},
        ),
        Document(
            content="This is the third test document discussing algorithms.",
            metadata={"id": "doc3", "source": "test3.pdf", "page": 2},
        ),
    ]


@pytest.fixture
def sample_retrieval_results(sample_documents):
    """Create sample retrieval results for testing."""
    return [
        RetrievalResult(document=sample_documents[0], score=0.95, retrieval_method="dense"),
        RetrievalResult(document=sample_documents[1], score=0.87, retrieval_method="hybrid"),
        RetrievalResult(document=sample_documents[2], score=0.76, retrieval_method="sparse"),
    ]


@pytest.fixture
def health_service():
    """Create ComponentHealthServiceImpl instance with proper cleanup."""
    service = ComponentHealthServiceImpl()
    yield service
    service.monitored_components.clear()
    service.health_history.clear()
    service.failure_counts.clear()
    service.last_health_checks.clear()


@pytest.fixture
def analytics_service():
    """Create SystemAnalyticsServiceImpl instance with proper cleanup."""
    service = SystemAnalyticsServiceImpl()
    yield service
    service.component_metrics.clear()
    service.system_metrics_history.clear()
    service.performance_tracking.clear()
    service.performance_history.clear()
    service.query_analytics.clear()


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
        return {"healthy": self.healthy, "component": self.name, "last_check": time.time()}

    def get_configuration(self) -> Dict[str, Any]:
        return self._config

    def update_configuration(self, config: Dict[str, Any]) -> None:
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
    assert hasattr(metrics, "response_time")
    assert hasattr(metrics, "success_rate")
    assert hasattr(metrics, "error_count")


def create_performance_metrics(
    response_time: float = 0.1,
    success_rate: float = 1.0,
    error_count: int = 0,
    **kwargs,
) -> Dict[str, Any]:
    """Create test performance metrics."""
    return {
        "response_time": response_time,
        "success_rate": success_rate,
        "error_count": error_count,
        "timestamp": time.time(),
        **kwargs,
    }


# ---------------------------------------------------------------------------
# Epic 5 LangChain fixtures
# (from tests/epic5/phase2/unit/conftest.py — converted from autouse)
# ---------------------------------------------------------------------------


@pytest.fixture
def patch_langchain_internals(request):
    """Patch LangChain internals that fail with Mock LLMs.

    NOT autouse — only requested by agent tests that need it
    (ut_react_agent, ut_execution_planner, ut_plan_executor, ut_query_decomposer).
    """
    executor = Mock()
    executor.invoke = Mock(return_value={"output": "mock answer", "intermediate_steps": []})

    with patch(
        "components.query_processors.agents.react_agent.create_react_agent"
    ) as mock_create, patch(
        "components.query_processors.agents.react_agent.AgentExecutor"
    ) as mock_ae_cls:
        mock_create.return_value = Mock()
        mock_ae_cls.return_value = executor
        request.node._mock_executor = executor
        request.node._mock_executor_class = mock_ae_cls
        yield


@pytest.fixture
def mock_executor(request):
    """Access the mock executor for custom behavior setup."""
    return request.node._mock_executor


@pytest.fixture
def mock_executor_class(request):
    """Access the mock AgentExecutor class for custom behavior setup."""
    return request.node._mock_executor_class


# ---------------------------------------------------------------------------
# Epic 1 Phase 2 fixtures
# (from tests/epic1/phase2/conftest.py — selected fixtures)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_environment():
    """Set up test environment with required variables."""
    vars_set = []
    for env_var in REQUIRED_ENV_VARS:
        if env_var not in os.environ:
            os.environ[env_var] = f"test-{env_var.lower().replace('_', '-')}-key"
            vars_set.append(env_var)
    for var in ["EPIC1_TEST_MODE", "EPIC1_USE_MOCKS", "EPIC1_USE_MOCK_APIS"]:
        os.environ[var] = "true"
        vars_set.append(var)
    yield
    for var in vars_set:
        os.environ.pop(var, None)


@pytest.fixture
def test_queries():
    """Provide categorized test queries."""
    return TEST_DATA


@pytest.fixture
def expected_routing():
    """Provide expected routing decisions for validation."""
    return EXPECTED_ROUTING


@pytest.fixture
def cost_validation_data():
    """Provide cost validation data."""
    return COST_VALIDATION


@pytest.fixture
def performance_targets():
    """Provide performance targets for validation."""
    return PERFORMANCE_TARGETS


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="This is a test response from OpenAI."))]
    mock_response.usage = MagicMock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_mistral_response():
    """Mock Mistral API response for testing."""
    return {
        "choices": [{"message": {"content": "This is a test response from Mistral."}}],
        "usage": {"prompt_tokens": 80, "completion_tokens": 40, "total_tokens": 120},
    }


@pytest.fixture
def model_options():
    """Provide model options for testing routing strategies."""
    from src.components.generators.routing.routing_strategies import ModelOption

    return {
        "simple": [
            ModelOption("ollama", "llama3.2:3b", Decimal("0.000"), 1.5, 0.75),
            ModelOption("openai", "gpt-3.5-turbo", Decimal("0.002"), 0.8, 0.90),
        ],
        "medium": [
            ModelOption("mistral", "mistral-small", Decimal("0.010"), 1.2, 0.85),
            ModelOption("openai", "gpt-4-turbo", Decimal("0.050"), 2.0, 0.95),
        ],
        "complex": [
            ModelOption("openai", "gpt-3.5-turbo", Decimal("0.020"), 1.5, 0.85),
            ModelOption("openai", "gpt-4-turbo", Decimal("0.100"), 3.0, 0.98),
        ],
    }


@pytest.fixture
def epic1_config():
    """Provide Epic1 multi-model configuration."""
    return {
        "query_analyzer": {"type": "epic1"},
        "routing": {"strategy": "balanced", "cost_weight": 0.4, "quality_weight": 0.6},
        "model_mappings": {
            "simple": {"provider": "ollama", "model": "llama3.2:3b"},
            "medium": {"provider": "mistral", "model": "mistral-small"},
            "complex": {"provider": "openai", "model": "gpt-4-turbo"},
        },
        "cost_tracking": {"enabled": True, "daily_budget": 10.00, "warning_threshold": 0.80},
    }


@pytest.fixture
def temp_export_file():
    """Provide temporary file for export testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name
    yield temp_path
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def sample_usage_records():
    """Provide sample usage records for cost tracking tests."""
    from datetime import datetime, timedelta

    base_time = datetime.now()
    return [
        {
            "provider": "openai",
            "model": "gpt-4-turbo",
            "input_tokens": 200,
            "output_tokens": 100,
            "cost_usd": Decimal("0.005000"),
            "query_complexity": "complex",
            "timestamp": base_time - timedelta(hours=1),
        },
        {
            "provider": "mistral",
            "model": "mistral-small",
            "input_tokens": 150,
            "output_tokens": 75,
            "cost_usd": Decimal("0.000750"),
            "query_complexity": "medium",
            "timestamp": base_time - timedelta(minutes=30),
        },
        {
            "provider": "ollama",
            "model": "llama3.2:3b",
            "input_tokens": 100,
            "output_tokens": 50,
            "cost_usd": Decimal("0.000000"),
            "query_complexity": "simple",
            "timestamp": base_time,
        },
    ]
