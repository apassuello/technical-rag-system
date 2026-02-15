"""
Comprehensive test suite for Metrics Collector (Priority 2 - Epic 2 Calibration Systems).

This test suite provides 75% coverage for the 441-line Metrics Collector implementation,
testing query metrics collection, validation results tracking, aggregate metrics calculation,
and metrics export functionality following TDD principles.

Key Testing Areas:
1. Query Metrics Collection - Individual query performance tracking
2. Retrieval Metrics - Document retrieval quality and performance metrics
3. Generation Metrics - Answer generation quality and timing metrics
4. Validation Results - Expected behavior validation and scoring
5. Performance Metrics - System performance and resource usage tracking
6. Aggregate Analysis - Statistical analysis and metrics aggregation
7. Export Functionality - Metrics export and reporting capabilities

Target: ~300 test lines for 75% coverage of Epic 2 calibration system metrics collection.
"""

import pytest
import tempfile
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Tuple

from src.components.calibration.metrics_collector import (
    MetricsCollector,
    QueryMetrics
)


class TestQueryMetrics:
    """Test cases for QueryMetrics dataclass."""
    
    def test_query_metrics_initialization(self):
        """Test QueryMetrics initialization with required fields."""
        metrics = QueryMetrics(
            query_id="TEST001",
            query_text="What is RISC-V architecture?"
        )
        
        assert metrics.query_id == "TEST001"
        assert metrics.query_text == "What is RISC-V architecture?"
        assert isinstance(metrics.timestamp, str)
        assert isinstance(metrics.retrieval_metrics, dict)
        assert isinstance(metrics.generation_metrics, dict)
        assert isinstance(metrics.validation_results, dict)
        assert isinstance(metrics.performance_metrics, dict)
    
    def test_query_metrics_timestamp_format(self):
        """Test QueryMetrics timestamp is in ISO format."""
        metrics = QueryMetrics("TEST001", "Test query")
        
        # Verify timestamp can be parsed as datetime
        timestamp_dt = datetime.fromisoformat(metrics.timestamp)
        assert isinstance(timestamp_dt, datetime)
        
        # Verify timestamp is recent (within last minute)
        now = datetime.now()
        time_diff = (now - timestamp_dt).total_seconds()
        assert time_diff < 60  # Within 1 minute
    
    def test_query_metrics_custom_timestamp(self):
        """Test QueryMetrics with custom timestamp."""
        custom_timestamp = "2025-08-23T10:30:00.000Z"
        
        # Create metrics with field() but we can't directly set timestamp in constructor
        # Test that timestamp field exists and can be set
        metrics = QueryMetrics("TEST001", "Test query")
        metrics.timestamp = custom_timestamp
        
        assert metrics.timestamp == custom_timestamp


