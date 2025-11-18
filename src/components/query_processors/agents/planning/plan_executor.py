"""
Plan executor for executing query execution plans.

This module executes execution plans using agents, supporting sequential,
parallel, and hybrid execution strategies.

Architecture:
- Sequential execution for dependent tasks
- Parallel execution for independent tasks
- Hybrid execution combining both
- Result aggregation and cost tracking

Usage:
    >>> from src.components.query_processors.agents.base_agent import BaseAgent
    >>>
    >>> executor = PlanExecutor()
    >>> plan = ExecutionPlan(...)
    >>> agent = ReActAgent(...)
    >>> result = executor.execute(plan, agent)
    >>> print(f"Success: {result.success}")
    >>> print(f"Answer: {result.final_answer}")
"""

import time
import logging
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..base_agent import BaseAgent
from ..models import (
    ExecutionPlan,
    ExecutionResult,
    ExecutionStrategy,
    SubTask,
    ReasoningStep,
    AgentResult,
)

logger = logging.getLogger(__name__)


class PlanExecutor:
    """
    Execute execution plans using agents.

    This executor supports multiple execution strategies:
    - DIRECT: Single query execution
    - SEQUENTIAL: Execute tasks one by one
    - PARALLEL: Execute independent tasks concurrently
    - HYBRID: Mix of sequential and parallel execution

    Attributes:
        max_parallel_tasks: Maximum number of parallel tasks
        timeout_per_task: Timeout for each task in seconds

    Example:
        >>> executor = PlanExecutor(max_parallel_tasks=3)
        >>> plan = ExecutionPlan(strategy=ExecutionStrategy.SEQUENTIAL, ...)
        >>> agent = ReActAgent(...)
        >>> result = executor.execute(plan, agent)
        >>> assert result.success
        >>> assert len(result.task_results) == len(plan.tasks)
    """

    def __init__(
        self,
        max_parallel_tasks: int = 3,
        timeout_per_task: float = 60.0,
    ) -> None:
        """
        Initialize plan executor.

        Args:
            max_parallel_tasks: Maximum concurrent tasks
            timeout_per_task: Timeout per task in seconds
        """
        self.max_parallel_tasks = max_parallel_tasks
        self.timeout_per_task = timeout_per_task

    def execute(
        self,
        plan: ExecutionPlan,
        agent: BaseAgent,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute plan with agent.

        Args:
            plan: Execution plan to execute
            agent: Agent to use for task execution
            context: Optional context for execution

        Returns:
            ExecutionResult with final answer and metadata

        Example:
            >>> executor = PlanExecutor()
            >>> result = executor.execute(plan, agent)
            >>> assert result.success
            >>> print(f"Time: {result.execution_time:.2f}s")
            >>> print(f"Cost: ${result.total_cost:.4f}")
        """
        logger.info(
            f"Executing plan {plan.plan_id} with strategy {plan.strategy.value}"
        )
        start_time = time.time()

        try:
            # Execute based on strategy
            if plan.strategy == ExecutionStrategy.DIRECT:
                result = self._execute_direct(plan, agent, context)
            elif plan.strategy == ExecutionStrategy.SEQUENTIAL:
                result = self._execute_sequential(plan, agent, context)
            elif plan.strategy == ExecutionStrategy.PARALLEL:
                result = self._execute_parallel(plan, agent, context)
            else:  # HYBRID
                result = self._execute_hybrid(plan, agent, context)

            # Update timing
            result.execution_time = time.time() - start_time

            logger.info(
                f"Plan execution completed: success={result.success}, "
                f"time={result.execution_time:.2f}s, "
                f"cost=${result.total_cost:.4f}"
            )

            return result

        except Exception as e:
            logger.error(f"Plan execution failed: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                final_answer="",
                task_results={},
                reasoning_trace=[],
                execution_time=time.time() - start_time,
                total_cost=0.0,
                metadata={"strategy": plan.strategy.value, "error_type": type(e).__name__},
                error=str(e),
            )

    def _execute_direct(
        self,
        plan: ExecutionPlan,
        agent: BaseAgent,
        context: Optional[Dict[str, Any]],
    ) -> ExecutionResult:
        """
        Execute plan directly (single query).

        Args:
            plan: Execution plan
            agent: Agent to use
            context: Optional context

        Returns:
            ExecutionResult
        """
        logger.debug("Executing plan directly")

        # Execute query with agent
        agent_result = agent.process(plan.query, context)

        return ExecutionResult(
            success=agent_result.success,
            final_answer=agent_result.answer,
            task_results={"main": agent_result.answer},
            reasoning_trace=agent_result.reasoning_steps,
            execution_time=agent_result.execution_time,
            total_cost=agent_result.total_cost,
            metadata={"strategy": "direct", "tool_calls": len(agent_result.tool_calls)},
            error=agent_result.error,
        )

    def _execute_sequential(
        self,
        plan: ExecutionPlan,
        agent: BaseAgent,
        context: Optional[Dict[str, Any]],
    ) -> ExecutionResult:
        """
        Execute tasks sequentially.

        Args:
            plan: Execution plan
            agent: Agent to use
            context: Optional context

        Returns:
            ExecutionResult
        """
        logger.debug(f"Executing {len(plan.tasks)} tasks sequentially")

        task_results: Dict[str, Any] = {}
        all_reasoning: List[ReasoningStep] = []
        total_cost = 0.0

        for i, task in enumerate(plan.tasks):
            logger.debug(f"Executing task {i+1}/{len(plan.tasks)}: {task.id}")

            # Build context with previous results
            task_context = self._build_task_context(context, task_results, task)

            # Execute task
            agent_result = agent.process(task.query, task_context)

            # Store result
            task_results[task.id] = {
                "answer": agent_result.answer,
                "success": agent_result.success,
                "error": agent_result.error,
            }

            # Accumulate metrics
            all_reasoning.extend(agent_result.reasoning_steps)
            total_cost += agent_result.total_cost

            # Check if task failed
            if not agent_result.success:
                logger.warning(f"Task {task.id} failed: {agent_result.error}")
                # Continue execution but mark failure

        # Aggregate results
        final_answer = self._aggregate_results(plan, task_results)
        overall_success = all(
            result.get("success", False) for result in task_results.values()
        )

        return ExecutionResult(
            success=overall_success,
            final_answer=final_answer,
            task_results=task_results,
            reasoning_trace=all_reasoning,
            execution_time=0.0,  # Set by caller
            total_cost=total_cost,
            metadata={
                "strategy": "sequential",
                "completed_tasks": len(task_results),
                "total_tasks": len(plan.tasks),
            },
            error=None if overall_success else "One or more tasks failed",
        )

    def _execute_parallel(
        self,
        plan: ExecutionPlan,
        agent: BaseAgent,
        context: Optional[Dict[str, Any]],
    ) -> ExecutionResult:
        """
        Execute tasks in parallel.

        Args:
            plan: Execution plan
            agent: Agent to use
            context: Optional context

        Returns:
            ExecutionResult
        """
        logger.debug(f"Executing {len(plan.tasks)} tasks in parallel")

        task_results: Dict[str, Any] = {}
        all_reasoning: List[ReasoningStep] = []
        total_cost = 0.0

        # Execute tasks in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_parallel_tasks) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(
                    self._execute_single_task, agent, task, context, {}
                ): task
                for task in plan.tasks
            }

            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    agent_result = future.result(timeout=self.timeout_per_task)

                    # Store result
                    task_results[task.id] = {
                        "answer": agent_result.answer,
                        "success": agent_result.success,
                        "error": agent_result.error,
                    }

                    # Accumulate metrics
                    all_reasoning.extend(agent_result.reasoning_steps)
                    total_cost += agent_result.total_cost

                except Exception as e:
                    logger.error(f"Task {task.id} failed: {e}")
                    task_results[task.id] = {
                        "answer": "",
                        "success": False,
                        "error": str(e),
                    }

        # Aggregate results
        final_answer = self._aggregate_results(plan, task_results)
        overall_success = all(
            result.get("success", False) for result in task_results.values()
        )

        return ExecutionResult(
            success=overall_success,
            final_answer=final_answer,
            task_results=task_results,
            reasoning_trace=all_reasoning,
            execution_time=0.0,  # Set by caller
            total_cost=total_cost,
            metadata={
                "strategy": "parallel",
                "completed_tasks": len(task_results),
                "total_tasks": len(plan.tasks),
            },
            error=None if overall_success else "One or more tasks failed",
        )

    def _execute_hybrid(
        self,
        plan: ExecutionPlan,
        agent: BaseAgent,
        context: Optional[Dict[str, Any]],
    ) -> ExecutionResult:
        """
        Execute tasks with hybrid strategy.

        Hybrid strategy:
        1. Identify independent task groups
        2. Execute each group in parallel
        3. Execute groups sequentially (respecting dependencies)

        Args:
            plan: Execution plan
            agent: Agent to use
            context: Optional context

        Returns:
            ExecutionResult
        """
        logger.debug("Executing tasks with hybrid strategy")

        # Group tasks by dependency levels
        task_levels = self._group_tasks_by_level(plan)

        task_results: Dict[str, Any] = {}
        all_reasoning: List[ReasoningStep] = []
        total_cost = 0.0

        # Execute each level sequentially, but tasks within level in parallel
        for level_num, level_tasks in enumerate(task_levels):
            logger.debug(
                f"Executing level {level_num+1}/{len(task_levels)} "
                f"with {len(level_tasks)} tasks"
            )

            # Execute tasks in this level in parallel
            with ThreadPoolExecutor(max_workers=self.max_parallel_tasks) as executor:
                future_to_task = {
                    executor.submit(
                        self._execute_single_task, agent, task, context, task_results
                    ): task
                    for task in level_tasks
                }

                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        agent_result = future.result(timeout=self.timeout_per_task)

                        # Store result
                        task_results[task.id] = {
                            "answer": agent_result.answer,
                            "success": agent_result.success,
                            "error": agent_result.error,
                        }

                        # Accumulate metrics
                        all_reasoning.extend(agent_result.reasoning_steps)
                        total_cost += agent_result.total_cost

                    except Exception as e:
                        logger.error(f"Task {task.id} failed: {e}")
                        task_results[task.id] = {
                            "answer": "",
                            "success": False,
                            "error": str(e),
                        }

        # Aggregate results
        final_answer = self._aggregate_results(plan, task_results)
        overall_success = all(
            result.get("success", False) for result in task_results.values()
        )

        return ExecutionResult(
            success=overall_success,
            final_answer=final_answer,
            task_results=task_results,
            reasoning_trace=all_reasoning,
            execution_time=0.0,  # Set by caller
            total_cost=total_cost,
            metadata={
                "strategy": "hybrid",
                "levels": len(task_levels),
                "completed_tasks": len(task_results),
                "total_tasks": len(plan.tasks),
            },
            error=None if overall_success else "One or more tasks failed",
        )

    def _execute_single_task(
        self,
        agent: BaseAgent,
        task: SubTask,
        base_context: Optional[Dict[str, Any]],
        previous_results: Dict[str, Any],
    ) -> AgentResult:
        """
        Execute single task with agent.

        Args:
            agent: Agent to use
            task: Task to execute
            base_context: Base context
            previous_results: Results from previous tasks

        Returns:
            AgentResult
        """
        # Build context with previous results
        task_context = self._build_task_context(base_context, previous_results, task)

        # Execute task
        return agent.process(task.query, task_context)

    def _build_task_context(
        self,
        base_context: Optional[Dict[str, Any]],
        task_results: Dict[str, Any],
        task: SubTask,
    ) -> Dict[str, Any]:
        """
        Build context for task execution.

        Args:
            base_context: Base context
            task_results: Results from previous tasks
            task: Current task

        Returns:
            Context dictionary
        """
        context = base_context.copy() if base_context else {}

        # Add results from dependency tasks
        if task.dependencies:
            dependency_results = {
                dep_id: task_results.get(dep_id, {})
                for dep_id in task.dependencies
                if dep_id in task_results
            }
            context["dependency_results"] = dependency_results

        # Add task metadata
        context["task_id"] = task.id
        context["task_description"] = task.description
        context["required_tools"] = task.required_tools

        return context

    def _group_tasks_by_level(self, plan: ExecutionPlan) -> List[List[SubTask]]:
        """
        Group tasks by dependency level.

        Tasks at the same level can run in parallel.
        Levels must be executed sequentially.

        Args:
            plan: Execution plan

        Returns:
            List of task groups (one per level)
        """
        task_map = {task.id: task for task in plan.tasks}
        task_levels: Dict[str, int] = {}

        def get_level(task_id: str) -> int:
            """Get dependency level for task."""
            if task_id in task_levels:
                return task_levels[task_id]

            task = task_map.get(task_id)
            if not task or not task.dependencies:
                task_levels[task_id] = 0
                return 0

            # Level is 1 + max level of dependencies
            max_dep_level = max(
                (
                    get_level(dep_id)
                    for dep_id in task.dependencies
                    if dep_id in task_map
                ),
                default=-1,
            )
            task_levels[task_id] = max_dep_level + 1
            return task_levels[task_id]

        # Calculate levels for all tasks
        for task in plan.tasks:
            get_level(task.id)

        # Group tasks by level
        max_level = max(task_levels.values()) if task_levels else 0
        levels: List[List[SubTask]] = [[] for _ in range(max_level + 1)]

        for task in plan.tasks:
            level = task_levels.get(task.id, 0)
            levels[level].append(task)

        return levels

    def _aggregate_results(
        self,
        plan: ExecutionPlan,
        task_results: Dict[str, Any],
    ) -> str:
        """
        Aggregate task results into final answer.

        Args:
            plan: Execution plan
            task_results: Results from all tasks

        Returns:
            Aggregated final answer
        """
        if not task_results:
            return "No results generated."

        # Simple aggregation: concatenate answers
        answers = []
        for task in plan.tasks:
            result = task_results.get(task.id, {})
            answer = result.get("answer", "")
            if answer:
                answers.append(f"**{task.description}**\n{answer}")

        if not answers:
            return "Tasks completed but no answers generated."

        return "\n\n".join(answers)
