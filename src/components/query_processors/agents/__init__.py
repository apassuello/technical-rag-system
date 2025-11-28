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
from .base_agent import BaseAgent, AgentError, AgentTimeoutError, AgentIterationLimitError
from .base_memory import BaseMemory, MemoryError, MemoryCapacityError

# Data models
from .models import (
    # Results
    AgentResult,
    ReasoningStep,
    ExecutionResult,

    # Enums
    StepType,
    QueryType,
    ExecutionStrategy,

    # Configuration
    AgentConfig,
    ProcessorConfig,

    # Planning
    QueryAnalysis,
    SubTask,
    ExecutionPlan,

    # Memory
    Message,
)

# Memory implementations
from .memory import ConversationMemory, WorkingMemory

# Agent implementations
from .react_agent import ReActAgent
from .langchain_adapter import PhaseOneToolAdapter, convert_tools_to_langchain

# Planning components
from .planning import QueryAnalyzer, QueryDecomposer, ExecutionPlanner, PlanExecutor

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

    # Planning components
    "QueryAnalyzer",
    "QueryDecomposer",
    "ExecutionPlanner",
    "PlanExecutor",
]
