"""
Metrics collector for the calibration system.

Implements the metrics collector component from calibration-system-spec.md
for gathering performance metrics during test runs.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for a single query execution following calibration-system-spec.md structure."""
    query_id: str
    query_text: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Retrieval metrics
    retrieval_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Generation metrics  
    generation_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Validation results
    validation_results: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """
    Gathers performance metrics during test runs following calibration-system-spec.md.
    
    Collects comprehensive metrics for calibration analysis including retrieval quality,
    generation performance, and validation results.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.query_metrics: List[QueryMetrics] = []
        self.session_metadata: Dict[str, Any] = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "start_time": datetime.now().isoformat(),
            "parameter_config": {},
            "system_config": {}
        }

    def start_query_collection(self, query_id: str, query_text: str) -> QueryMetrics:
        """Start collecting metrics for a query."""
        metrics = QueryMetrics(query_id=query_id, query_text=query_text)
        
        # Initialize default structure
        metrics.retrieval_metrics = {
            "documents_retrieved": 0,
            "avg_semantic_score": 0.0,
            "avg_bm25_score": 0.0,
            "fusion_score_spread": 0.0,
            "retrieval_time": 0.0,
            "dense_results_count": 0,
            "sparse_results_count": 0,
            "fusion_results_count": 0
        }
        
        metrics.generation_metrics = {
            "confidence_score": 0.0,
            "answer_length": 0,
            "citations_used": 0,
            "generation_time": 0.0,
            "model_used": "",
            "temperature": 0.0
        }
        
        metrics.validation_results = {
            "meets_expectations": False,
            "confidence_in_range": False,
            "contains_required_terms": False,
            "has_citations": False,
            "answer_quality_score": 0.0
        }
        
        metrics.performance_metrics = {
            "total_time": 0.0,
            "memory_peak_mb": 0,
            "cpu_usage_percent": 0.0
        }
        
        self.query_metrics.append(metrics)
        logger.debug(f"Started metrics collection for query: {query_id}")
        return metrics

    def collect_retrieval_metrics(
        self, 
        query_metrics: QueryMetrics,
        retrieval_results: List[Tuple[int, float]],
        dense_results: Optional[List[Tuple[int, float]]] = None,
        sparse_results: Optional[List[Tuple[int, float]]] = None,
        retrieval_time: float = 0.0
    ) -> None:
        """Collect retrieval-specific metrics."""
        
        if retrieval_results:
            scores = [score for _, score in retrieval_results]
            query_metrics.retrieval_metrics.update({
                "documents_retrieved": len(retrieval_results),
                "avg_semantic_score": np.mean(scores) if scores else 0.0,
                "max_score": max(scores) if scores else 0.0,
                "min_score": min(scores) if scores else 0.0,
                "score_std": np.std(scores) if scores else 0.0,
                "fusion_score_spread": max(scores) - min(scores) if scores else 0.0,
                "retrieval_time": retrieval_time
            })

        if dense_results:
            dense_scores = [score for _, score in dense_results]
            query_metrics.retrieval_metrics.update({
                "dense_results_count": len(dense_results),
                "avg_dense_score": np.mean(dense_scores) if dense_scores else 0.0,
                "dense_score_spread": max(dense_scores) - min(dense_scores) if dense_scores else 0.0
            })

        if sparse_results:
            sparse_scores = [score for _, score in sparse_results] 
            query_metrics.retrieval_metrics.update({
                "sparse_results_count": len(sparse_results),
                "avg_bm25_score": np.mean(sparse_scores) if sparse_scores else 0.0,
                "sparse_score_spread": max(sparse_scores) - min(sparse_scores) if sparse_scores else 0.0
            })

        logger.debug(f"Collected retrieval metrics for {query_metrics.query_id}")

    def collect_generation_metrics(
        self,
        query_metrics: QueryMetrics,
        answer: str,
        confidence_score: float,
        generation_time: float,
        citations: Optional[List[Dict[str, Any]]] = None,
        model_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """Collect answer generation metrics."""
        
        query_metrics.generation_metrics.update({
            "confidence_score": confidence_score,
            "answer_length": len(answer) if answer else 0,
            "word_count": len(answer.split()) if answer else 0,
            "citations_used": len(citations) if citations else 0,
            "generation_time": generation_time
        })

        if model_info:
            query_metrics.generation_metrics.update({
                "model_used": model_info.get("model_name", "unknown"),
                "temperature": model_info.get("temperature", 0.0),
                "max_tokens": model_info.get("max_tokens", 0)
            })

        if citations:
            citation_scores = [c.get("relevance", 0.0) for c in citations]
            query_metrics.generation_metrics.update({
                "avg_citation_relevance": np.mean(citation_scores) if citation_scores else 0.0,
                "citation_sources": list(set(c.get("source", "unknown") for c in citations))
            })

        logger.debug(f"Collected generation metrics for {query_metrics.query_id}")

    def collect_validation_results(
        self,
        query_metrics: QueryMetrics, 
        expected_behavior: Dict[str, Any],
        actual_results: Dict[str, Any]
    ) -> None:
        """Collect validation results against expected behavior."""
        
        # Basic validation checks
        meets_expectations = True
        validation_details = {}

        # Check confidence range
        expected_min_conf = expected_behavior.get("min_confidence", 0.0)
        expected_max_conf = expected_behavior.get("max_confidence", 1.0)
        actual_confidence = actual_results.get("confidence", 0.0)
        
        confidence_in_range = expected_min_conf <= actual_confidence <= expected_max_conf
        validation_details["confidence_check"] = {
            "expected_range": [expected_min_conf, expected_max_conf],
            "actual": actual_confidence,
            "passed": confidence_in_range
        }

        if not confidence_in_range:
            meets_expectations = False

        # Check required terms
        required_terms = expected_behavior.get("must_contain_terms", [])
        answer_text = actual_results.get("answer", "").lower()
        
        contains_required_terms = all(term.lower() in answer_text for term in required_terms)
        validation_details["required_terms_check"] = {
            "required_terms": required_terms,
            "found_terms": [term for term in required_terms if term.lower() in answer_text],
            "passed": contains_required_terms
        }

        if required_terms and not contains_required_terms:
            meets_expectations = False

        # Check forbidden terms  
        forbidden_terms = expected_behavior.get("must_not_contain", [])
        contains_forbidden_terms = any(term.lower() in answer_text for term in forbidden_terms)
        validation_details["forbidden_terms_check"] = {
            "forbidden_terms": forbidden_terms,
            "found_forbidden": [term for term in forbidden_terms if term.lower() in answer_text],
            "passed": not contains_forbidden_terms
        }

        if contains_forbidden_terms:
            meets_expectations = False

        # Check citations
        has_citations = len(actual_results.get("citations", [])) > 0
        expected_citations = expected_behavior.get("min_citations", 0)
        sufficient_citations = len(actual_results.get("citations", [])) >= expected_citations
        
        validation_details["citations_check"] = {
            "expected_min": expected_citations,
            "actual_count": len(actual_results.get("citations", [])),
            "passed": sufficient_citations
        }

        if expected_citations > 0 and not sufficient_citations:
            meets_expectations = False

        # Update metrics
        query_metrics.validation_results.update({
            "meets_expectations": meets_expectations,
            "confidence_in_range": confidence_in_range,
            "contains_required_terms": contains_required_terms,
            "has_citations": has_citations,
            "validation_details": validation_details,
            "answer_quality_score": self._calculate_answer_quality_score(validation_details)
        })

        logger.debug(f"Collected validation results for {query_metrics.query_id}: {'PASS' if meets_expectations else 'FAIL'}")

    def _calculate_answer_quality_score(self, validation_details: Dict[str, Any]) -> float:
        """Calculate composite answer quality score."""
        checks = [
            validation_details.get("confidence_check", {}).get("passed", False),
            validation_details.get("required_terms_check", {}).get("passed", False), 
            validation_details.get("forbidden_terms_check", {}).get("passed", False),
            validation_details.get("citations_check", {}).get("passed", False)
        ]
        
        return sum(checks) / len(checks) if checks else 0.0

    def collect_performance_metrics(
        self,
        query_metrics: QueryMetrics,
        total_time: float,
        memory_peak_mb: Optional[float] = None,
        cpu_usage_percent: Optional[float] = None
    ) -> None:
        """Collect performance metrics."""
        
        query_metrics.performance_metrics.update({
            "total_time": total_time,
            "memory_peak_mb": memory_peak_mb or 0,
            "cpu_usage_percent": cpu_usage_percent or 0.0
        })

    def update_session_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update session-level metadata."""
        self.session_metadata.update(metadata)

    def calculate_aggregate_metrics(self) -> Dict[str, Any]:
        """Calculate aggregate metrics across all queries."""
        if not self.query_metrics:
            return {}

        aggregate = {
            "total_queries": len(self.query_metrics),
            "session_metadata": self.session_metadata
        }

        # Retrieval aggregates
        retrieval_times = [q.retrieval_metrics.get("retrieval_time", 0) for q in self.query_metrics]
        documents_retrieved = [q.retrieval_metrics.get("documents_retrieved", 0) for q in self.query_metrics]
        score_spreads = [q.retrieval_metrics.get("fusion_score_spread", 0) for q in self.query_metrics]

        aggregate["retrieval_aggregates"] = {
            "avg_retrieval_time": np.mean(retrieval_times) if retrieval_times else 0,
            "p95_retrieval_time": np.percentile(retrieval_times, 95) if retrieval_times else 0,
            "avg_documents_per_query": np.mean(documents_retrieved) if documents_retrieved else 0,
            "avg_score_spread": np.mean(score_spreads) if score_spreads else 0
        }

        # Generation aggregates
        generation_times = [q.generation_metrics.get("generation_time", 0) for q in self.query_metrics]
        confidence_scores = [q.generation_metrics.get("confidence_score", 0) for q in self.query_metrics]
        answer_lengths = [q.generation_metrics.get("answer_length", 0) for q in self.query_metrics]

        aggregate["generation_aggregates"] = {
            "avg_generation_time": np.mean(generation_times) if generation_times else 0,
            "avg_confidence": np.mean(confidence_scores) if confidence_scores else 0,
            "avg_answer_length": np.mean(answer_lengths) if answer_lengths else 0
        }

        # Validation aggregates
        quality_scores = [q.validation_results.get("answer_quality_score", 0) for q in self.query_metrics]
        meets_expectations = [q.validation_results.get("meets_expectations", False) for q in self.query_metrics]

        aggregate["validation_aggregates"] = {
            "avg_quality_score": np.mean(quality_scores) if quality_scores else 0,
            "success_rate": np.mean(meets_expectations) if meets_expectations else 0,
            "total_passed": sum(meets_expectations),
            "total_failed": len(meets_expectations) - sum(meets_expectations)
        }

        # Performance aggregates
        total_times = [q.performance_metrics.get("total_time", 0) for q in self.query_metrics]
        
        aggregate["performance_aggregates"] = {
            "avg_total_time": np.mean(total_times) if total_times else 0,
            "p95_total_time": np.percentile(total_times, 95) if total_times else 0,
            "throughput_queries_per_sec": len(self.query_metrics) / sum(total_times) if sum(total_times) > 0 else 0
        }

        return aggregate

    def export_metrics(self, output_path: Path) -> None:
        """Export collected metrics to JSON file."""
        try:
            export_data = {
                "session_metadata": self.session_metadata,
                "query_metrics": [
                    {
                        "query_id": q.query_id,
                        "query_text": q.query_text,
                        "timestamp": q.timestamp,
                        "retrieval_metrics": q.retrieval_metrics,
                        "generation_metrics": q.generation_metrics,
                        "validation_results": q.validation_results,
                        "performance_metrics": q.performance_metrics
                    }
                    for q in self.query_metrics
                ],
                "aggregate_metrics": self.calculate_aggregate_metrics()
            }

            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            logger.info(f"Exported metrics to {output_path}")

        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")

    def get_metrics_summary(self) -> str:
        """Get human-readable summary of collected metrics."""
        if not self.query_metrics:
            return "No metrics collected yet."

        aggregates = self.calculate_aggregate_metrics()
        
        summary = [
            f"Metrics Collection Summary",
            f"=" * 40,
            f"Total Queries: {len(self.query_metrics)}",
            f"Session ID: {self.session_metadata.get('session_id', 'unknown')}",
            f"",
            f"RETRIEVAL PERFORMANCE:",
            f"  Avg Retrieval Time: {aggregates['retrieval_aggregates']['avg_retrieval_time']:.3f}s",
            f"  Avg Documents/Query: {aggregates['retrieval_aggregates']['avg_documents_per_query']:.1f}",
            f"  Avg Score Spread: {aggregates['retrieval_aggregates']['avg_score_spread']:.3f}",
            f"",
            f"GENERATION PERFORMANCE:",
            f"  Avg Generation Time: {aggregates['generation_aggregates']['avg_generation_time']:.3f}s",
            f"  Avg Confidence: {aggregates['generation_aggregates']['avg_confidence']:.3f}",
            f"  Avg Answer Length: {aggregates['generation_aggregates']['avg_answer_length']:.0f} chars",
            f"",
            f"VALIDATION RESULTS:",
            f"  Success Rate: {aggregates['validation_aggregates']['success_rate']*100:.1f}%",
            f"  Avg Quality Score: {aggregates['validation_aggregates']['avg_quality_score']:.3f}",
            f"  Passed: {aggregates['validation_aggregates']['total_passed']}",
            f"  Failed: {aggregates['validation_aggregates']['total_failed']}",
            f"",
            f"SYSTEM PERFORMANCE:",
            f"  Avg Total Time: {aggregates['performance_aggregates']['avg_total_time']:.3f}s",
            f"  Throughput: {aggregates['performance_aggregates']['throughput_queries_per_sec']:.2f} queries/sec"
        ]

        return "\n".join(summary)


if __name__ == "__main__":
    # Test the metrics collector
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
        [{"source": "risc-v-spec.pdf", "relevance": 0.92}],
        {"model_name": "llama3.2:3b", "temperature": 0.3}
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
    
    print(collector.get_metrics_summary())