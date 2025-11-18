"""
Unit tests for IntelligentQueryProcessor (Epic 5 Phase 2 Block 3).

Tests processor initialization, configuration, routing logic, and internal methods.

Test Strategy:
- Focus on processor logic and configuration
- Test routing decisions in isolation
- Validate initialization and dependency injection
- Verify statistics and metrics tracking
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.components.query_processors.intelligent_query_processor import IntelligentQueryProcessor
from src.components.query_processors.agents.planning.query_analyzer import QueryAnalyzer
from src.components.query_processors.agents.react_agent import ReActAgent
from src.components.query_processors.agents.models import (
    ProcessorConfig,
    AgentResult,
    QueryType,
    QueryAnalysis,
    StepType,
    ReasoningStep
)
from src.core.interfaces import (
    Answer,
    Document,
    Retriever,
    AnswerGenerator
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_components():
    """Create all mock components."""
    retriever = Mock(spec=Retriever)
    generator = Mock(spec=AnswerGenerator)
    agent = Mock(spec=ReActAgent)
    query_analyzer = Mock(spec=QueryAnalyzer)

    return {
        'retriever': retriever,
        'generator': generator,
        'agent': agent,
        'query_analyzer': query_analyzer
    }


@pytest.fixture
def processor_with_mocks(mock_components):
    """Create IntelligentQueryProcessor with mocked components."""
    return IntelligentQueryProcessor(
        retriever=mock_components['retriever'],
        generator=mock_components['generator'],
        agent=mock_components['agent'],
        query_analyzer=mock_components['query_analyzer'],
        config={'complexity_threshold': 0.7}
    )


# =============================================================================
# Initialization Tests
# =============================================================================

def test_processor_initialization_with_config_object(mock_components):
    """Test initialization with ProcessorConfig object."""
    config = ProcessorConfig(
        use_agent_by_default=False,
        complexity_threshold=0.8,
        max_agent_cost=0.15,
        enable_planning=True,
        enable_parallel_execution=True
    )

    processor = IntelligentQueryProcessor(
        **mock_components,
        config=config
    )

    assert processor._config.complexity_threshold == 0.8
    assert processor._config.max_agent_cost == 0.15
    assert processor._config.enable_planning == True
    assert processor._config.enable_parallel_execution == True


def test_processor_initialization_with_dict_config(mock_components):
    """Test initialization with dict config."""
    config = {
        'complexity_threshold': 0.6,
        'max_agent_cost': 0.08,
        'fallback_to_rag_on_failure': False
    }

    processor = IntelligentQueryProcessor(
        **mock_components,
        config=config
    )

    assert processor._config.complexity_threshold == 0.6
    assert processor._config.max_agent_cost == 0.08
    assert processor._fallback_to_rag_on_failure == False


def test_processor_initialization_with_none_config(mock_components):
    """Test initialization with no config (uses defaults)."""
    processor = IntelligentQueryProcessor(
        **mock_components,
        config=None
    )

    # Check defaults
    assert processor._config.complexity_threshold == 0.7
    assert processor._config.max_agent_cost == 0.10
    assert processor._config.use_agent_by_default == False


def test_processor_tracks_statistics_on_init(mock_components):
    """Test that processor initializes statistics counters."""
    processor = IntelligentQueryProcessor(
        **mock_components
    )

    assert processor._total_queries == 0
    assert processor._rag_queries == 0
    assert processor._agent_queries == 0
    assert processor._fallback_queries == 0
    assert processor._total_cost == 0.0
    assert processor._total_time == 0.0


# =============================================================================
# Routing Logic Tests
# =============================================================================

def test_should_use_agent_high_complexity(processor_with_mocks):
    """Test _should_use_agent with high complexity."""
    analysis = QueryAnalysis(
        query_type=QueryType.ANALYTICAL,
        complexity=0.85,  # > threshold
        intent="analysis",
        entities=[],
        requires_tools=['calculator'],
        estimated_steps=3
    )

    result = processor_with_mocks._should_use_agent(analysis)
    assert result == True


def test_should_use_agent_low_complexity(processor_with_mocks):
    """Test _should_use_agent with low complexity."""
    analysis = QueryAnalysis(
        query_type=QueryType.SIMPLE,
        complexity=0.3,  # < threshold
        intent="information_retrieval",
        entities=[],
        requires_tools=[],
        estimated_steps=1
    )

    result = processor_with_mocks._should_use_agent(analysis)
    assert result == False


def test_should_use_agent_at_threshold(processor_with_mocks):
    """Test _should_use_agent at exact threshold."""
    analysis = QueryAnalysis(
        query_type=QueryType.RESEARCH,
        complexity=0.7,  # == threshold
        intent="research",
        entities=[],
        requires_tools=[],
        estimated_steps=2
    )

    # At threshold, should use agent (>= threshold)
    result = processor_with_mocks._should_use_agent(analysis)
    assert result == True


def test_should_use_agent_with_override(mock_components):
    """Test _should_use_agent with use_agent_by_default override."""
    config = ProcessorConfig(
        use_agent_by_default=True,
        complexity_threshold=0.7
    )

    processor = IntelligentQueryProcessor(
        **mock_components,
        config=config
    )

    # Low complexity analysis
    analysis = QueryAnalysis(
        query_type=QueryType.SIMPLE,
        complexity=0.2,
        intent="information_retrieval",
        entities=[],
        requires_tools=[],
        estimated_steps=1
    )

    # Should use agent despite low complexity (due to override)
    result = processor._should_use_agent(analysis)
    assert result == True


# =============================================================================
# Internal Method Tests
# =============================================================================

def test_analyze_query_success(processor_with_mocks):
    """Test _analyze_query with successful analysis."""
    # Setup mock analyzer
    expected_analysis = QueryAnalysis(
        query_type=QueryType.SIMPLE,
        complexity=0.4,
        intent="information_retrieval",
        entities=['Python'],
        requires_tools=[],
        estimated_steps=1
    )

    processor_with_mocks._query_analyzer.analyze = Mock(return_value=expected_analysis)

    result = processor_with_mocks._analyze_query("What is Python?")

    assert result == expected_analysis
    processor_with_mocks._query_analyzer.analyze.assert_called_once_with("What is Python?")


def test_analyze_query_with_analyzer_failure(processor_with_mocks, caplog):
    """Test _analyze_query when analyzer fails (fallback)."""
    # Make analyzer fail
    processor_with_mocks._query_analyzer.analyze = Mock(side_effect=Exception("Analyzer error"))

    with caplog.at_level('WARNING'):
        result = processor_with_mocks._analyze_query("Test query")

    # Should return fallback analysis
    assert result.query_type == QueryType.SIMPLE
    assert result.complexity == 0.3  # Default fallback complexity
    assert 'analyzer_error' in result.metadata


def test_estimate_rag_cost(processor_with_mocks):
    """Test _estimate_rag_cost calculation."""
    cost = processor_with_mocks._estimate_rag_cost("Query", "Answer")

    # Should return a small cost estimate
    assert isinstance(cost, float)
    assert cost >= 0
    assert cost < 0.01  # Local RAG should be cheap


def test_create_error_answer(processor_with_mocks):
    """Test _create_error_answer creation."""
    answer = processor_with_mocks._create_error_answer(
        query="Test query",
        error="Test error",
        complexity=0.5,
        execution_time=1.0
    )

    assert isinstance(answer, Answer)
    assert answer.confidence == 0.0
    assert answer.metadata['source'] == 'error'
    assert answer.metadata['error'] == "Test error"
    assert answer.metadata['complexity'] == 0.5
    assert answer.metadata['execution_time'] == 1.0


def test_perform_health_check_all_healthy(processor_with_mocks):
    """Test _perform_health_check with all components healthy."""
    health = processor_with_mocks._perform_health_check()

    assert health['healthy'] == True
    assert len(health['issues']) == 0


def test_perform_health_check_missing_retriever(mock_components):
    """Test _perform_health_check with missing retriever."""
    mock_components['retriever'] = None

    processor = IntelligentQueryProcessor(**mock_components)
    health = processor._perform_health_check()

    assert health['healthy'] == False
    assert 'Retriever not available' in health['issues']


def test_perform_health_check_missing_agent(mock_components):
    """Test _perform_health_check with missing agent."""
    mock_components['agent'] = None

    processor = IntelligentQueryProcessor(**mock_components)
    health = processor._perform_health_check()

    assert health['healthy'] == False
    assert 'Agent not available' in health['issues']


# =============================================================================
# Statistics and Metrics Tests
# =============================================================================

def test_get_metrics_initial_state(processor_with_mocks):
    """Test get_metrics with initial state."""
    metrics = processor_with_mocks.get_metrics()

    assert metrics['total_queries'] == 0
    assert metrics['rag_queries'] == 0
    assert metrics['agent_queries'] == 0
    assert metrics['total_cost'] == 0.0
    assert metrics['total_time'] == 0.0
    assert metrics['avg_cost_per_query'] == 0.0
    assert metrics['avg_time_per_query'] == 0.0


def test_reset_stats(processor_with_mocks):
    """Test reset_stats clears all statistics."""
    # Set some statistics
    processor_with_mocks._total_queries = 10
    processor_with_mocks._rag_queries = 7
    processor_with_mocks._agent_queries = 3
    processor_with_mocks._total_cost = 0.05
    processor_with_mocks._total_time = 5.0
    processor_with_mocks._routing_decisions = [{'test': 'data'}]

    # Reset
    processor_with_mocks.reset_stats()

    # Verify all cleared
    assert processor_with_mocks._total_queries == 0
    assert processor_with_mocks._rag_queries == 0
    assert processor_with_mocks._agent_queries == 0
    assert processor_with_mocks._total_cost == 0.0
    assert processor_with_mocks._total_time == 0.0
    assert len(processor_with_mocks._routing_decisions) == 0


def test_get_routing_decisions(processor_with_mocks):
    """Test get_routing_decisions returns copy of decisions."""
    # Add some decisions
    processor_with_mocks._routing_decisions = [
        {'query': 'q1', 'route': 'rag'},
        {'query': 'q2', 'route': 'agent'}
    ]

    decisions = processor_with_mocks.get_routing_decisions()

    # Verify returns copy
    assert len(decisions) == 2
    assert decisions == processor_with_mocks._routing_decisions

    # Verify it's a copy (modifying doesn't affect original)
    decisions.append({'query': 'q3', 'route': 'rag'})
    assert len(processor_with_mocks._routing_decisions) == 2


# =============================================================================
# Configuration Tests
# =============================================================================

def test_complexity_threshold_configuration(mock_components):
    """Test different complexity threshold values."""
    thresholds = [0.3, 0.5, 0.7, 0.9]

    for threshold in thresholds:
        processor = IntelligentQueryProcessor(
            **mock_components,
            config={'complexity_threshold': threshold}
        )
        assert processor._config.complexity_threshold == threshold


def test_max_agent_cost_configuration(mock_components):
    """Test different max_agent_cost values."""
    costs = [0.01, 0.05, 0.10, 0.20]

    for cost in costs:
        processor = IntelligentQueryProcessor(
            **mock_components,
            config={'max_agent_cost': cost}
        )
        assert processor._config.max_agent_cost == cost


def test_fallback_configuration(mock_components):
    """Test fallback_to_rag_on_failure configuration."""
    # Test enabled
    processor_enabled = IntelligentQueryProcessor(
        **mock_components,
        config={'fallback_to_rag_on_failure': True}
    )
    assert processor_enabled._fallback_to_rag_on_failure == True

    # Test disabled
    processor_disabled = IntelligentQueryProcessor(
        **mock_components,
        config={'fallback_to_rag_on_failure': False}
    )
    assert processor_disabled._fallback_to_rag_on_failure == False


def test_track_routing_decisions_configuration(mock_components):
    """Test track_routing_decisions configuration."""
    # Test enabled
    processor_enabled = IntelligentQueryProcessor(
        **mock_components,
        config={'track_routing_decisions': True}
    )
    assert processor_enabled._track_routing_decisions == True

    # Test disabled
    processor_disabled = IntelligentQueryProcessor(
        **mock_components,
        config={'track_routing_decisions': False}
    )
    assert processor_disabled._track_routing_decisions == False


# =============================================================================
# Component Interface Tests
# =============================================================================

def test_get_capabilities(processor_with_mocks):
    """Test get_capabilities returns correct capabilities."""
    capabilities = processor_with_mocks.get_capabilities()

    # Check base capabilities
    assert 'intelligent_routing' in capabilities
    assert 'rag_pipeline' in capabilities
    assert 'agent_system' in capabilities
    assert 'complexity_analysis' in capabilities
    assert 'cost_tracking' in capabilities
    assert 'fallback_handling' in capabilities


def test_get_capabilities_with_planning(mock_components):
    """Test get_capabilities with planning enabled."""
    config = ProcessorConfig(enable_planning=True)

    processor = IntelligentQueryProcessor(
        **mock_components,
        config=config
    )

    capabilities = processor.get_capabilities()
    assert 'query_planning' in capabilities


def test_get_capabilities_with_parallel_execution(mock_components):
    """Test get_capabilities with parallel execution enabled."""
    config = ProcessorConfig(enable_parallel_execution=True)

    processor = IntelligentQueryProcessor(
        **mock_components,
        config=config
    )

    capabilities = processor.get_capabilities()
    assert 'parallel_execution' in capabilities


def test_initialize_services(processor_with_mocks):
    """Test initialize_services sets platform."""
    mock_platform = Mock()

    processor_with_mocks.initialize_services(mock_platform)

    assert processor_with_mocks.platform == mock_platform


# =============================================================================
# String Representation Tests
# =============================================================================

def test_repr(processor_with_mocks):
    """Test __repr__ string representation."""
    repr_str = repr(processor_with_mocks)

    assert 'IntelligentQueryProcessor' in repr_str
    assert 'threshold=0.7' in repr_str
    assert 'total_queries=0' in repr_str


# =============================================================================
# Analyze Query Public Method Tests
# =============================================================================

def test_analyze_query_public_method(processor_with_mocks):
    """Test public analyze_query method."""
    # Setup mock
    expected_analysis = QueryAnalysis(
        query_type=QueryType.ANALYTICAL,
        complexity=0.75,
        intent="analysis",
        entities=['Python', 'Java'],
        requires_tools=['calculator'],
        estimated_steps=3,
        metadata={'test': 'data'}
    )

    processor_with_mocks._query_analyzer.analyze = Mock(return_value=expected_analysis)

    result = processor_with_mocks.analyze_query("Compare Python and Java")

    # Verify structure
    assert result['query_type'] == QueryType.ANALYTICAL.value
    assert result['complexity'] == 0.75
    assert result['intent'] == "analysis"
    assert result['entities'] == ['Python', 'Java']
    assert result['requires_tools'] == ['calculator']
    assert result['estimated_steps'] == 3
    assert result['recommended_route'] == 'agent'  # Complexity 0.75 > 0.7


def test_analyze_query_recommends_rag_for_simple(processor_with_mocks):
    """Test analyze_query recommends RAG for simple queries."""
    # Setup mock
    simple_analysis = QueryAnalysis(
        query_type=QueryType.SIMPLE,
        complexity=0.3,
        intent="information_retrieval",
        entities=[],
        requires_tools=[],
        estimated_steps=1
    )

    processor_with_mocks._query_analyzer.analyze = Mock(return_value=simple_analysis)

    result = processor_with_mocks.analyze_query("What is Python?")

    assert result['recommended_route'] == 'rag'  # Complexity 0.3 < 0.7


def test_analyze_query_with_empty_query(processor_with_mocks):
    """Test analyze_query with empty query."""
    result = processor_with_mocks.analyze_query("")

    assert 'error' in result
    assert result['complexity'] == 0.0
    assert result['recommended_route'] is None


def test_analyze_query_handles_exception(processor_with_mocks, caplog):
    """Test analyze_query handles exceptions gracefully."""
    processor_with_mocks._query_analyzer.analyze = Mock(side_effect=Exception("Test error"))

    with caplog.at_level('ERROR'):
        result = processor_with_mocks.analyze_query("Test query")

    assert 'error' in result
    assert result['complexity'] == 0.0
    assert result['recommended_route'] is None
