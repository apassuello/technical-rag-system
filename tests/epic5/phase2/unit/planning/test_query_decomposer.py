"""
Unit tests for QueryDecomposer.

Tests query decomposition, LLM integration, heuristic fallback,
and sub-task validation.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.components.query_processors.agents.planning.query_decomposer import QueryDecomposer
from src.components.query_processors.agents.models import QueryAnalysis, QueryType, SubTask
from src.components.generators.base import GenerationParams


class TestQueryDecomposer:
    """Test suite for QueryDecomposer."""

    @pytest.fixture
    def decomposer(self) -> QueryDecomposer:
        """Create QueryDecomposer without LLM."""
        return QueryDecomposer(llm_adapter=None, max_sub_tasks=5)

    @pytest.fixture
    def mock_llm(self) -> Mock:
        """Create mock LLM adapter."""
        llm = Mock()
        llm.generate = Mock(return_value='[{"description": "Task 1", "query": "Do task 1", "required_tools": [], "dependencies": [], "can_run_parallel": false}]')
        return llm

    @pytest.fixture
    def decomposer_with_llm(self, mock_llm: Mock) -> QueryDecomposer:
        """Create QueryDecomposer with mock LLM."""
        return QueryDecomposer(llm_adapter=mock_llm, max_sub_tasks=5)

    # Simple Query Tests

    def test_simple_query_single_task(self, decomposer: QueryDecomposer) -> None:
        """Test simple query returns single task."""
        query = "What is machine learning?"
        analysis = QueryAnalysis(
            query_type=QueryType.SIMPLE,
            complexity=0.3,
            intent="information_retrieval",
            entities=[],
            requires_tools=[],
            estimated_steps=1,
        )

        tasks = decomposer.decompose(query, analysis)

        assert len(tasks) == 1
        assert tasks[0].id == "task_0"
        assert tasks[0].query == query
        assert tasks[0].metadata["decomposition"] == "none"

    def test_low_complexity_single_task(self, decomposer: QueryDecomposer) -> None:
        """Test low complexity query returns single task."""
        query = "Calculate 2 + 2"
        analysis = QueryAnalysis(
            query_type=QueryType.ANALYTICAL,
            complexity=0.5,  # Below 0.7 threshold
            intent="calculation",
            entities=[],
            requires_tools=["calculator"],
            estimated_steps=1,
        )

        tasks = decomposer.decompose(query, analysis)

        assert len(tasks) == 1

    # Heuristic Decomposition Tests

    def test_heuristic_decomposition_and_then(self, decomposer: QueryDecomposer) -> None:
        """Test heuristic decomposition with 'and then' separator."""
        query = "Search for papers and then calculate average citations"
        analysis = QueryAnalysis(
            query_type=QueryType.MULTI_STEP,
            complexity=0.8,
            intent="research",
            entities=[],
            requires_tools=["document_search", "calculator"],
            estimated_steps=3,
        )

        tasks = decomposer.decompose(query, analysis)

        assert len(tasks) >= 2
        assert all(isinstance(t, SubTask) for t in tasks)
        assert tasks[0].metadata.get("decomposition") == "heuristic"

    def test_heuristic_decomposition_periods(self, decomposer: QueryDecomposer) -> None:
        """Test heuristic decomposition with period separators."""
        query = "First search for papers. Then calculate averages. Finally analyze trends."
        analysis = QueryAnalysis(
            query_type=QueryType.MULTI_STEP,
            complexity=0.8,
            intent="research",
            entities=[],
            requires_tools=[],
            estimated_steps=4,
        )

        tasks = decomposer.decompose(query, analysis)

        assert len(tasks) >= 2
        # Should have dependencies
        if len(tasks) > 1:
            assert any(t.dependencies for t in tasks[1:])

    def test_heuristic_decomposition_respects_max_tasks(self, decomposer: QueryDecomposer) -> None:
        """Test heuristic decomposition respects max_sub_tasks."""
        query = "Do A. Do B. Do C. Do D. Do E. Do F. Do G. Do H."
        analysis = QueryAnalysis(
            query_type=QueryType.MULTI_STEP,
            complexity=0.9,
            intent="multi_step",
            entities=[],
            requires_tools=[],
            estimated_steps=8,
        )

        tasks = decomposer.decompose(query, analysis)

        assert len(tasks) <= decomposer.max_sub_tasks

    # LLM Decomposition Tests

    def test_llm_decomposition_called(self, decomposer_with_llm: QueryDecomposer, mock_llm: Mock) -> None:
        """Test LLM is called for complex queries."""
        query = "Complex multi-step query"
        analysis = QueryAnalysis(
            query_type=QueryType.MULTI_STEP,
            complexity=0.8,
            intent="multi_step",
            entities=[],
            requires_tools=[],
            estimated_steps=3,
        )

        tasks = decomposer_with_llm.decompose(query, analysis)

        mock_llm.generate.assert_called_once()
        args, kwargs = mock_llm.generate.call_args
        assert query in args[0]  # Query should be in prompt

    def test_llm_decomposition_json_parsing(self, mock_llm: Mock) -> None:
        """Test LLM response JSON parsing."""
        mock_llm.generate.return_value = '''[
            {"description": "Task 1", "query": "Do task 1", "required_tools": ["tool1"], "dependencies": [], "can_run_parallel": false},
            {"description": "Task 2", "query": "Do task 2", "required_tools": [], "dependencies": ["task_0"], "can_run_parallel": true}
        ]'''

        decomposer = QueryDecomposer(llm_adapter=mock_llm)
        query = "Complex query"
        analysis = QueryAnalysis(
            query_type=QueryType.MULTI_STEP,
            complexity=0.8,
            intent="multi_step",
            entities=[],
            requires_tools=[],
            estimated_steps=3,
        )

        tasks = decomposer.decompose(query, analysis)

        assert len(tasks) == 2
        assert tasks[0].description == "Task 1"
        assert tasks[0].required_tools == ["tool1"]
        assert tasks[1].dependencies == ["task_0"]
        assert tasks[1].can_run_parallel is True

    def test_llm_decomposition_markdown_code_blocks(self, mock_llm: Mock) -> None:
        """Test LLM response with markdown code blocks."""
        mock_llm.generate.return_value = '''```json
[
    {"description": "Task", "query": "Do it", "required_tools": [], "dependencies": [], "can_run_parallel": false}
]
```'''

        decomposer = QueryDecomposer(llm_adapter=mock_llm)
        analysis = QueryAnalysis(
            query_type=QueryType.MULTI_STEP,
            complexity=0.8,
            intent="multi_step",
            entities=[],
            requires_tools=[],
            estimated_steps=3,
        )

        tasks = decomposer.decompose("query", analysis)

        assert len(tasks) == 1

    def test_llm_fallback_on_error(self, mock_llm: Mock) -> None:
        """Test fallback to heuristic when LLM fails."""
        mock_llm.generate.side_effect = Exception("LLM error")

        decomposer = QueryDecomposer(llm_adapter=mock_llm)
        query = "First do A, then do B"
        analysis = QueryAnalysis(
            query_type=QueryType.MULTI_STEP,
            complexity=0.8,
            intent="multi_step",
            entities=[],
            requires_tools=[],
            estimated_steps=3,
        )

        tasks = decomposer.decompose(query, analysis)

        # Should fall back to heuristic
        assert len(tasks) >= 1
        assert tasks[0].metadata.get("decomposition") == "heuristic"

    # Validation Tests

    def test_validation_empty_query(self, mock_llm: Mock) -> None:
        """Test validation rejects empty queries."""
        mock_llm.generate.return_value = '''[
            {"description": "Task 1", "query": "", "required_tools": [], "dependencies": [], "can_run_parallel": false},
            {"description": "Task 2", "query": "Valid query", "required_tools": [], "dependencies": [], "can_run_parallel": false}
        ]'''

        decomposer = QueryDecomposer(llm_adapter=mock_llm)
        analysis = QueryAnalysis(
            query_type=QueryType.MULTI_STEP,
            complexity=0.8,
            intent="multi_step",
            entities=[],
            requires_tools=[],
            estimated_steps=3,
        )

        tasks = decomposer.decompose("query", analysis)

        # Should only have 1 task (empty query filtered out)
        assert len(tasks) == 1
        assert tasks[0].query == "Valid query"

    def test_validation_invalid_dependencies(self, mock_llm: Mock) -> None:
        """Test validation removes invalid dependencies."""
        mock_llm.generate.return_value = '''[
            {"description": "Task 1", "query": "Do task 1", "required_tools": [], "dependencies": [], "can_run_parallel": false},
            {"description": "Task 2", "query": "Do task 2", "required_tools": [], "dependencies": ["task_0", "task_99"], "can_run_parallel": false}
        ]'''

        decomposer = QueryDecomposer(llm_adapter=mock_llm)
        analysis = QueryAnalysis(
            query_type=QueryType.MULTI_STEP,
            complexity=0.8,
            intent="multi_step",
            entities=[],
            requires_tools=[],
            estimated_steps=3,
        )

        tasks = decomposer.decompose("query", analysis)

        # task_99 should be removed, only task_0 should remain
        assert len(tasks) == 2
        assert "task_99" not in tasks[1].dependencies
        assert "task_0" in tasks[1].dependencies

    def test_validation_max_tasks_limit(self, mock_llm: Mock) -> None:
        """Test validation enforces max_sub_tasks limit."""
        # Generate 10 tasks
        tasks_json = [
            f'{{"description": "Task {i}", "query": "Do task {i}", "required_tools": [], "dependencies": [], "can_run_parallel": false}}'
            for i in range(10)
        ]
        mock_llm.generate.return_value = f'[{",".join(tasks_json)}]'

        decomposer = QueryDecomposer(llm_adapter=mock_llm, max_sub_tasks=5)
        analysis = QueryAnalysis(
            query_type=QueryType.MULTI_STEP,
            complexity=0.9,
            intent="multi_step",
            entities=[],
            requires_tools=[],
            estimated_steps=10,
        )

        tasks = decomposer.decompose("query", analysis)

        assert len(tasks) <= 5

    # Edge Cases

    def test_invalid_json_response(self, mock_llm: Mock) -> None:
        """Test handling of invalid JSON response."""
        mock_llm.generate.return_value = "Not valid JSON"

        decomposer = QueryDecomposer(llm_adapter=mock_llm)
        analysis = QueryAnalysis(
            query_type=QueryType.MULTI_STEP,
            complexity=0.8,
            intent="multi_step",
            entities=[],
            requires_tools=[],
            estimated_steps=3,
        )

        # Should fall back to heuristic
        tasks = decomposer.decompose("First do A, then do B", analysis)

        assert len(tasks) >= 1
        assert tasks[0].metadata.get("decomposition") == "heuristic"

    def test_non_array_json_response(self, mock_llm: Mock) -> None:
        """Test handling of non-array JSON response."""
        mock_llm.generate.return_value = '{"description": "Task", "query": "Do it"}'

        decomposer = QueryDecomposer(llm_adapter=mock_llm)
        analysis = QueryAnalysis(
            query_type=QueryType.MULTI_STEP,
            complexity=0.8,
            intent="multi_step",
            entities=[],
            requires_tools=[],
            estimated_steps=3,
        )

        # Should fall back to heuristic
        tasks = decomposer.decompose("First do A, then do B", analysis)

        assert len(tasks) >= 1
