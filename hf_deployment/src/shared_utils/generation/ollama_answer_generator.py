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
            # Llama-3.2 format with technical prompt templates
            return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{prompt_data['system']}

MANDATORY CITATION RULES:
- Use [chunk_1], [chunk_2] etc. for ALL factual statements
- Every technical claim MUST have a citation
- Example: "RISC-V is an open-source ISA [chunk_1] that supports multiple data widths [chunk_2]."

<|eot_id|><|start_header_id|>user<|end_header_id|>
{prompt_data['user']}

CRITICAL: You MUST cite sources with [chunk_X] format for every fact you state.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

        elif "mistral" in self.model_name.lower():
            # Mistral format with technical templates
            return f"""[INST] {prompt_data['system']}

Context:
{context}

Question: {query}

MANDATORY: Use [chunk_1], [chunk_2] etc. for ALL factual statements. [/INST]"""

        else:
            # Generic format with technical templates
            return f"""{prompt_data['system']}

Context:
{context}

Question: {query}

MANDATORY CITATIONS: Use [chunk_1], [chunk_2] etc. for every fact.

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
        self, answer: str, citations: List[Citation], chunks: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score."""
        if not answer or len(answer.strip()) < 10:
            return 0.1

        # Base confidence from content quality
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

        # Uncertainty penalty
        uncertainty_phrases = [
            "insufficient information",
            "cannot determine",
            "not available in the provided documents",
        ]

        if any(phrase in answer.lower() for phrase in uncertainty_phrases):
            confidence *= 0.3

        return min(confidence, 0.95)  # Cap at 95%

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

        # Calculate confidence
        confidence = self._calculate_confidence(natural_answer, citations, chunks)

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
        
        # Calculate confidence
        confidence = self._calculate_confidence(natural_answer, citations, chunks)
        
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
