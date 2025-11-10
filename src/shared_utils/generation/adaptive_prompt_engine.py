"""
Adaptive Prompt Engine for Dynamic Context-Aware Prompt Optimization.

This module provides intelligent prompt adaptation based on context quality,
query complexity, and performance requirements.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

from .prompt_templates import (
    QueryType, 
    PromptTemplate, 
    TechnicalPromptTemplates
)


class ContextQuality(Enum):
    """Context quality levels for adaptive prompting."""
    HIGH = "high"      # >0.8 relevance, low noise
    MEDIUM = "medium"  # 0.5-0.8 relevance, moderate noise
    LOW = "low"        # <0.5 relevance, high noise


class QueryComplexity(Enum):
    """Query complexity levels."""
    SIMPLE = "simple"      # Single concept, direct answer
    MODERATE = "moderate"  # Multiple concepts, structured answer
    COMPLEX = "complex"    # Multi-step reasoning, comprehensive answer


@dataclass
class ContextMetrics:
    """Metrics for evaluating context quality."""
    relevance_score: float
    noise_ratio: float
    chunk_count: int
    avg_chunk_length: int
    technical_density: float
    source_diversity: int


@dataclass
class AdaptivePromptConfig:
    """Configuration for adaptive prompt generation."""
    context_quality: ContextQuality
    query_complexity: QueryComplexity
    max_context_length: int
    prefer_concise: bool
    include_few_shot: bool
    enable_chain_of_thought: bool
    confidence_threshold: float


class AdaptivePromptEngine:
    """
    Intelligent prompt adaptation engine that optimizes prompts based on:
    - Context quality and relevance
    - Query complexity and type
    - Performance requirements
    - User preferences
    """
    
    def __init__(self):
        """Initialize the adaptive prompt engine."""
        self.logger = logging.getLogger(__name__)
        
        # Context quality thresholds
        self.high_quality_threshold = 0.8
        self.medium_quality_threshold = 0.5
        
        # Query complexity indicators
        self.complex_keywords = {
            "implementation": ["implement", "build", "create", "develop", "setup"],
            "comparison": ["compare", "difference", "versus", "vs", "better"],
            "analysis": ["analyze", "evaluate", "assess", "study", "examine"],
            "multi_step": ["process", "procedure", "steps", "how to", "guide"]
        }
        
        # Length optimization thresholds
        self.token_limits = {
            "concise": 512,
            "standard": 1024,
            "detailed": 2048,
            "comprehensive": 4096
        }
    
    def analyze_context_quality(self, chunks: List[Dict[str, Any]]) -> ContextMetrics:
        """
        Analyze the quality of retrieved context chunks.
        
        Args:
            chunks: List of context chunks with metadata
            
        Returns:
            ContextMetrics with quality assessment
        """
        if not chunks:
            return ContextMetrics(
                relevance_score=0.0,
                noise_ratio=1.0,
                chunk_count=0,
                avg_chunk_length=0,
                technical_density=0.0,
                source_diversity=0
            )
        
        # Calculate relevance score (using confidence scores if available)
        relevance_scores = []
        for chunk in chunks:
            # Use confidence score if available, otherwise use a heuristic
            if 'confidence' in chunk:
                relevance_scores.append(chunk['confidence'])
            elif 'score' in chunk:
                relevance_scores.append(chunk['score'])
            else:
                # Heuristic: longer chunks with technical terms are more relevant
                content = chunk.get('content', chunk.get('text', ''))
                tech_terms = self._count_technical_terms(content)
                relevance_scores.append(min(tech_terms / 10.0, 1.0))
        
        avg_relevance = np.mean(relevance_scores) if relevance_scores else 0.0
        
        # Calculate noise ratio (fragments, repetitive content)
        noise_count = 0
        total_chunks = len(chunks)
        
        for chunk in chunks:
            content = chunk.get('content', chunk.get('text', ''))
            if self._is_noisy_chunk(content):
                noise_count += 1
        
        noise_ratio = noise_count / total_chunks if total_chunks > 0 else 0.0
        
        # Calculate average chunk length
        chunk_lengths = []
        for chunk in chunks:
            content = chunk.get('content', chunk.get('text', ''))
            chunk_lengths.append(len(content))
        
        avg_chunk_length = int(np.mean(chunk_lengths)) if chunk_lengths else 0
        
        # Calculate technical density
        technical_density = self._calculate_technical_density(chunks)
        
        # Calculate source diversity
        sources = set()
        for chunk in chunks:
            source = chunk.get('metadata', {}).get('source', 'unknown')
            sources.add(source)
        
        source_diversity = len(sources)
        
        return ContextMetrics(
            relevance_score=avg_relevance,
            noise_ratio=noise_ratio,
            chunk_count=len(chunks),
            avg_chunk_length=avg_chunk_length,
            technical_density=technical_density,
            source_diversity=source_diversity
        )
    
    def determine_query_complexity(self, query: str) -> QueryComplexity:
        """
        Determine the complexity level of a query.
        
        Args:
            query: User's question
            
        Returns:
            QueryComplexity level
        """
        query_lower = query.lower()
        complexity_score = 0
        
        # Check for complex keywords
        for category, keywords in self.complex_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                complexity_score += 1
        
        # Check for multiple questions or concepts
        if '?' in query[:-1]:  # Multiple question marks (excluding the last one)
            complexity_score += 1
        
        if any(word in query_lower for word in ["and", "or", "also", "additionally", "furthermore"]):
            complexity_score += 1
        
        # Check query length
        word_count = len(query.split())
        if word_count > 20:
            complexity_score += 1
        elif word_count > 10:
            complexity_score += 0.5
        
        # Determine complexity level
        if complexity_score >= 2:
            return QueryComplexity.COMPLEX
        elif complexity_score >= 1:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE
    
    def generate_adaptive_config(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        max_tokens: int = 2048,
        prefer_speed: bool = False
    ) -> AdaptivePromptConfig:
        """
        Generate adaptive prompt configuration based on context and query analysis.
        
        Args:
            query: User's question
            context_chunks: Retrieved context chunks
            max_tokens: Maximum token limit
            prefer_speed: Whether to optimize for speed over quality
            
        Returns:
            AdaptivePromptConfig with optimized settings
        """
        # Analyze context quality
        context_metrics = self.analyze_context_quality(context_chunks)
        
        # Determine context quality level
        if context_metrics.relevance_score >= self.high_quality_threshold:
            context_quality = ContextQuality.HIGH
        elif context_metrics.relevance_score >= self.medium_quality_threshold:
            context_quality = ContextQuality.MEDIUM
        else:
            context_quality = ContextQuality.LOW
        
        # Determine query complexity
        query_complexity = self.determine_query_complexity(query)
        
        # Adapt configuration based on analysis
        config = AdaptivePromptConfig(
            context_quality=context_quality,
            query_complexity=query_complexity,
            max_context_length=max_tokens,
            prefer_concise=prefer_speed,
            include_few_shot=self._should_include_few_shot(context_quality, query_complexity),
            enable_chain_of_thought=self._should_enable_cot(query_complexity),
            confidence_threshold=self._get_confidence_threshold(context_quality)
        )
        
        return config
    
    def create_adaptive_prompt(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        config: Optional[AdaptivePromptConfig] = None
    ) -> Dict[str, str]:
        """
        Create an adaptive prompt optimized for the specific query and context.
        
        Args:
            query: User's question
            context_chunks: Retrieved context chunks
            config: Optional configuration (auto-generated if None)
            
        Returns:
            Dict with optimized 'system' and 'user' prompts
        """
        if config is None:
            config = self.generate_adaptive_config(query, context_chunks)
        
        # Get base template
        query_type = TechnicalPromptTemplates.detect_query_type(query)
        base_template = TechnicalPromptTemplates.get_template_for_query(query)
        
        # Adapt template based on configuration
        adapted_template = self._adapt_template(base_template, config)
        
        # Format context with optimization
        formatted_context = self._format_context_adaptive(context_chunks, config)
        
        # Create prompt with adaptive formatting
        prompt = TechnicalPromptTemplates.format_prompt_with_template(
            query=query,
            context=formatted_context,
            template=adapted_template,
            include_few_shot=config.include_few_shot
        )
        
        # Add chain-of-thought if enabled
        if config.enable_chain_of_thought:
            prompt = self._add_chain_of_thought(prompt, query_type)
        
        return prompt
    
    def _adapt_template(
        self,
        base_template: PromptTemplate,
        config: AdaptivePromptConfig
    ) -> PromptTemplate:
        """
        Adapt a base template based on configuration.
        
        Args:
            base_template: Base prompt template
            config: Adaptive configuration
            
        Returns:
            Adapted PromptTemplate
        """
        # Modify system prompt based on context quality
        system_prompt = base_template.system_prompt
        
        if config.context_quality == ContextQuality.LOW:
            system_prompt += """
            
