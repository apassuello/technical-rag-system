"""Integration tests for orchestrator → IntelligentQueryProcessor wiring.

Tests that PlatformOrchestrator._initialize_intelligent_processor correctly
assembles the full agent stack (tools, memory, LLM, ReActAgent, QueryAnalyzer)
and passes them to the factory. Uses mocked LLM to avoid API key requirements.

These tests validate Gap 3 from the Epic 5 audit:
  "PlatformOrchestrator doesn't support 'intelligent' processor"
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

pytestmark = [pytest.mark.integration]

from src.core.platform_orchestrator import PlatformOrchestrator
from src.components.query_processors.intelligent_query_processor import (
    IntelligentQueryProcessor,
)
from src.components.query_processors.agents.react_agent import ReActAgent
from src.components.query_processors.agents.models import (
    AgentConfig,
    ProcessorConfig,
)
from src.components.query_processors.agents.planning.query_analyzer import QueryAnalyzer
from src.core.interfaces import Answer


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def agent_config_dict():
    """Config dict matching config/epic5_agents.yaml structure."""
    return {
        "agent": {
            "type": "react",
            "enabled": True,
            "llm": {
                "provider": "openai",
                "model": "gpt-4-turbo",
                "temperature": 0.7,
                "max_tokens": 2048,
            },
            "executor": {
                "max_iterations": 10,
                "max_execution_time": 300,
                "early_stopping_method": "force",
                "verbose": False,
            },
            "use_technical_prompts": True,
            "include_few_shot": True,
            "agent_role": "technical_docs",
        },
        "tools": ["calculator", "code_analyzer", "document_search"],
        "memory": {
            "conversation": {"max_messages": 50},
            "working": {},
        },
        "processor": {
            "use_agent_by_default": False,
            "complexity_threshold": 0.7,
            "max_agent_cost": 0.10,
            "enable_planning": False,
            "enable_parallel_execution": False,
        },
    }


@pytest.fixture
def mock_orchestrator():
    """Create a PlatformOrchestrator with mocked components (no config file)."""
    with patch.object(PlatformOrchestrator, "__init__", lambda self, *a, **kw: None):
        orch = PlatformOrchestrator.__new__(PlatformOrchestrator)
        orch._components = {
            "retriever": Mock(),
            "answer_generator": Mock(),
        }
        return orch


# =============================================================================
# Tests
# =============================================================================


class TestOrchestratorAgentAssembly:
    """Test that the orchestrator correctly assembles the agent stack."""

    def test_initialize_intelligent_processor_creates_correct_type(
        self, mock_orchestrator, agent_config_dict
    ):
        """The method should return an IntelligentQueryProcessor."""
        mock_llm = MagicMock()

        with patch.object(
            PlatformOrchestrator,
            "_create_agent_llm",
            return_value=mock_llm,
        ), patch(
            "components.query_processors.agents.react_agent.create_react_agent"
        ) as mock_create, patch(
            "components.query_processors.agents.react_agent.AgentExecutor"
        ) as mock_ae_cls:
            mock_create.return_value = Mock()
            mock_ae_cls.return_value = Mock(
                invoke=Mock(
                    return_value={"output": "mock", "intermediate_steps": []}
                )
            )

            processor = mock_orchestrator._initialize_intelligent_processor(
                agent_config_dict
            )

        assert isinstance(processor, IntelligentQueryProcessor)

    def test_tools_created_from_config(
        self, mock_orchestrator, agent_config_dict
    ):
        """All configured tools should be created."""
        mock_llm = MagicMock()

        with patch.object(
            PlatformOrchestrator,
            "_create_agent_llm",
            return_value=mock_llm,
        ), patch(
            "components.query_processors.agents.react_agent.create_react_agent"
        ) as mock_create, patch(
            "components.query_processors.agents.react_agent.AgentExecutor"
        ) as mock_ae_cls, patch(
            "src.core.component_factory.ComponentFactory.create_tool"
        ) as mock_create_tool:
            mock_create.return_value = Mock()
            mock_ae_cls.return_value = Mock(
                invoke=Mock(
                    return_value={"output": "mock", "intermediate_steps": []}
                )
            )
            mock_create_tool.return_value = Mock()

            mock_orchestrator._initialize_intelligent_processor(agent_config_dict)

            # Verify all 3 tools were created
            assert mock_create_tool.call_count == 3
            tool_names = [
                call.args[0] for call in mock_create_tool.call_args_list
            ]
            assert "calculator" in tool_names
            assert "code_analyzer" in tool_names
            assert "document_search" in tool_names

    def test_document_search_gets_retriever_injected(
        self, mock_orchestrator, agent_config_dict
    ):
        """DocumentSearchTool should have set_retriever called with the retriever."""
        mock_llm = MagicMock()
        mock_doc_search_tool = Mock()
        mock_doc_search_tool.set_retriever = Mock()

        def create_tool_side_effect(name, **kw):
            if name == "document_search":
                return mock_doc_search_tool
            return Mock()

        with patch.object(
            PlatformOrchestrator,
            "_create_agent_llm",
            return_value=mock_llm,
        ), patch(
            "components.query_processors.agents.react_agent.create_react_agent"
        ) as mock_create, patch(
            "components.query_processors.agents.react_agent.AgentExecutor"
        ) as mock_ae_cls, patch(
            "src.core.component_factory.ComponentFactory.create_tool",
            side_effect=create_tool_side_effect,
        ):
            mock_create.return_value = Mock()
            mock_ae_cls.return_value = Mock(
                invoke=Mock(
                    return_value={"output": "mock", "intermediate_steps": []}
                )
            )

            mock_orchestrator._initialize_intelligent_processor(agent_config_dict)

            mock_doc_search_tool.set_retriever.assert_called_once_with(
                mock_orchestrator._components["retriever"]
            )

    def test_processor_config_from_yaml(
        self, mock_orchestrator, agent_config_dict
    ):
        """ProcessorConfig values should match the config dict."""
        mock_llm = MagicMock()

        with patch.object(
            PlatformOrchestrator,
            "_create_agent_llm",
            return_value=mock_llm,
        ), patch(
            "components.query_processors.agents.react_agent.create_react_agent"
        ) as mock_create, patch(
            "components.query_processors.agents.react_agent.AgentExecutor"
        ) as mock_ae_cls:
            mock_create.return_value = Mock()
            mock_ae_cls.return_value = Mock(
                invoke=Mock(
                    return_value={"output": "mock", "intermediate_steps": []}
                )
            )

            processor = mock_orchestrator._initialize_intelligent_processor(
                agent_config_dict
            )

        assert processor._config.complexity_threshold == 0.7
        assert processor._config.use_agent_by_default is False
        assert processor._config.max_agent_cost == 0.10

    def test_rag_path_with_mocked_components(
        self, mock_orchestrator, agent_config_dict
    ):
        """Simple query should route through RAG path (complexity < threshold)."""
        mock_llm = MagicMock()

        # Set up retriever to return mock documents
        mock_doc = Mock()
        mock_doc.content = "RISC-V is an open standard ISA."
        mock_doc.metadata = {"source": "test"}
        mock_orchestrator._components["retriever"].retrieve = Mock(
            return_value=[mock_doc]
        )

        # Set up generator to return an Answer
        mock_answer = Answer(
            text="RISC-V is an open standard ISA.",
            confidence=0.9,
            sources=[mock_doc],
            metadata={"source": "rag_pipeline"},
        )
        mock_orchestrator._components["answer_generator"].generate = Mock(
            return_value=mock_answer
        )

        with patch.object(
            PlatformOrchestrator,
            "_create_agent_llm",
            return_value=mock_llm,
        ), patch(
            "components.query_processors.agents.react_agent.create_react_agent"
        ) as mock_create, patch(
            "components.query_processors.agents.react_agent.AgentExecutor"
        ) as mock_ae_cls:
            mock_create.return_value = Mock()
            mock_ae_cls.return_value = Mock(
                invoke=Mock(
                    return_value={"output": "mock", "intermediate_steps": []}
                )
            )

            # Set high threshold so simple queries go to RAG
            agent_config_dict["processor"]["complexity_threshold"] = 0.99
            processor = mock_orchestrator._initialize_intelligent_processor(
                agent_config_dict
            )

        result = processor.process("What is RISC-V?")
        assert isinstance(result, Answer)
        assert "RISC-V" in result.text


class TestCreateAgentLLM:
    """Test LLM creation from config."""

    def test_openai_provider(self):
        """OpenAI provider should create ChatOpenAI."""
        config = AgentConfig(
            llm_provider="openai",
            llm_model="gpt-4-turbo",
        )
        with patch("src.core.platform_orchestrator.ChatOpenAI", create=True) as mock_cls:
            # Simulate langchain_openai import
            with patch.dict(
                "sys.modules",
                {"langchain_openai": MagicMock(ChatOpenAI=mock_cls)},
            ):
                llm = PlatformOrchestrator._create_agent_llm(config)
                mock_cls.assert_called_once()

    def test_unsupported_provider_raises(self):
        """Invalid provider should raise RuntimeError."""
        # Can't create AgentConfig with invalid provider (validation),
        # so test the method directly with a mock config
        config = Mock()
        config.llm_provider = "invalid"
        with pytest.raises(RuntimeError, match="Cannot create LLM"):
            PlatformOrchestrator._create_agent_llm(config)
