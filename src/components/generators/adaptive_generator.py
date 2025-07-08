"""
Adaptive answer generator adapter for the modular RAG system.

This module provides an adapter that wraps the existing RAGWithGeneration
answer generation capabilities to conform to the AnswerGenerator interface,
enabling it to be used in the modular architecture.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import Document, Answer, AnswerGenerator

# Import generation components
from shared_utils.generation.hf_answer_generator import (
    HuggingFaceAnswerGenerator,
    GeneratedAnswer,
)
try:
    from shared_utils.generation.ollama_answer_generator import OllamaAnswerGenerator
    from shared_utils.generation.inference_providers_generator import (
        InferenceProvidersGenerator,
    )
    from shared_utils.generation.prompt_templates import TechnicalPromptTemplates
    from shared_utils.generation.adaptive_prompt_engine import AdaptivePromptEngine
    from shared_utils.generation.chain_of_thought_engine import ChainOfThoughtEngine
except ImportError as e:
    # Fallback for missing optional components
    logger.warning(f"Optional generation components not available: {e}")
    OllamaAnswerGenerator = None
    InferenceProvidersGenerator = None
    TechnicalPromptTemplates = None
    AdaptivePromptEngine = None
    ChainOfThoughtEngine = None


class AdaptiveAnswerGenerator(AnswerGenerator):
    """
    Adapter for existing adaptive answer generation system.
    
    This class wraps the advanced answer generation capabilities including
    adaptive prompts, chain-of-thought reasoning, and multiple LLM providers
    to provide an AnswerGenerator interface.
    
    Features:
    - Multiple LLM providers (HuggingFace, Ollama, Inference APIs)
    - Adaptive prompt optimization based on context quality
    - Chain-of-thought reasoning for complex queries
    - Technical documentation specialization
    - Confidence scoring and calibration
    - Streaming response support
    
    Example:
        generator = AdaptiveAnswerGenerator(
            model_name="sshleifer/distilbart-cnn-12-6",
            enable_adaptive_prompts=True,
            confidence_threshold=0.85
        )
        answer = generator.generate("What is RISC-V?", context_documents)
    """
    
    def __init__(
        self,
        model_name: str = "sshleifer/distilbart-cnn-12-6",
        api_token: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 512,
        use_ollama: bool = False,
        ollama_url: str = "http://localhost:11434",
        use_inference_providers: bool = False,
        enable_adaptive_prompts: bool = True,
        enable_chain_of_thought: bool = False,
        confidence_threshold: float = 0.85
    ):
        """
        Initialize the adaptive answer generator.
        
        Args:
            model_name: Model identifier for the LLM
            api_token: API token for HuggingFace (if needed)
            temperature: Sampling temperature for generation (default: 0.3)
            max_tokens: Maximum tokens to generate (default: 512)
            use_ollama: Use local Ollama server (default: False)
            ollama_url: URL for Ollama server (default: http://localhost:11434)
            use_inference_providers: Use inference API providers (default: False)
            enable_adaptive_prompts: Enable adaptive prompt optimization (default: True)
            enable_chain_of_thought: Enable chain-of-thought reasoning (default: False)
            confidence_threshold: Minimum confidence for answer acceptance (default: 0.85)
        """
        self.model_name = model_name
        self.api_token = api_token
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.use_ollama = use_ollama
        self.ollama_url = ollama_url
        self.use_inference_providers = use_inference_providers
        self.enable_adaptive_prompts = enable_adaptive_prompts
        self.enable_chain_of_thought = enable_chain_of_thought
        self.confidence_threshold = confidence_threshold
        
        # Initialize the appropriate generator
        self._initialize_generator()
        
        # Initialize prompt engines if enabled and available
        self.prompt_templates = TechnicalPromptTemplates() if TechnicalPromptTemplates else None
        self.adaptive_engine = None
        self.cot_engine = None
        
        if self.enable_adaptive_prompts and AdaptivePromptEngine:
            self.adaptive_engine = AdaptivePromptEngine()
        elif self.enable_adaptive_prompts:
            logger.warning("Adaptive prompts requested but AdaptivePromptEngine not available")
            self.enable_adaptive_prompts = False
        
        if self.enable_chain_of_thought and ChainOfThoughtEngine:
            self.cot_engine = ChainOfThoughtEngine()
        elif self.enable_chain_of_thought:
            logger.warning("Chain of thought requested but ChainOfThoughtEngine not available")
            self.enable_chain_of_thought = False
    
    def generate(self, query: str, context: List[Document]) -> Answer:
        """
        Generate an answer from query and context documents.
        
        This method uses adaptive prompting and multiple generation strategies
        to produce high-quality answers for technical documentation queries.
        
        Args:
            query: User query string
            context: List of relevant context documents
            
        Returns:
            Answer object with generated text, sources, confidence, and metadata
            
        Raises:
            ValueError: If query is empty or context is invalid
            RuntimeError: If answer generation fails
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        if not context:
            raise ValueError("Context documents cannot be empty")
        
        try:
            # Convert context documents to the format expected by generators
            context_chunks = self._documents_to_chunks(context)
            
            # Generate answer using adaptive prompts if enabled
            if self.enable_adaptive_prompts and self.adaptive_engine:
                response = self._generate_with_adaptive_prompts(query, context_chunks)
            else:
                response = self._generate_standard(query, context_chunks)
            
            # Extract answer information
            answer_text = self._extract_answer_text(response)
            confidence = self._extract_confidence(response)
            metadata = self._extract_metadata(response, query)
            
            return Answer(
                text=answer_text,
                sources=context,
                confidence=confidence,
                metadata=metadata
            )
            
        except Exception as e:
            raise RuntimeError(f"Answer generation failed: {str(e)}") from e
    
    def _initialize_generator(self) -> None:
        """Initialize the appropriate LLM generator based on configuration."""
        if self.use_ollama and OllamaAnswerGenerator:
            self.generator = OllamaAnswerGenerator(
                model_name=self.model_name,
                base_url=self.ollama_url,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        elif self.use_ollama:
            logger.warning("Ollama requested but OllamaAnswerGenerator not available, falling back to HuggingFace")
            self.use_ollama = False
            self._initialize_generator()
        elif self.use_inference_providers and InferenceProvidersGenerator:
            self.generator = InferenceProvidersGenerator(
                model_name=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        elif self.use_inference_providers:
            logger.warning("Inference providers requested but InferenceProvidersGenerator not available, falling back to HuggingFace")
            self.use_inference_providers = False
            self._initialize_generator()
        else:
            self.generator = HuggingFaceAnswerGenerator(
                model_name=self.model_name,
                api_token=self.api_token,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
    
    def _documents_to_chunks(self, documents: List[Document]) -> List[Dict]:
        """
        Convert Document objects to chunk format expected by generators.
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        for i, doc in enumerate(documents):
            chunk = {
                "text": doc.content,
                "chunk_id": i,
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("start_page", 1),
                **doc.metadata
            }
            chunks.append(chunk)
        return chunks
    
    def _generate_with_adaptive_prompts(self, query: str, chunks: List[Dict]) -> Dict:
        """
        Generate answer using adaptive prompts.
        
        Args:
            query: User query
            chunks: Context chunks
            
        Returns:
            Generation response dictionary
        """
        # Analyze context quality for adaptive prompting
        context_quality = self._analyze_context_quality(chunks)
        
        # Get adaptive prompt
        prompt_info = self.adaptive_engine.get_adaptive_prompt(
            query=query,
            context_chunks=chunks,
            quality_score=context_quality
        )
        
        # Generate with custom prompt
        if hasattr(self.generator, 'generate_with_custom_prompt'):
            response = self.generator.generate_with_custom_prompt(
                query=query,
                context_chunks=chunks,
                custom_prompt=prompt_info["prompt"]
            )
        else:
            # Fallback to standard generation
            response = self.generator.generate(query, chunks)
        
        # Add adaptive prompt metadata
        if isinstance(response, dict):
            response["adaptive_prompt_info"] = prompt_info
        
        return response
    
    def _generate_standard(self, query: str, chunks: List[Dict]) -> Dict:
        """
        Generate answer using standard prompts.
        
        Args:
            query: User query
            chunks: Context chunks
            
        Returns:
            Generation response dictionary
        """
        return self.generator.generate(query, chunks)
    
    def _analyze_context_quality(self, chunks: List[Dict]) -> float:
        """
        Analyze the quality of context chunks.
        
        Args:
            chunks: Context chunks to analyze
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not chunks:
            return 0.0
        
        # Simple quality analysis based on chunk metadata
        total_score = 0.0
        for chunk in chunks:
            score = chunk.get("quality_score", 0.8)  # Default score
            total_score += score
        
        return total_score / len(chunks)
    
    def _extract_answer_text(self, response: Dict) -> str:
        """Extract answer text from generation response."""
        if isinstance(response, GeneratedAnswer):
            return response.answer
        elif isinstance(response, dict):
            return response.get("answer", response.get("generated_text", ""))
        else:
            return str(response)
    
    def _extract_confidence(self, response: Dict) -> float:
        """Extract confidence score from generation response."""
        if isinstance(response, GeneratedAnswer):
            return response.confidence_score
        elif isinstance(response, dict):
            return response.get("confidence", 0.8)  # Default confidence
        else:
            return 0.8
    
    def _extract_metadata(self, response: Dict, query: str) -> Dict[str, Any]:
        """Extract metadata from generation response."""
        metadata = {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "provider": self._get_provider_name(),
            "adaptive_prompts_enabled": self.enable_adaptive_prompts,
            "chain_of_thought_enabled": self.enable_chain_of_thought,
            "query_length": len(query)
        }
        
        # Add response-specific metadata
        if isinstance(response, dict):
            # Add generation metadata
            metadata.update({
                k: v for k, v in response.items() 
                if k in ["generation_time", "token_count", "prompt_tokens", "completion_tokens"]
            })
            
            # Add adaptive prompt info if available
            if "adaptive_prompt_info" in response:
                metadata["adaptive_prompt_type"] = response["adaptive_prompt_info"].get("type", "unknown")
        
        return metadata
    
    def _get_provider_name(self) -> str:
        """Get the name of the current LLM provider."""
        if self.use_ollama:
            return "ollama"
        elif self.use_inference_providers:
            return "inference_providers"
        else:
            return "huggingface"
    
    def get_generator_info(self) -> Dict[str, Any]:
        """
        Get information about the current generator configuration.
        
        Returns:
            Dictionary with generator configuration and capabilities
        """
        return {
            "model_name": self.model_name,
            "provider": self._get_provider_name(),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "adaptive_prompts": self.enable_adaptive_prompts,
            "chain_of_thought": self.enable_chain_of_thought,
            "confidence_threshold": self.confidence_threshold,
            "capabilities": {
                "streaming": hasattr(self.generator, 'generate_answer_stream'),
                "custom_prompts": hasattr(self.generator, 'generate_with_custom_prompt'),
                "confidence_scoring": True,
                "technical_specialization": True
            }
        }
    
    def supports_streaming(self) -> bool:
        """Check if the generator supports streaming responses."""
        return hasattr(self.generator, 'generate_answer_stream')