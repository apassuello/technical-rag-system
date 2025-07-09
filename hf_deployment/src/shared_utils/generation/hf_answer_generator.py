"""
HuggingFace API-based answer generation for deployment environments.

This module provides answer generation using HuggingFace's Inference API,
optimized for cloud deployment where local LLMs aren't feasible.
"""

import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Generator, Tuple
from datetime import datetime
import re
from pathlib import Path
import requests
import os
import sys

# Import technical prompt templates
from .prompt_templates import TechnicalPromptTemplates

# Import standard interfaces for adapter pattern
try:
    from src.core.interfaces import Document, Answer, AnswerGenerator
except ImportError:
    # Fallback if interfaces not available
    Document = None
    Answer = None
    AnswerGenerator = object

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


class HuggingFaceAnswerGenerator(AnswerGenerator if AnswerGenerator != object else object):
    """
    Generates answers using HuggingFace Inference API with hybrid reliability.
    
    🎯 HYBRID APPROACH - Best of Both Worlds:
    - Primary: High-quality open models (Zephyr-7B, Mistral-7B-Instruct)
    - Fallback: Reliable classics (DialoGPT-medium)
    - Foundation: HF GPT's proven Docker + auth setup
    - Pro Benefits: Better rate limits, priority processing
    
    Optimized for deployment environments with:
    - Fast API-based inference
    - No local model requirements
    - Citation extraction and formatting
    - Confidence scoring
    - Automatic fallback for reliability
    """
    
    def __init__(
        self,
        model_name: str = "sshleifer/distilbart-cnn-12-6",
        api_token: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 512
    ):
        """
        Initialize the HuggingFace answer generator.
        
        Args:
            model_name: HuggingFace model to use
            api_token: HF API token (optional, uses free tier if None)
            temperature: Generation temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
        """
        self.model_name = model_name
        # Try multiple common token environment variable names
        self.api_token = (api_token or 
                         os.getenv("HUGGINGFACE_API_TOKEN") or 
                         os.getenv("HF_TOKEN") or 
                         os.getenv("HF_API_TOKEN"))
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Hybrid approach: Classic API + fallback models
        self.api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        
        # Prepare headers
        self.headers = {"Content-Type": "application/json"}
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"
            logger.info("Using authenticated HuggingFace API")
        else:
            logger.info("Using free HuggingFace API (rate limited)")
            
        # Only include models that actually work based on tests
        self.fallback_models = [
            "deepset/roberta-base-squad2",      # Q&A model - perfect for RAG
            "sshleifer/distilbart-cnn-12-6",   # Summarization - also good
            "facebook/bart-base",               # Base BART - works but needs right format
        ]
    
    def _call_api_with_model(self, prompt: str, model_name: str) -> str:
        """Call API with a specific model (for fallback support)."""
        fallback_url = f"https://api-inference.huggingface.co/models/{model_name}"
        
        # SIMPLIFIED payload that works
        payload = {"inputs": prompt}
        
        response = requests.post(
            fallback_url,
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Handle response
        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], dict):
                return result[0].get("generated_text", "").strip()
            else:
                return str(result[0]).strip()
        elif isinstance(result, dict):
            return result.get("generated_text", "").strip()
        else:
            return str(result).strip()
    
    def _create_system_prompt(self) -> str:
        """Create system prompt optimized for the model type."""
        if "squad" in self.model_name.lower() or "roberta" in self.model_name.lower():
            # RoBERTa Squad2 uses question/context format - no system prompt needed
            return ""
        elif "gpt2" in self.model_name.lower() or "distilgpt2" in self.model_name.lower():
            # GPT-2 style completion prompt - simpler is better
            return "Based on the following context, answer the question.\n\nContext: "
        elif "llama" in self.model_name.lower():
            # Llama-2 chat format
            return """<s>[INST] You are a helpful technical documentation assistant. Answer the user's question based only on the provided context. Always cite sources using [chunk_X] format.

Context:"""
        elif "flan" in self.model_name.lower() or "t5" in self.model_name.lower():
            # Flan-T5 instruction format - simple and direct
            return """Answer the question based on the context below. Cite sources using [chunk_X] format.

Context: """
        elif "falcon" in self.model_name.lower():
            # Falcon instruction format
            return """### Instruction: Answer based on the context and cite sources with [chunk_X].

### Context: """
        elif "bart" in self.model_name.lower():
            # BART summarization format
            return """Summarize the answer to the question from the context. Use [chunk_X] for citations.

Context: """
        else:
            # Default instruction prompt for other models
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
    
    def _call_api(self, prompt: str) -> str:
        """
        Call HuggingFace Inference API.
        
        Args:
            prompt: Input prompt for the model
            
        Returns:
            Generated text response
        """
        # Validate prompt
        if not prompt or len(prompt.strip()) < 5:
            logger.warning(f"Prompt too short: '{prompt}' - padding it")
            prompt = f"Please provide information about: {prompt}. Based on the context, give a detailed answer."
        
        # Model-specific payload formatting
        if "squad" in self.model_name.lower() or "roberta" in self.model_name.lower():
            # RoBERTa Squad2 needs question and context separately
            # Parse the structured prompt format we create
            if "Context:" in prompt and "Question:" in prompt:
                # Split by the markers we use
                parts = prompt.split("Question:")
                if len(parts) == 2:
                    context_part = parts[0].replace("Context:", "").strip()
                    question_part = parts[1].strip()
                else:
                    # Fallback
                    question_part = "What is this about?"
                    context_part = prompt
            else:
                # Fallback for unexpected format
                question_part = "What is this about?"
                context_part = prompt
            
            # Clean up the context and question
            context_part = context_part.replace("---", "").strip()
            if not question_part or len(question_part.strip()) < 3:
                question_part = "What is the main information?"
            
            # Debug output
            print(f"🔍 Squad2 Question: {question_part[:100]}...")
            print(f"🔍 Squad2 Context: {context_part[:200]}...")
            
            payload = {
                "inputs": {
                    "question": question_part,
                    "context": context_part
                }
            }
        elif "bart" in self.model_name.lower() or "distilbart" in self.model_name.lower():
            # BART/DistilBART for summarization
            if len(prompt) < 50:
                prompt = f"{prompt} Please provide a comprehensive answer based on the available information."
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 150,
                    "min_length": 10,
                    "do_sample": False
                }
            }
        else:
            # Simple payload for other models
            payload = {"inputs": prompt}
        
        try:
            logger.info(f"Calling API URL: {self.api_url}")
            logger.info(f"Headers: {self.headers}")
            logger.info(f"Payload: {payload}")
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            
            if response.status_code == 503:
                # Model is loading, wait and retry
                logger.warning("Model loading, waiting 20 seconds...")
                import time
                time.sleep(20)
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                logger.info(f"Retry response status: {response.status_code}")
            
            if response.status_code == 404:
                logger.error(f"Model not found: {self.model_name}")
                logger.error(f"Response text: {response.text}")
                # Try fallback models
                for fallback_model in self.fallback_models:
                    if fallback_model != self.model_name:
                        logger.info(f"Trying fallback model: {fallback_model}")
                        try:
                            return self._call_api_with_model(prompt, fallback_model)
                        except Exception as e:
                            logger.warning(f"Fallback model {fallback_model} failed: {e}")
                            continue
                return "All models are currently unavailable. Please try again later."
            
            response.raise_for_status()
            result = response.json()
            
            # Handle different response formats based on model type
            print(f"🔍 API Response type: {type(result)}")
            print(f"🔍 API Response preview: {str(result)[:300]}...")
            
            if isinstance(result, dict) and "answer" in result:
                # RoBERTa Squad2 format: {"answer": "...", "score": ..., "start": ..., "end": ...}
                answer = result["answer"].strip()
                print(f"🔍 Squad2 extracted answer: {answer}")
                return answer
            elif isinstance(result, list) and len(result) > 0:
                # Check for DistilBART format (returns dict with summary_text)
                if isinstance(result[0], dict) and "summary_text" in result[0]:
                    return result[0]["summary_text"].strip()
                # Check for nested list (BART format: [[...]])
                elif isinstance(result[0], list) and len(result[0]) > 0:
                    if isinstance(result[0][0], dict):
                        return result[0][0].get("summary_text", str(result[0][0])).strip()
                    else:
                        # BART base returns embeddings - not useful for text generation
                        logger.warning("BART returned embeddings instead of text")
                        return "Model returned embeddings instead of text. Please try a different model."
                # Regular list format
                elif isinstance(result[0], dict):
                    # Try different keys that models might use
                    text = (result[0].get("generated_text", "") or 
                           result[0].get("summary_text", "") or
                           result[0].get("translation_text", "") or
                           result[0].get("answer", "") or
                           str(result[0]))
                    # Remove the input prompt from the output if present
                    if isinstance(prompt, str) and text.startswith(prompt):
                        text = text[len(prompt):].strip()
                    return text
                else:
                    return str(result[0]).strip()
            elif isinstance(result, dict):
                # Some models return dict directly
                text = (result.get("generated_text", "") or
                       result.get("summary_text", "") or 
                       result.get("translation_text", "") or
                       result.get("answer", "") or
                       str(result))
                # Remove input prompt if model included it
                if isinstance(prompt, str) and text.startswith(prompt):
                    text = text[len(prompt):].strip()
                return text
            elif isinstance(result, str):
                return result.strip()
            else:
                logger.error(f"Unexpected response format: {type(result)} - {result}")
                return "I apologize, but I couldn't generate a response."
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return f"API Error: {str(e)}. Using free tier? Try adding an API token."
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return f"Error: {str(e)}. Please check logs for details."
    
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
        
        # FALLBACK: If no explicit citations found but we have an answer and chunks,
        # create citations for the top chunks that were likely used
        if not cited_chunks and chunks and len(answer.strip()) > 50:
            # Use the top chunks that were provided as likely sources
            num_fallback_citations = min(3, len(chunks))  # Use top 3 chunks max
            cited_chunks = set(range(num_fallback_citations))
            print(f"🔧 HF Fallback: Creating {num_fallback_citations} citations for answer without explicit [chunk_X] references", file=sys.stderr, flush=True)
        
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
        Calculate confidence score for the generated answer.
        
        Args:
            answer: Generated answer
            citations: Extracted citations
            chunks: Retrieved chunks
            
        Returns:
            Confidence score (0.0-1.0)
        """
        if not chunks:
            return 0.05  # No context = very low confidence
        
        # Base confidence from context quality
        scores = [chunk.get('score', 0) for chunk in chunks]
        max_relevance = max(scores) if scores else 0
        
        if max_relevance >= 0.8:
            confidence = 0.7  # High-quality context
        elif max_relevance >= 0.6:
            confidence = 0.5  # Good context
        elif max_relevance >= 0.4:
            confidence = 0.3  # Fair context
        else:
            confidence = 0.1  # Poor context
        
        # Uncertainty indicators
        uncertainty_phrases = [
            "does not contain sufficient information",
            "context does not provide", 
            "insufficient information",
            "cannot determine",
            "not available in the provided documents"
        ]
        
        if any(phrase in answer.lower() for phrase in uncertainty_phrases):
            return min(0.15, confidence * 0.3)
        
        # Citation bonus
        if citations and chunks:
            citation_ratio = len(citations) / min(len(chunks), 3)
            confidence += 0.2 * citation_ratio
        
        return min(confidence, 0.9)  # Cap at 90%
    
    def _generate_internal(
        self,
        query: str,
        chunks: List[Dict[str, Any]]
    ) -> GeneratedAnswer:
        """
        Generate an answer based on the query and retrieved chunks (internal method).
        
        This method contains the original HuggingFace-specific logic and is called
        by the adapter pattern interface.
        
        Args:
            query: User's question
            chunks: Retrieved document chunks
            
        Returns:
            GeneratedAnswer object with HuggingFace-specific format
        """
        start_time = datetime.now()
        
        # Check for no-context situation
        if not chunks or all(len(chunk.get('content', chunk.get('text', ''))) < 20 for chunk in chunks):
            return GeneratedAnswer(
                answer="This information isn't available in the provided documents.",
                citations=[],
                confidence_score=0.05,
                generation_time=0.1,
                model_used=self.model_name,
                context_used=chunks
            )
        
        # Format context from chunks
        context = self._format_context(chunks)
        
        # Create prompt using TechnicalPromptTemplates for consistency
        prompt_data = TechnicalPromptTemplates.format_prompt_with_template(
            query=query,
            context=context
        )
        
        # Format for specific model types
        if "squad" in self.model_name.lower() or "roberta" in self.model_name.lower():
            # Squad2 uses special question/context format - handled in _call_api
            prompt = f"Context: {context}\n\nQuestion: {query}"
        elif "gpt2" in self.model_name.lower() or "distilgpt2" in self.model_name.lower():
            # Simple completion style for GPT-2
            prompt = f"""{prompt_data['system']}

