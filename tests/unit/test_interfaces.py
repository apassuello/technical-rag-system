"""
Comprehensive unit tests for all core interfaces and data classes.

Tests ALL components of the interface layer including:
- Data classes: Document, RetrievalResult, Answer, QueryOptions
- Component interfaces: DocumentProcessor, Embedder, VectorStore, Retriever, AnswerGenerator, QueryProcessor  
- Service interfaces: ComponentHealthService, SystemAnalyticsService, ABTestingService, ConfigurationService, BackendManagementService
- Data structures: HealthStatus, ComponentMetrics, ExperimentAssignment, ExperimentResult, BackendStatus

Following TDD principles - these tests define the CONTRACT that all implementations must satisfy.
"""

import pytest
import sys
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import (
    # Data classes
    Document, 
    RetrievalResult, 
    Answer,
    QueryOptions,
    HealthStatus,
    ComponentMetrics,
    ExperimentAssignment,
    ExperimentResult,
    BackendStatus,
    
    # Component interfaces
    ComponentBase,
    DocumentProcessor,
    Embedder,
    VectorStore,
    Retriever,
    AnswerGenerator,
    QueryProcessor,
    
    # Service interfaces
    ComponentHealthService,
    SystemAnalyticsService,
    ABTestingService,
    ConfigurationService,
    BackendManagementService
)


class TestDocument:
    """Test Document dataclass."""
    
    def test_document_creation(self):
        """Test basic document creation."""
        doc = Document(
            content="This is test content",
            metadata={"source": "test.pdf", "page": 1}
        )
        assert doc.content == "This is test content"
        assert doc.metadata["source"] == "test.pdf"
        assert doc.metadata["page"] == 1
        assert doc.embedding is None
    
    def test_document_with_embedding(self):
        """Test document with embedding."""
        embedding = [0.1, 0.2, 0.3, 0.4]
        doc = Document(
            content="Test content",
            metadata={},
            embedding=embedding
        )
        assert doc.embedding == embedding
    
    def test_document_empty_content_raises_error(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="Document content cannot be empty"):
            Document(content="", metadata={})
    
    def test_document_invalid_embedding_type(self):
        """Test that non-list embedding raises TypeError."""
        with pytest.raises(TypeError, match="Embedding must be a list of floats"):
            Document(
                content="Test content",
                metadata={},
                embedding="not a list"
            )
    
    def test_document_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        doc = Document(content="Test content")
        assert doc.metadata == {}


class TestRetrievalResult:
    """Test RetrievalResult dataclass."""
    
    def test_retrieval_result_creation(self):
        """Test basic retrieval result creation."""
        doc = Document(content="Test content", metadata={})
        result = RetrievalResult(
            document=doc,
            score=0.95,
            retrieval_method="semantic"
        )
        assert result.document == doc
        assert result.score == 0.95
        assert result.retrieval_method == "semantic"
    
    def test_retrieval_result_invalid_document_type(self):
        """Test that non-Document raises TypeError."""
        with pytest.raises(TypeError, match="document must be a Document instance"):
            RetrievalResult(
                document="not a document",
                score=0.5,
                retrieval_method="test"
            )
    
    def test_retrieval_result_score_validation(self):
        """Test score validation for BM25 and semantic scores."""
        doc = Document(content="Test", metadata={})

        # High scores are valid (BM25 can be >1 for high term frequency)
        result_bm25 = RetrievalResult(document=doc, score=15.0, retrieval_method="bm25")
        assert result_bm25.score == 15.0

        # Negative scores are invalid
        with pytest.raises(ValueError, match="Score must be a non-negative number"):
            RetrievalResult(document=doc, score=-0.1, retrieval_method="test")

        # Valid boundary and typical scores
        result_zero = RetrievalResult(document=doc, score=0.0, retrieval_method="test")
        assert result_zero.score == 0.0

        result_semantic = RetrievalResult(document=doc, score=0.85, retrieval_method="semantic")
        assert result_semantic.score == 0.85

        result_one = RetrievalResult(document=doc, score=1.0, retrieval_method="test")
        assert result_one.score == 1.0


class TestAnswer:
    """Test Answer dataclass."""
    
    def test_answer_creation(self):
        """Test basic answer creation."""
        doc1 = Document(content="Source 1", metadata={})
        doc2 = Document(content="Source 2", metadata={})
        
        answer = Answer(
            text="This is the answer",
            sources=[doc1, doc2],
            confidence=0.9,
            metadata={"model": "gpt-4"}
        )
        
        assert answer.text == "This is the answer"
        assert len(answer.sources) == 2
        assert answer.sources[0] == doc1
        assert answer.confidence == 0.9
        assert answer.metadata["model"] == "gpt-4"
    
    def test_answer_empty_text_raises_error(self):
        """Test that empty answer text raises ValueError."""
        with pytest.raises(ValueError, match="Answer text cannot be empty"):
            Answer(text="", sources=[], confidence=0.5)
    
    def test_answer_confidence_validation(self):
        """Test confidence validation."""
        # Confidence too high
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            Answer(text="Answer", sources=[], confidence=1.1)
        
        # Confidence too low
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            Answer(text="Answer", sources=[], confidence=-0.1)
    
    def test_answer_sources_type_validation(self):
        """Test that sources must be a list."""
        with pytest.raises(TypeError, match="Sources must be a list of Documents"):
            Answer(text="Answer", sources="not a list", confidence=0.5)
    
    def test_answer_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        answer = Answer(text="Answer", sources=[], confidence=0.5)
        assert answer.metadata == {}


