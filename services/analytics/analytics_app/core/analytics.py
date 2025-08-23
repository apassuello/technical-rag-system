"""
Analytics Service Core Implementation.

This module implements the main AnalyticsService class that orchestrates
cost tracking, performance analytics, and usage trend analysis for Epic 8.

Features:
- Epic 1 CostTracker integration with $0.001 precision
- Real-time performance monitoring and SLO tracking
- Usage pattern analysis and optimization recommendations
- A/B testing framework support
- Circuit breaker pattern for resilience
- Comprehensive health monitoring
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
import logging

import structlog
from pybreaker import CircuitBreaker

from .config import get_settings, get_circuit_breaker_config
from .cost_tracker import get_analytics_cost_tracker, AnalyticsCostTracker
from .metrics_store import get_metrics_store, MetricsStore, QueryMetric

logger = structlog.get_logger(__name__)


class AnalyticsService:
    """
    Main Analytics Service implementation.
    
    This service provides comprehensive analytics capabilities including:
    - Cost tracking with Epic 1 CostTracker integration
    - Performance monitoring and SLO compliance
    - Usage trend analysis and pattern recognition
    - Cost optimization recommendations
    - A/B testing framework support
    - Real-time and historical analytics
    
    The service is designed to be resilient with circuit breaker patterns
    and comprehensive error handling.
    """
    
    def __init__(self):
        """Initialize the Analytics Service."""
        self.settings = get_settings()
        
        # Initialize components
        self.cost_tracker: AnalyticsCostTracker = get_analytics_cost_tracker()
        self.metrics_store: MetricsStore = get_metrics_store()
        
        # Circuit breaker for resilience
        self.circuit_breaker = None
        if self.settings.circuit_breaker_enabled:
            cb_config = get_circuit_breaker_config()
            self.circuit_breaker = CircuitBreaker(
                fail_max=cb_config["failure_threshold"],
                reset_timeout=cb_config["recovery_timeout"]
            )
        
        # Service state
        self._start_time = datetime.now()
        self._initialized = True
        
        logger.info(
            "Initialized AnalyticsService",
            cost_tracking_enabled=self.settings.enable_cost_tracking,
            performance_tracking_enabled=self.settings.enable_performance_tracking,
            circuit_breaker_enabled=self.settings.circuit_breaker_enabled,
            metrics_retention_hours=self.settings.metrics_retention_hours
        )
    
    async def record_query_completion(self,
                                     query_id: str,
                                     query: str,
                                     complexity: str,
                                     provider: str,
                                     model: str,
                                     cost_usd: float,
                                     processing_time_ms: float,
                                     response_time_ms: float,
                                     input_tokens: int = 0,
                                     output_tokens: int = 0,
                                     success: bool = True,
                                     error_type: Optional[str] = None,
                                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record completion of a query across all analytics systems.
        
        This method records the query in both the cost tracker (Epic 1 integration)
        and the metrics store for comprehensive analytics.
        
        Args:
            query_id: Unique identifier for the query
            query: The query text (for analysis)
            complexity: Query complexity level (simple/medium/complex)
            provider: LLM provider used (e.g., "openai", "mistral", "ollama")
            model: Specific model used (e.g., "gpt-4", "llama3.2:3b")
            cost_usd: Cost in USD
            processing_time_ms: Total processing time in milliseconds
            response_time_ms: Response generation time in milliseconds
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            success: Whether the query was successful
            error_type: Type of error if unsuccessful
            metadata: Additional metadata
        """
        try:
            # Record in cost tracker (Epic 1 integration)
            if self.settings.enable_cost_tracking:
                cost_decimal = Decimal(str(cost_usd))
                await self.cost_tracker.record_query_cost(
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost_decimal,
                    query_complexity=complexity,
                    request_time_ms=response_time_ms,
                    request_id=query_id,
                    success=success,
                    metadata=metadata
                )
            
            # Record in metrics store for performance analytics
            if self.settings.enable_performance_tracking:
                metric = QueryMetric(
                    timestamp=datetime.now(),
                    query_id=query_id,
                    query=query if len(query) <= 1000 else query[:1000],  # Limit query length
                    complexity=complexity,
                    provider=provider,
                    model=model,
                    cost_usd=cost_usd,
                    processing_time_ms=processing_time_ms,
                    response_time_ms=response_time_ms,
                    success=success,
                    error_type=error_type,
                    metadata=metadata or {}
                )
                
                await self.metrics_store.record_query_metric(metric)
            
            logger.debug(
                "Recorded query completion",
                query_id=query_id,
                complexity=complexity,
                provider=provider,
                model=model,
                success=success,
                cost=cost_usd
            )
            
        except Exception as e:
            logger.error(
                "Failed to record query completion",
                error=str(e),
                query_id=query_id,
                provider=provider,
                model=model
            )
            raise
    
    async def get_cost_report(self, 
                             time_range_hours: int = 24,
                             include_recommendations: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive cost report.
        
        Args:
            time_range_hours: Time range for the report in hours
            include_recommendations: Whether to include optimization recommendations
            
        Returns:
            Comprehensive cost report
        """
        try:
            if self.circuit_breaker:
                return self.circuit_breaker(self._get_cost_report_impl)(
                    time_range_hours, include_recommendations
                )
            else:
                return await self._get_cost_report_impl(time_range_hours, include_recommendations)
                
        except Exception as e:
            logger.error("Failed to get cost report", error=str(e))
            raise
    
    async def _get_cost_report_impl(self, time_range_hours: int, include_recommendations: bool) -> Dict[str, Any]:
        """Implementation of cost report generation."""
        if not self.settings.enable_cost_tracking:
            return {
                "error": "Cost tracking is disabled",
                "cost_tracking_enabled": False
            }
        
        # Get cost summary from Epic 1 CostTracker
        cost_summary = await self.cost_tracker.get_cost_summary(time_range_hours)
        
        # Get performance metrics for correlation
        performance_metrics = None
        if self.settings.enable_performance_tracking:
            perf_metrics = await self.metrics_store.get_performance_metrics(time_range_hours)
            performance_metrics = {
                "total_requests": perf_metrics.total_requests,
                "avg_response_time_ms": perf_metrics.avg_response_time_ms,
                "error_rate": perf_metrics.error_rate,
                "slo_compliance": perf_metrics.slo_compliance
            }
        
        # Build comprehensive report
        report = {
            "report_type": "cost_analysis",
            "time_range_hours": time_range_hours,
            "generated_at": datetime.now().isoformat(),
            "cost_summary": cost_summary,
            "performance_correlation": performance_metrics,
            "epic1_integration": True
        }
        
        # Add optimization recommendations if requested
        if include_recommendations:
            optimization_report = await self.cost_tracker.get_cost_optimization_report(time_range_hours)
            report["optimization"] = optimization_report
        
        # Add budget status
        budget_status = await self.cost_tracker.get_budget_status()
        report["budget_status"] = budget_status
        
        logger.debug("Generated cost report", 
                    time_range_hours=time_range_hours,
                    total_cost=cost_summary.get("total_cost_usd", 0),
                    recommendations_included=include_recommendations)
        
        return report
    
    async def get_performance_report(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Args:
            time_range_hours: Time range for the report in hours
            
        Returns:
            Comprehensive performance report
        """
        try:
            if self.circuit_breaker:
                return self.circuit_breaker(self._get_performance_report_impl)(time_range_hours)
            else:
                return await self._get_performance_report_impl(time_range_hours)
                
        except Exception as e:
            logger.error("Failed to get performance report", error=str(e))
            raise
    
    async def _get_performance_report_impl(self, time_range_hours: int) -> Dict[str, Any]:
        """Implementation of performance report generation."""
        if not self.settings.enable_performance_tracking:
            return {
                "error": "Performance tracking is disabled",
                "performance_tracking_enabled": False
            }
        
        # Get performance metrics
        perf_metrics = await self.metrics_store.get_performance_metrics(time_range_hours)
        
        # Get complexity analysis
        complexity_analysis = await self.metrics_store.get_complexity_analysis(time_range_hours)
        
        # Get provider analysis
        provider_analysis = await self.metrics_store.get_provider_analysis(time_range_hours)
        
        # Calculate SLO compliance details
        slo_status = {
            "response_time_slo": self.settings.slo_response_time_ms,
            "error_rate_slo": self.settings.slo_error_rate_threshold,
            "availability_slo": self.settings.slo_availability_threshold,
            "current_compliance": perf_metrics.slo_compliance,
            "response_time_compliant": perf_metrics.avg_response_time_ms <= self.settings.slo_response_time_ms,
            "error_rate_compliant": perf_metrics.error_rate <= self.settings.slo_error_rate_threshold,
            "availability_compliant": (perf_metrics.successful_requests / perf_metrics.total_requests) >= self.settings.slo_availability_threshold if perf_metrics.total_requests > 0 else True
        }
        
        # Performance recommendations
        recommendations = []
        
        if perf_metrics.avg_response_time_ms > self.settings.slo_response_time_ms:
            recommendations.append({
                "type": "performance",
                "priority": "high",
                "title": "Response time SLO violation",
                "description": f"Average response time ({perf_metrics.avg_response_time_ms:.0f}ms) exceeds SLO ({self.settings.slo_response_time_ms}ms)",
                "suggestions": ["Consider caching frequently requested queries", "Optimize model selection", "Scale service instances"]
            })
        
        if perf_metrics.error_rate > self.settings.slo_error_rate_threshold:
            recommendations.append({
                "type": "reliability",
                "priority": "critical",
                "title": "High error rate",
                "description": f"Error rate ({perf_metrics.error_rate:.2%}) exceeds threshold ({self.settings.slo_error_rate_threshold:.2%})",
                "suggestions": ["Investigate error patterns", "Improve fallback mechanisms", "Check service dependencies"]
            })
        
        # Build report
        report = {
            "report_type": "performance_analysis",
            "time_range_hours": time_range_hours,
            "generated_at": datetime.now().isoformat(),
            "performance_metrics": {
                "total_requests": perf_metrics.total_requests,
                "successful_requests": perf_metrics.successful_requests,
                "failed_requests": perf_metrics.failed_requests,
                "avg_response_time_ms": perf_metrics.avg_response_time_ms,
                "p95_response_time_ms": perf_metrics.p95_response_time_ms,
                "p99_response_time_ms": perf_metrics.p99_response_time_ms,
                "error_rate": perf_metrics.error_rate,
                "requests_per_second": perf_metrics.requests_per_second,
                "slo_compliance": perf_metrics.slo_compliance
            },
            "slo_status": slo_status,
            "complexity_analysis": complexity_analysis,
            "provider_analysis": provider_analysis,
            "recommendations": recommendations
        }
        
        logger.debug("Generated performance report",
                    time_range_hours=time_range_hours,
                    total_requests=perf_metrics.total_requests,
                    slo_compliance=perf_metrics.slo_compliance)
        
        return report
    
    async def get_usage_trends(self, 
                              time_range_hours: int = 24,
                              bucket_size_hours: int = 1) -> Dict[str, Any]:
        """
        Generate usage trends analysis.
        
        Args:
            time_range_hours: Time range for analysis in hours
            bucket_size_hours: Size of time buckets in hours
            
        Returns:
            Usage trends analysis
        """
        try:
            if self.circuit_breaker:
                return self.circuit_breaker(self._get_usage_trends_impl)(
                    time_range_hours, bucket_size_hours
                )
            else:
                return await self._get_usage_trends_impl(time_range_hours, bucket_size_hours)
                
        except Exception as e:
            logger.error("Failed to get usage trends", error=str(e))
            raise
    
    async def _get_usage_trends_impl(self, time_range_hours: int, bucket_size_hours: int) -> Dict[str, Any]:
        """Implementation of usage trends analysis."""
        if not self.settings.enable_performance_tracking:
            return {
                "error": "Performance tracking is disabled",
                "usage_trends_enabled": False
            }
        
        # Get usage trends from metrics store
        trends = await self.metrics_store.get_usage_trends(time_range_hours, bucket_size_hours)
        
        # Calculate trend analysis
        if trends:
            request_counts = [t.request_count for t in trends]
            response_times = [t.avg_response_time for t in trends]
            error_rates = [t.error_rate for t in trends]
            costs = [t.cost_usd for t in trends]
            
            trend_analysis = {
                "request_volume_trend": self._calculate_trend(request_counts),
                "response_time_trend": self._calculate_trend(response_times),
                "error_rate_trend": self._calculate_trend(error_rates),
                "cost_trend": self._calculate_trend(costs),
                "peak_usage_time": self._find_peak_usage_time(trends),
                "complexity_patterns": self._analyze_complexity_patterns(trends),
                "provider_usage_patterns": self._analyze_provider_patterns(trends)
            }
        else:
            trend_analysis = {
                "request_volume_trend": "no_data",
                "response_time_trend": "no_data",
                "error_rate_trend": "no_data",
                "cost_trend": "no_data",
                "peak_usage_time": None,
                "complexity_patterns": {},
                "provider_usage_patterns": {}
            }
        
        # Build report
        report = {
            "report_type": "usage_trends",
            "time_range_hours": time_range_hours,
            "bucket_size_hours": bucket_size_hours,
            "generated_at": datetime.now().isoformat(),
            "trend_analysis": trend_analysis,
            "time_series_data": [
                {
                    "timestamp": trend.time_period,
                    "request_count": trend.request_count,
                    "avg_response_time": trend.avg_response_time,
                    "error_rate": trend.error_rate,
                    "cost_usd": trend.cost_usd,
                    "complexity_distribution": trend.complexity_distribution,
                    "provider_distribution": trend.provider_distribution
                }
                for trend in trends
            ]
        }
        
        logger.debug("Generated usage trends report",
                    time_range_hours=time_range_hours,
                    data_points=len(trends))
        
        return report
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple linear trend calculation
        first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
        second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        if second_half_avg > first_half_avg * 1.1:
            return "increasing"
        elif second_half_avg < first_half_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _find_peak_usage_time(self, trends) -> Optional[str]:
        """Find the time period with peak usage."""
        if not trends:
            return None
        
        peak_trend = max(trends, key=lambda t: t.request_count)
        return peak_trend.time_period
    
    def _analyze_complexity_patterns(self, trends) -> Dict[str, Any]:
        """Analyze complexity patterns over time."""
        if not trends:
            return {}
        
        complexity_totals = {"simple": 0, "medium": 0, "complex": 0}
        
        for trend in trends:
            for complexity, count in trend.complexity_distribution.items():
                if complexity in complexity_totals:
                    complexity_totals[complexity] += count
        
        total_requests = sum(complexity_totals.values())
        if total_requests == 0:
            return {}
        
        return {
            "simple_percentage": (complexity_totals["simple"] / total_requests) * 100,
            "medium_percentage": (complexity_totals["medium"] / total_requests) * 100,
            "complex_percentage": (complexity_totals["complex"] / total_requests) * 100,
            "dominant_complexity": max(complexity_totals, key=complexity_totals.get)
        }
    
    def _analyze_provider_patterns(self, trends) -> Dict[str, Any]:
        """Analyze provider usage patterns over time."""
        if not trends:
            return {}
        
        provider_totals = {}
        
        for trend in trends:
            for provider, count in trend.provider_distribution.items():
                if provider not in provider_totals:
                    provider_totals[provider] = 0
                provider_totals[provider] += count
        
        total_requests = sum(provider_totals.values())
        if total_requests == 0:
            return {}
        
        provider_percentages = {
            provider: (count / total_requests) * 100
            for provider, count in provider_totals.items()
        }
        
        return {
            "provider_distribution": provider_percentages,
            "dominant_provider": max(provider_totals, key=provider_totals.get),
            "provider_diversity": len(provider_totals)
        }
    
    async def health_check(self) -> bool:
        """
        Perform comprehensive health check of the Analytics Service.
        
        Returns:
            True if all components are healthy, False otherwise
        """
        try:
            checks = {
                "cost_tracker": await self.cost_tracker.health_check(),
                "metrics_store": await self.metrics_store.health_check(),
                "service_initialized": self._initialized,
                "circuit_breaker": self.circuit_breaker.current_state != "open" if self.circuit_breaker else True
            }
            
            is_healthy = all(checks.values())
            
            logger.debug("Analytics service health check", 
                        checks=checks, 
                        is_healthy=is_healthy)
            
            return is_healthy
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False
    
    async def get_service_status(self) -> Dict[str, Any]:
        """
        Get comprehensive service status information.
        
        Returns:
            Service status information
        """
        try:
            uptime_seconds = (datetime.now() - self._start_time).total_seconds()
            
            status = {
                "service": "analytics",
                "version": "1.0.0",
                "status": "healthy" if await self.health_check() else "unhealthy",
                "uptime_seconds": uptime_seconds,
                "initialized": self._initialized,
                "components": {
                    "cost_tracker": {
                        "enabled": self.settings.enable_cost_tracking,
                        "epic1_integration": True,
                        "healthy": await self.cost_tracker.health_check()
                    },
                    "metrics_store": {
                        "enabled": self.settings.enable_performance_tracking,
                        "retention_hours": self.settings.metrics_retention_hours,
                        "healthy": await self.metrics_store.health_check()
                    },
                    "circuit_breaker": {
                        "enabled": self.settings.circuit_breaker_enabled,
                        "state": self.circuit_breaker.current_state if self.circuit_breaker else "disabled"
                    }
                },
                "configuration": {
                    "cost_tracking_enabled": self.settings.enable_cost_tracking,
                    "performance_tracking_enabled": self.settings.enable_performance_tracking,
                    "usage_trends_enabled": self.settings.enable_usage_trends,
                    "ab_testing_enabled": self.settings.enable_ab_testing,
                    "metrics_retention_hours": self.settings.metrics_retention_hours
                }
            }
            
            return status
            
        except Exception as e:
            logger.error("Failed to get service status", error=str(e))
            return {
                "service": "analytics",
                "status": "error",
                "error": str(e)
            }