{prompt_data['user']}

MANDATORY: Use [chunk_1], [chunk_2] etc. for all facts.

Answer:"""
        elif "llama" in self.model_name.lower():
            # Llama-2 chat format with technical templates
            prompt = f"""[INST] {prompt_data['system']}

{prompt_data['user']}

MANDATORY: Use [chunk_1], [chunk_2] etc. for all facts. [/INST]"""
        elif "mistral" in self.model_name.lower():
            # Mistral instruction format with technical templates
            prompt = f"""[INST] {prompt_data['system']}

{prompt_data['user']}

MANDATORY: Use [chunk_1], [chunk_2] etc. for all facts. [/INST]"""
        elif "codellama" in self.model_name.lower():
            # CodeLlama instruction format with technical templates
            prompt = f"""[INST] {prompt_data['system']}

{prompt_data['user']}

MANDATORY: Use [chunk_1], [chunk_2] etc. for all facts. [/INST]"""
        elif "distilbart" in self.model_name.lower():
            # DistilBART is a summarization model - simpler prompt works better
            prompt = f"""Technical Documentation Context:
{context}

Question: {query}

Instructions: Provide a technical answer using only the context above. Include source citations."""
        else:
            # Default instruction prompt with technical templates
            prompt = f"""{prompt_data['system']}

