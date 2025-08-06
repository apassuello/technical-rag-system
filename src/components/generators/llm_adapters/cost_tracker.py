"""
Cost Tracking System for Multi-Model LLM Usage.

This module provides comprehensive cost tracking and analysis for the Epic 1
multi-model answer generation system, enabling precise financial monitoring
and optimization across all LLM providers.

Architecture Notes:
- Centralized cost tracking for all LLM adapters
- Real-time cost calculation with $0.001 precision
- Provider-agnostic cost aggregation and reporting
- Support for cost optimization recommendations
- Thread-safe for concurrent usage tracking

Epic 1 Integration:
- Enables 40%+ cost reduction validation
- Provides cost-based routing decisions
- Tracks ROI of intelligent query routing
- Supports cost budgeting and alerts
"""

import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
import json

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """
    Individual usage record for a single LLM request.
    
    Attributes:
        timestamp: When the request was made
        provider: LLM provider (openai, mistral, ollama)
        model: Specific model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cost_usd: Total cost in USD for this request
        query_complexity: Complexity level (simple, medium, complex)
        request_time_ms: Request duration in milliseconds
        success: Whether the request was successful
    """
    timestamp: datetime
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    query_complexity: Optional[str] = None
    request_time_ms: Optional[float] = None
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostSummary:
    """
    Cost summary for a provider, model, or time period.
    
    Attributes:
        total_requests: Total number of requests
        total_input_tokens: Total input tokens used
        total_output_tokens: Total output tokens used
        total_cost_usd: Total cost in USD
        avg_cost_per_request: Average cost per request
        avg_request_time_ms: Average request time
        success_rate: Percentage of successful requests
    """
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: Decimal
    avg_cost_per_request: Decimal
    avg_request_time_ms: Optional[float] = None
    success_rate: float = 1.0
    
    @property
    def total_tokens(self) -> int:
        """Total tokens (input + output)."""
        return self.total_input_tokens + self.total_output_tokens


