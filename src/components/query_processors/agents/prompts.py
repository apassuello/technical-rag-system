"""
Prompt templates for Epic 5 Agent System.

This module provides domain-specific prompt engineering for the agent system,
optimized for technical documentation queries about embedded systems, RISC-V,
RTOS, and AI/ML topics.

Key Features:
- Domain-specific system prompts
- Few-shot examples for tool use
- Configurable prompt templates
- Integration with TechnicalPromptTemplates

Usage:
    >>> from src.components.query_processors.agents.prompts import (
    ...     TechnicalReActPrompt,
    ...     get_system_prompt,
    ...     get_tool_guidance
    ... )
    >>>
    >>> # Get configured prompt
    >>> prompt = TechnicalReActPrompt.get_react_prompt()
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class AgentRole(Enum):
    """Agent role specializations."""
    TECHNICAL_DOCS = "technical_docs"
    CODE_ASSISTANT = "code_assistant"
    RESEARCH = "research"
    GENERAL = "general"


@dataclass
class ToolGuidance:
    """Guidance for when and how to use a specific tool."""
    name: str
    when_to_use: str
    example_queries: List[str]
    tips: List[str]


# =============================================================================
# System Prompts
# =============================================================================

TECHNICAL_DOCS_SYSTEM_PROMPT = """You are an expert technical documentation assistant specializing in:
- Embedded systems and microcontrollers
- RISC-V architecture and instruction sets
- Real-time operating systems (FreeRTOS, Zephyr, etc.)
- Embedded AI/ML and edge computing
- Hardware-software integration

Your role is to provide accurate, detailed technical answers by:
1. Using available tools to gather information and perform calculations
2. Always citing sources from retrieved documents using [Document X] notation
3. Maintaining technical accuracy with correct terminology
4. Considering hardware constraints and embedded system limitations
5. Providing code examples when relevant

Guidelines:
- Think step-by-step before taking actions
- Use the calculator tool for ANY mathematical calculations - never estimate
- Use document_search to find relevant technical documentation
- Use code_analyzer for understanding code snippets
- If information is not available, clearly state this
- Be precise with technical specifications (clock speeds, memory sizes, etc.)
"""

CODE_ASSISTANT_SYSTEM_PROMPT = """You are an expert code assistant specializing in embedded systems programming.

Your expertise includes:
- C/C++ for embedded systems
- Python for ML and automation
- Assembly language (RISC-V, ARM)
- Build systems (CMake, Make)
- Debugging and optimization

Guidelines:
- Analyze code thoroughly before providing answers
- Consider memory constraints and performance implications
- Suggest optimizations specific to embedded platforms
- Use the code_analyzer tool for code inspection
- Provide working code examples when possible
"""

RESEARCH_SYSTEM_PROMPT = """You are a research assistant helping with technical documentation analysis.

Your approach:
- Break down complex questions into sub-queries
- Search documentation systematically
- Synthesize information from multiple sources
- Identify gaps in available information
- Provide comprehensive, well-cited answers

Always cite your sources using [Document X] notation.
"""


# =============================================================================
# ReAct Prompt Templates
# =============================================================================

class TechnicalReActPrompt:
    """
    Domain-specific ReAct prompt templates for technical documentation.

    Provides enhanced prompts with:
    - Technical domain context
    - Tool usage guidance
    - Few-shot examples
    - Citation requirements
    """

    # Base ReAct template with domain context
    REACT_TEMPLATE = """{system_prompt}

You have access to the following tools:

{tools}

IMPORTANT Tool Usage Guidelines:
{tool_guidance}

Use the following format for your reasoning:

Question: the input question you must answer
Thought: think about what information you need and which tool to use
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action (be specific and complete)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation cycle can repeat as needed)
Thought: I now have enough information to provide a complete answer
Final Answer: provide a comprehensive answer with citations [Document X]

{few_shot_examples}

Now answer the following question:

Question: {input}
Thought: {agent_scratchpad}"""

    # Few-shot examples for tool use
    FEW_SHOT_EXAMPLES = """
Examples of good tool usage:

