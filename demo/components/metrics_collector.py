"""
Metrics Collector - Performance tracking for demo

Collects and aggregates performance metrics from RAG queries
for visualization in the dashboard.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque
from dataclasses import dataclass, asdict
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for a single query."""
    timestamp: datetime
    query: str
    strategy: str
    total_time_ms: float
    embedding_time_ms: float
    retrieval_time_ms: float
    num_results: int
    top_score: Optional[float] = None
    avg_score: Optional[float] = None


class MetricsCollector:
    """
    Collects and aggregates metrics from RAG queries.

    Features:
    - Query-level metrics tracking
    - Strategy performance comparison
    - Time-series data for visualization
    - Statistical aggregations
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector.

        Args:
            max_history: Maximum number of queries to keep in history
        """
        self.max_history = max_history
        self.query_metrics: deque = deque(maxlen=max_history)

        # Strategy-level aggregations
        self.strategy_stats: Dict[str, Dict[str, Any]] = {}

    def record_query(
        self,
        query: str,
        strategy: str,
        performance: Dict[str, float],
        results: List[Any],
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Record metrics for a query.

        Args:
            query: Query text
            strategy: Retrieval strategy used
            performance: Performance dict with timing info
            results: List of retrieval results
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Calculate scores
        top_score = None
        avg_score = None

        if results:
            scores = [r.score for r in results if hasattr(r, 'score')]
            if scores:
                top_score = max(scores)
                avg_score = sum(scores) / len(scores)

        # Create metrics record
        metrics = QueryMetrics(
            timestamp=timestamp,
            query=query,
            strategy=strategy,
            total_time_ms=performance.get('total_ms', 0),
            embedding_time_ms=performance.get('embedding_ms', 0),
            retrieval_time_ms=performance.get('retrieval_ms', 0),
            num_results=len(results),
            top_score=top_score,
            avg_score=avg_score
        )

        # Add to history
        self.query_metrics.append(metrics)

        # Update strategy stats
        self._update_strategy_stats(strategy, metrics)

        logger.debug(f"Recorded metrics for query: {query[:50]}...")

    def _update_strategy_stats(self, strategy: str, metrics: QueryMetrics) -> None:
        """Update aggregated statistics for a strategy."""
        if strategy not in self.strategy_stats:
            self.strategy_stats[strategy] = {
                'total_queries': 0,
                'total_time_ms': 0,
                'total_results': 0,
                'total_score': 0,
                'avg_time_ms': 0,
                'avg_results': 0,
                'avg_score': 0
            }

        stats = self.strategy_stats[strategy]
        stats['total_queries'] += 1
        stats['total_time_ms'] += metrics.total_time_ms
        stats['total_results'] += metrics.num_results

        if metrics.avg_score is not None:
            stats['total_score'] += metrics.avg_score

        # Update averages
        stats['avg_time_ms'] = stats['total_time_ms'] / stats['total_queries']
        stats['avg_results'] = stats['total_results'] / stats['total_queries']

        if metrics.avg_score is not None:
            stats['avg_score'] = stats['total_score'] / stats['total_queries']

    def get_recent_queries(self, limit: int = 10) -> List[QueryMetrics]:
        """Get most recent query metrics."""
        return list(self.query_metrics)[-limit:]

    def get_queries_dataframe(self) -> pd.DataFrame:
        """Get all query metrics as a pandas DataFrame."""
        if not self.query_metrics:
            return pd.DataFrame()

        return pd.DataFrame([asdict(m) for m in self.query_metrics])

    def get_strategy_comparison(self) -> pd.DataFrame:
        """Get comparison of all strategies as DataFrame."""
        if not self.strategy_stats:
            return pd.DataFrame()

        df = pd.DataFrame(self.strategy_stats).T
        df.index.name = 'strategy'
        return df.reset_index()

    def get_time_series_data(
        self,
        metric: str = 'total_time_ms',
        window_size: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get time series data for a specific metric.

        Args:
            metric: Metric name (e.g., 'total_time_ms', 'num_results')
            window_size: Optional rolling window for smoothing

        Returns:
            DataFrame with timestamp and metric columns
        """
        df = self.get_queries_dataframe()

        if df.empty:
            return pd.DataFrame()

        # Select columns
        result = df[['timestamp', metric, 'strategy']].copy()

        # Apply rolling window if requested
        if window_size:
            result[f'{metric}_smoothed'] = (
                result[metric].rolling(window=window_size, min_periods=1).mean()
            )

        return result

    def get_strategy_metrics(self, strategy: str) -> Optional[Dict[str, Any]]:
        """Get aggregated metrics for a specific strategy."""
        return self.strategy_stats.get(strategy)

    def get_latency_breakdown(self) -> Dict[str, float]:
        """
        Get average latency breakdown across all queries.

        Returns:
            Dictionary with average times for each stage
        """
        if not self.query_metrics:
            return {}

        total_embedding = sum(m.embedding_time_ms for m in self.query_metrics)
        total_retrieval = sum(m.retrieval_time_ms for m in self.query_metrics)
        count = len(self.query_metrics)

        return {
            'embedding_ms': total_embedding / count,
            'retrieval_ms': total_retrieval / count,
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get overall performance summary.

        Returns:
            Dictionary with summary statistics
        """
        if not self.query_metrics:
            return {
                'total_queries': 0,
                'avg_time_ms': 0,
                'min_time_ms': 0,
                'max_time_ms': 0,
                'avg_results': 0,
                'strategies_used': 0
            }

        times = [m.total_time_ms for m in self.query_metrics]
        results = [m.num_results for m in self.query_metrics]

        return {
            'total_queries': len(self.query_metrics),
            'avg_time_ms': sum(times) / len(times),
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'avg_results': sum(results) / len(results),
            'strategies_used': len(self.strategy_stats),
            'time_range': {
                'start': min(m.timestamp for m in self.query_metrics),
                'end': max(m.timestamp for m in self.query_metrics)
            }
        }

    def calculate_precision_at_k(
        self,
        results: List[Any],
        relevant_threshold: float = 0.5,
        k: int = 10
    ) -> float:
        """
        Calculate Precision@K for results.

        Args:
            results: List of retrieval results
            relevant_threshold: Score threshold for relevance
            k: Number of top results to consider

        Returns:
            Precision@K value (0-1)
        """
        if not results or k == 0:
            return 0.0

        top_k = results[:k]
        relevant = sum(
            1 for r in top_k
            if hasattr(r, 'score') and r.score >= relevant_threshold
        )

        return relevant / k

    def clear_history(self) -> None:
        """Clear all collected metrics."""
        self.query_metrics.clear()
        self.strategy_stats.clear()
        logger.info("Metrics history cleared")
