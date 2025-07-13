"""
Base interfaces and abstract classes for Query Processor components.

This module defines the core interfaces that all Query Processor sub-components
must implement, following the established architecture patterns from other components.

Key Design Principles:
- Abstract base classes define clear contracts
- Minimal required methods for flexibility
- Configuration-driven component selection
- Consistent error handling and metrics
- Type hints for better IDE support
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import Document, Answer, QueryOptions


@dataclass 
class QueryAnalysis:
    """Results from query analysis containing query characteristics."""
    
    query: str
    complexity_score: float = 0.0
    technical_terms: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    intent_category: str = "general"
    suggested_k: int = 5
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextSelection:
    """Results from context selection containing selected documents."""
    
    selected_documents: List[Document]
    total_tokens: int = 0
    selection_strategy: str = "unknown"
    diversity_score: float = 0.0
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryProcessorConfig:
    """Configuration for Query Processor and its sub-components."""
    
    # Query Analyzer configuration
    analyzer_type: str = "nlp"
    analyzer_config: Dict[str, Any] = field(default_factory=dict)
    
    # Context Selector configuration  
    selector_type: str = "mmr"
    selector_config: Dict[str, Any] = field(default_factory=dict)
    
    # Response Assembler configuration
    assembler_type: str = "rich"
    assembler_config: Dict[str, Any] = field(default_factory=dict)
    
    # Workflow configuration
    default_k: int = 5
    max_tokens: int = 2048
    enable_fallback: bool = True
    timeout_seconds: float = 30.0


class QueryAnalyzer(ABC):
    """
    Abstract base class for query analysis components.
    
    Query analyzers examine user queries to extract characteristics that
    can optimize the retrieval and generation process.
    """
    
    @abstractmethod
    def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyze a query and return its characteristics.
        
        Args:
            query: User query string
            
        Returns:
            QueryAnalysis with extracted characteristics
            
        Raises:
            ValueError: If query is empty or invalid
            RuntimeError: If analysis fails
        """
        pass
    
    @abstractmethod
    def get_supported_features(self) -> List[str]:
        """
        Return list of analysis features this analyzer supports.
        
        Returns:
            List of feature names (e.g., ["entities", "complexity", "intent"])
        """
        pass
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the analyzer with provided settings.
        
        Args:
            config: Configuration dictionary
        """
        pass


class ContextSelector(ABC):
    """
    Abstract base class for context selection components.
    
    Context selectors choose optimal documents from retrieval results
    to maximize answer quality within token constraints.
    """
    
    @abstractmethod
    def select(
        self, 
        query: str,
        documents: List[Document], 
        max_tokens: int,
        query_analysis: Optional[QueryAnalysis] = None
    ) -> ContextSelection:
        """
        Select optimal context documents for answer generation.
        
        Args:
            query: Original user query
            documents: Retrieved documents to select from
            max_tokens: Maximum token limit for selected context
            query_analysis: Optional query analysis for optimization
            
        Returns:
            ContextSelection with selected documents and metadata
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If selection fails
        """
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        pass
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the selector with provided settings.
        
        Args:
            config: Configuration dictionary
        """
        pass


