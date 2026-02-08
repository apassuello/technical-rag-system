"""
Query Interface - Interactive RAG Q&A

Interactive query interface with real-time retrieval, citations,
and performance metrics.
"""

import streamlit as st
import sys
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from demos.components_epic2.rag_engine import RAGEngine
from demos.components_epic2.metrics_collector import MetricsCollector

# Page config
st.set_page_config(
    page_title="Query Interface",
    page_icon="🔍",
    layout="wide"
)


@st.cache_resource
def get_rag_engine():
    """Get cached RAG engine instance."""
    engine = RAGEngine()
    engine.initialize()
    return engine


@st.cache_resource
def get_metrics_collector():
    """Get cached metrics collector instance."""
    return MetricsCollector()


def display_retrieval_result(result, rank: int):
    """Display a single retrieval result."""
    score = result.score if hasattr(result, 'score') else 0.0
    doc = result.document

    # Score visualization
    stars = "⭐" * int(score * 5)
    score_pct = f"{score * 100:.1f}%"

    with st.expander(f"**#{rank}** - {doc.metadata.get('source', 'Unknown')} ({score_pct}) {stars}"):
        col1, col2 = st.columns([3, 1])

        with col1:
            # Document preview
            preview = doc.content[:500]
            if len(doc.content) > 500:
                preview += "..."

            st.markdown(f"**Content Preview:**")
            st.text(preview)

        with col2:
            # Metadata
            st.markdown("**Metadata:**")
            st.markdown(f"**Score:** {score:.4f}")

            if 'page' in doc.metadata:
                st.markdown(f"**Page:** {doc.metadata['page']}")

            if 'chunk_id' in doc.metadata:
                st.markdown(f"**Chunk:** {doc.metadata['chunk_id']}")

            st.markdown(f"**Length:** {len(doc.content)} chars")


