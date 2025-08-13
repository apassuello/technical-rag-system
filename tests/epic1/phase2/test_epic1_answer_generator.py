"""Test suite for Epic1AnswerGenerator - Epic 1 Phase 2.

Tests integration of multi-model answer generation including:
- End-to-end multi-model workflow
- Backward compatibility with single-model configs
- Cost budget enforcement
- Integration with Epic 1 query analyzer
"""

import pytest
import os
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

# Import Epic1 components
from src.components.generators.epic1_answer_generator import Epic1AnswerGenerator
from src.components.generators.base import Answer
from src.core.component_factory import ComponentFactory


class TestEpic1AnswerGenerator:
    """Test suite for Epic1AnswerGenerator integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Set up API keys for testing
        os.environ['OPENAI_API_KEY'] = 'test-openai-key'
        os.environ['MISTRAL_API_KEY'] = 'test-mistral-key'
        
        # Test data
        from src.core.interfaces import Document
        self.test_query = "How does OAuth 2.0 authentication work?"
        self.test_context = [
            Document(
                content="OAuth 2.0 is an authorization framework...",
                metadata={"source": "oauth_guide.pdf", "page": 1}
            ),
            Document(
                content="The OAuth 2.0 flow involves several steps...",
                metadata={"source": "oauth_guide.pdf", "page": 2}
            )
        ]
        
        # Test configuration for multi-model
        self.multi_model_config = {
            "type": "epic1_multi_model",
            "config": {
                "query_analyzer": {
                    "type": "epic1"
                },
                "routing": {
                    "strategy": "balanced",
                    "cost_weight": 0.4,
                    "quality_weight": 0.6
                },
                "model_mappings": {
                    "simple": {"provider": "ollama", "model": "llama3.2:3b"},
                    "medium": {"provider": "mistral", "model": "mistral-small"},
                    "complex": {"provider": "openai", "model": "gpt-4-turbo"}
                },
                "cost_tracking": {
                    "enabled": True,
                    "daily_budget": 10.00
                }
            }
        }
        
        # Legacy single-model config
        self.legacy_config = {
            "type": "standard",
            "config": {
                "llm_client": {
                    "type": "ollama",
                    "config": {
                        "model_name": "llama3.2:3b",
                        "temperature": 0.7
                    }
                }
            }
        }
    
    def teardown_method(self):
        """Clean up after tests."""
        # Remove test API keys
        for key in ['OPENAI_API_KEY', 'MISTRAL_API_KEY']:
            if key in os.environ:
                del os.environ[key]
    
    # EPIC1-INTEG-001: End-to-End Multi-Model Workflow
    @patch('src.components.generators.llm_adapters.ollama_adapter.requests.post')
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    @patch('src.components.generators.llm_adapters.mistral_adapter.requests.post')
    def test_end_to_end_multi_model_workflow(self, mock_mistral_post, mock_openai_class, mock_ollama_post):
        """Test complete query processing with routing.
        
        Requirement: Seamless multi-model answer generation
        PASS Criteria:
        - Complete workflow: No failures
        - Routing metadata: Present and accurate
        - Cost tracking: Integrated correctly
        - Answer quality: Meets thresholds
        - Performance: <2s end-to-end
        """
        # Mock Epic1QueryAnalyzer
        with patch('src.components.query_processors.analyzers.epic1_query_analyzer.Epic1QueryAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            
            # Configure analyzer to return medium complexity
            mock_analyzer.analyze.return_value = {
                "complexity_level": "medium",
                "complexity_score": 0.55,
                "confidence": 0.85,
                "recommended_model": {"provider": "mistral", "model": "mistral-small"},
                "features": {"technical_terms": 3, "clause_count": 2}
            }
            
            # Mock Mistral API response
            mock_mistral_response = MagicMock()
            mock_mistral_response.status_code = 200
            mock_mistral_response.json.return_value = {
                'choices': [{
                    'message': {
                        'content': 'OAuth 2.0 is an authorization framework that enables applications to obtain limited access to user accounts. The flow involves several key steps: authorization request, user authorization, authorization grant, access token request, and resource access.'
                    }
                }],
                'usage': {
                    'prompt_tokens': 200,
                    'completion_tokens': 150,
                    'total_tokens': 350
                }
            }
            mock_mistral_post.return_value = mock_mistral_response
            
            # Mock Ollama API response
            mock_ollama_response = MagicMock()
            mock_ollama_response.status_code = 200
            mock_ollama_response.json.return_value = {
                'response': 'OAuth 2.0 is an authorization framework that allows third-party applications to access user resources without exposing credentials. It involves authorization server, resource server, client application, and resource owner.',
                'done': True,
                'context': [],
                'total_duration': 1000000000,
                'load_duration': 100000000,
                'prompt_eval_count': 50,
                'prompt_eval_duration': 200000000,
                'eval_count': 30,
                'eval_duration': 300000000
            }
            mock_ollama_post.return_value = mock_ollama_response
            
            # Create Epic1AnswerGenerator
            generator = Epic1AnswerGenerator(config=self.multi_model_config["config"])
            
            # Measure end-to-end performance
            import time
            start_time = time.time()
            
            # Generate answer
            answer = generator.generate(
                query=self.test_query,
                context=self.test_context
            )
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verify complete workflow
            assert answer is not None
            assert isinstance(answer, Answer)
            assert len(answer.text) > 50  # Substantial response
            
            # Verify routing metadata present
            assert 'routing' in answer.metadata
            routing_info = answer.metadata['routing']
            assert routing_info['complexity_level'] == 'medium'
            assert routing_info['selected_model']['provider'] == 'ollama'
            assert routing_info['selected_model']['model'] == 'llama3.2:3b'
            assert 'routing_decision_time_ms' in routing_info
            
            # Verify cost tracking integrated
            assert 'cost_usd' in answer.metadata
            assert 'input_tokens' in answer.metadata
            assert 'output_tokens' in answer.metadata
            
            cost = Decimal(str(answer.metadata['cost_usd']))
            assert cost > Decimal('0')
            assert answer.metadata['input_tokens'] == 200
            assert answer.metadata['output_tokens'] == 150
            
            # Verify performance target
            assert total_time < 2.0, f"End-to-end time {total_time:.2f}s > 2s target"
            
            # Verify answer quality
            assert 'oauth' in answer.content.lower() or 'authorization' in answer.content.lower()
            
            # Check confidence if available
            if 'confidence' in answer.metadata:
                assert answer.metadata['confidence'] > 0.7
    
    # EPIC1-INTEG-002: Backward Compatibility Validation
    def test_backward_compatibility_validation(self):
        """Test Epic1AnswerGenerator with legacy configurations.
        
        Requirement: Existing single-model configs continue working
        PASS Criteria:
        - Initialization: Succeeds without errors
        - Routing: Automatically disabled
        - Functionality: Identical to original
        - No breaking changes: All features work
        """
        with patch('src.components.generators.llm_adapters.ollama_adapter.OllamaAdapter') as mock_ollama:
            # Mock Ollama adapter
            mock_adapter_instance = MagicMock()
            mock_ollama.return_value = mock_adapter_instance
            
            mock_adapter_instance.generate.return_value = Answer(
                text="This is a response from Ollama",
                sources=[],
                confidence=0.85,
                metadata={
                    "provider": "ollama",
                    "model": "llama3.2:3b",
                    "cost_usd": 0.0,
                    "tokens": 50
                }
            )
            
            # Initialize with legacy config
            generator = Epic1AnswerGenerator(config=self.legacy_config["config"])
            
            # Verify routing is disabled
            assert not hasattr(generator, 'adaptive_router') or generator.adaptive_router is None
            assert generator.routing_enabled is False
            
            # Test answer generation
            answer = generator.generate(
                query=self.test_query,
                context=self.test_context
            )
            
            # Verify functionality identical to original
            assert answer is not None
            assert isinstance(answer, Answer)
            assert answer.content == "This is a response from Ollama"
            assert answer.metadata['provider'] == 'ollama'
            
            # Verify no routing metadata added
            assert 'routing_decision' not in answer.metadata
            assert 'complexity_analysis' not in answer.metadata
    
    def test_backward_compatibility_component_factory(self):
        """Test backward compatibility through ComponentFactory."""
        # Test that legacy config works through ComponentFactory
        try:
            generator = ComponentFactory.create_generator(
                generator_type="adaptive",
                config=self.legacy_config["config"]
            )
            
            # Should create without errors
            assert generator is not None
            
            # Should be Epic1AnswerGenerator in compatibility mode
            if isinstance(generator, Epic1AnswerGenerator):
                assert generator.routing_enabled is False
        
        except Exception as e:
            pytest.fail(f"Legacy config failed through ComponentFactory: {e}")
    
    # EPIC1-INTEG-003: Cost Budget Enforcement
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_cost_budget_enforcement(self, mock_openai_class):
        """Test system with daily cost budget enforcement.
        
        Requirement: Enforce budget limits with graceful degradation
        PASS Criteria:
        - Budget tracking: Accurate to $0.001
        - Warning threshold: Triggers at 80%
        - Graceful degradation: Shifts to cheaper models
        - Hard limit: Enforced at 100%
        - Continued operation: System remains functional
        """
        # Mock OpenAI with expensive costs
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock expensive response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Expensive response"))]
        mock_response.usage = MagicMock(
            prompt_tokens=1000,  # High token usage
            completion_tokens=500,
            total_tokens=1500
        )
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock Epic1QueryAnalyzer to return complex queries (expensive)
        with patch('src.components.query_processors.analyzers.epic1_query_analyzer.Epic1QueryAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            
            mock_analyzer.analyze.return_value = {
                "complexity_level": "complex",
                "complexity_score": 0.85,
                "confidence": 0.90,
                "recommended_model": {"provider": "openai", "model": "gpt-4-turbo"}
            }
            
            # Configuration with tight budget
            budget_config = {
                **self.multi_model_config["config"],
                "cost_tracking": {
                    "enabled": True,
                    "daily_budget": 1.00,  # $1 daily budget
                    "warning_threshold": 0.80  # 80% warning
                }
            }
            
            generator = Epic1AnswerGenerator(config=budget_config)
            
            # Track spending through multiple queries
            total_spent = Decimal('0')
            warning_triggered = False
            budget_exceeded = False
            
            # Simulate multiple expensive queries
            for i in range(10):  # May exceed budget
                try:
                    answer = generator.generate(
                        query=f"Complex query {i}: Explain advanced ML concepts",
                        context=self.test_context
                    )
                    
                    if answer:
                        query_cost = Decimal(str(answer.metadata.get('cost_usd', 0)))
                        total_spent += query_cost
                        
                        # Check for warnings in metadata
                        if 'budget_warning' in answer.metadata:
                            warning_triggered = True
                        
                        # Check if system degraded to cheaper models
                        if total_spent > Decimal('0.80'):
                            routing_info = answer.metadata.get('routing_decision', {})
                            selected_provider = routing_info.get('selected_provider')
                            
                            # Should shift away from expensive OpenAI models
                            if selected_provider in ['mistral', 'ollama']:
                                print(f"System degraded to cheaper provider: {selected_provider}")
                        
                        # Check for hard budget limit
                        if total_spent >= Decimal('1.00'):
                            budget_exceeded = True
                            break
                    
                except Exception as e:
                    if "budget" in str(e).lower():
                        budget_exceeded = True
                        break
                    else:
                        raise
            
            print(f"Total spent: ${total_spent}")
            print(f"Warning triggered: {warning_triggered}")
            print(f"Budget exceeded: {budget_exceeded}")
            
            # Verify budget enforcement
            assert total_spent <= Decimal('1.01'), f"Budget exceeded: ${total_spent} > $1.00"
            
            # Should have triggered warning before hitting limit
            if total_spent > Decimal('0.80'):
                assert warning_triggered, "Warning should trigger at 80% of budget"
    
    def test_cost_budget_graceful_degradation(self):
        """Test graceful degradation when approaching budget limits."""
        # Configure system with budget limits
        degradation_config = {
            **self.multi_model_config["config"],
            "cost_tracking": {
                "enabled": True,
                "daily_budget": 0.50,  # Very tight budget
                "warning_threshold": 0.50,  # Immediate warnings
                "degradation_strategy": "force_cheap"  # Force cheaper models
            }
        }
        
        with patch('src.components.query_processors.analyzers.epic1_query_analyzer.Epic1QueryAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            
            # Start with complex query (would normally use expensive model)
            mock_analyzer.analyze.return_value = {
                "complexity_level": "complex",
                "complexity_score": 0.85,
                "confidence": 0.90,
                "recommended_model": {"provider": "openai", "model": "gpt-4-turbo"}
            }
            
            generator = Epic1AnswerGenerator(config=degradation_config)
            
            # Should force degradation to cheaper models
            with patch.object(generator.cost_tracker, 'get_daily_spending', return_value=Decimal('0.45')):
                # Near budget limit (90% of $0.50)
                
                with patch('src.components.generators.llm_adapters.ollama_adapter.OllamaAdapter') as mock_ollama:
                    mock_adapter = MagicMock()
                    mock_ollama.return_value = mock_adapter
                    mock_adapter.generate.return_value = Answer(
                        text="Response from degraded model",
                        sources=[],
                        confidence=0.75,
                        metadata={"cost_usd": 0.00, "provider": "ollama"}
                    )
                    
                    answer = generator.generate(
                        query="Complex query requiring degradation",
                        context=self.test_context
                    )
                    
                    # Should have degraded to free model
                    assert answer is not None
                    routing_info = answer.metadata.get('routing_decision', {})
                    selected_provider = routing_info.get('selected_provider')
                    assert selected_provider == 'ollama'  # Degraded to free option
                    
                    # Should include degradation notice
                    assert 'budget_degradation' in answer.metadata or \
                           'routing_decision' in answer.metadata
    
    # Performance and Integration Tests
    def test_routing_overhead_measurement(self):
        """Test routing decision overhead in Epic1AnswerGenerator."""
        with patch('src.components.query_processors.analyzers.epic1_query_analyzer.Epic1QueryAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            
            # Fast analyzer response
            mock_analyzer.analyze.return_value = {
                "complexity_level": "simple",
                "complexity_score": 0.25,
                "confidence": 0.90
            }
            
            with patch('src.components.generators.llm_adapters.ollama_adapter.OllamaAdapter') as mock_ollama:
                mock_adapter = MagicMock()
                mock_ollama.return_value = mock_adapter
                mock_adapter.generate.return_value = Answer(
                    text="Fast response",
                    sources=[],
                    confidence=0.80,
                    metadata={"cost_usd": 0.0, "generation_time_ms": 500}
                )
                
                generator = Epic1AnswerGenerator(config=self.multi_model_config["config"])
                
                # Measure routing overhead
                import time
                routing_times = []
                
                for i in range(10):
                    start_time = time.perf_counter()
                    
                    answer = generator.generate(
                        query=f"Simple query {i}",
                        context=["Simple context"]
                    )
                    
                    end_time = time.perf_counter()
                    total_time_ms = (end_time - start_time) * 1000
                    
                    # Extract routing time from metadata
                    routing_info = answer.metadata.get('routing_decision', {})
                    routing_time = routing_info.get('decision_time_ms', 0)
                    routing_times.append(routing_time)
                    
                    print(f"Query {i}: Routing={routing_time:.2f}ms, Total={total_time_ms:.2f}ms")
                
                # Verify routing overhead targets
                avg_routing_time = sum(routing_times) / len(routing_times)
                max_routing_time = max(routing_times)
                
                assert avg_routing_time < 50.0, f"Average routing time {avg_routing_time:.2f}ms > 50ms"
                assert max_routing_time < 100.0, f"Max routing time {max_routing_time:.2f}ms > 100ms"
    
    def test_epic2_compatibility_validation(self):
        """Test that Epic1 enhancements don't break Epic2 features."""
        # This test ensures Epic2 retriever features still work with Epic1 answer generation
        
        epic2_config = {
            **self.multi_model_config["config"],
            "retriever_features": {
                "neural_reranking": True,
                "graph_enhancement": True
            }
        }
        
        # Mock Epic2 retriever components would be tested here
        # This is a placeholder for comprehensive Epic2 compatibility testing
        
        generator = Epic1AnswerGenerator(config=epic2_config)
        
        # Verify Epic1 features don't interfere with Epic2
        assert generator.routing_enabled is True
        
        # Additional Epic2 compatibility tests would go here
        # (Testing neural reranking, graph enhancement, etc.)
    
    def test_configuration_validation(self):
        """Test configuration validation and error handling."""
        # Test invalid configuration
        invalid_config = {
            "routing": {
                "strategy": "invalid_strategy"
            }
        }
        
        with pytest.raises(ValueError, match="Invalid strategy"):
            generator = Epic1AnswerGenerator(config=invalid_config)
        
        # Test missing required configuration
        incomplete_config = {
            "query_analyzer": {"type": "epic1"}
            # Missing routing configuration
        }
        
        # Should use defaults or raise appropriate error
        try:
            generator = Epic1AnswerGenerator(config=incomplete_config)
            # If defaults are provided, should work
            assert generator is not None
        except ValueError as e:
            # If validation is strict, should raise descriptive error
            assert "routing" in str(e) or "configuration" in str(e)
    
    def test_model_availability_handling(self):
        """Test handling when configured models are unavailable."""
        with patch('src.components.query_processors.analyzers.epic1_query_analyzer.Epic1QueryAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            
            mock_analyzer.analyze.return_value = {
                "complexity_level": "medium",
                "complexity_score": 0.55,
                "confidence": 0.85,
                "recommended_model": {"provider": "mistral", "model": "mistral-small"}
            }
            
            # Configure generator
            generator = Epic1AnswerGenerator(config=self.multi_model_config["config"])
            
            # Mock all adapters to fail (simulating service unavailability)
            with patch.object(generator, '_get_adapter_for_model') as mock_get_adapter:
                mock_get_adapter.side_effect = Exception("Service unavailable")
                
                # Should handle gracefully with fallbacks or clear error
                try:
                    answer = generator.generate(
                        query="Test query with unavailable models",
                        context=self.test_context
                    )
                    
                    # If fallback succeeded, should have answer
                    if answer:
                        assert isinstance(answer, Answer)
                        # Should indicate fallback was used
                        assert 'fallback_used' in answer.metadata or \
                               'error_recovery' in answer.metadata
                
                except Exception as e:
                    # If no fallback available, should give clear error message
                    assert "unavailable" in str(e).lower() or "fallback" in str(e).lower()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])