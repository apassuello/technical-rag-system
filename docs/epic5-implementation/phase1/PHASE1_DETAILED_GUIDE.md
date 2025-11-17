# Phase 1: API-Based Tool Integration - Detailed Implementation Guide

**Duration**: 8-12 hours
**Deliverable**: Production-ready tool system with OpenAI & Anthropic
**Status**: Ready to Start
**Date**: 2025-11-17

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Task 1.1: Anthropic Adapter](#task-11-anthropic-adapter-with-claude-tools)
3. [Task 1.2: OpenAI Enhancement](#task-12-openai-function-calling-enhancement)
4. [Task 1.3: Tool Registry](#task-13-tool-registry--implementation)
5. [Task 1.4: Integration & Testing](#task-14-integration--testing)
6. [Verification Checklist](#verification-checklist)

---

## Quick Start

### Prerequisites
```bash
# Create Phase 1 working branch
cd /home/user/rag-portfolio
git checkout -b claude/epic5-phase1-tools

# Install dependencies
conda activate rag-portfolio
pip install anthropic>=0.8.0
pip install openai>=1.0.0  # Already installed, but ensure latest

# Verify installation
python -c "import anthropic; print(anthropic.__version__)"
python -c "import openai; print(openai.__version__)"
```

### API Keys Setup
```bash
# Set environment variables (add to ~/.bashrc or use .env)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Or create .env file
cat > project-1-technical-rag/.env << EOF
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
EOF
```

### Development Workflow
```bash
# Run tests continuously
pytest tests/epic5/phase1/ -v --cov

# Run specific test file
pytest tests/epic5/phase1/unit/test_anthropic_adapter.py -v

# Check code quality
ruff check src/components/generators/llm_adapters/
mypy src/components/generators/llm_adapters/
```

---

## Task 1.1: Anthropic Adapter with Claude Tools

**Duration**: 4-5 hours
**Priority**: High (do this first!)
**Rationale**: Claude has the cleanest tools API

### Step 1.1.1: Create Anthropic Adapter Base (1.5 hours)

**File**: `src/components/generators/llm_adapters/anthropic_adapter.py`

**Implementation Checklist**:
- [ ] Create `AnthropicAdapter` class extending `BaseLLMAdapter`
- [ ] Initialize Anthropic client with API key
- [ ] Implement `_make_request()` for basic chat completions
- [ ] Implement `_parse_response()` for text extraction
- [ ] Add error handling for Anthropic-specific errors
- [ ] Add cost tracking (if pricing available)

**Code Template**:
```python
"""
Anthropic Claude LLM Adapter Implementation.

Provides integration with Anthropic's Claude models including tools API support.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal

try:
    import anthropic
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None

from .base_adapter import BaseLLMAdapter, RateLimitError, AuthenticationError, ModelNotFoundError
from ..base import GenerationParams, LLMError

logger = logging.getLogger(__name__)


class AnthropicAdapter(BaseLLMAdapter):
    """
    Anthropic Claude adapter with tools API support.

    Supports:
    - Claude 3.5 Sonnet (best for tools)
    - Claude 3 Opus (high capability)
    - Claude 3 Haiku (fast and cheap)

    Tools API Features:
    - Multi-turn tool conversations
    - Parallel tool use (when appropriate)
    - Structured tool results
    - Chain-of-thought reasoning with tools
    """

    # Model pricing (per 1M tokens) - as of Nov 2024
    MODEL_PRICING = {
        'claude-3-5-sonnet-20241022': {
            'input': Decimal('3.00'),   # $3 per 1M input tokens
            'output': Decimal('15.00')  # $15 per 1M output tokens
        },
        'claude-3-opus-20240229': {
            'input': Decimal('15.00'),
            'output': Decimal('75.00')
        },
        'claude-3-haiku-20240307': {
            'input': Decimal('0.25'),
            'output': Decimal('1.25')
        }
    }

    # Model context limits (tokens)
    MODEL_LIMITS = {
        'claude-3-5-sonnet-20241022': 200000,
        'claude-3-opus-20240229': 200000,
        'claude-3-haiku-20240307': 200000
    }

    def __init__(self,
                 model_name: str = "claude-3-5-sonnet-20241022",
                 api_key: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 timeout: float = 120.0):
        """
        Initialize Anthropic adapter.

        Args:
            model_name: Claude model to use
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            config: Additional configuration
            max_retries: Maximum retry attempts
            retry_delay: Initial delay between retries
            timeout: Request timeout in seconds
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic package not installed. Install with: pip install anthropic"
            )

        super().__init__(model_name, config, max_retries, retry_delay)

        # Get API key
        self.api_key = (
            api_key or
            (config or {}).get('api_key') or
            os.getenv('ANTHROPIC_API_KEY')
        )

        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable."
            )

        # Initialize client
        self.client = Anthropic(api_key=self.api_key, timeout=timeout)
        self.timeout = timeout

        # Cost tracking
        self._total_cost = Decimal('0.00')
        self._input_tokens = 0
        self._output_tokens = 0

        logger.info(f"Initialized Anthropic adapter with model: {model_name}")

    def _make_request(self, prompt: str, params: GenerationParams) -> Dict[str, Any]:
        """Make request to Anthropic API."""
        try:
            start_time = time.time()

            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=params.max_tokens or 1024,
                temperature=params.temperature or 1.0,
                messages=[{"role": "user", "content": prompt}]
            )

            request_time = time.time() - start_time
            logger.debug(f"Anthropic request completed in {request_time:.2f}s")

            # Convert to dict
            response_dict = {
                'id': response.id,
                'model': response.model,
                'role': response.role,
                'content': response.content,
                'stop_reason': response.stop_reason,
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                },
                'request_time': request_time
            }

            # Track usage
            self._track_usage(response_dict['usage'])

            return response_dict

        except anthropic.RateLimitError as e:
            logger.warning(f"Anthropic rate limit: {str(e)}")
            raise RateLimitError(f"Anthropic rate limit: {str(e)}")
        except anthropic.AuthenticationError as e:
            logger.error(f"Anthropic authentication failed: {str(e)}")
            raise AuthenticationError(f"Anthropic auth error: {str(e)}")
        except Exception as e:
            logger.error(f"Anthropic error: {str(e)}")
            raise LLMError(f"Anthropic error: {str(e)}")

    def _parse_response(self, response: Dict[str, Any]) -> str:
        """Parse Anthropic response to extract text."""
        try:
            content = response.get('content', [])
            if not content:
                raise LLMError("Empty content in Anthropic response")

            # Extract text blocks
            text_parts = []
            for block in content:
                if block.type == 'text':
                    text_parts.append(block.text)

            if not text_parts:
                raise LLMError("No text content in Anthropic response")

            return ' '.join(text_parts).strip()

        except Exception as e:
            raise LLMError(f"Failed to parse Anthropic response: {str(e)}")

    def _track_usage(self, usage: Dict[str, int]) -> None:
        """Track token usage and costs."""
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)

        self._input_tokens += input_tokens
        self._output_tokens += output_tokens

        # Calculate cost
        if self.model_name in self.MODEL_PRICING:
            pricing = self.MODEL_PRICING[self.model_name]
            input_cost = (Decimal(str(input_tokens)) / Decimal('1000000')) * pricing['input']
            output_cost = (Decimal(str(output_tokens)) / Decimal('1000000')) * pricing['output']
            self._total_cost += (input_cost + output_cost)

            logger.debug(
                f"Anthropic usage: {input_tokens} input + {output_tokens} output tokens, "
                f"cost: ${float(input_cost + output_cost):.6f}"
            )

    def _get_provider_name(self) -> str:
        return "Anthropic"

    def _supports_streaming(self) -> bool:
        return True

    def _get_max_tokens(self) -> Optional[int]:
        return self.MODEL_LIMITS.get(self.model_name)
```

**Testing**:
```bash
# Create test file
cat > tests/epic5/phase1/unit/test_anthropic_adapter.py << 'EOF'
import pytest
from src.components.generators.llm_adapters.anthropic_adapter import AnthropicAdapter
from src.components.generators.base import GenerationParams

def test_anthropic_adapter_init():
    """Test adapter initialization."""
    adapter = AnthropicAdapter(api_key="test-key")
    assert adapter.model_name == "claude-3-5-sonnet-20241022"
    assert adapter._get_provider_name() == "Anthropic"

@pytest.mark.skipif(not os.getenv('ANTHROPIC_API_KEY'), reason="No API key")
def test_anthropic_basic_generation():
    """Test basic text generation."""
    adapter = AnthropicAdapter()
    params = GenerationParams(max_tokens=100, temperature=0.0)

    result = adapter.generate("Say 'hello' and nothing else.", params)
    assert "hello" in result.lower()
    assert adapter._input_tokens > 0
    assert adapter._output_tokens > 0
EOF

# Run test
pytest tests/epic5/phase1/unit/test_anthropic_adapter.py -v
```

---

### Step 1.1.2: Add Tools API Support (1.5 hours)

**Enhancement**: Add `generate_with_tools()` method

**Implementation Checklist**:
- [ ] Add `generate_with_tools()` method
- [ ] Handle tool use blocks in responses
- [ ] Implement multi-turn tool conversations
- [ ] Add tool execution framework
- [ ] Handle tool errors gracefully

**Code Addition**:
```python
class AnthropicAdapter(BaseLLMAdapter):
    # ... existing code ...

    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        params: GenerationParams,
        max_tool_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Generate response with tool use capability.

        Args:
            prompt: User prompt
            tools: List of tool schemas (Anthropic format)
            params: Generation parameters
            max_tool_iterations: Max tool use rounds

        Returns:
            Dict with final answer and tool use history
        """
        messages = [{"role": "user", "content": prompt}]
        tool_history = []

        for iteration in range(max_tool_iterations):
            logger.debug(f"Tool iteration {iteration + 1}/{max_tool_iterations}")

            try:
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=params.max_tokens or 1024,
                    temperature=params.temperature or 1.0,
                    tools=tools,
                    messages=messages
                )

                # Track usage
                usage = {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }
                self._track_usage(usage)

                # Check stop reason
                if response.stop_reason == "end_turn":
                    # Final answer reached
                    final_text = self._extract_text_from_content(response.content)
                    return {
                        'answer': final_text,
                        'tool_history': tool_history,
                        'iterations': iteration + 1,
                        'stop_reason': 'end_turn'
                    }

                elif response.stop_reason == "tool_use":
                    # Extract tool calls
                    tool_calls = self._extract_tool_calls(response.content)
                    text_before_tools = self._extract_text_from_content(response.content)

                    # Log tool use
                    logger.info(f"Claude wants to use {len(tool_calls)} tool(s)")
                    for tool_call in tool_calls:
                        logger.debug(f"  - {tool_call['name']}: {tool_call['input']}")

                    # Add assistant response to conversation
                    messages.append({
                        "role": "assistant",
                        "content": response.content
                    })

                    # Execute tools (placeholder - will implement in Task 1.3)
                    tool_results = self._execute_tools(tool_calls)

                    # Add tool results to conversation
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })

                    # Record in history
                    tool_history.append({
                        'iteration': iteration + 1,
                        'thinking': text_before_tools,
                        'tool_calls': tool_calls,
                        'tool_results': tool_results
                    })

                    continue

                else:
                    # Unexpected stop reason
                    logger.warning(f"Unexpected stop reason: {response.stop_reason}")
                    final_text = self._extract_text_from_content(response.content)
                    return {
                        'answer': final_text,
                        'tool_history': tool_history,
                        'iterations': iteration + 1,
                        'stop_reason': response.stop_reason
                    }

            except Exception as e:
                logger.error(f"Error in tool iteration {iteration + 1}: {str(e)}")
                raise LLMError(f"Tool execution failed: {str(e)}")

        # Max iterations reached
        raise LLMError(f"Max tool iterations ({max_tool_iterations}) exceeded")

    def _extract_text_from_content(self, content: List) -> str:
        """Extract text blocks from content."""
        text_parts = []
        for block in content:
            if hasattr(block, 'type') and block.type == 'text':
                text_parts.append(block.text)
        return ' '.join(text_parts).strip()

    def _extract_tool_calls(self, content: List) -> List[Dict[str, Any]]:
        """Extract tool use blocks from content."""
        tool_calls = []
        for block in content:
            if hasattr(block, 'type') and block.type == 'tool_use':
                tool_calls.append({
                    'id': block.id,
                    'name': block.name,
                    'input': block.input
                })
        return tool_calls

    def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute tools and format results.

        NOTE: This is a placeholder. Real implementation in Task 1.3.
        """
        # Placeholder - return mock results
        results = []
        for tool_call in tool_calls:
            results.append({
                "type": "tool_result",
                "tool_use_id": tool_call['id'],
                "content": f"Mock result for {tool_call['name']}"
            })
        return results
```

**Testing**:
```python
@pytest.mark.skipif(not os.getenv('ANTHROPIC_API_KEY'), reason="No API key")
def test_anthropic_tools_api():
    """Test tools API integration."""
    adapter = AnthropicAdapter()
    params = GenerationParams(max_tokens=1000, temperature=0.0)

    # Simple calculator tool schema
    tools = [{
        "name": "calculator",
        "description": "Perform basic arithmetic",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression"}
            },
            "required": ["expression"]
        }
    }]

    result = adapter.generate_with_tools(
        "What is 25 * 47?",
        tools=tools,
        params=params
    )

    assert 'answer' in result
    assert len(result['tool_history']) > 0
    assert result['tool_history'][0]['tool_calls'][0]['name'] == 'calculator'
```

**Acceptance Criteria**:
- ✅ `generate_with_tools()` method works
- ✅ Multi-turn conversations handled
- ✅ Tool calls extracted correctly
- ✅ Tests pass with real API
- ✅ Cost tracking works

---

### Step 1.1.3: Tool Schema Helpers (1 hour)

**File**: `src/components/generators/llm_adapters/anthropic_tools/tool_schemas.py`

**Create helper for tool schema generation**:
```python
"""Anthropic tool schema utilities."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: str  # "string", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    enum: Optional[List[str]] = None


class AnthropicToolSchema:
    """Helper for creating Anthropic tool schemas."""

    @staticmethod
    def create_tool_schema(
        name: str,
        description: str,
        parameters: List[ToolParameter]
    ) -> Dict[str, Any]:
        """
        Create Anthropic tool schema.

        Args:
            name: Tool name
            description: Tool description
            parameters: List of tool parameters

        Returns:
            Anthropic-compatible tool schema
        """
        properties = {}
        required = []

        for param in parameters:
            param_schema = {
                "type": param.type,
                "description": param.description
            }

            if param.enum:
                param_schema["enum"] = param.enum

            properties[param.name] = param_schema

            if param.required:
                required.append(param.name)

        return {
            "name": name,
            "description": description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


# Example tool schemas
CALCULATOR_SCHEMA = AnthropicToolSchema.create_tool_schema(
    name="calculator",
    description="Evaluate mathematical expressions. Supports +, -, *, /, **, sqrt, etc.",
    parameters=[
        ToolParameter(
            name="expression",
            type="string",
            description="Mathematical expression to evaluate (e.g., '25 * 47')"
        )
    ]
)

DOCUMENT_SEARCH_SCHEMA = AnthropicToolSchema.create_tool_schema(
    name="search_documents",
    description="Search the RAG document collection for relevant information.",
    parameters=[
        ToolParameter(
            name="query",
            type="string",
            description="Search query to find relevant documents"
        ),
        ToolParameter(
            name="max_results",
            type="number",
            description="Maximum number of results to return",
            required=False
        )
    ]
)
```

---

## Task 1.2: OpenAI Function Calling Enhancement

**Duration**: 3-4 hours
**Prerequisites**: Existing `OpenAIAdapter` understanding

### Step 1.2.1: Add Function Calling Method (1.5 hours)

**File**: `src/components/generators/llm_adapters/openai_adapter.py`

**Add to existing class**:
```python
class OpenAIAdapter(BaseLLMAdapter):
    # ... existing code ...

    def generate_with_functions(
        self,
        prompt: str,
        functions: List[Dict[str, Any]],
        params: GenerationParams,
        max_function_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Generate response with function calling capability.

        Args:
            prompt: User prompt
            functions: List of function schemas (OpenAI format)
            params: Generation parameters
            max_function_iterations: Max function call rounds

        Returns:
            Dict with final answer and function call history
        """
        messages = [{"role": "user", "content": prompt}]
        function_history = []

        for iteration in range(max_function_iterations):
            logger.debug(f"Function iteration {iteration + 1}/{max_function_iterations}")

            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=[{"type": "function", "function": func} for func in functions],
                    tool_choice="auto",
                    temperature=params.temperature,
                    max_tokens=params.max_tokens
                )

                # Track usage
                usage = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
                self._track_usage(usage)

                message = response.choices[0].message

                # Check for function calls
                if message.tool_calls:
                    # Extract function calls
                    function_calls = [
                        {
                            'id': tool_call.id,
                            'name': tool_call.function.name,
                            'arguments': tool_call.function.arguments
                        }
                        for tool_call in message.tool_calls
                    ]

                    logger.info(f"GPT wants to use {len(function_calls)} function(s)")

                    # Add assistant message
                    messages.append(message)

                    # Execute functions (placeholder)
                    function_results = self._execute_functions(message.tool_calls)

                    # Add results
                    messages.extend(function_results)

                    # Record history
                    function_history.append({
                        'iteration': iteration + 1,
                        'function_calls': function_calls,
                        'results': function_results
                    })

                    continue

                # Final answer
                return {
                    'answer': message.content,
                    'function_history': function_history,
                    'iterations': iteration + 1,
                    'finish_reason': response.choices[0].finish_reason
                }

            except Exception as e:
                logger.error(f"Error in function iteration {iteration + 1}: {str(e)}")
                raise LLMError(f"Function execution failed: {str(e)}")

        raise LLMError(f"Max function iterations ({max_function_iterations}) exceeded")

    def _execute_functions(self, tool_calls) -> List[Dict[str, Any]]:
        """Execute functions - placeholder for Task 1.3."""
        results = []
        for tool_call in tool_calls:
            results.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_call.function.name,
                "content": f"Mock result for {tool_call.function.name}"
            })
        return results
```

---

(Continue with remaining Phase 1 tasks...)

## Verification Checklist

### Task 1.1 Complete:
- [ ] Anthropic adapter initializes correctly
- [ ] Basic chat completions work
- [ ] Tools API integration functional
- [ ] Multi-turn tool conversations work
- [ ] Cost tracking accurate
- [ ] All tests pass

### Task 1.2 Complete:
- [ ] OpenAI function calling works
- [ ] Parallel function calls supported
- [ ] Cost tracking includes functions
- [ ] Backward compatible
- [ ] All tests pass

### Task 1.3 Complete:
- [ ] Tool registry operational
- [ ] 3-5 tools implemented
- [ ] Document search uses RAG retriever
- [ ] All tools tested
- [ ] Schema generation works for both providers

### Task 1.4 Complete:
- [ ] Integration tests pass
- [ ] End-to-end scenarios work
- [ ] Performance acceptable
- [ ] Documentation complete

### Phase 1 Complete:
- [ ] Can demo tool use with Claude
- [ ] Can demo function calling with GPT
- [ ] Tool registry works with both
- [ ] Ready for Phase 2
