"""
Answer generation module using Ollama for local LLM inference.

This module provides answer generation with citation support for RAG systems,
optimized for technical documentation Q&A on Apple Silicon.
"""

import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Generator, Tuple
import ollama
from datetime import datetime
import re
from pathlib import Path
import sys

# Import calibration framework
try:
    # Try relative import first
    from ...project_1_technical_rag.src.confidence_calibration import ConfidenceCalibrator
except ImportError:
    # Fallback to absolute import
    project_root = Path(__file__).parent.parent.parent / "project-1-technical-rag"
    sys.path.insert(0, str(project_root / "src"))
    from confidence_calibration import ConfidenceCalibrator

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Represents a citation to a source document chunk."""
    chunk_id: str
    page_number: int
    source_file: str
    relevance_score: float
    text_snippet: str


@dataclass
class GeneratedAnswer:
    """Represents a generated answer with citations."""
    answer: str
    citations: List[Citation]
    confidence_score: float
    generation_time: float
    model_used: str
    context_used: List[Dict[str, Any]]


class AnswerGenerator:
    """
    Generates answers using local LLMs via Ollama with citation support.
    
    Optimized for technical documentation Q&A with:
    - Streaming response support
    - Citation extraction and formatting
    - Confidence scoring
    - Fallback model support
    """
    
    def __init__(
        self,
        primary_model: str = "llama3.2:3b",
        fallback_model: str = "mistral:latest",
        temperature: float = 0.3,
        max_tokens: int = 1024,
        stream: bool = True,
        enable_calibration: bool = True
    ):
        """
        Initialize the answer generator.
        
        Args:
            primary_model: Primary Ollama model to use
            fallback_model: Fallback model for complex queries
            temperature: Generation temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream responses
            enable_calibration: Whether to enable confidence calibration
        """
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.stream = stream
        self.client = ollama.Client()
        
        # Initialize confidence calibration
        self.enable_calibration = enable_calibration
        self.calibrator = None
        if enable_calibration:
            try:
                self.calibrator = ConfidenceCalibrator()
                logger.info("Confidence calibration enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize calibration: {e}")
                self.enable_calibration = False
        
        # Verify models are available
        self._verify_models()
        
    def _verify_models(self) -> None:
        """Verify that required models are available."""
        try:
            model_list = self.client.list()
            available_models = []
            
            # Handle Ollama's ListResponse object
            if hasattr(model_list, 'models'):
                for model in model_list.models:
                    if hasattr(model, 'model'):
                        available_models.append(model.model)
                    elif isinstance(model, dict) and 'model' in model:
                        available_models.append(model['model'])
            
            if self.primary_model not in available_models:
                logger.warning(f"Primary model {self.primary_model} not found. Available models: {available_models}")
                raise ValueError(f"Model {self.primary_model} not available. Please run: ollama pull {self.primary_model}")
                
            if self.fallback_model not in available_models:
                logger.warning(f"Fallback model {self.fallback_model} not found in: {available_models}")
                
        except Exception as e:
            logger.error(f"Error verifying models: {e}")
            raise
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for technical documentation Q&A."""
        return """You are a technical documentation assistant that provides clear, accurate answers based on the provided context.

CORE PRINCIPLES:
1. ANSWER DIRECTLY: If context contains the answer, provide it clearly and confidently
2. BE CONCISE: Keep responses focused and avoid unnecessary uncertainty language
3. CITE ACCURATELY: Use [chunk_X] citations for every fact from context

RESPONSE GUIDELINES:
- If context has sufficient information → Answer directly and confidently
- If context has partial information → Answer what's available, note what's missing briefly
- If context is irrelevant → Brief refusal: "This information isn't available in the provided documents"

CITATION FORMAT:
- Use [chunk_1], [chunk_2] etc. for all facts from context
- Example: "According to [chunk_1], RISC-V is an open-source architecture."

WHAT TO AVOID:
- Do NOT add details not in context
- Do NOT second-guess yourself if context is clear
- Do NOT use phrases like "does not contain sufficient information" when context clearly answers the question
- Do NOT be overly cautious when context is adequate

Be direct, confident, and accurate. If the context answers the question, provide that answer clearly."""

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format retrieved chunks into context for the LLM.
        
        Args:
            chunks: List of retrieved chunks with metadata
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            chunk_text = chunk.get('content', chunk.get('text', ''))
            page_num = chunk.get('metadata', {}).get('page_number', 'unknown')
            source = chunk.get('metadata', {}).get('source', 'unknown')
            
            context_parts.append(
                f"[chunk_{i+1}] (Page {page_num} from {source}):\n{chunk_text}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _extract_citations(self, answer: str, chunks: List[Dict[str, Any]]) -> Tuple[str, List[Citation]]:
        """
        Extract citations from the generated answer and integrate them naturally.
        
        Args:
            answer: Generated answer with [chunk_X] citations
            chunks: Original chunks used for context
            
        Returns:
            Tuple of (natural_answer, citations)
        """
        citations = []
        citation_pattern = r'\[chunk_(\d+)\]'
        
        cited_chunks = set()
        
        # Find [chunk_X] citations and collect cited chunks
        matches = re.finditer(citation_pattern, answer)
        for match in matches:
            chunk_idx = int(match.group(1)) - 1  # Convert to 0-based index
            if 0 <= chunk_idx < len(chunks):
                cited_chunks.add(chunk_idx)
        
        # Create Citation objects for each cited chunk
        chunk_to_source = {}
        for idx in cited_chunks:
            chunk = chunks[idx]
            citation = Citation(
                chunk_id=chunk.get('id', f'chunk_{idx}'),
                page_number=chunk.get('metadata', {}).get('page_number', 0),
                source_file=chunk.get('metadata', {}).get('source', 'unknown'),
                relevance_score=chunk.get('score', 0.0),
                text_snippet=chunk.get('content', chunk.get('text', ''))[:200] + '...'
            )
            citations.append(citation)
            
            # Map chunk reference to natural source name
            source_name = chunk.get('metadata', {}).get('source', 'unknown')
            if source_name != 'unknown':
                # Use just the filename without extension for natural reference
                natural_name = Path(source_name).stem.replace('-', ' ').replace('_', ' ')
                chunk_to_source[f'[chunk_{idx+1}]'] = f"the {natural_name} documentation"
            else:
                chunk_to_source[f'[chunk_{idx+1}]'] = "the documentation"
        
        # Replace [chunk_X] with natural references instead of removing them
        natural_answer = answer
        for chunk_ref, natural_ref in chunk_to_source.items():
            natural_answer = natural_answer.replace(chunk_ref, natural_ref)
        
        # Clean up any remaining unreferenced citations (fallback)
        natural_answer = re.sub(r'\[chunk_\d+\]', 'the documentation', natural_answer)
        
        # Clean up multiple spaces and formatting
        natural_answer = re.sub(r'\s+', ' ', natural_answer).strip()
        
        return natural_answer, citations
    
    def _calculate_confidence(self, answer: str, citations: List[Citation], chunks: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence score for the generated answer with improved calibration.
        
        Args:
            answer: Generated answer
            citations: Extracted citations
            chunks: Retrieved chunks
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Check if no chunks were provided first
        if not chunks:
            return 0.05  # No context = very low confidence
        
        # Assess context quality to determine base confidence
        scores = [chunk.get('score', 0) for chunk in chunks]
        max_relevance = max(scores) if scores else 0
        avg_relevance = sum(scores) / len(scores) if scores else 0
        
        # Dynamic base confidence based on context quality
        if max_relevance >= 0.8:
            confidence = 0.6  # High-quality context starts high
        elif max_relevance >= 0.6:
            confidence = 0.4  # Good context starts moderately
        elif max_relevance >= 0.4:
            confidence = 0.2  # Fair context starts low
        else:
            confidence = 0.05  # Poor context starts very low
        
        # Strong uncertainty and explicit refusal indicators
        strong_uncertainty_phrases = [
            "does not contain sufficient information",
            "context does not provide", 
            "insufficient information",
            "cannot determine",
            "refuse to answer",
            "cannot answer",
            "does not contain relevant",
            "no relevant context",
            "missing from the provided context"
        ]
        
        # Weak uncertainty phrases that might be in nuanced but correct answers
        weak_uncertainty_phrases = [
            "unclear",
            "conflicting",
            "not specified",
            "questionable", 
            "not contained",
            "no mention",
            "no relevant",
            "missing",
            "not explicitly"
        ]
        
        # Check for strong uncertainty - these should drastically reduce confidence
        if any(phrase in answer.lower() for phrase in strong_uncertainty_phrases):
            return min(0.1, confidence * 0.2)  # Max 10% for explicit refusal/uncertainty
        
        # Check for weak uncertainty - reduce but don't destroy confidence for good context
        weak_uncertainty_count = sum(1 for phrase in weak_uncertainty_phrases if phrase in answer.lower())
        if weak_uncertainty_count > 0:
            if max_relevance >= 0.7 and citations:
                # Good context with citations - reduce less severely
                confidence *= (0.8 ** weak_uncertainty_count)  # Moderate penalty
            else:
                # Poor context - reduce more severely  
                confidence *= (0.5 ** weak_uncertainty_count)  # Strong penalty
        
        # If all chunks have very low relevance scores, cap confidence low
        if max_relevance < 0.4:
            return min(0.08, confidence)  # Max 8% for low relevance context
        
        # Factor 1: Citation quality and coverage
        if citations and chunks:
            citation_ratio = len(citations) / min(len(chunks), 3)
            
            # Strong boost for high-relevance citations
            relevant_chunks = [c for c in chunks if c.get('score', 0) > 0.6]
            if relevant_chunks:
                # Significant boost for citing relevant chunks
                confidence += 0.25 * citation_ratio
                
                # Extra boost if citing majority of relevant chunks
                if len(citations) >= len(relevant_chunks) * 0.5:
                    confidence += 0.15
            else:
                # Small boost for citations to lower-relevance chunks
                confidence += 0.1 * citation_ratio
        else:
            # No citations = reduce confidence unless it's a simple factual statement
            if max_relevance >= 0.8 and len(answer.split()) < 20:
                confidence *= 0.8  # Gentle penalty for uncited but simple answers
            else:
                confidence *= 0.6  # Stronger penalty for complex uncited answers
        
        # Factor 2: Relevance score reinforcement
        if citations:
            avg_citation_relevance = sum(c.relevance_score for c in citations) / len(citations)
            if avg_citation_relevance > 0.8:
                confidence += 0.2  # Strong boost for highly relevant citations
            elif avg_citation_relevance > 0.6:
                confidence += 0.1  # Moderate boost
            elif avg_citation_relevance < 0.4:
                confidence *= 0.6  # Penalty for low-relevance citations
        
        # Factor 3: Context utilization quality
        if chunks:
            avg_chunk_length = sum(len(chunk.get('content', chunk.get('text', ''))) for chunk in chunks) / len(chunks)
            
            # Boost for substantial, high-quality context
            if avg_chunk_length > 200 and max_relevance > 0.8:
                confidence += 0.1
            elif avg_chunk_length < 50:  # Very short chunks
                confidence *= 0.8
        
        # Factor 4: Answer characteristics
        answer_words = len(answer.split())
        if answer_words < 10:
            confidence *= 0.9  # Slight penalty for very short answers
        elif answer_words > 50 and citations:
            confidence += 0.05  # Small boost for detailed cited answers
        
        # Factor 5: High-quality scenario bonus
        if (max_relevance >= 0.8 and citations and 
            len(citations) > 0 and 
            not any(phrase in answer.lower() for phrase in strong_uncertainty_phrases)):
            # This is a high-quality response scenario
            confidence += 0.15
        
        raw_confidence = min(confidence, 0.95)  # Cap at 95% to maintain some uncertainty
        
        # Apply temperature scaling calibration if available
        if self.enable_calibration and self.calibrator and self.calibrator.is_fitted:
            try:
                calibrated_confidence = self.calibrator.calibrate_confidence(raw_confidence)
                logger.debug(f"Confidence calibrated: {raw_confidence:.3f} -> {calibrated_confidence:.3f}")
                return calibrated_confidence
            except Exception as e:
                logger.warning(f"Calibration failed, using raw confidence: {e}")
                
        return raw_confidence
    
    def fit_calibration(self, validation_data: List[Dict[str, Any]]) -> float:
        """
        Fit temperature scaling calibration using validation data.
        
        Args:
            validation_data: List of dicts with 'confidence' and 'correctness' keys
            
        Returns:
            Optimal temperature parameter
        """
        if not self.enable_calibration or not self.calibrator:
            logger.warning("Calibration not enabled or not available")
            return 1.0
            
        try:
            confidences = [item['confidence'] for item in validation_data]
            correctness = [item['correctness'] for item in validation_data]
            
            optimal_temp = self.calibrator.fit_temperature_scaling(confidences, correctness)
            logger.info(f"Calibration fitted with temperature: {optimal_temp:.3f}")
            return optimal_temp
            
        except Exception as e:
            logger.error(f"Failed to fit calibration: {e}")
            return 1.0
    
    def save_calibration(self, filepath: str) -> bool:
        """Save fitted calibration to file."""
        if not self.calibrator or not self.calibrator.is_fitted:
            logger.warning("No fitted calibration to save")
            return False
            
        try:
            calibration_data = {
                'temperature': self.calibrator.temperature,
                'is_fitted': self.calibrator.is_fitted,
                'model_info': {
                    'primary_model': self.primary_model,
                    'fallback_model': self.fallback_model
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(calibration_data, f, indent=2)
            
            logger.info(f"Calibration saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save calibration: {e}")
            return False
    
    def load_calibration(self, filepath: str) -> bool:
        """Load fitted calibration from file."""
        if not self.enable_calibration or not self.calibrator:
            logger.warning("Calibration not enabled")
            return False
            
        try:
            with open(filepath, 'r') as f:
                calibration_data = json.load(f)
            
            self.calibrator.temperature = calibration_data['temperature']
            self.calibrator.is_fitted = calibration_data['is_fitted']
            
            logger.info(f"Calibration loaded from {filepath} (temp: {self.calibrator.temperature:.3f})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load calibration: {e}")
            return False
    
    def generate(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        use_fallback: bool = False
    ) -> GeneratedAnswer:
        """
        Generate an answer based on the query and retrieved chunks.
        
        Args:
            query: User's question
            chunks: Retrieved document chunks
            use_fallback: Whether to use fallback model
            
        Returns:
            GeneratedAnswer object with answer, citations, and metadata
        """
        start_time = datetime.now()
        model = self.fallback_model if use_fallback else self.primary_model
        
        # Check for no-context or very poor context situation
        if not chunks or all(len(chunk.get('content', chunk.get('text', ''))) < 20 for chunk in chunks):
            # Handle no-context situation with brief, professional refusal
            user_prompt = f"""Context: [NO RELEVANT CONTEXT FOUND]

Question: {query}

INSTRUCTION: Respond with exactly this brief message:

"This information isn't available in the provided documents."

DO NOT elaborate, explain, or add any other information."""
        else:
            # Format context from chunks
            context = self._format_context(chunks)
            
            # Create concise prompt for faster generation
            user_prompt = f"""Context:
{context}

Question: {query}

Instructions: Answer using only the context above. Cite with [chunk_1], [chunk_2] etc.

Answer:"""
        
        try:
            # Generate response
            response = self.client.chat(
                model=model,
                messages=[
                    {"role": "system", "content": self._create_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": self.temperature,
                    "num_predict": min(self.max_tokens, 300),  # Reduce max tokens for speed
                    "top_k": 40,  # Optimize sampling for speed
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                },
                stream=False  # Get complete response for processing
            )
            
            # Extract answer
            answer_with_citations = response['message']['content']
            
            # Extract and clean citations
            clean_answer, citations = self._extract_citations(answer_with_citations, chunks)
            
            # Calculate confidence
            confidence = self._calculate_confidence(clean_answer, citations, chunks)
            
            # Calculate generation time
            generation_time = (datetime.now() - start_time).total_seconds()
            
            return GeneratedAnswer(
                answer=clean_answer,
                citations=citations,
                confidence_score=confidence,
                generation_time=generation_time,
                model_used=model,
                context_used=chunks
            )
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            # Return a fallback response
            return GeneratedAnswer(
                answer="I apologize, but I encountered an error while generating the answer. Please try again.",
                citations=[],
                confidence_score=0.0,
                generation_time=0.0,
                model_used=model,
                context_used=chunks
            )
    
    def generate_stream(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        use_fallback: bool = False
    ) -> Generator[str, None, GeneratedAnswer]:
        """
        Generate an answer with streaming support.
        
        Args:
            query: User's question
            chunks: Retrieved document chunks
            use_fallback: Whether to use fallback model
            
        Yields:
            Partial answer strings
            
        Returns:
            Final GeneratedAnswer object
        """
        start_time = datetime.now()
        model = self.fallback_model if use_fallback else self.primary_model
        
        # Check for no-context or very poor context situation
        if not chunks or all(len(chunk.get('content', chunk.get('text', ''))) < 20 for chunk in chunks):
            # Handle no-context situation with brief, professional refusal
            user_prompt = f"""Context: [NO RELEVANT CONTEXT FOUND]

Question: {query}

INSTRUCTION: Respond with exactly this brief message:

"This information isn't available in the provided documents."

DO NOT elaborate, explain, or add any other information."""
        else:
            # Format context from chunks
            context = self._format_context(chunks)
            
            # Create concise prompt for faster generation
            user_prompt = f"""Context:
{context}

Question: {query}

Instructions: Answer using only the context above. Cite with [chunk_1], [chunk_2] etc.

Answer:"""
        
        try:
            # Generate streaming response
            stream = self.client.chat(
                model=model,
                messages=[
                    {"role": "system", "content": self._create_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": self.temperature,
                    "num_predict": min(self.max_tokens, 300),  # Reduce max tokens for speed
                    "top_k": 40,  # Optimize sampling for speed
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                },
                stream=True
            )
            
            # Collect full answer while streaming
            full_answer = ""
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    partial = chunk['message']['content']
                    full_answer += partial
                    yield partial
            
            # Process complete answer
            clean_answer, citations = self._extract_citations(full_answer, chunks)
            confidence = self._calculate_confidence(clean_answer, citations, chunks)
            generation_time = (datetime.now() - start_time).total_seconds()
            
            return GeneratedAnswer(
                answer=clean_answer,
                citations=citations,
                confidence_score=confidence,
                generation_time=generation_time,
                model_used=model,
                context_used=chunks
            )
            
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            yield "I apologize, but I encountered an error while generating the answer."
            
            return GeneratedAnswer(
                answer="Error occurred during generation.",
                citations=[],
                confidence_score=0.0,
                generation_time=0.0,
                model_used=model,
                context_used=chunks
            )
    
    def format_answer_with_citations(self, generated_answer: GeneratedAnswer) -> str:
        """
        Format the generated answer with citations for display.
        
        Args:
            generated_answer: GeneratedAnswer object
            
        Returns:
            Formatted string with answer and citations
        """
        formatted = f"{generated_answer.answer}\n\n"
        
        if generated_answer.citations:
            formatted += "**Sources:**\n"
            for i, citation in enumerate(generated_answer.citations, 1):
                formatted += f"{i}. {citation.source_file} (Page {citation.page_number})\n"
        
        formatted += f"\n*Confidence: {generated_answer.confidence_score:.1%} | "
        formatted += f"Model: {generated_answer.model_used} | "
        formatted += f"Time: {generated_answer.generation_time:.2f}s*"
        
        return formatted


if __name__ == "__main__":
    # Example usage
    generator = AnswerGenerator()
    
    # Example chunks (would come from retrieval system)
    example_chunks = [
        {
            "id": "chunk_1",
            "content": "RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles.",
            "metadata": {"page_number": 1, "source": "riscv-spec.pdf"},
            "score": 0.95
        },
        {
            "id": "chunk_2", 
            "content": "The RISC-V ISA is designed to support a wide range of implementations including 32-bit, 64-bit, and 128-bit variants.",
            "metadata": {"page_number": 2, "source": "riscv-spec.pdf"},
            "score": 0.89
        }
    ]
    
    # Generate answer
    result = generator.generate(
        query="What is RISC-V?",
        chunks=example_chunks
    )
    
    # Display formatted result
    print(generator.format_answer_with_citations(result))