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

# Import standard interfaces (add this for the adapter)
try:
    from pathlib import Path
    import sys
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.append(str(project_root))
    from src.core.interfaces import Document, Answer, AnswerGenerator
except ImportError:
    # Fallback for standalone usage
    Document = None
    Answer = None
    AnswerGenerator = object


class OllamaAnswerGenerator(AnswerGenerator if AnswerGenerator != object else object):
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

    def _create_prompt(self, query: str, context: str, chunks: List[Dict[str, Any]]) -> str:
        """Create optimized prompt with dynamic length constraints and citation instructions."""
        # Get the appropriate template based on query type
        prompt_data = TechnicalPromptTemplates.format_prompt_with_template(
            query=query, context=context
        )

        # Create dynamic citation instructions based on available chunks
        num_chunks = len(chunks)
        available_chunks = ", ".join([f"[chunk_{i+1}]" for i in range(min(num_chunks, 5))])  # Show max 5 examples
        
        # Create appropriate example based on actual chunks
        if num_chunks == 1:
            citation_example = "RISC-V is an open-source ISA [chunk_1]."
        elif num_chunks == 2:
            citation_example = "RISC-V is an open-source ISA [chunk_1] that supports multiple data widths [chunk_2]."
        else:
            citation_example = "RISC-V is an open-source ISA [chunk_1] that supports multiple data widths [chunk_2] and provides extensions [chunk_3]."

        # Determine optimal answer length based on query complexity
        target_length = self._determine_target_length(query, chunks)
        length_instruction = self._create_length_instruction(target_length)
        
        # Format for different model types
        if "llama" in self.model_name.lower():
            # Llama-3.2 format with technical prompt templates
            return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{prompt_data['system']}

MANDATORY CITATION RULES:
- ONLY use available chunks: {available_chunks}
- You have {num_chunks} chunks available - DO NOT cite chunk numbers higher than {num_chunks}
- Every technical claim MUST have a citation from available chunks
- Example: "{citation_example}"

{length_instruction}

<|eot_id|><|start_header_id|>user<|end_header_id|>
{prompt_data['user']}

