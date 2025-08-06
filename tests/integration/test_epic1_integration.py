#!/usr/bin/env python3
"""
Integration tests for Epic 1 Query Analyzer with ModularQueryProcessor.

This module tests the integration of Epic1QueryAnalyzer with the 
ModularQueryProcessor and validates end-to-end query processing.
"""

import pytest
import sys
from pathlib import Path
import time
from typing import List, Dict, Any

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.components.query_processors import ModularQueryProcessor
from src.components.query_processors.base import QueryProcessorConfig
from src.core.interfaces import Document, Answer
from src.core.component_factory import ComponentFactory


class TestEpic1Integration:
    """Test Epic1QueryAnalyzer integration with ModularQueryProcessor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Epic 1 configuration
        self.epic1_config = {
            'type': 'modular',
            'analyzer': {
                'implementation': 'epic1',
                'config': {
                    'feature_extractor': {
                        'technical_terms': {
                            'domains': ['ml', 'rag', 'llm'],
                            'min_term_length': 3
                        },
                        'enable_entity_extraction': True
                    },
                    'complexity_classifier': {
                        'weights': {
                            'length': 0.20,
                            'syntactic': 0.25,
                            'vocabulary': 0.30,
                            'question': 0.15,
                            'ambiguity': 0.10
                        },
                        'thresholds': {
                            'simple': 0.35,
                            'complex': 0.70
                        }
                    },
                    'model_recommender': {
                        'strategy': 'balanced',
                        'model_mappings': {
                            'simple': {
                                'provider': 'ollama',
                                'model': 'llama3.2:3b',
                                'max_cost_per_query': 0.001,
                                'avg_latency_ms': 500
                            },
                            'medium': {
                                'provider': 'mistral',
                                'model': 'mistral-small',
                                'max_cost_per_query': 0.01,
                                'avg_latency_ms': 1000
                            },
                            'complex': {
                                'provider': 'openai',
                                'model': 'gpt-4-turbo',
                                'max_cost_per_query': 0.10,
                                'avg_latency_ms': 2000
                            }
                        }
                    }
                }
            },
            'selector': {
                'implementation': 'mmr',
                'config': {
                    'lambda_param': 0.5,
                    'max_tokens': 2048
                }
            },
            'assembler': {
                'implementation': 'rich',
                'config': {
                    'include_sources': True,
                    'format_citations': True
                }
            }
        }
        
        # Create sample documents for testing
        self.sample_documents = [
            Document(
                content="Retrieval-Augmented Generation (RAG) is a method that combines retrieval and generation.",
                metadata={"id": "doc1", "source": "rag_guide.pdf", "page": 1}
            ),
            Document(
                content="Transformers use attention mechanisms to process sequences in parallel.",
                metadata={"id": "doc2", "source": "transformers.pdf", "page": 5}
            ),
            Document(
                content="Dense embeddings capture semantic similarity between texts.",
                metadata={"id": "doc3", "source": "embeddings.pdf", "page": 3}
            )
        ]
    
    def test_modular_query_processor_with_epic1(self):
        """Test ModularQueryProcessor can use Epic1QueryAnalyzer."""
        # Create configuration
        config = QueryProcessorConfig(
            analyzer_type='epic1',
            analyzer_config=self.epic1_config['analyzer']['config'],
            selector_type='token_limit',
            selector_config={'max_tokens': 2048},
            assembler_type='standard',
            assembler_config={}
        )
        
        # Create processor
        processor = ModularQueryProcessor(config)
        
        # Verify Epic1QueryAnalyzer is being used
        assert processor._analyzer.__class__.__name__ == 'Epic1QueryAnalyzer'
        
        # Test analysis
        query = "How does transformer attention mechanism work?"
        analysis = processor.analyze_query(query)
        
        assert analysis is not None
        assert 'epic1_analysis' in analysis.metadata
        
        epic1_data = analysis.metadata['epic1_analysis']
        assert 'complexity_level' in epic1_data
        assert 'recommended_model' in epic1_data
    
    def test_epic1_metadata_flow(self):
        """Test Epic 1 metadata flows through the entire pipeline."""
        # Create processor with Epic 1 analyzer
        config = QueryProcessorConfig(
            analyzer_type='epic1',
            analyzer_config=self.epic1_config['analyzer']['config'],
            selector_type='token_limit',
            selector_config={'max_tokens': 2048},
            assembler_type='rich',
            assembler_config={'include_sources': True}
        )
        
        processor = ModularQueryProcessor(config)
        
        # Process different complexity queries
        queries = [
            ("What is RAG?", 'simple'),
            ("How does the retriever work in RAG?", 'simple'),
            ("Compare neural reranking strategies for technical documentation", 'medium')
        ]
        
        for query, expected_level in queries:
            # Analyze query
            analysis = processor.analyze_query(query)
            
            # Check Epic 1 metadata exists
            assert 'epic1_analysis' in analysis.metadata
            epic1_data = analysis.metadata['epic1_analysis']
            
            # Verify complexity assessment
            if expected_level == 'simple':
                assert epic1_data['complexity_level'] == 'simple'
                assert 'ollama' in epic1_data['recommended_model']
            
            # Select context (with mock documents)
            selection = processor.select_context(self.sample_documents, analysis)
            assert selection is not None
            
            # The Epic 1 metadata should be preserved
            assert analysis.metadata.get('epic1_analysis') is not None
    
    def test_performance_with_epic1(self):
        """Test performance meets <50ms target with Epic1QueryAnalyzer."""
        config = QueryProcessorConfig(
            analyzer_type='epic1',
            analyzer_config=self.epic1_config['analyzer']['config'],
            selector_type='token_limit',
            selector_config={'max_tokens': 2048},
            assembler_type='standard',
            assembler_config={}
        )
        
        processor = ModularQueryProcessor(config)
        
        queries = [
            "What is RAG?",
            "How does transformer attention work?",
            "Explain the difference between dense and sparse retrieval methods in information retrieval systems"
        ]
        
        for query in queries:
            start = time.time()
            analysis = processor.analyze_query(query)
            elapsed = (time.time() - start) * 1000
            
            # Should meet <50ms target
            assert elapsed < 50, f"Query '{query[:30]}...' took {elapsed:.1f}ms"
            
            # Verify Epic 1 analysis was performed
            assert 'epic1_analysis' in analysis.metadata
    
    def test_configuration_switching(self):
        """Test switching between different analyzer types."""
        # Start with NLP analyzer
        nlp_config = QueryProcessorConfig(
            analyzer_type='nlp',
            analyzer_config={},
            selector_type='token_limit',
            selector_config={'max_tokens': 2048},
            assembler_type='standard',
            assembler_config={}
        )
        
        nlp_processor = ModularQueryProcessor(nlp_config)
        assert nlp_processor._analyzer.__class__.__name__ == 'NLPAnalyzer'
        
        # Switch to Epic 1 analyzer
        epic1_config = QueryProcessorConfig(
            analyzer_type='epic1',
            analyzer_config=self.epic1_config['analyzer']['config'],
            selector_type='token_limit',
            selector_config={'max_tokens': 2048},
            assembler_type='standard',
            assembler_config={}
        )
        
        epic1_processor = ModularQueryProcessor(epic1_config)
        assert epic1_processor._analyzer.__class__.__name__ == 'Epic1QueryAnalyzer'
        
        # Test both work correctly
        query = "What is transformer architecture?"
        
        nlp_analysis = nlp_processor.analyze_query(query)
        assert 'epic1_analysis' not in nlp_analysis.metadata
        
        epic1_analysis = epic1_processor.analyze_query(query)
        assert 'epic1_analysis' in epic1_analysis.metadata
    
    def test_backward_compatibility(self):
        """Test Epic 1 doesn't break existing functionality."""
        # Use standard configuration without Epic 1
        standard_config = QueryProcessorConfig(
            analyzer_type='rule_based',
            analyzer_config={},
            selector_type='mmr',
            selector_config={'lambda_param': 0.5},
            assembler_type='standard',
            assembler_config={}
        )
        
        processor = ModularQueryProcessor(standard_config)
        
        # Should work without Epic 1
        query = "How does retrieval work?"
        analysis = processor.analyze_query(query)
        
        assert analysis is not None
        assert 'epic1_analysis' not in analysis.metadata
        assert processor._analyzer.__class__.__name__ == 'RuleBasedAnalyzer'
    
    def test_epic1_with_component_factory(self):
        """Test Epic 1 works when created via ComponentFactory."""
        # Create processor via ComponentFactory
        processor = ComponentFactory.create_query_processor(
            'modular',
            analyzer_type='epic1',
            analyzer_config=self.epic1_config['analyzer']['config']
        )
        
        # Verify Epic 1 analyzer is used
        assert hasattr(processor, '_analyzer')
        assert processor._analyzer.__class__.__name__ == 'Epic1QueryAnalyzer'
        
        # Test functionality
        query = "Complex query about transformer optimization"
        analysis = processor.analyze_query(query)
        
        assert 'epic1_analysis' in analysis.metadata
        epic1_data = analysis.metadata['epic1_analysis']
        assert 'complexity_level' in epic1_data
        assert 'recommended_model' in epic1_data
    
    def test_epic1_error_handling(self):
        """Test Epic 1 handles errors gracefully."""
        # Create processor with Epic 1
        config = QueryProcessorConfig(
            analyzer_type='epic1',
            analyzer_config=self.epic1_config['analyzer']['config'],
            selector_type='token_limit',
            selector_config={'max_tokens': 2048},
            assembler_type='standard',
            assembler_config={}
        )
        
        processor = ModularQueryProcessor(config)
        
        # Test with edge cases
        edge_cases = [
            "",  # Empty query
            " " * 100,  # Whitespace only
            "a" * 5000,  # Very long query
            "???",  # Special characters
        ]
        
        for query in edge_cases:
            # Should not crash
            analysis = processor.analyze_query(query)
            assert analysis is not None
            
            # Epic 1 should provide some result
            if 'epic1_analysis' in analysis.metadata:
                epic1_data = analysis.metadata['epic1_analysis']
                assert 'complexity_level' in epic1_data
    
    def test_epic1_metrics_tracking(self):
        """Test Epic 1 performance metrics are tracked."""
        config = QueryProcessorConfig(
            analyzer_type='epic1',
            analyzer_config=self.epic1_config['analyzer']['config'],
            selector_type='token_limit',
            selector_config={'max_tokens': 2048},
            assembler_type='standard',
            assembler_config={}
        )
        
        processor = ModularQueryProcessor(config)
        
        # Process multiple queries
        queries = [
            "What is RAG?",
            "How does it work?",
            "Complex technical question here"
        ]
        
        for query in queries:
            processor.analyze_query(query)
        
        # Get metrics
        metrics = processor.get_metrics()
        
        # Check metrics are tracked
        assert 'total_queries' in metrics
        assert metrics['total_queries'] == 3
        assert 'avg_analysis_time' in metrics
        
        # Check Epic 1 specific metrics if available
        if hasattr(processor._analyzer, 'get_performance_metrics'):
            epic1_metrics = processor._analyzer.get_performance_metrics()
            assert 'epic1_performance' in epic1_metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])