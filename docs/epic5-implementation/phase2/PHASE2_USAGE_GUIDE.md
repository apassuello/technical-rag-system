# Phase 2 Usage Guide

**Epic 5**: Tool & Function Calling for RAG System
**Phase**: Phase 2 - Agent Orchestration & Query Planning
**Version**: 1.0
**Date**: November 18, 2025

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Common Use Cases](#common-use-cases)
3. [Configuration Guide](#configuration-guide)
4. [Best Practices](#best-practices)
5. [Troubleshooting](#troubleshooting)
6. [Performance Tuning](#performance-tuning)
7. [Advanced Usage](#advanced-usage)

---

## Quick Start

### Minimal Setup (RAG Only)

```python
from src.components.query_processors import IntelligentQueryProcessor

# Backward compatible - works exactly like original QueryProcessor
processor = IntelligentQueryProcessor(
    retriever=my_retriever,
    generator=my_generator
)

# Process queries (always uses RAG)
answer = processor.process("What is machine learning?")
print(answer.answer)
```

### Full Setup (RAG + Agent)

```python
from src.components.query_processors import IntelligentQueryProcessor
from src.components.query_processors.agents import ReActAgent, QueryAnalyzer
from src.components.query_processors.agents.memory import ConversationMemory
from src.components.query_processors.agents.models import (
    AgentConfig,
    ProcessorConfig
)
from src.components.query_processors.tools.implementations import (
    CalculatorTool,
    DocumentSearchTool,
    CodeAnalyzerTool
)
from langchain_openai import ChatOpenAI

# 1. Create LLM
llm = ChatOpenAI(
    model="gpt-4-turbo",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

# 2. Create tools
tools = [
    CalculatorTool(),
    DocumentSearchTool(index_path="data/indices"),
    CodeAnalyzerTool()
]

# 3. Create memory
memory = ConversationMemory(max_messages=100)

# 4. Configure agent
agent_config = AgentConfig(
    llm_provider="openai",
    llm_model="gpt-4-turbo",
    temperature=0.7,
    max_iterations=10,
    max_execution_time=300
)

# 5. Create agent
agent = ReActAgent(llm, tools, memory, agent_config)

# 6. Configure processor
processor_config = ProcessorConfig(
    use_agent_by_default=True,
    complexity_threshold=0.7,  # Queries > 0.7 use agent
    max_agent_cost=0.10,  # Max $0.10 per query
    enable_planning=True
)

# 7. Create processor
processor = IntelligentQueryProcessor(
    retriever=my_retriever,
    generator=my_generator,
    agent=agent,
    query_analyzer=QueryAnalyzer(),
    config=processor_config
)

# 8. Process queries (automatic routing)
answer = processor.process("Calculate 25 * 47")  # Uses agent
print(answer.answer)
print(f"Cost: ${answer.metadata['total_cost']:.4f}")
```

---

## Common Use Cases

### Use Case 1: Simple Q&A (RAG Only)

**Scenario**: Answer factual questions from documentation

```python
# Simple queries automatically route to RAG
questions = [
    "What is machine learning?",
    "Define neural networks",
    "Explain transformers architecture"
]

for question in questions:
    answer = processor.process(question)
    print(f"Q: {question}")
    print(f"A: {answer.answer}")
    print(f"Routing: {answer.metadata['routing_decision']}")  # "rag_pipeline"
    print()
```

**Output**:
```
Q: What is machine learning?
A: Machine learning is a subset of AI that enables systems to learn...
Routing: rag_pipeline

Q: Define neural networks
A: Neural networks are computing systems inspired by biological...
Routing: rag_pipeline
```

---

### Use Case 2: Mathematical Calculations

**Scenario**: Perform calculations using Calculator tool

```python
# Complex calculations trigger agent
calculations = [
    "What is 25 * 47?",
    "Calculate (100 + 50) * 2 - 25",
    "What is the square root of 144?",
    "Calculate 25 * 47 + sqrt(144)"  # Multi-step
]

for calc in calculations:
    answer = processor.process(calc)
    print(f"Q: {calc}")
    print(f"A: {answer.answer}")
    print(f"Steps: {len(answer.metadata.get('reasoning_trace', []))}")
    print()
```

**Output**:
```
Q: What is 25 * 47?
A: The result is 1175.
Steps: 3

Q: Calculate 25 * 47 + sqrt(144)
A: The final result is 1187 (1175 + 12).
Steps: 8
```

---

### Use Case 3: Document Research

**Scenario**: Search and synthesize information from multiple documents

```python
# Document search triggers agent
research_queries = [
    "Find all mentions of transformers in the documentation",
    "What papers discuss attention mechanisms?",
    "Search for Python examples in the codebase"
]

for query in research_queries:
    answer = processor.process(query)
    print(f"Query: {query}")
    print(f"Answer: {answer.answer}")
    print(f"Tools used: {answer.metadata.get('tools_used', [])}")
    print()
```

---

### Use Case 4: Code Analysis

**Scenario**: Analyze Python code for bugs, complexity, etc.

```python
code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

query = f"Analyze this code for bugs and suggest improvements:\n{code}"
answer = processor.process(query)

print("Code Analysis:")
print(answer.answer)
print(f"\nComplexity: {answer.metadata.get('query_complexity')}")
print(f"Tools used: {answer.metadata.get('tools_used', [])}")
```

---

### Use Case 5: Multi-Step Workflows

**Scenario**: Complex queries requiring multiple tools

```python
# Multi-tool query
query = """
1. Search the documentation for Python performance tips
2. Analyze the code examples for complexity
3. Calculate the average time complexity
"""

answer = processor.process(query)
print("Multi-Step Result:")
print(answer.answer)
print(f"\nTools used: {answer.metadata.get('tools_used', [])}")
print(f"Number of tool calls: {answer.metadata.get('num_tool_calls', 0)}")
print(f"Execution time: {answer.metadata.get('execution_time', 0):.2f}s")
print(f"Total cost: ${answer.metadata.get('total_cost', 0):.4f}")
```

---

### Use Case 6: Multi-Turn Conversations

**Scenario**: Maintain context across multiple queries

```python
from src.components.query_processors.agents.memory import ConversationMemory

# Create processor with conversation memory
memory = ConversationMemory()
agent = ReActAgent(llm, tools, memory, agent_config)
processor = IntelligentQueryProcessor(
    retriever=my_retriever,
    generator=my_generator,
    agent=agent,
    query_analyzer=QueryAnalyzer(),
    config=processor_config
)

# Multi-turn conversation
queries = [
    "What is 25 * 47?",
    "Add 100 to that result",  # Refers to previous answer
    "Now divide by 5"  # Refers to cumulative result
]

for query in queries:
    answer = processor.process(query)
    print(f"User: {query}")
    print(f"Assistant: {answer.answer}\n")
```

**Output**:
```
User: What is 25 * 47?
Assistant: The result is 1175.

User: Add 100 to that result
Assistant: Adding 100 to 1175 gives 1275.

User: Now divide by 5
Assistant: Dividing 1275 by 5 gives 255.
```

---

## Configuration Guide

### Processor Configuration

```python
from src.components.query_processors.agents.models import ProcessorConfig

# Conservative (prefer RAG)
conservative_config = ProcessorConfig(
    use_agent_by_default=True,
    complexity_threshold=0.9,  # Only very complex queries use agent
    max_agent_cost=0.05,  # Low cost limit
    enable_planning=False  # Disable planning for speed
)

# Balanced (default)
balanced_config = ProcessorConfig(
    use_agent_by_default=True,
    complexity_threshold=0.7,  # Moderate threshold
    max_agent_cost=0.10,  # Reasonable limit
    enable_planning=True  # Enable planning
)

# Aggressive (prefer agent)
aggressive_config = ProcessorConfig(
    use_agent_by_default=True,
    complexity_threshold=0.5,  # Lower threshold
    max_agent_cost=0.25,  # Higher limit
    enable_planning=True,
    enable_parallel_execution=True  # Maximum performance
)

# RAG-only (no agent)
rag_only_config = ProcessorConfig(
    use_agent_by_default=False  # Disable agent entirely
)
```

### Agent Configuration

```python
from src.components.query_processors.agents.models import AgentConfig

# Fast (fewer iterations, shorter timeout)
fast_config = AgentConfig(
    llm_provider="openai",
    llm_model="gpt-4-turbo",
    temperature=0.5,  # Less creative
    max_tokens=1024,  # Shorter responses
    max_iterations=5,  # Fewer iterations
    max_execution_time=60,  # 1 minute timeout
    verbose=False
)

# Thorough (more iterations, longer timeout)
thorough_config = AgentConfig(
    llm_provider="openai",
    llm_model="gpt-4-turbo",
    temperature=0.7,  # Balanced creativity
    max_tokens=2048,  # Longer responses
    max_iterations=15,  # More iterations
    max_execution_time=600,  # 10 minute timeout
    verbose=True  # Debug logging
)

# Cost-optimized (cheaper model)
budget_config = AgentConfig(
    llm_provider="openai",
    llm_model="gpt-3.5-turbo",  # Cheaper model
    temperature=0.7,
    max_tokens=1024,
    max_iterations=10,
    max_execution_time=300
)
```

### Memory Configuration

```python
from src.components.query_processors.agents.memory import ConversationMemory

# Short-term (quick sessions)
short_memory = ConversationMemory(max_messages=20)

# Long-term (extended conversations)
long_memory = ConversationMemory(max_messages=200)

# Persistent (save/load across sessions)
persistent_memory = ConversationMemory(max_messages=100)
persistent_memory.load("session.json")  # Load previous session

# ... use memory ...

persistent_memory.save("session.json")  # Save for later
```

---

## Best Practices

### 1. Choose the Right Threshold

```python
# Match threshold to your use case
configs = {
    "chatbot": ProcessorConfig(complexity_threshold=0.8),  # Prefer fast RAG
    "research": ProcessorConfig(complexity_threshold=0.5),  # Prefer thorough agent
    "mixed": ProcessorConfig(complexity_threshold=0.7)  # Balanced
}

processor = IntelligentQueryProcessor(
    retriever=my_retriever,
    generator=my_generator,
    agent=my_agent,
    query_analyzer=QueryAnalyzer(),
    config=configs["chatbot"]  # Choose based on use case
)
```

### 2. Set Cost Budgets

```python
# Always set reasonable cost limits
config = ProcessorConfig(
    max_agent_cost=0.10  # $0.10 per query
)

# Monitor costs
answer = processor.process(query)
if answer.metadata.get("total_cost", 0) > 0.05:
    print(f"WARNING: High cost query: ${answer.metadata['total_cost']:.4f}")
```

### 3. Handle Errors Gracefully

```python
def safe_process(processor, query):
    """Process query with error handling."""
    try:
        answer = processor.process(query)

        # Check for agent failures
        if answer.metadata.get("agent_failed"):
            print("Agent failed, used RAG fallback")

        # Check for timeouts
        if answer.metadata.get("timeout_occurred"):
            print("Query timed out, partial results returned")

        return answer

    except Exception as e:
        print(f"Error processing query: {e}")
        return None

# Use safe wrapper
answer = safe_process(processor, "Complex query")
if answer:
    print(answer.answer)
```

### 4. Monitor Performance

```python
import time

def monitored_process(processor, query):
    """Process query with performance monitoring."""
    start_time = time.time()

    answer = processor.process(query)

    elapsed = time.time() - start_time
    metadata = answer.metadata

    print(f"Performance Metrics:")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Routing: {metadata.get('routing_decision')}")
    print(f"  Complexity: {metadata.get('query_complexity', 0):.2f}")
    print(f"  Cost: ${metadata.get('total_cost', 0):.4f}")

    if metadata.get("routing_decision") == "agent_system":
        print(f"  Tools used: {metadata.get('tools_used', [])}")
        print(f"  Reasoning steps: {len(metadata.get('reasoning_trace', []))}")

    return answer
```

### 5. Use Tool-Specific Configurations

```python
from src.components.query_processors.tools.implementations import (
    CalculatorTool,
    DocumentSearchTool,
    CodeAnalyzerTool
)

# Configure tools for your needs
tools = [
    CalculatorTool(),  # Default config
    DocumentSearchTool(
        index_path="data/indices",
        top_k=10  # Return more results
    ),
    CodeAnalyzerTool(
        max_file_size=10000  # Larger files
    )
]
```

### 6. Save and Resume Conversations

```python
from src.components.query_processors.agents.memory import ConversationMemory

# Start of session
memory = ConversationMemory()
agent = ReActAgent(llm, tools, memory, agent_config)

# ... process queries ...

# End of session - save
memory.save(f"conversation_{session_id}.json")

# New session - resume
memory = ConversationMemory()
memory.load(f"conversation_{session_id}.json")
agent = ReActAgent(llm, tools, memory, agent_config)

# Continue conversation with context
answer = processor.process("Continue from where we left off")
```

---

## Troubleshooting

### Problem: Agent not being used

**Symptoms**: All queries use RAG even when they seem complex

**Solutions**:
```python
# 1. Lower complexity threshold
config = ProcessorConfig(complexity_threshold=0.5)

# 2. Check query analysis
analyzer = QueryAnalyzer()
analysis = analyzer.analyze(your_query)
print(f"Complexity: {analysis.complexity}")
print(f"Requires tools: {analysis.requires_tools}")

# 3. Force agent usage
answer = processor.process(query, use_agent=True)
```

---

### Problem: High costs

**Symptoms**: Queries cost more than expected

**Solutions**:
```python
# 1. Set strict budget
config = ProcessorConfig(max_agent_cost=0.01)

# 2. Use cheaper model
agent_config = AgentConfig(
    llm_provider="openai",
    llm_model="gpt-3.5-turbo"  # Cheaper
)

# 3. Monitor and alert
answer = processor.process(query)
if answer.metadata.get("total_cost", 0) > 0.05:
    send_alert(f"High cost: ${answer.metadata['total_cost']:.4f}")
```

---

### Problem: Slow performance

**Symptoms**: Queries take too long

**Solutions**:
```python
# 1. Reduce max iterations
agent_config = AgentConfig(max_iterations=5)

# 2. Set timeout
agent_config = AgentConfig(max_execution_time=60)

# 3. Disable planning for simple queries
config = ProcessorConfig(enable_planning=False)

# 4. Use RAG for borderline queries
config = ProcessorConfig(complexity_threshold=0.8)
```

---

### Problem: Memory errors

**Symptoms**: Out of memory or memory not persisting

**Solutions**:
```python
# 1. Limit memory size
memory = ConversationMemory(max_messages=50)

# 2. Clear memory periodically
if len(memory.get_messages()) > 100:
    memory.clear()

# 3. Verify save/load
memory.save("test.json")
print(f"Saved {len(memory.get_messages())} messages")

new_memory = ConversationMemory()
new_memory.load("test.json")
print(f"Loaded {len(new_memory.get_messages())} messages")
```

---

### Problem: Agent timeout

**Symptoms**: Queries timeout before completion

**Solutions**:
```python
# 1. Increase timeout
agent_config = AgentConfig(max_execution_time=600)  # 10 minutes

# 2. Reduce complexity
# Break complex query into simpler sub-queries

# 3. Check tool performance
# Ensure tools respond quickly

# 4. Handle timeout gracefully
answer = processor.process(query)
if answer.metadata.get("timeout_occurred"):
    print("Query timed out, retrying with simpler approach...")
    answer = processor.process(query, use_agent=False)  # Fallback to RAG
```

---

### Problem: Incorrect tool selection

**Symptoms**: Agent uses wrong tools or no tools

**Solutions**:
```python
# 1. Check tool descriptions
for tool in tools:
    print(f"{tool.name}: {tool.description}")

# 2. Improve query phrasing
# Bad: "Do math"
# Good: "Calculate 25 * 47"

# 3. Examine reasoning trace
answer = processor.process(query)
for step in answer.metadata.get("reasoning_trace", []):
    print(f"{step.step_type}: {step.content}")
```

---

## Performance Tuning

### Optimize for Latency

```python
# Priority: Speed

# 1. Aggressive RAG routing (avoid agent overhead)
config = ProcessorConfig(
    complexity_threshold=0.9,  # Very high threshold
    enable_planning=False  # Skip planning
)

# 2. Fast agent configuration
agent_config = AgentConfig(
    max_iterations=3,  # Fewer iterations
    max_execution_time=30,  # Short timeout
    temperature=0.5  # Less exploration
)

# 3. Limited memory
memory = ConversationMemory(max_messages=20)
```

### Optimize for Accuracy

```python
# Priority: Best answers

# 1. Prefer agent for better reasoning
config = ProcessorConfig(
    complexity_threshold=0.5,  # Lower threshold
    enable_planning=True,
    enable_parallel_execution=True
)

# 2. Thorough agent configuration
agent_config = AgentConfig(
    llm_model="gpt-4-turbo",  # Best model
    max_iterations=15,  # More iterations
    max_execution_time=600,  # Longer timeout
    temperature=0.7  # Balanced
)

# 3. Extended memory
memory = ConversationMemory(max_messages=200)
```

### Optimize for Cost

```python
# Priority: Minimize expenses

# 1. Prefer RAG (cheaper)
config = ProcessorConfig(
    complexity_threshold=0.95,  # Almost never use agent
    max_agent_cost=0.01  # Very low limit
)

# 2. Budget model
agent_config = AgentConfig(
    llm_model="gpt-3.5-turbo",  # Cheaper
    max_iterations=5,  # Fewer iterations
    max_tokens=1024  # Shorter responses
)
```

---

## Advanced Usage

### Custom Tool Integration

```python
from src.components.query_processors.tools.base_tool import BaseTool
from src.components.query_processors.tools.models import ToolParameter, ToolResult

class CustomTool(BaseTool):
    """Custom tool implementation."""

    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="My custom tool for special tasks"
        )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="input",
                type="string",
                description="Input for custom processing",
                required=True
            )
        ]

    def execute(self, **kwargs) -> ToolResult:
        """Execute custom logic."""
        input_value = kwargs.get("input", "")

        # Your custom logic here
        result = f"Processed: {input_value}"

        return ToolResult(
            success=True,
            content=result
        )

# Use custom tool
tools = [CalculatorTool(), CustomTool()]
agent = ReActAgent(llm, tools, memory, agent_config)
```

### Programmatic Query Complexity Adjustment

```python
from src.components.query_processors.agents.planning import QueryAnalyzer
from src.components.query_processors.agents.models import QueryType

# Analyze before processing
analyzer = QueryAnalyzer()
analysis = analyzer.analyze(query)

# Adjust routing based on analysis
if analysis.query_type == QueryType.CODE:
    # Force agent for code queries
    answer = processor.process(query, use_agent=True)
elif analysis.complexity < 0.3:
    # Force RAG for very simple queries
    answer = processor.process(query, use_agent=False)
else:
    # Automatic routing
    answer = processor.process(query)
```

### Batch Processing

```python
def batch_process(processor, queries):
    """Process multiple queries efficiently."""
    results = []

    for query in queries:
        answer = processor.process(query)
        results.append({
            "query": query,
            "answer": answer.answer,
            "routing": answer.metadata.get("routing_decision"),
            "cost": answer.metadata.get("total_cost", 0),
            "time": answer.metadata.get("execution_time", 0)
        })

    # Aggregate statistics
    total_cost = sum(r["cost"] for r in results)
    total_time = sum(r["time"] for r in results)
    rag_count = sum(1 for r in results if r["routing"] == "rag_pipeline")
    agent_count = len(results) - rag_count

    print(f"Batch Statistics:")
    print(f"  Total queries: {len(results)}")
    print(f"  RAG queries: {rag_count}")
    print(f"  Agent queries: {agent_count}")
    print(f"  Total cost: ${total_cost:.4f}")
    print(f"  Total time: {total_time:.2f}s")

    return results
```

---

**Document Version**: 1.0
**Last Updated**: November 18, 2025
**Status**: ✅ Complete
