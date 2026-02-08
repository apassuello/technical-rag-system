"""
Agent framework for intelligent query processing.

This package provides the agent infrastructure for Phase 2, including:
- Base agent and memory interfaces
- Data models for agent results and reasoning
- Memory implementations
- Agent implementations (ReAct, etc.)

Usage:
    >>> from src.components.query_processors.agents import (
    ...     BaseAgent,
    ...     BaseMemory,
    ...     AgentResult,
    ...     ConversationMemory,
    ...     WorkingMemory
    ... )
    >>>
    >>> # Create memory
    >>> memory = ConversationMemory()
    >>>
    >>> # Create agent (concrete implementation)
    >>> # agent = ReActAgent(llm, tools, memory, config)
    >>>
    >>> # Process query
    >>> # result = agent.process("What is machine learning?")
"""

# Base classes
from .base_agent import (
    AgentError,
    AgentIterationLimitError,
    AgentTimeoutError,
    BaseAgent,
)
from .base_memory import BaseMemory, MemoryCapacityError, MemoryError
from .langchain_adapter import PhaseOneToolAdapter, convert_tools_to_langchain

# Memory implementations
from .memory import ConversationMemory, WorkingMemory

# Data models
from .models import (
    # Configuration
    AgentConfig,
    # Results
    AgentResult,
    ExecutionPlan,
    ExecutionResult,
    ExecutionStrategy,
    # Memory
    Message,
    ProcessorConfig,
    # Planning
    QueryAnalysis,
    QueryType,
    ReasoningStep,
    # Enums
    StepType,
    SubTask,
)

# Planning components
from .planning import ExecutionPlanner, PlanExecutor, QueryAnalyzer, QueryDecomposer

# Prompt engineering
from .prompts import (
    AgentRole,
    TechnicalReActPrompt,
    get_react_prompt,
    get_system_prompt,
    get_tool_guidance,
)

# Agent implementations
from .react_agent import ReActAgent

__all__ = [
    # Base classes
    "BaseAgent",
    "BaseMemory",
    "AgentError",
    "AgentTimeoutError",
    "AgentIterationLimitError",
    "MemoryError",
    "MemoryCapacityError",

    # Data models - Results
    "AgentResult",
    "ReasoningStep",
    "ExecutionResult",

    # Data models - Enums
    "StepType",
    "QueryType",
    "ExecutionStrategy",

    # Data models - Configuration
    "AgentConfig",
    "ProcessorConfig",

    # Data models - Planning
    "QueryAnalysis",
    "SubTask",
    "ExecutionPlan",

    # Data models - Memory
    "Message",

    # Memory implementations
    "ConversationMemory",
    "WorkingMemory",

    # Agent implementations
    "ReActAgent",
    "PhaseOneToolAdapter",
    "convert_tools_to_langchain",

    # Prompt engineering
    "TechnicalReActPrompt",
    "AgentRole",
    "get_system_prompt",
    "get_tool_guidance",
    "get_react_prompt",

    # Planning components
    "QueryAnalyzer",
    "QueryDecomposer",
    "ExecutionPlanner",
    "PlanExecutor",
]