IMPORTANT: The provided context may have limited relevance. Focus on:
- Only use information that directly relates to the question
- Clearly state if information is insufficient
- Avoid making assumptions beyond the provided context
- Be explicit about confidence levels"""
            
        elif config.context_quality == ContextQuality.HIGH:
            system_prompt += """
            
CONTEXT QUALITY: High-quality, relevant context is provided. You can:
- Provide comprehensive, detailed answers
- Make reasonable inferences from the context
- Include related technical details and examples
- Reference multiple sources confidently"""
        
        # Modify answer guidelines based on complexity and preferences
        answer_guidelines = base_template.answer_guidelines
        
        if config.prefer_concise:
            answer_guidelines += "\n\nResponse style: Be concise and focus on essential information. Aim for clarity over comprehensiveness."
        
        if config.query_complexity == QueryComplexity.COMPLEX:
            answer_guidelines += "\n\nComplex query handling: Break down your answer into clear sections. Use numbered steps for procedures."
        
        return PromptTemplate(
            system_prompt=system_prompt,
            context_format=base_template.context_format,
            query_format=base_template.query_format,
            answer_guidelines=answer_guidelines,
            few_shot_examples=base_template.few_shot_examples
        )
    
    def _format_context_adaptive(
        self,
        chunks: List[Dict[str, Any]],
        config: AdaptivePromptConfig
    ) -> str:
        """
        Format context chunks with adaptive optimization.
        
        Args:
            chunks: Context chunks to format
            config: Adaptive configuration
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant context available."
        
        # Filter chunks based on confidence if low quality context
        filtered_chunks = chunks
        if config.context_quality == ContextQuality.LOW:
            filtered_chunks = [
                chunk for chunk in chunks
                if self._meets_confidence_threshold(chunk, config.confidence_threshold)
            ]
        
        # Limit context length if needed
        if config.prefer_concise:
            filtered_chunks = filtered_chunks[:3]  # Limit to top 3 chunks
        
        # Format chunks
        context_parts = []
        for i, chunk in enumerate(filtered_chunks):
            chunk_text = chunk.get('content', chunk.get('text', ''))
            
            # Truncate if too long and prefer_concise is True
            if config.prefer_concise and len(chunk_text) > 800:
                chunk_text = chunk_text[:800] + "..."
            
            metadata = chunk.get('metadata', {})
            page_num = metadata.get('page_number', 'unknown')
            source = metadata.get('source', 'unknown')
            
            context_parts.append(
                f"[chunk_{i+1}] (Page {page_num} from {source}):\n{chunk_text}"
            )
        
        return "\n\n---\n\n".join(context_parts)
    
    def _add_chain_of_thought(
        self,
        prompt: Dict[str, str],
        query_type: QueryType
    ) -> Dict[str, str]:
        """
        Add chain-of-thought reasoning to the prompt.
        
        Args:
            prompt: Base prompt dictionary
            query_type: Type of query
            
        Returns:
            Enhanced prompt with chain-of-thought
        """
        cot_addition = """

Before providing your final answer, think through this step-by-step:

1. What is the user specifically asking for?
2. What relevant information is available in the context?
3. How should I structure my response for maximum clarity?
4. Are there any important caveats or limitations to mention?

Step-by-step reasoning:"""
        
        prompt["user"] = prompt["user"] + cot_addition
        
        return prompt
    
    def _should_include_few_shot(
        self,
        context_quality: ContextQuality,
        query_complexity: QueryComplexity
    ) -> bool:
        """Determine if few-shot examples should be included."""
        # Include few-shot for complex queries or when context quality is low
        if query_complexity == QueryComplexity.COMPLEX:
            return True
        if context_quality == ContextQuality.LOW:
            return True
        return False
    
    def _should_enable_cot(self, query_complexity: QueryComplexity) -> bool:
        """Determine if chain-of-thought should be enabled."""
        return query_complexity == QueryComplexity.COMPLEX
    
    def _get_confidence_threshold(self, context_quality: ContextQuality) -> float:
        """Get confidence threshold based on context quality."""
        thresholds = {
            ContextQuality.HIGH: 0.3,
            ContextQuality.MEDIUM: 0.5,
            ContextQuality.LOW: 0.7
        }
        return thresholds[context_quality]
    
    def _count_technical_terms(self, text: str) -> int:
        """Count technical terms in text."""
        technical_terms = [
            "risc-v", "riscv", "cpu", "gpu", "mcu", "interrupt", "register",
            "memory", "cache", "pipeline", "instruction", "assembly", "compiler",
            "embedded", "freertos", "rtos", "gpio", "uart", "spi", "i2c",
            "adc", "dac", "timer", "pwm", "dma", "firmware", "bootloader",
            "ai", "ml", "neural", "transformer", "attention", "embedding"
        ]
        
        text_lower = text.lower()
        count = 0
        for term in technical_terms:
            count += text_lower.count(term)
        
        return count
    
    def _is_noisy_chunk(self, content: str) -> bool:
        """Determine if a chunk is noisy (low quality)."""
        # Check for common noise indicators
        noise_indicators = [
            "table of contents",
            "copyright",
            "creative commons",
            "license",
            "all rights reserved",
            "terms of use",
            "privacy policy"
        ]
        
        content_lower = content.lower()
        
        # Check for noise indicators
        for indicator in noise_indicators:
            if indicator in content_lower:
                return True
        
        # Check for very short fragments
        if len(content) < 100:
            return True
        
        # Check for repetitive content
        words = content.split()
        if len(set(words)) < len(words) * 0.3:  # Less than 30% unique words
            return True
        
        return False
    
    def _calculate_technical_density(self, chunks: List[Dict[str, Any]]) -> float:
        """Calculate technical density of chunks."""
        if not chunks:
            return 0.0
        
        total_terms = 0
        total_words = 0
        
        for chunk in chunks:
            content = chunk.get('content', chunk.get('text', ''))
            words = content.split()
            total_words += len(words)
            total_terms += self._count_technical_terms(content)
        
        return (total_terms / total_words) if total_words > 0 else 0.0
    
    def _meets_confidence_threshold(
        self,
        chunk: Dict[str, Any],
        threshold: float
    ) -> bool:
        """Check if chunk meets confidence threshold."""
        confidence = chunk.get('confidence', chunk.get('score', 0.5))
        return confidence >= threshold


# Example usage
if __name__ == "__main__":
    # Initialize engine
    engine = AdaptivePromptEngine()
    
    # Example context chunks
    example_chunks = [
        {
            "content": "RISC-V is an open-source instruction set architecture...",
            "metadata": {"page_number": 1, "source": "riscv-spec.pdf"},
            "confidence": 0.9
        },
        {
            "content": "The RISC-V processor supports 32-bit and 64-bit implementations...",
            "metadata": {"page_number": 2, "source": "riscv-spec.pdf"},
            "confidence": 0.8
        }
    ]
    
    # Example queries
    simple_query = "What is RISC-V?"
    complex_query = "How do I implement a complete interrupt handling system in RISC-V with nested interrupts and priority management?"
    
    # Generate adaptive prompts
    simple_config = engine.generate_adaptive_config(simple_query, example_chunks)
    complex_config = engine.generate_adaptive_config(complex_query, example_chunks)
    
    print(f"Simple query complexity: {simple_config.query_complexity}")
    print(f"Complex query complexity: {complex_config.query_complexity}")
    print(f"Context quality: {simple_config.context_quality}")
    print(f"Few-shot enabled: {complex_config.include_few_shot}")
    print(f"Chain-of-thought enabled: {complex_config.enable_chain_of_thought}")