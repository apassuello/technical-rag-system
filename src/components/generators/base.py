"""
Abstract base classes for Answer Generator sub-components.

This module defines the interfaces that all answer generation sub-components
must implement, ensuring consistency across different implementations.

Architecture Notes:
- All sub-components follow a consistent interface pattern
- LLM adapters convert between unified interface and provider-specific formats
- Direct implementations handle algorithms without external dependencies
- Configuration is passed through dictionaries for flexibility
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass
from enum import Enum

from src.core.interfaces import Document, Answer


class GenerationError(Exception):
    """Base exception for generation-related errors."""
    pass


class LLMError(GenerationError):
    """Errors from LLM providers."""
    pass


class ParsingError(GenerationError):
    """Errors during response parsing."""
    pass


class PromptBuilderType(Enum):
    """Types of prompt builders available."""
    SIMPLE = "simple"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    FEW_SHOT = "few_shot"


class ResponseFormat(Enum):
    """Expected response formats."""
    MARKDOWN = "markdown"
    JSON = "json"
    PLAIN_TEXT = "plain_text"


@dataclass
class GenerationParams:
    """Parameters for LLM generation."""
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls."""
        return {
            k: v for k, v in self.__dict__.items() 
            if v is not None
        }


@dataclass
class Citation:
    """Represents a citation in the generated answer."""
    source_id: str
    text: str
    start_pos: int
    end_pos: int
    confidence: float = 1.0


class PromptBuilder(ABC):
    """
    Abstract base class for prompt builders.
    
    Prompt builders create prompts from queries and context documents
    using various strategies (simple, chain-of-thought, few-shot, etc.).
    
    All implementations should be direct (no adapters) as they implement
    pure prompt construction algorithms without external dependencies.
    """
    
    @abstractmethod
    def build_prompt(self, query: str, context: List[Document]) -> str:
        """
        Build a prompt from query and context documents.
        
        Args:
            query: User query string
            context: List of relevant context documents
            
        Returns:
            Formatted prompt string ready for LLM
            
        Raises:
            ValueError: If query is empty or context is invalid
        """
        pass
    
    @abstractmethod
    def get_template(self) -> str:
        """
        Return the prompt template being used.
        
        Returns:
            Template string with placeholders
        """
        pass
    
    @abstractmethod
    def get_builder_info(self) -> Dict[str, Any]:
        """
        Get information about the prompt builder.
        
        Returns:
            Dictionary with builder type and configuration
        """
        pass


class LLMAdapter(ABC):
    """
    Abstract base class for LLM adapters.
    
    LLM adapters provide a unified interface to different language model
    providers (Ollama, OpenAI, HuggingFace, etc.). Each adapter handles:
    - API authentication and connection
    - Request format conversion
    - Response format conversion
    - Error mapping and handling
    
    ALL LLM integrations must use adapters due to vastly different APIs.
    """
    
    @abstractmethod
    def generate(self, prompt: str, params: GenerationParams) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            params: Generation parameters
            
        Returns:
            Generated text response
            
        Raises:
            LLMError: If generation fails
        """
        pass
    
    @abstractmethod
    def generate_streaming(self, prompt: str, params: GenerationParams) -> Iterator[str]:
        """
        Generate a streaming response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            params: Generation parameters
            
        Yields:
            Generated text chunks
            
        Raises:
            LLMError: If generation fails
            NotImplementedError: If streaming not supported
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model and provider.
        
        Returns:
            Dictionary with model name, provider, capabilities
        """
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Validate the connection to the LLM provider.
        
        Returns:
            True if connection is valid
            
        Raises:
            LLMError: If connection validation fails
        """
        pass


class ResponseParser(ABC):
    """
    Abstract base class for response parsers.
    
    Response parsers extract structured information from LLM responses,
    including citations, formatting, and metadata.
    
    All implementations should be direct (no adapters) as they implement
    pure text parsing algorithms without external dependencies.
    """
    
    @abstractmethod
    def parse(self, raw_response: str) -> Dict[str, Any]:
        """
        Parse the raw LLM response into structured format.
        
        Args:
            raw_response: Raw text from LLM
            
        Returns:
            Structured dictionary with parsed content
            
        Raises:
            ParsingError: If parsing fails
        """
        pass
    
    @abstractmethod
    def extract_citations(self, response: Dict[str, Any], context: List[Document]) -> List[Citation]:
        """
        Extract citations from the parsed response.
        
        Args:
            response: Parsed response dictionary
            context: Original context documents
            
        Returns:
            List of extracted citations
        """
        pass
    
    @abstractmethod
    def get_parser_info(self) -> Dict[str, Any]:
        """
        Get information about the parser.
        
        Returns:
            Dictionary with parser type and capabilities
        """
        pass


class ConfidenceScorer(ABC):
    """
    Abstract base class for confidence scorers.
    
    Confidence scorers evaluate the quality and reliability of generated
    answers using various metrics (perplexity, semantic coherence, etc.).
    
    All implementations should be direct (no adapters) as they implement
    pure scoring algorithms without external dependencies.
    """
    
    @abstractmethod
    def score(self, query: str, answer: str, context: List[Document]) -> float:
        """
        Calculate confidence score for the generated answer.
        
        Args:
            query: Original query
            answer: Generated answer text
            context: Context documents used
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        pass
    
    @abstractmethod
    def get_scoring_method(self) -> str:
        """
        Return the name of the scoring method.
        
        Returns:
            Method name (e.g., "perplexity", "semantic", "ensemble")
        """
        pass
    
    @abstractmethod
    def get_scorer_info(self) -> Dict[str, Any]:
        """
        Get information about the scorer.
        
        Returns:
            Dictionary with scorer type and configuration
        """
        pass


class ConfigurableComponent(ABC):
    """
    Base class for components that support configuration.
    
    Provides common configuration handling for all sub-components.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize with optional configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        self.config.update(updates)