Example 1 - Calculation:
Question: What is the memory bandwidth if we have a 32-bit bus running at 100MHz?
Thought: I need to calculate the memory bandwidth. This requires multiplying the bus width by the clock frequency.
Action: calculator
Action Input: expression=32 * 100000000 / 8
Observation: 400000000.0
Thought: The result is 400,000,000 bytes per second, or 400 MB/s. I should present this clearly.
Final Answer: The memory bandwidth for a 32-bit bus at 100MHz is 400 MB/s (400,000,000 bytes/second) [Document 1]. This is calculated as: (32 bits × 100 MHz) / 8 bits per byte = 400 MB/s.

Example 2 - Document Search:
Question: How does FreeRTOS handle task priorities?
Thought: I need to search the documentation for information about FreeRTOS task priority handling.
Action: document_search
Action Input: query=FreeRTOS task priority scheduling preemption
Observation: [Retrieved documents about FreeRTOS scheduling...]
Thought: I found relevant information about FreeRTOS priority-based scheduling.
Final Answer: FreeRTOS uses a priority-based preemptive scheduler [Document 1]. Tasks with higher priority values have higher priority and will preempt lower-priority tasks when they become ready to run [Document 2]. The scheduler always runs the highest priority ready task...

Example 3 - Multi-step reasoning:
Question: Calculate the maximum interrupt latency for a system with 10 interrupts at 1MHz clock.
Thought: This requires understanding interrupt handling and then calculating. Let me first search for interrupt latency information.
Action: document_search
Action Input: query=interrupt latency calculation embedded systems
Observation: [Documents about interrupt handling...]
Thought: Now I understand the factors. I need to calculate based on the worst-case scenario.
Action: calculator
Action Input: expression=10 * (1 / 1000000) * 1000000
Observation: 10.0
Thought: I can now provide a complete answer with both the theory and calculation.
Final Answer: The maximum interrupt latency in a system with 10 interrupts at 1MHz is approximately 10 microseconds in the worst case [Document 1]. This assumes each interrupt takes one clock cycle to acknowledge...
"""

    # Tool-specific guidance
    TOOL_GUIDANCE = {
        "calculator": ToolGuidance(
            name="calculator",
            when_to_use="Use for ANY mathematical calculation, no matter how simple. Never estimate or calculate mentally.",
            example_queries=[
                "Calculate clock cycles: expression=1000000000 / 100",
                "Memory size: expression=1024 * 1024 * 64",
                "Timing: expression=1 / 115200 * 1000000"
            ],
            tips=[
                "Always use explicit numbers, not abbreviations (1000000 not 1M)",
                "Use parentheses for complex expressions",
                "Convert units in the expression when needed"
            ]
        ),
        "document_search": ToolGuidance(
            name="document_search",
            when_to_use="Use to find technical documentation, specifications, or explanations. Search before answering factual questions.",
            example_queries=[
                "query=RISC-V interrupt handling mechanism",
                "query=FreeRTOS queue implementation best practices",
                "query=embedded neural network optimization techniques"
            ],
            tips=[
                "Use specific technical terms in queries",
                "Search for concepts, not exact phrases",
                "Combine related terms: 'RISC-V vector extension performance'"
            ]
        ),
        "code_analyzer": ToolGuidance(
            name="code_analyzer",
            when_to_use="Use to analyze code snippets, understand implementations, or identify issues.",
            example_queries=[
                "Analyze this interrupt handler for potential issues",
                "Check memory allocation patterns in this code",
                "Identify optimization opportunities"
            ],
            tips=[
                "Provide complete code context when possible",
                "Specify what aspect to analyze (performance, safety, style)",
                "Include relevant constraints (memory limit, real-time requirements)"
            ]
        )
    }

    @classmethod
    def get_system_prompt(cls, role: AgentRole = AgentRole.TECHNICAL_DOCS) -> str:
        """
        Get system prompt for specified role.

        Args:
            role: Agent role specialization

        Returns:
            System prompt string
        """
        prompts = {
            AgentRole.TECHNICAL_DOCS: TECHNICAL_DOCS_SYSTEM_PROMPT,
            AgentRole.CODE_ASSISTANT: CODE_ASSISTANT_SYSTEM_PROMPT,
            AgentRole.RESEARCH: RESEARCH_SYSTEM_PROMPT,
            AgentRole.GENERAL: "You are a helpful assistant that uses tools to answer questions accurately."
        }
        return prompts.get(role, prompts[AgentRole.GENERAL])

    @classmethod
    def get_tool_guidance(cls, tool_names: List[str]) -> str:
        """
        Get formatted tool guidance for specified tools.

        Args:
            tool_names: List of tool names to include guidance for

        Returns:
            Formatted tool guidance string
        """
        guidance_parts = []
        for name in tool_names:
            if name in cls.TOOL_GUIDANCE:
                g = cls.TOOL_GUIDANCE[name]
                guidance_parts.append(f"""
