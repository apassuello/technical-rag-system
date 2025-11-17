# Phase 1: Tool Integration Architecture

**Version**: 1.0
**Date**: 2025-11-17
**Status**: Architecture Specification

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Interface Definitions](#interface-definitions)
4. [Data Models](#data-models)
5. [Error Handling Strategy](#error-handling-strategy)
6. [Integration Points](#integration-points)
7. [Testing Strategy](#testing-strategy)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Existing RAG System                           │
│                 (Answer Generator Component)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Enhanced LLM Adapters (Phase 1)                     │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ AnthropicAdapter │  │ OpenAIAdapter    │                    │
│  │ + tools support  │  │ + functions      │                    │
│  └──────────────────┘  └──────────────────┘                    │
│           │                      │                               │
│           └──────────┬───────────┘                              │
│                      ▼                                           │
│         ┌─────────────────────────┐                            │
│         │  Tool Executor           │                            │
│         │  (executes tool calls)   │                            │
│         └─────────────────────────┘                            │
│                      │                                           │
│                      ▼                                           │
│         ┌─────────────────────────┐                            │
│         │   Tool Registry          │                            │
│         │   (manages tools)        │                            │
│         └─────────────────────────┘                            │
│                      │                                           │
│         ┌────────────┴────────────┐                            │
│         ▼            ▼             ▼                            │
│    ┌────────┐  ┌─────────┐  ┌──────────┐                      │
│    │Document│  │Calculator│  │Code      │                      │
│    │Search  │  │Tool      │  │Analyzer  │                      │
│    └────────┘  └─────────┘  └──────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Backward Compatibility**: All existing adapter functionality preserved
2. **Provider Abstraction**: Tools work with any LLM provider
3. **Type Safety**: Full type hints, validated with mypy
4. **Error Resilience**: Graceful degradation, no crashes
5. **Testability**: All components mockable and testable
6. **Performance**: Minimal overhead (<50ms per tool call)

---

## Component Architecture

### Component Hierarchy

```
src/components/generators/llm_adapters/
├── base_adapter.py                 # Existing - unchanged
├── anthropic_adapter.py            # NEW - Phase 1
├── openai_adapter.py               # ENHANCED - Phase 1
├── anthropic_tools/
│   ├── __init__.py
│   ├── tool_schemas.py             # Anthropic tool definitions
│   └── tool_executor.py            # Tool execution logic
└── openai_tools/
    ├── __init__.py
    ├── function_schemas.py         # OpenAI function definitions
    └── function_executor.py        # Function execution logic

src/components/query_processors/tools/
├── __init__.py
├── base_tool.py                    # Abstract tool interface
├── tool_registry.py                # Central tool registry
├── tool_executor.py                # Tool execution coordinator
├── implementations/
│   ├── __init__.py
│   ├── document_search_tool.py     # Search RAG documents
│   ├── calculator_tool.py          # Math calculations
│   ├── code_analyzer_tool.py       # Code analysis
│   └── web_search_tool.py          # Optional: DuckDuckGo
└── schemas/
    ├── __init__.py
    ├── tool_schema.py              # Schema definitions
    ├── anthropic_schema.py         # Anthropic format
    └── openai_schema.py            # OpenAI format
```

---

## Interface Definitions

### 1. BaseTool Interface

**Purpose**: Abstract interface for all tools

**Contract**:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class ToolParameterType(Enum):
    """Tool parameter types."""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"

@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    enum: Optional[List[str]] = None
    default: Optional[Any] = None

@dataclass
class ToolResult:
    """Tool execution result."""
    success: bool
    content: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

class BaseTool(ABC):
    """
    Abstract base class for all tools.

    Responsibilities:
    - Define tool schema
    - Execute tool logic
    - Handle errors gracefully
    - Provide observability
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name (unique identifier)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM (clear, concise)."""
        pass

    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """Get tool parameters definition."""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute tool with given parameters.

        Must handle all errors internally and return ToolResult.
        Never raise exceptions - use ToolResult.error instead.
        """
        pass

    def validate_parameters(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate parameters before execution."""
        # Default implementation - can be overridden
        pass

    def to_anthropic_schema(self) -> Dict[str, Any]:
        """Convert to Anthropic tool schema."""
        pass

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI function schema."""
        pass
```

**Invariants**:
- `execute()` NEVER raises exceptions (returns error in ToolResult)
- `name` must be unique across all tools
- `description` must be clear enough for LLM to understand when to use
- Schema conversion must be bidirectional (can reconstruct tool from schema)

---

### 2. ToolRegistry Interface

**Purpose**: Centralized tool management

**Contract**:
```python
from typing import Dict, List, Optional
import logging

class ToolRegistry:
    """
    Central registry for all tools.

    Responsibilities:
    - Register/unregister tools
    - Provide tool lookup
    - Generate schemas for different providers
    - Validate tool configurations
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._logger = logging.getLogger(__name__)

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.

        Raises:
            ValueError: If tool with same name already registered
        """
        pass

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool."""
        pass

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool by name."""
        pass

    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        pass

    def get_anthropic_schemas(self) -> List[Dict[str, Any]]:
        """Get all tools as Anthropic schemas."""
        pass

    def get_openai_schemas(self) -> List[Dict[str, Any]]:
        """Get all tools as OpenAI schemas."""
        pass

    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a tool by name.

        Returns ToolResult with error if tool not found.
        """
        pass
```

**Invariants**:
- Tool names must be unique
- Registry is thread-safe
- Failed tool lookups return None, not exceptions
- Tool execution failures return ToolResult with error=True

---

### 3. Enhanced Adapter Interfaces

#### AnthropicAdapter (NEW)

**Contract**:
```python
from typing import List, Dict, Any, Optional
from .base_adapter import BaseLLMAdapter, GenerationParams

@dataclass
class ToolUseResult:
    """Result from tool-enhanced generation."""
    answer: str
    tool_calls: List[Dict[str, Any]]
    iterations: int
    total_tokens: int
    cost_usd: float
    execution_time: float

class AnthropicAdapter(BaseLLMAdapter):
    """
    Anthropic Claude adapter with tools API support.

    New methods for Phase 1:
    """

    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],  # Anthropic tool schemas
        params: GenerationParams,
        max_iterations: int = 5,
        tool_choice: str = "auto"
    ) -> ToolUseResult:
        """
        Generate response with tool use capability.

        Args:
            prompt: User prompt
            tools: List of Anthropic tool schemas
            params: Generation parameters
            max_iterations: Max tool use rounds
            tool_choice: "auto", "any", or specific tool name

        Returns:
            ToolUseResult with answer and tool call history

        Raises:
            LLMError: If generation fails
            MaxIterationsError: If max iterations exceeded
        """
        pass
```

**Invariants**:
- Existing `generate()` method unchanged (backward compatibility)
- `generate_with_tools()` handles multi-turn conversations
- Cost tracking includes all tool iterations
- Tool execution errors don't crash generation (graceful degradation)

#### OpenAIAdapter (ENHANCED)

**Contract**:
```python
@dataclass
class FunctionCallResult:
    """Result from function calling generation."""
    answer: str
    function_calls: List[Dict[str, Any]]
    iterations: int
    total_tokens: int
    cost_usd: float
    execution_time: float

class OpenAIAdapter(BaseLLMAdapter):
    """
    Enhanced OpenAI adapter with function calling.

    New methods for Phase 1:
    """

    def generate_with_functions(
        self,
        prompt: str,
        functions: List[Dict[str, Any]],  # OpenAI function schemas
        params: GenerationParams,
        max_iterations: int = 5,
        function_choice: str = "auto"
    ) -> FunctionCallResult:
        """
        Generate response with function calling capability.

        Args:
            prompt: User prompt
            functions: List of OpenAI function schemas
            params: Generation parameters
            max_iterations: Max function call rounds
            function_choice: "auto", "none", or {"name": "function_name"}

        Returns:
            FunctionCallResult with answer and function call history

        Raises:
            LLMError: If generation fails
            MaxIterationsError: If max iterations exceeded
        """
        pass
```

**Invariants**:
- Existing methods unchanged
- Supports parallel function calls (OpenAI feature)
- Cost tracking accurate for all iterations
- Handles streaming (future enhancement)

---

### 4. ToolExecutor Interface

**Purpose**: Execute tools with proper error handling and monitoring

**Contract**:
```python
from typing import Dict, Any, List
import time
import logging

class ToolExecutionError(Exception):
    """Tool execution error."""
    pass

class ToolExecutor:
    """
    Coordinates tool execution with error handling.

    Responsibilities:
    - Execute tools from registry
    - Handle timeouts
    - Track execution metrics
    - Log all executions
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        timeout: float = 30.0,
        max_retries: int = 1
    ):
        self.registry = tool_registry
        self.timeout = timeout
        self.max_retries = max_retries
        self._execution_count = 0
        self._total_time = 0.0

    def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> ToolResult:
        """
        Execute a tool with timeout and retry logic.

        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            timeout: Override default timeout

        Returns:
            ToolResult (never raises exceptions)
        """
        pass

    def execute_batch(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[ToolResult]:
        """Execute multiple tools (for parallel calls)."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        pass
```

**Invariants**:
- `execute()` NEVER raises exceptions
- Timeouts handled gracefully
- All executions logged
- Metrics tracked for monitoring

---

## Data Models

### Tool Call Flow

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class ToolCall:
    """Single tool call from LLM."""
    id: str                          # Tool call ID
    tool_name: str                   # Tool to execute
    arguments: Dict[str, Any]        # Tool arguments
    timestamp: datetime              # When LLM made the call

@dataclass
class ToolExecution:
    """Tool execution record."""
    call: ToolCall                   # Original call
    result: ToolResult               # Execution result
    started_at: datetime
    completed_at: datetime
    execution_time: float            # Seconds

@dataclass
class ToolConversation:
    """Multi-turn tool conversation."""
    prompt: str                      # Original user prompt
    tool_executions: List[ToolExecution]
    final_answer: str
    total_iterations: int
    total_tokens: int
    total_cost_usd: float
    total_time: float
```

---

## Error Handling Strategy

### Error Hierarchy

```python
# Base errors (existing)
class LLMError(Exception):
    """Base LLM error."""
    pass

class RateLimitError(LLMError):
    """Rate limit exceeded."""
    pass

class AuthenticationError(LLMError):
    """Authentication failed."""
    pass

# New Phase 1 errors
class ToolError(Exception):
    """Base tool error."""
    pass

class ToolNotFoundError(ToolError):
    """Tool not found in registry."""
    pass

class ToolExecutionError(ToolError):
    """Tool execution failed."""
    pass

class ToolTimeoutError(ToolError):
    """Tool execution timeout."""
    pass

class ToolValidationError(ToolError):
    """Tool parameter validation failed."""
    pass

class MaxIterationsError(LLMError):
    """Max tool/function iterations exceeded."""
    pass
```

### Error Handling Rules

1. **Tool Execution**:
   - Tools NEVER raise exceptions
   - Errors returned in `ToolResult.error`
   - LLM informed of errors to retry or adapt

2. **Adapter Level**:
   - API errors (rate limit, auth) raised as exceptions
   - Tool errors returned in result, not raised
   - Max iterations raised as exception

3. **Registry Level**:
   - Tool not found returns None
   - Execution errors caught and wrapped in ToolResult

4. **User-Facing**:
   - All errors logged with context
   - Graceful degradation (fallback to non-tool generation)
   - User-friendly error messages

---

## Integration Points

### With Existing Components

#### 1. Answer Generator Integration

**Location**: `src/components/generators/answer_generator.py`

**Integration Strategy**:
- Add optional `tools` parameter to `generate()` method
- Detect if adapter supports tools
- Fallback to non-tool generation if not supported

**Backward Compatibility**:
```python
class AnswerGenerator:
    def generate(
        self,
        query: str,
        context: List[Document],
        use_tools: bool = False,  # NEW - opt-in
        tools: Optional[List[BaseTool]] = None  # NEW
    ) -> str:
        """Generate answer with optional tool support."""

        if use_tools and hasattr(self.llm_adapter, 'generate_with_tools'):
            # Use tools
            return self._generate_with_tools(query, context, tools)
        else:
            # Existing behavior
            return self._generate_standard(query, context)
```

#### 2. Document Retriever Integration

**Purpose**: Document search tool needs access to retriever

**Strategy**:
```python
class DocumentSearchTool(BaseTool):
    def __init__(self, retriever: Retriever):
        self.retriever = retriever

    def execute(self, query: str, max_results: int = 5) -> ToolResult:
        """Search documents using existing retriever."""
        results = self.retriever.retrieve(query, k=max_results)
        return ToolResult(
            success=True,
            content=self._format_results(results)
        )
```

#### 3. Configuration Integration

**Location**: `config/default.yaml`

**New Configuration**:
```yaml
answer_generator:
  tools:
    enabled: false  # Opt-in for Phase 1
    max_iterations: 5
    timeout: 30.0
    available_tools:
      - document_search
      - calculator
      - code_analyzer

anthropic:
  model: "claude-3-5-sonnet-20241022"
  api_key_env: "ANTHROPIC_API_KEY"
  tools_enabled: true

openai:
  model: "gpt-4-turbo"
  api_key_env: "OPENAI_API_KEY"
  functions_enabled: true
```

---

## Testing Strategy

### Test Levels

#### 1. Unit Tests (Component Isolation)

**Coverage**: >95%

**Test Files**:
```
tests/epic5/phase1/unit/
├── test_base_tool.py
├── test_tool_registry.py
├── test_tool_executor.py
├── test_anthropic_adapter.py
├── test_openai_adapter.py
├── test_calculator_tool.py
├── test_document_search_tool.py
└── test_code_analyzer_tool.py
```

**Mock Strategy**:
- Mock LLM API calls (no real API in unit tests)
- Mock tool execution for adapter tests
- Mock retriever for document search tool tests

#### 2. Integration Tests (Component Interaction)

**Coverage**: All critical paths

**Test Files**:
```
tests/epic5/phase1/integration/
├── test_anthropic_tool_execution.py     # Real API (skipif no key)
├── test_openai_function_execution.py    # Real API (skipif no key)
├── test_tool_registry_integration.py
└── test_multi_tool_execution.py
```

**Real API Tests**:
- Conditional on API key presence
- Budget-aware (limit test count)
- Record and verify costs

#### 3. Scenario Tests (End-to-End)

**Test Files**:
```
tests/epic5/phase1/scenarios/
├── test_document_search_scenario.py
├── test_calculator_scenario.py
├── test_multi_turn_conversation.py
└── test_error_handling_scenarios.py
```

**Scenarios**:
1. User asks math question → Calculator tool used → Correct answer
2. User asks about docs → Document search tool used → Relevant docs retrieved
3. Tool execution fails → LLM retries with different approach
4. Max iterations reached → Graceful error message

### Test Quality Requirements

**All Tests Must**:
- Have clear docstrings explaining what is tested
- Use descriptive assertion messages
- Clean up resources (temp files, API clients)
- Be deterministic (no flaky tests)
- Run in <10 seconds (unit), <60 seconds (integration)

**Assertion Quality**:
```python
# BAD
assert result

# GOOD
assert result is not None, "Tool execution should return a result"
assert result.success, f"Tool execution failed: {result.error}"
assert result.content == expected, \
    f"Expected {expected}, got {result.content}"
```

---

## Definitions of Done

### Component: AnthropicAdapter

**Implementation Complete When**:
- ✅ Class created extending BaseLLMAdapter
- ✅ `generate_with_tools()` method implemented
- ✅ Multi-turn conversations working
- ✅ Tool call extraction correct
- ✅ Tool result formatting correct
- ✅ Cost tracking includes all iterations
- ✅ Error handling comprehensive

**Tests Complete When**:
- ✅ Unit tests >95% coverage
- ✅ Integration test with real API passing
- ✅ Mock tests for error conditions
- ✅ Performance test <3s for single tool call

**Documentation Complete When**:
- ✅ Docstrings for all public methods
- ✅ Usage examples in docstrings
- ✅ Type hints for all parameters
- ✅ README updated with examples

---

### Component: OpenAIAdapter Enhancement

**Implementation Complete When**:
- ✅ `generate_with_functions()` method added
- ✅ Backward compatible (existing tests still pass)
- ✅ Parallel function calls supported
- ✅ Function result formatting correct
- ✅ Cost tracking accurate
- ✅ Error handling comprehensive

**Tests Complete When**:
- ✅ Unit tests >95% coverage
- ✅ Integration test with real API passing
- ✅ Parallel function call test passing
- ✅ Backward compatibility verified
- ✅ Performance test <3s for single function call

**Documentation Complete When**:
- ✅ Docstrings complete
- ✅ Migration guide from old to new methods
- ✅ Examples for both sync and parallel calls

---

### Component: ToolRegistry

**Implementation Complete When**:
- ✅ Registry class implemented
- ✅ Thread-safe tool registration
- ✅ Tool lookup working
- ✅ Schema generation for both providers
- ✅ Tool execution coordination
- ✅ Error handling for missing tools

**Tests Complete When**:
- ✅ Unit tests >95% coverage
- ✅ Thread safety tests passing
- ✅ Schema conversion tests passing
- ✅ Error handling tests passing

**Documentation Complete When**:
- ✅ API documentation complete
- ✅ Usage examples provided
- ✅ Registration best practices documented

---

### Component: Tools (Each Tool)

**Implementation Complete When**:
- ✅ Tool class implementing BaseTool
- ✅ `execute()` method working correctly
- ✅ Parameter validation implemented
- ✅ Error handling (returns ToolResult.error)
- ✅ Schema generation for both providers
- ✅ Performance acceptable (<1s typical execution)

**Tests Complete When**:
- ✅ Unit tests >90% coverage
- ✅ Success case tested
- ✅ Error cases tested
- ✅ Edge cases tested
- ✅ Integration with real dependencies tested

**Documentation Complete When**:
- ✅ Tool purpose clearly documented
- ✅ Parameters documented with examples
- ✅ Usage examples provided
- ✅ Error conditions documented

---

### Phase 1 Complete When

**All Components**:
- ✅ All individual components meet DoD
- ✅ Integration tests passing
- ✅ Scenario tests passing
- ✅ No existing tests broken
- ✅ Code quality >95% (ruff, mypy)

**Documentation**:
- ✅ Architecture docs updated
- ✅ API documentation complete
- ✅ Usage examples provided
- ✅ Migration guide written

**Demo**:
- ✅ Working demo script showing:
  - Anthropic tool use
  - OpenAI function calling
  - Document search integration
  - Multi-turn conversation
  - Error handling

**Validation**:
- ✅ Audit completed (separate agent)
- ✅ All audit findings addressed
- ✅ Performance benchmarks met
- ✅ Ready for Phase 2

---

## Success Metrics

### Functional Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Tool execution success rate | >95% | Integration tests |
| Schema conversion accuracy | 100% | Unit tests |
| Backward compatibility | 100% | Existing tests pass |
| Error recovery rate | >90% | Error scenario tests |

### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Tool call latency | <3s | Integration tests |
| Registry lookup time | <1ms | Unit tests |
| Schema generation time | <10ms | Unit tests |
| Memory overhead | <50MB | Profiling |

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test coverage | >95% | pytest-cov |
| Type hint coverage | >95% | mypy |
| Code quality | >9.0/10 | ruff |
| Documentation coverage | 100% | Manual review |

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| API changes breaking | High | Pin API versions, comprehensive tests |
| Performance degradation | Medium | Benchmark each component |
| Tool execution failures | Medium | Graceful error handling, retries |
| Thread safety issues | High | Thread safety tests, locks where needed |

### Implementation Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep | High | Strict adherence to DoD |
| Breaking changes | High | Comprehensive backward compat tests |
| Incomplete error handling | Medium | Error scenario checklist |
| Test gaps | Medium | Coverage requirements enforced |

---

**Document Status**: Ready for Implementation

**Next Step**: Create detailed implementation plan with parallel execution strategy