{prompt_data['user']}

MANDATORY: Use [chunk_1], [chunk_2] etc. for all factual statements.

Answer:"""
        
        # Generate response
        try:
            answer_with_citations = self._call_api(prompt)
            
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
                model_used=self.model_name,
                context_used=chunks
            )
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return GeneratedAnswer(
                answer="I apologize, but I encountered an error while generating the answer. Please try again.",
                citations=[],
                confidence_score=0.0,
                generation_time=0.0,
                model_used=self.model_name,
                context_used=chunks
            )
    
    def generate_with_custom_prompt(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        custom_prompt: Dict[str, str]
    ) -> GeneratedAnswer:
        """
        Generate answer using a custom prompt (for adaptive prompting).
        
        Args:
            query: User's question
            chunks: Retrieved context chunks
            custom_prompt: Dict with 'system' and 'user' prompts
            
        Returns:
            GeneratedAnswer with custom prompt enhancement
        """
        start_time = datetime.now()
        
        # Format context
        context = self._format_context(chunks)
        
        # Build prompt using custom format
        if "llama" in self.model_name.lower():
            prompt = f"""[INST] {custom_prompt['system']}

{custom_prompt['user']}

MANDATORY: Use [chunk_1], [chunk_2] etc. for all facts. [/INST]"""
        elif "mistral" in self.model_name.lower():
            prompt = f"""[INST] {custom_prompt['system']}

