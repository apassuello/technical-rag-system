"""Conftest for Epic 5 Phase 2 unit tests."""

import pytest
from unittest.mock import patch, Mock


@pytest.fixture(autouse=True)
def _patch_langchain_internals(request):
    """Patch LangChain internals that fail with Mock LLMs.

    create_react_agent calls llm.bind() which fails with Mock LLMs.
    AgentExecutor is a Pydantic model that rejects Mock agents.

    Provides default mock behavior. Tests that need custom executor
    behavior should use the `mock_executor` fixture.
    """
    executor = Mock()
    executor.invoke = Mock(return_value={
        "output": "mock answer",
        "intermediate_steps": []
    })

    with patch(
        "components.query_processors.agents.react_agent.create_react_agent"
    ) as mock_create, patch(
        "components.query_processors.agents.react_agent.AgentExecutor"
    ) as mock_ae_cls:
        mock_create.return_value = Mock()
        mock_ae_cls.return_value = executor
        # Store on request node for tests that need custom behavior
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