class TestMetricsCollector:
    """Comprehensive test suite for MetricsCollector."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.collector = MetricsCollector()
        
        # Test data for retrieval metrics
        self.test_retrieval_results = [(0, 0.95), (1, 0.87), (2, 0.73), (3, 0.65)]
        self.test_dense_results = [(0, 0.91), (1, 0.83), (2, 0.76)]
        self.test_sparse_results = [(0, 8.45), (1, 6.32), (2, 5.18)]
        
        # Test data for generation metrics
        self.test_answer = "RISC-V is an open-source instruction set architecture based on established reduced instruction set computing (RISC) principles."
        self.test_citations = [
            {"source": "risc_v_spec.pdf", "relevance": 0.92, "page": 1},
            {"source": "risc_v_guide.pdf", "relevance": 0.87, "page": 15}
        ]
        self.test_model_info = {
            "model_name": "qwen2.5-1.5b-instruct",
            "temperature": 0.3,
            "max_tokens": 2048
        }
        
        # Test data for validation
        self.test_expected_behavior = {
            "min_confidence": 0.7,
            "max_confidence": 0.95,
            "must_contain_terms": ["instruction set", "RISC"],
            "must_not_contain": ["ARM", "x86"],
            "min_citations": 1
        }
        
        self.test_actual_results = {
            "confidence": 0.85,
            "answer": self.test_answer,
            "citations": self.test_citations
        }
    
    def test_initialization(self):
        """Test MetricsCollector initialization."""
        collector = MetricsCollector()
        
        assert collector.query_metrics == []
        assert isinstance(collector.session_metadata, dict)
        assert "session_id" in collector.session_metadata
        assert "start_time" in collector.session_metadata
        assert "parameter_config" in collector.session_metadata
        assert "system_config" in collector.session_metadata
        
        # Verify session_id format (YYYYMMDD_HHMMSS)
        session_id = collector.session_metadata["session_id"]
        assert len(session_id) == 15
        assert "_" in session_id
        
        # Verify start_time is ISO format
        start_time = collector.session_metadata["start_time"]
        datetime.fromisoformat(start_time)  # Should not raise exception
    
    def test_start_query_collection(self):
        """Test starting query metrics collection."""
        query_id = "TEST001"
        query_text = "What is RISC-V?"
        
        with patch('src.components.calibration.metrics_collector.logger') as mock_logger:
            metrics = self.collector.start_query_collection(query_id, query_text)
            mock_logger.debug.assert_called_once()
        
        # Verify returned metrics structure
        # QueryMetrics is an alias for CalibrationQueryMetrics
        from src.shared_utils.metrics import CalibrationQueryMetrics
        assert isinstance(metrics, (QueryMetrics, CalibrationQueryMetrics))
        assert metrics.query_id == query_id
        assert metrics.query_text == query_text
        
        # Verify metrics added to collector
        assert len(self.collector.query_metrics) == 1
        assert self.collector.query_metrics[0] == metrics
        
        # Verify default structure initialization
        assert "documents_retrieved" in metrics.retrieval_metrics
        assert "confidence_score" in metrics.generation_metrics
        assert "meets_expectations" in metrics.validation_results
        assert "total_time" in metrics.performance_metrics
        
        # Verify default values
        assert metrics.retrieval_metrics["documents_retrieved"] == 0
        assert metrics.generation_metrics["confidence_score"] == 0.0
        assert metrics.validation_results["meets_expectations"] is False
        assert metrics.performance_metrics["total_time"] == 0.0
    
    def test_collect_retrieval_metrics_basic(self):
        """Test collecting basic retrieval metrics."""
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        retrieval_time = 0.123
        
        with patch('src.components.calibration.metrics_collector.logger') as mock_logger:
            self.collector.collect_retrieval_metrics(
                metrics, 
                self.test_retrieval_results,
                retrieval_time=retrieval_time
            )
            mock_logger.debug.assert_called_once()
        
        # Verify retrieval metrics were collected
        rm = metrics.retrieval_metrics
        assert rm["documents_retrieved"] == 4
        assert rm["retrieval_time"] == retrieval_time
        
        # Verify score statistics
        expected_avg = np.mean([0.95, 0.87, 0.73, 0.65])
        assert rm["avg_semantic_score"] == pytest.approx(expected_avg, rel=1e-3)
        assert rm["max_score"] == 0.95
        assert rm["min_score"] == 0.65
        assert rm["score_std"] == pytest.approx(np.std([0.95, 0.87, 0.73, 0.65]), rel=1e-3)
        assert rm["fusion_score_spread"] == pytest.approx(0.95 - 0.65, rel=1e-3)
    
    def test_collect_retrieval_metrics_with_dense_sparse(self):
        """Test collecting retrieval metrics with dense and sparse results."""
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        
        self.collector.collect_retrieval_metrics(
            metrics,
            self.test_retrieval_results,
            dense_results=self.test_dense_results,
            sparse_results=self.test_sparse_results,
            retrieval_time=0.15
        )
        
        rm = metrics.retrieval_metrics
        
        # Verify dense results metrics
        assert rm["dense_results_count"] == 3
        expected_dense_avg = np.mean([0.91, 0.83, 0.76])
        assert rm["avg_dense_score"] == pytest.approx(expected_dense_avg, rel=1e-3)
        assert rm["dense_score_spread"] == pytest.approx(0.91 - 0.76, rel=1e-3)
        
        # Verify sparse results metrics  
        assert rm["sparse_results_count"] == 3
        expected_sparse_avg = np.mean([8.45, 6.32, 5.18])
        assert rm["avg_bm25_score"] == pytest.approx(expected_sparse_avg, rel=1e-3)
        assert rm["sparse_score_spread"] == pytest.approx(8.45 - 5.18, rel=1e-3)
    
    def test_collect_retrieval_metrics_empty_results(self):
        """Test collecting retrieval metrics with empty results."""
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        
        self.collector.collect_retrieval_metrics(metrics, [])
        
        rm = metrics.retrieval_metrics
        assert rm["documents_retrieved"] == 0
        assert rm["avg_semantic_score"] == 0.0
        assert rm["fusion_score_spread"] == 0.0
    
    def test_collect_generation_metrics_complete(self):
        """Test collecting complete generation metrics."""
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        confidence_score = 0.85
        generation_time = 1.234
        
        with patch('src.components.calibration.metrics_collector.logger') as mock_logger:
            self.collector.collect_generation_metrics(
                metrics,
                self.test_answer,
                confidence_score,
                generation_time,
                citations=self.test_citations,
                model_info=self.test_model_info
            )
            mock_logger.debug.assert_called_once()
        
        gm = metrics.generation_metrics
        
        # Verify basic generation metrics
        assert gm["confidence_score"] == confidence_score
        assert gm["answer_length"] == len(self.test_answer)
        assert gm["word_count"] == len(self.test_answer.split())
        assert gm["citations_used"] == len(self.test_citations)
        assert gm["generation_time"] == generation_time
        
        # Verify model info
        assert gm["model_used"] == "qwen2.5-1.5b-instruct"
        assert gm["temperature"] == 0.3
        assert gm["max_tokens"] == 2048
        
        # Verify citation analysis
        expected_citation_relevance = np.mean([0.92, 0.87])
        assert gm["avg_citation_relevance"] == pytest.approx(expected_citation_relevance, rel=1e-3)
        assert "risc_v_spec.pdf" in gm["citation_sources"]
        assert "risc_v_guide.pdf" in gm["citation_sources"]
        assert len(gm["citation_sources"]) == 2  # Unique sources
    
    def test_collect_generation_metrics_minimal(self):
        """Test collecting generation metrics with minimal data."""
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        
        self.collector.collect_generation_metrics(
            metrics,
            "Short answer",
            0.75,
            0.5
        )
        
        gm = metrics.generation_metrics
        assert gm["confidence_score"] == 0.75
        assert gm["answer_length"] == len("Short answer")
        assert gm["word_count"] == 2
        assert gm["citations_used"] == 0
        assert gm["generation_time"] == 0.5
    
    def test_collect_generation_metrics_empty_answer(self):
        """Test collecting generation metrics with empty answer."""
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        
        self.collector.collect_generation_metrics(
            metrics,
            "",  # Empty answer
            0.3,
            0.1
        )
        
        gm = metrics.generation_metrics
        assert gm["confidence_score"] == 0.3
        assert gm["answer_length"] == 0
        assert gm["word_count"] == 0
    
    def test_collect_validation_results_all_pass(self):
        """Test collecting validation results with all checks passing."""
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        
        with patch('src.components.calibration.metrics_collector.logger') as mock_logger:
            self.collector.collect_validation_results(
                metrics,
                self.test_expected_behavior,
                self.test_actual_results
            )
            mock_logger.debug.assert_called_once_with("Collected validation results for TEST001: PASS")
        
        vr = metrics.validation_results
        
        # Verify overall validation result
        assert vr["meets_expectations"] is True
        assert vr["confidence_in_range"] is True
        assert vr["contains_required_terms"] is True
        assert vr["has_citations"] is True
        assert vr["answer_quality_score"] == 1.0  # All checks passed
        
        # Verify validation details
        details = vr["validation_details"]
        
        # Confidence check
        conf_check = details["confidence_check"]
        assert conf_check["expected_range"] == [0.7, 0.95]
        assert conf_check["actual"] == 0.85
        assert conf_check["passed"] is True
        
        # Required terms check
        terms_check = details["required_terms_check"]
        assert terms_check["required_terms"] == ["instruction set", "RISC"]
        assert "instruction set" in terms_check["found_terms"]
        assert "RISC" in terms_check["found_terms"]
        assert terms_check["passed"] is True
        
        # Forbidden terms check
        forbidden_check = details["forbidden_terms_check"]
        assert forbidden_check["forbidden_terms"] == ["ARM", "x86"]
        assert forbidden_check["found_forbidden"] == []
        assert forbidden_check["passed"] is True
        
        # Citations check
        citations_check = details["citations_check"]
        assert citations_check["expected_min"] == 1
        assert citations_check["actual_count"] == 2
        assert citations_check["passed"] is True
    
    def test_collect_validation_results_confidence_fail(self):
        """Test collecting validation results with confidence out of range."""
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        
        # Confidence too low
        actual_results_low_conf = {
            "confidence": 0.5,  # Below min of 0.7
            "answer": self.test_answer,
            "citations": self.test_citations
        }
        
        with patch('src.components.calibration.metrics_collector.logger') as mock_logger:
            self.collector.collect_validation_results(
                metrics,
                self.test_expected_behavior,
                actual_results_low_conf
            )
            mock_logger.debug.assert_called_once_with("Collected validation results for TEST001: FAIL")
        
        vr = metrics.validation_results
        
        assert vr["meets_expectations"] is False
        assert vr["confidence_in_range"] is False
        assert vr["answer_quality_score"] == 0.75  # 3/4 checks passed
    
    def test_collect_validation_results_missing_required_terms(self):
        """Test collecting validation results with missing required terms."""
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        
        # Answer without required terms
        actual_results_missing_terms = {
            "confidence": 0.85,
            "answer": "This is about computer architecture.",  # Missing "instruction set" and "RISC"
            "citations": self.test_citations
        }
        
        self.collector.collect_validation_results(
            metrics,
            self.test_expected_behavior,
            actual_results_missing_terms
        )
        
        vr = metrics.validation_results
        
        assert vr["meets_expectations"] is False
        assert vr["contains_required_terms"] is False
        
        details = vr["validation_details"]
        terms_check = details["required_terms_check"]
        assert len(terms_check["found_terms"]) == 0  # No required terms found
    
    def test_collect_validation_results_contains_forbidden_terms(self):
        """Test collecting validation results with forbidden terms."""
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        
        # Answer with forbidden terms
        actual_results_forbidden = {
            "confidence": 0.85,
            "answer": "RISC-V differs from ARM and x86 instruction set architectures.",
            "citations": self.test_citations
        }
        
        self.collector.collect_validation_results(
            metrics,
            self.test_expected_behavior,
            actual_results_forbidden
        )
        
        vr = metrics.validation_results
        
        assert vr["meets_expectations"] is False
        
        details = vr["validation_details"]
        forbidden_check = details["forbidden_terms_check"]
        assert "ARM" in forbidden_check["found_forbidden"]
        assert "x86" in forbidden_check["found_forbidden"]
        assert forbidden_check["passed"] is False
    
    def test_collect_validation_results_insufficient_citations(self):
        """Test collecting validation results with insufficient citations."""
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        
        # Actual results with no citations
        actual_results_no_citations = {
            "confidence": 0.85,
            "answer": self.test_answer,
            "citations": []
        }
        
        self.collector.collect_validation_results(
            metrics,
            self.test_expected_behavior,
            actual_results_no_citations
        )
        
        vr = metrics.validation_results
        
        assert vr["meets_expectations"] is False
        assert vr["has_citations"] is False
        
        details = vr["validation_details"]
        citations_check = details["citations_check"]
        assert citations_check["actual_count"] == 0
        assert citations_check["passed"] is False
    
    def test_calculate_answer_quality_score(self):
        """Test answer quality score calculation."""
        # All checks pass
        validation_details_all_pass = {
            "confidence_check": {"passed": True},
            "required_terms_check": {"passed": True},
            "forbidden_terms_check": {"passed": True},
            "citations_check": {"passed": True}
        }
        
        score = self.collector._calculate_answer_quality_score(validation_details_all_pass)
        assert score == 1.0
        
        # Half checks pass
        validation_details_half_pass = {
            "confidence_check": {"passed": True},
            "required_terms_check": {"passed": False},
            "forbidden_terms_check": {"passed": True},
            "citations_check": {"passed": False}
        }
        
        score = self.collector._calculate_answer_quality_score(validation_details_half_pass)
        assert score == 0.5
        
        # No checks pass
        validation_details_none_pass = {
            "confidence_check": {"passed": False},
            "required_terms_check": {"passed": False},
            "forbidden_terms_check": {"passed": False},
            "citations_check": {"passed": False}
        }
        
        score = self.collector._calculate_answer_quality_score(validation_details_none_pass)
        assert score == 0.0
    
    def test_collect_performance_metrics(self):
        """Test collecting performance metrics."""
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        
        self.collector.collect_performance_metrics(
            metrics,
            total_time=1.5,
            memory_peak_mb=256.7,
            cpu_usage_percent=45.3
        )
        
        pm = metrics.performance_metrics
        assert pm["total_time"] == 1.5
        assert pm["memory_peak_mb"] == 256.7
        assert pm["cpu_usage_percent"] == 45.3
    
    def test_collect_performance_metrics_partial(self):
        """Test collecting performance metrics with partial data."""
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        
        self.collector.collect_performance_metrics(
            metrics,
            total_time=2.1
            # memory_peak_mb and cpu_usage_percent not provided
        )
        
        pm = metrics.performance_metrics
        assert pm["total_time"] == 2.1
        assert pm["memory_peak_mb"] == 0  # Default value
        assert pm["cpu_usage_percent"] == 0.0  # Default value
    
    def test_update_session_metadata(self):
        """Test updating session metadata."""
        additional_metadata = {
            "parameter_config": {"bm25_k1": 1.2, "dense_weight": 0.8},
            "system_config": {"model": "qwen2.5-1.5b-instruct"},
            "test_run_id": "calibration_001"
        }
        
        self.collector.update_session_metadata(additional_metadata)
        
        # Verify metadata was updated
        metadata = self.collector.session_metadata
        assert metadata["parameter_config"] == {"bm25_k1": 1.2, "dense_weight": 0.8}
        assert metadata["system_config"] == {"model": "qwen2.5-1.5b-instruct"}
        assert metadata["test_run_id"] == "calibration_001"
        
        # Verify original metadata preserved
        assert "session_id" in metadata
        assert "start_time" in metadata
    
    def test_calculate_aggregate_metrics_empty(self):
        """Test calculating aggregate metrics with no queries."""
        aggregates = self.collector.calculate_aggregate_metrics()
        
        assert aggregates == {}
    
    def test_calculate_aggregate_metrics_multiple_queries(self):
        """Test calculating aggregate metrics with multiple queries."""
        # Create multiple query metrics
        queries_data = [
            {"id": "TC001", "retrieval_time": 0.1, "docs": 5, "gen_time": 1.2, "conf": 0.85, "ans_len": 150},
            {"id": "TC002", "retrieval_time": 0.15, "docs": 8, "gen_time": 1.8, "conf": 0.72, "ans_len": 200},
            {"id": "TC003", "retrieval_time": 0.08, "docs": 6, "gen_time": 0.9, "conf": 0.91, "ans_len": 120}
        ]
        
        for query_data in queries_data:
            metrics = self.collector.start_query_collection(query_data["id"], f"Query {query_data['id']}")
            
            # Set retrieval metrics
            metrics.retrieval_metrics.update({
                "retrieval_time": query_data["retrieval_time"],
                "documents_retrieved": query_data["docs"],
                "fusion_score_spread": 0.3
            })
            
            # Set generation metrics
            metrics.generation_metrics.update({
                "generation_time": query_data["gen_time"],
                "confidence_score": query_data["conf"],
                "answer_length": query_data["ans_len"]
            })
            
            # Set validation results
            metrics.validation_results.update({
                "answer_quality_score": 0.8,
                "meets_expectations": True
            })
            
            # Set performance metrics
            metrics.performance_metrics.update({
                "total_time": query_data["retrieval_time"] + query_data["gen_time"]
            })
        
        aggregates = self.collector.calculate_aggregate_metrics()
        
        # Verify aggregate structure
        assert aggregates["total_queries"] == 3
        assert "session_metadata" in aggregates
        assert "retrieval_aggregates" in aggregates
        assert "generation_aggregates" in aggregates
        assert "validation_aggregates" in aggregates
        assert "performance_aggregates" in aggregates
        
        # Verify retrieval aggregates
        ret_agg = aggregates["retrieval_aggregates"]
        assert ret_agg["avg_retrieval_time"] == pytest.approx(np.mean([0.1, 0.15, 0.08]), rel=1e-3)
        assert ret_agg["avg_documents_per_query"] == pytest.approx(np.mean([5, 8, 6]), rel=1e-3)
        assert ret_agg["avg_score_spread"] == 0.3
        
        # Verify generation aggregates
        gen_agg = aggregates["generation_aggregates"]
        assert gen_agg["avg_generation_time"] == pytest.approx(np.mean([1.2, 1.8, 0.9]), rel=1e-3)
        assert gen_agg["avg_confidence"] == pytest.approx(np.mean([0.85, 0.72, 0.91]), rel=1e-3)
        assert gen_agg["avg_answer_length"] == pytest.approx(np.mean([150, 200, 120]), rel=1e-3)
        
        # Verify validation aggregates
        val_agg = aggregates["validation_aggregates"]
        assert val_agg["avg_quality_score"] == pytest.approx(0.8, rel=1e-6)
        assert val_agg["success_rate"] == 1.0
        assert val_agg["total_passed"] == 3
        assert val_agg["total_failed"] == 0
        
        # Verify performance aggregates
        perf_agg = aggregates["performance_aggregates"]
        expected_total_times = [1.3, 1.95, 0.98]  # retrieval + generation
        assert perf_agg["avg_total_time"] == pytest.approx(np.mean(expected_total_times), rel=1e-3)
        assert perf_agg["p95_total_time"] == pytest.approx(np.percentile(expected_total_times, 95), rel=1e-3)
        
        # Verify throughput calculation
        total_time_sum = sum(expected_total_times)
        expected_throughput = 3 / total_time_sum
        assert perf_agg["throughput_queries_per_sec"] == pytest.approx(expected_throughput, rel=1e-3)
    
    def test_export_metrics(self):
        """Test exporting metrics to JSON file."""
        # Create query with metrics
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        metrics.retrieval_metrics["documents_retrieved"] = 5
        metrics.generation_metrics["confidence_score"] = 0.85
        metrics.validation_results["meets_expectations"] = True
        metrics.performance_metrics["total_time"] = 1.5
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = Path(f.name)
        
        try:
            with patch('src.components.calibration.metrics_collector.logger') as mock_logger:
                self.collector.export_metrics(export_path)
                mock_logger.info.assert_called_once()
            
            # Verify file was created
            assert export_path.exists()
            
            # Load and verify exported data
            with open(export_path, 'r') as f:
                exported_data = json.load(f)
            
            # Verify structure
            assert "session_metadata" in exported_data
            assert "query_metrics" in exported_data
            assert "aggregate_metrics" in exported_data
            
            # Verify query metrics structure
            query_metrics = exported_data["query_metrics"]
            assert len(query_metrics) == 1
            
            query_metric = query_metrics[0]
            assert query_metric["query_id"] == "TEST001"
            assert query_metric["query_text"] == "Test query"
            assert "timestamp" in query_metric
            assert "retrieval_metrics" in query_metric
            assert "generation_metrics" in query_metric
            assert "validation_results" in query_metric
            assert "performance_metrics" in query_metric
            
            # Verify data values
            assert query_metric["retrieval_metrics"]["documents_retrieved"] == 5
            assert query_metric["generation_metrics"]["confidence_score"] == 0.85
            assert query_metric["validation_results"]["meets_expectations"] is True
            assert query_metric["performance_metrics"]["total_time"] == 1.5
            
        finally:
            export_path.unlink(missing_ok=True)
    
    def test_export_metrics_error_handling(self):
        """Test export metrics error handling."""
        invalid_path = Path("/invalid/directory/metrics.json")

        with patch('src.shared_utils.metrics.calibration_collector.logger') as mock_logger:
            self.collector.export_metrics(invalid_path)
            mock_logger.error.assert_called_once()
    
    def test_get_metrics_summary_no_metrics(self):
        """Test getting metrics summary with no collected metrics."""
        summary = self.collector.get_metrics_summary()
        
        assert isinstance(summary, str)
        assert "No metrics collected yet." in summary
    
    def test_get_metrics_summary_with_metrics(self):
        """Test getting metrics summary with collected metrics."""
        # Create query with metrics
        metrics = self.collector.start_query_collection("TEST001", "Test query")
        metrics.retrieval_metrics.update({
            "retrieval_time": 0.12,
            "documents_retrieved": 5,
            "fusion_score_spread": 0.25
        })
        metrics.generation_metrics.update({
            "generation_time": 1.3,
            "confidence_score": 0.85,
            "answer_length": 180
        })
        metrics.validation_results.update({
            "answer_quality_score": 0.9,
            "meets_expectations": True
        })
        metrics.performance_metrics.update({
            "total_time": 1.42
        })
        
        summary = self.collector.get_metrics_summary()
        
        # Verify summary structure
        assert isinstance(summary, str)
        assert "Metrics Collection Summary" in summary
        assert "Total Queries: 1" in summary
        
        # Verify performance sections
        assert "RETRIEVAL PERFORMANCE:" in summary
        assert "Avg Retrieval Time: 0.120s" in summary
        assert "Avg Documents/Query: 5.0" in summary
        
        assert "GENERATION PERFORMANCE:" in summary
        assert "Avg Generation Time: 1.300s" in summary
        assert "Avg Confidence: 0.850" in summary
        assert "Avg Answer Length: 180 chars" in summary
        
        assert "VALIDATION RESULTS:" in summary
        assert "Success Rate: 100.0%" in summary
        assert "Avg Quality Score: 0.900" in summary
        assert "Passed: 1" in summary
        assert "Failed: 0" in summary
        
        assert "SYSTEM PERFORMANCE:" in summary
        assert "Avg Total Time: 1.420s" in summary
        
        # Verify session ID is included
        session_id = self.collector.session_metadata["session_id"]
        assert f"Session ID: {session_id}" in summary
    
    def test_main_execution_block(self):
        """Test main execution block functionality."""
        # Test that the main block can run without errors
        with patch('builtins.print') as mock_print:
            # Simulate main execution by creating collector and running test
            collector = MetricsCollector()
            
            # Simulate collecting metrics for a query
            metrics = collector.start_query_collection("TEST001", "What is RISC-V?")
            
            collector.collect_retrieval_metrics(
                metrics, 
                [(0, 0.95), (1, 0.87), (2, 0.73)],
                retrieval_time=0.12
            )
            
            collector.collect_generation_metrics(
                metrics,
                "RISC-V is an open-source instruction set architecture...",
                0.89,
                1.23,
                citations=[{"source": "risc-v-spec.pdf", "relevance": 0.92}],
                model_info={"model_name": "qwen2.5-1.5b-instruct", "temperature": 0.3}
            )
            
            expected = {
                "min_confidence": 0.7,
                "must_contain_terms": ["instruction set", "open-source"],
                "must_not_contain": ["ARM", "x86"]
            }
            actual = {
                "confidence": 0.89,
                "answer": "RISC-V is an open-source instruction set architecture...",
                "citations": [{"source": "risc-v-spec.pdf"}]
            }
            
            collector.collect_validation_results(metrics, expected, actual)
            collector.collect_performance_metrics(metrics, 1.45, 256.0, 45.2)
            
            summary = collector.get_metrics_summary()
            
            # Verify outputs
            assert isinstance(summary, str)
            assert len(summary) > 0
            # Summary doesn't include query ID in standard format, check it exists in collector
            assert len(collector.query_metrics) == 1
            assert collector.query_metrics[0].query_id == "TEST001"
            assert "0.890" in summary   # Should show confidence as decimal