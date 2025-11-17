# Phase 2: Agent Orchestration - Detailed Implementation Guide

**Duration**: 12-18 hours
**Prerequisites**: Phase 1 Complete
**Deliverable**: Intelligent agent system with multi-step reasoning
**Status**: Pending Phase 1
**Date**: 2025-11-17

---

## Table of Contents

1. [Overview](#overview)
2. [Task 2.1: LangChain Agent Framework](#task-21-langchain-agent-framework)
3. [Task 2.2: Query Planning System](#task-22-query-planning-system)
4. [Task 2.3: RAG Pipeline Integration](#task-23-rag-pipeline-integration)
5. [Task 2.4: Testing & Documentation](#task-24-testing--documentation)
6. [Verification Checklist](#verification-checklist)

---

## Overview

### Phase 2 Goals
Transform Phase 1 tools into a sophisticated agent system with:
- **Multi-step reasoning** using ReAct pattern
- **Intelligent query planning** for complex queries
- **LangChain integration** for production-grade orchestration
- **Full RAG pipeline integration** with existing components

### Architecture Addition

```
┌─────────────────────────────────────────────────────────────┐
│                   IntelligentQueryProcessor                  │
│                                                              │
│  ┌────────────┐         ┌────────────┐                     │
│  │  Query     │ ──────> │  Query     │ ──────┐             │
│  │  Analyzer  │         │  Planner   │       │             │
│  └────────────┘         └────────────┘       │             │
│                                               ▼             │
│                         ┌─────────────────────────────┐    │
│                         │   Execution Strategy        │    │
│                         │  • Simple (direct RAG)      │    │
│                         │  • Research (agent + tools) │    │
│                         │  • Analytical (multi-step)  │    │
│                         └─────────────────────────────┘    │
│                                      │                      │
│                                      ▼                      │
│  ┌────────────────────────────────────────────────┐       │
│  │          ReAct Agent (LangChain)                │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │       │
│  │  │ Thought  │─>│  Action  │─>│ Observe  │ ──┐ │       │
│  │  └──────────┘  └──────────┘  └──────────┘   │ │       │
│  │       ▲                                      │ │       │
│  │       └──────────────────────────────────────┘ │       │
│  └────────────────────────────────────────────────┘       │
│                         │                                   │
│                         ▼                                   │
│  ┌────────────────────────────────────────────────┐       │
│  │     Tool Registry (from Phase 1)               │       │
│  │  • document_search  • calculator  • code       │       │
│  └────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                  Existing RAG Pipeline
```

---

## Task 2.1: LangChain Agent Framework

**Duration**: 5-6 hours
**Goal**: Production-grade agent system with ReAct pattern

### Step 2.1.1: Install LangChain Dependencies (0.5 hours)

**Installation**:
```bash
# Activate environment
conda activate rag-portfolio

# Install LangChain core packages
pip install langchain>=0.1.0
pip install langchain-core>=0.1.0
pip install langchain-openai>=0.0.5
pip install langchain-anthropic>=0.1.0

# Install optional dependencies
pip install langchain-community>=0.0.10  # For additional tools

# Verify installation
python -c "import langchain; print(langchain.__version__)"
python -c "from langchain_openai import ChatOpenAI; print('OpenAI OK')"
python -c "from langchain_anthropic import ChatAnthropic; print('Anthropic OK')"
```

**Version Pinning** (recommended):
```bash
# Create requirements file for Phase 2
cat > requirements-epic5-phase2.txt << EOF
langchain==0.1.0
langchain-core==0.1.0
langchain-openai==0.0.5
langchain-anthropic==0.1.0
langchain-community==0.0.10
EOF

# Install
pip install -r requirements-epic5-phase2.txt
```

---

### Step 2.1.2: Create Base Agent Interface (1 hour)

**File**: `src/components/query_processors/agents/base_agent.py`

**Implementation**:
```python
"""
Base agent interface for query processing.

Defines the contract for all agent implementations including ReAct,
research agents, and analytical agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result from agent execution."""
    answer: str
    reasoning_steps: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    confidence: float
    execution_time: float
    cost_estimate: Optional[float] = None


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Agents are responsible for:
    - Multi-step reasoning
    - Tool selection and execution
    - Result synthesis
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize agent.

        Args:
            name: Agent name (e.g., "react_agent", "research_agent")
            config: Agent configuration
        """
        self.name = name
        self.config = config or {}
        self._execution_count = 0
        self._total_execution_time = 0.0

    @abstractmethod
    def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResult:
        """
        Process a query using agent reasoning.

        Args:
            query: User query
            context: Optional context (conversation history, etc.)
            **kwargs: Additional parameters

        Returns:
            Agent result with answer and reasoning trace
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get list of agent capabilities.

        Returns:
            List of capability strings (e.g., ["multi_step_reasoning", "tool_use"])
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get agent execution statistics."""
        return {
            'name': self.name,
            'executions': self._execution_count,
            'total_time': self._total_execution_time,
            'avg_time': (
                self._total_execution_time / self._execution_count
                if self._execution_count > 0
                else 0.0
            )
        }

    def _record_execution(self, execution_time: float) -> None:
        """Record execution metrics."""
        self._execution_count += 1
        self._total_execution_time += execution_time
```

---

### Step 2.1.3: Implement ReAct Agent (2-3 hours)

**File**: `src/components/query_processors/agents/react_agent.py`

**Implementation**:
```python
"""
ReAct (Reasoning + Acting) agent implementation.

Implements the ReAct pattern:
1. Thought: Reason about the next action
2. Action: Select and execute a tool
3. Observation: Observe the result
4. Repeat until final answer

Reference: https://arxiv.org/abs/2210.03629
"""

import time
import logging
from typing import Dict, Any, List, Optional

try:
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import HumanMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from .base_agent import BaseAgent, AgentResult
from ..tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class ReActAgent(BaseAgent):
    """
    ReAct pattern agent using LangChain.

    Features:
    - Multi-step reasoning with chain-of-thought
    - Automatic tool selection
    - Iterative problem solving
    - Conversation memory
    """

    def __init__(
        self,
        llm_provider: str = "openai",
        model_name: str = "gpt-4-turbo",
        tool_registry: Optional[ToolRegistry] = None,
        max_iterations: int = 10,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ReAct agent.

        Args:
            llm_provider: "openai" or "anthropic"
            model_name: Model to use
            tool_registry: Tool registry from Phase 1
            max_iterations: Max reasoning iterations
            config: Additional configuration
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain not installed. Run: pip install langchain")

        super().__init__(name="react_agent", config=config)

        self.llm_provider = llm_provider
        self.model_name = model_name
        self.max_iterations = max_iterations

        # Get tools from registry
        if tool_registry is None:
            raise ValueError("ToolRegistry required for ReAct agent")
        self.tool_registry = tool_registry
        self.tools = self._convert_tools_to_langchain()

        # Initialize LLM
        self.llm = self._initialize_llm()

        # Create agent
        self.agent = self._create_agent()
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=self.max_iterations,
            return_intermediate_steps=True
        )

        logger.info(f"Initialized ReAct agent with {len(self.tools)} tools")

    def _initialize_llm(self):
        """Initialize LLM based on provider."""
        if self.llm_provider == "openai":
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.config.get('temperature', 0.1)
            )
        elif self.llm_provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=self.model_name,
                temperature=self.config.get('temperature', 0.1)
            )
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")

    def _convert_tools_to_langchain(self) -> List:
        """Convert Phase 1 tools to LangChain format."""
        from langchain.tools import Tool

        langchain_tools = []
        for tool_name, tool in self.tool_registry.tools.items():
            langchain_tool = Tool(
                name=tool.name,
                description=tool.description,
                func=tool.execute
            )
            langchain_tools.append(langchain_tool)

        return langchain_tools

    def _create_agent(self):
        """Create ReAct agent with prompt."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful technical assistant with access to tools.

Use the following format for reasoning:

Thought: Think about what you need to do
Action: Choose a tool to use
Observation: Observe the result
... (repeat as needed)
Thought: I now know the final answer
Final Answer: Provide the complete answer

Always reason step-by-step and use tools when needed."""),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        return create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

    def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResult:
        """
        Process query with ReAct reasoning.

        Args:
            query: User query
            context: Optional context (conversation history)
            **kwargs: Additional parameters

        Returns:
            Agent result with reasoning trace
        """
        start_time = time.time()

        try:
            # Prepare input
            agent_input = {"input": query}

            # Add chat history if available
            if context and 'chat_history' in context:
                agent_input['chat_history'] = context['chat_history']

            # Execute agent
            logger.info(f"ReAct agent processing: {query[:100]}...")
            result = self.executor.invoke(agent_input)

            execution_time = time.time() - start_time
            self._record_execution(execution_time)

            # Extract reasoning steps
            reasoning_steps = []
            for step in result.get('intermediate_steps', []):
                action, observation = step
                reasoning_steps.append({
                    'action': action.tool,
                    'action_input': action.tool_input,
                    'observation': str(observation)
                })

            # Extract tool calls
            tool_calls = [
                {
                    'tool': step['action'],
                    'input': step['action_input'],
                    'result': step['observation']
                }
                for step in reasoning_steps
            ]

            # Calculate confidence (simple heuristic)
            confidence = 0.9 if len(reasoning_steps) > 0 else 0.7

            return AgentResult(
                answer=result['output'],
                reasoning_steps=reasoning_steps,
                tool_calls=tool_calls,
                confidence=confidence,
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"ReAct agent error: {str(e)}")
            execution_time = time.time() - start_time
            self._record_execution(execution_time)

            # Return error result
            return AgentResult(
                answer=f"Error processing query: {str(e)}",
                reasoning_steps=[],
                tool_calls=[],
                confidence=0.0,
                execution_time=execution_time
            )

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return [
            "multi_step_reasoning",
            "tool_use",
            "chain_of_thought",
            "iterative_problem_solving"
        ]
```

**Testing**:
```python
# tests/epic5/phase2/unit/test_react_agent.py
import pytest
from src.components.query_processors.agents.react_agent import ReActAgent
from src.components.query_processors.tools.tool_registry import ToolRegistry

def test_react_agent_initialization():
    """Test agent initialization."""
    tool_registry = ToolRegistry()
    # Register mock tool
    # ...

    agent = ReActAgent(
        llm_provider="openai",
        model_name="gpt-4-turbo",
        tool_registry=tool_registry
    )

    assert agent.name == "react_agent"
    assert len(agent.tools) > 0

@pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason="No API key")
def test_react_agent_simple_query():
    """Test agent with simple query."""
    # Setup
    tool_registry = ToolRegistry()
    # Register tools...

    agent = ReActAgent(tool_registry=tool_registry)

    # Execute
    result = agent.process("What is 25 * 47?")

    # Verify
    assert result.answer
    assert result.execution_time > 0
    assert len(result.reasoning_steps) > 0
```

---

### Step 2.1.4: Memory System (1.5 hours)

**File**: `src/components/query_processors/agents/memory/conversation_memory.py`

**Implementation**:
```python
"""Conversation memory for agents."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversationTurn:
    """Single conversation turn."""
    timestamp: datetime
    role: str  # "user" or "assistant"
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationMemory:
    """
    Manages conversation history for agents.

    Features:
    - Stores conversation turns
    - Provides context window management
    - Supports summarization
    """

    def __init__(self, max_turns: int = 10, max_tokens: int = 4000):
        """
        Initialize conversation memory.

        Args:
            max_turns: Maximum conversation turns to keep
            max_tokens: Maximum tokens in context (approximate)
        """
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.turns: List[ConversationTurn] = []

    def add_turn(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add conversation turn."""
        turn = ConversationTurn(
            timestamp=datetime.now(),
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.turns.append(turn)

        # Trim if needed
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]

    def get_context(self) -> List[Dict[str, str]]:
        """Get conversation context as message list."""
        return [
            {"role": turn.role, "content": turn.content}
            for turn in self.turns
        ]

    def clear(self) -> None:
        """Clear conversation history."""
        self.turns = []

    def get_summary(self) -> str:
        """Get summary of conversation."""
        if not self.turns:
            return "No conversation history"

        return f"Conversation with {len(self.turns)} turns"
```

---

## Task 2.2: Query Planning System

**Duration**: 4-5 hours
**Goal**: Intelligent query decomposition and execution planning

### Step 2.2.1: Query Analyzer (1 hour)

**File**: `src/components/query_processors/planning/query_analyzer.py`

```python
"""
Query analysis for intelligent routing.

Analyzes queries to determine:
- Query type (simple, research, analytical, creative)
- Complexity score
- Required capabilities
- Execution strategy
"""

import re
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    """Query classification types."""
    SIMPLE = "simple"           # Direct RAG lookup
    RESEARCH = "research"       # Multi-source research
    ANALYTICAL = "analytical"   # Multi-step analysis
    CREATIVE = "creative"       # Creative generation


@dataclass
class QueryAnalysis:
    """Analysis result for a query."""
    query_type: QueryType
    complexity: float  # 0.0 to 1.0
    requires_tools: bool
    suggested_tools: List[str]
    estimated_steps: int
    confidence: float


class QueryAnalyzer:
    """Analyze queries to determine execution strategy."""

    # Keywords for query type classification
    RESEARCH_KEYWORDS = [
        "compare", "research", "investigate", "analyze",
        "find information", "what are the differences"
    ]

    ANALYTICAL_KEYWORDS = [
        "calculate", "compute", "solve", "analyze",
        "break down", "step by step"
    ]

    SIMPLE_KEYWORDS = [
        "what is", "define", "explain", "describe"
    ]

    def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyze query and determine characteristics.

        Args:
            query: User query

        Returns:
            Query analysis result
        """
        query_lower = query.lower()

        # Determine type
        query_type = self._classify_type(query_lower)

        # Calculate complexity
        complexity = self._calculate_complexity(query_lower)

        # Determine if tools needed
        requires_tools = self._requires_tools(query_lower, query_type)

        # Suggest tools
        suggested_tools = self._suggest_tools(query_lower, query_type)

        # Estimate steps
        estimated_steps = self._estimate_steps(complexity, requires_tools)

        return QueryAnalysis(
            query_type=query_type,
            complexity=complexity,
            requires_tools=requires_tools,
            suggested_tools=suggested_tools,
            estimated_steps=estimated_steps,
            confidence=0.8  # Simple heuristic
        )

    def _classify_type(self, query: str) -> QueryType:
        """Classify query type based on keywords."""
        if any(kw in query for kw in self.RESEARCH_KEYWORDS):
            return QueryType.RESEARCH
        elif any(kw in query for kw in self.ANALYTICAL_KEYWORDS):
            return QueryType.ANALYTICAL
        elif any(kw in query for kw in self.SIMPLE_KEYWORDS):
            return QueryType.SIMPLE
        else:
            return QueryType.SIMPLE

    def _calculate_complexity(self, query: str) -> float:
        """Calculate query complexity (0.0 to 1.0)."""
        complexity = 0.0

        # Length factor
        word_count = len(query.split())
        complexity += min(word_count / 50, 0.3)

        # Question marks (multi-part)
        question_count = query.count('?')
        complexity += min(question_count * 0.2, 0.3)

        # Keywords indicating complexity
        complex_indicators = ["and", "or", "but", "compare", "analyze"]
        indicator_count = sum(1 for ind in complex_indicators if ind in query)
        complexity += min(indicator_count * 0.1, 0.4)

        return min(complexity, 1.0)

    def _requires_tools(self, query: str, query_type: QueryType) -> bool:
        """Determine if tools are needed."""
        # Analytical queries usually need tools
        if query_type == QueryType.ANALYTICAL:
            return True

        # Check for specific tool indicators
        tool_indicators = ["calculate", "compute", "code", "search"]
        return any(ind in query for ind in tool_indicators)

    def _suggest_tools(self, query: str, query_type: QueryType) -> List[str]:
        """Suggest tools based on query."""
        tools = []

        if "calculate" in query or "compute" in query:
            tools.append("calculator")

        if "code" in query or "program" in query:
            tools.append("code_analyzer")

        if query_type == QueryType.RESEARCH:
            tools.append("document_search")

        return tools

    def _estimate_steps(self, complexity: float, requires_tools: bool) -> int:
        """Estimate number of reasoning steps."""
        if not requires_tools:
            return 1

        if complexity < 0.3:
            return 1
        elif complexity < 0.7:
            return 2
        else:
            return 3
```

---

(Continue with remaining Phase 2 tasks: Query Planner, Execution Strategies, Integration...)

## Verification Checklist

### Task 2.1 Complete:
- [ ] LangChain dependencies installed
- [ ] Base agent interface created
- [ ] ReAct agent operational
- [ ] Memory system functional
- [ ] Agents use Phase 1 tools
- [ ] All tests pass

### Task 2.2 Complete:
- [ ] Query analyzer classifies correctly
- [ ] Query planner creates valid plans
- [ ] Execution strategies work
- [ ] Plans execute successfully

### Task 2.3 Complete:
- [ ] Intelligent processor integrates with RAG
- [ ] Configuration-driven routing works
- [ ] Backward compatible
- [ ] Performance acceptable

### Task 2.4 Complete:
- [ ] Comprehensive test suite
- [ ] Documentation complete
- [ ] Usage examples provided
- [ ] Performance benchmarks documented

### Phase 2 Complete:
- [ ] End-to-end agent system works
- [ ] Multi-step reasoning functional
- [ ] Integration with existing RAG pipeline
- [ ] Production-quality code and docs
- [ ] Ready for portfolio showcase
