#!/usr/bin/env python3
"""
Ollama-based answer generator for local inference.

Provides the same interface as HuggingFaceAnswerGenerator but uses
local Ollama server for model inference.
"""

import time
import requests
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Import shared components
from .hf_answer_generator import Citation, GeneratedAnswer
from .prompt_templates import TechnicalPromptTemplates


class OllamaAnswerGenerator:
    """
    Generates answers using local Ollama server.

    Perfect for:
    - Local development
    - Privacy-sensitive applications
    - No API rate limits
    - Consistent performance
    - Offline operation
    """

    def __init__(
        self,
        model_name: str = "llama3.2:3b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.3,
        max_tokens: int = 512,
    ):
        """
        Initialize Ollama answer generator.

        Args:
            model_name: Ollama model to use (e.g., "llama3.2:3b", "mistral")
            base_url: Ollama server URL
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Test connection
        self._test_connection()

    def _test_connection(self):
        """Test if Ollama server is accessible."""
        # Reduce retries for faster initialization - container should be ready quickly
        max_retries = 12  # Wait up to 60 seconds for Ollama to start
        retry_delay = 5

        print(
            f"🔧 Testing connection to {self.base_url}/api/tags...",
            file=sys.stderr,
            flush=True,
        )

        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=8)
                if response.status_code == 200:
                    print(
                        f"✅ Connected to Ollama at {self.base_url}",
                        file=sys.stderr,
                        flush=True,
                    )

                    # Check if our model is available
                    models = response.json().get("models", [])
                    model_names = [m["name"] for m in models]

                    if self.model_name in model_names:
                        print(
                            f"✅ Model {self.model_name} is available",
                            file=sys.stderr,
                            flush=True,
                        )
                        return  # Success!
                    else:
                        print(
                            f"⚠️ Model {self.model_name} not found. Available: {model_names}",
                            file=sys.stderr,
                            flush=True,
                        )
                        if models:  # If any models are available, use the first one
                            fallback_model = model_names[0]
                            print(
                                f"🔄 Using fallback model: {fallback_model}",
                                file=sys.stderr,
                                flush=True,
                            )
                            self.model_name = fallback_model
                            return
                        else:
                            print(
                                f"📥 No models found, will try to pull {self.model_name}",
                                file=sys.stderr,
                                flush=True,
                            )
                            # Try to pull the model
                            self._pull_model(self.model_name)
                            return
                else:
                    print(f"⚠️ Ollama server returned status {response.status_code}")
                    if attempt < max_retries - 1:
                        print(
                            f"🔄 Retry {attempt + 1}/{max_retries} in {retry_delay} seconds..."
                        )
                        time.sleep(retry_delay)
                        continue

            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    print(
                        f"⏳ Ollama not ready yet, retry {attempt + 1}/{max_retries} in {retry_delay} seconds..."
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception(
                        f"Cannot connect to Ollama server at {self.base_url} after 60 seconds. Check if it's running."
                    )
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"⏳ Ollama timeout, retry {attempt + 1}/{max_retries}...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception("Ollama server timeout after multiple retries.")
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Ollama error: {e}, retry {attempt + 1}/{max_retries}...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception(
                        f"Ollama connection failed after {max_retries} attempts: {e}"
                    )

        raise Exception("Failed to connect to Ollama after all retries")

    def _pull_model(self, model_name: str):
        """Pull a model if it's not available."""
        try:
            print(f"📥 Pulling model {model_name}...")
            pull_response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=300,  # 5 minutes for model download
            )
            if pull_response.status_code == 200:
                print(f"✅ Successfully pulled {model_name}")
            else:
                print(f"⚠️ Failed to pull {model_name}: {pull_response.status_code}")
                # Try smaller models as fallback
                fallback_models = ["llama3.2:1b", "llama2:latest", "mistral:latest"]
                for fallback in fallback_models:
                    try:
                        print(f"🔄 Trying fallback model: {fallback}")
                        fallback_response = requests.post(
                            f"{self.base_url}/api/pull",
                            json={"name": fallback},
                            timeout=300,
                        )
                        if fallback_response.status_code == 200:
                            print(f"✅ Successfully pulled fallback {fallback}")
                            self.model_name = fallback
                            return
                    except:
                        continue
                raise Exception(f"Failed to pull {model_name} or any fallback models")
        except Exception as e:
            print(f"❌ Model pull failed: {e}")
            raise

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into context."""
        context_parts = []

        for i, chunk in enumerate(chunks):
            chunk_text = chunk.get("content", chunk.get("text", ""))
            page_num = chunk.get("metadata", {}).get("page_number", "unknown")
            source = chunk.get("metadata", {}).get("source", "unknown")

            context_parts.append(
                f"[chunk_{i+1}] (Page {page_num} from {source}):\n{chunk_text}\n"
            )

        return "\n---\n".join(context_parts)

    def _create_prompt(self, query: str, context: str) -> str:
        """Create optimized prompt using TechnicalPromptTemplates."""
        # Get the appropriate template based on query type
        prompt_data = TechnicalPromptTemplates.format_prompt_with_template(
            query=query, context=context
        )

        # Format for different model types
        if "llama" in self.model_name.lower():
            # Llama-3.2 format with simplified citation instructions
            return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{prompt_data['system']}

<|eot_id|><|start_header_id|>user<|end_header_id|>
{prompt_data['user']}

<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

        elif "mistral" in self.model_name.lower():
            # Mistral format with simplified instructions
            return f"""[INST] {prompt_data['system']}

