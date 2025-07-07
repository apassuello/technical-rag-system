"""
Enhanced RAG system with integrated answer generation.

This module extends BasicRAG to include answer generation capabilities
using local LLMs via Ollama, with specialized prompt templates for
technical documentation.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Generator
import sys

# Import from same directory
from .basic_rag import BasicRAG

# Import from shared utils - Support HF API, Ollama, and Inference Providers
from shared_utils.generation.hf_answer_generator import (
    HuggingFaceAnswerGenerator,
    GeneratedAnswer,
)
from shared_utils.generation.ollama_answer_generator import OllamaAnswerGenerator
from shared_utils.generation.inference_providers_generator import (
    InferenceProvidersGenerator,
)
from shared_utils.generation.prompt_templates import TechnicalPromptTemplates
from shared_utils.generation.adaptive_prompt_engine import AdaptivePromptEngine
from shared_utils.generation.chain_of_thought_engine import ChainOfThoughtEngine


class RAGWithGeneration(BasicRAG):
    """
    Extended RAG system with answer generation capabilities.

    Combines hybrid search with LLM-based answer generation,
    optimized for technical documentation Q&A.
    """

    def __init__(
        self,
        model_name: str = "sshleifer/distilbart-cnn-12-6",
        api_token: str = None,
        temperature: float = 0.3,
        max_tokens: int = 512,
        use_ollama: bool = False,
        ollama_url: str = "http://localhost:11434",
        use_inference_providers: bool = False,
        enable_adaptive_prompts: bool = True,
        enable_chain_of_thought: bool = True,
    ):
        """
        Initialize RAG with generation capabilities.

        Args:
            model_name: Model for generation (HF model or Ollama model)
            api_token: HF API token (for HF models only)
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            use_ollama: If True, use local Ollama instead of HuggingFace API
            ollama_url: Ollama server URL (if using Ollama)
            use_inference_providers: If True, use new Inference Providers API
            enable_adaptive_prompts: If True, use context-aware prompt adaptation
            enable_chain_of_thought: If True, enable multi-step reasoning for complex queries
        """
        super().__init__()

        # Choose generator based on configuration with fallback chain
        if use_inference_providers:
            # Try new Inference Providers API first
            print(
                f"🚀 Trying HuggingFace Inference Providers API...",
                file=sys.stderr,
                flush=True,
            )
            try:
                self.answer_generator = InferenceProvidersGenerator(
                    model_name=None,  # Let it auto-select best available model
                    api_token=api_token,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                print(
                    f"✅ Inference Providers API connected successfully",
                    file=sys.stderr,
                    flush=True,
                )
                self._using_ollama = False
                self._using_inference_providers = True
            except Exception as e:
                print(
                    f"❌ Inference Providers failed: {e}", file=sys.stderr, flush=True
                )
                print(
                    f"🔄 Falling back to classic HuggingFace API...",
                    file=sys.stderr,
                    flush=True,
                )
                # Fallback to classic HF API
                self.answer_generator = HuggingFaceAnswerGenerator(
                    model_name=model_name,
                    api_token=api_token,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                print(f"✅ HuggingFace classic API ready", file=sys.stderr, flush=True)
                self._using_ollama = False
                self._using_inference_providers = False
        elif use_ollama:
            print(
                f"🦙 Trying local Ollama server at {ollama_url}...",
                file=sys.stderr,
                flush=True,
            )
            try:
                self.answer_generator = OllamaAnswerGenerator(
                    model_name=model_name,
                    base_url=ollama_url,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                print(
                    f"✅ Ollama connected successfully with {model_name}",
                    file=sys.stderr,
                    flush=True,
                )
                self._using_ollama = True
                self._using_inference_providers = False
            except Exception as e:
                print(f"❌ Ollama failed: {e}", file=sys.stderr, flush=True)
                print(
                    f"🔄 Falling back to HuggingFace API...",
                    file=sys.stderr,
                    flush=True,
                )
                # Fallback to HuggingFace
                hf_model = "sshleifer/distilbart-cnn-12-6"
                self.answer_generator = HuggingFaceAnswerGenerator(
                    model_name=hf_model,
                    api_token=api_token,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                print(
                    f"✅ HuggingFace fallback ready with {hf_model}",
                    file=sys.stderr,
                    flush=True,
                )
                self._using_ollama = False
                self._using_inference_providers = False
        else:
            print("🤗 Using HuggingFace classic API...", file=sys.stderr, flush=True)
            self.answer_generator = HuggingFaceAnswerGenerator(
                model_name=model_name,
                api_token=api_token,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            self._using_ollama = False
            self._using_inference_providers = False

        # Initialize prompt engineering components
        self.prompt_templates = TechnicalPromptTemplates()
        self.adaptive_engine = (
            AdaptivePromptEngine() if enable_adaptive_prompts else None
        )
        self.cot_engine = ChainOfThoughtEngine() if enable_chain_of_thought else None
        self.enable_adaptive_prompts = enable_adaptive_prompts
        self.enable_chain_of_thought = enable_chain_of_thought
        self.enable_streaming = (
            False  # HF API doesn't support streaming in this implementation
        )

    def get_generator_info(self) -> Dict[str, str]:
        """Get information about the current answer generator."""
        return {
            "using_ollama": getattr(self, "_using_ollama", False),
            "using_inference_providers": getattr(
                self, "_using_inference_providers", False
            ),
            "generator_type": type(self.answer_generator).__name__,
            "model_name": getattr(self.answer_generator, "model_name", "unknown"),
            "base_url": getattr(self.answer_generator, "base_url", None),
        }

    def query_with_answer(
        self,
        question: str,
        top_k: int = 5,
        use_hybrid: bool = True,
        dense_weight: float = 0.7,
        use_fallback_llm: bool = False,
        return_context: bool = False,
        similarity_threshold: float = 0.3,
    ) -> Dict:
        """
        Query the system and generate a complete answer.

        Args:
            question: User's question
            top_k: Number of chunks to retrieve
            use_hybrid: Whether to use hybrid search (vs basic semantic)
            dense_weight: Weight for dense retrieval in hybrid search
            use_fallback_llm: Whether to use fallback LLM model
            return_context: Whether to include retrieved chunks in response
            similarity_threshold: Minimum similarity score to include results (0.3 = 30%)

        Returns:
            Dict containing:
                - answer: Generated answer text
                - citations: List of citations with sources
                - confidence: Confidence score
                - sources: List of unique source documents
                - retrieval_stats: Statistics from retrieval
                - generation_stats: Statistics from generation
                - context (optional): Retrieved chunks if requested
        """
        start_time = time.time()

        # Debug: Show which generator is being used
        generator_info = self.get_generator_info()
        print(
            f"🔧 Debug: Using {generator_info['generator_type']} (Ollama: {generator_info['using_ollama']}) with model {generator_info['model_name']}",
            file=sys.stderr,
            flush=True,
        )

        # Step 1: Retrieve relevant chunks
        if use_hybrid and self.hybrid_retriever is not None:
            retrieval_result = self.hybrid_query(question, top_k, dense_weight)
        else:
            retrieval_result = self.query(question, top_k)

        retrieval_time = time.time() - start_time

        # Step 2: Generate answer using retrieved chunks
        chunks = retrieval_result.get("chunks", [])

        if not chunks:
            return {
                "answer": "I couldn't find relevant information in the documentation to answer your question.",
                "citations": [],
                "confidence": 0.0,
                "sources": [],
                "retrieval_stats": {
                    "method": retrieval_result.get("retrieval_method", "none"),
                    "chunks_retrieved": 0,
                    "retrieval_time": retrieval_time,
                },
                "generation_stats": {"model": "none", "generation_time": 0.0},
            }

        # Prepare chunks for answer generator
        formatted_chunks = []
        for chunk in chunks:
            formatted_chunk = {
                "id": f"chunk_{chunk.get('chunk_id', 0)}",
                "content": chunk.get("text", ""),
                "metadata": {
                    "page_number": chunk.get("page", 0),
                    "source": Path(chunk.get("source", "unknown")).name,
                    "quality_score": chunk.get("quality_score", 0.0),
                },
                "score": chunk.get("hybrid_score", chunk.get("similarity_score", 0.0)),
            }
            formatted_chunks.append(formatted_chunk)

        # Generate answer using enhanced prompt engineering
        generation_start = time.time()

        # Use adaptive prompt engineering if enabled
        if self.enable_adaptive_prompts and self.adaptive_engine:
            generated_answer = self._generate_with_adaptive_prompts(
                question=question, chunks=formatted_chunks
            )
        else:
            # Use standard generation
            generated_answer = self.answer_generator.generate(
                query=question, chunks=formatted_chunks
            )

        generation_time = time.time() - generation_start

        # Prepare response
        response = {
            "answer": generated_answer.answer,
            "citations": [
                {
                    "source": citation.source_file,
                    "page": citation.page_number,
                    "relevance": citation.relevance_score,
                    "snippet": citation.text_snippet,
                }
                for citation in generated_answer.citations
            ],
            "confidence": generated_answer.confidence_score,
            "sources": list(set(chunk.get("source", "unknown") for chunk in chunks)),
            "retrieval_stats": {
                "method": retrieval_result.get("retrieval_method", "semantic"),
                "chunks_retrieved": len(chunks),
                "retrieval_time": retrieval_time,
                "dense_weight": retrieval_result.get("dense_weight", 1.0),
                "sparse_weight": retrieval_result.get("sparse_weight", 0.0),
            },
            "generation_stats": {
                "model": generated_answer.model_used,
                "generation_time": generation_time,
                "total_time": time.time() - start_time,
            },
        }

        # Optionally include context
        if return_context:
            response["context"] = chunks

        return response

    def _generate_with_adaptive_prompts(
        self, question: str, chunks: List[Dict]
    ) -> "GeneratedAnswer":
        """
        Generate answer using adaptive prompt engineering.

        Args:
            question: User's question
            chunks: Retrieved context chunks

        Returns:
            GeneratedAnswer with adaptive prompt enhancement
        """
        # Convert chunks to adaptive engine format
        adaptive_chunks = []
        for chunk in chunks:
            adaptive_chunks.append(
                {
                    "content": chunk.get("content", ""),
                    "metadata": chunk.get("metadata", {}),
                    "confidence": chunk.get("score", 0.5),
                }
            )

        # Generate adaptive configuration
        config = self.adaptive_engine.generate_adaptive_config(
            query=question, context_chunks=adaptive_chunks, prefer_speed=False
        )

        # Create adaptive prompt
        if (
            self.enable_chain_of_thought
            and self.cot_engine
            and config.enable_chain_of_thought
        ):
            # Use chain-of-thought for complex queries
            query_type = self.prompt_templates.detect_query_type(question)
            base_template = self.prompt_templates.get_template_for_query(question)

            # Format context for CoT
            context = self._format_context_for_prompt(adaptive_chunks)

            # Generate CoT prompt
            enhanced_prompt = self.cot_engine.generate_chain_of_thought_prompt(
                query=question,
                query_type=query_type,
                context=context,
                base_template=base_template,
            )

            # Use the enhanced prompt with the answer generator
            return self.answer_generator.generate_with_custom_prompt(
                query=question, chunks=chunks, custom_prompt=enhanced_prompt
            )
        else:
            # Use adaptive prompt without CoT
            adaptive_prompt = self.adaptive_engine.create_adaptive_prompt(
                query=question, context_chunks=adaptive_chunks, config=config
            )

            # Use the adaptive prompt with the answer generator
            return self.answer_generator.generate_with_custom_prompt(
                query=question, chunks=chunks, custom_prompt=adaptive_prompt
            )

    def _format_context_for_prompt(self, chunks: List[Dict]) -> str:
        """Format chunks for prompt context."""
        if not chunks:
            return "No relevant context available."

        context_parts = []
        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            page_num = metadata.get("page_number", "unknown")
            source = metadata.get("source", "unknown")

            context_parts.append(
                f"[chunk_{i+1}] (Page {page_num} from {source}):\n{content}"
            )

        return "\n\n---\n\n".join(context_parts)

    def query_with_answer_stream(
        self,
        question: str,
        top_k: int = 5,
        use_hybrid: bool = True,
        dense_weight: float = 0.7,
        use_fallback_llm: bool = False,
    ) -> Generator[Union[str, Dict], None, None]:
        """
        Query the system and stream the answer generation.

        Args:
            question: User's question
            top_k: Number of chunks to retrieve
            use_hybrid: Whether to use hybrid search
            dense_weight: Weight for dense retrieval
            use_fallback_llm: Whether to use fallback LLM

        Yields:
            Partial answer strings during generation

        Returns:
            Final complete response dict (after generator exhaustion)
        """
        if not self.enable_streaming:
            # Fall back to non-streaming if disabled
            result = self.query_with_answer(
                question, top_k, use_hybrid, dense_weight, use_fallback_llm
            )
            yield result["answer"]
            yield result
            return

        start_time = time.time()

        # Step 1: Retrieve relevant chunks
        if use_hybrid and self.hybrid_retriever is not None:
            retrieval_result = self.hybrid_query(question, top_k, dense_weight)
        else:
            retrieval_result = self.query(question, top_k)

        retrieval_time = time.time() - start_time

        # Step 2: Stream answer generation
        chunks = retrieval_result.get("chunks", [])

        if not chunks:
            yield "I couldn't find relevant information in the documentation to answer your question."
            yield {
                "answer": "I couldn't find relevant information in the documentation to answer your question.",
                "citations": [],
                "confidence": 0.0,
                "sources": [],
                "retrieval_stats": {
                    "chunks_retrieved": 0,
                    "retrieval_time": retrieval_time,
                },
            }
            return

        # Prepare chunks
        formatted_chunks = []
        for chunk in chunks:
            formatted_chunk = {
                "id": f"chunk_{chunk.get('chunk_id', 0)}",
                "content": chunk.get("text", ""),
                "metadata": {
                    "page_number": chunk.get("page", 0),
                    "source": Path(chunk.get("source", "unknown")).name,
                    "quality_score": chunk.get("quality_score", 0.0),
                },
                "score": chunk.get("hybrid_score", chunk.get("similarity_score", 0.0)),
            }
            formatted_chunks.append(formatted_chunk)

        # Stream generation
        generation_start = time.time()
        stream_generator = self.answer_generator.generate_stream(
            query=question, chunks=formatted_chunks, use_fallback=use_fallback_llm
        )

        # Stream partial results
        for partial in stream_generator:
            if isinstance(partial, str):
                yield partial
            elif isinstance(partial, GeneratedAnswer):
                # Final result
                generation_time = time.time() - generation_start

                final_response = {
                    "answer": partial.answer,
                    "citations": [
                        {
                            "source": citation.source_file,
                            "page": citation.page_number,
                            "relevance": citation.relevance_score,
                            "snippet": citation.text_snippet,
                        }
                        for citation in partial.citations
                    ],
                    "confidence": partial.confidence_score,
                    "sources": list(
                        set(chunk.get("source", "unknown") for chunk in chunks)
                    ),
                    "retrieval_stats": {
                        "method": retrieval_result.get("retrieval_method", "semantic"),
                        "chunks_retrieved": len(chunks),
                        "retrieval_time": retrieval_time,
                    },
                    "generation_stats": {
                        "model": partial.model_used,
                        "generation_time": generation_time,
                        "total_time": time.time() - start_time,
                    },
                }

                yield final_response

    def get_formatted_answer(self, response: Dict) -> str:
        """
        Format a query response for display.

        Args:
            response: Response dict from query_with_answer

        Returns:
            Formatted string for display
        """
        formatted = f"**Answer:**\n{response['answer']}\n\n"

        if response["citations"]:
            formatted += "**Sources:**\n"
            for i, citation in enumerate(response["citations"], 1):
                formatted += f"{i}. {citation['source']} (Page {citation['page']})\n"

        formatted += f"\n*Confidence: {response['confidence']:.1%} | "
        formatted += f"Model: {response['generation_stats']['model']} | "
        formatted += f"Time: {response['generation_stats']['total_time']:.2f}s*"

        return formatted


# Example usage
if __name__ == "__main__":
    # Initialize RAG with generation
    rag = RAGWithGeneration()

    # Example query (would need indexed documents first)
    question = "What is RISC-V and what are its main features?"

    print("Initializing system...")
    print(f"Primary model: llama3.2:3b")
    print(f"Fallback model: mistral:latest")

    # Note: This would only work after indexing documents
    # Example of how to use:
    # rag.index_document(Path("path/to/document.pdf"))
    # result = rag.query_with_answer(question)
    # print(rag.get_formatted_answer(result))
