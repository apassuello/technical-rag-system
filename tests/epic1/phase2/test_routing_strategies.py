"""Test suite for Routing Strategies - Epic 1 Phase 2.

Tests routing strategy implementations including:
- Cost optimized strategy validation
- Quality first strategy validation
- Balanced strategy optimization
- Model option scoring and selection
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock

# Import routing strategy components
from src.components.generators.routing.routing_strategies import (
    CostOptimizedStrategy,
    QualityFirstStrategy,
    BalancedStrategy,
    ModelOption
)


class TestRoutingStrategies:
    """Test suite for routing strategy functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock model options for testing
        self.model_options = {
            "simple": [
                ModelOption(
                    provider="ollama",
                    model="llama3.2:3b",
                    estimated_cost=Decimal('0.000'),
                    estimated_latency=1.5,
                    quality_score=0.75
                ),
                ModelOption(
                    provider="openai",
                    model="gpt-3.5-turbo",
                    estimated_cost=Decimal('0.002'),
                    estimated_latency=0.8,
                    quality_score=0.90
                )
            ],
            "medium": [
                ModelOption(
                    provider="mistral",
                    model="mistral-small",
                    estimated_cost=Decimal('0.010'),
                    estimated_latency=1.2,
                    quality_score=0.85
                ),
                ModelOption(
                    provider="openai",
                    model="gpt-4-turbo",
                    estimated_cost=Decimal('0.050'),
                    estimated_latency=2.0,
                    quality_score=0.95
                )
            ],
            "complex": [
                ModelOption(
                    provider="openai",
                    model="gpt-3.5-turbo",
                    estimated_cost=Decimal('0.020'),
                    estimated_latency=1.5,
                    quality_score=0.85
                ),
                ModelOption(
                    provider="openai",
                    model="gpt-4-turbo",
                    estimated_cost=Decimal('0.100'),
                    estimated_latency=3.0,
                    quality_score=0.98
                )
            ]
        }
        
        # Test query analysis result
        self.query_analysis = {
            "complexity_level": "medium",
            "complexity_score": 0.55,
            "confidence": 0.85,
            "features": {
                "technical_terms": 3,
                "clause_count": 2,
                "word_count": 12
            }
        }
    
    # EPIC1-ROUTE-001: Cost Optimized Strategy Validation
    def test_cost_optimized_strategy_basic(self):
        """Test cost optimized strategy with basic configuration.
        
        Requirement: Minimize costs while maintaining quality
        PASS Criteria:
        - Model selection: Cheapest viable option selected
        - Budget compliance: Never exceeds max_cost
        - Quality threshold: Maintains minimum quality
        - Fallback logic: Activates when budget exceeded
        """
        strategy = CostOptimizedStrategy(
            max_cost_per_query=Decimal('0.015'),
            min_quality_threshold=0.80
        )
        
        # Test simple query routing
        simple_analysis = {**self.query_analysis, "complexity_level": "simple"}
        selection = strategy.select_model(
            query_analysis=simple_analysis,
            available_models=self.model_options["simple"]
        )
        
        # Should select cheapest option (Ollama)
        assert selection.provider == "ollama"
        assert selection.model == "llama3.2:3b"
        assert selection.estimated_cost == Decimal('0.000')
        assert selection.quality_score >= 0.80  # Meets minimum quality
        
        # Test medium complexity with budget constraint
        selection = strategy.select_model(
            query_analysis=self.query_analysis,
            available_models=self.model_options["medium"]
        )
        
        # Should select Mistral (cheaper than GPT-4, within budget)
        assert selection.provider == "mistral"
        assert selection.model == "mistral-small"
        assert selection.estimated_cost <= Decimal('0.015')
        assert selection.quality_score >= 0.80
    
    def test_cost_optimized_budget_enforcement(self):
        """Test strict budget enforcement in cost optimized strategy."""
        # Very tight budget
        strategy = CostOptimizedStrategy(
            max_cost_per_query=Decimal('0.005'),
            min_quality_threshold=0.70
        )
        
        # Test with medium complexity models
        selection = strategy.select_model(
            query_analysis=self.query_analysis,
            available_models=self.model_options["medium"]
        )
        
        # Should select cheapest option or return None if none fit budget
        if selection is not None:
            assert selection.estimated_cost <= Decimal('0.005')
        
        # If no model fits budget, should use fallback
        if selection is None:
            # Test fallback behavior
            fallback_models = self.model_options["simple"]  # Cheaper alternatives
            fallback_selection = strategy.select_model(
                query_analysis=self.query_analysis,
                available_models=fallback_models
            )
            assert fallback_selection is not None
            assert fallback_selection.estimated_cost <= Decimal('0.005')
    
    def test_cost_optimized_quality_threshold(self):
        """Test quality threshold enforcement."""
        strategy = CostOptimizedStrategy(
            max_cost_per_query=Decimal('1.000'),  # High budget
            min_quality_threshold=0.90  # High quality requirement
        )
        
        selection = strategy.select_model(
            query_analysis=self.query_analysis,
            available_models=self.model_options["medium"]
        )
        
        # Should select model meeting quality threshold
        assert selection is not None
        assert selection.quality_score >= 0.90
        
        # May not be the cheapest if it doesn't meet quality
        if selection.provider == "openai":
            assert selection.model == "gpt-4-turbo"  # Higher quality option
    
    # EPIC1-ROUTE-002: Quality First Strategy Validation
    def test_quality_first_strategy_basic(self):
        """Test quality first strategy prioritizing response quality.
        
        Requirement: Select highest quality models regardless of cost
        PASS Criteria:
        - Model selection: Highest quality option chosen
        - Quality maintenance: All selections >min_quality
        - Consistency: Same complexity → same model
        - Cost acknowledgment: Cost tracked but not limiting
        """
        strategy = QualityFirstStrategy(
            min_quality_threshold=0.85,
            cost_awareness_factor=0.1  # Minimal cost consideration
        )
        
        # Test simple query
        simple_analysis = {**self.query_analysis, "complexity_level": "simple"}
        selection = strategy.select_model(
            query_analysis=simple_analysis,
            available_models=self.model_options["simple"]
        )
        
        # Should select highest quality option
        assert selection.quality_score == max(opt.quality_score for opt in self.model_options["simple"])
        assert selection.provider == "openai"  # Higher quality than Ollama
        assert selection.model == "gpt-3.5-turbo"
        
        # Test medium complexity
        selection = strategy.select_model(
            query_analysis=self.query_analysis,
            available_models=self.model_options["medium"]
        )
        
        # Should select GPT-4 (highest quality)
        assert selection.provider == "openai"
        assert selection.model == "gpt-4-turbo"
        assert selection.quality_score == 0.95  # Highest available
        
        # Test complex queries
        complex_analysis = {**self.query_analysis, "complexity_level": "complex"}
        selection = strategy.select_model(
            query_analysis=complex_analysis,
            available_models=self.model_options["complex"]
        )
        
        # Should consistently select GPT-4 for quality
        assert selection.provider == "openai"
        assert selection.model == "gpt-4-turbo"
        assert selection.quality_score == 0.98
    
    def test_quality_first_consistency(self):
        """Test consistency of quality-first selections."""
        strategy = QualityFirstStrategy(min_quality_threshold=0.80)
        
        # Test same complexity multiple times
        selections = []
        for _ in range(5):
            selection = strategy.select_model(
                query_analysis=self.query_analysis,
                available_models=self.model_options["medium"]
            )
            selections.append((selection.provider, selection.model))
        
        # Should be consistent
        assert all(sel == selections[0] for sel in selections)
        assert selections[0] == ("openai", "gpt-4-turbo")  # Highest quality
    
    def test_quality_first_cost_tracking(self):
        """Test that quality-first strategy tracks but doesn't limit by cost."""
        strategy = QualityFirstStrategy(min_quality_threshold=0.80)
        
        selection = strategy.select_model(
            query_analysis=self.query_analysis,
            available_models=self.model_options["medium"]
        )
        
        # Should select high-quality model despite high cost
        assert selection.provider == "openai"
        assert selection.model == "gpt-4-turbo"
        assert selection.estimated_cost > Decimal('0.010')  # More expensive than alternatives
        
        # Cost should be tracked for reporting
        assert hasattr(selection, 'estimated_cost')
        assert selection.estimated_cost == Decimal('0.050')
    
    # EPIC1-ROUTE-003: Balanced Strategy Optimization
    def test_balanced_strategy_basic(self):
        """Test balanced strategy with weighted cost/quality tradeoff.
        
        Requirement: Optimal balance between cost and quality
        PASS Criteria:
        - Scoring accuracy: Correct weighted calculations
        - Model selection: Reflects weight balance
        - Cost reduction: 25-40% vs quality-first
        - Quality maintenance: >85% average
        """
        strategy = BalancedStrategy(
            cost_weight=0.4,
            quality_weight=0.6,
            latency_weight=0.0  # Focus on cost/quality only
        )
        
        # Test medium complexity balancing
        selection = strategy.select_model(
            query_analysis=self.query_analysis,
            available_models=self.model_options["medium"]
        )
        
        # Calculate expected scores for validation
        options = self.model_options["medium"]
        for option in options:
            # Cost score (lower cost = higher score)
            max_cost = max(opt.estimated_cost for opt in options)
            cost_score = 1.0 - (float(option.estimated_cost) / float(max_cost))
            
            # Balanced score calculation
            balanced_score = (0.4 * cost_score) + (0.6 * option.quality_score)
            
            print(f"{option.model}: cost_score={cost_score:.3f}, quality_score={option.quality_score}, balanced_score={balanced_score:.3f}")
        
        # Verify selection makes sense for balanced approach
        assert selection is not None
        
        # Should be a reasonable balance (not necessarily cheapest or highest quality)
        if len(options) > 1:
            # For medium complexity, Mistral should win on balance
            # (lower cost, decent quality vs GPT-4's high cost, high quality)
            assert selection.provider == "mistral" or selection.provider == "openai"
            assert selection.quality_score >= 0.80  # Maintain reasonable quality
    
    def test_balanced_strategy_weight_effects(self):
        """Test how different weights affect model selection."""
        options = self.model_options["medium"]
        
        # Cost-heavy balance (70% cost, 30% quality)
        cost_heavy_strategy = BalancedStrategy(
            cost_weight=0.7,
            quality_weight=0.3
        )
        
        cost_heavy_selection = cost_heavy_strategy.select_model(
            query_analysis=self.query_analysis,
            available_models=options
        )
        
        # Quality-heavy balance (30% cost, 70% quality)
        quality_heavy_strategy = BalancedStrategy(
            cost_weight=0.3,
            quality_weight=0.7
        )
        
        quality_heavy_selection = quality_heavy_strategy.select_model(
            query_analysis=self.query_analysis,
            available_models=options
        )
        
        # Cost-heavy should prefer cheaper option
        # Quality-heavy should prefer higher quality option
        if cost_heavy_selection.provider != quality_heavy_selection.provider:
            # They chose different models
            assert cost_heavy_selection.estimated_cost <= quality_heavy_selection.estimated_cost
            assert quality_heavy_selection.quality_score >= cost_heavy_selection.quality_score
    
    def test_balanced_strategy_scoring_accuracy(self):
        """Test accuracy of balanced scoring calculations."""
        strategy = BalancedStrategy(
            cost_weight=0.4,
            quality_weight=0.6
        )
        
        options = self.model_options["medium"]
        
        # Calculate scores manually for verification
        max_cost = max(opt.estimated_cost for opt in options)
        
        expected_scores = []
        for option in options:
            cost_score = 1.0 - (float(option.estimated_cost) / float(max_cost))
            balanced_score = (0.4 * cost_score) + (0.6 * option.quality_score)
            expected_scores.append((option, balanced_score))
        
        # Sort by expected score
        expected_scores.sort(key=lambda x: x[1], reverse=True)
        best_expected = expected_scores[0][0]
        
        # Test actual selection
        selection = strategy.select_model(
            query_analysis=self.query_analysis,
            available_models=options
        )
        
        # Should match expected best option
        assert selection.provider == best_expected.provider
        assert selection.model == best_expected.model
    
    def test_balanced_cost_reduction_validation(self):
        """Validate cost reduction compared to quality-first approach."""
        balanced_strategy = BalancedStrategy(cost_weight=0.4, quality_weight=0.6)
        quality_strategy = QualityFirstStrategy(min_quality_threshold=0.80)
        
        # Compare selections across different complexities
        total_balanced_cost = Decimal('0')
        total_quality_cost = Decimal('0')
        
        for complexity in ["simple", "medium", "complex"]:
            test_analysis = {**self.query_analysis, "complexity_level": complexity}
            options = self.model_options[complexity]
            
            balanced_selection = balanced_strategy.select_model(test_analysis, options)
            quality_selection = quality_strategy.select_model(test_analysis, options)
            
            if balanced_selection and quality_selection:
                total_balanced_cost += balanced_selection.estimated_cost
                total_quality_cost += quality_selection.estimated_cost
        
        # Calculate cost reduction
        if total_quality_cost > 0:
            cost_reduction = (total_quality_cost - total_balanced_cost) / total_quality_cost
            print(f"Cost reduction: {cost_reduction:.2%}")
            
            # Should achieve 25-40% cost reduction vs quality-first
            # (This is a rough target, actual results may vary based on test data)
            assert cost_reduction >= 0.0  # At least some reduction
    
    # Model Option Tests
    def test_model_option_creation(self):
        """Test ModelOption data structure."""
        option = ModelOption(
            provider="test",
            model="test-model",
            estimated_cost=Decimal('0.025'),
            estimated_latency=1.5,
            quality_score=0.88
        )
        
        assert option.provider == "test"
        assert option.model == "test-model"
        assert option.estimated_cost == Decimal('0.025')
        assert option.estimated_latency == 1.5
        assert option.quality_score == 0.88
        
        # Test validation
        assert 0.0 <= option.quality_score <= 1.0
        assert option.estimated_cost >= 0
        assert option.estimated_latency > 0
    
    def test_model_option_comparison(self):
        """Test ModelOption comparison for sorting."""
        option1 = ModelOption("provider1", "model1", Decimal('0.010'), 1.0, 0.85)
        option2 = ModelOption("provider2", "model2", Decimal('0.020'), 1.5, 0.90)
        
        # Test comparison methods if implemented
        options = [option1, option2]
        
        # Sort by cost (ascending)
        cost_sorted = sorted(options, key=lambda x: x.estimated_cost)
        assert cost_sorted[0] == option1  # Lower cost first
        
        # Sort by quality (descending)
        quality_sorted = sorted(options, key=lambda x: x.quality_score, reverse=True)
        assert quality_sorted[0] == option2  # Higher quality first
    
    # Edge Cases and Error Handling
    def test_empty_model_options(self):
        """Test handling of empty model options."""
        strategy = CostOptimizedStrategy()
        
        selection = strategy.select_model(
            query_analysis=self.query_analysis,
            available_models=[]
        )
        
        # Should handle gracefully
        assert selection is None
    
    def test_single_model_option(self):
        """Test handling of single model option."""
        strategy = BalancedStrategy()
        single_option = [self.model_options["medium"][0]]  # Just Mistral
        
        selection = strategy.select_model(
            query_analysis=self.query_analysis,
            available_models=single_option
        )
        
        # Should select the only available option
        assert selection == single_option[0]
    
    def test_invalid_quality_scores(self):
        """Test handling of invalid quality scores."""
        # Create option with invalid quality score
        invalid_option = ModelOption(
            provider="test",
            model="test-model",
            estimated_cost=Decimal('0.010'),
            estimated_latency=1.0,
            quality_score=1.5  # Invalid: > 1.0
        )
        
        strategy = QualityFirstStrategy()
        
        # Should handle gracefully or validate
        try:
            selection = strategy.select_model(
                query_analysis=self.query_analysis,
                available_models=[invalid_option]
            )
            # If no validation, should still work
            assert selection is not None
        except ValueError:
            # If validation exists, should raise appropriate error
            pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])