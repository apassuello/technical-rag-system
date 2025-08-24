"""
Cost Tracker Integration for Analytics Service.

This module integrates Epic 1's CostTracker with the Analytics Service,
providing cost tracking capabilities with $0.001 precision and multi-model
support for the Epic 8 microservices architecture.

Epic 1 Integration:
- Direct import and use of Epic 1 CostTracker
- Maintains all Epic 1 cost tracking functionality
- Adds microservice-specific enhancements
- Preserves $0.001 precision and budget enforcement
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from decimal import Decimal
import logging
from datetime import datetime, timedelta

# Add src path for Epic 1 imports - Docker structure
src_path = Path("/app/src")  # Direct path in Docker container
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    # Import Epic 1 CostTracker directly
    from components.generators.llm_adapters.cost_tracker import (
        CostTracker, 
        UsageRecord, 
        CostSummary,
        get_cost_tracker,
        record_llm_usage
    )
except ImportError as e:
    logging.warning(f"Could not import Epic 1 CostTracker: {e}")
    # Fallback implementation for Docker environments
    logging.info("Using fallback CostTracker implementation")
    
    # Minimal fallback classes for Epic 8 deployment
    class CostTracker:
        def __init__(self, **kwargs):
            pass
        
        def record_usage(self, **kwargs):
            return {}
            
        def get_summary(self):
            return {}
    
    class UsageRecord:
        def __init__(self, **kwargs):
            pass
    
    class CostSummary:
        def __init__(self, **kwargs):
            pass
    
    def get_cost_tracker():
        return CostTracker()
    
    def record_llm_usage(**kwargs):
        pass

import structlog
from .config import get_settings, get_cost_tracker_config

logger = structlog.get_logger(__name__)


class AnalyticsCostTracker:
    """
    Analytics Service wrapper for Epic 1 CostTracker.
    
    This class provides a microservice-friendly interface to Epic 1's
    CostTracker while maintaining all original functionality and precision.
    
    Features:
    - Full Epic 1 CostTracker integration
    - Microservice-specific enhancements
    - API-friendly data formatting
    - Enhanced analytics and reporting
    - Session-based tracking for request correlation
    """
    
    def __init__(self):
        """Initialize Analytics Cost Tracker with Epic 1 integration."""
        settings = get_settings()
        cost_config = get_cost_tracker_config()
        
        # Initialize Epic 1 CostTracker with configuration
        self.cost_tracker = CostTracker(**cost_config)
        
        # Analytics-specific enhancements
        self.session_tracking_enabled = True
        self.request_correlation_enabled = True
        self._request_sessions: Dict[str, str] = {}
        
        logger.info(
            "Initialized AnalyticsCostTracker with Epic 1 integration",
            precision_places=cost_config.get("precision_places", 6),
            daily_budget=cost_config.get("daily_budget"),
            enable_detailed_logging=cost_config.get("enable_detailed_logging", True)
        )
    
    async def record_query_cost(self,
                               provider: str,
                               model: str,
                               input_tokens: int,
                               output_tokens: int,
                               cost_usd: Decimal,
                               query_complexity: Optional[str] = None,
                               request_time_ms: Optional[float] = None,
                               request_id: Optional[str] = None,
                               success: bool = True,
                               metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record query cost using Epic 1 CostTracker.
        
        Args:
            provider: LLM provider name (e.g., "openai", "mistral", "ollama")
            model: Specific model used (e.g., "gpt-4", "llama3.2:3b")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens  
            cost_usd: Total cost in USD (Decimal for precision)
            query_complexity: Query complexity level (simple/medium/complex)
            request_time_ms: Request duration in milliseconds
            request_id: Request ID for correlation
            success: Whether the request was successful
            metadata: Additional metadata
        """
        try:
            # Start session tracking if request_id provided
            if request_id and self.session_tracking_enabled:
                if request_id not in self._request_sessions:
                    self.cost_tracker.start_session(request_id)
                    self._request_sessions[request_id] = request_id
            
            # Ensure cost is a Decimal
            if not isinstance(cost_usd, Decimal):
                cost_usd = Decimal(str(cost_usd))
            
            # Enhanced metadata for analytics
            enhanced_metadata = {
                **(metadata or {}),
                "request_id": request_id,
                "recorded_at": datetime.now().isoformat(),
                "service": "analytics"
            }
            
            # Record using Epic 1 CostTracker
            self.cost_tracker.record_usage(
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                query_complexity=query_complexity,
                request_time_ms=request_time_ms,
                success=success,
                metadata=enhanced_metadata
            )
            
            logger.debug(
                "Recorded query cost via Epic 1 CostTracker",
                provider=provider,
                model=model,
                cost_usd=str(cost_usd),
                complexity=query_complexity,
                request_id=request_id
            )
            
        except Exception as e:
            logger.error(
                "Failed to record query cost",
                error=str(e),
                provider=provider,
                model=model,
                request_id=request_id
            )
            raise
    
    async def end_request_session(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        End a request session and return cost summary.
        
        Args:
            request_id: Request ID to end session for
            
        Returns:
            Session cost summary or None
        """
        try:
            if request_id in self._request_sessions:
                # Set the session as current before ending
                self.cost_tracker.current_session_id = request_id
                summary = self.cost_tracker.end_session()
                
                # Clean up tracking
                del self._request_sessions[request_id]
                
                logger.debug("Ended request session", request_id=request_id, summary=summary)
                return summary
            
            return None
            
        except Exception as e:
            logger.error("Failed to end request session", error=str(e), request_id=request_id)
            return None
    
    async def get_cost_summary(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """
        Get comprehensive cost summary using Epic 1 CostTracker.
        
        Args:
            time_range_hours: Time range in hours for summary
            
        Returns:
            Comprehensive cost summary dictionary
        """
        try:
            # Get total cost from Epic 1 CostTracker
            total_cost = self.cost_tracker.get_total_cost()
            
            # Get cost breakdowns
            cost_by_provider = self.cost_tracker.get_cost_by_provider()
            cost_by_model = self.cost_tracker.get_cost_by_model()
            cost_by_complexity = self.cost_tracker.get_cost_by_complexity()
            
            # Get time-based summary
            time_summary = self.cost_tracker.get_summary_by_time_period(hours=time_range_hours)
            
            # Get cost optimization recommendations
            recommendations = self.cost_tracker.get_cost_optimization_recommendations()
            
            # Get usage patterns analysis
            usage_patterns = self.cost_tracker.analyze_usage_patterns()
            
            summary = {
                "total_cost_usd": float(total_cost),
                "time_range_hours": time_range_hours,
                "time_period_summary": {
                    "total_requests": time_summary.total_requests,
                    "total_cost_usd": float(time_summary.total_cost_usd),
                    "avg_cost_per_request": float(time_summary.avg_cost_per_request),
                    "success_rate": time_summary.success_rate,
                    "avg_request_time_ms": time_summary.avg_request_time_ms,
                },
                "cost_by_provider": {k: float(v) for k, v in cost_by_provider.items()},
                "cost_by_model": {k: float(v) for k, v in cost_by_model.items()},
                "cost_by_complexity": {k: float(v) for k, v in cost_by_complexity.items()},
                "usage_patterns": usage_patterns,
                "optimization_recommendations": recommendations,
                "generated_at": datetime.now().isoformat(),
                "epic1_integration": True,
                "precision_places": 6
            }
            
            logger.debug("Generated cost summary", summary_keys=list(summary.keys()))
            return summary
            
        except Exception as e:
            logger.error("Failed to get cost summary", error=str(e))
            raise
    
    async def get_cost_optimization_report(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """
        Generate cost optimization report with Epic 1 recommendations.
        
        Args:
            time_range_hours: Time range for analysis
            
        Returns:
            Cost optimization report
        """
        try:
            # Get Epic 1 cost optimization recommendations
            recommendations = self.cost_tracker.get_cost_optimization_recommendations()
            
            # Get current cost summary
            cost_summary = await self.get_cost_summary(time_range_hours)
            
            # Calculate potential savings
            total_cost = cost_summary["time_period_summary"]["total_cost_usd"]
            
            potential_savings = 0.0
            for rec in recommendations:
                if "potential_savings" in rec and rec["potential_savings"].startswith("$"):
                    savings_str = rec["potential_savings"].replace("$", "")
                    try:
                        potential_savings += float(savings_str)
                    except ValueError:
                        pass
            
            # Generate optimization report
            report = {
                "analysis_period": {
                    "time_range_hours": time_range_hours,
                    "total_cost_usd": total_cost,
                    "total_requests": cost_summary["time_period_summary"]["total_requests"],
                    "avg_cost_per_request": cost_summary["time_period_summary"]["avg_cost_per_request"]
                },
                "optimization_opportunities": recommendations,
                "potential_total_savings": round(potential_savings, 4),
                "savings_percentage": round((potential_savings / total_cost * 100) if total_cost > 0 else 0, 2),
                "cost_distribution": cost_summary["cost_by_provider"],
                "complexity_analysis": cost_summary["cost_by_complexity"],
                "recommendations_count": len(recommendations),
                "high_priority_recommendations": len([r for r in recommendations if r.get("priority") == "high"]),
                "epic1_powered": True,
                "generated_at": datetime.now().isoformat()
            }
            
            logger.debug("Generated cost optimization report", 
                        recommendations_count=len(recommendations),
                        potential_savings=potential_savings)
            
            return report
            
        except Exception as e:
            logger.error("Failed to generate cost optimization report", error=str(e))
            raise
    
    async def get_budget_status(self) -> Dict[str, Any]:
        """
        Get current budget status and alerts.
        
        Returns:
            Budget status information
        """
        try:
            settings = get_settings()
            
            # Get daily spending
            daily_summary = self.cost_tracker.get_summary_by_time_period(hours=24)
            daily_spend = float(daily_summary.total_cost_usd)
            
            # Get monthly spending (approximate - 30 days)
            monthly_summary = self.cost_tracker.get_summary_by_time_period(hours=24 * 30)
            monthly_spend = float(monthly_summary.total_cost_usd)
            
            status = {
                "daily_budget": settings.daily_budget,
                "monthly_budget": settings.monthly_budget,
                "daily_spend": daily_spend,
                "monthly_spend": monthly_spend,
                "daily_utilization": (daily_spend / settings.daily_budget * 100) if settings.daily_budget else None,
                "monthly_utilization": (monthly_spend / settings.monthly_budget * 100) if settings.monthly_budget else None,
                "active_alerts": self.cost_tracker.active_alerts,
                "alert_thresholds": settings.alert_thresholds,
                "budget_status": "healthy",
                "last_updated": datetime.now().isoformat()
            }
            
            # Determine budget status
            if settings.daily_budget and daily_spend >= settings.daily_budget:
                status["budget_status"] = "exceeded"
            elif settings.daily_budget and daily_spend >= (settings.daily_budget * 0.95):
                status["budget_status"] = "warning"
            
            return status
            
        except Exception as e:
            logger.error("Failed to get budget status", error=str(e))
            raise
    
    async def export_cost_data(self, format_type: str = "json", 
                              include_metadata: bool = True) -> str:
        """
        Export cost data using Epic 1 CostTracker export functionality.
        
        Args:
            format_type: Export format ("json" or "csv")
            include_metadata: Whether to include metadata
            
        Returns:
            Exported data as string
        """
        try:
            return self.cost_tracker.export_usage_data(
                format_type=format_type,
                include_metadata=include_metadata
            )
            
        except Exception as e:
            logger.error("Failed to export cost data", error=str(e), format=format_type)
            raise
    
    async def health_check(self) -> bool:
        """
        Perform health check on cost tracking system.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Check if Epic 1 CostTracker is accessible
            total_cost = self.cost_tracker.get_total_cost()
            
            # Check if we can record a test usage (minimal)
            test_record_successful = True
            try:
                # This should work if the tracker is healthy
                providers = self.cost_tracker.get_cost_by_provider()
            except Exception:
                test_record_successful = False
            
            is_healthy = test_record_successful and total_cost is not None
            
            logger.debug("Cost tracker health check", is_healthy=is_healthy)
            return is_healthy
            
        except Exception as e:
            logger.error("Cost tracker health check failed", error=str(e))
            return False


# Global instance
_analytics_cost_tracker: Optional[AnalyticsCostTracker] = None


def get_analytics_cost_tracker() -> AnalyticsCostTracker:
    """
    Get global analytics cost tracker instance.
    
    Returns:
        AnalyticsCostTracker instance
    """
    global _analytics_cost_tracker
    if _analytics_cost_tracker is None:
        _analytics_cost_tracker = AnalyticsCostTracker()
    return _analytics_cost_tracker