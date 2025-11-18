# Phase 2 API Documentation

**Epic 5**: Tool & Function Calling for RAG System
**Phase**: Phase 2 - Agent Orchestration & Query Planning
**Version**: 1.0
**Date**: November 18, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Core Components](#core-components)
   - [IntelligentQueryProcessor](#intelligentqueryprocessor)
   - [ReActAgent](#reactagent)
   - [QueryAnalyzer](#queryanalyzer)
   - [QueryDecomposer](#querydecomposer)
   - [ExecutionPlanner](#executionplanner)
   - [PlanExecutor](#planexecutor)
3. [Memory System](#memory-system)
   - [ConversationMemory](#conversationmemory)
   - [WorkingMemory](#workingmemory)
4. [Data Models](#data-models)
   - [AgentResult](#agentresult)
   - [QueryAnalysis](#queryanalysis)
   - [ExecutionPlan](#executionplan)
   - [Configuration Models](#configuration-models)
5. [Usage Examples](#usage-examples)
6. [Error Handling](#error-handling)

---

## Overview

Phase 2 adds intelligent agent orchestration and query planning to the RAG system. The API provides:

- **Automatic routing** between RAG pipeline and agent system
- **Multi-step reasoning** with the ReAct pattern
- **Query planning** for complex tasks
- **Memory management** for conversation context
- **Cost tracking** and budget enforcement
- **100% backward compatibility** with existing QueryProcessor

---

## Core Components

### IntelligentQueryProcessor

**Purpose**: Main entry point for intelligent query processing with automatic RAG/agent routing.

**Location**: `src.components.query_processors.intelligent_query_processor`

#### Class Definition

```python
class IntelligentQueryProcessor(QueryProcessor):
    """
    Intelligent query processor with automatic RAG/agent routing.

    Routes simple queries to RAG pipeline and complex queries to agent system
    based on complexity analysis. Provides cost tracking, fallback behavior,
    and comprehensive metadata.
    """
```

#### Constructor

```python
def __init__(
    self,
    retriever: Retriever,
    generator: AnswerGenerator,
    agent: Optional[BaseAgent] = None,
    query_analyzer: Optional[QueryAnalyzer] = None,
    config: Optional[ProcessorConfig] = None
) -> None:
    """
    Initialize intelligent query processor.

    Args:
        retriever: Document retriever for RAG pipeline
        generator: Answer generator for RAG pipeline
        agent: Optional ReAct agent for complex queries
        query_analyzer: Optional query analyzer for complexity detection
        config: Optional processor configuration

    Example:
        >>> from src.components.query_processors import IntelligentQueryProcessor
        >>> from src.components.query_processors.agents import ReActAgent, QueryAnalyzer
        >>> from src.components.query_processors.agents.models import ProcessorConfig
        >>>
        >>> # With full agent support
        >>> processor = IntelligentQueryProcessor(
        ...     retriever=my_retriever,
        ...     generator=my_generator,
        ...     agent=my_agent,
        ...     query_analyzer=QueryAnalyzer(),
        ...     config=ProcessorConfig(complexity_threshold=0.7)
        ... )
        >>>
        >>> # RAG-only mode (backward compatible)
        >>> processor = IntelligentQueryProcessor(
        ...     retriever=my_retriever,
        ...     generator=my_generator
        ... )
    """
```

#### Main Methods

##### `process()`

```python
def process(
    self,
    query: str,
    use_agent: Optional[bool] = None,
    context: Optional[Dict[str, Any]] = None
) -> Answer:
    """
    Process query with automatic or manual routing.

    Args:
        query: User's question
        use_agent: Optional override for routing decision
            - None: Automatic routing based on complexity
            - True: Force agent usage
            - False: Force RAG usage
        context: Optional context dictionary for additional information

    Returns:
        Answer object with:
            - answer: Final answer string
            - sources: List of source documents (for RAG queries)
            - metadata: Dict with routing info, cost, timing, etc.

    Raises:
        AgentError: If agent processing fails and no fallback available
        ValueError: If query is empty or invalid

    Example:
        >>> # Automatic routing
        >>> answer = processor.process("What is machine learning?")
        >>> print(answer.answer)
        >>> print(answer.metadata["routing_decision"])  # "rag_pipeline"
        >>>
        >>> # Force agent usage
        >>> answer = processor.process(
        ...     "Calculate 25 * 47",
        ...     use_agent=True
        ... )
        >>> print(answer.metadata["routing_decision"])  # "agent_system"
        >>>
        >>> # With context
        >>> answer = processor.process(
        ...     "Continue analysis",
        ...     context={"previous_results": [...]}
        ... )
    """
```

##### `health_check()`

```python
def health_check(self) -> HealthStatus:
    """
    Check health of processor and all components.

    Returns:
        HealthStatus with component status

    Example:
        >>> status = processor.health_check()
        >>> if status.is_healthy:
        ...     print("System ready")
    """
```

#### Metadata Fields

The `Answer.metadata` dictionary includes:

| Field | Type | Description |
|-------|------|-------------|
| `routing_decision` | str | "rag_pipeline" or "agent_system" |
| `query_complexity` | float | 0.0-1.0 complexity score |
| `query_type` | str | Query classification |
| `total_cost` | float | Total cost in USD |
| `execution_time` | float | Total time in seconds |
| `reasoning_trace` | List | Agent reasoning steps (if agent used) |
| `tools_used` | List[str] | Tools called (if agent used) |
| `agent_failed` | bool | Whether agent failed |
| `fallback_used` | bool | Whether fallback to RAG occurred |

---

### ReActAgent

**Purpose**: Multi-step reasoning agent using the ReAct (Reason + Act) pattern.

**Location**: `src.components.query_processors.agents.react_agent`

#### Class Definition

```python
class ReActAgent(BaseAgent):
    """
    ReAct pattern agent using LangChain.

    Implements iterative reasoning: Thought → Action → Observation → repeat
    until final answer is reached.
    """
```

#### Constructor

```python
def __init__(
    self,
    llm: BaseChatModel,
    tools: List[BaseTool],
    memory: ConversationMemory,
    config: AgentConfig,
    working_memory: Optional[WorkingMemory] = None
) -> None:
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
        >>> from src.components.query_processors.agents import ReActAgent
        >>> from src.components.query_processors.agents.models import AgentConfig
        >>> from src.components.query_processors.agents.memory import ConversationMemory
        >>> from src.components.query_processors.tools.implementations import CalculatorTool
        >>>
        >>> llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)
        >>> tools = [CalculatorTool()]
        >>> memory = ConversationMemory()
        >>> config = AgentConfig(
        ...     llm_provider="openai",
        ...     llm_model="gpt-4-turbo",
        ...     max_iterations=10,
        ...     max_execution_time=300
        ... )
        >>>
        >>> agent = ReActAgent(llm, tools, memory, config)
    """
```

#### Main Methods

##### `process()`

```python
def process(
    self,
    query: str,
    context: Optional[Dict[str, Any]] = None
) -> AgentResult:
    """
    Process query with multi-step reasoning.

    Args:
        query: User's question
        context: Optional context dictionary

    Returns:
        AgentResult with:
            - success: Whether processing succeeded
            - answer: Final answer string
            - reasoning_steps: List of ReasoningStep objects
            - tool_calls: List of ToolCall objects
            - execution_time: Total time in seconds
            - total_cost: Total cost in USD
            - metadata: Additional information
            - error: Error message if failed

    Raises:
        Never raises - all errors returned in AgentResult.error

    Example:
        >>> result = agent.process("What is 25 * 47 + sqrt(144)?")
        >>> print(result.answer)  # "1187"
        >>> print(f"Steps: {len(result.reasoning_steps)}")
        >>> print(f"Cost: ${result.total_cost:.4f}")
        >>>
        >>> # Check success
        >>> if result.success:
        ...     print(result.answer)
        ... else:
        ...     print(f"Error: {result.error}")
    """
```

##### `get_reasoning_trace()`

```python
def get_reasoning_trace(self) -> List[ReasoningStep]:
    """
    Get agent's reasoning steps for observability.

    Returns:
        List of ReasoningStep objects showing thought process

    Example:
        >>> result = agent.process("Calculate 25 * 47")
        >>> trace = agent.get_reasoning_trace()
        >>> for step in trace:
        ...     print(f"{step.step_type}: {step.content}")
    """
```

##### `reset()`

```python
def reset(self) -> None:
    """
    Reset agent state (clears reasoning trace).

    Example:
        >>> agent.reset()  # Clear for new session
    """
```

---

### QueryAnalyzer

**Purpose**: Analyze query characteristics and complexity.

**Location**: `src.components.query_processors.agents.planning.query_analyzer`

#### Class Definition

```python
class QueryAnalyzer:
    """Analyze query type and complexity."""
```

#### Main Methods

##### `analyze()`

```python
def analyze(self, query: str) -> QueryAnalysis:
    """
    Analyze query characteristics.

    Args:
        query: User's question

    Returns:
        QueryAnalysis with:
            - query_type: QueryType enum (SIMPLE, ANALYTICAL, CODE, RESEARCH, MULTI_STEP)
            - complexity: float (0.0-1.0 scale)
            - intent: str (e.g., "information_retrieval", "calculation")
            - entities: List[str] (extracted entities)
            - requires_tools: List[str] (predicted tool requirements)
            - estimated_steps: int (estimated reasoning steps)
            - metadata: Dict (additional analysis info)

    Example:
        >>> from src.components.query_processors.agents.planning import QueryAnalyzer
        >>>
        >>> analyzer = QueryAnalyzer()
        >>> analysis = analyzer.analyze("What is machine learning?")
        >>> print(analysis.query_type)  # QueryType.SIMPLE
        >>> print(analysis.complexity)  # 0.2
        >>>
        >>> analysis = analyzer.analyze("Calculate 25 * 47 and explain")
        >>> print(analysis.query_type)  # QueryType.ANALYTICAL
        >>> print(analysis.complexity)  # 0.8
        >>> print(analysis.requires_tools)  # ["calculator"]
    """
```

---

### QueryDecomposer

**Purpose**: Break complex queries into sub-tasks.

**Location**: `src.components.query_processors.agents.planning.query_decomposer`

#### Class Definition

```python
class QueryDecomposer:
    """Decompose complex queries into sub-tasks."""
```

#### Main Methods

##### `decompose()`

```python
def decompose(
    self,
    query: str,
    analysis: QueryAnalysis
) -> List[SubTask]:
    """
    Decompose query into sub-tasks.

    Args:
        query: User's question
        analysis: Query analysis from QueryAnalyzer

    Returns:
        List of SubTask objects with:
            - id: Unique task identifier
            - description: Task description
            - query: Sub-query string
            - required_tools: List[str] (tools needed)
            - dependencies: List[str] (prerequisite task IDs)
            - can_run_parallel: bool (parallel execution possible)
            - priority: int (lower = higher priority)
            - metadata: Dict (additional info)

    Example:
        >>> from src.components.query_processors.agents.planning import (
        ...     QueryAnalyzer, QueryDecomposer
        ... )
        >>>
        >>> analyzer = QueryAnalyzer()
        >>> decomposer = QueryDecomposer()
        >>>
        >>> query = "Search docs, analyze code, calculate metrics"
        >>> analysis = analyzer.analyze(query)
        >>> tasks = decomposer.decompose(query, analysis)
        >>>
        >>> for task in tasks:
        ...     print(f"Task: {task.description}")
        ...     print(f"  Tools: {task.required_tools}")
        ...     print(f"  Dependencies: {task.dependencies}")
        ...     print(f"  Parallel: {task.can_run_parallel}")
    """
```

---

### ExecutionPlanner

**Purpose**: Create optimized execution plans from sub-tasks.

**Location**: `src.components.query_processors.agents.planning.execution_planner`

#### Class Definition

```python
class ExecutionPlanner:
    """Create execution plan for query."""
```

#### Main Methods

##### `create_plan()`

```python
def create_plan(
    self,
    query: str,
    analysis: QueryAnalysis,
    sub_tasks: Optional[List[SubTask]] = None
) -> ExecutionPlan:
    """
    Create execution plan.

    Args:
        query: User's question
        analysis: Query analysis
        sub_tasks: Optional list of sub-tasks (from QueryDecomposer)

    Returns:
        ExecutionPlan with:
            - plan_id: Unique plan identifier
            - query: Original query
            - strategy: ExecutionStrategy (DIRECT, SEQUENTIAL, PARALLEL, HYBRID)
            - tasks: List[SubTask] (ordered tasks)
            - execution_graph: Dict (dependency graph)
            - estimated_time: float (seconds)
            - estimated_cost: float (USD)
            - metadata: Dict (additional info)

    Example:
        >>> from src.components.query_processors.agents.planning import (
        ...     QueryAnalyzer, QueryDecomposer, ExecutionPlanner
        ... )
        >>>
        >>> analyzer = QueryAnalyzer()
        >>> decomposer = QueryDecomposer()
        >>> planner = ExecutionPlanner()
        >>>
        >>> query = "Complex multi-step query"
        >>> analysis = analyzer.analyze(query)
        >>> tasks = decomposer.decompose(query, analysis)
        >>> plan = planner.create_plan(query, analysis, tasks)
        >>>
        >>> print(f"Strategy: {plan.strategy}")
        >>> print(f"Tasks: {len(plan.tasks)}")
        >>> print(f"Estimated time: {plan.estimated_time}s")
        >>> print(f"Estimated cost: ${plan.estimated_cost:.4f}")
    """
```

---

### PlanExecutor

**Purpose**: Execute execution plans using agent orchestration.

**Location**: `src.components.query_processors.agents.planning.plan_executor`

#### Class Definition

```python
class PlanExecutor:
    """Execute execution plan."""
```

#### Constructor

```python
def __init__(
    self,
    agent: BaseAgent,
    config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Initialize plan executor.

    Args:
        agent: Agent instance for task execution
        config: Optional configuration

    Example:
        >>> from src.components.query_processors.agents.planning import PlanExecutor
        >>>
        >>> executor = PlanExecutor(agent=my_agent)
    """
```

#### Main Methods

##### `execute()`

```python
def execute(
    self,
    plan: ExecutionPlan,
    agent: Optional[BaseAgent] = None
) -> ExecutionResult:
    """
    Execute plan with agent.

    Args:
        plan: Execution plan from ExecutionPlanner
        agent: Optional agent override

    Returns:
        ExecutionResult with:
            - success: bool (whether execution succeeded)
            - final_answer: str (aggregated answer)
            - task_results: Dict[str, Any] (results per task)
            - reasoning_trace: List[ReasoningStep]
            - execution_time: float (seconds)
            - total_cost: float (USD)
            - metadata: Dict (additional info)
            - error: Optional[str] (error message if failed)

    Example:
        >>> result = executor.execute(plan)
        >>> if result.success:
        ...     print(result.final_answer)
        ...     print(f"Time: {result.execution_time:.2f}s")
        ...     print(f"Cost: ${result.total_cost:.4f}")
        ... else:
        ...     print(f"Error: {result.error}")
    """
```

---

## Memory System

### ConversationMemory

**Purpose**: Manage conversation history for multi-turn interactions.

**Location**: `src.components.query_processors.agents.memory.conversation_memory`

#### Class Definition

```python
class ConversationMemory(BaseMemory):
    """Conversation history management with FIFO storage."""
```

#### Constructor

```python
def __init__(self, max_messages: int = 100) -> None:
    """
    Initialize conversation memory.

    Args:
        max_messages: Maximum messages to retain (FIFO)

    Example:
        >>> from src.components.query_processors.agents.memory import ConversationMemory
        >>>
        >>> memory = ConversationMemory(max_messages=50)
    """
```

#### Main Methods

##### `add_message()`

```python
def add_message(self, role: str, content: str) -> None:
    """
    Add message to conversation history.

    Args:
        role: Message role ("user", "assistant", "system")
        content: Message content

    Example:
        >>> memory.add_message("user", "What is machine learning?")
        >>> memory.add_message("assistant", "Machine learning is...")
    """
```

##### `get_messages()`

```python
def get_messages(self, last_n: Optional[int] = None) -> List[Message]:
    """
    Get conversation messages.

    Args:
        last_n: Optional number of recent messages to retrieve

    Returns:
        List of Message objects

    Example:
        >>> # Get all messages
        >>> messages = memory.get_messages()
        >>>
        >>> # Get last 10 messages
        >>> recent = memory.get_messages(last_n=10)
        >>>
        >>> for msg in recent:
        ...     print(f"{msg.role}: {msg.content}")
    """
```

##### `clear()`

```python
def clear(self) -> None:
    """
    Clear all messages from memory.

    Example:
        >>> memory.clear()  # New conversation
    """
```

##### `save()` / `load()`

```python
def save(self, filepath: str) -> None:
    """
    Persist memory to JSON file.

    Args:
        filepath: Path to save file

    Example:
        >>> memory.save("conversation.json")
    """

def load(self, filepath: str) -> None:
    """
    Load memory from JSON file.

    Args:
        filepath: Path to load file

    Example:
        >>> memory.load("conversation.json")
    """
```

---

### WorkingMemory

**Purpose**: Manage task execution context and intermediate state.

**Location**: `src.components.query_processors.agents.memory.working_memory`

#### Class Definition

```python
class WorkingMemory:
    """Task execution context storage."""
```

#### Constructor

```python
def __init__(self) -> None:
    """
    Initialize working memory.

    Example:
        >>> from src.components.query_processors.agents.memory import WorkingMemory
        >>>
        >>> working_mem = WorkingMemory()
    """
```

#### Main Methods

##### `set_context()` / `get_context()`

```python
def set_context(self, key: str, value: Any) -> None:
    """
    Set context variable.

    Args:
        key: Variable name
        value: Variable value (any type)

    Example:
        >>> working_mem.set_context("step_1_result", 1175)
        >>> working_mem.set_context("calculations", [25, 47, 1175])
    """

def get_context(self, key: str) -> Optional[Any]:
    """
    Get context variable.

    Args:
        key: Variable name

    Returns:
        Variable value or None if not found

    Example:
        >>> result = working_mem.get_context("step_1_result")
        >>> print(result)  # 1175
    """
```

##### `get_all_context()`

```python
def get_all_context(self) -> Dict[str, Any]:
    """
    Get all context variables.

    Returns:
        Dictionary of all context

    Example:
        >>> context = working_mem.get_all_context()
        >>> for key, value in context.items():
        ...     print(f"{key}: {value}")
    """
```

##### `clear()`

```python
def clear(self) -> None:
    """
    Clear all context variables.

    Example:
        >>> working_mem.clear()  # New task
    """
```

---

## Data Models

### AgentResult

**Purpose**: Result object from agent processing.

```python
@dataclass
class AgentResult:
    """Result from agent processing."""

    success: bool  # Whether processing succeeded
    answer: str  # Final answer
    reasoning_steps: List[ReasoningStep]  # Reasoning trace
    tool_calls: List[ToolCall]  # Tools called
    execution_time: float  # Total time (seconds)
    total_cost: float  # Total cost (USD)
    metadata: Dict[str, Any]  # Additional info
    error: Optional[str] = None  # Error message if failed
```

**Usage**:
```python
# Check success
if result.success:
    print(result.answer)
    print(f"Time: {result.execution_time:.2f}s")
    print(f"Cost: ${result.total_cost:.4f}")
else:
    print(f"Error: {result.error}")

# Examine reasoning
for step in result.reasoning_steps:
    print(f"{step.step_type}: {step.content}")
```

---

### QueryAnalysis

**Purpose**: Query analysis result.

```python
@dataclass
class QueryAnalysis:
    """Query analysis result."""

    query_type: QueryType  # SIMPLE, ANALYTICAL, CODE, RESEARCH, MULTI_STEP
    complexity: float  # 0.0-1.0 (0=simple, 1=complex)
    intent: str  # "information_retrieval", "calculation", etc.
    entities: List[str]  # Extracted entities
    requires_tools: List[str]  # Predicted tool requirements
    estimated_steps: int  # Estimated reasoning steps
    metadata: Dict[str, Any]  # Additional analysis
```

**QueryType Enum**:
```python
class QueryType(Enum):
    SIMPLE = "simple"  # Direct RAG retrieval
    RESEARCH = "research"  # Multi-document synthesis
    ANALYTICAL = "analytical"  # Computation/analysis
    CODE = "code"  # Code-related
    MULTI_STEP = "multi_step"  # Planning required
```

---

### ExecutionPlan

**Purpose**: Execution plan for complex queries.

```python
@dataclass
class ExecutionPlan:
    """Execution plan for query."""

    plan_id: str  # Unique identifier
    query: str  # Original query
    strategy: ExecutionStrategy  # DIRECT, SEQUENTIAL, PARALLEL, HYBRID
    tasks: List[SubTask]  # Ordered tasks
    execution_graph: Dict[str, List[str]]  # Dependency graph
    estimated_time: float  # Seconds
    estimated_cost: float  # USD
    metadata: Dict[str, Any]  # Additional info
```

**ExecutionStrategy Enum**:
```python
class ExecutionStrategy(Enum):
    DIRECT = "direct"  # Single RAG query
    SEQUENTIAL = "sequential"  # Sequential tool use
    PARALLEL = "parallel"  # Parallel execution
    HYBRID = "hybrid"  # Mixed strategy
```

---

### Configuration Models

#### ProcessorConfig

```python
@dataclass
class ProcessorConfig:
    """Intelligent processor configuration."""

    use_agent_by_default: bool = True  # Use agent when applicable
    complexity_threshold: float = 0.7  # Agent threshold
    max_agent_cost: float = 0.10  # Max cost per query (USD)
    enable_planning: bool = True  # Enable query planning
    enable_parallel_execution: bool = True  # Allow parallel tasks
```

#### AgentConfig

```python
@dataclass
class AgentConfig:
    """Agent configuration."""

    llm_provider: str  # "openai" or "anthropic"
    llm_model: str  # Model name
    temperature: float = 0.7  # LLM temperature
    max_tokens: int = 2048  # Max response tokens
    max_iterations: int = 10  # Max reasoning iterations
    max_execution_time: int = 300  # Max time (seconds)
    early_stopping: str = "force"  # Early stopping method
    verbose: bool = False  # Verbose logging
```

---

## Usage Examples

### Example 1: Simple RAG Query

```python
from src.components.query_processors import IntelligentQueryProcessor
from src.components.query_processors.agents import QueryAnalyzer
from src.components.query_processors.agents.models import ProcessorConfig

# Create processor
processor = IntelligentQueryProcessor(
    retriever=my_retriever,
    generator=my_generator,
    query_analyzer=QueryAnalyzer(),
    config=ProcessorConfig(complexity_threshold=0.7)
)

# Process simple query (routes to RAG)
answer = processor.process("What is machine learning?")
print(answer.answer)
print(f"Routing: {answer.metadata['routing_decision']}")  # "rag_pipeline"
```

### Example 2: Complex Query with Agent

```python
from src.components.query_processors import IntelligentQueryProcessor
from src.components.query_processors.agents import ReActAgent, QueryAnalyzer
from src.components.query_processors.agents.memory import ConversationMemory
from src.components.query_processors.agents.models import AgentConfig, ProcessorConfig
from src.components.query_processors.tools.implementations import CalculatorTool
from langchain_openai import ChatOpenAI

# Create agent
llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)
tools = [CalculatorTool()]
memory = ConversationMemory()
agent_config = AgentConfig(
    llm_provider="openai",
    llm_model="gpt-4-turbo",
    max_iterations=10
)
agent = ReActAgent(llm, tools, memory, agent_config)

# Create processor with agent
processor = IntelligentQueryProcessor(
    retriever=my_retriever,
    generator=my_generator,
    agent=agent,
    query_analyzer=QueryAnalyzer(),
    config=ProcessorConfig()
)

# Process complex query (routes to agent)
answer = processor.process("Calculate 25 * 47 and explain the steps")
print(answer.answer)
print(f"Routing: {answer.metadata['routing_decision']}")  # "agent_system"
print(f"Cost: ${answer.metadata['total_cost']:.4f}")
print(f"Reasoning steps: {len(answer.metadata['reasoning_trace'])}")
```

### Example 3: Multi-Step Planning

```python
from src.components.query_processors.agents.planning import (
    QueryAnalyzer,
    QueryDecomposer,
    ExecutionPlanner,
    PlanExecutor
)

# Analyze query
analyzer = QueryAnalyzer()
query = "Search for Python docs, analyze code examples, calculate metrics"
analysis = analyzer.analyze(query)

# Decompose into tasks
decomposer = QueryDecomposer()
tasks = decomposer.decompose(query, analysis)
print(f"Tasks: {len(tasks)}")
for task in tasks:
    print(f"  - {task.description}")

# Create execution plan
planner = ExecutionPlanner()
plan = planner.create_plan(query, analysis, tasks)
print(f"Strategy: {plan.strategy}")
print(f"Estimated time: {plan.estimated_time}s")
print(f"Estimated cost: ${plan.estimated_cost:.4f}")

# Execute plan
executor = PlanExecutor(agent=my_agent)
result = executor.execute(plan)
if result.success:
    print(result.final_answer)
```

### Example 4: Memory Persistence

```python
from src.components.query_processors.agents.memory import ConversationMemory

# Create memory
memory = ConversationMemory(max_messages=50)

# Multi-turn conversation
memory.add_message("user", "What is 25 * 47?")
memory.add_message("assistant", "1175")
memory.add_message("user", "Add 100 to that")
memory.add_message("assistant", "1275")

# Retrieve context
messages = memory.get_messages(last_n=4)
for msg in messages:
    print(f"{msg.role}: {msg.content}")

# Save for later
memory.save("conversation.json")

# Load in new session
new_memory = ConversationMemory()
new_memory.load("conversation.json")
```

### Example 5: Cost Budget Enforcement

```python
from src.components.query_processors.agents.models import ProcessorConfig

# Low budget configuration
config = ProcessorConfig(
    complexity_threshold=0.7,
    max_agent_cost=0.01  # Very low budget
)

processor = IntelligentQueryProcessor(
    retriever=my_retriever,
    generator=my_generator,
    agent=my_agent,
    query_analyzer=QueryAnalyzer(),
    config=config
)

# Expensive query falls back to RAG
answer = processor.process("Complex expensive multi-tool query")
if answer.metadata.get("cost_exceeded"):
    print("Budget exceeded, used RAG fallback")
```

---

## Error Handling

### Exception Hierarchy

```python
AgentError  # Base exception
├── PlanningError  # Query planning failures
├── ExecutionError  # Execution failures
│   └── ToolExecutionTimeoutError  # Tool timeout
├── MemoryError  # Memory operation failures
├── ConfigurationError  # Configuration issues
├── AnalysisError  # Analysis failures
└── DecompositionError  # Decomposition failures
```

### Error Handling Pattern

```python
from src.components.query_processors.agents.base_agent import AgentError

try:
    result = processor.process("Complex query")
    if result.metadata.get("agent_failed"):
        print("Agent failed, fallback used")
except AgentError as e:
    print(f"Agent error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### AgentResult Error Pattern

**Note**: Agent methods NEVER raise exceptions. All errors are returned in `AgentResult.error`.

```python
# Correct pattern
result = agent.process("Query that might fail")
if result.success:
    print(result.answer)
else:
    print(f"Error: {result.error}")

# NOT needed (no exceptions raised)
# try:
#     result = agent.process(query)
# except Exception as e:
#     ...
```

---

## API Versioning

**Current Version**: 1.0

**Backward Compatibility**:
- All Phase 2 APIs are 100% backward compatible
- Can use IntelligentQueryProcessor without agent components
- Existing QueryProcessor interface fully preserved
- No breaking changes from Phase 1

**Future Versions**:
- Minor versions (1.1, 1.2) will maintain backward compatibility
- Major versions (2.0) may introduce breaking changes with deprecation warnings

---

**Document Version**: 1.0
**Last Updated**: November 18, 2025
**Status**: ✅ Complete