class TestAbstractInterfaces:
    """Test that abstract interfaces cannot be instantiated."""
    
    def test_cannot_instantiate_document_processor(self):
        """Test DocumentProcessor is abstract."""
        with pytest.raises(TypeError):
            DocumentProcessor()
    
    def test_cannot_instantiate_embedder(self):
        """Test Embedder is abstract."""
        with pytest.raises(TypeError):
            Embedder()
    
    def test_cannot_instantiate_vector_store(self):
        """Test VectorStore is abstract."""
        with pytest.raises(TypeError):
            VectorStore()
    
    def test_cannot_instantiate_retriever(self):
        """Test Retriever is abstract."""
        with pytest.raises(TypeError):
            Retriever()
    
    def test_cannot_instantiate_answer_generator(self):
        """Test AnswerGenerator is abstract."""
        with pytest.raises(TypeError):
            AnswerGenerator()


class TestConcreteImplementations:
    """Test that concrete implementations work correctly."""
    
    def test_document_processor_implementation(self):
        """Test a concrete DocumentProcessor implementation."""
        
        class SimpleProcessor(DocumentProcessor):
            def process(self, file_path: Path):
                return [Document(content="Test chunk", metadata={"source": str(file_path)})]
            
            def supported_formats(self):
                return [".txt"]
            
            def get_health_status(self):
                return HealthStatus(is_healthy=True, component_name="SimpleProcessor")
            
            def get_metrics(self):
                return {"processed_files": 5}
            
            def get_capabilities(self):
                return ["text_processing"]
            
            def initialize_services(self, platform):
                pass
        
        processor = SimpleProcessor()
        docs = processor.process(Path("test.txt"))
        assert len(docs) == 1
        assert docs[0].content == "Test chunk"
        assert processor.supported_formats() == [".txt"]
    
    def test_embedder_implementation(self):
        """Test a concrete Embedder implementation."""
        
        class MockEmbedder(Embedder):
            def embed(self, texts):
                return [[0.1, 0.2, 0.3] for _ in texts]
            
            def embedding_dim(self):
                return 3
            
            def get_health_status(self):
                return HealthStatus(is_healthy=True, component_name="MockEmbedder")
            
            def get_metrics(self):
                return {"embeddings_generated": 1000}
            
            def get_capabilities(self):
                return ["semantic_embedding"]
            
            def initialize_services(self, platform):
                pass
        
        embedder = MockEmbedder()
        embeddings = embedder.embed(["text1", "text2"])
        assert len(embeddings) == 2
        assert embedder.embedding_dim() == 3


# ==============================================================================
# COMPREHENSIVE INTERFACE TESTING - TDD PROTOCOL
# ==============================================================================

class TestQueryOptions:
    """Test QueryOptions dataclass - defines query processing parameters."""
    
    def test_query_options_default_values(self):
        """Test that QueryOptions has correct default values."""
        options = QueryOptions()
        assert options.k == 5
        assert options.rerank is True
        assert options.max_tokens == 2048
        assert options.temperature == 0.7
        assert options.stream is False
    
    def test_query_options_custom_values(self):
        """Test QueryOptions with custom values."""
        options = QueryOptions(
            k=10,
            rerank=False,
            max_tokens=4096,
            temperature=0.5,
            stream=True
        )
        assert options.k == 10
        assert options.rerank is False
        assert options.max_tokens == 4096
        assert options.temperature == 0.5
        assert options.stream is True
    
    def test_query_options_partial_override(self):
        """Test QueryOptions with partial value override."""
        options = QueryOptions(k=15, temperature=0.9)
        assert options.k == 15
        assert options.rerank is True  # default
        assert options.max_tokens == 2048  # default
        assert options.temperature == 0.9
        assert options.stream is False  # default


class TestHealthStatus:
    """Test HealthStatus dataclass - component health information."""
    
    def test_health_status_creation(self):
        """Test basic HealthStatus creation."""
        status = HealthStatus(
            is_healthy=True,
            component_name="TestComponent",
            issues=[],
            metrics={"cpu": 0.5}
        )
        assert status.is_healthy is True
        assert status.component_name == "TestComponent"
        assert status.issues == []
        assert status.metrics["cpu"] == 0.5
        assert isinstance(status.last_check, float)
    
    def test_health_status_with_issues(self):
        """Test HealthStatus with health issues."""
        issues = ["High memory usage", "Connection timeout"]
        status = HealthStatus(
            is_healthy=False,
            component_name="FailingComponent",
            issues=issues
        )
        assert status.is_healthy is False
        assert status.issues == issues
    
    def test_health_status_invalid_is_healthy_type(self):
        """Test that non-boolean is_healthy raises TypeError."""
        with pytest.raises(TypeError, match="is_healthy must be a boolean"):
            HealthStatus(is_healthy="not_boolean", component_name="test")
    
    def test_health_status_invalid_issues_type(self):
        """Test that non-list issues raises TypeError."""
        with pytest.raises(TypeError, match="issues must be a list of strings"):
            HealthStatus(is_healthy=True, component_name="test", issues="not_a_list")
    
    def test_health_status_default_values(self):
        """Test HealthStatus default field values."""
        status = HealthStatus(is_healthy=True, component_name="test")
        assert status.issues == []
        assert status.metrics == {}
        assert isinstance(status.last_check, float)


