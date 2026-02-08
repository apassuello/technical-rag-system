"""
LangChain adapter for Phase 1 tools.

Converts Phase 1 BaseTool implementations to LangChain tool format,
enabling integration with LangChain's agent framework while preserving
all Phase 1 tool functionality.

Architecture:
- Wraps Phase 1 tools in LangChain Tool interface
- Preserves parameter schemas and validation
- Maintains error handling guarantees
- Zero modification to Phase 1 tools required

Usage:
    >>> from src.components.query_processors.tools.implementations import CalculatorTool
    >>> from src.components.query_processors.agents.langchain_adapter import PhaseOneToolAdapter
    >>>
    >>> # Create Phase 1 tool
    >>> calculator = CalculatorTool()
    >>>
    >>> # Convert to LangChain tool
    >>> lc_tool = PhaseOneToolAdapter.from_phase1_tool(calculator)
    >>>
    >>> # Use with LangChain agent
    >>> tools = [lc_tool]
    >>> agent = create_react_agent(llm, tools, prompt)
"""

import logging
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field, create_model

try:
    from langchain_core.callbacks.manager import CallbackManagerForToolRun
    from langchain_core.tools import BaseTool as LangChainBaseTool
except ImportError:
    try:
        from langchain.callbacks.manager import CallbackManagerForToolRun
        from langchain.tools import BaseTool as LangChainBaseTool
    except ImportError:
        CallbackManagerForToolRun = None  # type: ignore[assignment,misc]
        LangChainBaseTool = None  # type: ignore[assignment,misc]

# Relative imports to avoid torch dependency
from ...query_processors.tools.base_tool import BaseTool as Phase1BaseTool
from ...query_processors.tools.models import ToolParameterType

logger = logging.getLogger(__name__)