def main():
    """Main query interface."""

    st.title("🔍 Query Interface")
    st.markdown("Interactive RAG query system with real-time retrieval and citations")

    # Initialize components
    engine = get_rag_engine()
    metrics = get_metrics_collector()

    # Check if engine initialized successfully
    health = engine.get_component_health()
    if not health.get('embedder') or not health.get('retrievers'):
        st.error("⚠️ RAG Engine not fully initialized. Please check the main page.")
        st.stop()

    st.markdown("---")

    # Query Configuration
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### Configuration")

        # Get available strategies
        strategies = engine.get_available_strategies()
        strategy_names = {s: engine.config['retriever']['strategies'][s]['name'] for s in strategies}

        selected_strategy = st.selectbox(
            "Retrieval Strategy",
            options=strategies,
            format_func=lambda x: strategy_names.get(x, x),
            help="Choose the retrieval strategy to use"
        )

    with col2:
        st.markdown("### Parameters")

        # Check if Epic1 is available
        has_epic1 = health.get('query_analyzer', False)
        has_answer_gen = health.get('answer_generator', False)

        use_epic1 = st.checkbox(
            "🧠 Use Epic1 Classification",
            value=has_epic1,
            disabled=not has_epic1,
            help="Use ML-based query classification for intelligent routing"
        )

        if use_epic1:
            top_k = None  # Will use Epic1 suggestion
            st.info("Top-K will be determined by query complexity")
        else:
            top_k = st.slider(
                "Top-K Results",
                min_value=1,
                max_value=20,
                value=10,
                help="Number of documents to retrieve"
            )

    st.markdown("---")

    # Query Input
    st.markdown("### Ask Your Question")

    col1, col2 = st.columns([5, 1])

    with col1:
        query_text = st.text_input(
            "Query",
            placeholder="e.g., What is RISC-V?",
            label_visibility="collapsed"
        )

    with col2:
        search_button = st.button("🔍 Search", use_container_width=True, type="primary")

    # Sample queries
    sample_queries = engine.config.get('demo_settings', {}).get('sample_queries', [])
    if sample_queries:
        st.markdown("**Quick Test Queries:**")
        cols = st.columns(len(sample_queries))
        for i, sample in enumerate(sample_queries):
            with cols[i]:
                if st.button(f"📝 {sample[:30]}...", key=f"sample_{i}", use_container_width=True):
                    query_text = sample
                    search_button = True

    # Execute Query
    if search_button and query_text:
        with st.spinner(f"Searching with {strategy_names[selected_strategy]}..."):
            # Execute query with or without Epic1 classification
            start_time = time.time()

            if use_epic1:
                # Use Epic1 classification and answer generation
                result_dict = engine.query_with_classification(
                    query_text=query_text,
                    strategy=selected_strategy,
                    top_k=top_k,
                    use_recommended_model=True
                )

                # Convert to QueryResult format for compatibility
                from demos.components_epic2.rag_engine import QueryResult
                result = QueryResult(
                    query=query_text,
                    answer=result_dict.get('answer'),
                    documents=result_dict.get('documents', []),
                    retrieval_results=result_dict.get('retrieval_results', []),
                    performance=result_dict.get('performance', {}),
                    strategy=selected_strategy,
                    metadata=result_dict.get('metadata', {})
                )

                # Store Epic1 analysis for display
                query_analysis = result_dict.get('query_analysis')
            else:
                # Standard query without Epic1
                result = engine.query(
                    query_text=query_text,
                    strategy=selected_strategy,
                    top_k=top_k if top_k else 10,
                    generate_answer=False
                )
                query_analysis = None

            query_time = (time.time() - start_time) * 1000

            # Record metrics
            metrics.record_query(
                query=query_text,
                strategy=selected_strategy,
                performance=result.performance,
                results=result.retrieval_results
            )

        # Display Results
        st.markdown("---")

        # Epic1 Query Analysis (if available)
        if query_analysis:
            st.markdown("### 🧠 Query Analysis (Epic1)")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                complexity = query_analysis.get('complexity_level', 'unknown')
                color_map = {'simple': 'green', 'medium': 'orange', 'complex': 'red'}
                color = color_map.get(complexity, 'gray')
                st.markdown(f"**Complexity:** :{color}[{complexity.upper()}]")
                score = query_analysis.get('complexity_score', 0.0)
                st.caption(f"Score: {score:.2f}")

            with col2:
                model = query_analysis.get('recommended_model', 'default')
                st.markdown(f"**Recommended Model:**")
                st.code(model, language=None)

            with col3:
                routing_conf = query_analysis.get('routing_confidence', 0.0)
                st.metric("Routing Confidence", f"{routing_conf:.2%}")

            with col4:
                suggested_k = query_analysis.get('suggested_k', 5)
                st.metric("Suggested Top-K", suggested_k)

            # Additional metadata in expander
            with st.expander("📊 Full Analysis Details"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Intent & Features:**")
                    st.markdown(f"- **Intent:** {query_analysis.get('intent_category', 'unknown')}")

                    technical_terms = query_analysis.get('technical_terms', [])
                    if technical_terms:
                        st.markdown(f"- **Technical Terms:** {', '.join(technical_terms[:5])}")

                    entities = query_analysis.get('entities', [])
                    if entities:
                        st.markdown(f"- **Entities:** {', '.join(entities[:5])}")

                with col2:
                    st.markdown("**Cost & Performance:**")
                    st.markdown(f"- **Cost Estimate:** ${query_analysis.get('cost_estimate', 0.0):.6f}")
                    st.markdown(f"- **Latency Estimate:** {query_analysis.get('latency_estimate', 0.0):.0f}ms")
                    st.markdown(f"- **Complexity Confidence:** {query_analysis.get('complexity_confidence', 0.0):.2%}")

            st.markdown("---")

        # Performance Metrics
        st.markdown("### ⏱️ Performance Metrics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Time",
                f"{result.performance.get('total_ms', 0):.1f} ms"
            )

        with col2:
            st.metric(
                "Embedding",
                f"{result.performance.get('embedding_ms', 0):.1f} ms"
            )

        with col3:
            st.metric(
                "Retrieval",
                f"{result.performance.get('retrieval_ms', 0):.1f} ms"
            )

        with col4:
            st.metric(
                "Results",
                f"{len(result.documents)}"
            )

        # Generated Answer (from Epic1 or fallback)
        if result.answer:
            st.markdown("---")
            st.markdown("### ✨ Generated Answer")

            # Display answer with confidence
            st.markdown(result.answer)

            # Show answer metadata
            if hasattr(result, 'metadata') and 'answer_confidence' in result.metadata:
                col1, col2, col3 = st.columns(3)
                with col1:
                    conf = result.metadata.get('answer_confidence', 0.0)
                    st.metric("Answer Confidence", f"{conf:.2%}")
                with col2:
                    gen_time = result.performance.get('generation_ms', 0)
                    st.metric("Generation Time", f"{gen_time:.0f}ms")
                with col3:
                    num_docs = len(result.documents)
                    st.metric("Context Documents", num_docs)

            # Answer metadata expander
            if hasattr(result, 'metadata') and 'answer_metadata' in result.metadata:
                with st.expander("📋 Answer Generation Details"):
                    answer_meta = result.metadata['answer_metadata']
                    st.json(answer_meta)

        # Retrieved Documents
        st.markdown("---")
        st.markdown(f"### 📚 Retrieved Documents ({len(result.documents)})")

        if not result.documents:
            st.warning("No documents retrieved. Try a different query or strategy.")
        else:
            # Display score distribution
            scores = [r.score for r in result.retrieval_results if hasattr(r, 'score')]

            if scores:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Top Score", f"{max(scores):.4f}")

                with col2:
                    st.metric("Average Score", f"{sum(scores)/len(scores):.4f}")

                with col3:
                    st.metric("Min Score", f"{min(scores):.4f}")

            st.markdown("---")

            # Display results
            for i, result_item in enumerate(result.retrieval_results, 1):
                display_retrieval_result(result_item, i)

        # Query History
        st.markdown("---")
        st.markdown("### 📜 Recent Queries")

        recent = metrics.get_recent_queries(limit=5)

        if recent:
            for i, qm in enumerate(reversed(recent), 1):
                st.markdown(
                    f"**{i}.** {qm.query[:80]}... "
                    f"({qm.strategy}, {qm.total_time_ms:.0f}ms, {qm.num_results} results)"
                )
        else:
            st.info("No query history yet. Run a query to see history.")

    elif search_button and not query_text:
        st.warning("⚠️ Please enter a query")

    # Sidebar with stats
    with st.sidebar:
        st.markdown("### Strategy Info")

        if selected_strategy in engine.config['retriever']['strategies']:
            strategy_config = engine.config['retriever']['strategies'][selected_strategy]
            st.markdown(f"**Name:** {strategy_config['name']}")

            # Show configuration details
            with st.expander("Configuration Details"):
                st.json(strategy_config)

        st.markdown("---")
        st.markdown("### Session Stats")

        stats = engine.get_statistics()
        st.metric("Total Queries", stats.get('total_queries', 0))
        st.metric("Documents Indexed", f"{stats.get('total_documents', 0):,}")
        st.metric("Available Strategies", len(strategies))

        # Performance summary
        perf_summary = metrics.get_performance_summary()
        if perf_summary['total_queries'] > 0:
            st.markdown("---")
            st.markdown("### Performance")
            st.metric("Avg Query Time", f"{perf_summary['avg_time_ms']:.0f} ms")
            st.metric("Avg Results", f"{perf_summary['avg_results']:.1f}")


if __name__ == "__main__":
    main()