class CostTracker:
    """
    Centralized cost tracking system for multi-model LLM usage.
    
    This system provides:
    - Real-time cost tracking with $0.001 precision
    - Usage aggregation by provider, model, time period
    - Cost optimization recommendations
    - Budget monitoring and alerts
    - Thread-safe concurrent access
    
    Features:
    - Track costs across all LLM providers
    - Generate detailed cost reports
    - Provide cost-based routing recommendations
    - Monitor usage patterns and trends
    - Export cost data for analysis
    """
    
    def __init__(self,
                 precision_places: int = 6,
                 enable_detailed_logging: bool = True):
        """
        Initialize cost tracking system.
        
        Args:
            precision_places: Decimal precision for cost calculations
            enable_detailed_logging: Whether to log detailed usage info
        """
        # Thread-safe access
        self._lock = Lock()
        
        # Usage records storage
        self._usage_records: List[UsageRecord] = []
        
        # Configuration
        self.precision_places = precision_places
        self.enable_detailed_logging = enable_detailed_logging
        
        # Aggregated stats (cached for performance)
        self._last_aggregation_time: Optional[datetime] = None
        self._cached_summaries: Dict[str, CostSummary] = {}
        
        logger.info(f"Initialized CostTracker with ${10**(-precision_places):.{precision_places}f} precision")
    
    def record_usage(self,
                     provider: str,
                     model: str,
                     input_tokens: int,
                     output_tokens: int,
                     cost_usd: Decimal,
                     query_complexity: Optional[str] = None,
                     request_time_ms: Optional[float] = None,
                     success: bool = True,
                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record usage for a single LLM request.
        
        Args:
            provider: LLM provider name
            model: Specific model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost_usd: Total cost in USD
            query_complexity: Query complexity level (optional)
            request_time_ms: Request duration in ms (optional)
            success: Whether request was successful
            metadata: Additional metadata (optional)
        """
        # Ensure cost precision
        cost_usd = Decimal(str(cost_usd)).quantize(
            Decimal('0.000001'), rounding=ROUND_HALF_UP
        )
        
        # Create usage record
        record = UsageRecord(
            timestamp=datetime.now(),
            provider=provider.lower(),
            model=model.lower(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            query_complexity=query_complexity,
            request_time_ms=request_time_ms,
            success=success,
            metadata=metadata or {}
        )
        
        # Thread-safe recording
        with self._lock:
            self._usage_records.append(record)
            # Invalidate cache
            self._cached_summaries.clear()
        
        # Detailed logging if enabled
        if self.enable_detailed_logging:
            logger.debug(
                f"Recorded usage: {provider}/{model} - "
                f"{input_tokens}+{output_tokens} tokens, ${cost_usd:.6f}"
            )
    
    def get_total_cost(self) -> Decimal:
        """
        Get total cost across all providers and models.
        
        Returns:
            Total cost in USD with high precision
        """
        with self._lock:
            total = sum(record.cost_usd for record in self._usage_records)
            return total.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
    
    def get_cost_by_provider(self) -> Dict[str, Decimal]:
        """
        Get cost breakdown by provider.
        
        Returns:
            Dictionary mapping provider names to total costs
        """
        with self._lock:
            costs = {}
            for record in self._usage_records:
                provider = record.provider
                if provider not in costs:
                    costs[provider] = Decimal('0')
                costs[provider] += record.cost_usd
            
            # Ensure precision
            return {
                provider: cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                for provider, cost in costs.items()
            }
    
    def get_cost_by_model(self) -> Dict[str, Decimal]:
        """
        Get cost breakdown by model.
        
        Returns:
            Dictionary mapping model names to total costs
        """
        with self._lock:
            costs = {}
            for record in self._usage_records:
                model_key = f"{record.provider}/{record.model}"
                if model_key not in costs:
                    costs[model_key] = Decimal('0')
                costs[model_key] += record.cost_usd
            
            return {
                model: cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                for model, cost in costs.items()
            }
    
    def get_cost_by_complexity(self) -> Dict[str, Decimal]:
        """
        Get cost breakdown by query complexity level.
        
        Returns:
            Dictionary mapping complexity levels to total costs
        """
        with self._lock:
            costs = {}
            for record in self._usage_records:
                complexity = record.query_complexity or 'unknown'
                if complexity not in costs:
                    costs[complexity] = Decimal('0')
                costs[complexity] += record.cost_usd
            
            return {
                complexity: cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                for complexity, cost in costs.items()
            }
    
    def get_summary_by_provider(self, provider: str) -> Optional[CostSummary]:
        """
        Get detailed summary for a specific provider.
        
        Args:
            provider: Provider name to summarize
            
        Returns:
            CostSummary object or None if no records found
        """
        with self._lock:
            records = [r for r in self._usage_records if r.provider == provider.lower()]
            if not records:
                return None
            
            return self._calculate_summary(records)
    
    def get_summary_by_model(self, provider: str, model: str) -> Optional[CostSummary]:
        """
        Get detailed summary for a specific model.
        
        Args:
            provider: Provider name
            model: Model name
            
        Returns:
            CostSummary object or None if no records found
        """
        with self._lock:
            records = [
                r for r in self._usage_records 
                if r.provider == provider.lower() and r.model == model.lower()
            ]
            if not records:
                return None
            
            return self._calculate_summary(records)
    
    def get_summary_by_time_period(self, hours: int = 24) -> CostSummary:
        """
        Get summary for the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            CostSummary for the specified time period
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            records = [r for r in self._usage_records if r.timestamp >= cutoff_time]
            if not records:
                return CostSummary(0, 0, 0, Decimal('0'), Decimal('0'))
            
            return self._calculate_summary(records)
    
    def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate cost optimization recommendations based on usage patterns.
        
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        with self._lock:
            if not self._usage_records:
                return recommendations
            
            # Analyze cost by complexity
            complexity_costs = self.get_cost_by_complexity()
            total_cost = sum(complexity_costs.values())
            
            if total_cost == 0:
                return recommendations
            
            # Check for expensive simple queries
            simple_cost = complexity_costs.get('simple', Decimal('0'))
            simple_percentage = (simple_cost / total_cost) * 100
            
            if simple_percentage > 30:  # >30% cost on simple queries
                recommendations.append({
                    'type': 'cost_optimization',
                    'priority': 'high',
                    'title': 'High cost on simple queries',
                    'description': f'{simple_percentage:.1f}% of costs are from simple queries',
                    'suggestion': 'Consider using cheaper models (ollama) for simple queries',
                    'potential_savings': f'${(simple_cost * Decimal("0.8")):.3f}'
                })
            
            # Check for high-cost providers
            provider_costs = self.get_cost_by_provider()
            for provider, cost in provider_costs.items():
                percentage = (cost / total_cost) * 100
                if percentage > 60 and provider in ['openai']:  # High-cost provider
                    recommendations.append({
                        'type': 'provider_optimization',
                        'priority': 'medium',
                        'title': f'High usage of expensive provider: {provider}',
                        'description': f'{percentage:.1f}% of costs from {provider}',
                        'suggestion': 'Consider routing medium queries to Mistral',
                        'potential_savings': f'${(cost * Decimal("0.4")):.3f}'
                    })
        
        return recommendations
    
    def export_usage_data(self,
                          format_type: str = 'json',
                          include_metadata: bool = False) -> str:
        """
        Export usage data in specified format.
        
        Args:
            format_type: Export format ('json', 'csv')
            include_metadata: Whether to include metadata fields
            
        Returns:
            Formatted usage data as string
        """
        with self._lock:
            if format_type == 'json':
                return self._export_json(include_metadata)
            elif format_type == 'csv':
                return self._export_csv(include_metadata)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
    
    def clear_usage_data(self, older_than_hours: Optional[int] = None) -> int:
        """
        Clear usage data, optionally keeping recent records.
        
        Args:
            older_than_hours: Only clear records older than N hours
            
        Returns:
            Number of records cleared
        """
        with self._lock:
            initial_count = len(self._usage_records)
            
            if older_than_hours is None:
                # Clear all records
                self._usage_records.clear()
                cleared_count = initial_count
            else:
                # Clear only old records
                cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
                self._usage_records = [
                    r for r in self._usage_records 
                    if r.timestamp >= cutoff_time
                ]
                cleared_count = initial_count - len(self._usage_records)
            
            # Clear cache
            self._cached_summaries.clear()
            
        logger.info(f"Cleared {cleared_count} usage records")
        return cleared_count
    
    def _calculate_summary(self, records: List[UsageRecord]) -> CostSummary:
        """Calculate summary statistics for a list of records."""
        if not records:
            return CostSummary(0, 0, 0, Decimal('0'), Decimal('0'))
        
        total_requests = len(records)
        total_input_tokens = sum(r.input_tokens for r in records)
        total_output_tokens = sum(r.output_tokens for r in records)
        total_cost = sum(r.cost_usd for r in records)
        
        avg_cost = total_cost / total_requests if total_requests > 0 else Decimal('0')
        
        # Calculate average request time if available
        request_times = [r.request_time_ms for r in records if r.request_time_ms is not None]
        avg_request_time = sum(request_times) / len(request_times) if request_times else None
        
        # Calculate success rate
        successful_requests = sum(1 for r in records if r.success)
        success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
        
        return CostSummary(
            total_requests=total_requests,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_cost_usd=total_cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP),
            avg_cost_per_request=avg_cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP),
            avg_request_time_ms=avg_request_time,
            success_rate=success_rate
        )
    
    def _export_json(self, include_metadata: bool) -> str:
        """Export usage data as JSON."""
        data = []
        for record in self._usage_records:
            record_dict = {
                'timestamp': record.timestamp.isoformat(),
                'provider': record.provider,
                'model': record.model,
                'input_tokens': record.input_tokens,
                'output_tokens': record.output_tokens,
                'cost_usd': str(record.cost_usd),
                'query_complexity': record.query_complexity,
                'request_time_ms': record.request_time_ms,
                'success': record.success
            }
            
            if include_metadata:
                record_dict['metadata'] = record.metadata
            
            data.append(record_dict)
        
        return json.dumps(data, indent=2)
    
    def _export_csv(self, include_metadata: bool) -> str:
        """Export usage data as CSV."""
        import io
        import csv
        
        output = io.StringIO()
        
        # Headers
        headers = [
            'timestamp', 'provider', 'model', 'input_tokens', 'output_tokens',
            'cost_usd', 'query_complexity', 'request_time_ms', 'success'
        ]
        
        if include_metadata:
            headers.append('metadata')
        
        writer = csv.writer(output)
        writer.writerow(headers)
        
        # Data rows
        for record in self._usage_records:
            row = [
                record.timestamp.isoformat(),
                record.provider,
                record.model,
                record.input_tokens,
                record.output_tokens,
                str(record.cost_usd),
                record.query_complexity,
                record.request_time_ms,
                record.success
            ]
            
            if include_metadata:
                row.append(json.dumps(record.metadata) if record.metadata else '')
            
            writer.writerow(row)
        
        return output.getvalue()


# Global cost tracker instance
_global_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """
    Get the global cost tracker instance.
    
    Returns:
        Global CostTracker instance
    """
    global _global_cost_tracker
    if _global_cost_tracker is None:
        _global_cost_tracker = CostTracker()
    return _global_cost_tracker


def record_llm_usage(provider: str,
                     model: str,
                     input_tokens: int,
                     output_tokens: int,
                     cost_usd: Decimal,
                     query_complexity: Optional[str] = None,
                     request_time_ms: Optional[float] = None,
                     success: bool = True,
                     metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Convenience function to record LLM usage in the global tracker.
    
    Args:
        provider: LLM provider name
        model: Specific model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cost_usd: Total cost in USD
        query_complexity: Query complexity level (optional)
        request_time_ms: Request duration in ms (optional)
        success: Whether request was successful
        metadata: Additional metadata (optional)
    """
    tracker = get_cost_tracker()
    tracker.record_usage(
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        query_complexity=query_complexity,
        request_time_ms=request_time_ms,
        success=success,
        metadata=metadata
    )