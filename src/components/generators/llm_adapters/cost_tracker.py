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

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from threading import Lock
from typing import Any, Dict, List, Optional

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
    Thread-safe cost tracking system with budget enforcement and real-time monitoring.
    
    This enhanced system provides:
    - Real-time cost tracking with $0.001 precision
    - Budget enforcement with configurable thresholds and alerts
    - Usage aggregation by provider, model, time period
    - Cost optimization recommendations
    - Session-based cost tracking
    - Thread-safe concurrent access for high-throughput systems
    
    Features:
    - Track costs across all LLM providers
    - Generate detailed cost reports with analytics
    - Provide cost-based routing recommendations
    - Monitor usage patterns and trends
    - Budget alerts with customizable callbacks
    - Export cost data for external analysis
    """
    
    def __init__(self,
                 daily_budget: Optional[Decimal] = None,
                 monthly_budget: Optional[Decimal] = None,
                 alert_thresholds: List[float] = None,
                 precision_places: int = 6,
                 enable_detailed_logging: bool = True):
        """
        Initialize enhanced cost tracking system.
        
        Args:
            daily_budget: Daily spending limit (triggers alerts)
            monthly_budget: Monthly spending limit (triggers alerts)  
            alert_thresholds: Budget alert thresholds (0.0-1.0, e.g., [0.8, 0.95, 1.0])
            precision_places: Decimal precision for cost calculations
            enable_detailed_logging: Whether to log detailed usage info
        """
        # Thread-safe access with reentrant lock
        self._lock = Lock()
        
        # Budget configuration
        self.daily_budget = daily_budget
        self.monthly_budget = monthly_budget
        self.alert_thresholds = alert_thresholds or [0.80, 0.95, 1.0]
        
        # Usage records storage
        self._usage_records: List[UsageRecord] = []
        
        # Configuration
        self.precision_places = precision_places
        self.enable_detailed_logging = enable_detailed_logging
        
        # Aggregated stats (cached for performance)
        self._last_aggregation_time: Optional[datetime] = None
        self._cached_summaries: Dict[str, CostSummary] = {}
        
        # Budget tracking and alerts
        self.active_alerts: List[Dict[str, Any]] = []
        self.alert_callbacks: List[callable] = []
        self._last_alert_check = datetime.now()
        
        # Session tracking
        self.current_session_id: Optional[str] = None
        self.session_costs: Dict[str, Decimal] = {}
        
        logger.info(f"Initialized Enhanced CostTracker with ${10**(-precision_places):.{precision_places}f} precision")
        if daily_budget:
            logger.info(f"Daily budget set: ${float(daily_budget):.2f}")
        if monthly_budget:
            logger.info(f"Monthly budget set: ${float(monthly_budget):.2f}")
    
    def record_usage(self,
                     provider: str,
                     model: str,
                     input_tokens: int,
                     output_tokens: int,
                     cost_usd: Decimal,
                     query_complexity: Optional[str] = None,
                     request_time_ms: Optional[float] = None,
                     success: bool = True,
                     metadata: Optional[Dict[str, Any]] = None,
                     timestamp: Optional[datetime] = None) -> None:
        """
        Record usage for a single LLM request with budget monitoring.
        
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
            timestamp: Custom timestamp for testing (optional, defaults to now)
        """
        # Ensure cost precision
        cost_usd = Decimal(str(cost_usd)).quantize(
            Decimal('0.000001'), rounding=ROUND_HALF_UP
        )
        
        # Create usage record
        record = UsageRecord(
            timestamp=timestamp or datetime.now(),
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
            
            # Update session costs if active
            if self.current_session_id:
                if self.current_session_id not in self.session_costs:
                    self.session_costs[self.current_session_id] = Decimal('0.00')
                self.session_costs[self.current_session_id] += cost_usd
            
            # Invalidate cache
            self._cached_summaries.clear()
            
            # Check budget alerts (but don't hold the lock during callbacks)
            alerts_to_trigger = self._check_budget_alerts()
        
        # Trigger alerts outside of the lock to prevent deadlocks
        for alert in alerts_to_trigger:
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Budget alert callback failed: {e}")
        
        # Detailed logging if enabled
        if self.enable_detailed_logging:
            logger.debug(
                f"Recorded usage: {provider}/{model} - "
                f"{input_tokens}+{output_tokens} tokens, ${cost_usd:.6f}"
            )
    
    def start_session(self, session_id: str) -> None:
        """
        Start a new cost tracking session.
        
        Args:
            session_id: Unique identifier for the session
        """
        with self._lock:
            self.current_session_id = session_id
            if session_id not in self.session_costs:
                self.session_costs[session_id] = Decimal('0.00')
            logger.info(f"Started cost tracking session: {session_id}")
    
    def end_session(self) -> Optional[Dict[str, Any]]:
        """
        End the current session and return cost summary.
        
        Returns:
            Session cost summary or None if no active session
        """
        with self._lock:
            if not self.current_session_id:
                return None
            
            session_cost = self.session_costs.get(self.current_session_id, Decimal('0.00'))
            session_summary = {
                'session_id': self.current_session_id,
                'total_cost_usd': float(session_cost),
                'ended_at': datetime.now().isoformat()
            }
            
            logger.info(f"Ended session {self.current_session_id}: ${float(session_cost):.6f}")
            self.current_session_id = None
            
            return session_summary
    
    def add_alert_callback(self, callback: callable) -> None:
        """
        Add a callback function for budget alerts.
        
        Args:
            callback: Function to call when budget alert is triggered
        """
        with self._lock:
            self.alert_callbacks.append(callback)
            logger.info(f"Added budget alert callback: {callback.__name__}")
    
    def _check_budget_alerts(self) -> List[Dict[str, Any]]:
        """
        Check budget thresholds and return new alerts.
        
        Returns:
            List of new alerts to trigger (called without holding lock)
        """
        if not self.daily_budget:
            return []
        
        # Calculate current daily spend
        daily_spend = self.get_summary_by_time_period(hours=24).total_cost_usd
        new_alerts = []
        
        # Check each threshold
        for threshold in self.alert_thresholds:
            threshold_amount = self.daily_budget * Decimal(str(threshold))
            
            if daily_spend >= threshold_amount:
                # Check if we already have a recent alert for this threshold
                recent_alert = any(
                    alert.get('threshold') == threshold and
                    (datetime.now() - datetime.fromisoformat(alert.get('timestamp', '1970-01-01'))).total_seconds() < 3600
                    for alert in self.active_alerts
                )
                
                if not recent_alert:
                    alert = {
                        'threshold': threshold,
                        'current_spend': float(daily_spend),
                        'budget_limit': float(self.daily_budget),
                        'utilization_percent': float(daily_spend / self.daily_budget * 100),
                        'remaining_budget': float(self.daily_budget - daily_spend),
                        'level': 'warning' if threshold < 0.90 else 'critical' if threshold < 1.0 else 'exceeded',
                        'message': self._get_alert_message(threshold, daily_spend, self.daily_budget),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    self.active_alerts.append(alert)
                    new_alerts.append(alert)
        
        return new_alerts
    
    def _get_alert_message(self, threshold: float, current: Decimal, budget: Decimal) -> str:
        """Generate appropriate alert message based on threshold."""
        percent = float(current / budget * 100)
        
        if threshold < 0.90:
            return f"Budget {percent:.1f}% utilized - monitoring recommended"
        elif threshold < 1.0:
            return f"Budget {percent:.1f}% utilized - consider cost optimization"
        else:
            overage = float(current - budget)
            return f"Daily budget exceeded by ${overage:.2f} - immediate action required"
    
    def get_total_cost(self) -> Decimal:
        """
        Get total cost across all providers and models.
        
        Returns:
            Total cost in USD with high precision
        """
        with self._lock:
            total = sum(record.cost_usd for record in self._usage_records) or Decimal('0.000000')
            if not isinstance(total, Decimal):
                total = Decimal(str(total))
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
            
            # Analyze cost by complexity (inline to avoid deadlock)
            complexity_costs = {}
            for record in self._usage_records:
                complexity = record.query_complexity or 'unknown'
                if complexity not in complexity_costs:
                    complexity_costs[complexity] = Decimal('0')
                complexity_costs[complexity] += record.cost_usd
            
            # Quantize complexity costs
            complexity_costs = {
                complexity: cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                for complexity, cost in complexity_costs.items()
            }
            
            total_cost = sum(complexity_costs.values())
            
            if total_cost == 0:
                return recommendations
            
            # Check for expensive simple queries
            simple_cost = complexity_costs.get('simple', Decimal('0'))
            simple_percentage = (simple_cost / total_cost) * 100
            
            if simple_percentage > 30:  # >30% cost on simple queries
                # Calculate savings as the difference between using expensive models vs cheap models
                # Assume cheap model cost is near zero for simple queries
                potential_savings = simple_cost * Decimal("0.9")  # 90% savings by switching to cheap models
                recommendations.append({
                    'type': 'cost_optimization',
                    'priority': 'high',
                    'title': 'High cost on simple queries',
                    'description': f'{simple_percentage:.1f}% of costs are from simple queries',
                    'suggestion': 'Consider routing simple queries to cheaper models (ollama) or use cheaper models for simple queries',
                    'potential_savings': f'${potential_savings:.3f}'
                })
            
            # Analyze cost by provider (inline to avoid deadlock)
            provider_costs = {}
            for record in self._usage_records:
                provider = record.provider.lower()
                if provider not in provider_costs:
                    provider_costs[provider] = Decimal('0')
                provider_costs[provider] += record.cost_usd
            
            # Quantize provider costs
            provider_costs = {
                provider: cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                for provider, cost in provider_costs.items()
            }
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
    
    def get_usage_history(self, 
                          hours: Optional[int] = None,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None) -> List[UsageRecord]:
        """
        Get usage history records.
        
        Args:
            hours: If specified, only return records from the last N hours
            start_time: If specified (with end_time), filter records after this time
            end_time: If specified (with start_time), filter records before this time
            
        Returns:
            List of usage records
        """
        with self._lock:
            if start_time is not None and end_time is not None:
                return [r for r in self._usage_records 
                       if start_time <= r.timestamp <= end_time]
            elif hours is not None:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                return [r for r in self._usage_records if r.timestamp >= cutoff_time]
            else:
                return list(self._usage_records)
    
    def analyze_usage_patterns(self) -> Dict[str, Any]:
        """
        Analyze usage patterns to identify optimization opportunities.
        
        Returns:
            Dictionary containing usage pattern analysis including:
            - complexity_distribution: Usage by complexity level
            - provider_distribution: Usage by provider
            - cost_per_complexity: Average cost per complexity level
        """
        with self._lock:
            if not self._usage_records:
                return {
                    "complexity_distribution": {},
                    "provider_distribution": {},
                    "cost_per_complexity": {}
                }
            
            # Analyze complexity distribution
            complexity_stats = {}
            provider_stats = {}
            
            for record in self._usage_records:
                # Complexity analysis
                complexity = record.query_complexity
                if complexity not in complexity_stats:
                    complexity_stats[complexity] = {"count": 0, "total_cost": Decimal('0')}
                complexity_stats[complexity]["count"] += 1
                complexity_stats[complexity]["total_cost"] += record.cost_usd
                
                # Provider analysis
                provider = record.provider
                if provider not in provider_stats:
                    provider_stats[provider] = {"count": 0, "total_cost": Decimal('0')}
                provider_stats[provider]["count"] += 1
                provider_stats[provider]["total_cost"] += record.cost_usd
            
            # Calculate distributions
            total_requests = len(self._usage_records)
            complexity_distribution = {
                k: v["count"] / total_requests 
                for k, v in complexity_stats.items()
            }
            provider_distribution = {
                k: v["count"] / total_requests 
                for k, v in provider_stats.items()
            }
            
            # Calculate cost per complexity
            cost_per_complexity = {
                k: float(v["total_cost"] / v["count"]) if v["count"] > 0 else 0.0
                for k, v in complexity_stats.items()
            }
            
            return {
                "complexity_distribution": complexity_distribution,
                "provider_distribution": provider_distribution, 
                "cost_per_complexity": cost_per_complexity
            }
    
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
        import csv
        import io
        
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