class TestComponentMetrics:
    """Test ComponentMetrics dataclass - component performance metrics."""
    
    def test_component_metrics_creation(self):
        """Test basic ComponentMetrics creation."""
        metrics = ComponentMetrics(
            component_name="TestRetriever",
            component_type="retriever",
            performance_metrics={"latency": 0.05, "throughput": 100},
            resource_usage={"memory": "500MB", "cpu": 25},
            error_count=2,
            success_count=98
        )
        assert metrics.component_name == "TestRetriever"
        assert metrics.component_type == "retriever"
        assert metrics.performance_metrics["latency"] == 0.05
        assert metrics.resource_usage["memory"] == "500MB"
        assert metrics.error_count == 2
        assert metrics.success_count == 98
        assert isinstance(metrics.timestamp, float)
    
    def test_component_metrics_empty_component_name_raises_error(self):
        """Test that empty component_name raises ValueError."""
        with pytest.raises(ValueError, match="component_name cannot be empty"):
            ComponentMetrics(component_name="", component_type="test")
    
    def test_component_metrics_empty_component_type_raises_error(self):
        """Test that empty component_type raises ValueError."""
        with pytest.raises(ValueError, match="component_type cannot be empty"):
            ComponentMetrics(component_name="test", component_type="")
    
    def test_component_metrics_default_values(self):
        """Test ComponentMetrics default field values."""
        metrics = ComponentMetrics(component_name="test", component_type="embedder")
        assert metrics.performance_metrics == {}
        assert metrics.resource_usage == {}
        assert metrics.error_count == 0
        assert metrics.success_count == 0
        assert isinstance(metrics.timestamp, float)


class TestExperimentAssignment:
    """Test ExperimentAssignment dataclass - A/B test assignments."""
    
    def test_experiment_assignment_creation(self):
        """Test basic ExperimentAssignment creation."""
        assignment = ExperimentAssignment(
            experiment_id="model_comparison_v2",
            variant="gpt4_variant",
            context={"user_tier": "premium", "region": "eu"}
        )
        assert assignment.experiment_id == "model_comparison_v2"
        assert assignment.variant == "gpt4_variant"
        assert assignment.context["user_tier"] == "premium"
        assert isinstance(assignment.assignment_time, float)
    
    def test_experiment_assignment_empty_experiment_id_raises_error(self):
        """Test that empty experiment_id raises ValueError."""
        with pytest.raises(ValueError, match="experiment_id cannot be empty"):
            ExperimentAssignment(experiment_id="", variant="test_variant")
    
    def test_experiment_assignment_empty_variant_raises_error(self):
        """Test that empty variant raises ValueError."""
        with pytest.raises(ValueError, match="variant cannot be empty"):
            ExperimentAssignment(experiment_id="test_exp", variant="")
    
    def test_experiment_assignment_default_context(self):
        """Test ExperimentAssignment default context."""
        assignment = ExperimentAssignment(experiment_id="test", variant="control")
        assert assignment.context == {}


class TestExperimentResult:
    """Test ExperimentResult dataclass - A/B test outcomes."""
    
    def test_experiment_result_creation(self):
        """Test basic ExperimentResult creation."""
        outcome = {"response_time": 1.2, "satisfaction_score": 4.5, "conversion": True}
        result = ExperimentResult(
            experiment_id="model_comparison_v2",
            variant="gpt4_variant",
            outcome=outcome,
            success=True
        )
        assert result.experiment_id == "model_comparison_v2"
        assert result.variant == "gpt4_variant"
        assert result.outcome == outcome
        assert result.success is True
        assert isinstance(result.timestamp, float)
    
    def test_experiment_result_empty_experiment_id_raises_error(self):
        """Test that empty experiment_id raises ValueError."""
        with pytest.raises(ValueError, match="experiment_id cannot be empty"):
            ExperimentResult(experiment_id="", variant="test", outcome={})
    
    def test_experiment_result_empty_variant_raises_error(self):
        """Test that empty variant raises ValueError."""
        with pytest.raises(ValueError, match="variant cannot be empty"):
            ExperimentResult(experiment_id="test", variant="", outcome={})
    
    def test_experiment_result_invalid_outcome_type_raises_error(self):
        """Test that non-dict outcome raises TypeError."""
        with pytest.raises(TypeError, match="outcome must be a dictionary"):
            ExperimentResult(experiment_id="test", variant="control", outcome="not_dict")
    
    def test_experiment_result_default_success(self):
        """Test ExperimentResult default success value."""
        result = ExperimentResult(experiment_id="test", variant="control", outcome={})
        assert result.success is True