{custom_prompt['user']}

MANDATORY: Use [chunk_1], [chunk_2] etc. for all facts. [/INST]"""
        elif "distilbart" in self.model_name.lower():
            # For BART, use the user prompt directly (it already contains context)
            prompt = custom_prompt['user']
        else:
            # Default format
            prompt = f"""{custom_prompt['system']}

{custom_prompt['user']}

MANDATORY: Use [chunk_1], [chunk_2] etc. for all factual statements.

Answer:"""
        
        # Generate response
        try:
            answer_with_citations = self._call_api(prompt)
            
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
                model_used=self.model_name,
                context_used=chunks
            )
            
        except Exception as e:
            logger.error(f"Error generating answer with custom prompt: {e}")
            return GeneratedAnswer(
                answer="I apologize, but I encountered an error while generating the answer. Please try again.",
                citations=[],
                confidence_score=0.0,
                generation_time=0.0,
                model_used=self.model_name,
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

    # ===============================================
    # ADAPTER PATTERN IMPLEMENTATION
    # ===============================================
    
    def generate(self, query: str, context: List[Document]) -> Answer:
        """
        Generate an answer from query and context documents (standard interface).
        
        This is the public interface that conforms to the AnswerGenerator protocol.
        It handles the conversion between standard Document objects and HuggingFace's
        internal chunk format.
        
        Args:
            query: User's question
            context: List of relevant Document objects
            
        Returns:
            Answer object conforming to standard interface
            
        Raises:
            ValueError: If query is empty or context is None
        """
        if Document is None or Answer is None:
            raise ImportError("Standard interfaces not available - falling back to chunk-based interface")
            
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        if context is None:
            raise ValueError("Context cannot be None")
        
        # Internal adapter: Convert Documents to HuggingFace chunk format
        hf_chunks = self._documents_to_hf_chunks(context)
        
        # Use existing HuggingFace-specific generation logic
        hf_result = self._generate_internal(query, hf_chunks)
        
        # Internal adapter: Convert HuggingFace result to standard Answer
        return self._hf_result_to_answer(hf_result, context)
    
    def _documents_to_hf_chunks(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Convert Document objects to HuggingFace's internal chunk format.
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of chunk dictionaries in HuggingFace format
        """
        chunks = []
        for i, doc in enumerate(documents):
            chunk = {
                "id": f"chunk_{i+1}",
                "content": doc.content,  # HuggingFace expects "content" field
                "text": doc.content,    # Fallback field for compatibility
                "score": 1.0,           # Default relevance score
                "metadata": {
                    "source": doc.metadata.get("source", "unknown"),
                    "page_number": doc.metadata.get("start_page", 1),
                    **doc.metadata  # Include all original metadata
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def _hf_result_to_answer(self, hf_result: GeneratedAnswer, original_context: List[Document]) -> Answer:
        """
        Convert HuggingFace's GeneratedAnswer to the standard Answer format.
        
        Args:
            hf_result: The GeneratedAnswer from HuggingFace generation
            original_context: Original Document objects for source attribution
            
        Returns:
            Answer object conforming to standard interface
        """
        return Answer(
            text=hf_result.answer,
            sources=original_context,
            confidence=hf_result.confidence_score,
            metadata={
                "model_used": hf_result.model_used,
                "generation_time": hf_result.generation_time,
                "citations": [
                    {
                        "chunk_id": citation.chunk_id,
                        "page_number": citation.page_number,
                        "source_file": citation.source_file,
                        "relevance_score": citation.relevance_score,
                        "text_snippet": citation.text_snippet
                    }
                    for citation in hf_result.citations
                ],
                "context_chunks_used": len(hf_result.context_used),
                "provider": "huggingface",
                "adapter_pattern": "unified_interface"
            }
        )
    

if __name__ == "__main__":
    # Example usage
    generator = HuggingFaceAnswerGenerator()
    
    # Example chunks (would come from retrieval system)
    example_chunks = [
        {
            "id": "chunk_1",
            "content": "RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles.",
            "metadata": {"page_number": 1, "source": "riscv-spec.pdf"},
            "score": 0.95
        }
    ]
    
    # Generate answer
    result = generator.generate(
        query="What is RISC-V?",
        chunks=example_chunks
    )
    
    # Display formatted result
    print(generator.format_answer_with_citations(result))