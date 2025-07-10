"""
Modular Answer Generator Implementation.

This module implements the primary AnswerGenerator interface that
coordinates all answer generation sub-components (prompt building,
LLM interaction, response parsing, confidence scoring).

Architecture Notes:
- Implements AnswerGenerator interface from core.interfaces
- Coordinates sub-components for flexible generation
- Configuration-driven component selection
- Provides unified interface for answer generation
- Extensive use of adapters for LLM integration
"""

import time
import logging
from typing import List, Dict, Any, Optional, Iterator
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import AnswerGenerator as AnswerGeneratorInterface, Document, Answer
from .base import ConfigurableComponent, GenerationParams, GenerationError, Citation

# Import sub-component registries
from .prompt_builders import get_builder_class
from .llm_adapters import get_adapter_class
from .response_parsers import get_parser_class
from .confidence_scorers import get_scorer_class

logger = logging.getLogger(__name__)


class AnswerGenerator(AnswerGeneratorInterface, ConfigurableComponent):
    """
    Modular answer generator with configurable sub-components.
    
    This generator implements the AnswerGenerator interface while
    providing a modular architecture where prompt building, LLM selection,
    response parsing, and confidence scoring can be configured independently.
    
    Key Architecture Points:
    - ALL LLM clients use adapters (unlike Document Processor)
    - Direct implementations for algorithms (prompting, parsing, scoring)
    - Configuration-driven component selection
    - Supports both structured config and legacy parameters
    
    Features:
    - Multiple LLM provider support through adapters
    - Configurable prompt strategies
    - Flexible response parsing
    - Multi-method confidence scoring
    - Streaming support (when available)
    - Comprehensive error handling
    
    Configuration Structure:
    {
        "prompt_builder": {
            "type": "simple",
            "config": {...}
        },
        "llm_client": {
            "type": "ollama",
            "config": {...}
        },
        "response_parser": {
            "type": "markdown",
            "config": {...}
        },
        "confidence_scorer": {
            "type": "semantic",
            "config": {...}
        }
    }
    """
    
    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 # Legacy parameters for backward compatibility
                 model_name: Optional[str] = None,
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None,
                 use_ollama: Optional[bool] = None,
                 ollama_url: Optional[str] = None,
                 **kwargs):
        """
        Initialize the modular answer generator.
        
        Args:
            config: Configuration dictionary for all sub-components
            model_name: Legacy parameter for model name
            temperature: Legacy parameter for generation temperature
            max_tokens: Legacy parameter for max tokens
            use_ollama: Legacy parameter to use Ollama
            ollama_url: Legacy parameter for Ollama URL
            **kwargs: Additional legacy parameters
        """
        # Default configuration
        default_config = {
            'prompt_builder': {
                'type': 'simple',
                'config': {
                    'max_context_length': 4000,
                    'include_instructions': True,
                    'citation_style': 'inline'
                }
            },
            'llm_client': {
                'type': 'ollama',
                'config': {
                    'model_name': 'llama3.2',
                    'base_url': 'http://localhost:11434',
                    'timeout': 120
                }
            },
            'response_parser': {
                'type': 'markdown',
                'config': {
                    'extract_citations': True,
                    'preserve_formatting': True
                }
            },
            'confidence_scorer': {
                'type': 'semantic',
                'config': {
                    'relevance_weight': 0.4,
                    'grounding_weight': 0.4,
                    'quality_weight': 0.2
                }
            }
        }
        
        # Handle legacy parameters
        if model_name or temperature or max_tokens or use_ollama is not None:
            logger.info("Converting legacy parameters to new configuration format")
            
            if use_ollama is False:
                # If explicitly not using Ollama, we'd need other adapters
                # For now, default to Ollama anyway
                logger.warning("Non-Ollama providers not yet implemented, using Ollama")
            
            # Override LLM config with legacy parameters
            if not config:
                config = default_config.copy()
            
            if model_name:
                config.setdefault('llm_client', {}).setdefault('config', {})['model_name'] = model_name
            if temperature is not None:
                config.setdefault('llm_client', {}).setdefault('config', {})['temperature'] = temperature
            if max_tokens is not None:
                config.setdefault('llm_client', {}).setdefault('config', {})['max_tokens'] = max_tokens
            if ollama_url:
                config.setdefault('llm_client', {}).setdefault('config', {})['base_url'] = ollama_url
        
        # Merge with defaults
        self.config = self._merge_configs(default_config, config or {})
        
        # Initialize sub-components
        self._initialize_components()
        
        # Track metrics
        self._generation_count = 0
        self._total_time = 0.0
        
        logger.info(f"Initialized AnswerGenerator with components: "
                   f"prompt_builder={self.config['prompt_builder']['type']}, "
                   f"llm_client={self.config['llm_client']['type']}, "
                   f"response_parser={self.config['response_parser']['type']}, "
                   f"confidence_scorer={self.config['confidence_scorer']['type']}")
    
    def generate(self, query: str, context: List[Document]) -> Answer:
        """
        Generate an answer from query and context documents.
        
        This method orchestrates all sub-components to produce a high-quality
        answer with citations and confidence scoring.
        
        Args:
            query: User query string
            context: List of relevant context documents
            
        Returns:
            Answer object with generated text, sources, confidence, and metadata
            
        Raises:
            ValueError: If query is empty or context is invalid
            GenerationError: If answer generation fails
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        start_time = time.time()
        
        try:
            # Step 1: Build prompt
            logger.debug("Building prompt...")
            prompt = self.prompt_builder.build_prompt(query, context)
            
            # Step 2: Generate response
            logger.debug("Generating response...")
            generation_params = self._get_generation_params()
            raw_response = self.llm_client.generate(prompt, generation_params)
            
            # Step 3: Parse response
            logger.debug("Parsing response...")
            parsed_response = self.response_parser.parse(raw_response)
            answer_text = parsed_response.get('answer', raw_response)
            
            # Step 4: Extract citations
            citations = self.response_parser.extract_citations(parsed_response, context)
            
            # Step 5: Calculate confidence
            logger.debug("Calculating confidence...")
            confidence = self.confidence_scorer.score(query, answer_text, context)
            
            # Override with parsed confidence if available and higher
            if 'confidence' in parsed_response:
                confidence = max(confidence, parsed_response['confidence'])
            
            # Step 6: Build metadata
            elapsed_time = time.time() - start_time
            metadata = self._build_metadata(
                query, parsed_response, citations, elapsed_time
            )
            
            # Update metrics
            self._generation_count += 1
            self._total_time += elapsed_time
            
            logger.info(f"Generated answer in {elapsed_time:.2f}s with confidence {confidence:.3f}")
            
            return Answer(
                text=answer_text,
                sources=context,
                confidence=confidence,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Answer generation failed: {str(e)}")
            raise GenerationError(f"Failed to generate answer: {str(e)}") from e
    
    def get_component_info(self) -> Dict[str, Any]:
        """
        Get information about active sub-components.
        
        This method is used by ComponentFactory for enhanced logging.
        
        Returns:
            Dictionary with component information
        """
        return {
            'prompt_builder': {
                'type': self.config['prompt_builder']['type'],
                'class': self.prompt_builder.__class__.__name__,
                **self.prompt_builder.get_builder_info()
            },
            'llm_client': {
                'type': self.config['llm_client']['type'],
                'class': self.llm_client.__class__.__name__,
                **self.llm_client.get_model_info()
            },
            'response_parser': {
                'type': self.config['response_parser']['type'],
                'class': self.response_parser.__class__.__name__,
                **self.response_parser.get_parser_info()
            },
            'confidence_scorer': {
                'type': self.config['confidence_scorer']['type'],
                'class': self.confidence_scorer.__class__.__name__,
                **self.confidence_scorer.get_scorer_info()
            }
        }
    
    def get_generator_info(self) -> Dict[str, Any]:
        """
        Get information about the generator configuration.
        
        For compatibility with AdaptiveAnswerGenerator interface.
        
        Returns:
            Dictionary with generator configuration and capabilities
        """
        model_info = self.llm_client.get_model_info()
        
        return {
            'model_name': model_info.get('model', 'unknown'),
            'provider': model_info.get('provider', 'unknown'),
            'temperature': self._get_generation_params().temperature,
            'max_tokens': self._get_generation_params().max_tokens,
            'supports_streaming': model_info.get('supports_streaming', False),
            'components': {
                'prompt_builder': self.config['prompt_builder']['type'],
                'llm_client': self.config['llm_client']['type'],
                'response_parser': self.config['response_parser']['type'],
                'confidence_scorer': self.config['confidence_scorer']['type']
            },
            'metrics': {
                'generations': self._generation_count,
                'avg_time': self._total_time / max(1, self._generation_count)
            }
        }
    
    def validate_configuration(self) -> bool:
        """
        Validate the current configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate all components are properly initialized
        if not all([self.prompt_builder, self.llm_client, 
                   self.response_parser, self.confidence_scorer]):
            raise ValueError("Not all components are initialized")
        
        # Validate LLM connection
        try:
            if not self.llm_client.validate_connection():
                raise ValueError("LLM connection validation failed")
        except Exception as e:
            raise ValueError(f"LLM validation error: {str(e)}")
        
        return True
    
    def _initialize_components(self) -> None:
        """Initialize all sub-components based on configuration."""
        # Initialize prompt builder
        builder_type = self.config['prompt_builder']['type']
        builder_config = self.config['prompt_builder'].get('config', {})
        builder_class = get_builder_class(builder_type)
        self.prompt_builder = builder_class(**builder_config)
        
        # Initialize LLM adapter
        llm_type = self.config['llm_client']['type']
        llm_config = self.config['llm_client'].get('config', {})
        adapter_class = get_adapter_class(llm_type)
        self.llm_client = adapter_class(**llm_config)
        
        # Initialize response parser
        parser_type = self.config['response_parser']['type']
        parser_config = self.config['response_parser'].get('config', {})
        parser_class = get_parser_class(parser_type)
        self.response_parser = parser_class(**parser_config)
        
        # Initialize confidence scorer
        scorer_type = self.config['confidence_scorer']['type']
        scorer_config = self.config['confidence_scorer'].get('config', {})
        scorer_class = get_scorer_class(scorer_type)
        self.confidence_scorer = scorer_class(**scorer_config)
    
    def _get_generation_params(self) -> GenerationParams:
        """Get generation parameters from configuration."""
        llm_config = self.config['llm_client'].get('config', {})
        
        return GenerationParams(
            temperature=llm_config.get('temperature', 0.7),
            max_tokens=llm_config.get('max_tokens', 512),
            top_p=llm_config.get('top_p', 1.0),
            frequency_penalty=llm_config.get('frequency_penalty', 0.0),
            presence_penalty=llm_config.get('presence_penalty', 0.0),
            stop_sequences=llm_config.get('stop_sequences')
        )
    
    def _build_metadata(self, 
                       query: str,
                       parsed_response: Dict[str, Any],
                       citations: List[Citation],
                       elapsed_time: float) -> Dict[str, Any]:
        """Build metadata for the answer."""
        metadata = {
            'generator_type': 'modular',
            'generation_time': elapsed_time,
            'query_length': len(query),
            'citations_found': len(citations),
            'components_used': {
                'prompt_builder': self.config['prompt_builder']['type'],
                'llm_client': self.config['llm_client']['type'],
                'response_parser': self.config['response_parser']['type'],
                'confidence_scorer': self.config['confidence_scorer']['type']
            }
        }
        
        # Add parsed metadata
        if 'metadata' in parsed_response:
            metadata['parsed_metadata'] = parsed_response['metadata']
        
        # Add model info
        model_info = self.llm_client.get_model_info()
        metadata['model'] = model_info.get('model', 'unknown')
        metadata['provider'] = model_info.get('provider', 'unknown')
        
        return metadata
    
    def _merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge configuration dictionaries."""
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result