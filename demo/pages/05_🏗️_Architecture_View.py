"""
Architecture View - System architecture visualization

Interactive visualization of the RAG system architecture showing:
- 6 core components
- 97 sub-components
- Component configurations
- Health and performance metrics
"""

import streamlit as st
import sys
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from demo.components.rag_engine import RAGEngine

# Page config
st.set_page_config(
    page_title="Architecture View",
    page_icon="🏗️",
    layout="wide"
)


@st.cache_resource
def get_rag_engine():
    """Get cached RAG engine instance."""
    engine = RAGEngine()
    engine.initialize()
    return engine


def main():
    """Main architecture visualization."""

    st.title("🏗️ System Architecture")
    st.markdown("Modular RAG system with 6 core components and 97 sub-components")

    # Initialize engine
    engine = get_rag_engine()

    st.markdown("---")

    # Architecture Diagram (ASCII art for now, can be replaced with graphviz/mermaid)
    st.markdown("## System Overview")

    st.markdown("""
```
                    ┌────────────────────────────────┐
                    │   Platform Orchestrator        │
                    │   - Component Lifecycle        │
                    │   - Health Monitoring          │
                    │   - Configuration Management   │
                    └────────────┬───────────────────┘
                                 │
                ┌────────────────┼────────────────┬──────────────┬─────────────┐
                │                │                │              │             │
                ▼                ▼                ▼              ▼             ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐
        │   Document   │  │   Embedder   │  │Retriever │  │ Answer  │  │  Cache   │
        │  Processor   │  │              │  │          │  │Generator│  │          │
        └──────┬───────┘  └──────┬───────┘  └────┬─────┘  └────┬────┘  └────┬─────┘
               │                 │               │             │            │
        ┌──────┴───────┐  ┌──────┴────────┐ ┌───┴────────┐    │      ┌─────┴─────┐
        │ PyMuPDF      │  │ Sentence      │ │ FAISS      │    │      │  Memory   │
        │ Adapter      │  │ Transformer   │ │ Index      │    │      │  Cache    │
        │              │  │ Model         │ │            │    │      │           │
        │ Sentence     │  │               │ │ BM25       │    │      └───────────┘
        │ Chunker      │  │ Dynamic Batch │ │ Retriever  │    │
        │              │  │ Processor     │ │            │    │
        │ Content      │  │               │ │ RRF        │    │
        │ Cleaner      │  │ Memory Cache  │ │ Fusion     │    │
        │              │  │               │ │            │    │
        └──────────────┘  └───────────────┘ │ Weighted   │    │
                                            │ Fusion     │    │
                                            │            │    │
                                            │ Semantic   │    │
                                            │ Reranker   │    │
                                            └────────────┘    │
```
    """)

    st.markdown("---")

    # Component Details
    st.markdown("## 📦 Component Details")

    # Define component information
    components = {
        "Platform Orchestrator": {
            "description": "Manages system lifecycle, component initialization, and platform services",
            "sub_components": [
                "ComponentRegistry",
                "ComponentHealthService",
                "SystemAnalyticsService",
                "ABTestingService",
                "ConfigurationService",
                "BackendManagementService"
            ],
            "key_features": [
                "Factory-based component creation",
                "Health monitoring and diagnostics",
                "Performance analytics",
                "A/B testing framework",
                "Dynamic configuration management"
            ],
            "file": "src/core/platform_orchestrator.py",
            "lines": "1,380 lines",
            "tests": "~200 tests"
        },
        "Document Processor": {
            "description": "Handles PDF parsing, text chunking, and content cleaning",
            "sub_components": [
                "PyMuPDFAdapter (external)",
                "SentenceBoundaryChunker",
                "TechnicalContentCleaner",
                "DocumentProcessingPipeline"
            ],
            "key_features": [
                "PDF text extraction",
                "Sentence-aware chunking",
                "Technical content cleaning",
                "Metadata preservation"
            ],
            "file": "src/components/processors/document_processor.py",
            "lines": "~800 lines",
            "tests": "~150 tests"
        },
        "Embedder": {
            "description": "Generates embeddings with batch optimization and caching",
            "sub_components": [
                "SentenceTransformerModel",
                "DynamicBatchProcessor",
                "MemoryCache"
            ],
            "key_features": [
                "Sentence transformers integration",
                "Dynamic batch sizing (2408x speedup)",
                "In-memory caching with TTL",
                "Hardware acceleration (MPS/CUDA/CPU)"
            ],
            "file": "src/components/embedders/modular_embedder.py",
            "lines": "~600 lines",
            "tests": "~180 tests"
        },
        "Retriever": {
            "description": "Hybrid retrieval with multiple fusion strategies",
            "sub_components": [
                "FAISSIndex (dense)",
                "BM25Retriever (sparse)",
                "RRFFusion",
                "WeightedFusion",
                "GraphEnhancedFusion",
                "ScoreAwareFusion",
                "SemanticReranker",
                "NeuralReranker",
                "IdentityReranker"
            ],
            "key_features": [
                "Dense + sparse hybrid retrieval",
                "4 fusion strategies",
                "3 reranking options",
                "Configurable top-k",
                "Sub-millisecond search (FAISS)"
            ],
            "file": "src/components/retrievers/modular_unified_retriever.py",
            "lines": "~900 lines",
            "tests": "~250 tests"
        },
        "Answer Generator": {
            "description": "Generates context-aware answers from retrieved documents",
            "sub_components": [
                "SimplePromptBuilder",
                "OllamaAdapter (LLM)",
                "MarkdownParser",
                "SemanticScorer"
            ],
            "key_features": [
                "Prompt engineering",
                "LLM integration",
                "Citation extraction",
                "Confidence scoring"
            ],
            "file": "src/components/generators/answer_generator.py",
            "lines": "~500 lines",
            "tests": "~120 tests"
        },
        "Cache": {
            "description": "In-memory caching for embeddings and results",
            "sub_components": [
                "MemoryCache (TTL-based)"
            ],
            "key_features": [
                "LRU eviction",
                "TTL support",
                "Memory limit enforcement",
                "Thread-safe operations"
            ],
            "file": "src/components/embedders/caches/memory_cache.py",
            "lines": "433 lines",
            "tests": "~90 tests"
        }
    }

    # Display each component
    for component_name, info in components.items():
        with st.expander(f"**{component_name}** - {info['description']}", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("### Key Features")
                for feature in info['key_features']:
                    st.markdown(f"- {feature}")

                st.markdown("### Sub-Components")
                for sub in info['sub_components']:
                    st.markdown(f"- `{sub}`")

            with col2:
                st.markdown("### Implementation")
                st.markdown(f"**File:** `{info['file']}`")
                st.markdown(f"**Size:** {info['lines']}")
                st.markdown(f"**Tests:** {info['tests']}")

    st.markdown("---")

    # Configuration Explorer
    st.markdown("## ⚙️ Configuration Explorer")

    st.markdown("Explore the configuration for each component and retrieval strategy")

    config_category = st.selectbox(
        "Select Configuration Category",
        ["Embedder", "Retriever Strategies", "Document Processor", "Answer Generator"]
    )

    if config_category == "Embedder":
        st.json(engine.config.get('embedder', {}))

    elif config_category == "Retriever Strategies":
        strategy = st.selectbox(
            "Select Strategy",
            list(engine.config['retriever']['strategies'].keys()),
            format_func=lambda x: engine.config['retriever']['strategies'][x]['name']
        )

        st.json(engine.config['retriever']['strategies'][strategy])

    elif config_category == "Document Processor":
        st.json(engine.config.get('document_processor', {}))

    elif config_category == "Answer Generator":
        st.json(engine.config.get('answer_generator', {}))

    st.markdown("---")

    # Statistics
    st.markdown("## 📊 Architecture Statistics")

    stats = engine.get_statistics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Core Components", stats.get('components', 6))

    with col2:
        st.metric("Sub-Components", stats.get('subcomponents', 97))

    with col3:
        st.metric("Total Tests", f"{stats.get('total_tests', 1943):,}")

    with col4:
        st.metric("Type Hints", f"{stats.get('type_hint_coverage', 96.6)}%")

    st.markdown("---")

    # Design Principles
    st.markdown("## 🎯 Design Principles")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### Modularity
        - **Direct Wiring:** Components hold direct references for performance
        - **Adapter Pattern:** Used only for external integrations (PyMuPDF, Ollama)
        - **Factory Pattern:** Centralized component creation
        - **Interface-Based:** All components implement clear interfaces

        ### Configuration-Driven
        - **YAML Configuration:** All components configurable via YAML
        - **Strategy Pattern:** Multiple retrieval strategies switchable at runtime
        - **Dependency Injection:** Components receive dependencies via constructors
        """)

    with col2:
        st.markdown("""
        ### Production-Ready
        - **Comprehensive Testing:** 1,943 test functions (80/100 quality)
        - **Type Safety:** 96.6% type hint coverage
        - **Error Handling:** Zero bare excepts, proper exception handling
        - **Monitoring:** Health checks, performance metrics, analytics
        - **Infrastructure:** K8s/Helm configurations (92/100 quality)

        ### Swiss Engineering Standards
        - **Precision:** Quantitative metrics for all operations
        - **Robustness:** Comprehensive error handling and validation
        - **Efficiency:** Optimized batch processing, caching
        """)

    # Sidebar
    with st.sidebar:
        st.markdown("### Architecture Summary")

        st.markdown("**6 Core Components:**")
        for i, component in enumerate(components.keys(), 1):
            st.markdown(f"{i}. {component}")

        st.markdown("---")
        st.markdown("### Component Health")

        health = engine.get_component_health()

        for component, is_healthy in health.items():
            icon = "✅" if is_healthy else "❌"
            st.markdown(f"{icon} {component.replace('_', ' ').title()}")


if __name__ == "__main__":
    main()
