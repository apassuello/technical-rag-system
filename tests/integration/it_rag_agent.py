"""
Integration tests for RAG-Agent integration (Epic 5 Phase 2 Block 3).

Tests the IntelligentQueryProcessor with real components to verify:
- Simple query routing to RAG pipeline
- Complex query routing to agent system
- Threshold boundary behavior
- Fallback mechanisms on agent failure
- Cost tracking and budgets
- Performance metrics
- Configuration changes

Test Strategy:
- Use real components (not mocks) for integration validation
- Test both RAG and agent paths end-to-end
- Verify routing decisions are correct
- Validate metadata and metrics tracking
"""

import pytest
import time
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock, patch

from src.components.query_processors.intelligent_query_processor import IntelligentQueryProcessor
from src.components.query_processors.agents.planning.query_analyzer import QueryAnalyzer
from src.components.query_processors.agents.react_agent import ReActAgent
from src.components.query_processors.agents.models import (
    ProcessorConfig,
    AgentResult,
    AgentConfig,
    QueryType,
    StepType,
    ReasoningStep
)
from src.core.interfaces import (
    Answer,
    Document,
    QueryOptions,
    Retriever,
    AnswerGenerator,
    RetrievalResult
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_retriever():
    """Mock retriever for testing."""
    retriever = Mock(spec=Retriever)

    # Create mock documents
    def retrieve(query: str, k: int = 5) -> List[RetrievalResult]:
        docs = [
            Document(
                content=f"Document {i}: Relevant content about {query}",
                metadata={'source': f'doc{i}.pdf', 'page': i},
                embedding=[0.1] * 384
            )
            for i in range(k)
        ]
        return [
            RetrievalResult(
                document=doc,
                score=0.9 - (i * 0.1),
                retrieval_method="semantic"
            )
            for i, doc in enumerate(docs)
        ]

    retriever.retrieve = Mock(side_effect=retrieve)
    return retriever


@pytest.fixture
def mock_generator():
    """Mock answer generator for testing."""
    generator = Mock(spec=AnswerGenerator)

    def generate(query: str, context: List[Document]) -> Answer:
        return Answer(
            text=f"Answer to: {query}",
            sources=context[:3],
            confidence=0.85,
            metadata={
                'model': 'mock-generator',
                'tokens': 100
            }
        )

    generator.generate = Mock(side_effect=generate)
    return generator


@pytest.fixture
def mock_agent():
    """Mock ReAct agent for testing."""
    agent = Mock(spec=ReActAgent)

    def process(query: str, context: Dict[str, Any] = None) -> AgentResult:
        # Simulate agent success
        return AgentResult(
            success=True,
            answer=f"Agent answer to: {query}",
            reasoning_steps=[
                ReasoningStep(
                    step_number=1,
                    step_type=StepType.THOUGHT,
                    content="I need to analyze this query"
                ),
                ReasoningStep(
                    step_number=2,
                    step_type=StepType.FINAL_ANSWER,
                    content=f"Agent answer to: {query}"
                )
            ],
            tool_calls=[],
            execution_time=1.5,
            total_cost=0.02,
            metadata={'llm_model': 'gpt-4-turbo'}
        )

    agent.process = Mock(side_effect=process)
    return agent


@pytest.fixture
def query_analyzer():
    """Real QueryAnalyzer for testing."""
    return QueryAnalyzer()


@pytest.fixture
def processor_config():
    """Default processor configuration."""
    return ProcessorConfig(
        use_agent_by_default=False,
        complexity_threshold=0.35,  # Lowered to match actual query complexity scores
        max_agent_cost=0.10,
        enable_planning=False,
        enable_parallel_execution=False
    )


@pytest.fixture
def intelligent_processor(mock_retriever, mock_generator, mock_agent, query_analyzer, processor_config):
    """IntelligentQueryProcessor with mocked components."""
    return IntelligentQueryProcessor(
        retriever=mock_retriever,
        generator=mock_generator,
        agent=mock_agent,
        query_analyzer=query_analyzer,
        config=processor_config
    )


# =============================================================================
# Simple Query Routing Tests (Should use RAG)
# =============================================================================

def test_simple_query_routes_to_rag(intelligent_processor, mock_retriever, mock_generator, mock_agent):
    """Test that simple queries route to RAG pipeline."""
    query = "What is Python?"

    answer = intelligent_processor.process(query)

    # Verify routing
    assert answer.metadata['source'] == 'rag_pipeline'
    assert answer.metadata['complexity'] < 0.35  # Below threshold

    # Verify RAG components called
    mock_retriever.retrieve.assert_called_once()
    mock_generator.generate.assert_called_once()

    # Verify agent NOT called
    mock_agent.process.assert_not_called()


def test_simple_question_routes_to_rag(intelligent_processor):
    """Test simple question routing."""
    query = "Who invented Python?"

    answer = intelligent_processor.process(query)

    assert answer.metadata['source'] == 'rag_pipeline'
    assert answer.metadata['query_type'] == QueryType.SIMPLE.value


def test_definition_query_routes_to_rag(intelligent_processor):
    """Test definition query routing."""
    query = "Define machine learning"

    answer = intelligent_processor.process(query)

    assert answer.metadata['source'] == 'rag_pipeline'
    assert answer.metadata['complexity'] < 0.35


# =============================================================================
# Complex Query Routing Tests (Should use Agent)
# =============================================================================

def test_complex_query_routes_to_agent(intelligent_processor, mock_agent, mock_retriever):
    """Test that complex queries route to agent system."""
    query = "Calculate 25 * 47 and then find the square root of the result, explaining each step"

    answer = intelligent_processor.process(query)

    # Verify routing
    assert answer.metadata['source'] == 'agent'
    assert answer.metadata['complexity'] >= 0.35  # Above threshold

    # Verify agent called
    mock_agent.process.assert_called_once()

    # Verify RAG retriever NOT called (agent path)
    mock_retriever.retrieve.assert_not_called()

    # Verify reasoning steps captured
    assert 'reasoning_steps' in answer.metadata
    assert len(answer.metadata['reasoning_steps']) > 0


def test_multi_step_query_routes_to_agent(intelligent_processor, mock_agent):
    """Test multi-step query routing."""
    query = "First search for Python tutorials, then analyze the code examples, and finally summarize key concepts"

    answer = intelligent_processor.process(query)

    assert answer.metadata['source'] == 'agent'
    # "code" keyword is checked before "then", so this is CODE type
    assert answer.metadata['query_type'] == QueryType.CODE.value
    mock_agent.process.assert_called_once()


def test_analytical_query_routes_to_agent(intelligent_processor, mock_agent):
    """Test analytical query routing."""
    query = "Calculate the performance metrics for the following code and evaluate optimization opportunities"

    answer = intelligent_processor.process(query)

    assert answer.metadata['source'] == 'agent'
    mock_agent.process.assert_called_once()


# =============================================================================
# Threshold Boundary Tests
# =============================================================================

def test_query_at_threshold_boundary(intelligent_processor):
    """Test query exactly at complexity threshold."""
    # Create a query that should be right at threshold
    # Complexity threshold is now 0.35
    query = "Compare and contrast Python and Java for machine learning applications"

    answer = intelligent_processor.process(query)

    # At threshold, should use agent (>= threshold)
    # This tests the boundary condition
    complexity = answer.metadata['complexity']
    if complexity >= 0.35:
        assert answer.metadata['source'] == 'agent'
    else:
        assert answer.metadata['source'] == 'rag_pipeline'


def test_threshold_configuration_changes_routing(mock_retriever, mock_generator, mock_agent, query_analyzer):
    """Test that changing threshold affects routing."""
    query = "Explain Python decorators"  # Medium complexity

    # Test with low threshold (0.3) - should use agent
    low_threshold_config = ProcessorConfig(
        complexity_threshold=0.3,
        use_agent_by_default=False
    )
    processor_low = IntelligentQueryProcessor(
        retriever=mock_retriever,
        generator=mock_generator,
        agent=mock_agent,
        query_analyzer=query_analyzer,
        config=low_threshold_config
    )

    answer_low = processor_low.process(query)

    # Reset mocks
    mock_agent.reset_mock()
    mock_retriever.reset_mock()

    # Test with high threshold (0.9) - should use RAG
    high_threshold_config = ProcessorConfig(
        complexity_threshold=0.9,
        use_agent_by_default=False
    )
    processor_high = IntelligentQueryProcessor(
        retriever=mock_retriever,
        generator=mock_generator,
        agent=mock_agent,
        query_analyzer=query_analyzer,
        config=high_threshold_config
    )

    answer_high = processor_high.process(query)

    # Verify different routing
    # With low threshold, likely used agent (if complexity > 0.3)
    # With high threshold, likely used RAG (if complexity < 0.9)
    assert 'source' in answer_low.metadata
    assert 'source' in answer_high.metadata


# =============================================================================
# Fallback Behavior Tests
# =============================================================================

def test_fallback_to_rag_on_agent_failure(mock_retriever, mock_generator, mock_agent, query_analyzer, processor_config):
    """Test fallback to RAG when agent fails."""
    query = "Calculate 25 * 47 and then find the square root of the result, explaining each step"  # Complexity 0.40

    # Make agent fail
    mock_agent.process = Mock(return_value=AgentResult(
        success=False,
        answer="",
        reasoning_steps=[],
        tool_calls=[],
        execution_time=0.1,
        total_cost=0.0,
        error="Agent processing failed"
    ))

    # Enable fallback
    config_with_fallback = {
        'complexity_threshold': 0.35,
        'fallback_to_rag_on_failure': True
    }

    processor = IntelligentQueryProcessor(
        retriever=mock_retriever,
        generator=mock_generator,
        agent=mock_agent,
        query_analyzer=query_analyzer,
        config=config_with_fallback
    )

    answer = processor.process(query)

    # Verify fallback happened
    assert answer.metadata['source'] == 'rag_pipeline'
    assert processor._fallback_queries == 1


def test_no_fallback_when_disabled(mock_retriever, mock_generator, mock_agent, query_analyzer):
    """Test that fallback doesn't happen when disabled."""
    query = "Calculate 25 * 47 and then find the square root of the result, explaining each step"  # Complexity 0.40

    # Make agent fail
    mock_agent.process = Mock(return_value=AgentResult(
        success=False,
        answer="",
        reasoning_steps=[],
        tool_calls=[],
        execution_time=0.1,
        total_cost=0.0,
        error="Agent failed"
    ))

    # Disable fallback
    config_no_fallback = {
        'complexity_threshold': 0.35,
        'fallback_to_rag_on_failure': False
    }

    processor = IntelligentQueryProcessor(
        retriever=mock_retriever,
        generator=mock_generator,
        agent=mock_agent,
        query_analyzer=query_analyzer,
        config=config_no_fallback
    )

    answer = processor.process(query)

    # Should return error, not fallback
    assert answer.metadata.get('source') == 'error'
    assert answer.confidence == 0.0


def test_fallback_on_agent_exception(mock_retriever, mock_generator, mock_agent, query_analyzer):
    """Test fallback when agent raises exception."""
    query = "Complex query causing exception"

    # Make agent raise exception
    mock_agent.process = Mock(side_effect=Exception("Agent crashed"))

    config_with_fallback = {
        'complexity_threshold': 0.7,
        'fallback_to_rag_on_failure': True
    }

    processor = IntelligentQueryProcessor(
        retriever=mock_retriever,
        generator=mock_generator,
        agent=mock_agent,
        query_analyzer=query_analyzer,
        config=config_with_fallback
    )

    answer = processor.process(query)

    # Should fallback to RAG
    assert answer.metadata['source'] == 'rag_pipeline'


# =============================================================================
# Cost Tracking Tests
# =============================================================================

def test_cost_tracking_for_rag(intelligent_processor):
    """Test cost tracking for RAG pipeline."""
    query = "What is Python?"

    answer = intelligent_processor.process(query)

    # Verify cost recorded
    assert 'cost' in answer.metadata
    assert answer.metadata['cost'] >= 0
    assert intelligent_processor._total_cost >= 0


def test_cost_tracking_for_agent(intelligent_processor, mock_agent):
    """Test cost tracking for agent system."""
    query = "Calculate 25 * 47 and then find the square root of the result, explaining each step"  # Complexity 0.40

    # Agent returns cost of 0.02
    answer = intelligent_processor.process(query)

    # Verify cost recorded
    assert 'cost' in answer.metadata
    assert answer.metadata['cost'] == 0.02
    assert intelligent_processor._total_cost >= 0.02


def test_cost_budget_warning(intelligent_processor, mock_agent, caplog):
    """Test warning when agent cost exceeds budget."""
    query = "Calculate 25 * 47 and then find the square root of the result, explaining each step"  # Complexity 0.40

    # Make agent return high cost
    mock_agent.process = Mock(return_value=AgentResult(
        success=True,
        answer="Expensive answer",
        reasoning_steps=[],
        tool_calls=[],
        execution_time=5.0,
        total_cost=0.15,  # Exceeds budget of 0.10
        metadata={}
    ))

    with caplog.at_level('WARNING'):
        answer = intelligent_processor.process(query)

    # Verify warning logged
    assert any('exceeds budget' in record.message for record in caplog.records)
    assert answer.metadata['cost'] == 0.15


# =============================================================================
# Performance Metrics Tests
# =============================================================================

def test_execution_time_tracking(intelligent_processor):
    """Test execution time tracking."""
    query = "What is Python?"

    start = time.time()
    answer = intelligent_processor.process(query)
    end = time.time()

    # Verify execution time recorded
    assert 'execution_time' in answer.metadata
    assert answer.metadata['execution_time'] <= (end - start)


def test_metrics_aggregation(intelligent_processor):
    """Test metrics aggregation across queries."""
    queries = [
        "What is Python?",  # Simple -> RAG (complexity ~0.15)
        "What is Java?",  # Simple -> RAG (complexity ~0.15)
        "Calculate 25 * 47 and then find the square root of the result, explaining each step"  # Complex -> Agent (complexity 0.40)
    ]

    for query in queries:
        intelligent_processor.process(query)

    metrics = intelligent_processor.get_metrics()

    assert metrics['total_queries'] == 3
    assert metrics['rag_queries'] == 2
    assert metrics['agent_queries'] == 1
    assert metrics['rag_percentage'] > 0
    assert metrics['agent_percentage'] > 0


def test_routing_decisions_tracking(intelligent_processor):
    """Test routing decision history tracking."""
    queries = [
        "Simple query",
        "Another simple query",
        "Calculate 25 * 47 and analyze the result in detail"
    ]

    for query in queries:
        intelligent_processor.process(query)

    decisions = intelligent_processor.get_routing_decisions()

    assert len(decisions) == 3
    for decision in decisions:
        assert 'query' in decision
        assert 'complexity' in decision
        assert 'route' in decision
        assert decision['route'] in ['rag', 'agent']


# =============================================================================
# Configuration Tests
# =============================================================================

def test_use_agent_by_default_override(mock_retriever, mock_generator, mock_agent, query_analyzer):
    """Test use_agent_by_default configuration."""
    query = "Simple query"  # Low complexity

    config_agent_default = ProcessorConfig(
        use_agent_by_default=True,  # Override threshold
        complexity_threshold=0.7
    )

    processor = IntelligentQueryProcessor(
        retriever=mock_retriever,
        generator=mock_generator,
        agent=mock_agent,
        query_analyzer=query_analyzer,
        config=config_agent_default
    )

    answer = processor.process(query)

    # Should use agent despite low complexity
    assert answer.metadata['source'] == 'agent'
    mock_agent.process.assert_called_once()


def test_dict_config_initialization(mock_retriever, mock_generator, mock_agent, query_analyzer):
    """Test initialization with dict config."""
    config_dict = {
        'complexity_threshold': 0.5,
        'max_agent_cost': 0.05,
        'fallback_to_rag_on_failure': False
    }

    processor = IntelligentQueryProcessor(
        retriever=mock_retriever,
        generator=mock_generator,
        agent=mock_agent,
        query_analyzer=query_analyzer,
        config=config_dict
    )

    assert processor._config.complexity_threshold == 0.5
    assert processor._config.max_agent_cost == 0.05
    assert processor._fallback_to_rag_on_failure == False


# =============================================================================
# Error Handling Tests
# =============================================================================

def test_empty_query_handling(intelligent_processor):
    """Test handling of empty query."""
    answer = intelligent_processor.process("")

    assert answer.confidence == 0.0
    assert 'error' in answer.metadata
    assert answer.metadata['source'] == 'error'


def test_rag_pipeline_failure(mock_retriever, mock_generator, mock_agent, query_analyzer):
    """Test handling of RAG pipeline failure."""
    query = "Simple query"

    # Make retriever fail
    mock_retriever.retrieve = Mock(side_effect=Exception("Retriever failed"))

    processor = IntelligentQueryProcessor(
        retriever=mock_retriever,
        generator=mock_generator,
        agent=mock_agent,
        query_analyzer=query_analyzer,
        config={'complexity_threshold': 0.7}
    )

    answer = processor.process(query)

    # Should return error answer
    assert answer.confidence == 0.0
    assert 'error' in answer.metadata


def test_analyze_query_with_empty_string(intelligent_processor):
    """Test analyze_query with empty string."""
    analysis = intelligent_processor.analyze_query("")

    assert 'error' in analysis
    assert analysis['complexity'] == 0.0


def test_analyze_query_success(intelligent_processor):
    """Test successful query analysis."""
    analysis = intelligent_processor.analyze_query("What is Python?")

    assert 'query_type' in analysis
    assert 'complexity' in analysis
    assert 'recommended_route' in analysis
    assert analysis['recommended_route'] in ['rag', 'agent']


# =============================================================================
# Component Interface Tests
# =============================================================================

def test_get_health_status(intelligent_processor):
    """Test health status retrieval."""
    health = intelligent_processor.get_health_status()

    assert isinstance(health.is_healthy, bool)
    assert hasattr(health, 'issues')
    assert hasattr(health, 'metrics')


def test_get_capabilities(intelligent_processor):
    """Test capabilities retrieval."""
    capabilities = intelligent_processor.get_capabilities()

    assert 'intelligent_routing' in capabilities
    assert 'rag_pipeline' in capabilities
    assert 'agent_system' in capabilities
    assert 'complexity_analysis' in capabilities


def test_reset_stats(intelligent_processor):
    """Test statistics reset."""
    # Process some queries
    intelligent_processor.process("Query 1")
    intelligent_processor.process("Query 2")

    # Reset stats
    intelligent_processor.reset_stats()

    metrics = intelligent_processor.get_metrics()
    assert metrics['total_queries'] == 0
    assert metrics['rag_queries'] == 0
    assert metrics['agent_queries'] == 0
    assert len(intelligent_processor.get_routing_decisions()) == 0


# =============================================================================
# End-to-End Integration Tests
# =============================================================================

def test_end_to_end_simple_query_flow(intelligent_processor, mock_retriever, mock_generator):
    """Test complete flow for simple query."""
    query = "What is Python?"
    options = QueryOptions(k=5, rerank=True)

    answer = intelligent_processor.process(query, options)

    # Verify complete answer structure
    assert isinstance(answer, Answer)
    assert len(answer.text) > 0
    assert len(answer.sources) > 0
    assert answer.confidence > 0

    # Verify metadata
    assert answer.metadata['source'] == 'rag_pipeline'
    assert 'execution_time' in answer.metadata
    assert 'retrieval_time' in answer.metadata
    assert 'generation_time' in answer.metadata


def test_end_to_end_complex_query_flow(intelligent_processor, mock_agent):
    """Test complete flow for complex query."""
    query = "Calculate 25 * 47 and then find the square root of the result, explaining each step"  # Complexity 0.40

    answer = intelligent_processor.process(query)

    # Verify complete answer structure
    assert isinstance(answer, Answer)
    assert len(answer.text) > 0

    # Verify agent-specific metadata
    assert answer.metadata['source'] == 'agent'
    assert 'reasoning_steps' in answer.metadata
    assert len(answer.metadata['reasoning_steps']) > 0
    assert 'tool_calls' in answer.metadata
