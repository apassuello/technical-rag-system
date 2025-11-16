#!/usr/bin/env python3
"""
HuggingFace Inference Providers API-based answer generation.

This module provides answer generation using HuggingFace's new Inference Providers API,
which offers OpenAI-compatible chat completion format for better reliability and consistency.
"""

import os
import sys
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re

# Import shared components
from .hf_answer_generator import Citation, GeneratedAnswer
from .prompt_templates import TechnicalPromptTemplates

# Set up logging
logger = logging.getLogger(__name__)

# Check if huggingface_hub is new enough for InferenceClient chat completion
try:
    from huggingface_hub import InferenceClient
    from huggingface_hub import __version__ as hf_hub_version
    logger.info(f"🔍 Using huggingface_hub version: {hf_hub_version}")
except ImportError:
    logger.error("❌ huggingface_hub not found or outdated. Please install: pip install -U huggingface-hub")
    raise


class InferenceProvidersGenerator:
    """
    Generates answers using HuggingFace Inference Providers API.
    
    This uses the new OpenAI-compatible chat completion format for better reliability
    compared to the classic Inference API. It provides:
    - Consistent response format across models
    - Better error handling and retry logic
    - Support for streaming responses
    - Automatic provider selection and failover
    """
    
    # Models that work well with chat completion format
    CHAT_MODELS = [
        "microsoft/DialoGPT-medium",  # Proven conversational model
        "google/gemma-2-2b-it",       # Instruction-tuned, good for Q&A
        "meta-llama/Llama-3.2-3B-Instruct",  # If available with token
        "Qwen/Qwen2.5-1.5B-Instruct",  # Small, fast, good quality
    ]
    
    # Fallback to classic API models if chat completion fails
    CLASSIC_FALLBACK_MODELS = [
        "google/flan-t5-small",       # Good for instructions
        "deepset/roberta-base-squad2", # Q&A specific
        "facebook/bart-base",          # Summarization
    ]
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        api_token: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 512,
        timeout: int = 30
    ):
        """
        Initialize the Inference Providers answer generator.
        
        Args:
            model_name: Model to use (defaults to first available chat model)
            api_token: HF API token (uses env vars if not provided)
            temperature: Generation temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
        """
        # Get API token from various sources
        self.api_token = (
            api_token or 
            os.getenv("HUGGINGFACE_API_TOKEN") or 
            os.getenv("HF_TOKEN") or 
            os.getenv("HF_API_TOKEN")
        )
        
        if not self.api_token:
            logger.warning("⚠️ No HF API token found. Inference Providers requires authentication.")
            logger.warning("Set HF_TOKEN, HUGGINGFACE_API_TOKEN, or HF_API_TOKEN environment variable.")
            raise ValueError("HuggingFace API token required for Inference Providers")

        logger.info(f"✅ Found HF token (starts with: {self.api_token[:8]}...)")
        
        # Initialize client with token
        self.client = InferenceClient(token=self.api_token)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # Select model
        self.model_name = model_name or self.CHAT_MODELS[0]
        self.using_chat_completion = True

        logger.info(f"🚀 Initialized Inference Providers with model: {self.model_name}")

        # Test the connection
        self._test_connection()

    def _test_connection(self):
        """Test if the API is accessible and model is available."""
        logger.info("🔧 Testing Inference Providers API connection...")
        
        try:
            # Try a simple test query
            test_messages = [
                {"role": "user", "content": "Hello"}
            ]
            
            # First try chat completion (preferred)
            try:
                response = self.client.chat_completion(
                    messages=test_messages,
                    model=self.model_name,
                    max_tokens=10,
                    temperature=0.1
                )
                logger.info(f"✅ Chat completion API working with {self.model_name}")
                self.using_chat_completion = True
                return
            except Exception as e:
                logger.warning(f"⚠️ Chat completion failed for {self.model_name}: {e}")

                # Try other chat models
                for model in self.CHAT_MODELS:
                    if model != self.model_name:
                        try:
                            logger.info(f"🔄 Trying {model}...")
                            response = self.client.chat_completion(
                                messages=test_messages,
                                model=model,
                                max_tokens=10
                            )
                            logger.info(f"✅ Found working model: {model}")
                            self.model_name = model
                            self.using_chat_completion = True
                            return
                        except Exception as e:
                            logger.warning(f"⚠️ Model {model} failed: {e}")
                            continue
            
            # If chat completion fails, test classic text generation
            logger.info("🔄 Falling back to classic text generation API...")
            for model in self.CLASSIC_FALLBACK_MODELS:
                try:
                    response = self.client.text_generation(
                        model=model,
                        prompt="Hello",
                        max_new_tokens=10
                    )
                    logger.info(f"✅ Classic API working with fallback model: {model}")
                    self.model_name = model
                    self.using_chat_completion = False
                    return
                except Exception as e:
                    logger.warning(f"⚠️ Classic model {model} failed: {e}")
                    continue

            raise Exception("No working models found in Inference Providers API")

        except Exception as e:
            logger.error(f"❌ Inference Providers API test failed: {e}")
            raise
    
    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into context string."""
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            chunk_text = chunk.get('content', chunk.get('text', ''))
            page_num = chunk.get('metadata', {}).get('page_number', 'unknown')
            source = chunk.get('metadata', {}).get('source', 'unknown')
            
            context_parts.append(
                f"[chunk_{i+1}] (Page {page_num} from {source}):\n{chunk_text}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _create_messages(self, query: str, context: str) -> List[Dict[str, str]]:
        """Create chat messages using TechnicalPromptTemplates."""
        # Get appropriate template based on query type
        prompt_data = TechnicalPromptTemplates.format_prompt_with_template(
            query=query,
            context=context
        )
        
        # Create messages for chat completion
        messages = [
            {
                "role": "system",
                "content": prompt_data['system'] + "\n\nMANDATORY: Use [chunk_X] citations for all facts."
            },
            {
                "role": "user", 
                "content": prompt_data['user']
            }
        ]
        
        return messages
    
    def _call_chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """Call the chat completion API."""
        try:
            logger.info(f"🤖 Calling Inference Providers chat completion with {self.model_name}...")

            # Use chat completion with proper error handling
            response = self.client.chat_completion(
                messages=messages,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False
            )

            # Extract content from response
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                logger.info(f"✅ Got response: {len(content)} characters")
                return content
            else:
                logger.warning(f"⚠️ Unexpected response format: {response}")
                return str(response)

        except Exception as e:
            logger.error(f"❌ Chat completion error: {e}")

            # Try with a fallback model
            if self.model_name != "microsoft/DialoGPT-medium":
                logger.info("🔄 Trying fallback model: microsoft/DialoGPT-medium")
                try:
                    response = self.client.chat_completion(
                        messages=messages,
                        model="microsoft/DialoGPT-medium",
                        temperature=self.temperature,
                        max_tokens=self.max_tokens
                    )
                    if hasattr(response, 'choices') and response.choices:
                        return response.choices[0].message.content
                except Exception as fallback_error:
                    logger.warning(f"⚠️ Fallback model also failed: {fallback_error}")

            raise Exception(f"Chat completion failed: {e}")
    
    def _call_classic_api(self, query: str, context: str) -> str:
        """Fallback to classic text generation API."""
        logger.info(f"🔄 Using classic text generation with {self.model_name}...")

        # Format prompt for classic API
        if "squad" in self.model_name.lower():
            # Q&A format for squad models
            prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
        elif "flan" in self.model_name.lower():
            # Instruction format for Flan models
            prompt = f"Answer the question based on the context.\n\nContext: {context}\n\nQuestion: {query}\n\nAnswer:"
        else:
            # Generic format
            prompt = f"Based on the following context, answer the question.\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"

        try:
            response = self.client.text_generation(
                model=self.model_name,
                prompt=prompt,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response
        except Exception as e:
            logger.error(f"❌ Classic API error: {e}")
            return f"Error generating response: {str(e)}"
    
    def _extract_citations(self, answer: str, chunks: List[Dict[str, Any]]) -> Tuple[str, List[Citation]]:
        """Extract citations from the answer."""
        citations = []
        citation_pattern = r'\[chunk_(\d+)\]'
        
        cited_chunks = set()
        
        # Find explicit citations
        matches = re.finditer(citation_pattern, answer)
        for match in matches:
            chunk_idx = int(match.group(1)) - 1
            if 0 <= chunk_idx < len(chunks):
                cited_chunks.add(chunk_idx)
        
        # Fallback: Create citations for top chunks if none found
        if not cited_chunks and chunks and len(answer.strip()) > 50:
            num_fallback = min(3, len(chunks))
            cited_chunks = set(range(num_fallback))
            logger.debug(f"🔧 Creating {num_fallback} fallback citations")
        
        # Create Citation objects
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
            
            # Map for natural language replacement
            source_name = chunk.get('metadata', {}).get('source', 'unknown')
            if source_name != 'unknown':
                natural_name = Path(source_name).stem.replace('-', ' ').replace('_', ' ')
                chunk_to_source[f'[chunk_{idx+1}]'] = f"the {natural_name} documentation"
            else:
                chunk_to_source[f'[chunk_{idx+1}]'] = "the documentation"
        
        # Replace citations with natural language
        natural_answer = answer
        for chunk_ref, natural_ref in chunk_to_source.items():
            natural_answer = natural_answer.replace(chunk_ref, natural_ref)
        
        # Clean up any remaining citations
        natural_answer = re.sub(r'\[chunk_\d+\]', 'the documentation', natural_answer)
        natural_answer = re.sub(r'\s+', ' ', natural_answer).strip()
        
        return natural_answer, citations
    
    def _calculate_confidence(self, answer: str, citations: List[Citation], chunks: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for the answer."""
        if not answer or len(answer.strip()) < 10:
            return 0.1
        
        # Base confidence from chunk quality
        if len(chunks) >= 3:
            confidence = 0.8
        elif len(chunks) >= 2:
            confidence = 0.7
        else:
            confidence = 0.6
        
        # Citation bonus
        if citations and chunks:
            citation_ratio = len(citations) / min(len(chunks), 3)
            confidence += 0.15 * citation_ratio
        
        # Check for uncertainty phrases
        uncertainty_phrases = [
            "insufficient information",
            "cannot determine",
            "not available in the provided documents",
            "i don't know",
            "unclear"
        ]
        
        if any(phrase in answer.lower() for phrase in uncertainty_phrases):
            confidence *= 0.3
        
        return min(confidence, 0.95)
    
    def generate(self, query: str, chunks: List[Dict[str, Any]]) -> GeneratedAnswer:
        """
        Generate an answer using Inference Providers API.
        
        Args:
            query: User's question
            chunks: Retrieved document chunks
            
        Returns:
            GeneratedAnswer with answer, citations, and metadata
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
        
        # Format context
        context = self._format_context(chunks)
        
        # Generate answer
        try:
            if self.using_chat_completion:
                # Create chat messages
                messages = self._create_messages(query, context)
                
                # Call chat completion API
                answer_text = self._call_chat_completion(messages)
            else:
                # Fallback to classic API
                answer_text = self._call_classic_api(query, context)
            
            # Extract citations and clean answer
            natural_answer, citations = self._extract_citations(answer_text, chunks)
            
            # Calculate confidence
            confidence = self._calculate_confidence(natural_answer, citations, chunks)
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            return GeneratedAnswer(
                answer=natural_answer,
                citations=citations,
                confidence_score=confidence,
                generation_time=generation_time,
                model_used=self.model_name,
                context_used=chunks
            )
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            logger.error(f"❌ Generation failed: {e}")

            # Return error response
            return GeneratedAnswer(
                answer="I apologize, but I encountered an error while generating the answer. Please try again.",
                citations=[],
                confidence_score=0.0,
                generation_time=(datetime.now() - start_time).total_seconds(),
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
        
        if not chunks:
            return GeneratedAnswer(
                answer="I don't have enough context to answer your question.",
                citations=[],
                confidence_score=0.0,
                generation_time=0.1,
                model_used=self.model_name,
                context_used=chunks
            )
        
        try:
            # Try chat completion with custom prompt
            messages = [
                {"role": "system", "content": custom_prompt['system']},
                {"role": "user", "content": custom_prompt['user']}
            ]
            
            answer_text = self._call_chat_completion(messages)
            
            # Extract citations and clean answer
            natural_answer, citations = self._extract_citations(answer_text, chunks)
            
            # Calculate confidence
            confidence = self._calculate_confidence(natural_answer, citations, chunks)
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            return GeneratedAnswer(
                answer=natural_answer,
                citations=citations,
                confidence_score=confidence,
                generation_time=generation_time,
                model_used=self.model_name,
                context_used=chunks
            )
            
        except Exception as e:
            logger.error(f"Error generating answer with custom prompt: {e}")
            logger.error(f"❌ Custom prompt generation failed: {e}")

            # Return error response
            return GeneratedAnswer(
                answer="I apologize, but I encountered an error while generating the answer. Please try again.",
                citations=[],
                confidence_score=0.0,
                generation_time=(datetime.now() - start_time).total_seconds(),
                model_used=self.model_name,
                context_used=chunks
            )


# Example usage
if __name__ == "__main__":
    # Test the generator
    print("Testing Inference Providers Generator...")
    
    try:
        generator = InferenceProvidersGenerator()
        
        # Test chunks
        test_chunks = [
            {
                "content": "RISC-V is an open-source instruction set architecture (ISA) based on established reduced instruction set computer (RISC) principles.",
                "metadata": {"page_number": 1, "source": "riscv-spec.pdf"},
                "score": 0.95
            },
            {
                "content": "Unlike most other ISA designs, RISC-V is provided under open source licenses that do not require fees to use.",
                "metadata": {"page_number": 2, "source": "riscv-spec.pdf"},
                "score": 0.85
            }
        ]
        
        # Generate answer
        result = generator.generate("What is RISC-V and why is it important?", test_chunks)
        
        print(f"\n📝 Answer: {result.answer}")
        print(f"📊 Confidence: {result.confidence_score:.1%}")
        print(f"⏱️ Generation time: {result.generation_time:.2f}s")
        print(f"🤖 Model: {result.model_used}")
        print(f"📚 Citations: {len(result.citations)}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()