Context:
{context}

Question: {query}

[/INST]"""

        else:
            # Generic format with simplified instructions
            return f"""{prompt_data['system']}

Context:
{context}

Question: {query}

Answer:"""

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API for generation."""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate", json=payload, timeout=300
            )

            response.raise_for_status()
            result = response.json()

            return result.get("response", "").strip()

        except requests.exceptions.RequestException as e:
            print(f"❌ Ollama API error: {e}")
            return f"Error communicating with Ollama: {str(e)}"
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return f"Unexpected error: {str(e)}"

    def _extract_citations(
        self, answer: str, chunks: List[Dict[str, Any]]
    ) -> Tuple[str, List[Citation]]:
        """Extract citations from the generated answer."""
        citations = []
        citation_pattern = r"\[chunk_(\d+)\]"

        cited_chunks = set()

        # Find [chunk_X] citations
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
            print(
                f"🔧 Fallback: Creating {num_fallback_citations} citations for answer without explicit [chunk_X] references",
                file=sys.stderr,
                flush=True,
            )

        # Create Citation objects
        chunk_to_source = {}
        for idx in cited_chunks:
            chunk = chunks[idx]
            citation = Citation(
                chunk_id=chunk.get("id", f"chunk_{idx}"),
                page_number=chunk.get("metadata", {}).get("page_number", 0),
                source_file=chunk.get("metadata", {}).get("source", "unknown"),
                relevance_score=chunk.get("score", 0.0),
                text_snippet=chunk.get("content", chunk.get("text", ""))[:200] + "...",
            )
            citations.append(citation)

            # Map chunk reference to natural source name
            source_name = chunk.get("metadata", {}).get("source", "unknown")
            if source_name != "unknown":
                natural_name = (
                    Path(source_name).stem.replace("-", " ").replace("_", " ")
                )
                chunk_to_source[f"[chunk_{idx+1}]"] = (
                    f"the {natural_name} documentation"
                )
            else:
                chunk_to_source[f"[chunk_{idx+1}]"] = "the documentation"

        # Replace [chunk_X] with natural references
        natural_answer = answer
        for chunk_ref, natural_ref in chunk_to_source.items():
            natural_answer = natural_answer.replace(chunk_ref, natural_ref)

        # Clean up any remaining unreferenced citations
        natural_answer = re.sub(r"\[chunk_\d+\]", "the documentation", natural_answer)
        natural_answer = re.sub(r"\s+", " ", natural_answer).strip()

        return natural_answer, citations

    def _calculate_confidence(
        self, answer: str, citations: List[Citation], chunks: List[Dict[str, Any]], query: str = None
    ) -> float:
        """
        Calculate confidence score with enhanced context awareness.
        
        Args:
            answer: Generated answer text
            citations: List of citations found in answer
            chunks: Retrieved context chunks
            query: Original query for semantic relevance checking
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not answer or len(answer.strip()) < 10:
            return 0.1

        # Start with base confidence based on content quality
        base_confidence = 0.5  # Lower starting point for better calibration
        
        # Context quality assessment
        context_quality = self._assess_context_quality(chunks)
        base_confidence += context_quality * 0.3  # Max +0.3 for excellent context
        
        # Citation quality assessment
        citation_quality = self._assess_citation_quality(citations, chunks)
        base_confidence += citation_quality * 0.2  # Max +0.2 for excellent citations
        
        # Semantic relevance check (if query provided)
        if query:
            relevance_score = self._assess_semantic_relevance(query, answer, chunks)
            base_confidence += relevance_score * 0.2  # Max +0.2 for highly relevant
        
        # Answer quality indicators
        answer_quality = self._assess_answer_quality(answer)
        base_confidence += answer_quality * 0.15  # Max +0.15 for high quality
        
        # Uncertainty penalty (stronger than before)
        uncertainty_phrases = [
            "insufficient information",
            "cannot determine", 
            "not available in the provided documents",
            "I don't have enough information",
            "unable to answer",
            "not clear from the context"
        ]
        
        if any(phrase in answer.lower() for phrase in uncertainty_phrases):
            base_confidence *= 0.3  # Heavy penalty for uncertainty
        
        # Off-topic detection penalty
        if self._is_off_topic(query, chunks) if query else False:
            base_confidence *= 0.4  # Penalty for off-topic queries
        
        # Ensure reasonable range: 0.2 to 0.9 (more realistic than 0.1 to 0.95)
        return max(0.2, min(base_confidence, 0.9))

    def _assess_context_quality(self, chunks: List[Dict[str, Any]]) -> float:
        """Assess the quality of retrieved context chunks."""
        if not chunks:
            return 0.0
        
        # Consider chunk count, content length, and relevance scores
        chunk_count_score = min(len(chunks) / 3.0, 1.0)  # Normalize to 1.0 for 3+ chunks
        
        # Average relevance score from retrieval
        avg_relevance = sum(chunk.get('score', 0.0) for chunk in chunks) / len(chunks)
        
        # Content richness (average chunk length)
        avg_length = sum(len(chunk.get('content', chunk.get('text', ''))) for chunk in chunks) / len(chunks)
        length_score = min(avg_length / 500.0, 1.0)  # Normalize to 1.0 for 500+ char chunks
        
        return (chunk_count_score + avg_relevance + length_score) / 3.0

    def _assess_citation_quality(self, citations: List[Citation], chunks: List[Dict[str, Any]]) -> float:
        """Assess the quality of citations in the answer."""
        if not citations or not chunks:
            return 0.0
        
        # Citation coverage (how many chunks are cited)
        citation_coverage = len(citations) / min(len(chunks), 3)
        
        # Citation relevance (based on chunk scores)
        citation_relevance = sum(chunk.get('score', 0.0) for chunk in chunks[:len(citations)]) / len(citations)
        
        return min((citation_coverage + citation_relevance) / 2.0, 1.0)

    def _assess_semantic_relevance(self, query: str, answer: str, chunks: List[Dict[str, Any]]) -> float:
        """Assess semantic relevance between query, answer, and context."""
        if not query or not answer:
            return 0.5  # Neutral if we can't assess
        
        # Simple keyword overlap assessment (could be enhanced with embeddings)
        import re
        
        # Clean and tokenize with better word boundary detection
        query_clean = re.sub(r'[^\w\s-]', ' ', query.lower())
        answer_clean = re.sub(r'[^\w\s-]', ' ', answer.lower())
        
        query_words = set(query_clean.split())
        answer_words = set(answer_clean.split())
        context_words = set()
        
        for chunk in chunks:
            content = chunk.get('content', chunk.get('text', ''))
            content_clean = re.sub(r'[^\w\s-]', ' ', content.lower())
            context_words.update(content_clean.split())
        
        # Query-answer overlap
        query_answer_overlap = len(query_words & answer_words) / max(len(query_words), 1)
        
        # Query-context overlap
        query_context_overlap = len(query_words & context_words) / max(len(query_words), 1)
        
        # Combine overlaps
        relevance_score = (query_answer_overlap + query_context_overlap) / 2.0
        
        return min(relevance_score, 1.0)

    def _assess_answer_quality(self, answer: str) -> float:
        """Assess the quality of the generated answer."""
        if not answer:
            return 0.0
        
        # Length appropriateness (not too short, not too long)
        length = len(answer)
        if length < 50:
            length_score = 0.0
        elif length < 200:
            length_score = 0.5
        elif length < 2000:
            length_score = 1.0
        else:
            length_score = 0.7  # Penalize overly long answers
        
        # Technical vocabulary presence (indicates domain expertise)
        technical_terms = ['architecture', 'instruction', 'processor', 'system', 'implementation', 
                          'specification', 'protocol', 'interface', 'module', 'framework']
        tech_score = sum(1 for term in technical_terms if term in answer.lower()) / len(technical_terms)
        
        # Sentence structure (rough assessment)
        sentence_count = answer.count('.') + answer.count('!') + answer.count('?')
        structure_score = min(sentence_count / 5.0, 1.0)  # Normalize to 1.0 for 5+ sentences
        
        return (length_score + tech_score + structure_score) / 3.0

    def _is_off_topic(self, query: str, chunks: List[Dict[str, Any]]) -> bool:
        """Detect if query is off-topic relative to available context."""
        if not query or not chunks:
            return False
        
        # Simple keyword-based off-topic detection with better tokenization
        import re
        
        # Clean and tokenize query and context
        query_clean = re.sub(r'[^\w\s-]', ' ', query.lower())  # Keep hyphens for terms like "risc-v"
        query_words = set(query_clean.split())
        context_words = set()
        
        for chunk in chunks:
            content = chunk.get('content', chunk.get('text', ''))
            content_clean = re.sub(r'[^\w\s-]', ' ', content.lower())
            context_words.update(content_clean.split())
        
        # If query has very little overlap with context, it might be off-topic
        overlap_ratio = len(query_words & context_words) / max(len(query_words), 1)
        
        # Filter out common stop words that don't indicate relevance
        stop_words = {'is', 'what', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        meaningful_query_words = query_words - stop_words
        meaningful_context_words = context_words - stop_words
        
        if meaningful_query_words:
            meaningful_overlap = len(meaningful_query_words & meaningful_context_words) / len(meaningful_query_words)
            return meaningful_overlap < 0.2  # Less than 20% meaningful overlap suggests off-topic
        
        return overlap_ratio < 0.15  # Fallback: less than 15% overlap suggests off-topic

    def generate(self, query: str, chunks: List[Dict[str, Any]]) -> GeneratedAnswer:
        """
        Generate an answer based on the query and retrieved chunks.

        Args:
            query: User's question
            chunks: Retrieved document chunks (as dictionaries)

        Returns:
            GeneratedAnswer object with answer, citations, and metadata
        """
        start_time = datetime.now()

        # Check for no-context situation
        if not chunks or all(
            len(chunk.get("content", chunk.get("text", ""))) < 20 for chunk in chunks
        ):
            return GeneratedAnswer(
                answer="This information isn't available in the provided documents.",
                citations=[],
                confidence_score=0.05,
                generation_time=0.1,
                model_used=self.model_name,
                context_used=chunks,
            )

        # Format context - chunks are already in dictionary format
        context = self._format_context(chunks)

        # Create prompt
        prompt = self._create_prompt(query, context)

        # Generate answer
        print(
            f"🤖 Calling Ollama with {self.model_name}...", file=sys.stderr, flush=True
        )
        answer_with_citations = self._call_ollama(prompt)

        generation_time = (datetime.now() - start_time).total_seconds()

        # Extract citations and create natural answer
        natural_answer, citations = self._extract_citations(
            answer_with_citations, chunks
        )

        # Calculate confidence with enhanced context awareness
        confidence = self._calculate_confidence(natural_answer, citations, chunks, query)

        return GeneratedAnswer(
            answer=natural_answer,
            citations=citations,
            confidence_score=confidence,
            generation_time=generation_time,
            model_used=self.model_name,
            context_used=chunks,
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
                context_used=chunks,
            )
        
        # Build custom prompt based on model type
        if "llama" in self.model_name.lower():
            prompt = f"""[INST] {custom_prompt['system']}