class TestBackendStatus:
    """Test BackendStatus dataclass - backend availability status."""
    
    def test_backend_status_creation(self):
        """Test basic BackendStatus creation."""
        status = BackendStatus(
            backend_name="openai_api",
            is_healthy=True,
            health_metrics={"response_time": 0.8, "rate_limit_remaining": 1000},
            error_message=None
        )
        assert status.backend_name == "openai_api"
        assert status.is_healthy is True
        assert status.health_metrics["response_time"] == 0.8
        assert status.error_message is None
        assert isinstance(status.last_check, float)
    
    def test_backend_status_with_error(self):
        """Test BackendStatus with error condition."""
        status = BackendStatus(
            backend_name="ollama_local",
            is_healthy=False,
            error_message="Connection refused"
        )
        assert status.is_healthy is False
        assert status.error_message == "Connection refused"
    
    def test_backend_status_empty_backend_name_raises_error(self):
        """Test that empty backend_name raises ValueError."""
        with pytest.raises(ValueError, match="backend_name cannot be empty"):
            BackendStatus(backend_name="", is_healthy=True)
    
    def test_backend_status_invalid_is_healthy_type_raises_error(self):
        """Test that non-boolean is_healthy raises TypeError."""
        with pytest.raises(TypeError, match="is_healthy must be a boolean"):
            BackendStatus(backend_name="test", is_healthy="not_boolean")


# ==============================================================================
# COMPONENT BASE INTERFACE TESTING
# ==============================================================================

class TestComponentBase:
    """Test ComponentBase abstract interface - foundation for all components."""
    
    def test_component_base_is_abstract(self):
        """Test that ComponentBase cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ComponentBase()
    
    def test_component_base_concrete_implementation(self):
        """Test that concrete ComponentBase implementations work correctly."""
        
        class TestComponent(ComponentBase):
            def get_health_status(self):
                return HealthStatus(is_healthy=True, component_name="TestComponent")
            
            def get_metrics(self):
                return {"test_metric": 42}
            
            def get_capabilities(self):
                return ["test_capability"]
            
            def initialize_services(self, platform):
                self.platform = platform
        
        component = TestComponent()
        
        # Test health status
        health = component.get_health_status()
        assert isinstance(health, HealthStatus)
        assert health.is_healthy is True
        assert health.component_name == "TestComponent"
        
        # Test metrics
        metrics = component.get_metrics()
        assert metrics["test_metric"] == 42
        
        # Test capabilities
        capabilities = component.get_capabilities()
        assert "test_capability" in capabilities
        
        # Test service initialization
        mock_platform = Mock()
        component.initialize_services(mock_platform)
        assert component.platform == mock_platform
    
    def test_component_base_abstract_method_enforcement(self):
        """Test that ComponentBase enforces implementation of all abstract methods."""
        
        # Missing get_health_status
        class IncompleteComponent1(ComponentBase):
            def get_metrics(self): return {}
            def get_capabilities(self): return []
            def initialize_services(self, platform): pass
        
        # Missing get_metrics  
        class IncompleteComponent2(ComponentBase):
            def get_health_status(self): return HealthStatus(is_healthy=True, component_name="test")
            def get_capabilities(self): return []
            def initialize_services(self, platform): pass
        
        # Missing get_capabilities
        class IncompleteComponent3(ComponentBase):
            def get_health_status(self): return HealthStatus(is_healthy=True, component_name="test")
            def get_metrics(self): return {}
            def initialize_services(self, platform): pass
        
        # Missing initialize_services
        class IncompleteComponent4(ComponentBase):
            def get_health_status(self): return HealthStatus(is_healthy=True, component_name="test")
            def get_metrics(self): return {}
            def get_capabilities(self): return []
        
        # All should fail to instantiate
        with pytest.raises(TypeError):
            IncompleteComponent1()
        with pytest.raises(TypeError):
            IncompleteComponent2()
        with pytest.raises(TypeError):
            IncompleteComponent3()
        with pytest.raises(TypeError):
            IncompleteComponent4()


class TestQueryProcessor:
    """Test QueryProcessor interface - orchestrates complete query workflow."""
    
    def test_query_processor_is_abstract(self):
        """Test that QueryProcessor cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            QueryProcessor()
    
    def test_query_processor_concrete_implementation(self):
        """Test concrete QueryProcessor implementation."""
        
        class TestQueryProcessor(QueryProcessor):
            def process(self, query, options=None):
                # Mock complete processing workflow
                doc = Document(content="Source content", metadata={"source": "test.pdf"})
                return Answer(text="Generated answer", sources=[doc], confidence=0.9)
            
            def analyze_query(self, query):
                return {"complexity": "medium", "query_type": "factual"}
            
            def get_health_status(self):
                return HealthStatus(is_healthy=True, component_name="TestQueryProcessor")
            
            def get_metrics(self):
                return {"queries_processed": 100, "avg_response_time": 1.2}
            
            def get_capabilities(self):
                return ["query_analysis", "answer_generation", "workflow_orchestration"]
            
            def initialize_services(self, platform):
                self.platform = platform
        
        processor = TestQueryProcessor()
        
        # Test query processing
        answer = processor.process("What is machine learning?")
        assert isinstance(answer, Answer)
        assert answer.text == "Generated answer"
        assert len(answer.sources) == 1
        
        # Test query processing with options
        options = QueryOptions(k=10, temperature=0.5)
        answer = processor.process("What is AI?", options)
        assert isinstance(answer, Answer)
        
        # Test query analysis
        analysis = processor.analyze_query("Explain neural networks")
        assert analysis["complexity"] == "medium"
        assert analysis["query_type"] == "factual"
        
        # Test ComponentBase methods
        health = processor.get_health_status()
        assert health.is_healthy is True
        
        metrics = processor.get_metrics()
        assert metrics["queries_processed"] == 100
        
        capabilities = processor.get_capabilities()
        assert "workflow_orchestration" in capabilities
    
    def test_query_processor_abstract_method_enforcement(self):
        """Test that QueryProcessor enforces implementation of abstract methods."""
        
        class IncompleteQueryProcessor(QueryProcessor):
            def analyze_query(self, query):
                return {}
            # Missing process method
            def get_health_status(self): return HealthStatus(is_healthy=True, component_name="test")
            def get_metrics(self): return {}
            def get_capabilities(self): return []
            def initialize_services(self, platform): pass
        
        with pytest.raises(TypeError):
            IncompleteQueryProcessor()


