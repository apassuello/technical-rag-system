"""
Abstract base class for all agents.

This module defines the agent interface that all agent implementations must follow.
Ensures consistent API across different agent types (ReAct, Plan-and-Execute, etc.).

Architecture:
- Abstract interface using ABC
- Type-safe with comprehensive type hints
- Clear contract for agent implementations
- Optional methods for advanced features

Usage:
    >>> from src.components.query_processors.agents.base_agent.py import BaseAgent
    >>> from src.components.query_processors.agents.react_agent import ReActAgent
    >>>
    >>> # Create concrete agent
    >>> agent = ReActAgent(llm, tools, memory, config)
    >>>
    >>> # Process query
    >>> result = agent.process("What is machine learning?")
    >>> print(result.answer)
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .models import AgentResult, ReasoningStep

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    All agent implementations must inherit from this class and implement
    the abstract methods. This ensures a consistent interface across
    different agent types.

    Key Principles:
    - process() is the main entry point
    - get_reasoning_trace() for observability
    - reset() for stateful agents
    - Never raise exceptions from process() (return AgentResult with error)

    Example:
        >>> class MyAgent(BaseAgent):
        ...     def process(self, query, context=None):
        ...         # Implementation
        ...         return AgentResult(...)
        ...
        ...     def get_reasoning_trace(self):
        ...         return self.reasoning_steps
    """

    @abstractmethod
    def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Process query with agent.

        This is the main entry point for agent processing. The agent should:
        1. Analyze the query
        2. Plan approach (if needed)
        3. Execute tools as needed
        4. Synthesize final answer

        CRITICAL: This method MUST NEVER raise exceptions.
        All errors should be returned in AgentResult.error field.

        Args:
            query: User question or request
            context: Optional context dictionary containing:
                - previous_messages: List of prior messages
                - user_preferences: User-specific settings
                - session_id: Session identifier
                - any other contextual information

        Returns:
            AgentResult containing:
                - success: Whether processing succeeded
                - answer: Final answer string
                - reasoning_steps: List of reasoning steps taken
                - tool_calls: List of tools called
                - execution_time: Total time in seconds
                - total_cost: Total cost in USD
                - metadata: Additional metadata
                - error: Error message if success=False

        Example:
            >>> agent = ReActAgent(llm, tools, memory, config)
            >>> result = agent.process("What is 25 * 47?")
            >>> print(f"Answer: {result.answer}")
            >>> print(f"Steps: {len(result.reasoning_steps)}")
            >>> print(f"Cost: ${result.total_cost:.4f}")
        """
        pass

    @abstractmethod
    def get_reasoning_trace(self) -> List[ReasoningStep]:
        """
        Get agent's reasoning steps for observability.

        Returns the complete trace of the agent's reasoning process,
        including thoughts, actions, and observations. Useful for:
        - Debugging agent behavior
        - Understanding decision-making
        - Auditing tool use
        - Explaining answers to users

        Returns:
            List of ReasoningStep objects in chronological order,
            each containing:
                - step_number: Sequential step number
                - step_type: THOUGHT, ACTION, OBSERVATION, or FINAL_ANSWER
                - content: Step content
                - tool_call: Tool call details (if ACTION)
                - tool_result: Tool result (if OBSERVATION)
                - timestamp: When step occurred

        Example:
            >>> result = agent.process("Calculate 25 * 47 + sqrt(144)")
            >>> trace = agent.get_reasoning_trace()
            >>> for step in trace:
            ...     print(f"{step.step_type.value}: {step.content[:50]}")
            THOUGHT: I need to perform calculations...
            ACTION: Calling calculator tool...
            OBSERVATION: Result: 1175...
            THOUGHT: Now I need sqrt(144)...
            ACTION: Calling calculator again...
            OBSERVATION: Result: 12...
            FINAL_ANSWER: 1187
        """
        pass

    def reset(self) -> None:
        """
        Reset agent state.

        Optional method for stateful agents that maintain internal state
        across multiple process() calls. Implementations should:
        - Clear reasoning traces
        - Reset memory (if applicable)
        - Clear cached results
        - Reset any counters or metrics

        Default implementation does nothing (for stateless agents).

        Example:
            >>> agent = ReActAgent(llm, tools, memory, config)
            >>> agent.process("First query")
            >>> agent.process("Second query")  # May use context from first
            >>> agent.reset()  # Clear all state
            >>> agent.process("Third query")  # Fresh start
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics.

        Optional method to return agent performance metrics and statistics.
        Useful for monitoring, optimization, and debugging.

        Returns:
            Dictionary with statistics such as:
                - total_queries: Number of queries processed
                - total_execution_time: Cumulative execution time
                - total_cost: Cumulative cost
                - avg_steps_per_query: Average reasoning steps
                - tool_usage: Tool usage counts
                - success_rate: Percentage of successful queries

        Default implementation returns empty dict.

        Example:
            >>> agent = ReActAgent(llm, tools, memory, config)
            >>> # ... process several queries ...
            >>> stats = agent.get_stats()
            >>> print(f"Success rate: {stats['success_rate']:.1%}")
            >>> print(f"Avg cost: ${stats['avg_cost']:.4f}")
        """
        return {}

    def validate_query(self, query: str) -> bool:
        """
        Validate query before processing.

        Optional method to perform query validation. Useful for:
        - Checking query length limits
        - Detecting malicious inputs
        - Ensuring query is well-formed
        - Pre-processing checks

        Args:
            query: Query to validate

        Returns:
            True if query is valid, False otherwise

        Default implementation accepts all non-empty queries.

        Example:
            >>> agent = ReActAgent(llm, tools, memory, config)
            >>> if agent.validate_query(user_query):
            ...     result = agent.process(user_query)
            ... else:
            ...     print("Invalid query")
        """
        return len(query.strip()) > 0

    def __repr__(self) -> str:
        """String representation of agent."""
        return f"{self.__class__.__name__}()"


class AgentError(Exception):
    """Base exception for agent errors."""

    pass


class AgentTimeoutError(AgentError):
    """Agent execution exceeded timeout."""

    pass


class AgentIterationLimitError(AgentError):
    """Agent exceeded maximum iterations."""

    pass


class AgentToolError(AgentError):
    """Error in tool execution."""

    pass


class AgentPlanningError(AgentError):
    """Error in query planning."""

    pass