CRITICAL: You MUST cite sources ONLY from available chunks: {available_chunks}. DO NOT use chunk numbers > {num_chunks}.
{length_instruction}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

        elif "mistral" in self.model_name.lower():
            # Mistral format with technical templates
            return f"""[INST] {prompt_data['system']}

Context:
{context}

Question: {query}

MANDATORY: ONLY use available chunks: {available_chunks}. DO NOT cite chunk numbers > {num_chunks}.
{length_instruction} [/INST]"""

        else:
            # Generic format with technical templates
            return f"""{prompt_data['system']}

Context:
{context}

Question: {query}

MANDATORY CITATIONS: ONLY use available chunks: {available_chunks}. DO NOT cite chunk numbers > {num_chunks}.
{length_instruction}

Answer:"""
    
    def _determine_target_length(self, query: str, chunks: List[Dict[str, Any]]) -> int:
        """
        Determine optimal answer length based on query complexity.
        
        Target range: 150-400 characters (down from 1000-2600)
        """
        # Analyze query complexity
        query_length = len(query)
        query_words = len(query.split())
        
        # Check for complexity indicators
        complex_words = [
            "explain", "describe", "analyze", "compare", "contrast", 
            "evaluate", "discuss", "detail", "elaborate", "comprehensive"
        ]
        
        simple_words = [
            "what", "define", "list", "name", "identify", "is", "are"
        ]
        
        query_lower = query.lower()
        is_complex = any(word in query_lower for word in complex_words)
        is_simple = any(word in query_lower for word in simple_words)
        
        # Base length from query type
        if is_complex:
            base_length = 350  # Complex queries get longer answers
        elif is_simple:
            base_length = 200  # Simple queries get shorter answers
        else:
            base_length = 275  # Default middle ground
        
        # Adjust based on available context
        context_factor = min(len(chunks) * 25, 75)  # More context allows longer answers
        
        # Adjust based on query length
        query_factor = min(query_words * 5, 50)  # Longer queries allow longer answers
        
        target_length = base_length + context_factor + query_factor
        
        # Constrain to target range
        return max(150, min(target_length, 400))
    
    def _create_length_instruction(self, target_length: int) -> str:
        """Create length instruction based on target length."""
        if target_length <= 200:
            return f"ANSWER LENGTH: Keep your answer concise and focused, approximately {target_length} characters. Be direct and to the point."
        elif target_length <= 300:
            return f"ANSWER LENGTH: Provide a clear and informative answer, approximately {target_length} characters. Include key details but avoid unnecessary elaboration."
        else:
            return f"ANSWER LENGTH: Provide a comprehensive but concise answer, approximately {target_length} characters. Include important details while maintaining clarity."

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

            # Don't replace chunk references - keep them as proper citations
            # The issue was that replacing [chunk_X] with "the documentation" creates repetitive text
            # Instead, we should keep the proper citation format
            pass

        # Keep the answer as-is with proper [chunk_X] citations
        # Don't replace citations with repetitive text
        natural_answer = re.sub(r"\s+", " ", answer).strip()

        return natural_answer, citations

    def _calculate_confidence(
        self, answer: str, citations: List[Citation], chunks: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence score with expanded multi-factor assessment.
        
        Enhanced algorithm expands range from 0.75-0.95 to 0.3-0.9 with:
        - Context quality assessment
        - Citation quality evaluation
        - Semantic relevance scoring
        - Off-topic detection
        - Answer completeness analysis
        """
        if not answer or len(answer.strip()) < 10:
            return 0.1

        # 1. Context Quality Assessment (0.3-0.6 base range)
        context_quality = self._assess_context_quality(chunks)
        
        # 2. Citation Quality Evaluation (0.0-0.2 boost)
        citation_quality = self._assess_citation_quality(citations, chunks)
        
        # 3. Semantic Relevance Scoring (0.0-0.15 boost)
        semantic_relevance = self._assess_semantic_relevance(answer, chunks)
        
        # 4. Off-topic Detection (-0.4 penalty if off-topic)
        off_topic_penalty = self._detect_off_topic(answer, chunks)
        
        # 5. Answer Completeness Analysis (0.0-0.1 boost)
        completeness_bonus = self._assess_answer_completeness(answer, len(chunks))
        
        # Combine all factors
        confidence = (
            context_quality + 
            citation_quality + 
            semantic_relevance + 
            completeness_bonus + 
            off_topic_penalty
        )
        
        # Apply uncertainty penalty
        uncertainty_phrases = [
            "insufficient information",
            "cannot determine", 
            "not available in the provided documents",
            "I don't have enough context",
            "the context doesn't seem to provide"
        ]
        
        if any(phrase in answer.lower() for phrase in uncertainty_phrases):
            confidence *= 0.4  # Stronger penalty for uncertainty
        
        # Constrain to target range 0.3-0.9
        return max(0.3, min(confidence, 0.9))
    
    def _assess_context_quality(self, chunks: List[Dict[str, Any]]) -> float:
        """Assess quality of context chunks (0.3-0.6 range)."""
        if not chunks:
            return 0.3
        
        # Base score from chunk count
        if len(chunks) >= 3:
            base_score = 0.6
        elif len(chunks) >= 2:
            base_score = 0.5
        else:
            base_score = 0.4
        
        # Quality adjustments based on chunk content
        avg_chunk_length = sum(len(chunk.get("content", chunk.get("text", ""))) for chunk in chunks) / len(chunks)
        
        if avg_chunk_length > 500:  # Rich content
            base_score += 0.05
        elif avg_chunk_length < 100:  # Sparse content
            base_score -= 0.05
        
        return max(0.3, min(base_score, 0.6))
    
    def _assess_citation_quality(self, citations: List[Citation], chunks: List[Dict[str, Any]]) -> float:
        """Assess citation quality (0.0-0.2 range)."""
        if not citations or not chunks:
            return 0.0
        
        # Citation coverage bonus
        citation_ratio = len(citations) / min(len(chunks), 3)
        coverage_bonus = 0.1 * citation_ratio
        
        # Citation diversity bonus (multiple sources)
        unique_sources = len(set(cit.source_file for cit in citations))
        diversity_bonus = 0.05 * min(unique_sources / max(len(chunks), 1), 1.0)
        
        return min(coverage_bonus + diversity_bonus, 0.2)
    
    def _assess_semantic_relevance(self, answer: str, chunks: List[Dict[str, Any]]) -> float:
        """Assess semantic relevance between answer and context (0.0-0.15 range)."""
        if not answer or not chunks:
            return 0.0
        
        # Simple keyword overlap assessment
        answer_words = set(answer.lower().split())
        context_words = set()
        
        for chunk in chunks:
            chunk_text = chunk.get("content", chunk.get("text", ""))
            context_words.update(chunk_text.lower().split())
        
        if not context_words:
            return 0.0
        
        # Calculate overlap ratio
        overlap = len(answer_words & context_words)
        total_unique = len(answer_words | context_words)
        
        if total_unique == 0:
            return 0.0
        
        overlap_ratio = overlap / total_unique
        return min(0.15 * overlap_ratio, 0.15)
    
    def _detect_off_topic(self, answer: str, chunks: List[Dict[str, Any]]) -> float:
        """Detect if answer is off-topic (-0.4 penalty if off-topic)."""
        if not answer or not chunks:
            return 0.0
        
        # Check for off-topic indicators
        off_topic_phrases = [
            "but I have to say that the context doesn't seem to provide",
            "these documents appear to be focused on",
            "but they don't seem to cover",
            "I'd recommend consulting a different type of documentation",
            "without more context or information"
        ]
        
        answer_lower = answer.lower()
        for phrase in off_topic_phrases:
            if phrase in answer_lower:
                return -0.4  # Strong penalty for off-topic responses
        
        return 0.0
    
    def _assess_answer_completeness(self, answer: str, chunk_count: int) -> float:
        """Assess answer completeness (0.0-0.1 range)."""
        if not answer:
            return 0.0
        
        # Length-based completeness assessment
        answer_length = len(answer)
        
        if answer_length > 500:  # Comprehensive answer
            return 0.1
        elif answer_length > 200:  # Adequate answer
            return 0.05
        else:  # Brief answer
            return 0.0

    def generate(self, query: str, context: List[Document]) -> Answer:
        """
        Generate an answer from query and context documents (standard interface).
        
        This is the public interface that conforms to the AnswerGenerator protocol.
        It handles the conversion between standard Document objects and Ollama's
        internal chunk format.
        
        Args:
            query: User's question
            context: List of relevant Document objects
            
        Returns:
            Answer object conforming to standard interface
            
        Raises:
            ValueError: If query is empty or context is None
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        if context is None:
            raise ValueError("Context cannot be None")
        
        # Internal adapter: Convert Documents to Ollama chunk format
        ollama_chunks = self._documents_to_ollama_chunks(context)
        
        # Use existing Ollama-specific generation logic
        ollama_result = self._generate_internal(query, ollama_chunks)
        
        # Internal adapter: Convert Ollama result to standard Answer
        return self._ollama_result_to_answer(ollama_result, context)
    
    def _generate_internal(self, query: str, chunks: List[Dict[str, Any]]) -> GeneratedAnswer:
        """
        Generate an answer based on the query and retrieved chunks.

        Args:
            query: User's question
            chunks: Retrieved document chunks

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

        # Format context
        context = self._format_context(chunks)

        # Create prompt with chunks parameter for dynamic citation instructions
        prompt = self._create_prompt(query, context, chunks)

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
    
    def _documents_to_ollama_chunks(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Convert Document objects to Ollama's internal chunk format.
        
        This internal adapter ensures that Document objects are properly formatted
        for Ollama's processing pipeline while keeping the format requirements
        encapsulated within this class.
        
        Args:
            documents: List of Document objects from the standard interface
            
        Returns:
            List of chunk dictionaries in Ollama's expected format
        """
        if not documents:
            return []
        
        chunks = []
        for i, doc in enumerate(documents):
            chunk = {
                "id": f"chunk_{i+1}",
                "content": doc.content,  # Ollama expects "content" field
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
    
    def _ollama_result_to_answer(self, ollama_result: GeneratedAnswer, original_context: List[Document]) -> Answer:
        """
        Convert Ollama's GeneratedAnswer to the standard Answer format.
        
        This internal adapter converts Ollama's result format back to the
        standard interface format expected by the rest of the system.
        
        Args:
            ollama_result: Result from Ollama's internal generation
            original_context: Original Document objects for sources
            
        Returns:
            Answer object conforming to standard interface
        """
        if not Answer:
            # Fallback if standard interface not available
            return ollama_result
        
        # Convert to standard Answer format
        return Answer(
            text=ollama_result.answer,
            sources=original_context,  # Use original Document objects
            confidence=ollama_result.confidence_score,
            metadata={
                "model_used": ollama_result.model_used,
                "generation_time": ollama_result.generation_time,
                "citations": [
                    {
                        "chunk_id": cit.chunk_id,
                        "page_number": cit.page_number,
                        "source_file": cit.source_file,
                        "relevance_score": cit.relevance_score,
                        "text_snippet": cit.text_snippet
                    }
                    for cit in ollama_result.citations
                ],
                "provider": "ollama",
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
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