- {g.name.upper()}:
  When to use: {g.when_to_use}
  Tips: {'; '.join(g.tips)}""")

        if not guidance_parts:
            return "Use tools appropriately based on their descriptions."

        return "\n".join(guidance_parts)

    @classmethod
    def get_react_prompt(
        cls,
        role: AgentRole = AgentRole.TECHNICAL_DOCS,
        include_few_shot: bool = True,
        tool_names: Optional[List[str]] = None
    ) -> str:
        """
        Get complete ReAct prompt template.

        Args:
            role: Agent role for system prompt
            include_few_shot: Whether to include few-shot examples
            tool_names: List of available tool names for guidance

        Returns:
            Complete prompt template string
        """
        system_prompt = cls.get_system_prompt(role)
        tool_guidance = cls.get_tool_guidance(tool_names or ["calculator", "document_search", "code_analyzer"])
        few_shot = cls.FEW_SHOT_EXAMPLES if include_few_shot else ""

        return cls.REACT_TEMPLATE.format(
            system_prompt=system_prompt,
            tools="{tools}",
            tool_names="{tool_names}",
            tool_guidance=tool_guidance,
            few_shot_examples=few_shot,
            input="{input}",
            agent_scratchpad="{agent_scratchpad}"
        )


# =============================================================================
# Query Decomposition Prompts
# =============================================================================

QUERY_DECOMPOSITION_PROMPT = """You are a technical query analyst. Break down complex queries into clear sub-tasks.

Query: {query}

Query Analysis:
- Type: {query_type}
- Complexity: {complexity:.2f}
- Domain: {domain}
- Required Tools: {required_tools}

Instructions:
1. Identify distinct sub-tasks needed to fully answer the query
2. Order tasks by dependency (independent tasks first)
3. Specify which tools each task needs
4. Keep tasks focused and atomic

For each sub-task, provide:
- description: What needs to be done
- query: Specific question or instruction
- required_tools: List of tools needed
- dependencies: IDs of prerequisite tasks
- can_run_parallel: Whether this can run with other tasks

Output as JSON array. Maximum {max_tasks} sub-tasks.

Example output:
[
  {{
    "description": "Calculate memory requirements",
    "query": "What is 1024 * 64 * 8 bytes?",
    "required_tools": ["calculator"],
    "dependencies": [],
    "can_run_parallel": true
  }},
  {{
    "description": "Find memory optimization techniques",
    "query": "What are memory optimization techniques for embedded systems?",
    "required_tools": ["document_search"],
    "dependencies": [],
    "can_run_parallel": true
  }},
  {{
    "description": "Synthesize recommendations",
    "query": "Based on the memory size and techniques, what do you recommend?",
    "required_tools": [],
    "dependencies": ["task_0", "task_1"],
    "can_run_parallel": false
  }}
]

Now decompose this query:"""


# =============================================================================
# Convenience Functions
# =============================================================================

def get_system_prompt(role: AgentRole = AgentRole.TECHNICAL_DOCS) -> str:
    """Get system prompt for specified role."""
    return TechnicalReActPrompt.get_system_prompt(role)


def get_tool_guidance(tool_names: List[str]) -> str:
    """Get tool guidance for specified tools."""
    return TechnicalReActPrompt.get_tool_guidance(tool_names)


def get_react_prompt(
    role: AgentRole = AgentRole.TECHNICAL_DOCS,
    include_few_shot: bool = True,
    tool_names: Optional[List[str]] = None
) -> str:
    """Get complete ReAct prompt template."""
    return TechnicalReActPrompt.get_react_prompt(role, include_few_shot, tool_names)


__all__ = [
    "AgentRole",
    "ToolGuidance",
    "TechnicalReActPrompt",
    "TECHNICAL_DOCS_SYSTEM_PROMPT",
    "CODE_ASSISTANT_SYSTEM_PROMPT",
    "RESEARCH_SYSTEM_PROMPT",
    "QUERY_DECOMPOSITION_PROMPT",
    "get_system_prompt",
    "get_tool_guidance",
    "get_react_prompt",
]
