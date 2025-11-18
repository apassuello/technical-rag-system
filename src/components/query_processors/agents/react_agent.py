"""
ReAct (Reason + Act) agent implementation using LangChain.

Implements multi-step reasoning using the ReAct pattern where the agent:
1. Observes the current state
2. Thinks about what to do
3. Acts by calling tools
4. Observes the results
5. Repeats until answer is found

Architecture:
- LangChain AgentExecutor for core loop
- Phase 1 tools via adapter
- Memory integration (conversation + working)
- Comprehensive error handling
- Cost and time tracking

Usage:
    >>> from src.components.query_processors.agents import ReActAgent
    >>> from src.components.query_processors.agents.models import AgentConfig
    >>> from langchain_openai import ChatOpenAI
    >>>
    >>> # Configure agent
    >>> config = AgentConfig(
    ...     llm_provider="openai",
    ...     llm_model="gpt-4-turbo",
    ...     max_iterations=10
    ... )
    >>>
    >>> # Create LLM
    >>> llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)
    >>>
    >>> # Create agent
    >>> agent = ReActAgent(llm, tools, memory, config)
    >>>
    >>> # Process query
    >>> result = agent.process("What is 25 * 47 + sqrt(144)?")
    >>> print(result.answer)  # "1187"
"""

import time
from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseChatModel

from .base_agent import BaseAgent
from .models import (
    AgentConfig,
    AgentResult,
    ReasoningStep,
    StepType,
    Message
)
from .langchain_adapter import PhaseOneToolAdapter, convert_tools_to_langchain
from .memory.conversation_memory import ConversationMemory
from .memory.working_memory import WorkingMemory
from ...query_processors.tools.base_tool import BaseTool as Phase1BaseTool
from ...query_processors.tools.models import ToolCall, ToolResult


logger = logging.getLogger(__name__)


# ReAct prompt template
REACT_PROMPT_TEMPLATE = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


