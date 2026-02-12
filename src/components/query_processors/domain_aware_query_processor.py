"""
Domain-Aware Query Processor for Epic 1 Phase 1

This module extends the ModularQueryProcessor with domain relevance filtering
to create a domain-aware query processing pipeline.

The enhanced workflow:
1. Domain Relevance Analysis (NEW) - Filter for RISC-V relevance
2. Early Exit Decision (NEW) - Handle out-of-scope queries
3. Query Analysis - Continue with Epic1MLAnalyzer if relevant
4. Document Retrieval - Use optimized parameters
5. Context Selection - Choose optimal documents
6. Answer Generation - Generate response
7. Response Assembly - Format with domain metadata

Integration with Epic 1:
- Maintains all existing ModularQueryProcessor functionality
- Adds domain filtering as optional pre-processing step
- Provides clear routing decisions and user feedback
- Follows established Epic 1 architectural patterns
"""

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import (
    Answer,
    AnswerGenerator,
    QueryOptions,
    Retriever,
)

from .base import QueryAnalysis, QueryProcessorConfig
from .domain_relevance_filter import DomainRelevanceFilter
from .modular_query_processor import ModularQueryProcessor

logger = logging.getLogger(__name__)


class DomainAwareQueryProcessor(ModularQueryProcessor):
    """
    Domain-aware query processor extending ModularQueryProcessor with
    RISC-V domain relevance filtering.
    
    This processor adds domain filtering as the first step in query processing:
    - High relevance queries (0.8-1.0): Full RISC-V specialized processing
    - Medium relevance queries (0.3-0.7): Conservative processing with general models
    - Low relevance queries (0.0-0.2): Early exit with clear explanations
    
    The processor maintains full backward compatibility with ModularQueryProcessor
    while adding sophisticated domain awareness for cost optimization and
    improved user experience.
    """
    
    def __init__(
        self,
        retriever: Retriever,
        generator: AnswerGenerator,
        analyzer: Optional = None,
        selector: Optional = None,
        assembler: Optional = None,
        config: Optional[Union[Dict[str, Any], QueryProcessorConfig]] = None,
        enable_domain_filtering: bool = True
    ):
        """
        Initialize domain-aware query processor.
        
        Args:
            retriever: Document retriever component
            generator: Answer generator component
            analyzer: Query analyzer (uses Epic1MLAnalyzer if None)
            selector: Context selector (uses MMRSelector if None)
            assembler: Response assembler (uses RichAssembler if None)
            config: Configuration for query processor and domain filter
            enable_domain_filtering: Whether to enable domain relevance filtering
        """
        # Initialize parent ModularQueryProcessor
        super().__init__(retriever, generator, analyzer, selector, assembler, config)
        
        # Domain filtering configuration
        self.enable_domain_filtering = enable_domain_filtering
        self.domain_filter = None
        
        if self.enable_domain_filtering:
            # Extract domain filter config
            domain_config = {}
            if isinstance(config, dict):
                domain_config = config.get('domain_filter', {})
            elif hasattr(config, 'domain_filter'):
                domain_config = getattr(config, 'domain_filter', {})
            
            self.domain_filter = DomainRelevanceFilter(domain_config)
            logger.info("Domain relevance filtering enabled")
        else:
            logger.info("Domain relevance filtering disabled")
        
        # Performance tracking
        self.domain_analysis_time = 0.0
        self.early_exits = 0
        self.processed_queries = 0
    
    def process_query(
        self, 
        query: str, 
        options: Optional[QueryOptions] = None
    ) -> Answer:
        """
        Process query with domain-aware filtering.
        
        Args:
            query: User query string
            options: Optional query processing options
            
        Returns:
            Answer with response and metadata
        """
        start_time = time.time()
        total_phase_times = {'total': 0.0}
        
        try:
            # Phase 0: Domain Relevance Analysis (NEW)
            domain_result = None
            if self.enable_domain_filtering and self.domain_filter:
                phase_start = time.time()
                domain_result = self.domain_filter.analyze_domain_relevance(query)
                total_phase_times['domain_analysis'] = time.time() - phase_start
                self.domain_analysis_time += total_phase_times['domain_analysis']
                
                # Early exit for low relevance queries
                if not domain_result.is_relevant:
                    self.early_exits += 1
                    refusal_answer = self.domain_filter.create_refusal_response(domain_result)
                    
                    # Add timing metadata
                    refusal_answer.metadata.update({
                        'total_processing_time': time.time() - start_time,
                        'phase_times': total_phase_times,
                        'early_exit_reason': 'low_domain_relevance'
                    })
                    
                    logger.info(f"Early exit for low relevance query: "
                               f"score={domain_result.relevance_score:.3f}")
                    return refusal_answer
            
            # Continue with normal ModularQueryProcessor workflow
            self.processed_queries += 1
            answer = super().process(query, options)
            
            # Enhance answer metadata with domain information
            if domain_result:
                answer.metadata.update({
                    'domain_relevance_score': domain_result.relevance_score,
                    'domain_relevance_tier': domain_result.relevance_tier,
                    'domain_reasoning': domain_result.reasoning,
                    'domain_confidence': domain_result.confidence,
                    'domain_analysis_time_ms': domain_result.processing_time_ms
                })
            
            # Update total timing
            total_phase_times['total'] = time.time() - start_time
            if 'phase_times' in answer.metadata:
                answer.metadata['phase_times'].update(total_phase_times)
            else:
                answer.metadata['phase_times'] = total_phase_times
            
            return answer
            
        except Exception as e:
            logger.error(f"Domain-aware query processing failed: {e}")
            
            # Fallback to parent implementation
            return super().process(query, options)
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze query with optional domain enhancement.
        
        Args:
            query: User query string
            
        Returns:
            QueryAnalysis with domain relevance metadata
        """
        # Get domain analysis if enabled
        domain_result = None
        if self.enable_domain_filtering and self.domain_filter:
            domain_result = self.domain_filter.analyze_domain_relevance(query)
        
        # Get standard query analysis
        analysis = super().analyze_query(query)
        
        # Enhance with domain information
        if domain_result:
            analysis.metadata.update({
                'domain_relevance_score': domain_result.relevance_score,
                'domain_relevance_tier': domain_result.relevance_tier,
                'domain_reasoning': domain_result.reasoning,
                'domain_confidence': domain_result.confidence,
                'domain_is_relevant': domain_result.is_relevant
            })
        
        return analysis
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics including domain filtering.
        
        Returns:
            Dictionary with performance statistics
        """
        # Get base metrics from parent
        base_metrics = super().get_performance_metrics()
        
        # Add domain filtering metrics
        domain_metrics = {
            'domain_filtering_enabled': self.enable_domain_filtering,
            'total_domain_analysis_time': self.domain_analysis_time,
            'early_exits': self.early_exits,
            'processed_queries': self.processed_queries,
            'early_exit_rate': self.early_exits / max(self.early_exits + self.processed_queries, 1),
            'avg_domain_analysis_time': self.domain_analysis_time / max(self.early_exits + self.processed_queries, 1)
        }
        
        # Add domain filter stats if available
        if self.domain_filter:
            domain_metrics.update({
                'domain_filter_stats': self.domain_filter.get_performance_stats()
            })
        
        # Combine metrics
        base_metrics.update(domain_metrics)
        return base_metrics
    
    def get_component_info(self) -> Dict[str, Any]:
        """
        Get information about all components including domain filter.
        
        Returns:
            Dictionary with component information
        """
        # Get base component info
        base_info = super().get_component_info()
        
        # Add domain filter info
        if self.domain_filter:
            base_info['domain_filter'] = {
                'type': 'DomainRelevanceFilter',
                'enabled': self.enable_domain_filtering,
                'high_threshold': getattr(self.domain_filter, 'high_threshold', 0.8),
                'medium_threshold': getattr(self.domain_filter, 'medium_threshold', 0.3)
            }
        else:
            base_info['domain_filter'] = {
                'type': None,
                'enabled': False
            }
        
        return base_info
    
    def configure_domain_filter(self, config: Dict[str, Any]) -> None:
        """
        Configure domain filter settings.
        
        Args:
            config: Domain filter configuration
        """
        if self.domain_filter:
            self.domain_filter.config.update(config)
            self.domain_filter.high_threshold = config.get('high_threshold', 0.8)
            self.domain_filter.medium_threshold = config.get('medium_threshold', 0.3)
            logger.info(f"Domain filter reconfigured: {config}")
        else:
            logger.warning("Cannot configure domain filter - filtering is disabled")
    
    def enable_domain_filtering_runtime(self, domain_config: Optional[Dict[str, Any]] = None) -> None:
        """
        Enable domain filtering at runtime.
        
        Args:
            domain_config: Optional domain filter configuration
        """
        if not self.enable_domain_filtering:
            self.enable_domain_filtering = True
            self.domain_filter = DomainRelevanceFilter(domain_config or {})
            logger.info("Domain filtering enabled at runtime")
        else:
            logger.info("Domain filtering already enabled")
    
    def disable_domain_filtering_runtime(self) -> None:
        """Disable domain filtering at runtime."""
        if self.enable_domain_filtering:
            self.enable_domain_filtering = False
            self.domain_filter = None
            logger.info("Domain filtering disabled at runtime")
        else:
            logger.info("Domain filtering already disabled")