#!/usr/bin/env python3
"""
Test script to verify improved Epic1AnswerGenerator cost tracking with actual token counts.
"""

import os
import sys
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.components.generators.epic1_answer_generator import Epic1AnswerGenerator
from src.core.interfaces import Document, Answer

def test_cost_tracking_with_api_tokens():
    """Test that Epic1AnswerGenerator uses actual API token counts when available."""
    
    print("🧪 Testing Epic1AnswerGenerator cost tracking with API token counts...")
    
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
        # Mock Epic1QueryAnalyzer to return medium complexity
        with patch('src.components.query_processors.analyzers.epic1_query_analyzer.Epic1QueryAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            
            mock_analyzer.analyze.return_value = {
                "complexity_level": "medium",
                "complexity_score": 0.55,
                "confidence": 0.85,
                "recommended_model": {"provider": "ollama", "model": "llama3.2:3b"},
                "features": {"technical_terms": 3, "clause_count": 2}
            }
            
            # Mock Ollama adapter with API-style token counts in metadata
            with patch('src.components.generators.llm_adapters.ollama_adapter.OllamaAdapter') as mock_ollama:
                mock_adapter = MagicMock()
                mock_ollama.return_value = mock_adapter
                
                # Mock response with specific token counts (like the test expects)
                mock_answer = Answer(
                    text="OAuth 2.0 is an authorization framework that enables applications to obtain limited access to user accounts. The flow involves several key steps: authorization request, user authorization, authorization grant, access token request, and resource access.",
                    sources=test_context,
                    confidence=0.85,
                    metadata={
                        "provider": "ollama",
                        "model": "llama3.2:3b",
                        "generation_time": 1.2,
                        # Add usage info like real API responses
                        "usage": {
                            "prompt_tokens": 200,
                            "completion_tokens": 150,
                            "total_tokens": 350
                        }
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
                
                # Verify cost tracking uses API token counts
                assert 'cost_usd' in answer.metadata
                assert 'input_tokens' in answer.metadata
                assert 'output_tokens' in answer.metadata
                
                # Check that it uses the API token counts, not text estimation
                assert answer.metadata['input_tokens'] == 200, f"Expected 200 input tokens, got {answer.metadata['input_tokens']}"
                assert answer.metadata['output_tokens'] == 150, f"Expected 150 output tokens, got {answer.metadata['output_tokens']}"
                
                print(f"✅ API token count test passed:")
                print(f"   - Input tokens: {answer.metadata['input_tokens']} (expected 200)")
                print(f"   - Output tokens: {answer.metadata['output_tokens']} (expected 150)")
                print(f"   - Cost: ${answer.metadata['cost_usd']}")
                
                return True
                
    except Exception as e:
        print(f"❌ API token count test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cost_tracking_fallback_estimation():
    """Test that cost tracking falls back to text estimation when API tokens unavailable."""
    
    print("\n🧪 Testing Epic1AnswerGenerator cost tracking fallback to text estimation...")
    
    config = {
        "routing": {
            "enabled": True,
            "default_strategy": "balanced"
        },
        "cost_tracking": {
            "enabled": True
        }
    }
    
    test_query = "Simple query"
    test_context = [
        Document(
            content="Simple content",
            metadata={"source": "test.pdf", "page": 1}
        )
    ]
    
    try:
        with patch('src.components.query_processors.analyzers.epic1_query_analyzer.Epic1QueryAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            
            mock_analyzer.analyze.return_value = {
                "complexity_level": "simple",
                "complexity_score": 0.25,
                "confidence": 0.90,
                "recommended_model": {"provider": "ollama", "model": "llama3.2:3b"}
            }
            
            with patch('src.components.generators.llm_adapters.ollama_adapter.OllamaAdapter') as mock_ollama:
                mock_adapter = MagicMock()
                mock_ollama.return_value = mock_adapter
                
                # Mock response WITHOUT usage info (no API token counts)
                mock_answer = Answer(
                    text="Simple response text",
                    sources=test_context,
                    confidence=0.80,
                    metadata={
                        "provider": "ollama",
                        "model": "llama3.2:3b",
                        "generation_time": 0.5
                        # No usage field - should trigger text estimation
                    }
                )
                mock_adapter.generate.return_value = mock_answer
                
                generator = Epic1AnswerGenerator(config=config)
                answer = generator.generate(query=test_query, context=test_context)
                
                # Verify cost tracking falls back to text estimation
                assert 'input_tokens' in answer.metadata
                assert 'output_tokens' in answer.metadata
                
                # Calculate expected estimation
                expected_input = len(test_query.split()) * 1.3  # 2 * 1.3 = 2.6
                expected_output = len("Simple response text".split()) * 1.3  # 3 * 1.3 = 3.9
                
                # Should be close to text estimation (allowing for rounding)
                assert abs(answer.metadata['input_tokens'] - expected_input) < 1
                assert abs(answer.metadata['output_tokens'] - expected_output) < 1
                
                print(f"✅ Text estimation fallback test passed:")
                print(f"   - Input tokens: {answer.metadata['input_tokens']} (estimated from '{test_query}')")
                print(f"   - Output tokens: {answer.metadata['output_tokens']} (estimated from response)")
                
                return True
                
    except Exception as e:
        print(f"❌ Text estimation fallback test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Testing Improved Epic1AnswerGenerator Cost Tracking\n")
    
    # Test 1: Using API token counts when available
    test1_result = test_cost_tracking_with_api_tokens()
    
    # Test 2: Fallback to text estimation when API tokens unavailable
    test2_result = test_cost_tracking_fallback_estimation()
    
    if test1_result and test2_result:
        print("\n🎉 ALL TESTS PASSED - Improved cost tracking is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Cost tracking improvements need fixes")
        sys.exit(1)