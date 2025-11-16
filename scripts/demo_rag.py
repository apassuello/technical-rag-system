#!/usr/bin/env python3
"""
End-to-End RAG System Demo.

This script demonstrates the complete RAG pipeline:
Query → Retrieval → Answer Generation with Citations

Features:
- Natural language queries
- Semantic search with FAISS
- Answer generation with LLM (Ollama or OpenAI)
- Source citations
- Performance metrics

Usage:
    # Interactive mode with Ollama
    python scripts/demo_rag.py --interactive

    # Single query
    python scripts/demo_rag.py --query "What are RISC-V vector instructions?"

    # Use OpenAI instead of Ollama
    python scripts/demo_rag.py --query "..." --use-openai

    # Show retrieved documents
    python scripts/demo_rag.py --query "..." --show-sources

Author: Arthur Passuello
Created: 2025-11-16
"""

import sys
import os
import argparse
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.component_factory import ComponentFactory
from src.core.interfaces import Document
from src.core.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RAGDemo:
    """End-to-end RAG system demonstration."""

    def __init__(
        self,
        indices_dir: Path = None,
        config_path: Path = None,
        use_openai: bool = False,
        top_k: int = 5
    ):
        """
        Initialize RAG demo.

        Args:
            indices_dir: Directory containing indices
            config_path: Path to configuration file
            use_openai: Use OpenAI API instead of Ollama
            top_k: Number of documents to retrieve
        """
        self.indices_dir = indices_dir or project_root / "data" / "indices"
        self.config_path = config_path or project_root / "config" / "default.yaml"
        self.use_openai = use_openai
        self.top_k = top_k

        # Load configuration
        self.config = load_config(self.config_path)

        # Initialize components
        self._load_indices()
        self._initialize_embedder()
        self._initialize_llm()

    def _load_indices(self):
        """Load FAISS index and documents."""
        print("📚 Loading indices...")

        # Load documents
        documents_path = self.indices_dir / "documents.pkl"
        with open(documents_path, 'rb') as f:
            self.documents = pickle.load(f)

        # Load FAISS index
        import faiss
        index_path = self.indices_dir / "faiss_index.bin"
        self.faiss_index = faiss.read_index(str(index_path))

        print(f"   ✓ Loaded {len(self.documents)} documents")
        print(f"   ✓ FAISS index ready ({self.faiss_index.ntotal} vectors)\n")

    def _initialize_embedder(self):
        """Initialize embedder for query encoding."""
        print("🔤 Initializing embedder...")

        factory = ComponentFactory()
        embedder_config = self.config.embedder.model_dump()

        self.embedder = factory.create_embedder(
            embedder_config["type"],
            **embedder_config.get("config", {})
        )

        print("   ✓ Embedder ready\n")

    def _initialize_llm(self):
        """Initialize LLM for answer generation."""
        print("🤖 Initializing LLM...")

        if self.use_openai:
            self._initialize_openai()
        else:
            self._initialize_ollama()

    def _initialize_ollama(self):
        """Initialize Ollama LLM."""
        try:
            import requests

            # Check if Ollama is running
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if models:
                    # Use first available model
                    self.llm_model = models[0]['name']
                    print(f"   ✓ Ollama ready (model: {self.llm_model})\n")
                    self.llm_type = "ollama"
                else:
                    print("   ⚠️  No Ollama models found. Please run: ollama pull llama3.2:3b")
                    print("   ℹ️  Falling back to mock LLM for demo\n")
                    self.llm_type = "mock"
            else:
                raise Exception("Ollama not responding")

        except Exception as e:
            print(f"   ⚠️  Ollama not available: {e}")
            print("   ℹ️  Falling back to mock LLM for demo")
            print("   💡 Install: brew install ollama && ollama pull llama3.2:3b\n")
            self.llm_type = "mock"

    def _initialize_openai(self):
        """Initialize OpenAI LLM."""
        try:
            import openai

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise Exception("OPENAI_API_KEY not set")

            openai.api_key = api_key
            self.llm_type = "openai"
            self.llm_model = "gpt-3.5-turbo"
            print(f"   ✓ OpenAI ready (model: {self.llm_model})\n")

        except Exception as e:
            print(f"   ⚠️  OpenAI not available: {e}")
            print("   ℹ️  Set OPENAI_API_KEY environment variable\n")
            self.llm_type = "mock"

    def retrieve(self, query: str) -> List[Tuple[Document, float]]:
        """
        Retrieve relevant documents for query.

        Args:
            query: Natural language query

        Returns:
            List of (document, score) tuples
        """
        # Generate query embedding
        query_embedding = self.embedder.embed([query])[0]

        # Search FAISS index
        import numpy as np
        query_vec = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.faiss_index.search(query_vec, k=self.top_k)

        # Collect results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                results.append((self.documents[idx], float(distance)))

        return results

    def generate_answer(
        self,
        query: str,
        context_docs: List[Tuple[Document, float]]
    ) -> Dict[str, Any]:
        """
        Generate answer using LLM.

        Args:
            query: User query
            context_docs: Retrieved documents with scores

        Returns:
            Dictionary with answer, sources, and metadata
        """
        # Build context from retrieved documents
        context_parts = []
        sources = []

        for i, (doc, score) in enumerate(context_docs, 1):
            source_name = "Unknown"
            if hasattr(doc, 'metadata') and doc.metadata:
                source = doc.metadata.get('source', 'Unknown')
                if '/' in source or '\\' in source:
                    source_name = Path(source).name
                else:
                    source_name = source

            sources.append({
                'index': i,
                'source': source_name,
                'score': score,
                'content': doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
            })

            context_parts.append(f"[{i}] Source: {source_name}\n{doc.content}\n")

        context = "\n".join(context_parts)

        # Build prompt
        prompt = f"""You are a helpful technical assistant. Answer the question based ONLY on the provided context.
Include citations using [1], [2], etc. to reference sources.

Context:
{context}

Question: {query}

Answer:"""

        # Generate answer
        if self.llm_type == "ollama":
            answer = self._generate_ollama(prompt)
        elif self.llm_type == "openai":
            answer = self._generate_openai(prompt)
        else:
            answer = self._generate_mock(query, context_docs)

        return {
            'answer': answer,
            'sources': sources,
            'num_sources': len(sources),
            'llm_type': self.llm_type
        }

    def _generate_ollama(self, prompt: str) -> str:
        """Generate answer using Ollama."""
        import requests

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()['response']
            else:
                return f"Error generating answer: {response.status_code}"

        except Exception as e:
            return f"Error: {e}"

    def _generate_openai(self, prompt: str) -> str:
        """Generate answer using OpenAI."""
        try:
            import openai

            response = openai.ChatCompletion.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are a helpful technical assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error: {e}"

    def _generate_mock(self, query: str, context_docs: List[Tuple[Document, float]]) -> str:
        """Generate mock answer for demo purposes."""
        top_source = "Unknown"
        if context_docs and hasattr(context_docs[0][0], 'metadata'):
            source = context_docs[0][0].metadata.get('source', 'Unknown')
            if '/' in source or '\\' in source:
                top_source = Path(source).name

        return f"""[Mock LLM Response - Install Ollama for real answers]

Based on the retrieved documents, particularly from {top_source} [1],
I can provide information about: {query}

The top {len(context_docs)} sources retrieved have relevance scores ranging from
{context_docs[0][1]:.2f} to {context_docs[-1][1]:.2f}, indicating good semantic match.

To get real AI-generated answers:
1. Install Ollama: brew install ollama
2. Download a model: ollama pull llama3.2:3b
3. Run this script again

Or use OpenAI: python scripts/demo_rag.py --query "..." --use-openai"""

    def query(self, query_text: str, show_sources: bool = False) -> Dict[str, Any]:
        """
        Execute full RAG pipeline.

        Args:
            query_text: User query
            show_sources: Whether to display retrieved sources

        Returns:
            Complete RAG response with timing
        """
        print("\n" + "=" * 80)
        print(f"🔍 QUERY: {query_text}")
        print("=" * 80)

        # Retrieval
        print("\n📖 Retrieving relevant documents...")
        retrieval_start = time.time()
        retrieved_docs = self.retrieve(query_text)
        retrieval_time = (time.time() - retrieval_start) * 1000

        print(f"   ✓ Retrieved {len(retrieved_docs)} documents ({retrieval_time:.1f}ms)")

        if show_sources:
            print("\n   Top sources:")
            for i, (doc, score) in enumerate(retrieved_docs[:3], 1):
                source = "Unknown"
                if hasattr(doc, 'metadata') and doc.metadata:
                    src = doc.metadata.get('source', 'Unknown')
                    source = Path(src).name if ('/' in src or '\\' in src) else src
                print(f"   [{i}] {source} (score: {score:.3f})")

        # Answer generation
        print("\n💭 Generating answer...")
        generation_start = time.time()
        result = self.generate_answer(query_text, retrieved_docs)
        generation_time = (time.time() - generation_start) * 1000

        print(f"   ✓ Answer generated ({generation_time:.1f}ms)")

        # Display answer
        print("\n" + "─" * 80)
        print("📝 ANSWER:")
        print("─" * 80)
        print(result['answer'])
        print("─" * 80)

        # Display sources
        print(f"\n📚 Sources ({len(result['sources'])}):")
        for source in result['sources']:
            print(f"   [{source['index']}] {source['source']} (relevance: {source['score']:.3f})")

        # Timing summary
        total_time = retrieval_time + generation_time
        print(f"\n⏱️  Timing: Retrieval={retrieval_time:.1f}ms, Generation={generation_time:.1f}ms, Total={total_time:.1f}ms")
        print("=" * 80 + "\n")

        return {
            **result,
            'query': query_text,
            'retrieval_time_ms': retrieval_time,
            'generation_time_ms': generation_time,
            'total_time_ms': total_time
        }

    def interactive_mode(self, show_sources: bool = False):
        """Run interactive RAG demo."""
        print("\n" + "=" * 80)
        print("🚀 INTERACTIVE RAG DEMO")
        print("=" * 80)
        print("\nCommands:")
        print("  - Enter a question to get an AI answer")
        print("  - 'sources' to toggle source display")
        print("  - 'quit' or 'exit' to stop")
        print("=" * 80)

        while True:
            try:
                query = input("\n❓ Question: ").strip()

                if not query:
                    continue

                if query.lower() in ['quit', 'exit', 'q']:
                    print("\nExiting RAG demo...")
                    break

                if query.lower() == 'sources':
                    show_sources = not show_sources
                    print(f"   Source display: {'ON' if show_sources else 'OFF'}")
                    continue

                # Execute query
                self.query(query, show_sources=show_sources)

            except KeyboardInterrupt:
                print("\n\nExiting RAG demo...")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                logger.error(f"Query error: {e}", exc_info=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="End-to-end RAG system demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Interactive mode
    python scripts/demo_rag.py --interactive

    # Single query
    python scripts/demo_rag.py --query "What are RISC-V vector instructions?"

    # Use OpenAI
    python scripts/demo_rag.py --query "..." --use-openai

    # Show retrieved sources
    python scripts/demo_rag.py --query "..." --show-sources
        """
    )

    parser.add_argument(
        '--query',
        type=str,
        help='Query to answer'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )

    parser.add_argument(
        '--use-openai',
        action='store_true',
        help='Use OpenAI API instead of Ollama'
    )

    parser.add_argument(
        '--show-sources',
        action='store_true',
        help='Show retrieved source documents'
    )

    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of documents to retrieve (default: 5)'
    )

    parser.add_argument(
        '--indices-dir',
        type=Path,
        help='Directory containing indices (default: data/indices)'
    )

    args = parser.parse_args()

    try:
        # Initialize RAG system
        rag = RAGDemo(
            indices_dir=args.indices_dir,
            use_openai=args.use_openai,
            top_k=args.top_k
        )

        # Run appropriate mode
        if args.interactive:
            rag.interactive_mode(show_sources=args.show_sources)
        elif args.query:
            rag.query(args.query, show_sources=args.show_sources)
        else:
            parser.print_help()
            print("\n💡 Tip: Try --interactive mode for a conversation-style demo")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Demo failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
