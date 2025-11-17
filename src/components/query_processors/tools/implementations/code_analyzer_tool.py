"""
Code analyzer tool for Python code analysis.

Provides LLMs with the ability to analyze Python code for syntax,
structure, and basic metrics without executing the code.

Architecture:
- Safe code analysis using ast module (no execution)
- Extracts structural information (functions, classes, imports)
- Detects syntax errors
- NEVER raises exceptions (returns errors in ToolResult)
- Comprehensive analysis results
- Clear error messages for LLM understanding

Usage:
    >>> from src.components.query_processors.tools.implementations import CodeAnalyzerTool
    >>>
    >>> analyzer = CodeAnalyzerTool()
    >>> code = '''
    ... def hello(name):
    ...     return f"Hello, {name}!"
    ... '''
    >>> result = analyzer.execute(code=code)
    >>> print(result.content)
    # Analysis output showing functions, complexity, etc.
"""

import ast
from typing import List, Dict, Any, Set
import logging

from ..base_tool import BaseTool
from ..models import ToolParameter, ToolParameterType, ToolResult


logger = logging.getLogger(__name__)


class CodeAnalyzerTool(BaseTool):
    """
    Safe Python code analyzer using AST.

    Analyzes Python code structure without executing it, providing
    insights about functions, classes, imports, and potential issues.

    Features:
    - Syntax validation
    - Function and class extraction
    - Import analysis
    - Complexity metrics (basic)
    - Docstring detection
    - Safe (no code execution)

    Analysis Includes:
    - Syntax validity
    - Number of functions and classes
    - List of imports
    - Function signatures
    - Basic complexity metrics
    - Docstring coverage

    Example:
        >>> tool = CodeAnalyzerTool()
        >>> code = '''
        ... import math
        ...
        ... def calculate_area(radius):
        ...     \"\"\"Calculate circle area.\"\"\"
        ...     return math.pi * radius ** 2
        ...
        ... class Circle:
        ...     def __init__(self, radius):
        ...         self.radius = radius
        ... '''
        >>> result = tool.execute(code=code)
        >>> print(result.content)
        # Shows: valid syntax, 1 function, 1 class, 1 import, etc.
    """

    def __init__(self):
        """
        Initialize code analyzer tool.

        Sets up AST parser and analysis rules.
        """
        super().__init__()
        self._logger.info("Initialized CodeAnalyzerTool")

    @property
    def name(self) -> str:
        """
        Tool name.

        Returns:
            "analyze_code"
        """
        return "analyze_code"

    @property
    def description(self) -> str:
        """
        Tool description for LLM.

        Returns:
            Clear description of code analysis capabilities
        """
        return (
            "Analyzes Python code for structure, syntax, and basic metrics. "
            "Does NOT execute the code (safe analysis only). "
            "Returns information about functions, classes, imports, syntax validity, "
            "and basic complexity metrics. "
            "Use this tool to understand code structure, check syntax, "
            "or analyze code before using it."
        )

    def get_parameters(self) -> List[ToolParameter]:
        """
        Get tool parameter definitions.

        Returns:
            List containing single 'code' parameter
        """
        return [
            ToolParameter(
                name="code",
                type=ToolParameterType.STRING,
                description=(
                    "Python code to analyze. Can be any valid Python code. "
                    "The code will NOT be executed, only analyzed for structure. "
                    "Example: 'def hello(): return \"world\"'"
                ),
                required=True
            )
        ]

    def execute(self, code: str) -> ToolResult:
        """
        Execute code analysis.

        Args:
            code: Python code to analyze

        Returns:
            ToolResult with:
            - success=True, content=analysis results on success
            - success=False, error=description on syntax/parse errors

        Example:
            >>> result = tool.execute(code="def foo(): pass")
            >>> print(result.content)
            # Analysis showing valid syntax, 1 function, etc.
        """
        try:
            # Validate input
            if code is None:
                return ToolResult(
                    success=False,
                    error="Code cannot be None"
                )

            if not code.strip():
                return ToolResult(
                    success=False,
                    error="Code cannot be empty"
                )

            # Log execution
            self._logger.debug(f"Analyzing code ({len(code)} characters)")

            # Parse code into AST
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                # Syntax error is not a tool failure - it's a valid analysis result
                return ToolResult(
                    success=True,
                    content=self._format_syntax_error(e),
                    metadata={
                        "syntax_valid": False,
                        "error_type": "SyntaxError",
                        "error_line": e.lineno,
                        "error_msg": str(e)
                    }
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Failed to parse code: {str(e)}"
                )

            # Analyze the AST
            analysis = self._analyze_ast(tree, code)

            # Format results
            formatted_analysis = self._format_analysis(analysis)

            self._logger.debug("Code analysis completed successfully")

            return ToolResult(
                success=True,
                content=formatted_analysis,
                metadata=analysis
            )

        except Exception as e:
            # This should never happen (all exceptions should be caught above)
            # But we handle it anyway for absolute safety
            self._logger.error(f"Unexpected error in code analyzer: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )

    def _analyze_ast(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """
        Analyze AST to extract code structure information.

        Args:
            tree: Parsed AST
            code: Original code string

        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "syntax_valid": True,
            "num_functions": 0,
            "num_classes": 0,
            "num_imports": 0,
            "functions": [],
            "classes": [],
            "imports": [],
            "has_main_block": False,
            "lines_of_code": len(code.splitlines()),
            "num_statements": 0,
        }

        # Walk the AST
        for node in ast.walk(tree):
            # Count statement types
            if isinstance(node, ast.stmt):
                analysis["num_statements"] += 1

            # Function definitions
            if isinstance(node, ast.FunctionDef):
                analysis["num_functions"] += 1
                func_info = self._analyze_function(node)
                analysis["functions"].append(func_info)

            # Class definitions
            elif isinstance(node, ast.ClassDef):
                analysis["num_classes"] += 1
                class_info = self._analyze_class(node)
                analysis["classes"].append(class_info)

            # Import statements
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                analysis["num_imports"] += 1
                import_info = self._analyze_import(node)
                analysis["imports"].extend(import_info)

            # Check for if __name__ == "__main__": block
            elif isinstance(node, ast.If):
                if self._is_main_block(node):
                    analysis["has_main_block"] = True

        # Calculate additional metrics
        analysis["avg_function_complexity"] = (
            sum(f["num_statements"] for f in analysis["functions"]) / analysis["num_functions"]
            if analysis["num_functions"] > 0
            else 0
        )

        analysis["has_docstrings"] = any(
            f["has_docstring"] for f in analysis["functions"]
        ) or any(
            c["has_docstring"] for c in analysis["classes"]
        )

        return analysis

    def _analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """
        Analyze a function definition.

        Args:
            node: FunctionDef AST node

        Returns:
            Dictionary with function information
        """
        # Get parameters
        params = []
        for arg in node.args.args:
            params.append(arg.arg)

        # Check for docstring
        has_docstring = (
            len(node.body) > 0 and
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)
        )

        # Count statements in function
        num_statements = len([n for n in ast.walk(node) if isinstance(n, ast.stmt)])

        return {
            "name": node.name,
            "parameters": params,
            "num_parameters": len(params),
            "has_docstring": has_docstring,
            "num_statements": num_statements,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
        }

    def _analyze_class(self, node: ast.ClassDef) -> Dict[str, Any]:
        """
        Analyze a class definition.

        Args:
            node: ClassDef AST node

        Returns:
            Dictionary with class information
        """
        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)

        # Check for docstring
        has_docstring = (
            len(node.body) > 0 and
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)
        )

        # Count methods
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        num_methods = len(methods)

        return {
            "name": node.name,
            "base_classes": bases,
            "num_methods": num_methods,
            "has_docstring": has_docstring,
        }

    def _analyze_import(self, node: ast.AST) -> List[str]:
        """
        Analyze import statement.

        Args:
            node: Import or ImportFrom AST node

        Returns:
            List of imported module/name strings
        """
        imports = []

        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                if module:
                    imports.append(f"{module}.{alias.name}")
                else:
                    imports.append(alias.name)

        return imports

    def _is_main_block(self, node: ast.If) -> bool:
        """
        Check if node is a if __name__ == "__main__": block.

        Args:
            node: If AST node

        Returns:
            True if this is a main block
        """
        if not isinstance(node.test, ast.Compare):
            return False

        test = node.test
        if not isinstance(test.left, ast.Name) or test.left.id != "__name__":
            return False

        if not test.ops or not isinstance(test.ops[0], ast.Eq):
            return False

        if not test.comparators:
            return False

        comparator = test.comparators[0]
        if isinstance(comparator, ast.Constant):
            return comparator.value == "__main__"

        return False

    def _format_syntax_error(self, error: SyntaxError) -> str:
        """
        Format syntax error for LLM understanding.

        Args:
            error: SyntaxError exception

        Returns:
            Formatted error message
        """
        lines = ["Code Analysis: SYNTAX ERROR"]
        lines.append("")
        lines.append(f"Error: {error.msg}")

        if error.lineno:
            lines.append(f"Line: {error.lineno}")

        if error.offset:
            lines.append(f"Column: {error.offset}")

        if error.text:
            lines.append("")
            lines.append("Problematic line:")
            lines.append(f"  {error.text.rstrip()}")
            if error.offset:
                lines.append(f"  {' ' * (error.offset - 1)}^")

        lines.append("")
        lines.append("The code contains syntax errors and cannot be analyzed further.")

        return "\n".join(lines)

    def _format_analysis(self, analysis: Dict[str, Any]) -> str:
        """
        Format analysis results for LLM consumption.

        Args:
            analysis: Analysis results dictionary

        Returns:
            Formatted analysis string
        """
        lines = ["Code Analysis: SUCCESS"]
        lines.append("")

        # Basic metrics
        lines.append("=== Basic Metrics ===")
        lines.append(f"Syntax Valid: Yes")
        lines.append(f"Lines of Code: {analysis['lines_of_code']}")
        lines.append(f"Total Statements: {analysis['num_statements']}")
        lines.append(f"Functions: {analysis['num_functions']}")
        lines.append(f"Classes: {analysis['num_classes']}")
        lines.append(f"Imports: {analysis['num_imports']}")
        lines.append(f"Has Main Block: {'Yes' if analysis['has_main_block'] else 'No'}")
        lines.append("")

        # Imports
        if analysis["imports"]:
            lines.append("=== Imports ===")
            for imp in analysis["imports"]:
                lines.append(f"  - {imp}")
            lines.append("")

        # Functions
        if analysis["functions"]:
            lines.append("=== Functions ===")
            for func in analysis["functions"]:
                async_marker = " (async)" if func["is_async"] else ""
                params_str = ", ".join(func["parameters"]) if func["parameters"] else "no parameters"
                docstring_marker = " [has docstring]" if func["has_docstring"] else ""

                lines.append(f"  {func['name']}({params_str}){async_marker}{docstring_marker}")
                lines.append(f"    Statements: {func['num_statements']}")
            lines.append("")

        # Classes
        if analysis["classes"]:
            lines.append("=== Classes ===")
            for cls in analysis["classes"]:
                bases_str = f" (inherits from: {', '.join(cls['base_classes'])})" if cls["base_classes"] else ""
                docstring_marker = " [has docstring]" if cls["has_docstring"] else ""

                lines.append(f"  {cls['name']}{bases_str}{docstring_marker}")
                lines.append(f"    Methods: {cls['num_methods']}")
            lines.append("")

        # Code quality notes
        lines.append("=== Code Quality Notes ===")
        if analysis["has_docstrings"]:
            lines.append("  ✓ Code includes documentation (docstrings)")
        else:
            lines.append("  ✗ No docstrings found (consider adding documentation)")

        if analysis["avg_function_complexity"] > 0:
            lines.append(f"  Average function complexity: {analysis['avg_function_complexity']:.1f} statements")

        return "\n".join(lines)