class ResponseAssembler(ABC):
    """
    Abstract base class for response assembly components.
    
    Response assemblers format the final Answer object with consistent
    structure, citations, and metadata.
    """
    
    @abstractmethod
    def assemble(
        self,
        query: str,
        answer_text: str, 
        context: ContextSelection,
        confidence: float,
        query_analysis: Optional[QueryAnalysis] = None,
        generation_metadata: Optional[Dict[str, Any]] = None
    ) -> Answer:
        """
        Assemble final Answer object with proper formatting.
        
        Args:
            query: Original user query
            answer_text: Generated answer text
            context: Selected context from ContextSelector
            confidence: Answer confidence score
            query_analysis: Optional query analysis metadata
            generation_metadata: Optional metadata from answer generation
            
        Returns:
            Complete Answer object with sources and metadata
            
        Raises:
            ValueError: If required parameters are missing
            RuntimeError: If assembly fails
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Return list of output formats this assembler supports.
        
        Returns:
            List of format names (e.g., ["standard", "rich", "streaming"])
        """
        pass
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the assembler with provided settings.
        
        Args:
            config: Configuration dictionary
        """
        pass


class QueryProcessor(ABC):
    """
    Abstract base class for the main Query Processor component.
    
    The Query Processor orchestrates the complete query workflow:
    analyze → retrieve → select → generate → assemble.
    """
    
    @abstractmethod
    def process(self, query: str, options: Optional[QueryOptions] = None) -> Answer:
        """
        Process a query end-to-end and return a complete answer.
        
        Args:
            query: User query string
            options: Optional query processing options
            
        Returns:
            Complete Answer object with text, sources, and metadata
            
        Raises:
            ValueError: If query is empty or options are invalid
            RuntimeError: If processing pipeline fails
        """
        pass
    
    @abstractmethod
    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze query characteristics without full processing.
        
        Args:
            query: User query string
            
        Returns:
            QueryAnalysis with extracted characteristics
        """
        pass
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of query processor and sub-components.
        
        Returns:
            Dictionary with health information
        """
        pass
    
    def configure(self, config: QueryProcessorConfig) -> None:
        """
        Configure the query processor and all sub-components.
        
        Args:
            config: Complete configuration object
        """
        pass


# Configuration validation utilities
def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate query processor configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Check required fields
    required_fields = ['analyzer_type', 'selector_type', 'assembler_type']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate known types
    valid_analyzers = ['nlp', 'rule_based', 'llm']
    if config.get('analyzer_type') not in valid_analyzers:
        errors.append(f"Unknown analyzer_type. Valid options: {valid_analyzers}")
    
    valid_selectors = ['mmr', 'diversity', 'token_limit']
    if config.get('selector_type') not in valid_selectors:
        errors.append(f"Unknown selector_type. Valid options: {valid_selectors}")
    
    valid_assemblers = ['standard', 'rich', 'streaming']
    if config.get('assembler_type') not in valid_assemblers:
        errors.append(f"Unknown assembler_type. Valid options: {valid_assemblers}")
    
    # Validate numeric ranges
    if 'default_k' in config and (config['default_k'] < 1 or config['default_k'] > 50):
        errors.append("default_k must be between 1 and 50")
    
    if 'max_tokens' in config and (config['max_tokens'] < 100 or config['max_tokens'] > 8192):
        errors.append("max_tokens must be between 100 and 8192")
    
    return errors


# Performance tracking utilities
class QueryProcessorMetrics:
    """Utility class for tracking query processor performance metrics."""
    
    def __init__(self):
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0
        self.average_latency = 0.0
        self.phase_latencies = {
            'analysis': 0.0,
            'retrieval': 0.0, 
            'selection': 0.0,
            'generation': 0.0,
            'assembly': 0.0
        }
    
    def record_query(self, success: bool, latency: float, phase_times: Dict[str, float]):
        """Record metrics for a completed query."""
        self.total_queries += 1
        if success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1
        
        # Update average latency
        self.average_latency = (
            (self.average_latency * (self.total_queries - 1) + latency) / self.total_queries
        )
        
        # Update phase latencies
        for phase, time_taken in phase_times.items():
            if phase in self.phase_latencies:
                current_avg = self.phase_latencies[phase]
                self.phase_latencies[phase] = (
                    (current_avg * (self.total_queries - 1) + time_taken) / self.total_queries
                )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        success_rate = self.successful_queries / self.total_queries if self.total_queries > 0 else 0.0
        
        return {
            'total_queries': self.total_queries,
            'success_rate': success_rate,
            'average_latency_ms': self.average_latency * 1000,
            'phase_latencies_ms': {k: v * 1000 for k, v in self.phase_latencies.items()},
            'failed_queries': self.failed_queries
        }