class ReActAgent(BaseAgent):
    """
    ReAct pattern agent using LangChain.

    Implements multi-step reasoning where the agent reasons about what
    to do (Thought), takes actions using tools (Action), observes results
    (Observation), and iterates until it reaches a conclusion.

    Key Features:
    - Multi-step reasoning with ReAct pattern
    - Integration with Phase 1 tools
    - Conversation and working memory
    - Configurable LLM backend (OpenAI, Anthropic)
    - Cost and execution time tracking
    - Comprehensive error handling

    Example:
        >>> # Create agent with calculator tool
        >>> config = AgentConfig(
        ...     llm_provider="openai",
        ...     llm_model="gpt-4-turbo",
        ...     temperature=0.7,
        ...     max_iterations=10
        ... )
        >>>
        >>> llm = ChatOpenAI(model="gpt-4-turbo")
        >>> tools = [CalculatorTool()]
        >>> memory = ConversationMemory()
        >>>
        >>> agent = ReActAgent(llm, tools, memory, config)
        >>>
        >>> # Process multi-step query
        >>> result = agent.process(
        ...     "Calculate 25 * 47, then add sqrt(144) to the result"
        ... )
        >>> print(result.answer)  # "1187"
        >>> print(len(result.reasoning_steps))  # Multiple steps
    """

    def __init__(
        self,
        llm: BaseChatModel,
        tools: List[Phase1BaseTool],
        memory: ConversationMemory,
        config: AgentConfig,
        working_memory: Optional[WorkingMemory] = None
    ):
        """
        Initialize ReAct agent.

        Args:
            llm: LangChain LLM instance (ChatOpenAI or ChatAnthropic)
            tools: List of Phase 1 BaseTool instances
            memory: Conversation memory for context
            config: Agent configuration
            working_memory: Optional working memory for task state

        Example:
            >>> from langchain_openai import ChatOpenAI
            >>> llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)
            >>> tools = [CalculatorTool(), DocumentSearchTool(index_path)]
            >>> memory = ConversationMemory(max_messages=100)
            >>> config = AgentConfig(
            ...     llm_provider="openai",
            ...     llm_model="gpt-4-turbo",
            ...     max_iterations=10
            ... )
            >>> agent = ReActAgent(llm, tools, memory, config)
        """
        self.llm = llm
        self.phase1_tools = tools
        self.memory = memory
        self.config = config
        self.working_memory = working_memory or WorkingMemory()

        # Convert Phase 1 tools to LangChain format
        self.langchain_tools = convert_tools_to_langchain(tools)

        # Create ReAct prompt
        self.prompt = PromptTemplate.from_template(REACT_PROMPT_TEMPLATE)

        # Create ReAct agent
        self.react_agent = create_react_agent(
            llm=self.llm,
            tools=self.langchain_tools,
            prompt=self.prompt
        )

        # Create executor
        self.executor = AgentExecutor(
            agent=self.react_agent,
            tools=self.langchain_tools,
            max_iterations=config.max_iterations,
            max_execution_time=config.max_execution_time,
            early_stopping_method=config.early_stopping,
            verbose=config.verbose,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )

        # Reasoning trace
        self._reasoning_steps: List[ReasoningStep] = []
        self._tool_calls: List[ToolCall] = []

        # Statistics
        self._total_queries = 0
        self._total_execution_time = 0.0
        self._total_cost = 0.0
        self._success_count = 0

        logger.info(
            f"Initialized ReActAgent with {len(self.langchain_tools)} tools, "
            f"max_iterations={config.max_iterations}"
        )

    def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Process query with multi-step reasoning.

        This is the main entry point for the agent. It:
        1. Validates the query
        2. Adds query to conversation memory
        3. Executes ReAct loop (Thought → Action → Observation)
        4. Extracts reasoning trace
        5. Returns comprehensive result

        CRITICAL: This method NEVER raises exceptions. All errors are
        returned in AgentResult.error field.

        Args:
            query: User question or request
            context: Optional context dictionary containing:
                - previous_messages: Prior conversation
                - user_preferences: User settings
                - session_id: Session identifier
                - any other contextual information

        Returns:
            AgentResult containing:
                - success: Whether processing succeeded
                - answer: Final answer string
                - reasoning_steps: List of reasoning steps
                - tool_calls: List of tools called
                - execution_time: Total time in seconds
                - total_cost: Estimated cost in USD
                - metadata: Additional metadata
                - error: Error message if success=False

        Example:
            >>> agent = ReActAgent(llm, tools, memory, config)
            >>>
            >>> # Simple query
            >>> result = agent.process("What is 2 + 2?")
            >>> print(result.answer)  # "4"
            >>>
            >>> # Multi-step query
            >>> result = agent.process(
            ...     "Calculate 25 * 47, then add the square root of 144"
            ... )
            >>> print(result.answer)  # "1187"
            >>> print(f"Steps: {len(result.reasoning_steps)}")
            >>>
            >>> # Get reasoning trace
            >>> for step in result.reasoning_steps:
            ...     print(f"{step.step_type.value}: {step.content}")
        """
        start_time = time.time()
        self._reasoning_steps = []
        self._tool_calls = []

        try:
            # Validate query
            if not self.validate_query(query):
                return AgentResult(
                    success=False,
                    answer="",
                    reasoning_steps=[],
                    tool_calls=[],
                    execution_time=0.0,
                    total_cost=0.0,
                    error="Invalid query: query cannot be empty"
                )

            logger.info(f"Processing query: {query[:100]}")

            # Add query to conversation memory
            self.memory.add_message("user", query)

            # Prepare context
            agent_context = self._prepare_context(query, context)

            # Execute agent
            try:
                result = self.executor.invoke({
                    "input": query,
                    **agent_context
                })
            except Exception as e:
                # Agent execution failed
                logger.error(f"Agent execution failed: {e}", exc_info=True)
                execution_time = time.time() - start_time
                return AgentResult(
                    success=False,
                    answer="",
                    reasoning_steps=self._reasoning_steps,
                    tool_calls=self._tool_calls,
                    execution_time=execution_time,
                    total_cost=0.0,
                    error=f"Agent execution failed: {str(e)}"
                )

            # Extract answer
            answer = result.get("output", "")

            # Parse intermediate steps into reasoning trace
            self._parse_intermediate_steps(result.get("intermediate_steps", []))

            # Add final answer to reasoning trace
            self._add_reasoning_step(
                step_type=StepType.FINAL_ANSWER,
                content=answer
            )

            # Calculate execution time and cost
            execution_time = time.time() - start_time
            total_cost = self._estimate_cost(query, answer, self._reasoning_steps)

            # Add assistant response to memory
            self.memory.add_message("assistant", answer)

            # Update statistics
            self._total_queries += 1
            self._total_execution_time += execution_time
            self._total_cost += total_cost
            self._success_count += 1

            logger.info(
                f"Query processed successfully in {execution_time:.2f}s, "
                f"cost: ${total_cost:.4f}, steps: {len(self._reasoning_steps)}"
            )

            return AgentResult(
                success=True,
                answer=answer,
                reasoning_steps=self._reasoning_steps.copy(),
                tool_calls=self._tool_calls.copy(),
                execution_time=execution_time,
                total_cost=total_cost,
                metadata={
                    "llm_provider": self.config.llm_provider,
                    "llm_model": self.config.llm_model,
                    "iterations": len(self._reasoning_steps),
                    "tools_used": len(self._tool_calls)
                }
            )

        except Exception as e:
            # Unexpected error (should not happen)
            logger.error(f"Unexpected error in agent process: {e}", exc_info=True)
            execution_time = time.time() - start_time
            self._total_queries += 1

            return AgentResult(
                success=False,
                answer="",
                reasoning_steps=self._reasoning_steps,
                tool_calls=self._tool_calls,
                execution_time=execution_time,
                total_cost=0.0,
                error=f"Unexpected error: {str(e)}"
            )

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
            List of ReasoningStep objects in chronological order

        Example:
            >>> agent = ReActAgent(llm, tools, memory, config)
            >>> result = agent.process("Calculate 25 * 47 + sqrt(144)")
            >>>
            >>> trace = agent.get_reasoning_trace()
            >>> for step in trace:
            ...     print(f"Step {step.step_number}: {step.step_type.value}")
            ...     print(f"  Content: {step.content[:50]}")
        """
        return self._reasoning_steps.copy()

    def reset(self) -> None:
        """
        Reset agent state.

        Clears:
        - Reasoning trace
        - Tool call history
        - Working memory
        - Conversation memory (if specified)

        Example:
            >>> agent = ReActAgent(llm, tools, memory, config)
            >>> agent.process("First query")
            >>> agent.process("Second query")  # May use context from first
            >>> agent.reset()  # Clear all state
            >>> agent.process("Third query")  # Fresh start
        """
        self._reasoning_steps = []
        self._tool_calls = []
        self.working_memory.clear()
        logger.info("Agent state reset")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics.

        Returns:
            Dictionary with performance metrics:
                - total_queries: Number of queries processed
                - success_count: Number of successful queries
                - success_rate: Percentage of successful queries
                - total_execution_time: Cumulative execution time
                - avg_execution_time: Average time per query
                - total_cost: Cumulative cost
                - avg_cost: Average cost per query

        Example:
            >>> agent = ReActAgent(llm, tools, memory, config)
            >>> # ... process several queries ...
            >>> stats = agent.get_stats()
            >>> print(f"Success rate: {stats['success_rate']:.1%}")
            >>> print(f"Avg cost: ${stats['avg_cost']:.4f}")
        """
        return {
            "total_queries": self._total_queries,
            "success_count": self._success_count,
            "success_rate": (
                self._success_count / self._total_queries
                if self._total_queries > 0
                else 0.0
            ),
            "total_execution_time": self._total_execution_time,
            "avg_execution_time": (
                self._total_execution_time / self._total_queries
                if self._total_queries > 0
                else 0.0
            ),
            "total_cost": self._total_cost,
            "avg_cost": (
                self._total_cost / self._total_queries
                if self._total_queries > 0
                else 0.0
            )
        }

    def _prepare_context(
        self,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Prepare context for agent execution.

        Args:
            query: User query
            context: Optional additional context

        Returns:
            Context dictionary for agent
        """
        agent_context = {}

        # Add conversation history if available
        if self.memory.get_message_count() > 0:
            recent_messages = self.memory.get_messages(last_n=5)
            agent_context["conversation_history"] = [
                f"{msg.role}: {msg.content}"
                for msg in recent_messages
            ]

        # Add working memory context
        if len(self.working_memory) > 0:
            agent_context["working_context"] = self.working_memory.get_all_context()

        # Add additional context if provided
        if context:
            agent_context.update(context)

        return agent_context

    def _parse_intermediate_steps(
        self,
        intermediate_steps: List[tuple]
    ) -> None:
        """
        Parse LangChain intermediate steps into reasoning trace.

        Args:
            intermediate_steps: List of (AgentAction, observation) tuples
        """
        for i, (action, observation) in enumerate(intermediate_steps, 1):
            # Add thought step (from action.log)
            if hasattr(action, 'log') and action.log:
                self._add_reasoning_step(
                    step_type=StepType.THOUGHT,
                    content=action.log
                )

            # Add action step
            tool_call = ToolCall(
                tool_name=action.tool,
                arguments={action.tool_input: action.tool_input} if isinstance(action.tool_input, str) else action.tool_input,
                timestamp=datetime.now()
            )
            self._tool_calls.append(tool_call)

            self._add_reasoning_step(
                step_type=StepType.ACTION,
                content=f"Calling tool: {action.tool}",
                tool_call=tool_call
            )

            # Add observation step
            tool_result = ToolResult(
                success=True,
                content=str(observation),
                execution_time=0.0
            )

            self._add_reasoning_step(
                step_type=StepType.OBSERVATION,
                content=str(observation),
                tool_result=tool_result
            )

    def _add_reasoning_step(
        self,
        step_type: StepType,
        content: str,
        tool_call: Optional[ToolCall] = None,
        tool_result: Optional[ToolResult] = None
    ) -> None:
        """
        Add reasoning step to trace.

        Args:
            step_type: Type of step
            content: Step content
            tool_call: Optional tool call (for ACTION steps)
            tool_result: Optional tool result (for OBSERVATION steps)
        """
        step = ReasoningStep(
            step_number=len(self._reasoning_steps) + 1,
            step_type=step_type,
            content=content,
            tool_call=tool_call,
            tool_result=tool_result,
            timestamp=datetime.now()
        )
        self._reasoning_steps.append(step)

    def _estimate_cost(
        self,
        query: str,
        answer: str,
        reasoning_steps: List[ReasoningStep]
    ) -> float:
        """
        Estimate cost of query processing.

        This is a rough estimate based on token counts and provider pricing.
        For accurate costs, integrate with provider billing APIs.

        Args:
            query: Input query
            answer: Output answer
            reasoning_steps: Reasoning trace

        Returns:
            Estimated cost in USD
        """
        # Rough token estimation (actual tokenization would be more accurate)
        input_tokens = len(query.split()) * 1.3  # ~1.3 tokens per word
        output_tokens = len(answer.split()) * 1.3

        # Add tokens from reasoning steps
        for step in reasoning_steps:
            input_tokens += len(step.content.split()) * 1.3

        # Pricing (approximate, as of 2024)
        if self.config.llm_provider == "openai":
            if "gpt-4" in self.config.llm_model:
                # GPT-4 pricing
                input_cost = (input_tokens / 1000) * 0.03
                output_cost = (output_tokens / 1000) * 0.06
            else:
                # GPT-3.5 pricing
                input_cost = (input_tokens / 1000) * 0.001
                output_cost = (output_tokens / 1000) * 0.002
        elif self.config.llm_provider == "anthropic":
            # Claude pricing
            input_cost = (input_tokens / 1000) * 0.008
            output_cost = (output_tokens / 1000) * 0.024
        else:
            # Unknown provider
            return 0.0

        return input_cost + output_cost

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ReActAgent(llm={self.config.llm_model}, "
            f"tools={len(self.langchain_tools)}, "
            f"max_iterations={self.config.max_iterations})"
        )
