"""Test suite for Cost Tracker - Epic 1 Phase 2.

Tests cost tracking system including:
- $0.001 precision tracking
- Thread-safe operations
- Cost aggregation and analytics
- Export capabilities
"""

import pytest
import threading
import time
from decimal import Decimal
from datetime import datetime, timedelta
from pathlib import Path
import json
import csv
from concurrent.futures import ThreadPoolExecutor

# Import cost tracking components
from src.components.generators.llm_adapters.cost_tracker import (
    CostTracker, UsageRecord, CostSummary
)


class TestCostTracker:
    """Test suite for cost tracking functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cost_tracker = CostTracker()
        self.test_timestamp = datetime.now()
        
    # EPIC1-COST-001: Cost Tracker Precision Validation
    def test_precision_validation(self):
        """Test cost tracking with $0.001 precision.
        
        Requirement: $0.001 precision with decimal accuracy
        PASS Criteria:
        - Internal precision: 6 decimal places (0.000001)
        - Display precision: 3-6 places as configured
        - Arithmetic accuracy: No rounding errors in aggregation
        - Decimal type usage: Throughout system
        """
        # Record precise usage
        precise_cost = Decimal('0.029340')  # 6 decimal places
        
        self.cost_tracker.record_usage(
            provider="openai",
            model="gpt-4-turbo",
            input_tokens=1234,
            output_tokens=567,
            cost_usd=precise_cost,
            query_complexity="complex"
        )
        
        # Verify precision preservation through cost tracker API
        total_cost = self.cost_tracker.get_total_cost()
        assert isinstance(total_cost, Decimal)
        assert total_cost == precise_cost
        assert len(str(total_cost).split('.')[-1]) <= 6  # Max 6 decimal places
        
        # Test aggregation precision
        summary = self.cost_tracker.get_summary_by_time_period(hours=24)
        assert isinstance(summary.total_cost_usd, Decimal)
        assert summary.total_cost_usd == precise_cost
        
        # Test multiple precise additions
        costs = [Decimal('0.001234'), Decimal('0.005678'), Decimal('0.009012')]
        for i, cost in enumerate(costs):
            self.cost_tracker.record_usage(
                provider="test",
                model="test-model",
                input_tokens=100,
                output_tokens=50,
                cost_usd=cost,
                query_complexity="simple"
            )
        
        # Verify aggregation accuracy
        expected_total = precise_cost + sum(costs)
        actual_total = self.cost_tracker.get_total_cost()
        assert actual_total == expected_total
        
        # Test no floating-point errors
        assert isinstance(actual_total, Decimal)
        precision = len(str(actual_total).split('.')[-1])
        assert precision <= 6
    
    def test_decimal_arithmetic_accuracy(self):
        """Test decimal arithmetic prevents rounding errors."""
        # Known problematic floating-point calculation: 0.1 + 0.2
        cost1 = Decimal('0.100000')
        cost2 = Decimal('0.200000')
        
        self.cost_tracker.record_usage(
            provider="test1", model="model1", input_tokens=100, output_tokens=50,
            cost_usd=cost1, query_complexity="simple"
        )
        self.cost_tracker.record_usage(
            provider="test2", model="model2", input_tokens=100, output_tokens=50,
            cost_usd=cost2, query_complexity="simple"
        )
        
        summary = self.cost_tracker.get_summary_by_time_period(hours=24)
        expected = Decimal('0.300000')
        assert summary.total_cost_usd == expected
        
        # Verify this doesn't have floating-point errors
        # (0.1 + 0.2 = 0.30000000000000004 with float)
        assert str(summary.total_cost_usd) == '0.300000'
    
    # EPIC1-COST-002: Thread-Safe Cost Tracking
    def test_thread_safe_operations(self):
        """Test concurrent cost recording from multiple threads.
        
        Requirement: Thread-safe operations without data corruption
        PASS Criteria:
        - Entry count: Exactly 1000
        - Data integrity: All fields preserved
        - Performance: <100ms per record
        - No exceptions or deadlocks
        """
        num_threads = 10
        records_per_thread = 100
        total_expected = num_threads * records_per_thread
        
        def record_usage_batch(thread_id):
            """Record usage entries from a single thread."""
            for i in range(records_per_thread):
                cost = Decimal(f'0.00{thread_id:02d}{i:02d}')  # Unique cost per record
                
                start_time = time.time()
                self.cost_tracker.record_usage(
                    provider=f"provider_{thread_id}",
                    model=f"model_{thread_id}",
                    input_tokens=100 + i,
                    output_tokens=50 + i,
                    cost_usd=cost,
                    query_complexity="medium"
                )
                record_time = time.time() - start_time
                
                # Verify performance requirement
                assert record_time < 0.1  # <100ms per record
        
        # Execute concurrent recording
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_usage_batch, i) for i in range(num_threads)]
            
            # Wait for all threads to complete
            for future in futures:
                future.result()  # Will raise exception if thread failed
        
        execution_time = time.time() - start_time
        print(f"Thread safety test completed in {execution_time:.2f}s")
        
        # Verify entry count
        summary = self.cost_tracker.get_summary_by_time_period(hours=24)
        assert summary.total_requests == total_expected, f"Expected {total_expected} entries, got {summary.total_requests}"
        
        # Verify data integrity - check a few specific records
        usage_history = self.cost_tracker.get_usage_history()
        assert len(usage_history) == total_expected
        
        # Verify no data corruption by checking unique costs
        costs = [record.cost_usd for record in usage_history]
        unique_costs = set(costs)
        assert len(unique_costs) == total_expected, "Cost values corrupted or duplicated"
        
        # Verify total cost calculation
        expected_total_cost = sum(costs)
        assert summary.total_cost_usd == expected_total_cost
    
    def test_concurrent_summary_generation(self):
        """Test thread-safe summary generation during concurrent writes."""
        def continuous_recording():
            """Continuously record usage for a short period."""
            for i in range(50):
                self.cost_tracker.record_usage(
                    provider="test", model="test-model",
                    input_tokens=100, output_tokens=50,
                    cost_usd=Decimal('0.001000'),
                    query_complexity="simple"
                )
                time.sleep(0.01)  # Small delay
        
        def continuous_summary():
            """Continuously generate summaries."""
            summaries = []
            for i in range(20):
                summary = self.cost_tracker.get_summary_by_time_period(hours=24)
                summaries.append(summary)
                time.sleep(0.02)
            return summaries
        
        # Start concurrent operations
        with ThreadPoolExecutor(max_workers=3) as executor:
            recording_future = executor.submit(continuous_recording)
            summary_future = executor.submit(continuous_summary)
            
            # Both should complete without deadlock
            recording_future.result(timeout=10)
            summaries = summary_future.result(timeout=10)
        
        # Verify summaries were generated successfully
        assert len(summaries) == 20
        for summary in summaries:
            assert isinstance(summary, CostSummary)
            assert summary.total_requests >= 0
    
    # EPIC1-COST-003: Cost Optimization Recommendations
    def test_cost_optimization_recommendations(self):
        """Test generation of actionable optimization recommendations.
        
        Requirement: Generate actionable optimization recommendations
        PASS Criteria:
        - Relevant recommendations: Address actual patterns
        - Savings accuracy: Within 10% of actual potential
        - Priority levels: Correctly assigned (high/medium/low)
        - Actionable suggestions: Clear implementation path
        """
        # Create usage pattern: 70% simple queries using expensive GPT-4
        expensive_model_usage = 70  # Simple queries on expensive model
        cheap_model_usage = 30    # Appropriate model usage
        
        # Record expensive usage pattern
        expensive_cost = Decimal('0.050000')  # High cost per query
        cheap_cost = Decimal('0.001000')     # Low cost per query
        
        for i in range(expensive_model_usage):
            self.cost_tracker.record_usage(
                provider="openai", model="gpt-4-turbo",
                input_tokens=100, output_tokens=50,
                cost_usd=expensive_cost,
                query_complexity="simple"  # Wrong model for complexity
            )
        
        for i in range(cheap_model_usage):
            self.cost_tracker.record_usage(
                provider="local", model="qwen2.5-1.5b-instruct",
                input_tokens=100, output_tokens=50,
                cost_usd=cheap_cost,
                query_complexity="simple"  # Correct model
            )
        
        # Generate recommendations
        recommendations = self.cost_tracker.get_cost_optimization_recommendations()
        
        # Verify recommendations are relevant
        assert len(recommendations) > 0
        
        # Should identify simple queries on expensive model
        simple_query_rec = None
        for rec in recommendations:
            if 'simple' in rec['description'].lower() and rec['type'] == 'cost_optimization':
                simple_query_rec = rec
                break
        
        assert simple_query_rec is not None, "Should recommend routing simple queries to cheaper models"
        
        # Verify savings calculation accuracy
        current_cost = expensive_model_usage * expensive_cost + cheap_model_usage * cheap_cost
        optimized_cost = (expensive_model_usage + cheap_model_usage) * cheap_cost
        expected_savings = current_cost - optimized_cost
        
        # Should be within 10% of actual potential
        potential_savings_str = simple_query_rec['potential_savings'].replace('$', '')
        potential_savings = Decimal(potential_savings_str)
        savings_error = abs(potential_savings - expected_savings) / expected_savings
        assert savings_error <= 0.10, f"Savings calculation error {savings_error:.2%} > 10%"
        
        # Verify priority assignment
        assert 'priority' in simple_query_rec
        assert simple_query_rec['priority'] in ['high', 'medium', 'low']
        
        # High savings should get high priority
        if expected_savings > Decimal('1.00'):
            assert simple_query_rec['priority'] == 'high'
        
        # Verify actionable suggestion
        assert len(simple_query_rec['suggestion']) > 0
        assert 'route' in simple_query_rec['suggestion'].lower() or 'use' in simple_query_rec['suggestion'].lower()
    
    def test_usage_pattern_analysis(self):
        """Test analysis of usage patterns for optimization."""
        # Create varied usage pattern
        patterns = [
            {"complexity": "simple", "provider": "openai", "model": "gpt-4", "count": 50, "cost": "0.040"},
            {"complexity": "medium", "provider": "mistral", "model": "mistral-small", "count": 30, "cost": "0.015"},
            {"complexity": "complex", "provider": "openai", "model": "gpt-4", "count": 20, "cost": "0.080"},
        ]
        
        for pattern in patterns:
            for _ in range(pattern["count"]):
                self.cost_tracker.record_usage(
                    provider=pattern["provider"],
                    model=pattern["model"],
                    input_tokens=200,
                    output_tokens=100,
                    cost_usd=Decimal(pattern["cost"]),
                    query_complexity=pattern["complexity"]
                )
        
        # Analyze patterns
        analysis = self.cost_tracker.analyze_usage_patterns()
        
        # Should identify complexity distribution
        assert "simple" in analysis["complexity_distribution"]
        assert "medium" in analysis["complexity_distribution"]
        assert "complex" in analysis["complexity_distribution"]
        
        # Verify provider distribution
        assert "openai" in analysis["provider_distribution"]
        assert "mistral" in analysis["provider_distribution"]
        
        # Check cost efficiency analysis
        assert "cost_per_complexity" in analysis
        simple_cost_per_query = analysis["cost_per_complexity"]["simple"]
        complex_cost_per_query = analysis["cost_per_complexity"]["complex"]
        assert complex_cost_per_query > simple_cost_per_query  # Complex should be more expensive
    
    # Export and Reporting Tests
    def test_json_export(self):
        """Test JSON export functionality."""
        # Record some usage
        for i in range(3):
            self.cost_tracker.record_usage(
                provider=f"provider_{i}", model=f"model_{i}",
                input_tokens=100 + i, output_tokens=50 + i,
                cost_usd=Decimal(f'0.00{i+1}000'),
                query_complexity="simple"
            )
        
        # Export to JSON
        json_data = self.cost_tracker.export_usage_data(format_type="json")
        
        # Verify export data is valid JSON
        import json
        data = json.loads(json_data)
        
        # Should be a list of usage records
        assert isinstance(data, list)
        assert len(data) == 3
        
        # Verify record structure
        record = data[0]
        assert 'provider' in record
        assert 'model' in record
        assert 'cost_usd' in record
    
    def test_csv_export(self):
        """Test CSV export functionality."""
        # Record usage
        self.cost_tracker.record_usage(
            provider="test", model="test-model",
            input_tokens=150, output_tokens=75,
            cost_usd=Decimal('0.025000'),
            query_complexity="medium"
        )
        
        # Export to CSV
        csv_data = self.cost_tracker.export_usage_data(format_type="csv")
        
        # Verify CSV structure
        import csv
        import io
        reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(reader)
        
        assert len(rows) == 1
        row = rows[0]
        assert row['provider'] == 'test'
        assert row['model'] == 'test-model'
        assert row['cost_usd'] == '0.025000'
    
    # Edge Cases and Error Handling
    def test_zero_cost_handling(self):
        """Test handling of zero-cost operations (e.g., local models)."""
        self.cost_tracker.record_usage(
            provider="local", model="qwen2.5-1.5b-instruct",
            input_tokens=100, output_tokens=50,
            cost_usd=Decimal('0.000000'),  # Zero cost
            query_complexity="simple"
        )
        
        summary = self.cost_tracker.get_summary_by_time_period(hours=24)
        assert summary.total_cost_usd == Decimal('0.000000')
        assert summary.total_requests == 1
        
        # Should still track tokens and requests
        assert summary.total_input_tokens == 100
        assert summary.total_output_tokens == 50
    
    def test_large_number_handling(self):
        """Test handling of large token counts and costs."""
        large_tokens = 1_000_000  # 1M tokens
        large_cost = Decimal('100.123456')  # $100+
        
        self.cost_tracker.record_usage(
            provider="test", model="test-model",
            input_tokens=large_tokens, output_tokens=large_tokens,
            cost_usd=large_cost,
            query_complexity="complex"
        )
        
        summary = self.cost_tracker.get_summary_by_time_period(hours=24)
        assert summary.total_cost_usd == large_cost
        assert summary.total_input_tokens == large_tokens
        assert summary.total_output_tokens == large_tokens
    
    def test_time_range_filtering(self):
        """Test filtering usage records by time range."""
        base_time = datetime.now()
        
        # Record usage at different times
        times = [
            base_time - timedelta(hours=2),  # 2 hours ago
            base_time - timedelta(hours=1),  # 1 hour ago
            base_time,                       # Now
        ]
        
        for i, timestamp in enumerate(times):
            self.cost_tracker.record_usage(
                provider=f"provider_{i}", model=f"model_{i}",
                input_tokens=100, output_tokens=50,
                cost_usd=Decimal('0.010000'),
                query_complexity="simple",
                timestamp=timestamp
            )
        
        # Get usage for last hour
        one_hour_ago = base_time - timedelta(hours=1)
        recent_usage = self.cost_tracker.get_usage_history(
            start_time=one_hour_ago,
            end_time=base_time + timedelta(minutes=1)
        )
        
        # Should get 2 records (1 hour ago and now)
        assert len(recent_usage) == 2


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])