# ==============================================================================
# SERVICE INTERFACE TESTING - PLATFORM ORCHESTRATOR SERVICES  
# ==============================================================================

class TestComponentHealthService:
    """Test ComponentHealthService interface - component health monitoring."""
    
    def test_component_health_service_is_abstract(self):
        """Test that ComponentHealthService cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ComponentHealthService()
    
    def test_component_health_service_concrete_implementation(self):
        """Test concrete ComponentHealthService implementation."""
        
        class TestHealthService(ComponentHealthService):
            def __init__(self):
                self.monitored_components = []
                self.failures = []
            
            def check_component_health(self, component):
                return HealthStatus(is_healthy=True, component_name="test_component")
            
            def monitor_component_health(self, component):
                self.monitored_components.append(component)
            
            def report_component_failure(self, component, error):
                self.failures.append((component, error))
            
            def get_system_health_summary(self):
                return {
                    "overall_health": "healthy",
                    "monitored_components": len(self.monitored_components),
                    "total_failures": len(self.failures)
                }
        
        service = TestHealthService()
        mock_component = Mock()
        
        # Test health checking
        health = service.check_component_health(mock_component)
        assert isinstance(health, HealthStatus)
        assert health.is_healthy is True
        
        # Test component monitoring
        service.monitor_component_health(mock_component)
        assert len(service.monitored_components) == 1
        
        # Test failure reporting
        test_error = Exception("Test error")
        service.report_component_failure(mock_component, test_error)
        assert len(service.failures) == 1
        
        # Test system health summary
        summary = service.get_system_health_summary()
        assert summary["overall_health"] == "healthy"
        assert summary["monitored_components"] == 1
        assert summary["total_failures"] == 1


class TestSystemAnalyticsService:
    """Test SystemAnalyticsService interface - system metrics collection."""
    
    def test_system_analytics_service_is_abstract(self):
        """Test that SystemAnalyticsService cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            SystemAnalyticsService()
    
    def test_system_analytics_service_concrete_implementation(self):
        """Test concrete SystemAnalyticsService implementation."""
        
        class TestAnalyticsService(SystemAnalyticsService):
            def __init__(self):
                self.collected_metrics = []
                self.tracked_performance = []
            
            def collect_component_metrics(self, component):
                metrics = ComponentMetrics(
                    component_name="test_component",
                    component_type="test_type"
                )
                self.collected_metrics.append(metrics)
                return metrics
            
            def aggregate_system_metrics(self):
                return {
                    "total_components": len(self.collected_metrics),
                    "avg_performance": 0.95
                }
            
            def track_component_performance(self, component, metrics):
                self.tracked_performance.append((component, metrics))
            
            def generate_analytics_report(self):
                return {
                    "report_type": "system_analytics",
                    "metrics_collected": len(self.collected_metrics),
                    "performance_tracked": len(self.tracked_performance)
                }
        
        service = TestAnalyticsService()
        mock_component = Mock()
        
        # Test metrics collection
        metrics = service.collect_component_metrics(mock_component)
        assert isinstance(metrics, ComponentMetrics)
        assert len(service.collected_metrics) == 1
        
        # Test system metrics aggregation
        aggregated = service.aggregate_system_metrics()
        assert aggregated["total_components"] == 1
        
        # Test performance tracking
        perf_metrics = {"latency": 0.5, "throughput": 100}
        service.track_component_performance(mock_component, perf_metrics)
        assert len(service.tracked_performance) == 1
        
        # Test analytics report generation
        report = service.generate_analytics_report()
        assert report["report_type"] == "system_analytics"


