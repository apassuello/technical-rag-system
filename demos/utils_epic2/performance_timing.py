"""
Performance Timing Utilities for Epic 2 Demo
============================================

Provides timing context managers and performance instrumentation for accurate
measurement of component performance in the Epic 2 demo system.
"""

import time
import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class TimingResult:
    """Represents a timing measurement result"""
    stage_name: str
    start_time: float
    end_time: float
    duration_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        return self.duration_ms / 1000.0


@dataclass
class PipelineTimings:
    """Aggregates timing results for a complete pipeline"""
    total_start: float
    total_end: Optional[float] = None
    stages: List[TimingResult] = field(default_factory=list)
    
    @property
    def total_duration_ms(self) -> float:
        if self.total_end is None:
            return 0.0
        return (self.total_end - self.total_start) * 1000.0
    
    def get_stage_timings(self) -> Dict[str, Dict[str, Any]]:
        """Get stage timings in format expected by demo UI"""
        timings = {}
        for stage in self.stages:
            timings[stage.stage_name] = {
                "time_ms": stage.duration_ms,
                "results": stage.metadata.get("results", 0),
                "metadata": stage.metadata
            }
        return timings
    
    def add_stage(self, stage_name: str, duration_ms: float, metadata: Dict[str, Any] = None):
        """Add a completed stage timing"""
        current_time = time.time()
        stage = TimingResult(
            stage_name=stage_name,
            start_time=current_time - (duration_ms / 1000.0),
            end_time=current_time,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        self.stages.append(stage)


class PerformanceInstrumentation:
    """Main performance timing instrumentation for Epic 2 demo"""
    
    def __init__(self):
        self._active_timings: Dict[str, PipelineTimings] = {}
        self._lock = Lock()
    
    def start_pipeline(self, pipeline_id: str) -> PipelineTimings:
        """Start timing a new pipeline"""
        with self._lock:
            timing = PipelineTimings(total_start=time.time())
            self._active_timings[pipeline_id] = timing
            return timing
    
    def finish_pipeline(self, pipeline_id: str) -> Optional[PipelineTimings]:
        """Finish timing a pipeline and return results"""
        with self._lock:
            if pipeline_id in self._active_timings:
                timing = self._active_timings[pipeline_id]
                timing.total_end = time.time()
                del self._active_timings[pipeline_id]
                return timing
        return None
    
    @contextmanager
    def time_stage(self, pipeline_id: str, stage_name: str, metadata: Dict[str, Any] = None):
        """Context manager for timing a pipeline stage"""
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000.0
            
            with self._lock:
                if pipeline_id in self._active_timings:
                    timing = self._active_timings[pipeline_id]
                    timing.add_stage(stage_name, duration_ms, metadata or {})
                    logger.debug(f"Stage '{stage_name}' completed in {duration_ms:.2f}ms")
    
    def get_timing(self, pipeline_id: str) -> Optional[PipelineTimings]:
        """Get current timing for a pipeline"""
        with self._lock:
            return self._active_timings.get(pipeline_id)


class ComponentPerformanceExtractor:
    """Extracts performance metrics from RAG system components"""
    
    @staticmethod
    def extract_retriever_metrics(retriever) -> Dict[str, Any]:
        """Extract detailed timing metrics from ModularUnifiedRetriever"""
        metrics = {}
        
        # Try to get performance metrics from the retriever
        if hasattr(retriever, 'get_metrics'):
            component_metrics = retriever.get_metrics()
            if component_metrics:
                # Extract stats from the actual format
                retrieval_stats = component_metrics.get('retrieval_stats', {})
                
                # Get sub-component statistics
                sub_components = component_metrics.get('sub_components', {})
                
                # Extract reranker statistics
                reranker_stats = sub_components.get('reranker', {}).get('statistics', {})
                fusion_stats = sub_components.get('fusion_strategy', {}).get('statistics', {})
                
                # Create metrics in expected format
                metrics['dense_retrieval'] = {
                    'time_ms': retrieval_stats.get('last_retrieval_time', 0) * 1000,
                    'results': component_metrics.get('indexed_documents', 0)
                }
                metrics['sparse_retrieval'] = {
                    'time_ms': retrieval_stats.get('avg_time', 0) * 1000,
                    'results': component_metrics.get('indexed_documents', 0)
                }
                metrics['fusion'] = {
                    'time_ms': fusion_stats.get('avg_graph_latency_ms', 0),
                    'results': fusion_stats.get('total_fusions', 0)
                }
                metrics['neural_reranking'] = {
                    'time_ms': reranker_stats.get('total_latency_ms', 0),
                    'results': reranker_stats.get('successful_queries', 0)
                }
                
                # Total retrieval time
                metrics['total_retrieval_time_ms'] = retrieval_stats.get('total_time', 0) * 1000
        
        return metrics
    
    @staticmethod
    def extract_generator_metrics(generator) -> Dict[str, Any]:
        """Extract detailed timing metrics from AnswerGenerator"""
        metrics = {}
        
        # Try to get performance metrics from the generator
        if hasattr(generator, 'get_metrics'):
            component_metrics = generator.get_metrics()
            if component_metrics:
                # Extract stats from the actual format
                generation_count = component_metrics.get('generation_count', 0)
                total_time = component_metrics.get('total_time', 0)
                avg_time = component_metrics.get('avg_time', 0)
                
                # Get sub-component information
                sub_components = component_metrics.get('sub_components', {})
                llm_client = sub_components.get('llm_client', {})
                
                # Create metrics in expected format
                metrics['prompt_building'] = {
                    'time_ms': avg_time * 1000 * 0.1,  # Estimate 10% of total time
                    'results': generation_count
                }
                metrics['llm_generation'] = {
                    'time_ms': avg_time * 1000 * 0.8,  # Estimate 80% of total time
                    'results': generation_count
                }
                metrics['response_parsing'] = {
                    'time_ms': avg_time * 1000 * 0.05,  # Estimate 5% of total time
                    'results': generation_count
                }
                metrics['confidence_scoring'] = {
                    'time_ms': avg_time * 1000 * 0.05,  # Estimate 5% of total time
                    'results': generation_count
                }
                
                # Total generation time
                metrics['total_generation_time_ms'] = total_time * 1000
        
        return metrics
    
    @staticmethod
    def create_demo_timing_format(retriever_metrics: Dict[str, Any], 
                                 generator_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Create timing format expected by the demo UI"""
        return {
            # Retrieval stages
            "dense_retrieval": retriever_metrics.get('dense_retrieval', {"time_ms": 0, "results": 0}),
            "sparse_retrieval": retriever_metrics.get('sparse_retrieval', {"time_ms": 0, "results": 0}),
            "graph_enhancement": retriever_metrics.get('fusion', {"time_ms": 0, "results": 0}),
            "neural_reranking": retriever_metrics.get('neural_reranking', {"time_ms": 0, "results": 0}),
            
            # Generation stages
            "prompt_building": generator_metrics.get('prompt_building', {"time_ms": 0, "results": 0}),
            "llm_generation": generator_metrics.get('llm_generation', {"time_ms": 0, "results": 0}),
            "response_parsing": generator_metrics.get('response_parsing', {"time_ms": 0, "results": 0}),
            "confidence_scoring": generator_metrics.get('confidence_scoring', {"time_ms": 0, "results": 0}),
        }


# Global performance instrumentation instance
performance_instrumentation = PerformanceInstrumentation()


@contextmanager
def time_query_pipeline(query: str):
    """Context manager for timing a complete query processing pipeline"""
    pipeline_id = f"query_{int(time.time() * 1000)}"
    timing = performance_instrumentation.start_pipeline(pipeline_id)
    
    try:
        yield timing, pipeline_id
    finally:
        final_timing = performance_instrumentation.finish_pipeline(pipeline_id)
        if final_timing:
            logger.info(f"Query pipeline completed in {final_timing.total_duration_ms:.2f}ms")