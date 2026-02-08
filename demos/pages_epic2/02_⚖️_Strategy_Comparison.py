"""
Strategy Comparison - Side-by-side retrieval strategy analysis

Compare multiple retrieval strategies simultaneously to evaluate:
- Precision and recall characteristics
- Latency differences
- Result overlap and diversity
- Score distributions
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Set

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from demos.components_epic2.rag_engine import RAGEngine, QueryResult

# Page config
st.set_page_config(
    page_title="Strategy Comparison",
    page_icon="⚖️",
    layout="wide"
)


@st.cache_resource
def get_rag_engine():
    """Get cached RAG engine instance."""
    engine = RAGEngine()
    engine.initialize()
    return engine


def calculate_overlap(results1: List, results2: List) -> float:
    """Calculate overlap between two result sets."""
    if not results1 or not results2:
        return 0.0

    docs1 = {r.document.id if hasattr(r.document, 'id') else id(r.document) for r in results1}
    docs2 = {r.document.id if hasattr(r.document, 'id') else id(r.document) for r in results2}

    intersection = len(docs1 & docs2)
    union = len(docs1 | docs2)

    return (intersection / union) if union > 0 else 0.0


def create_comparison_table(results_dict: Dict[str, QueryResult]) -> pd.DataFrame:
    """Create comparison table from results."""
    data = []

    for strategy_name, result in results_dict.items():
        scores = [r.score for r in result.retrieval_results if hasattr(r, 'score')]

        strategy_display = result.metadata.get('strategy_config', strategy_name)

        row = {
            'Strategy': strategy_display,
            'Latency (ms)': f"{result.performance.get('total_ms', 0):.1f}",
            'Results': len(result.documents),
            'Top Score': f"{max(scores):.3f}" if scores else "N/A",
            'Avg Score': f"{sum(scores)/len(scores):.3f}" if scores else "N/A",
            'Min Score': f"{min(scores):.3f}" if scores else "N/A",
        }
        data.append(row)

    return pd.DataFrame(data)


def create_latency_chart(results_dict: Dict[str, QueryResult]) -> go.Figure:
    """Create latency comparison bar chart."""
    strategies = []
    embedding_times = []
    retrieval_times = []
    total_times = []

    for strategy_name, result in results_dict.items():
        strategy_display = result.metadata.get('strategy_config', strategy_name)
        strategies.append(strategy_display)
        embedding_times.append(result.performance.get('embedding_ms', 0))
        retrieval_times.append(result.performance.get('retrieval_ms', 0))
        total_times.append(result.performance.get('total_ms', 0))

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Embedding',
        x=strategies,
        y=embedding_times,
        marker_color='#1f77b4'
    ))

    fig.add_trace(go.Bar(
        name='Retrieval',
        x=strategies,
        y=retrieval_times,
        marker_color='#ff7f0e'
    ))

    fig.update_layout(
        title='Latency Breakdown by Strategy',
        xaxis_title='Strategy',
        yaxis_title='Time (ms)',
        barmode='stack',
        height=400,
        hovermode='x unified'
    )

    return fig


def create_score_distribution_chart(results_dict: Dict[str, QueryResult]) -> go.Figure:
    """Create score distribution violin/box plot."""
    data = []

    for strategy_name, result in results_dict.items():
        strategy_display = result.metadata.get('strategy_config', strategy_name)
        scores = [r.score for r in result.retrieval_results if hasattr(r, 'score')]

        for score in scores:
            data.append({
                'Strategy': strategy_display,
                'Score': score
            })

    df = pd.DataFrame(data)

    if df.empty:
        return go.Figure()

    fig = px.violin(
        df,
        x='Strategy',
        y='Score',
        box=True,
        points='all',
        title='Score Distribution by Strategy',
        height=400
    )

    fig.update_layout(
        yaxis_title='Relevance Score',
        hovermode='closest'
    )

    return fig


def create_precision_at_k_chart(results_dict: Dict[str, QueryResult], threshold: float = 0.5) -> go.Figure:
    """Create Precision@K comparison chart."""
    strategies = []
    k_values = [1, 3, 5, 10]
    precision_data = {k: [] for k in k_values}

    for strategy_name, result in results_dict.items():
        strategy_display = result.metadata.get('strategy_config', strategy_name)
        strategies.append(strategy_display)

        scores = [r.score for r in result.retrieval_results if hasattr(r, 'score')]

        for k in k_values:
            if len(scores) >= k:
                relevant = sum(1 for score in scores[:k] if score >= threshold)
                precision_data[k].append(relevant / k)
            else:
                precision_data[k].append(0)

    fig = go.Figure()

    for k in k_values:
        fig.add_trace(go.Scatter(
            name=f'P@{k}',
            x=strategies,
            y=precision_data[k],
            mode='lines+markers',
            marker=dict(size=10)
        ))

    fig.update_layout(
        title=f'Precision@K Comparison (threshold={threshold})',
        xaxis_title='Strategy',
        yaxis_title='Precision',
        yaxis=dict(range=[0, 1.1]),
        height=400,
        hovermode='x unified'
    )

    return fig


def create_overlap_matrix(results_dict: Dict[str, QueryResult]) -> go.Figure:
    """Create heatmap showing result overlap between strategies."""
    strategies = list(results_dict.keys())
    strategy_displays = [results_dict[s].metadata.get('strategy_config', s) for s in strategies]

    n = len(strategies)
    overlap_matrix = [[0.0] * n for _ in range(n)]

    for i, strat1 in enumerate(strategies):
        for j, strat2 in enumerate(strategies):
            if i == j:
                overlap_matrix[i][j] = 1.0
            else:
                overlap = calculate_overlap(
                    results_dict[strat1].retrieval_results,
                    results_dict[strat2].retrieval_results
                )
                overlap_matrix[i][j] = overlap

    fig = go.Figure(data=go.Heatmap(
        z=overlap_matrix,
        x=strategy_displays,
        y=strategy_displays,
        colorscale='Blues',
        text=[[f'{val:.2f}' for val in row] for row in overlap_matrix],
        texttemplate='%{text}',
        textfont={"size": 12},
        colorbar=dict(title="Overlap")
    ))

    fig.update_layout(
        title='Result Overlap Between Strategies',
        xaxis_title='Strategy',
        yaxis_title='Strategy',
        height=500
    )

    return fig


def main():
    """Main strategy comparison page."""

    st.title("⚖️ Strategy Comparison")
    st.markdown("Compare multiple retrieval strategies side-by-side to analyze performance and quality")

    # Initialize engine
    engine = get_rag_engine()

    # Check health
    health = engine.get_component_health()
    if not health.get('retrievers'):
        st.error("⚠️ Retrievers not initialized. Please check the main page.")
        st.stop()

    st.markdown("---")

    # Query Input
    st.markdown("### Enter Query for Comparison")

    query_text = st.text_input(
        "Query",
        value="What is RISC-V?",
        placeholder="Enter your question here..."
    )

    # Strategy Selection
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Select Strategies to Compare")

        available_strategies = engine.get_available_strategies()
        default_strategies = engine.config.get('demo_settings', {}).get(
            'comparison_strategies',
            available_strategies[:4]
        )

        selected_strategies = st.multiselect(
            "Strategies",
            options=available_strategies,
            default=[s for s in default_strategies if s in available_strategies],
            format_func=lambda x: engine.config['retriever']['strategies'][x]['name'],
            label_visibility="collapsed"
        )

    with col2:
        st.markdown("### Parameters")

        top_k = st.slider(
            "Top-K Results",
            min_value=5,
            max_value=20,
            value=10
        )

        relevance_threshold = st.slider(
            "Relevance Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
            help="Score threshold for Precision@K calculation"
        )

    # Compare Button
    compare_button = st.button("⚖️ Compare Strategies", type="primary", use_container_width=True)

    if compare_button and query_text and selected_strategies:
        with st.spinner(f"Comparing {len(selected_strategies)} strategies..."):
            # Run comparison
            results = engine.compare_strategies(
                query_text=query_text,
                strategies=selected_strategies,
                top_k=top_k
            )

        # Display Results
        st.markdown("---")
        st.markdown("## 📊 Comparison Results")

        # Summary Table
        st.markdown("### Summary Table")
        comparison_df = create_comparison_table(results)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

        # Charts
        st.markdown("---")

        # Latency Comparison
        col1, col2 = st.columns(2)

        with col1:
            st.plotly_chart(
                create_latency_chart(results),
                use_container_width=True
            )

        with col2:
            st.plotly_chart(
                create_score_distribution_chart(results),
                use_container_width=True
            )

        # Precision@K
        st.plotly_chart(
            create_precision_at_k_chart(results, threshold=relevance_threshold),
            use_container_width=True
        )

        # Overlap Analysis
        if len(results) >= 2:
            st.markdown("---")
            st.markdown("### Result Overlap Analysis")

            st.plotly_chart(
                create_overlap_matrix(results),
                use_container_width=True
            )

            # Overlap insights
            st.markdown("**Overlap Insights:**")
            st.markdown("""
            - **High overlap (>0.7):** Strategies retrieve similar documents
            - **Medium overlap (0.3-0.7):** Strategies have partial agreement
            - **Low overlap (<0.3):** Strategies find different relevant documents (diversity)
            """)

        # Detailed Results
        st.markdown("---")
        st.markdown("### Detailed Results by Strategy")

        for strategy_name, result in results.items():
            strategy_display = result.metadata.get('strategy_config', strategy_name)

            with st.expander(f"**{strategy_display}** - {len(result.documents)} results in {result.performance.get('total_ms', 0):.1f}ms"):
                # Top 5 results for this strategy
                st.markdown("**Top 5 Retrieved Documents:**")

                for i, res in enumerate(result.retrieval_results[:5], 1):
                    score = res.score if hasattr(res, 'score') else 0.0
                    source = res.document.metadata.get('source', 'Unknown')
                    preview = res.document.content[:150] + "..."

                    st.markdown(f"""
                    **#{i}** - {source} (score: {score:.3f})
                    > {preview}
                    """)

    elif compare_button and not query_text:
        st.warning("⚠️ Please enter a query")

    elif compare_button and not selected_strategies:
        st.warning("⚠️ Please select at least one strategy")

    # Sidebar
    with st.sidebar:
        st.markdown("### Available Strategies")

        for strategy in engine.get_available_strategies():
            strategy_config = engine.config['retriever']['strategies'][strategy]
            st.markdown(f"**{strategy_config['name']}**")

            # Show brief description based on type
            fusion_type = strategy_config.get('fusion', {}).get('type', 'unknown')
            reranker_enabled = strategy_config.get('reranker', {}).get('config', {}).get('enabled', False)

            st.markdown(f"- Fusion: `{fusion_type}`")
            st.markdown(f"- Reranking: {'✅' if reranker_enabled else '❌'}")

        st.markdown("---")
        st.markdown("### Evaluation Metrics")

        st.markdown("""
        **Precision@K:** Fraction of top-K results above relevance threshold

        **Score Distribution:** Range and variance of relevance scores

        **Latency:** Time breakdown (embedding + retrieval)

        **Overlap:** Jaccard similarity between result sets
        """)


if __name__ == "__main__":
    main()
