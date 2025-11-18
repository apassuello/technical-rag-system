"""
Execution planner for creating optimized query execution plans.

This module analyzes sub-tasks and creates execution plans with optimal
strategies (direct, sequential, parallel, or hybrid).

Architecture:
- Dependency analysis for task ordering
- Strategy selection based on parallelization opportunities
- Execution graph construction
- Time and cost estimation

Usage:
    >>> planner = ExecutionPlanner()
    >>> analysis = QueryAnalysis(...)
    >>> sub_tasks = [SubTask(...), SubTask(...)]
    >>> plan = planner.create_plan(sub_tasks)
    >>> print(f"Strategy: {plan.strategy}")
    >>> print(f"Estimated time: {plan.estimated_time:.2f}s")
"""

import uuid
import logging
from typing import List, Dict, Optional, Set

from ..models import (
    ExecutionPlan,
    ExecutionStrategy,
    SubTask,
    QueryAnalysis,
)

logger = logging.getLogger(__name__)


class ExecutionPlanner:
    """
    Create optimized execution plans for query processing.

    This planner analyzes sub-tasks and dependencies to create execution
    plans with optimal strategies for latency and cost.

    Attributes:
        optimize_for: Optimization target ("latency" or "cost")
        avg_task_time: Average time per task (seconds)
        avg_task_cost: Average cost per task (USD)

    Example:
        >>> planner = ExecutionPlanner(optimize_for="latency")
        >>> sub_tasks = [task1, task2, task3]
        >>> plan = planner.create_plan(sub_tasks)
        >>> assert plan.strategy in [ExecutionStrategy.SEQUENTIAL,
        ...                           ExecutionStrategy.PARALLEL,
        ...                           ExecutionStrategy.HYBRID]
    """

    def __init__(
        self,
        optimize_for: str = "latency",
        avg_task_time: float = 2.0,
        avg_task_cost: float = 0.02,
    ) -> None:
        """
        Initialize execution planner.

        Args:
            optimize_for: Optimization target ("latency" or "cost")
            avg_task_time: Average time per task in seconds
            avg_task_cost: Average cost per task in USD
        """
        if optimize_for not in ["latency", "cost"]:
            raise ValueError("optimize_for must be 'latency' or 'cost'")

        self.optimize_for = optimize_for
        self.avg_task_time = avg_task_time
        self.avg_task_cost = avg_task_cost

    def create_plan(
        self,
        sub_tasks: List[SubTask],
        query: Optional[str] = None,
        analysis: Optional[QueryAnalysis] = None,
    ) -> ExecutionPlan:
        """
        Create execution plan from sub-tasks.

        Args:
            sub_tasks: List of sub-tasks to execute
            query: Original query (optional)
            analysis: Query analysis (optional)

        Returns:
            ExecutionPlan with strategy and task ordering

        Example:
            >>> planner = ExecutionPlanner()
            >>> tasks = [SubTask(id="t1", ...), SubTask(id="t2", ...)]
            >>> plan = planner.create_plan(tasks, query="...")
            >>> assert plan.plan_id is not None
            >>> assert len(plan.tasks) == len(tasks)
        """
        logger.debug(f"Creating execution plan for {len(sub_tasks)} sub-tasks")

        # Generate plan ID
        plan_id = str(uuid.uuid4())

        # Select strategy
        strategy = self._select_strategy(sub_tasks, analysis)
        logger.info(f"Selected strategy: {strategy.value}")

        # Optimize task ordering
        optimized_tasks = self._optimize_task_ordering(sub_tasks, strategy)

        # Build execution graph
        execution_graph = self._build_execution_graph(optimized_tasks)

        # Estimate time and cost
        estimated_time = self._estimate_time(optimized_tasks, strategy)
        estimated_cost = self._estimate_cost(optimized_tasks, strategy)

        plan = ExecutionPlan(
            plan_id=plan_id,
            query=query or "",
            strategy=strategy,
            tasks=optimized_tasks,
            execution_graph=execution_graph,
            estimated_time=estimated_time,
            estimated_cost=estimated_cost,
            metadata={
                "optimization": self.optimize_for,
                "task_count": len(optimized_tasks),
                "has_dependencies": any(t.dependencies for t in optimized_tasks),
            },
        )

        logger.debug(
            f"Plan created: {len(optimized_tasks)} tasks, "
            f"estimated time={estimated_time:.2f}s, "
            f"cost=${estimated_cost:.4f}"
        )

        return plan

    def _select_strategy(
        self,
        sub_tasks: List[SubTask],
        analysis: Optional[QueryAnalysis] = None,
    ) -> ExecutionStrategy:
        """
        Select execution strategy based on task characteristics.

        Args:
            sub_tasks: List of sub-tasks
            analysis: Optional query analysis

        Returns:
            ExecutionStrategy enum value

        Strategy Selection Logic:
        - DIRECT: Single task or very simple query
        - SEQUENTIAL: Tasks with dependencies or cost-optimized
        - PARALLEL: Independent tasks that can run concurrently
        - HYBRID: Mix of sequential and parallel execution
        """
        # Single task → DIRECT
        if len(sub_tasks) <= 1:
            return ExecutionStrategy.DIRECT

        # Check if any tasks can run in parallel
        can_parallelize = any(task.can_run_parallel for task in sub_tasks)

        # Check if tasks have dependencies
        has_dependencies = any(task.dependencies for task in sub_tasks)

        # If optimizing for cost, prefer sequential
        if self.optimize_for == "cost":
            return ExecutionStrategy.SEQUENTIAL

        # No parallelization possible → SEQUENTIAL
        if not can_parallelize:
            return ExecutionStrategy.SEQUENTIAL

        # Some tasks can parallelize, some can't → HYBRID
        if has_dependencies and can_parallelize:
            # Check if there are independent task groups
            independent_groups = self._find_independent_groups(sub_tasks)
            if len(independent_groups) > 1:
                return ExecutionStrategy.HYBRID
            else:
                return ExecutionStrategy.SEQUENTIAL

        # All tasks can parallelize, no dependencies → PARALLEL
        if can_parallelize and not has_dependencies:
            return ExecutionStrategy.PARALLEL

        # Default → SEQUENTIAL
        return ExecutionStrategy.SEQUENTIAL

    def _optimize_task_ordering(
        self,
        sub_tasks: List[SubTask],
        strategy: ExecutionStrategy,
    ) -> List[SubTask]:
        """
        Optimize task ordering based on strategy.

        Args:
            sub_tasks: List of sub-tasks
            strategy: Selected execution strategy

        Returns:
            Optimized list of sub-tasks
        """
        if strategy == ExecutionStrategy.DIRECT:
            return sub_tasks

        # For sequential and parallel, sort by priority and dependencies
        return self._topological_sort(sub_tasks)

    def _topological_sort(self, sub_tasks: List[SubTask]) -> List[SubTask]:
        """
        Topologically sort tasks based on dependencies.

        Args:
            sub_tasks: List of sub-tasks

        Returns:
            Sorted list of sub-tasks

        Algorithm:
        - Kahn's algorithm for topological sorting
        - Ensures dependencies are satisfied
        """
        # Build adjacency list and in-degree count
        task_map = {task.id: task for task in sub_tasks}
        in_degree = {task.id: 0 for task in sub_tasks}
        adjacency = {task.id: [] for task in sub_tasks}

        for task in sub_tasks:
            for dep_id in task.dependencies:
                if dep_id in task_map:
                    adjacency[dep_id].append(task.id)
                    in_degree[task.id] += 1

        # Find tasks with no dependencies
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        sorted_tasks = []

        while queue:
            # Sort by priority for deterministic ordering
            queue.sort(key=lambda tid: task_map[tid].priority)

            # Process next task
            current_id = queue.pop(0)
            sorted_tasks.append(task_map[current_id])

            # Update in-degrees for dependent tasks
            for neighbor_id in adjacency[current_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)

        # Check for cycles
        if len(sorted_tasks) < len(sub_tasks):
            logger.warning("Dependency cycle detected, using original order")
            return sorted(sub_tasks, key=lambda t: t.priority)

        return sorted_tasks

    def _find_independent_groups(self, sub_tasks: List[SubTask]) -> List[List[str]]:
        """
        Find groups of tasks that can run independently.

        Args:
            sub_tasks: List of sub-tasks

        Returns:
            List of task ID groups that are independent
        """
        # Build dependency graph
        task_ids = {task.id for task in sub_tasks}
        dependencies = {
            task.id: set(task.dependencies) & task_ids for task in sub_tasks
        }

        # Find connected components
        visited = set()
        groups = []

        def dfs(task_id: str, group: Set[str]) -> None:
            """Depth-first search to find connected component."""
            if task_id in visited:
                return
            visited.add(task_id)
            group.add(task_id)

            # Visit dependencies
            for dep_id in dependencies.get(task_id, []):
                dfs(dep_id, group)

            # Visit dependents
            for tid, deps in dependencies.items():
                if task_id in deps:
                    dfs(tid, group)

        for task in sub_tasks:
            if task.id not in visited:
                group: Set[str] = set()
                dfs(task.id, group)
                groups.append(list(group))

        return groups

    def _build_execution_graph(
        self,
        sub_tasks: List[SubTask],
    ) -> Dict[str, List[str]]:
        """
        Build execution graph from sub-tasks.

        Args:
            sub_tasks: List of sub-tasks

        Returns:
            Adjacency list representation {task_id: [dependent_task_ids]}
        """
        graph: Dict[str, List[str]] = {task.id: [] for task in sub_tasks}

        for task in sub_tasks:
            for dep_id in task.dependencies:
                if dep_id in graph:
                    graph[dep_id].append(task.id)

        return graph

    def _estimate_time(
        self,
        sub_tasks: List[SubTask],
        strategy: ExecutionStrategy,
    ) -> float:
        """
        Estimate execution time.

        Args:
            sub_tasks: List of sub-tasks
            strategy: Execution strategy

        Returns:
            Estimated time in seconds
        """
        if not sub_tasks:
            return 0.0

        if strategy == ExecutionStrategy.DIRECT:
            return self.avg_task_time

        elif strategy == ExecutionStrategy.SEQUENTIAL:
            return len(sub_tasks) * self.avg_task_time

        elif strategy == ExecutionStrategy.PARALLEL:
            # Assume perfect parallelization
            return self.avg_task_time * 1.2  # Small overhead for coordination

        else:  # HYBRID
            # Estimate based on longest path in dependency graph
            max_depth = self._calculate_max_depth(sub_tasks)
            return max_depth * self.avg_task_time * 1.1  # Small overhead

    def _calculate_max_depth(self, sub_tasks: List[SubTask]) -> int:
        """
        Calculate maximum depth in dependency graph.

        Args:
            sub_tasks: List of sub-tasks

        Returns:
            Maximum depth (longest path)
        """
        task_map = {task.id: task for task in sub_tasks}
        depth_cache: Dict[str, int] = {}

        def get_depth(task_id: str) -> int:
            """Get depth of task in dependency graph."""
            if task_id in depth_cache:
                return depth_cache[task_id]

            task = task_map.get(task_id)
            if not task or not task.dependencies:
                depth_cache[task_id] = 1
                return 1

            # Depth is 1 + max depth of dependencies
            max_dep_depth = max(
                (get_depth(dep_id) for dep_id in task.dependencies if dep_id in task_map),
                default=0,
            )
            depth_cache[task_id] = max_dep_depth + 1
            return depth_cache[task_id]

        # Calculate depth for all tasks
        for task in sub_tasks:
            get_depth(task.id)

        return max(depth_cache.values()) if depth_cache else 1

    def _estimate_cost(
        self,
        sub_tasks: List[SubTask],
        strategy: ExecutionStrategy,
    ) -> float:
        """
        Estimate execution cost.

        Args:
            sub_tasks: List of sub-tasks
            strategy: Execution strategy

        Returns:
            Estimated cost in USD
        """
        if not sub_tasks:
            return 0.0

        # Cost is primarily number of tasks * avg cost
        base_cost = len(sub_tasks) * self.avg_task_cost

        # Parallel execution may have coordination overhead
        if strategy in (ExecutionStrategy.PARALLEL, ExecutionStrategy.HYBRID):
            base_cost *= 1.05  # 5% overhead

        return base_cost