class PhaseOneToolAdapter(LangChainBaseTool):
    """
    LangChain adapter for Phase 1 tools.

    Wraps a Phase 1 BaseTool to make it compatible with LangChain's
    agent framework. Handles schema conversion, parameter validation,
    and result formatting.

    Key Features:
    - Automatic schema conversion (Phase 1 → LangChain)
    - Parameter validation using Pydantic
    - Error handling preserved from Phase 1
    - Zero modification to original tools

    Example:
        >>> # Wrap Phase 1 tool
        >>> calculator = CalculatorTool()
        >>> lc_tool = PhaseOneToolAdapter.from_phase1_tool(calculator)
        >>>
        >>> # Execute via LangChain
        >>> result = lc_tool._run(expression="2 + 2")
        >>> print(result)  # "4"
    """

    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    phase1_tool: Any = Field(description="Wrapped Phase 1 tool")
    args_schema: Optional[Type[BaseModel]] = Field(default=None, description="Pydantic schema for arguments")

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True

    @classmethod
    def from_phase1_tool(cls, tool: Phase1BaseTool) -> "PhaseOneToolAdapter":
        """
        Create LangChain tool from Phase 1 tool.

        Args:
            tool: Phase 1 BaseTool instance

        Returns:
            PhaseOneToolAdapter wrapping the Phase 1 tool

        Example:
            >>> calculator = CalculatorTool()
            >>> lc_tool = PhaseOneToolAdapter.from_phase1_tool(calculator)
            >>> lc_tool.name  # "calculator"
        """
        # Create Pydantic schema from Phase 1 parameters
        args_schema = cls._create_pydantic_schema(tool)

        return cls(
            name=tool.name,
            description=tool.description,
            phase1_tool=tool,
            args_schema=args_schema
        )

    @staticmethod
    def _create_pydantic_schema(tool: Phase1BaseTool) -> Type[BaseModel]:
        """
        Create Pydantic schema from Phase 1 tool parameters.

        Args:
            tool: Phase 1 tool

        Returns:
            Pydantic BaseModel class for tool arguments

        Example:
            >>> tool = CalculatorTool()
            >>> schema = PhaseOneToolAdapter._create_pydantic_schema(tool)
            >>> schema.__fields__  # {'expression': FieldInfo(...)}
        """
        params = tool.get_parameters()

        # Build field definitions for Pydantic model
        field_definitions: Dict[str, Any] = {}

        for param in params:
            # Map Phase 1 types to Python types
            python_type = _map_parameter_type(param.type)

            # Create field with description
            if param.required:
                field_definitions[param.name] = (
                    python_type,
                    Field(description=param.description)
                )
            else:
                field_definitions[param.name] = (
                    Optional[python_type],
                    Field(default=None, description=param.description)
                )

        # Create dynamic Pydantic model
        schema_name = f"{tool.name.title()}Args"
        return create_model(schema_name, **field_definitions)

    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        """
        Execute Phase 1 tool.

        This is the main execution method called by LangChain agents.
        It delegates to the Phase 1 tool's execute() method and handles
        result conversion.

        Args:
            run_manager: LangChain callback manager (optional)
            **kwargs: Tool arguments

        Returns:
            Tool result as string (success content or error message)

        Example:
            >>> adapter = PhaseOneToolAdapter.from_phase1_tool(CalculatorTool())
            >>> result = adapter._run(expression="25 * 47")
            >>> print(result)  # "1175"
        """
        try:
            # Log execution
            logger.debug(f"Executing Phase 1 tool '{self.name}' with args: {kwargs}")

            # Execute Phase 1 tool (always returns ToolResult, never raises)
            result = self.phase1_tool.execute_safe(**kwargs)

            # Convert to LangChain format (string)
            if result.success:
                output = str(result.content)
                logger.debug(f"Tool '{self.name}' succeeded: {output[:100]}")
                return output
            else:
                # Return error as string (LangChain expects string, not exception)
                error_msg = f"Tool error: {result.error}"
                logger.warning(f"Tool '{self.name}' failed: {result.error}")
                return error_msg

        except Exception as e:
            # This should never happen (Phase 1 tools catch all exceptions)
            # But we handle it for absolute safety
            error_msg = f"Unexpected error in tool adapter: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    async def _arun(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        """
        Async execution (not supported, falls back to sync).

        Phase 1 tools are synchronous, so we execute synchronously
        even when called async.

        Args:
            run_manager: LangChain callback manager (optional)
            **kwargs: Tool arguments

        Returns:
            Tool result as string

        Example:
            >>> adapter = PhaseOneToolAdapter.from_phase1_tool(CalculatorTool())
            >>> result = await adapter._arun(expression="2 + 2")
            >>> print(result)  # "4"
        """
        # Phase 1 tools are sync, so just call sync version
        return self._run(run_manager=run_manager, **kwargs)


def _map_parameter_type(param_type: ToolParameterType) -> Type:
    """
    Map Phase 1 parameter type to Python type.

    Args:
        param_type: Phase 1 ToolParameterType enum value

    Returns:
        Corresponding Python type

    Example:
        >>> _map_parameter_type(ToolParameterType.STRING)
        <class 'str'>
        >>> _map_parameter_type(ToolParameterType.INTEGER)
        <class 'int'>
    """
    type_mapping = {
        ToolParameterType.STRING: str,
        ToolParameterType.INTEGER: int,
        ToolParameterType.FLOAT: float,
        ToolParameterType.BOOLEAN: bool,
        ToolParameterType.ARRAY: list,
        ToolParameterType.OBJECT: dict,
    }

    return type_mapping.get(param_type, str)


def convert_tools_to_langchain(
    tools: List[Phase1BaseTool]
) -> List[PhaseOneToolAdapter]:
    """
    Convert list of Phase 1 tools to LangChain tools.

    Convenience function for bulk conversion.

    Args:
        tools: List of Phase 1 BaseTool instances

    Returns:
        List of PhaseOneToolAdapter instances

    Example:
        >>> from src.components.query_processors.tools.implementations import (
        ...     CalculatorTool,
        ...     DocumentSearchTool,
        ...     CodeAnalyzerTool
        ... )
        >>>
        >>> phase1_tools = [
        ...     CalculatorTool(),
        ...     DocumentSearchTool(index_path),
        ...     CodeAnalyzerTool()
        ... ]
        >>>
        >>> lc_tools = convert_tools_to_langchain(phase1_tools)
        >>> len(lc_tools)  # 3
    """
    logger.info(f"Converting {len(tools)} Phase 1 tools to LangChain format")

    langchain_tools = []
    for tool in tools:
        try:
            lc_tool = PhaseOneToolAdapter.from_phase1_tool(tool)
            langchain_tools.append(lc_tool)
            logger.debug(f"Converted tool: {tool.name}")
        except Exception as e:
            logger.error(
                f"Failed to convert tool '{tool.name}': {e}",
                exc_info=True
            )
            # Continue with other tools
            continue

    logger.info(
        f"Successfully converted {len(langchain_tools)}/{len(tools)} tools"
    )

    return langchain_tools