class TestABTestingService:
    """Test ABTestingService interface - A/B testing management."""
    
    def test_ab_testing_service_is_abstract(self):
        """Test that ABTestingService cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ABTestingService()
    
    def test_ab_testing_service_concrete_implementation(self):
        """Test concrete ABTestingService implementation."""
        
        class TestABService(ABTestingService):
            def __init__(self):
                self.experiments = {}
                self.assignments = []
                self.outcomes = []
            
            def assign_experiment(self, context):
                assignment = ExperimentAssignment(
                    experiment_id="test_exp",
                    variant="control"
                )
                self.assignments.append(assignment)
                return assignment
            
            def track_experiment_outcome(self, experiment_id, variant, outcome):
                self.outcomes.append((experiment_id, variant, outcome))
            
            def get_experiment_results(self, experiment_name):
                return [ExperimentResult(
                    experiment_id=experiment_name,
                    variant="control",
                    outcome={"success": True}
                )]
            
            def configure_experiment(self, experiment_config):
                self.experiments[experiment_config["name"]] = experiment_config
        
        service = TestABService()
        
        # Test experiment assignment
        context = {"user_id": "123", "region": "us"}
        assignment = service.assign_experiment(context)
        assert isinstance(assignment, ExperimentAssignment)
        assert len(service.assignments) == 1
        
        # Test outcome tracking
        outcome = {"conversion": True, "satisfaction": 4.5}
        service.track_experiment_outcome("test_exp", "control", outcome)
        assert len(service.outcomes) == 1
        
        # Test experiment results retrieval
        results = service.get_experiment_results("test_exp")
        assert len(results) == 1
        assert isinstance(results[0], ExperimentResult)
        
        # Test experiment configuration
        config = {"name": "model_comparison", "variants": ["control", "treatment"]}
        service.configure_experiment(config)
        assert "model_comparison" in service.experiments


class TestConfigurationService:
    """Test ConfigurationService interface - configuration management."""
    
    def test_configuration_service_is_abstract(self):
        """Test that ConfigurationService cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ConfigurationService()
    
    def test_configuration_service_concrete_implementation(self):
        """Test concrete ConfigurationService implementation."""
        
        class TestConfigService(ConfigurationService):
            def __init__(self):
                self.component_configs = {}
                self.system_config = {"version": "1.0", "environment": "test"}
            
            def get_component_config(self, component_name):
                return self.component_configs.get(component_name, {})
            
            def update_component_config(self, component_name, config):
                self.component_configs[component_name] = config
            
            def validate_configuration(self, config):
                errors = []
                if "required_field" not in config:
                    errors.append("Missing required_field")
                return errors
            
            def get_system_configuration(self):
                return self.system_config
        
        service = TestConfigService()
        
        # Test component config retrieval
        config = service.get_component_config("test_component")
        assert config == {}
        
        # Test component config update
        new_config = {"model": "gpt-4", "temperature": 0.7}
        service.update_component_config("test_component", new_config)
        retrieved_config = service.get_component_config("test_component")
        assert retrieved_config == new_config
        
        # Test configuration validation
        invalid_config = {"some_field": "value"}
        errors = service.validate_configuration(invalid_config)
        assert len(errors) == 1
        assert "Missing required_field" in errors[0]
        
        valid_config = {"required_field": "value"}
        errors = service.validate_configuration(valid_config)
        assert len(errors) == 0
        
        # Test system configuration
        sys_config = service.get_system_configuration()
        assert sys_config["version"] == "1.0"


