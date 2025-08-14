#!/usr/bin/env python3
"""
Test script to verify Epic1AnswerGenerator cost tracking integration.

This script tests the cost tracking functionality without external API dependencies
by using mocked Ollama responses and verifying that cost metadata is properly added.
"""

import os
import sys
import logging
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.components.generators.epic1_answer_generator import Epic1AnswerGenerator
from src.core.interfaces import Document, Answer

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_cost_tracking_integration():
    """Test that Epic1AnswerGenerator properly adds cost metadata to answers."""
    
    print("🧪 Testing Epic1AnswerGenerator cost tracking integration...")
    
    # Test configuration for multi-model routing
    config = {
        "routing": {
            "enabled": True,
            "default_strategy": "balanced",
            "query_analyzer": {
                "type": "epic1",
                "config": {}
            },
            "strategies": {
                "cost_optimized": {},
                "quality_first": {},
                "balanced": {}
            }
        },
        "fallback": {
            "enabled": True,
            "fallback_model": "ollama/llama3.2:3b"
        },
        "cost_tracking": {
            "enabled": True,
            "precision_places": 6
        }
    }
    
    # Test data
    test_query = "How does OAuth 2.0 authentication work?"
    test_context = [
        Document(
            content="OAuth 2.0 is an authorization framework...",
            metadata={"source": "oauth_guide.pdf", "page": 1}
        ),
        Document(
            content="The OAuth 2.0 flow involves several steps...",
            metadata={"source": "oauth_guide.pdf", "page": 2}
        )
    ]
    
    try:
        # Mock Epic1QueryAnalyzer to return simple complexity (routes to Ollama - free)
        with patch('src.components.query_processors.analyzers.epic1_query_analyzer.Epic1QueryAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            
            # Configure analyzer to return simple complexity (routes to Ollama)
            mock_analyzer.analyze.return_value = {
                "complexity_level": "simple",
                "complexity_score": 0.25,
                "confidence": 0.90,
                "recommended_model": {"provider": "ollama", "model": "llama3.2:3b"},
                "features": {"technical_terms": 1, "clause_count": 1}
            }
            
            # Mock Ollama adapter to avoid real API calls
            with patch('src.components.generators.llm_adapters.ollama_adapter.OllamaAdapter') as mock_ollama:
                mock_adapter = MagicMock()
                mock_ollama.return_value = mock_adapter
                
                # Mock Ollama response
                mock_answer = Answer(
                    text="OAuth 2.0 is an authorization framework that enables applications to obtain limited access to user accounts. The framework involves authorization server, resource server, client application, and resource owner.",
                    sources=test_context,
                    confidence=0.85,
                    metadata={
                        "provider": "ollama",
                        "model": "llama3.2:3b",
                        "generation_time": 1.2
                    }
                )
                mock_adapter.generate.return_value = mock_answer
                
                # Create Epic1AnswerGenerator with routing enabled
                generator = Epic1AnswerGenerator(config=config)
                
                print(f"✅ Generator initialized (routing_enabled: {generator.routing_enabled})")
                
                # Generate answer
                answer = generator.generate(
                    query=test_query,
                    context=test_context
                )
                
                print(f"✅ Answer generated: {len(answer.text)} chars")
                
                # Verify basic answer properties
                assert answer is not None
                assert isinstance(answer, Answer)
                assert len(answer.text) > 50
                
                print("✅ Basic answer validation passed")
                
                # Verify routing metadata is present
                assert 'routing' in answer.metadata, "Missing routing metadata"
                routing_info = answer.metadata['routing']
                assert routing_info['complexity_level'] == 'simple'
                assert routing_info['selected_model']['provider'] == 'ollama'
                assert routing_info['selected_model']['model'] == 'llama3.2:3b'
                
                print("✅ Routing metadata validation passed")
                
                # Verify cost tracking metadata is present
                assert 'cost_usd' in answer.metadata, "Missing cost_usd in metadata"
                assert 'input_tokens' in answer.metadata, "Missing input_tokens in metadata"
                assert 'output_tokens' in answer.metadata, "Missing output_tokens in metadata"
                
                print("✅ Cost metadata fields present")
                
                # Verify cost values
                cost = Decimal(str(answer.metadata['cost_usd']))
                input_tokens = answer.metadata['input_tokens']
                output_tokens = answer.metadata['output_tokens']
                
                # For Ollama (free), cost should be 0
                assert cost == Decimal('0.0'), f"Expected cost 0.0 for Ollama, got {cost}"
                assert input_tokens > 0, f"Expected positive input_tokens, got {input_tokens}"
                assert output_tokens > 0, f"Expected positive output_tokens, got {output_tokens}"
                
                print(f"✅ Cost tracking validation passed:")
                print(f"   - Cost: ${cost}")
                print(f"   - Input tokens: {input_tokens}")
                print(f"   - Output tokens: {output_tokens}")
                
                # Verify cost breakdown is present
                assert 'cost_breakdown' in answer.metadata, "Missing cost_breakdown in metadata"
                cost_breakdown = answer.metadata['cost_breakdown']
                assert 'input_cost' in cost_breakdown, "Missing input_cost in breakdown"
                assert 'output_cost' in cost_breakdown, "Missing output_cost in breakdown"
                
                print("✅ Cost breakdown validation passed")
                
                print("\n🎉 All cost tracking integration tests PASSED!")
                return True
                
    except Exception as e:
        print(f"❌ Cost tracking integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cost_tracking_with_paid_model():
    """Test cost tracking with a paid model (Mistral) using mocked responses."""
    
    print("\n🧪 Testing Epic1AnswerGenerator cost tracking with paid model...")
    
    # Configuration that will route to Mistral
    config = {
        "routing": {
            "enabled": True,
            "default_strategy": "balanced",
            "query_analyzer": {
                "type": "epic1",
                "config": {}
            }
        },
        "cost_tracking": {
            "enabled": True,
            "precision_places": 6
        }
    }
    
    test_query = "How does OAuth 2.0 authentication work?"
    test_context = [
        Document(
            content="OAuth 2.0 is an authorization framework...",
            metadata={"source": "oauth_guide.pdf", "page": 1}
        )
    ]
    
    try:
        # Mock Epic1QueryAnalyzer to return medium complexity (routes to Mistral)
        with patch('src.components.query_processors.analyzers.epic1_query_analyzer.Epic1QueryAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            
            mock_analyzer.analyze.return_value = {
                "complexity_level": "medium",
                "complexity_score": 0.55,
                "confidence": 0.85,
                "recommended_model": {"provider": "mistral", "model": "mistral-small"},
                "features": {"technical_terms": 3, "clause_count": 2}
            }
            
            # Mock Mistral adapter to avoid real API calls
            with patch('src.components.generators.llm_adapters.mistral_adapter.MistralAdapter') as mock_mistral:
                mock_adapter = MagicMock()
                mock_mistral.return_value = mock_adapter
                
                # Mock Mistral response with realistic content
                mock_answer = Answer(
                    text="OAuth 2.0 is an authorization framework that enables applications to obtain limited access to user accounts. The flow involves several key steps: authorization request, user authorization, authorization grant, access token request, and resource access.",
                    sources=test_context,
                    confidence=0.85,
                    metadata={
                        "provider": "mistral",
                        "model": "mistral-small",
                        "generation_time": 0.8
                    }
                )
                mock_adapter.generate.return_value = mock_answer
                
                # Create Epic1AnswerGenerator
                generator = Epic1AnswerGenerator(config=config)
                
                # Generate answer
                answer = generator.generate(
                    query=test_query,
                    context=test_context
                )
                
                # Verify cost tracking for paid model
                assert 'cost_usd' in answer.metadata
                cost = Decimal(str(answer.metadata['cost_usd']))
                
                # For Mistral, cost should be > 0
                assert cost > Decimal('0.0'), f"Expected cost > 0.0 for Mistral, got {cost}"
                
                # Verify realistic token counts based on text length
                input_tokens = answer.metadata['input_tokens']
                output_tokens = answer.metadata['output_tokens']
                
                # Rough estimation based on text length
                expected_input_tokens = len(test_query.split()) * 1.3
                expected_output_tokens = len(answer.text.split()) * 1.3
                
                # Allow some variance in token estimation
                assert abs(input_tokens - expected_input_tokens) < 5, f"Input tokens {input_tokens} too far from expected {expected_input_tokens}"
                assert abs(output_tokens - expected_output_tokens) < 10, f"Output tokens {output_tokens} too far from expected {expected_output_tokens}"
                
                print(f"✅ Paid model cost tracking validation passed:")
                print(f"   - Cost: ${cost}")
                print(f"   - Input tokens: {input_tokens}")
                print(f"   - Output tokens: {output_tokens}")
                
                return True
                
    except Exception as e:
        print(f"❌ Paid model cost tracking test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Testing Epic1AnswerGenerator Cost Tracking Integration\n")
    
    # Test 1: Basic cost tracking with free model (Ollama)
    test1_result = test_cost_tracking_integration()
    
    # Test 2: Cost tracking with paid model (Mistral) 
    test2_result = test_cost_tracking_with_paid_model()
    
    if test1_result and test2_result:
        print("\n🎉 ALL TESTS PASSED - Cost tracking integration is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Cost tracking integration needs fixes")
        sys.exit(1)