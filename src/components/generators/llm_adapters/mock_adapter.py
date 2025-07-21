"""
Mock LLM adapter for testing without external dependencies.

This adapter provides deterministic responses for testing purposes,
eliminating the need for Ollama or other external LLM services.

Architecture Notes:
- Provides consistent test responses with proper citation format
- Supports all required adapter interface methods
- Returns predictable outputs for reliable testing
- No external dependencies or network calls
"""

import logging
from typing import Dict, Any, Optional, Iterator
import random

from .base_adapter import BaseLLMAdapter, LLMError
from ..base import GenerationParams

logger = logging.getLogger(__name__)


class MockLLMAdapter(BaseLLMAdapter):
    """
    Mock adapter for testing without external LLM dependencies.
    
    Features:
    - Deterministic responses for testing
    - Proper citation formatting
    - Configurable response patterns
    - No external dependencies
    - Fast response times
    
    Configuration:
    - response_pattern: Type of response to generate (default: "technical")
    - include_citations: Whether to include citations (default: True)
    - simulate_errors: Whether to simulate errors (default: False)
    - fixed_response: Use a fixed response instead of patterns (optional)
    """
    
    # Predefined response patterns for different test scenarios
    RESPONSE_PATTERNS = {
        "technical": {
            "template": "Based on the technical documentation, {topic} is {description}. The implementation details show that {detail} [Document {doc_num}].",
            "descriptions": [
                "a key component of the system architecture",
                "an important feature for performance optimization",
                "designed for scalability and reliability",
                "implemented using industry best practices"
            ],
            "details": [
                "it uses advanced algorithms for efficient processing",
                "the modular design allows for easy extension",
                "performance benchmarks show significant improvements",
                "the architecture supports both local and distributed deployment"
            ]
        },
        "simple": {
            "template": "{topic} refers to {description} [Document {doc_num}].",
            "descriptions": [
                "a fundamental concept",
                "an essential component",
                "a critical feature",
                "an important aspect"
            ],
            "details": []
        },
        "detailed": {
            "template": "The query about {topic} can be answered as follows:\n\n{description}\n\nKey points include:\n1. {point1} [Document {doc1}]\n2. {point2} [Document {doc2}]\n3. {point3} [Document {doc3}]\n\nIn conclusion, {conclusion} [Document {doc4}].",
            "descriptions": [
                "This is a comprehensive topic that requires detailed explanation",
                "This involves multiple interconnected components",
                "This represents a complex system with various considerations"
            ],
            "points": [
                "The architecture is designed for modularity",
                "Performance optimization is a key consideration",
                "The system supports various configuration options",
                "Integration with external services is supported",
                "Error handling is comprehensive and robust"
            ],
            "conclusions": [
                "the implementation provides a solid foundation",
                "the system meets all specified requirements",
                "the design ensures future scalability"
            ]
        }
    }
    
    def __init__(self,
                 model_name: str = "mock-model",
                 response_pattern: str = "technical",
                 include_citations: bool = True,
                 simulate_errors: bool = False,
                 fixed_response: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize mock adapter.
        
        Args:
            model_name: Mock model name for identification
            response_pattern: Type of response pattern to use
            include_citations: Whether to include document citations
            simulate_errors: Whether to simulate random errors
            fixed_response: Use this fixed response if provided
            config: Additional configuration
        """
        adapter_config = {
            'response_pattern': response_pattern,
            'include_citations': include_citations,
            'simulate_errors': simulate_errors,
            'fixed_response': fixed_response,
            **(config or {})
        }
        
        super().__init__(model_name, adapter_config)
        
        self.response_pattern = adapter_config['response_pattern']
        self.include_citations = adapter_config['include_citations']
        self.simulate_errors = adapter_config['simulate_errors']
        self.fixed_response = adapter_config.get('fixed_response')
        
        logger.info(f"Initialized Mock adapter with pattern '{response_pattern}'")
    
    def _make_request(self, prompt: str, params: GenerationParams) -> Dict[str, Any]:
        """
        Generate a mock response without external calls.
        
        Args:
            prompt: The prompt to respond to
            params: Generation parameters (mostly ignored for mock)
            
        Returns:
            Mock response in expected format
        """
        # Simulate errors if configured
        if self.simulate_errors and random.random() < 0.1:
            raise LLMError("Simulated mock error for testing")
        
        # Generate response text
        if self.fixed_response:
            response_text = self.fixed_response
        else:
            response_text = self._generate_response(prompt, params)
        
        # Build mock response structure
        response = {
            "model": self.model_name,
            "response": response_text,
            "done": True,
            "context": [],
            "total_duration": 1000000,  # 1ms in nanoseconds
            "load_duration": 0,
            "prompt_eval_count": len(prompt.split()),
            "prompt_eval_duration": 500000,
            "eval_count": len(response_text.split()),
            "eval_duration": 500000
        }
        
        return response
    
    def _parse_response(self, response: Dict[str, Any]) -> str:
        """
        Extract text from mock response.
        
        Args:
            response: Mock response dict
            
        Returns:
            Response text
        """
        return response.get("response", "")
    
    def _get_provider_name(self) -> str:
        """Return the provider name."""
        return "Mock"
    
    def _validate_model(self) -> bool:
        """Mock models are always valid."""
        return True
    
    def _supports_streaming(self) -> bool:
        """Mock adapter can simulate streaming."""
        return True
    
    def generate_streaming(self, prompt: str, params: GenerationParams) -> Iterator[str]:
        """
        Generate a mock streaming response.
        
        Args:
            prompt: The prompt to respond to
            params: Generation parameters
            
        Yields:
            Response chunks
        """
        # Get full response
        full_response = self._generate_response(prompt, params)
        
        # Simulate streaming by yielding word by word
        words = full_response.split()
        for i, word in enumerate(words):
            if i < len(words) - 1:
                yield word + " "
            else:
                yield word
    
    def _generate_response(self, prompt: str, params: GenerationParams) -> str:
        """
        Generate a response based on the configured pattern.
        
        Args:
            prompt: The user's prompt
            params: Generation parameters
            
        Returns:
            Generated response text
        """
        # Extract topic from prompt (simple heuristic)
        prompt_lower = prompt.lower()
        topic = "the requested information"
        
        # Try to extract a more specific topic
        if "risc-v" in prompt_lower:
            topic = "RISC-V"
        elif "pipeline" in prompt_lower:
            topic = "pipeline architecture"
        elif "memory" in prompt_lower:
            topic = "memory management"
        elif "what is" in prompt_lower:
            # Extract what comes after "what is"
            parts = prompt_lower.split("what is")
            if len(parts) > 1:
                topic = parts[1].strip().rstrip("?").strip()
        
        # Get pattern configuration
        pattern_config = self.RESPONSE_PATTERNS.get(
            self.response_pattern, 
            self.RESPONSE_PATTERNS["technical"]
        )
        
        # Generate response based on pattern
        if self.response_pattern == "simple":
            description = random.choice(pattern_config["descriptions"])
            response = pattern_config["template"].format(
                topic=topic,
                description=description,
                doc_num=random.randint(1, 5) if self.include_citations else ""
            )
            
        elif self.response_pattern == "detailed":
            description = random.choice(pattern_config["descriptions"])
            points = random.sample(pattern_config["points"], 3)
            conclusion = random.choice(pattern_config["conclusions"])
            
            response = pattern_config["template"].format(
                topic=topic,
                description=description,
                point1=points[0],
                point2=points[1],
                point3=points[2],
                conclusion=conclusion,
                doc1=1 if self.include_citations else "",
                doc2=2 if self.include_citations else "",
                doc3=3 if self.include_citations else "",
                doc4=4 if self.include_citations else ""
            )
            
        else:  # technical (default)
            description = random.choice(pattern_config["descriptions"])
            detail = random.choice(pattern_config["details"])
            response = pattern_config["template"].format(
                topic=topic,
                description=description,
                detail=detail,
                doc_num=random.randint(1, 5) if self.include_citations else ""
            )
        
        # Remove citation markers if not including citations
        if not self.include_citations:
            response = response.replace(" [Document ]", "").replace(" []", "")
        
        return response
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get mock model information.
        
        Returns:
            Model info dict
        """
        info = super().get_model_info()
        info.update({
            'is_mock': True,
            'response_pattern': self.response_pattern,
            'include_citations': self.include_citations,
            'simulate_errors': self.simulate_errors
        })
        return info