{custom_prompt['user']}

MANDATORY: Use [chunk_1], [chunk_2] etc. for all facts. [/INST]"""
        elif "mistral" in self.model_name.lower():
            prompt = f"""[INST] {custom_prompt['system']}

{custom_prompt['user']}

MANDATORY: Use [chunk_1], [chunk_2] etc. for all facts. [/INST]"""
        else:
            # Generic format for other models
            prompt = f"""{custom_prompt['system']}

{custom_prompt['user']}

MANDATORY: Use [chunk_1], [chunk_2] etc. for all factual statements.

Answer:"""
        
        # Generate answer
        print(f"🤖 Calling Ollama with custom prompt using {self.model_name}...", file=sys.stderr, flush=True)
        answer_with_citations = self._call_ollama(prompt)
        
        generation_time = (datetime.now() - start_time).total_seconds()
        
        # Extract citations and create natural answer
        natural_answer, citations = self._extract_citations(answer_with_citations, chunks)
        
        # Calculate confidence with enhanced context awareness
        confidence = self._calculate_confidence(natural_answer, citations, chunks, query)
        
        return GeneratedAnswer(
            answer=natural_answer,
            citations=citations,
            confidence_score=confidence,
            generation_time=generation_time,
            model_used=self.model_name,
            context_used=chunks,
        )


# Example usage
if __name__ == "__main__":
    # Test Ollama connection
    generator = OllamaAnswerGenerator(model_name="llama3.2:3b")

    # Mock chunks for testing
    test_chunks = [
        {
            "content": "RISC-V is a free and open-source ISA.",
            "metadata": {"page_number": 1, "source": "riscv-spec.pdf"},
            "score": 0.9,
        }
    ]

    # Test generation
    result = generator.generate("What is RISC-V?", test_chunks)
    print(f"Answer: {result.answer}")
    print(f"Confidence: {result.confidence_score:.2%}")