class TestBackendManagementService:
    """Test BackendManagementService interface - backend lifecycle management."""
    
    def test_backend_management_service_is_abstract(self):
        """Test that BackendManagementService cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BackendManagementService()
    
    def test_backend_management_service_concrete_implementation(self):
        """Test concrete BackendManagementService implementation."""
        
        class TestBackendService(BackendManagementService):
            def __init__(self):
                self.backends = {}
                self.component_backends = {}
                self.migrations = []
            
            def register_backend(self, backend_name, backend_config):
                self.backends[backend_name] = backend_config
            
            def switch_component_backend(self, component, backend_name):
                self.component_backends[str(component)] = backend_name
            
            def get_backend_status(self, backend_name):
                return BackendStatus(
                    backend_name=backend_name,
                    is_healthy=backend_name in self.backends
                )
            
            def migrate_component_data(self, component, from_backend, to_backend):
                self.migrations.append((str(component), from_backend, to_backend))
        
        service = TestBackendService()
        mock_component = Mock()
        
        # Test backend registration
        config = {"type": "vector_store", "url": "localhost:6333"}
        service.register_backend("qdrant_local", config)
        assert "qdrant_local" in service.backends
        
        # Test component backend switching
        service.switch_component_backend(mock_component, "qdrant_local")
        assert str(mock_component) in service.component_backends
        
        # Test backend status retrieval
        status = service.get_backend_status("qdrant_local")
        assert isinstance(status, BackendStatus)
        assert status.is_available is True
        
        unavailable_status = service.get_backend_status("nonexistent")
        assert unavailable_status.is_available is False
        
        # Test data migration
        service.migrate_component_data(mock_component, "old_backend", "new_backend")
        assert len(service.migrations) == 1
        assert service.migrations[0][1] == "old_backend"
        assert service.migrations[0][2] == "new_backend"


# ==============================================================================
# EDGE CASES AND VALIDATION TESTING
# ==============================================================================

class TestDataClassEdgeCases:
    """Test edge cases and boundary conditions for all data classes."""
    
    def test_document_with_very_large_content(self):
        """Test Document with extremely large content."""
        large_content = "A" * 1000000  # 1MB of content
        doc = Document(content=large_content)
        assert len(doc.content) == 1000000
    
    def test_document_with_special_characters(self):
        """Test Document with special characters and unicode."""
        special_content = "Test with émojis 🚀 and unicode ñáéíóú"
        doc = Document(content=special_content)
        assert doc.content == special_content
    
    def test_retrieval_result_boundary_scores(self):
        """Test RetrievalResult with boundary score values."""
        doc = Document(content="test", metadata={})
        
        # Test exact boundary values
        result_zero = RetrievalResult(document=doc, score=0.0, retrieval_method="test")
        assert result_zero.score == 0.0
        
        result_one = RetrievalResult(document=doc, score=1.0, retrieval_method="test")
        assert result_one.score == 1.0
        
        # Test very close to boundaries
        result_near_zero = RetrievalResult(document=doc, score=0.000001, retrieval_method="test")
        assert result_near_zero.score == 0.000001
        
        result_near_one = RetrievalResult(document=doc, score=0.999999, retrieval_method="test")
        assert result_near_one.score == 0.999999
    
    def test_answer_with_empty_sources_list(self):
        """Test Answer with empty sources list (valid case)."""
        answer = Answer(text="Answer without sources", sources=[], confidence=0.5)
        assert len(answer.sources) == 0
        assert answer.text == "Answer without sources"
    
    def test_answer_with_many_sources(self):
        """Test Answer with large number of sources."""
        sources = [Document(content=f"Source {i}", metadata={}) for i in range(100)]
        answer = Answer(text="Answer with many sources", sources=sources, confidence=0.8)
        assert len(answer.sources) == 100
    
    def test_health_status_with_many_issues(self):
        """Test HealthStatus with multiple issues."""
        issues = [f"Issue {i}" for i in range(50)]
        status = HealthStatus(is_healthy=False, component_name="test", issues=issues)
        assert len(status.issues) == 50
    
    def test_component_metrics_with_complex_nested_data(self):
        """Test ComponentMetrics with deeply nested performance data."""
        complex_metrics = {
            "processing": {
                "stages": {
                    "parsing": {"time": 0.1, "success_rate": 0.99},
                    "chunking": {"time": 0.05, "success_rate": 1.0},
                    "embedding": {"time": 0.3, "success_rate": 0.98}
                }
            },
            "memory": {
                "heap_usage": "256MB",
                "gc_frequency": 0.02
            }
        }
        
        metrics = ComponentMetrics(
            component_name="complex_processor",
            component_type="document_processor",
            performance_metrics=complex_metrics
        )
        
        assert metrics.performance_metrics["processing"]["stages"]["parsing"]["time"] == 0.1
        assert metrics.performance_metrics["memory"]["heap_usage"] == "256MB"


class TestInterfaceContractValidation:
    """Test interface contract compliance and type safety."""
    
    def test_document_processor_contract_validation(self):
        """Test that DocumentProcessor implementations must return correct types."""
        
        class ValidProcessor(DocumentProcessor):
            def process(self, file_path):
                return [Document(content="test", metadata={})]
            
            def supported_formats(self):
                return [".pdf", ".txt"]
                
            def get_health_status(self):
                return HealthStatus(is_healthy=True, component_name="ValidProcessor")
            
            def get_metrics(self):
                return {"processed_files": 10}
            
            def get_capabilities(self):
                return ["pdf_processing", "text_processing"]
            
            def initialize_services(self, platform):
                pass
        
        processor = ValidProcessor()
        
        # Test process method returns list of Documents
        result = processor.process(Path("test.pdf"))
        assert isinstance(result, list)
        assert all(isinstance(doc, Document) for doc in result)
        
        # Test supported_formats returns list of strings
        formats = processor.supported_formats()
        assert isinstance(formats, list)
        assert all(isinstance(fmt, str) for fmt in formats)
    
    def test_embedder_contract_validation(self):
        """Test that Embedder implementations return correct types."""
        
        class ValidEmbedder(Embedder):
            def embed(self, texts):
                return [[0.1, 0.2, 0.3] for _ in texts]
            
            def embedding_dim(self):
                return 3
                
            def get_health_status(self):
                return HealthStatus(is_healthy=True, component_name="ValidEmbedder")
            
            def get_metrics(self):
                return {"embeddings_generated": 1000}
            
            def get_capabilities(self):
                return ["semantic_embedding", "fast_inference"]
            
            def initialize_services(self, platform):
                pass
        
        embedder = ValidEmbedder()
        
        # Test embed method returns list of lists
        embeddings = embedder.embed(["text1", "text2"])
        assert isinstance(embeddings, list)
        assert len(embeddings) == 2
        assert all(isinstance(emb, list) for emb in embeddings)
        
        # Test embedding_dim returns integer
        dim = embedder.embedding_dim()
        assert isinstance(dim, int)
        assert dim > 0
    
    def test_vector_store_contract_validation(self):
        """Test that VectorStore implementations handle operations correctly."""
        
        class ValidVectorStore(VectorStore):
            def __init__(self):
                self.documents = []
            
            def add(self, documents):
                self.documents.extend(documents)
            
            def search(self, query_embedding, k=5):
                results = []
                for doc in self.documents[:k]:
                    result = RetrievalResult(
                        document=doc,
                        score=0.9,
                        retrieval_method="vector_similarity"
                    )
                    results.append(result)
                return results
            
            def delete(self, doc_ids):
                # Mock deletion
                pass
            
            def clear(self):
                self.documents = []
                
            def get_health_status(self):
                return HealthStatus(is_healthy=True, component_name="ValidVectorStore")
            
            def get_metrics(self):
                return {"stored_documents": len(self.documents)}
            
            def get_capabilities(self):
                return ["vector_storage", "similarity_search"]
            
            def initialize_services(self, platform):
                pass
        
        store = ValidVectorStore()
        doc_with_embedding = Document(
            content="test content",
            metadata={},
            embedding=[0.1, 0.2, 0.3]
        )
        
        # Test add method
        store.add([doc_with_embedding])
        assert len(store.documents) == 1
        
        # Test search method returns list of RetrievalResults
        results = store.search([0.1, 0.2, 0.3], k=1)
        assert isinstance(results, list)
        assert all(isinstance(result, RetrievalResult) for result in results)


# ==============================================================================
# SERIALIZATION AND PERSISTENCE TESTING
# ==============================================================================

class TestDataClassSerialization:
    """Test serialization/deserialization of data classes for persistence."""
    
    def test_document_serialization(self):
        """Test Document can be converted to/from dict for JSON serialization."""
        doc = Document(
            content="Test content",
            metadata={"source": "test.pdf", "page": 1},
            embedding=[0.1, 0.2, 0.3]
        )
        
        # Convert to dict (simulate JSON serialization)
        doc_dict = {
            "content": doc.content,
            "metadata": doc.metadata,
            "embedding": doc.embedding
        }
        
        # Convert back to Document
        restored_doc = Document(**doc_dict)
        
        assert restored_doc.content == doc.content
        assert restored_doc.metadata == doc.metadata
        assert restored_doc.embedding == doc.embedding
    
    def test_retrieval_result_serialization(self):
        """Test RetrievalResult serialization."""
        doc = Document(content="source", metadata={})
        result = RetrievalResult(
            document=doc,
            score=0.85,
            retrieval_method="hybrid",
            metadata={"rerank_score": 0.9}
        )
        
        # Simulate serialization (would need custom serializer for Document)
        result_dict = {
            "document": {
                "content": result.document.content,
                "metadata": result.document.metadata,
                "embedding": result.document.embedding
            },
            "score": result.score,
            "retrieval_method": result.retrieval_method,
            "metadata": result.metadata
        }
        
        # Restore
        restored_result = RetrievalResult(
            document=Document(**result_dict["document"]),
            score=result_dict["score"],
            retrieval_method=result_dict["retrieval_method"],
            metadata=result_dict["metadata"]
        )
        
        assert restored_result.score == result.score
        assert restored_result.retrieval_method == result.retrieval_method
        assert restored_result.document.content == result.document.content
    
    def test_answer_serialization(self):
        """Test Answer serialization with multiple sources."""
        sources = [
            Document(content="Source 1", metadata={"page": 1}),
            Document(content="Source 2", metadata={"page": 2})
        ]
        answer = Answer(
            text="Generated answer",
            sources=sources,
            confidence=0.92,
            metadata={"model": "gpt-4", "temperature": 0.7}
        )
        
        # Simulate serialization
        answer_dict = {
            "text": answer.text,
            "sources": [
                {"content": doc.content, "metadata": doc.metadata, "embedding": doc.embedding}
                for doc in answer.sources
            ],
            "confidence": answer.confidence,
            "metadata": answer.metadata
        }
        
        # Restore
        restored_answer = Answer(
            text=answer_dict["text"],
            sources=[Document(**source_dict) for source_dict in answer_dict["sources"]],
            confidence=answer_dict["confidence"],
            metadata=answer_dict["metadata"]
        )
        
        assert restored_answer.text == answer.text
        assert len(restored_answer.sources) == len(answer.sources)
        assert restored_answer.confidence == answer.confidence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])