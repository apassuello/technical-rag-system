"""
Query decomposer for breaking complex queries into sub-tasks.

This module uses LLM to intelligently decompose complex queries into
sequential or parallel sub-tasks with dependency tracking.

Architecture:
- LLM-based decomposition for accuracy
- Structured JSON output parsing
- Sub-task validation
- Dependency graph construction

Usage:
    >>> from src.components.generators.llm_adapters import OpenAIAdapter
    >>> from src.components.generators.base import GenerationParams
    >>>
    >>> llm = OpenAIAdapter(model_name="gpt-4")
    >>> decomposer = QueryDecomposer(llm_adapter=llm)
    >>>
    >>> query = "Research ML papers and calculate average citations"
    >>> analysis = QueryAnalysis(...)
    >>> sub_tasks = decomposer.decompose(query, analysis)
    >>> print(f"Decomposed into {len(sub_tasks)} sub-tasks")
"""

import json
import logging
import uuid
from typing import List, Optional, Dict, Any

from src.components.generators.base import GenerationParams
from src.components.generators.llm_adapters.base_adapter import BaseLLMAdapter
from ..models import SubTask, QueryAnalysis, QueryType

logger = logging.getLogger(__name__)


class QueryDecomposer:
    """
    Decompose complex queries into sub-tasks using LLM.

    This decomposer uses LLM to break complex queries into manageable sub-tasks
    with dependency tracking. Handles simple queries by returning single task.

    Attributes:
        llm_adapter: Optional LLM adapter for decomposition
        generation_params: Parameters for LLM generation

    Example:
        >>> decomposer = QueryDecomposer(llm_adapter=llm)
        >>> query = "Find papers on ML and calculate average citations"
        >>> analysis = QueryAnalysis(complexity=0.8, ...)
        >>> tasks = decomposer.decompose(query, analysis)
        >>> assert len(tasks) >= 2
        >>> assert any(task.can_run_parallel for task in tasks)
    """

    def __init__(
        self,
        llm_adapter: Optional[BaseLLMAdapter] = None,
        max_sub_tasks: int = 5,
    ) -> None:
        """
        Initialize query decomposer.

        Args:
            llm_adapter: Optional LLM adapter for decomposition
            max_sub_tasks: Maximum number of sub-tasks to generate
        """
        self.llm_adapter = llm_adapter
        self.max_sub_tasks = max_sub_tasks

        # Generation parameters for decomposition
        self.generation_params = GenerationParams()
        self.generation_params.temperature = 0.3  # Lower for structured output
        self.generation_params.max_tokens = 1024

    def decompose(
        self,
        query: str,
        analysis: QueryAnalysis,
    ) -> List[SubTask]:
        """
        Decompose query into sub-tasks.

        Args:
            query: User query to decompose
            analysis: Query analysis result

        Returns:
            List of SubTask objects (may be single task for simple queries)

        Example:
            >>> decomposer = QueryDecomposer(llm_adapter=llm)
            >>> analysis = QueryAnalysis(complexity=0.8, ...)
            >>> tasks = decomposer.decompose("Complex query", analysis)
            >>> assert all(isinstance(t, SubTask) for t in tasks)
        """
        logger.debug(f"Decomposing query with complexity {analysis.complexity:.2f}")

        # Simple queries don't need decomposition
        if analysis.complexity < 0.7:
            logger.debug("Query is simple, returning single task")
            return [self._create_single_task(query)]

        # Use LLM if available
        if self.llm_adapter:
            try:
                return self._decompose_with_llm(query, analysis)
            except Exception as e:
                logger.warning(f"LLM decomposition failed: {e}, using heuristic")
                return self._decompose_heuristic(query, analysis)

        # Fallback: heuristic decomposition
        return self._decompose_heuristic(query, analysis)

    def _create_single_task(self, query: str) -> SubTask:
        """
        Create single task for simple queries.

        Args:
            query: User query

        Returns:
            Single SubTask representing the entire query
        """
        return SubTask(
            id="task_0",
            description="Process query directly",
            query=query,
            required_tools=[],
            dependencies=[],
            can_run_parallel=False,
            priority=0,
            metadata={"decomposition": "none"},
        )

    def _decompose_with_llm(
        self,
        query: str,
        analysis: QueryAnalysis,
    ) -> List[SubTask]:
        """
        Use LLM to decompose query.

        Args:
            query: User query
            analysis: Query analysis

        Returns:
            List of SubTask objects

        Raises:
            ValueError: If LLM response is invalid
        """
        logger.debug("Using LLM for decomposition")

        # Create decomposition prompt
        prompt = self._create_decomposition_prompt(query, analysis)

        # Call LLM
        response = self.llm_adapter.generate(prompt, self.generation_params)

        # Parse response
        sub_tasks = self._parse_llm_response(response)

        # Validate sub-tasks
        validated_tasks = self._validate_sub_tasks(sub_tasks)

        logger.info(f"Decomposed into {len(validated_tasks)} sub-tasks")
        return validated_tasks

    def _create_decomposition_prompt(
        self,
        query: str,
        analysis: QueryAnalysis,
    ) -> str:
        """
        Create prompt for LLM decomposition.

        Args:
            query: User query
            analysis: Query analysis

        Returns:
            Formatted prompt string
        """
        prompt = f"""Break down this complex query into sequential sub-tasks.

Query: {query}

Query Analysis:
- Type: {analysis.query_type.value}
- Complexity: {analysis.complexity:.2f}
- Intent: {analysis.intent}
- Required Tools: {', '.join(analysis.requires_tools) if analysis.requires_tools else 'None'}

Instructions:
1. Identify distinct sub-tasks needed to answer the query
2. For each sub-task, specify:
   - description: Clear description of what needs to be done
   - query: Specific question or instruction for this sub-task
   - required_tools: List of tools needed (e.g., ["calculator", "document_search"])
   - dependencies: IDs of prerequisite tasks (e.g., ["task_0"])
   - can_run_parallel: Whether this task can run in parallel with others
3. Keep it simple: Maximum {self.max_sub_tasks} sub-tasks
4. Output ONLY valid JSON array, no additional text

Output Format (JSON array):
[
  {{
    "description": "First sub-task description",
    "query": "Specific question for this sub-task",
    "required_tools": ["tool1", "tool2"],
    "dependencies": [],
    "can_run_parallel": false
  }},
  {{
    "description": "Second sub-task description",
    "query": "Another specific question",
    "required_tools": ["tool3"],
    "dependencies": ["task_0"],
    "can_run_parallel": false
  }}
]

Now decompose the query:"""

        return prompt

    def _parse_llm_response(self, response: str) -> List[SubTask]:
        """
        Parse LLM response into SubTask objects.

        Args:
            response: JSON response from LLM

        Returns:
            List of SubTask objects

        Raises:
            ValueError: If response is invalid JSON
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()

            # Parse JSON
            tasks_data = json.loads(json_str)

            if not isinstance(tasks_data, list):
                raise ValueError("Expected JSON array")

            # Create SubTask objects
            sub_tasks = []
            for i, task_data in enumerate(tasks_data):
                sub_task = SubTask(
                    id=f"task_{i}",
                    description=task_data.get("description", f"Sub-task {i}"),
                    query=task_data.get("query", ""),
                    required_tools=task_data.get("required_tools", []),
                    dependencies=task_data.get("dependencies", []),
                    can_run_parallel=task_data.get("can_run_parallel", False),
                    priority=i,
                    metadata={"source": "llm_decomposition"},
                )
                sub_tasks.append(sub_task)

            return sub_tasks

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response: {response[:500]}")
            raise ValueError(f"Invalid JSON response: {e}")
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise ValueError(f"Invalid response format: {e}")

    def _validate_sub_tasks(self, sub_tasks: List[SubTask]) -> List[SubTask]:
        """
        Validate and clean sub-tasks.

        Args:
            sub_tasks: List of sub-tasks to validate

        Returns:
            Validated list of sub-tasks

        Validation:
        - Limit to max_sub_tasks
        - Ensure valid dependencies
        - Ensure queries are non-empty
        """
        if not sub_tasks:
            raise ValueError("No sub-tasks generated")

        # Limit number of tasks
        if len(sub_tasks) > self.max_sub_tasks:
            logger.warning(
                f"Too many sub-tasks ({len(sub_tasks)}), "
                f"limiting to {self.max_sub_tasks}"
            )
            sub_tasks = sub_tasks[: self.max_sub_tasks]

        # Validate each task
        validated = []
        task_ids = {task.id for task in sub_tasks}

        for task in sub_tasks:
            # Ensure query is non-empty
            if not task.query.strip():
                logger.warning(f"Task {task.id} has empty query, skipping")
                continue

            # Validate dependencies exist
            valid_deps = [dep for dep in task.dependencies if dep in task_ids]
            if len(valid_deps) < len(task.dependencies):
                logger.warning(
                    f"Task {task.id} has invalid dependencies, "
                    f"keeping only valid ones"
                )

            # Create validated task
            validated_task = SubTask(
                id=task.id,
                description=task.description,
                query=task.query,
                required_tools=task.required_tools,
                dependencies=valid_deps,
                can_run_parallel=task.can_run_parallel,
                priority=task.priority,
                metadata=task.metadata,
            )
            validated.append(validated_task)

        if not validated:
            raise ValueError("All sub-tasks failed validation")

        return validated

    def _decompose_heuristic(
        self,
        query: str,
        analysis: QueryAnalysis,
    ) -> List[SubTask]:
        """
        Heuristic-based decomposition fallback.

        Simple rule-based decomposition for when LLM is unavailable.

        Args:
            query: User query
            analysis: Query analysis

        Returns:
            List of SubTask objects
        """
        logger.debug("Using heuristic decomposition")

        # Split on common separators
        separators = ["and then", "after that", "then", ".", "?"]
        parts = [query]

        for sep in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(sep))
            parts = new_parts

        # Clean and filter parts
        parts = [p.strip() for p in parts if p.strip()]

        # Create sub-tasks
        sub_tasks = []
        for i, part in enumerate(parts[: self.max_sub_tasks]):
            if len(part) < 5:  # Skip very short parts
                continue

            sub_task = SubTask(
                id=f"task_{i}",
                description=f"Process: {part[:50]}...",
                query=part,
                required_tools=[],
                dependencies=[f"task_{i-1}"] if i > 0 else [],
                can_run_parallel=False,
                priority=i,
                metadata={"decomposition": "heuristic"},
            )
            sub_tasks.append(sub_task)

        # If only one part, return single task
        if not sub_tasks or len(sub_tasks) == 1:
            return [self._create_single_task(query)]

        return sub_tasks
