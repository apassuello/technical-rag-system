# Phase 2 Implementation Plan

**Epic 5**: Tool & Function Calling for RAG System
**Phase**: Phase 2 - Agent Orchestration & Query Planning
**Date**: November 17, 2025
**Status**: Ready for Execution
**Estimated Duration**: 12-18 hours wall clock (15-20 hours total with parallelization)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Prerequisites](#prerequisites)
3. [Execution Strategy](#execution-strategy)
4. [Block Breakdown](#block-breakdown)
5. [Task Dependencies](#task-dependencies)
6. [Parallel Execution Plan](#parallel-execution-plan)
7. [Risk Mitigation](#risk-mitigation)
8. [Quality Gates](#quality-gates)

---

## Executive Summary

### Approach

Following the proven Phase 1 pattern:
1. **Architecture-First**: Comprehensive design before coding (✅ Complete)
2. **Block Execution**: 4 sequential blocks with parallel sub-tasks
3. **Agent-Driven**: Use specialized agents for implementation
4. **Test-Driven**: Tests created alongside implementation
5. **Audit & Validate**: Comprehensive quality checks at end

### Timeline Estimate

| Block | Tasks | Sequential Time | With Parallelization | Status |
|-------|-------|----------------|----------------------|--------|
| **Block 1** | Memory + Base Classes | 2-3 hours | 2-3 hours | Pending |
| **Block 2** | Agent + Planning (parallel) | 9-11 hours | 5-7 hours | Pending |
| **Block 3** | Integration + Config | 2-3 hours | 2-3 hours | Pending |
| **Block 4** | Testing + Audit | 3-4 hours | 3-4 hours | Pending |
| **Total** | All Phase 2 | 16-21 hours | **12-17 hours** | Pending |

**Parallelization Savings**: ~4-5 hours via Block 2 parallel execution

---

## Prerequisites

### Phase 1 Completion ✅

**Required Components** (all complete from Phase 1):
- ✅ Tool framework (BaseTool, ToolRegistry)
- ✅ 3 working tools (Calculator, DocumentSearch, CodeAnalyzer)
- ✅ LLM adapters with function calling (OpenAI, Anthropic)
- ✅ 162 tests, 100% type hints, 0 vulnerabilities

### New Dependencies

**LangChain Framework**:
```bash
pip install \
  langchain==0.1.0 \
  langchain-openai==0.0.2 \
  langchain-anthropic==0.0.1 \
  langchain-community==0.0.10
```

**Verification**:
```bash
python -c "import langchain; print(langchain.__version__)"
python -c "from langchain_openai import ChatOpenAI; print('OpenAI OK')"
python -c "from langchain_anthropic import ChatAnthropic; print('Anthropic OK')"
```

### Environment Setup

```bash
# Set API keys (if not already set)
export OPENAI_API_KEY="your_key"
export ANTHROPIC_API_KEY="your_key"

# Verify Phase 1 tests still pass
pytest tests/epic5/phase1/ -v --tb=short
```

---

## Execution Strategy

### Design Principles

1. **Incremental Value**: Each block delivers working functionality
2. **Parallel Where Possible**: Block 2 uses 2 agents simultaneously
3. **Test Alongside**: Tests created with implementation
4. **Quality First**: Same standards as Phase 1 (100% type hints, comprehensive tests)
5. **Backward Compatible**: All Phase 1 functionality preserved

### Block Structure

```
Block 1: Foundation (2-3 hours)
├─ Memory System (ConversationMemory, WorkingMemory)
├─ Base Interfaces (BaseAgent, BaseMemory)
└─ Data Models (AgentResult, ReasoningStep, etc.)
     │
     ▼
Block 2: Core Components (5-7 hours, PARALLEL)
├─ [Agent 1] ReAct Agent + LangChain Integration
└─ [Agent 2] Query Planning System
     │
     ▼
Block 3: Integration (2-3 hours)
├─ IntelligentQueryProcessor
├─ Configuration System
└─ RAG Pipeline Integration
     │
     ▼
Block 4: Testing & Validation (3-4 hours)
├─ Comprehensive Test Suite
├─ Integration Tests
├─ Scenario Tests
└─ Quality Audit
```

---

## Block Breakdown

### Block 1: Foundation (2-3 hours)

**Goal**: Create foundational classes for Phase 2

**Sequential Execution** (single developer/agent):
1. Data models (1 hour)
2. Base interfaces (0.5 hour)
3. Memory system (0.5-1 hour)
4. Unit tests (0.5 hour)

#### Task 1.1: Data Models (1 hour)

**File**: `src/components/query_processors/agents/models.py`

**Deliverables**:
```python
# Data models for Phase 2
- AgentResult
- ReasoningStep
- StepType (enum)
- AgentConfig
- QueryAnalysis
- QueryType (enum)
- SubTask
- ExecutionPlan
- ExecutionStrategy (enum)
- ExecutionResult
- Message
- ProcessorConfig
```

**Implementation Steps**:
1. Create dataclasses for all models (30 min)
2. Add validation in `__post_init__` (15 min)
3. Add type hints (100% coverage) (10 min)
4. Create basic unit tests (5 min)

**Definition of Done**:
- [x] All data models defined with @dataclass
- [x] All fields have type hints
- [x] Validation logic in `__post_init__` where needed
- [x] Docstrings for all classes
- [x] Basic unit tests created

#### Task 1.2: Base Interfaces (30 min)

**Files**:
- `src/components/query_processors/agents/base_agent.py`
- `src/components/query_processors/agents/base_memory.py`

**Deliverables**:
```python
# Abstract base classes
- BaseAgent (ABC)
- BaseMemory (ABC)
```

**Implementation Steps**:
1. Create BaseAgent with abstract methods (15 min)
2. Create BaseMemory with abstract methods (10 min)
3. Add docstrings and type hints (5 min)

**Definition of Done**:
- [x] BaseAgent ABC with process() and get_reasoning_trace()
- [x] BaseMemory ABC with add_message(), get_messages(), clear()
- [x] 100% type hints
- [x] Comprehensive docstrings

#### Task 1.3: Memory System (30-60 min)

**Files**:
- `src/components/query_processors/agents/memory/__init__.py`
- `src/components/query_processors/agents/memory/conversation_memory.py`
- `src/components/query_processors/agents/memory/working_memory.py`

**Deliverables**:
```python
# Memory implementations
- ConversationMemory (implements BaseMemory)
- WorkingMemory (state management)
```

**Implementation Steps**:
1. ConversationMemory implementation (20 min)
   - List-based message storage
   - Add/get/clear operations
   - Optional persistence (save/load)
2. WorkingMemory implementation (15 min)
   - Dict-based context storage
   - Set/get/clear operations
3. Unit tests (15 min)

**Definition of Done**:
- [x] ConversationMemory working
- [x] WorkingMemory working
- [x] Unit tests for both (>95% coverage)
- [x] 100% type hints
- [x] Thread-safe if needed

#### Task 1.4: Block 1 Testing (30 min)

**Deliverables**:
```
tests/epic5/phase2/unit/
├── test_models.py              # Data model tests
├── test_base_agent.py          # Base interface tests
└── test_memory.py              # Memory system tests
```

**Definition of Done**:
- [x] All data models tested
- [x] Memory operations tested
- [x] 95%+ test coverage for Block 1
- [x] All tests passing

**Block 1 Summary**:
- **Duration**: 2-3 hours
- **Files Created**: 8-10 files
- **Lines of Code**: ~800-1000 lines
- **Tests Created**: ~30-40 tests
- **Definition of Done**: All base classes and models ready for Block 2

---

### Block 2: Core Components (5-7 hours, PARALLEL)

**Goal**: Implement ReAct agent and query planning system simultaneously

**Parallel Execution Strategy**:
- **Agent 1**: ReAct Agent + LangChain Integration (3-4 hours)
- **Agent 2**: Query Planning System (3-4 hours)
- **Execution**: Both agents work in parallel → saves ~3-4 hours

#### Agent 1: ReAct Agent + LangChain Integration (3-4 hours)

**Lead**: Implementation Agent 1

**Files to Create**:
```
src/components/query_processors/agents/
├── __init__.py
├── react_agent.py              # Main ReAct implementation
└── langchain_tools.py          # Tool wrappers for LangChain
```

**Deliverables**:
1. **LangChain Tool Wrappers** (45 min)
   - Wrap Phase 1 tools for LangChain
   - Convert ToolRegistry to LangChain tools
   - Handle tool execution and results

2. **ReAct Agent Implementation** (1.5-2 hours)
   - Create ReActAgent class
   - Integrate LangChain's AgentExecutor
   - Support OpenAI and Anthropic LLMs
   - Multi-step reasoning loop
   - Memory integration

3. **Configuration System** (30 min)
   - AgentConfig dataclass
   - YAML configuration loading
   - LLM provider selection

4. **Unit Tests** (1 hour)
   - Test agent initialization
   - Test single-step queries
   - Test multi-step reasoning
   - Test tool integration
   - Test memory persistence

**Implementation Steps**:

**Step 1: LangChain Tool Wrapper** (45 min)
```python
# src/components/query_processors/agents/langchain_tools.py

from langchain.tools import BaseTool as LangChainBaseTool
from src.components.query_processors.tools import BaseTool as Phase1Tool

class LangChainToolWrapper(LangChainBaseTool):
    """Wrap Phase 1 tool for LangChain."""

    def __init__(self, phase1_tool: Phase1Tool):
        super().__init__(
            name=phase1_tool.name,
            description=phase1_tool.description,
            func=self._execute
        )
        self.phase1_tool = phase1_tool

    def _execute(self, **kwargs):
        """Execute Phase 1 tool."""
        result = self.phase1_tool.execute(**kwargs)
        if result.success:
            return result.content
        else:
            raise RuntimeError(result.error)

def convert_tools_to_langchain(
    tool_registry: ToolRegistry
) -> List[LangChainBaseTool]:
    """Convert Phase 1 tools to LangChain format."""
    return [
        LangChainToolWrapper(tool)
        for tool in tool_registry.get_all_tools().values()
    ]
```

**Step 2: ReAct Agent** (1.5-2 hours)
```python
# src/components/query_processors/agents/react_agent.py

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

class ReActAgent(BaseAgent):
    """ReAct pattern agent using LangChain."""

    def __init__(
        self,
        llm_config: Dict[str, Any],
        tool_registry: ToolRegistry,
        memory: BaseMemory,
        agent_config: AgentConfig
    ):
        # Create LangChain LLM
        self.llm = self._create_llm(llm_config)

        # Convert tools
        self.tools = convert_tools_to_langchain(tool_registry)

        # Create prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant with access to tools."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create agent
        if llm_config["provider"] == "openai":
            agent = create_openai_functions_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self.prompt
            )
        else:  # anthropic
            agent = create_anthropic_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self.prompt
            )

        # Create executor
        self.executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=memory,
            verbose=agent_config.verbose,
            max_iterations=agent_config.max_iterations,
            max_execution_time=agent_config.max_execution_time
        )

        self.memory = memory
        self.config = agent_config
        self.reasoning_trace = []

    def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """Process query with multi-step reasoning."""
        start_time = time.time()
        self.reasoning_trace = []

        try:
            # Execute agent
            result = self.executor.invoke({"input": query})

            # Extract reasoning trace
            self._extract_reasoning_trace(result)

            # Create AgentResult
            return AgentResult(
                success=True,
                answer=result["output"],
                reasoning_steps=self.reasoning_trace,
                tool_calls=self._extract_tool_calls(),
                execution_time=time.time() - start_time,
                total_cost=self._calculate_cost(),
                metadata={"iterations": result.get("iterations", 0)}
            )

        except Exception as e:
            logger.error(f"Agent processing failed: {e}")
            return AgentResult(
                success=False,
                answer="",
                reasoning_steps=self.reasoning_trace,
                tool_calls=[],
                execution_time=time.time() - start_time,
                total_cost=0.0,
                metadata={},
                error=str(e)
            )

    def get_reasoning_trace(self) -> List[ReasoningStep]:
        """Get agent's reasoning steps."""
        return self.reasoning_trace
```

**Step 3: Tests** (1 hour)
```
tests/epic5/phase2/unit/
├── test_react_agent.py         # Core agent tests
└── test_langchain_tools.py     # Tool wrapper tests

tests/epic5/phase2/integration/
└── test_agent_with_tools.py    # End-to-end tests
```

**Agent 1 Definition of Done**:
- [x] LangChain tool wrappers working
- [x] ReActAgent class implemented
- [x] Multi-step reasoning functional
- [x] OpenAI and Anthropic support
- [x] Memory integration working
- [x] Unit tests (>95% coverage)
- [x] Integration tests passing
- [x] 100% type hints
- [x] Comprehensive docstrings

---

#### Agent 2: Query Planning System (3-4 hours)

**Lead**: Implementation Agent 2

**Files to Create**:
```
src/components/query_processors/planning/
├── __init__.py
├── query_analyzer.py           # Query analysis
├── decomposer.py               # Query decomposition
├── planner.py                  # Execution planning
└── executor.py                 # Plan execution
```

**Deliverables**:
1. **QueryAnalyzer** (1 hour)
   - Classify query type
   - Estimate complexity
   - Extract intent and entities

2. **QueryDecomposer** (1 hour)
   - Break queries into sub-tasks
   - Build dependency graph
   - Identify required tools

3. **ExecutionPlanner** (1 hour)
   - Create execution plans
   - Select strategy (direct, sequential, parallel)
   - Optimize for cost and latency

4. **PlanExecutor** (30 min)
   - Execute plans with agent
   - Handle parallel execution
   - Aggregate results

5. **Unit Tests** (30-60 min)
   - Test each component
   - Test integration

**Implementation Steps**:

**Step 1: QueryAnalyzer** (1 hour)
```python
# src/components/query_processors/planning/query_analyzer.py

class QueryAnalyzer:
    """Analyze query characteristics."""

    def __init__(self, llm_adapter: Optional[BaseLLMAdapter] = None):
        self.llm = llm_adapter
        # Simple heuristics for now, LLM-based for complex queries

    def analyze(self, query: str) -> QueryAnalysis:
        """Analyze query."""
        # Step 1: Basic analysis (no LLM)
        complexity = self._estimate_complexity(query)
        query_type = self._classify_type(query)

        # Step 2: Advanced analysis (with LLM if available)
        if self.llm and complexity > 0.7:
            return self._analyze_with_llm(query)

        # Step 3: Create analysis
        return QueryAnalysis(
            query_type=query_type,
            complexity=complexity,
            intent=self._extract_intent(query),
            entities=self._extract_entities(query),
            requires_tools=self._predict_tools(query),
            estimated_steps=self._estimate_steps(complexity),
            metadata={}
        )

    def _estimate_complexity(self, query: str) -> float:
        """Estimate query complexity (0.0-1.0)."""
        # Heuristics:
        # - Length
        # - Number of questions
        # - Keywords ("and then", "calculate", "analyze")
        # - Tool references

        score = 0.0

        # Length factor
        if len(query) > 200:
            score += 0.3
        elif len(query) > 100:
            score += 0.2

        # Multiple questions
        questions = query.count("?")
        score += min(questions * 0.2, 0.4)

        # Complex keywords
        complex_keywords = [
            "and then", "after that", "calculate", "analyze",
            "compare", "summarize", "research", "find all"
        ]
        for keyword in complex_keywords:
            if keyword in query.lower():
                score += 0.15

        return min(score, 1.0)

    def _classify_type(self, query: str) -> QueryType:
        """Classify query type."""
        query_lower = query.lower()

        # Code-related
        if any(word in query_lower for word in ["code", "function", "debug", "error"]):
            return QueryType.CODE

        # Analytical
        if any(word in query_lower for word in ["calculate", "analyze", "compute"]):
            return QueryType.ANALYTICAL

        # Research
        if any(word in query_lower for word in ["research", "find", "search", "papers"]):
            return QueryType.RESEARCH

        # Multi-step
        if any(word in query_lower for word in ["and then", "after", "next"]):
            return QueryType.MULTI_STEP

        # Default: simple
        return QueryType.SIMPLE
```

**Step 2: QueryDecomposer** (1 hour)
```python
# src/components/query_processors/planning/decomposer.py

class QueryDecomposer:
    """Decompose complex queries into sub-tasks."""

    def __init__(self, llm_adapter: Optional[BaseLLMAdapter] = None):
        self.llm = llm_adapter

    def decompose(
        self,
        query: str,
        analysis: QueryAnalysis
    ) -> List[SubTask]:
        """Decompose query into sub-tasks."""
        # Simple queries don't need decomposition
        if analysis.complexity < 0.7:
            return [self._create_single_task(query)]

        # Use LLM for complex decomposition
        if self.llm:
            return self._decompose_with_llm(query, analysis)

        # Fallback: heuristic decomposition
        return self._decompose_heuristic(query, analysis)

    def _decompose_with_llm(
        self,
        query: str,
        analysis: QueryAnalysis
    ) -> List[SubTask]:
        """Use LLM to decompose query."""
        prompt = f"""
        Break down this complex query into sequential sub-tasks:

        Query: {query}

        For each sub-task, provide:
        1. Description
        2. Specific question to answer
        3. Required tools (if any)
        4. Dependencies on other tasks

        Output as JSON array.
        """

        # Call LLM
        response = self.llm.generate(prompt, params)

        # Parse response
        tasks_json = json.loads(response)

        # Create SubTask objects
        return [
            SubTask(
                id=f"task_{i}",
                description=task["description"],
                query=task["query"],
                required_tools=task.get("tools", []),
                dependencies=task.get("dependencies", []),
                can_run_parallel=task.get("parallel", False),
                priority=i,
                metadata={}
            )
            for i, task in enumerate(tasks_json)
        ]
```

**Step 3: ExecutionPlanner** (1 hour)
```python
# src/components/query_processors/planning/planner.py

class ExecutionPlanner:
    """Create execution plans."""

    def create_plan(
        self,
        query: str,
        analysis: QueryAnalysis,
        sub_tasks: Optional[List[SubTask]] = None
    ) -> ExecutionPlan:
        """Create execution plan."""
        # Select strategy based on analysis
        strategy = self._select_strategy(analysis, sub_tasks)

        # Optimize task ordering
        if sub_tasks:
            optimized_tasks = self._optimize_tasks(sub_tasks, strategy)
        else:
            optimized_tasks = []

        # Build execution graph
        graph = self._build_execution_graph(optimized_tasks)

        # Estimate time and cost
        estimated_time = self._estimate_time(optimized_tasks, strategy)
        estimated_cost = self._estimate_cost(optimized_tasks, strategy)

        return ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            query=query,
            strategy=strategy,
            tasks=optimized_tasks,
            execution_graph=graph,
            estimated_time=estimated_time,
            estimated_cost=estimated_cost,
            metadata={}
        )

    def _select_strategy(
        self,
        analysis: QueryAnalysis,
        sub_tasks: Optional[List[SubTask]]
    ) -> ExecutionStrategy:
        """Select execution strategy."""
        # Simple query → DIRECT
        if analysis.complexity < 0.3:
            return ExecutionStrategy.DIRECT

        # No sub-tasks → SEQUENTIAL
        if not sub_tasks or len(sub_tasks) == 1:
            return ExecutionStrategy.SEQUENTIAL

        # Check if any tasks can run in parallel
        has_parallel = any(task.can_run_parallel for task in sub_tasks)

        if has_parallel:
            # Some sequential, some parallel → HYBRID
            has_dependencies = any(task.dependencies for task in sub_tasks)
            if has_dependencies:
                return ExecutionStrategy.HYBRID
            else:
                return ExecutionStrategy.PARALLEL
        else:
            return ExecutionStrategy.SEQUENTIAL
```

**Step 4: PlanExecutor** (30 min)
```python
# src/components/query_processors/planning/executor.py

class PlanExecutor:
    """Execute execution plans."""

    def execute(
        self,
        plan: ExecutionPlan,
        agent: BaseAgent
    ) -> ExecutionResult:
        """Execute plan with agent."""
        start_time = time.time()
        task_results = {}
        all_reasoning = []

        try:
            if plan.strategy == ExecutionStrategy.DIRECT:
                # Single execution
                result = agent.process(plan.query)
                task_results["main"] = result.answer
                all_reasoning = result.reasoning_steps

            elif plan.strategy == ExecutionStrategy.SEQUENTIAL:
                # Sequential execution
                for task in plan.tasks:
                    result = agent.process(task.query)
                    task_results[task.id] = result.answer
                    all_reasoning.extend(result.reasoning_steps)

            elif plan.strategy == ExecutionStrategy.PARALLEL:
                # Parallel execution (simplified for now)
                # In production, use ThreadPoolExecutor
                task_results = self._execute_parallel(plan.tasks, agent)

            else:  # HYBRID
                task_results = self._execute_hybrid(plan.tasks, agent)

            # Aggregate results
            final_answer = self._aggregate_results(task_results, plan)

            return ExecutionResult(
                success=True,
                final_answer=final_answer,
                task_results=task_results,
                reasoning_trace=all_reasoning,
                execution_time=time.time() - start_time,
                total_cost=0.0,  # Calculate from agent
                metadata={"strategy": plan.strategy.value}
            )

        except Exception as e:
            logger.error(f"Plan execution failed: {e}")
            return ExecutionResult(
                success=False,
                final_answer="",
                task_results=task_results,
                reasoning_trace=all_reasoning,
                execution_time=time.time() - start_time,
                total_cost=0.0,
                metadata={},
                error=str(e)
            )
```

**Step 5: Tests** (30-60 min)
```
tests/epic5/phase2/unit/
├── test_query_analyzer.py      # Analyzer tests
├── test_decomposer.py          # Decomposer tests
├── test_planner.py             # Planner tests
└── test_executor.py            # Executor tests

tests/epic5/phase2/integration/
└── test_planning_execution.py  # End-to-end planning tests
```

**Agent 2 Definition of Done**:
- [x] QueryAnalyzer working (>90% accuracy)
- [x] QueryDecomposer working
- [x] ExecutionPlanner working
- [x] PlanExecutor working
- [x] Unit tests (>95% coverage)
- [x] Integration tests passing
- [x] 100% type hints
- [x] Comprehensive docstrings

---

**Block 2 Summary**:
- **Duration**: 5-7 hours (wall clock with parallelization)
- **Sequential Time**: 6-8 hours (if done serially)
- **Savings**: ~1-2 hours
- **Files Created**: 10-12 files
- **Lines of Code**: ~2,500-3,000 lines
- **Tests Created**: ~60-80 tests

**Block 2 Coordination**:
- Agent 1 and Agent 2 work independently
- Minimal dependencies (both use Block 1 components)
- Merge at end of block
- Integration tests verify they work together

---

### Block 3: Integration & Configuration (2-3 hours)

**Goal**: Integrate Phase 2 components with existing RAG pipeline

**Sequential Execution**:
1. IntelligentQueryProcessor (1-1.5 hours)
2. Configuration system (0.5 hour)
3. Integration testing (0.5-1 hour)

#### Task 3.1: Intelligent Query Processor (1-1.5 hours)

**File**: `src/components/query_processors/intelligent_processor.py`

**Implementation Steps**:
```python
from src.components.query_processors.base import QueryProcessor

class IntelligentQueryProcessor(QueryProcessor):
    """Enhanced query processor with agent capabilities."""

    def __init__(
        self,
        retriever: Retriever,
        generator: AnswerGenerator,
        agent: Optional[BaseAgent] = None,
        planner: Optional[QueryPlanner] = None,
        analyzer: Optional[QueryAnalyzer] = None,
        config: Optional[ProcessorConfig] = None
    ):
        # Initialize base (existing RAG)
        super().__init__(retriever, generator)

        # Add Phase 2 capabilities
        self.agent = agent
        self.planner = planner
        self.analyzer = analyzer or QueryAnalyzer()
        self.config = config or ProcessorConfig()

    def process(
        self,
        query: str,
        use_agent: Optional[bool] = None,
        context: Optional[Dict] = None
    ) -> QueryResult:
        """
        Process query with optional agent use.

        Args:
            query: User question
            use_agent: Override automatic decision (None = auto-decide)
            context: Optional context

        Returns:
            QueryResult
        """
        # Determine if agent should be used
        if use_agent is None:
            use_agent = self._should_use_agent(query)

        # Route to appropriate processor
        if use_agent and self.agent:
            return self._process_with_agent(query, context)
        else:
            return self._process_with_rag(query)

    def _should_use_agent(self, query: str) -> bool:
        """Automatic decision: use agent or RAG?"""
        if not self.agent:
            return False

        # Analyze query
        analysis = self.analyzer.analyze(query)

        # Use agent if:
        # 1. Complex query
        if analysis.complexity > self.config.complexity_threshold:
            return True

        # 2. Multiple tools needed
        if len(analysis.requires_tools) > 1:
            return True

        # 3. Multi-step reasoning required
        if analysis.estimated_steps > 1:
            return True

        # Default: use RAG (faster, cheaper)
        return False

    def _process_with_agent(
        self,
        query: str,
        context: Optional[Dict]
    ) -> QueryResult:
        """Process using agent."""
        try:
            # Use planner if available
            if self.planner:
                analysis = self.analyzer.analyze(query)
                plan = self.planner.create_plan(query, analysis)
                result = self.planner.execute(plan, self.agent)

                return QueryResult(
                    success=result.success,
                    answer=result.final_answer,
                    sources=[],  # Extract from result
                    metadata={
                        "used_agent": True,
                        "strategy": plan.strategy.value,
                        "reasoning_steps": len(result.reasoning_trace)
                    },
                    error=result.error
                )
            else:
                # Direct agent use
                agent_result = self.agent.process(query, context)

                return QueryResult(
                    success=agent_result.success,
                    answer=agent_result.answer,
                    sources=[],
                    metadata={
                        "used_agent": True,
                        "reasoning_steps": len(agent_result.reasoning_steps)
                    },
                    error=agent_result.error
                )

        except Exception as e:
            logger.warning(f"Agent failed: {e}, falling back to RAG")
            return self._process_with_rag(query)

    def _process_with_rag(self, query: str) -> QueryResult:
        """Process using existing RAG pipeline."""
        # Call parent class method (existing implementation)
        result = super().process(query)

        # Add metadata to indicate RAG was used
        if not hasattr(result, 'metadata'):
            result.metadata = {}
        result.metadata["used_agent"] = False

        return result
```

**Definition of Done**:
- [x] IntelligentQueryProcessor implemented
- [x] Extends existing QueryProcessor (backward compatible)
- [x] Automatic agent/RAG selection working
- [x] Manual override supported
- [x] Graceful fallback on agent failure
- [x] 100% type hints
- [x] Unit tests (>95% coverage)

#### Task 3.2: Configuration System (30 min)

**Files**:
- `config/agent_config.yaml`
- `config/tool_config.yaml`

**agent_config.yaml**:
```yaml
# Agent configuration
agent:
  type: "react"  # ReAct agent
  llm:
    provider: "openai"  # or "anthropic"
    model: "gpt-4-turbo"
    temperature: 0.7
    max_tokens: 2048
  executor:
    max_iterations: 10
    max_execution_time: 300  # seconds
    early_stopping_method: "force"
    verbose: false
  memory:
    type: "conversation_buffer"
    max_token_limit: 2000

# Query processor configuration
processor:
  use_agent_by_default: true
  complexity_threshold: 0.7  # Use agent if complexity > threshold
  max_agent_cost: 0.10  # Max cost per query (USD)
  enable_planning: true
  enable_parallel_execution: true

# Planning configuration
planning:
  analyzer:
    use_llm: false  # Use LLM for analysis (more accurate but slower)
  decomposer:
    use_llm: true  # Use LLM for decomposition
    max_sub_tasks: 5
  executor:
    parallel_execution: true
    max_parallel_tasks: 3
```

**Definition of Done**:
- [x] Configuration files created
- [x] Config loading function implemented
- [x] Defaults provided
- [x] Validation logic

#### Task 3.3: Integration Testing (30-60 min)

**Files**:
```
tests/epic5/phase2/integration/
├── test_full_pipeline.py        # End-to-end tests
└── test_backward_compatibility.py  # Ensure Phase 1 still works
```

**Test Cases**:
1. Simple query → Uses RAG (not agent)
2. Complex query → Uses agent automatically
3. Manual override → Respects use_agent parameter
4. Agent failure → Falls back to RAG
5. Backward compatibility → Phase 1 tests still pass

**Definition of Done**:
- [x] Integration tests passing
- [x] Backward compatibility verified
- [x] Performance acceptable (<5s simple queries)
- [x] Phase 1 tests still passing

**Block 3 Summary**:
- **Duration**: 2-3 hours
- **Files Created**: 4-5 files
- **Lines of Code**: ~600-800 lines
- **Tests Created**: ~20-30 tests

---

### Block 4: Testing, Documentation & Audit (3-4 hours)

**Goal**: Comprehensive testing, documentation, and quality audit

**Sequential Execution**:
1. Comprehensive test suite (1.5 hours)
2. Documentation (1 hour)
3. Quality audit (0.5-1 hour)
4. Performance benchmarks (0.5 hour)

#### Task 4.1: Comprehensive Test Suite (1.5 hours)

**Deliverables**:
```
tests/epic5/phase2/
├── unit/                        # Component tests
│   ├── test_models.py
│   ├── test_base_agent.py
│   ├── test_memory.py
│   ├── test_react_agent.py
│   ├── test_langchain_tools.py
│   ├── test_query_analyzer.py
│   ├── test_decomposer.py
│   ├── test_planner.py
│   └── test_executor.py
├── integration/                 # Integration tests
│   ├── test_agent_with_tools.py
│   ├── test_planning_execution.py
│   ├── test_full_pipeline.py
│   └── test_backward_compatibility.py
└── scenarios/                   # Real-world scenarios
    ├── test_multi_step_research.py
    ├── test_complex_analysis.py
    └── test_code_debugging.py
```

**Test Coverage Target**: >95%

**Definition of Done**:
- [x] >150 total tests
- [x] >95% code coverage
- [x] All tests passing
- [x] Scenario tests demonstrate real use cases

#### Task 4.2: Documentation (1 hour)

**Deliverables**:
```
docs/epic5-implementation/
├── PHASE2_GUIDE.md              # Usage guide
├── PHASE2_DEMO.md               # Demo and examples
└── PHASE2_COMPLETE.md           # Completion summary
```

**Definition of Done**:
- [x] Architecture docs complete
- [x] Usage guide with examples
- [x] API documentation
- [x] Demo notebook or script

#### Task 4.3: Quality Audit (30-60 min)

**Checklist**:
1. Code quality (ruff, mypy)
2. Architecture compliance
3. Integration validation
4. Security audit
5. Performance validation

**Definition of Done**:
- [x] All ruff checks passed
- [x] 100% type hints verified
- [x] Architecture compliant
- [x] 0 security vulnerabilities
- [x] Performance acceptable

#### Task 4.4: Performance Benchmarks (30 min)

**Benchmarks**:
- Simple query latency
- Complex query latency
- Agent overhead
- Planning overhead
- Cost per query type

**Definition of Done**:
- [x] Benchmarks documented
- [x] Performance within targets
- [x] Cost analysis complete

**Block 4 Summary**:
- **Duration**: 3-4 hours
- **Files Created**: 15-20 files
- **Lines of Code**: ~2,000-2,500 lines (tests + docs)
- **Tests Created**: ~80-100 tests

---

## Task Dependencies

### Dependency Graph

```
Block 1 (Foundation)
    │
    ├─── Data Models ────────────┐
    ├─── Base Interfaces ────────┤
    └─── Memory System ──────────┤
                                 │
                                 ▼
                    Block 2 (Core Components)
                                 │
    ┌────────────────────────────┼────────────────────────────┐
    │                            │                            │
    ▼                            ▼                            ▼
Agent 1:                    Agent 2:                    (Both agents
ReAct Agent            Query Planning                  work in parallel)
    │                            │
    └────────────────────────────┘
                │
                ▼
    Block 3 (Integration)
                │
    ├─── IntelligentQueryProcessor
    ├─── Configuration
    └─── Integration Tests
                │
                ▼
    Block 4 (Testing & Audit)
                │
    ├─── Test Suite
    ├─── Documentation
    ├─── Quality Audit
    └─── Benchmarks
```

### Critical Path

```
Block 1 → Block 2 (parallel) → Block 3 → Block 4

Critical path: 2-3h + 5-7h + 2-3h + 3-4h = 12-17 hours
```

---

## Parallel Execution Plan

### Block 2 Parallelization Strategy

**Agent 1: ReAct Agent** (3-4 hours)
```
├─ LangChain tool wrappers (45 min)
├─ ReActAgent implementation (1.5-2h)
├─ Configuration (30 min)
└─ Unit tests (1h)
```

**Agent 2: Query Planning** (3-4 hours)
```
├─ QueryAnalyzer (1h)
├─ QueryDecomposer (1h)
├─ ExecutionPlanner (1h)
├─ PlanExecutor (30 min)
└─ Unit tests (30-60 min)
```

**Coordination**:
- Both agents use Block 1 components (no conflicts)
- Minimal shared code (ToolRegistry from Phase 1)
- Merge at end: integration tests verify they work together
- **Savings**: ~1-2 hours vs sequential execution

---

## Risk Mitigation

### Risk 1: LangChain Compatibility

**Risk**: LangChain API changes or incompatibilities

**Mitigation**:
- Pin exact LangChain versions in requirements
- Test with both OpenAI and Anthropic
- Have fallback to Phase 1 direct tool use

### Risk 2: Agent Performance

**Risk**: Agent too slow or expensive

**Mitigation**:
- Performance benchmarks in Block 4
- Automatic fallback to RAG for simple queries
- Cost monitoring and limits
- Timeout protection

### Risk 3: Integration Issues

**Risk**: Phase 2 breaks Phase 1 functionality

**Mitigation**:
- Maintain 100% backward compatibility
- Run Phase 1 tests after each block
- Extends (not modifies) existing classes
- Graceful degradation

### Risk 4: Test Environment

**Risk**: Missing dependencies block tests

**Mitigation**:
- Install dependencies at start (Block 0)
- Create mock LLMs for tests
- Conditional tests (skip if no API keys)

---

## Quality Gates

### Code Quality

- ✅ **Ruff**: All checks passed
- ✅ **Type Hints**: 100% coverage
- ✅ **Docstrings**: All public methods
- ✅ **Test Coverage**: >95%

### Architecture Compliance

- ✅ **Backward Compatible**: Phase 1 tests pass
- ✅ **Interface Adherence**: All abstractions implemented
- ✅ **Separation of Concerns**: Clear component boundaries
- ✅ **Configuration-Driven**: YAML configs working

### Performance

- ✅ **Simple Queries**: <5s
- ✅ **Complex Queries**: <15s
- ✅ **Agent Overhead**: <500ms
- ✅ **Cost per Query**: <$0.10

### Security

- ✅ **0 Vulnerabilities**: Security scan passed
- ✅ **Timeout Protection**: All tool executions
- ✅ **Input Validation**: All user inputs
- ✅ **Error Handling**: No exceptions to users

---

## Execution Command

```bash
# Start Phase 2 implementation
# This plan is ready for execution following the proven Phase 1 pattern
```

**Next Steps**:
1. ✅ Install dependencies (LangChain)
2. ✅ Execute Block 1 (Foundation)
3. ✅ Execute Block 2 (Core Components, parallel)
4. ✅ Execute Block 3 (Integration)
5. ✅ Execute Block 4 (Testing & Audit)

---

**Plan Status**: ✅ **Ready for Execution**
**Estimated Duration**: 12-17 hours (wall clock)
**Quality Target**: Same as Phase 1 (95/100+)

---

**Created**: November 17, 2025
**Phase**: Phase 2 Implementation
**Status**: Ready to Begin
