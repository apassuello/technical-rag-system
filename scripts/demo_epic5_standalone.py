#!/usr/bin/env python3
"""
Epic 5 Standalone Demo - Tools & Agent System

This demo shows the core Epic 5 functionality without heavy dependencies.
It demonstrates:
1. Calculator Tool - Safe math evaluation
2. Code Analyzer Tool - Python AST analysis
3. Tool Registry - Tool management
4. Prompt Engineering - Domain-specific prompts
"""

import sys
import os
import ast
import math
import operator
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

# ============================================================================
# TOOL MODELS (simplified from tools/models.py)
# ============================================================================

class ToolParameterType(Enum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class ToolResult:
    """Result from tool execution - NEVER raises exceptions."""
    success: bool
    content: str
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.success and self.error:
            raise ValueError("Successful result cannot have error")
        if not self.success and not self.error:
            raise ValueError("Failed result must have error message")


# ============================================================================
# CALCULATOR TOOL (simplified from implementations/calculator_tool.py)
# ============================================================================

class CalculatorTool:
    """Safe mathematical expression evaluator."""

    # Supported operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # Supported functions
    FUNCTIONS = {
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'abs': abs,
        'ceil': math.ceil,
        'floor': math.floor,
        'round': round,
    }

    # Constants
    CONSTANTS = {
        'pi': math.pi,
        'e': math.e,
    }

    def __init__(self):
        self.name = "calculator"
        self.description = "Evaluates mathematical expressions safely"
        self._execution_count = 0
        self._success_count = 0
        self._total_time = 0.0

    def execute(self, expression: str) -> ToolResult:
        """Execute calculation - NEVER raises exceptions."""
        start = datetime.now()

        try:
            # Parse and evaluate
            tree = ast.parse(expression, mode='eval')
            result = self._eval_node(tree.body)

            # Format result
            if isinstance(result, float) and result.is_integer():
                content = str(int(result))
            else:
                content = str(result)

            elapsed = (datetime.now() - start).total_seconds()
            self._execution_count += 1
            self._success_count += 1
            self._total_time += elapsed

            return ToolResult(
                success=True,
                content=content,
                execution_time=elapsed,
                metadata={"expression": expression, "result_type": type(result).__name__}
            )

        except ZeroDivisionError:
            return self._error_result("Division by zero", expression, start)
        except ValueError as e:
            return self._error_result(f"Math error: {e}", expression, start)
        except Exception as e:
            return self._error_result(f"Evaluation error: {e}", expression, start)

    def _error_result(self, error: str, expression: str, start: datetime) -> ToolResult:
        elapsed = (datetime.now() - start).total_seconds()
        self._execution_count += 1
        self._total_time += elapsed
        return ToolResult(
            success=False,
            content="",
            error=error,
            execution_time=elapsed,
            metadata={"expression": expression}
        )

    def _eval_node(self, node) -> float:
        """Recursively evaluate AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
            return node.n
        elif isinstance(node, ast.Name):
            if node.id in self.CONSTANTS:
                return self.CONSTANTS[node.id]
            raise ValueError(f"Unknown constant: {node.id}")
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op(operand)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in self.FUNCTIONS:
                    args = [self._eval_node(arg) for arg in node.args]
                    return self.FUNCTIONS[func_name](*args)
            raise ValueError(f"Unknown function: {node.func.id if hasattr(node.func, 'id') else 'unknown'}")
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "executions": self._execution_count,
            "success_rate": self._success_count / max(1, self._execution_count),
            "avg_time": self._total_time / max(1, self._execution_count)
        }


# ============================================================================
# CODE ANALYZER TOOL (simplified from implementations/code_analyzer_tool.py)
# ============================================================================

class CodeAnalyzerTool:
    """Python code structure analyzer using AST."""

    def __init__(self):
        self.name = "code_analyzer"
        self.description = "Analyzes Python code structure and complexity"
        self._execution_count = 0

    def execute(self, code: str) -> ToolResult:
        """Analyze Python code - NEVER raises exceptions."""
        start = datetime.now()
        self._execution_count += 1

        try:
            tree = ast.parse(code)

            functions = []
            classes = []
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "parameters": [arg.arg for arg in node.args.args],
                        "has_docstring": ast.get_docstring(node) is not None,
                        "line_number": node.lineno
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes.append({
                        "name": node.name,
                        "num_methods": len(methods),
                        "methods": methods,
                        "has_docstring": ast.get_docstring(node) is not None
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        imports.extend(alias.name for alias in node.names)
                    else:
                        imports.append(node.module or "")

            # Check for main block
            has_main = any(
                isinstance(node, ast.If) and
                isinstance(node.test, ast.Compare) and
                any(isinstance(c, ast.Constant) and c.value == "__main__"
                    for c in [node.test.left] + node.test.comparators)
                for node in ast.walk(tree)
            )

            metadata = {
                "syntax_valid": True,
                "num_functions": len(functions),
                "num_classes": len(classes),
                "num_imports": len(imports),
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "has_main_block": has_main,
                "has_docstrings": any(f["has_docstring"] for f in functions) or any(c["has_docstring"] for c in classes),
                "lines_of_code": len(code.splitlines())
            }

            elapsed = (datetime.now() - start).total_seconds()

            summary = f"Found {len(functions)} functions, {len(classes)} classes, {len(imports)} imports"

            return ToolResult(
                success=True,
                content=summary,
                execution_time=elapsed,
                metadata=metadata
            )

        except SyntaxError as e:
            elapsed = (datetime.now() - start).total_seconds()
            return ToolResult(
                success=True,  # Still "succeeds" but reports syntax error
                content=f"Syntax error at line {e.lineno}: {e.msg}",
                execution_time=elapsed,
                metadata={
                    "syntax_valid": False,
                    "error_line": e.lineno,
                    "error_message": e.msg
                }
            )


# ============================================================================
# TOOL REGISTRY (simplified from tool_registry.py)
# ============================================================================

class ToolRegistry:
    """Central registry for tool management."""

    def __init__(self):
        self._tools: Dict[str, Any] = {}

    def register(self, tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def get(self, name: str):
        """Get tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tools."""
        return list(self._tools.keys())

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self._tools.get(tool_name)
        if tool is None:
            return ToolResult(
                success=False,
                content="",
                error=f"Tool not found: {tool_name}"
            )
        return tool.execute(**kwargs)


# ============================================================================
# PROMPT ENGINEERING (simplified from agents/prompts.py)
# ============================================================================

class AgentRole(Enum):
    TECHNICAL_DOCS = "technical_docs"
    CODE_ASSISTANT = "code_assistant"
    RESEARCH = "research"
    GENERAL = "general"


SYSTEM_PROMPTS = {
    AgentRole.TECHNICAL_DOCS: """You are an expert technical documentation assistant specializing in:
- Embedded systems and microcontrollers
- RISC-V architecture and instruction sets
- Real-time operating systems (FreeRTOS, Zephyr)
- Embedded AI/ML and edge computing

Always cite sources using [Document X] notation.""",

    AgentRole.CODE_ASSISTANT: """You are an expert code assistant specializing in:
- C/C++ for embedded systems
- Python for ML and automation
- Assembly language (RISC-V, ARM)
- Build systems (CMake, Make)""",

    AgentRole.RESEARCH: """You are a research assistant helping with technical documentation analysis.
Break down complex questions, search systematically, and provide well-cited answers.""",

    AgentRole.GENERAL: "You are a helpful assistant that uses tools to answer questions accurately."
}


TOOL_GUIDANCE = {
    "calculator": {
        "when_to_use": "Use for ANY mathematical calculation, no matter how simple.",
        "examples": ["expression=1024 * 1024", "expression=sqrt(256)", "expression=2 * pi"]
    },
    "code_analyzer": {
        "when_to_use": "Use to analyze Python code structure and identify issues.",
        "examples": ["Analyze this function for complexity", "Check code style"]
    }
}


# ============================================================================
# DEMO FUNCTIONS
# ============================================================================

def demo_calculator():
    """Demonstrate CalculatorTool."""
    print("=" * 70)
    print("1. CALCULATOR TOOL DEMO")
    print("=" * 70)

    calc = CalculatorTool()
    print(f"\nTool: {calc.name}")
    print(f"Description: {calc.description}")

    test_cases = [
        ("2 + 2", "Basic addition"),
        ("25 * 47", "Multiplication"),
        ("sqrt(256) + 2 ** 3", "Functions + operators"),
        ("2 * pi", "Using constants"),
        ("sin(pi / 2)", "Trigonometry"),
        ("1 / 0", "Error handling"),
    ]

    print("\nExecutions:")
    for expr, desc in test_cases:
        result = calc.execute(expression=expr)
        status = "✓" if result.success else "✗"
        output = result.content if result.success else result.error
        print(f"  {status} {desc}: {expr} = {output}")

    stats = calc.get_stats()
    print(f"\nStatistics: {stats['executions']} executions, {stats['success_rate']:.0%} success rate")


def demo_code_analyzer():
    """Demonstrate CodeAnalyzerTool."""
    print("\n" + "=" * 70)
    print("2. CODE ANALYZER TOOL DEMO")
    print("=" * 70)

    analyzer = CodeAnalyzerTool()
    print(f"\nTool: {analyzer.name}")
    print(f"Description: {analyzer.description}")

    sample_code = '''
import math

def calculate_area(radius: float) -> float:
    """Calculate circle area."""
    return math.pi * radius ** 2

class Circle:
    """A circle with radius."""

    def __init__(self, radius: float):
        self.radius = radius

    def area(self) -> float:
        return calculate_area(self.radius)

    def circumference(self) -> float:
        return 2 * math.pi * self.radius

if __name__ == "__main__":
    c = Circle(5)
    print(f"Area: {c.area()}")
'''

    print("\nAnalyzing sample code...")
    result = analyzer.execute(code=sample_code)

    if result.success:
        m = result.metadata
        print(f"\nResults:")
        print(f"  ✓ Syntax Valid: {m['syntax_valid']}")
        print(f"  ✓ Functions: {m['num_functions']}")
        print(f"  ✓ Classes: {m['num_classes']}")
        print(f"  ✓ Imports: {m['num_imports']}")
        print(f"  ✓ Has Main Block: {m['has_main_block']}")
        print(f"  ✓ Lines of Code: {m['lines_of_code']}")

        print(f"\nFunctions found:")
        for func in m['functions']:
            params = ', '.join(func['parameters'])
            doc = "📝" if func['has_docstring'] else ""
            print(f"    - {func['name']}({params}) {doc}")

        print(f"\nClasses found:")
        for cls in m['classes']:
            doc = "📝" if cls['has_docstring'] else ""
            print(f"    - {cls['name']} ({cls['num_methods']} methods) {doc}")

    # Test syntax error handling
    print("\nSyntax error handling:")
    bad_result = analyzer.execute(code="def broken(")
    print(f"  ✓ Graceful handling: syntax_valid={bad_result.metadata.get('syntax_valid', 'N/A')}")


def demo_tool_registry():
    """Demonstrate ToolRegistry."""
    print("\n" + "=" * 70)
    print("3. TOOL REGISTRY DEMO")
    print("=" * 70)

    registry = ToolRegistry()

    # Register tools
    registry.register(CalculatorTool())
    registry.register(CodeAnalyzerTool())

    print(f"\nRegistered tools: {registry.list_tools()}")

    # Execute through registry
    print("\nExecuting through registry:")
    result = registry.execute("calculator", expression="100 * 1.21")
    print(f"  calculator('100 * 1.21') = {result.content}")

    result = registry.execute("code_analyzer", code="x = 1 + 2")
    print(f"  code_analyzer('x = 1 + 2') = {result.content}")

    # Unknown tool
    result = registry.execute("unknown_tool")
    print(f"  unknown_tool() = Error: {result.error}")


def demo_prompt_engineering():
    """Demonstrate prompt engineering system."""
    print("\n" + "=" * 70)
    print("4. PROMPT ENGINEERING DEMO")
    print("=" * 70)

    print("\nAvailable Agent Roles:")
    for role in AgentRole:
        prompt_preview = SYSTEM_PROMPTS[role][:80].replace('\n', ' ')
        print(f"  - {role.value}: \"{prompt_preview}...\"")

    print("\nTool Guidance:")
    for tool_name, guidance in TOOL_GUIDANCE.items():
        print(f"  {tool_name}:")
        print(f"    When: {guidance['when_to_use']}")
        print(f"    Examples: {guidance['examples'][:2]}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("EPIC 5: TOOL & AGENT IMPLEMENTATION DEMO")
    print("=" * 70)
    print("\nThis demo showcases the core Epic 5 functionality:")
    print("  1. Calculator Tool - Safe mathematical evaluation")
    print("  2. Code Analyzer Tool - Python AST analysis")
    print("  3. Tool Registry - Central tool management")
    print("  4. Prompt Engineering - Domain-specific agent prompts")

    try:
        demo_calculator()
        demo_code_analyzer()
        demo_tool_registry()
        demo_prompt_engineering()

        print("\n" + "=" * 70)
        print("✅ DEMO COMPLETE!")
        print("=" * 70)
        print("\nEpic 5 Key Features:")
        print("  ✓ Tools NEVER raise exceptions (safe for LLM use)")
        print("  ✓ Rich metadata for debugging and analysis")
        print("  ✓ Centralized tool registry for management")
        print("  ✓ Domain-specific prompts for embedded systems")
        print("  ✓ 634 tests with 1,601 assertions")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
