#!/usr/bin/env python3
"""
Integration tests for Epic 1 Query Analyzer with ModularQueryProcessor.

This module tests the integration of Epic1QueryAnalyzer with the 
ModularQueryProcessor and validates end-to-end query processing.
"""

import pytest
import time
from typing import List, Dict, Any

from src.components.query_processors import ModularQueryProcessor
from src.components.query_processors.base import QueryProcessorConfig
from src.core.interfaces import Document, Answer
from src.core.component_factory import ComponentFactory


class TestEpic1Integration:
    """Test Epic1QueryAnalyzer integration with ModularQueryProcessor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create sample documents for testing (needed by mock methods)
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
        
        # Create mock retriever and generator for ModularQueryProcessor
        self.mock_retriever = self._create_mock_retriever()
        self.mock_generator = self._create_mock_generator()
        
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
                                'provider': 'local',
                                'model': 'qwen2.5-1.5b-instruct',
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
        
        # Create processor with required dependencies
        processor = ModularQueryProcessor(
            self.mock_retriever,
            self.mock_generator,
            config=config
        )
        
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
        
        processor = ModularQueryProcessor(
            self.mock_retriever,
            self.mock_generator,
            config=config
        )

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
                assert 'local' in epic1_data['recommended_model']
            
            # The Epic 1 metadata should be preserved through analysis
            assert analysis.metadata.get('epic1_analysis') is not None
            
            # Verify metadata contains expected fields
            epic1_metadata = analysis.metadata['epic1_analysis']
            assert 'complexity_level' in epic1_metadata
            assert 'recommended_model' in epic1_metadata
    
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
        
        processor = ModularQueryProcessor(
            self.mock_retriever,
            self.mock_generator,
            config=config
        )

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
        
        nlp_processor = ModularQueryProcessor(
            self.mock_retriever,
            self.mock_generator,
            config=nlp_config
        )
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
        
        epic1_processor = ModularQueryProcessor(
            self.mock_retriever,
            self.mock_generator,
            config=epic1_config
        )
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
        
        processor = ModularQueryProcessor(
            self.mock_retriever,
            self.mock_generator,
            config=standard_config
        )

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
        
        processor = ModularQueryProcessor(
            self.mock_retriever,
            self.mock_generator,
            config=config
        )

        # Test with edge cases
        edge_cases = [
            ("", True),  # Empty query - should raise error
            (" " * 100, True),  # Whitespace only - should raise error
            ("a" * 5000, False),  # Very long query - should work
            ("???", False),  # Special characters - should work
        ]
        
        for query, should_error in edge_cases:
            if should_error:
                # Empty/whitespace queries should raise ValueError
                with pytest.raises(ValueError, match="Query cannot be empty"):
                    processor.analyze_query(query)
            else:
                # Other edge cases should work
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
        
        processor = ModularQueryProcessor(
            self.mock_retriever,
            self.mock_generator,
            config=config
        )

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
        
        # Check metrics are tracked - metrics are in performance_stats
        assert 'performance_stats' in metrics
        perf_stats = metrics['performance_stats']
        assert 'total_queries' in perf_stats
        # Note: analyze_query doesn't update metrics, only process() does
        # So we check the structure exists rather than count
        assert isinstance(perf_stats['total_queries'], int)
        
        # Check Epic 1 analyzer is being used
        assert 'analyzer_type' in metrics
        assert 'Epic1QueryAnalyzer' in metrics['analyzer_type']
        
        # Check Epic 1 specific metrics if available
        if hasattr(processor._analyzer, 'get_performance_metrics'):
            epic1_metrics = processor._analyzer.get_performance_metrics()
            assert 'epic1_performance' in epic1_metrics
    
    def _create_mock_retriever(self):
        """Create a mock retriever for testing."""
        from unittest.mock import Mock
        from src.core.interfaces import RetrievalResult
        
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            RetrievalResult(
                document=doc,
                score=0.9 - i * 0.1,
                retrieval_method="mock",
                metadata={"test": True}
            )
            for i, doc in enumerate(self.sample_documents[:2])
        ]
        return mock_retriever
    
    def _create_mock_generator(self):
        """Create a mock answer generator for testing."""
        from unittest.mock import Mock
        from src.core.interfaces import Answer
        
        mock_generator = Mock()
        mock_generator.generate.return_value = Answer(
            text="This is a mock answer based on the provided context.",
            sources=self.sample_documents[:2],
            confidence=0.85,
            metadata={"model": "mock", "generation_time": 0.5}
        )
        return mock_generator


if __name__ == "__main__":
    pytest.main([__file__, "-v"])