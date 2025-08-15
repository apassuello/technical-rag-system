"""
Integration tests for the Modular Answer Generator.

This module tests the new modular AnswerGenerator implementation,
ensuring it works correctly with ComponentFactory and maintains
backward compatibility.
"""

import logging
import pytest
from typing import List

# Configure logging to see ComponentFactory logs
logging.basicConfig(level=logging.INFO, format='[%(name)s] %(levelname)s: %(message)s')

# Import required components
from src.core.component_factory import ComponentFactory
from src.core.interfaces import Document, Answer


class TestModularAnswerGenerator:
    """Test suite for modular answer generator."""
    
    @pytest.fixture
    def sample_documents(self) -> List[Document]:
        """Create sample documents for testing."""
        return [
            Document(
                content="RISC-V is an open-source instruction set architecture (ISA) based on established reduced instruction set computer (RISC) principles. Unlike proprietary ISAs, RISC-V is free to use for any purpose, allowing anyone to design, manufacture and sell RISC-V chips and software.",
                metadata={"source": "test_doc_1.pdf", "page": 1}
            ),
            Document(
                content="The RISC-V ISA was originally developed at the University of California, Berkeley. The project began in 2010 and the first version was released in 2011. RISC-V International, a non-profit corporation, now maintains the specifications.",
                metadata={"source": "test_doc_2.pdf", "page": 5}
            )
        ]
    
    def test_factory_creation(self):
        """Test that the modular generator can be created via ComponentFactory."""
        # Create generator using factory
        generator = ComponentFactory.create_generator("adaptive_modular")
        
        # Verify it was created successfully
        assert generator is not None
        assert hasattr(generator, 'generate')
        assert hasattr(generator, 'get_component_info')
        
        # Check component info
        info = generator.get_component_info()
        assert 'prompt_builder' in info
        assert 'llm_client' in info
        assert 'response_parser' in info
        assert 'confidence_scorer' in info
    
    def test_legacy_compatibility(self):
        """Test backward compatibility with legacy parameters."""
        # Create with legacy parameters
        generator = ComponentFactory.create_generator(
            "adaptive_modular",
            model_name="llama3.2",
            temperature=0.5,
            max_tokens=256
        )
        
        # Verify configuration was applied
        info = generator.get_generator_info()
        assert info['model_name'] == 'llama3.2'
        assert info['temperature'] == 0.5
        assert info['max_tokens'] == 256
    
    def test_component_visibility(self):
        """Test that ComponentFactory logs show sub-components."""
        # This test verifies the enhanced logging feature
        generator = ComponentFactory.create_generator("adaptive_modular")
        
        # Get component info - this is what ComponentFactory uses for logging
        info = generator.get_component_info()
        
        # Verify all sub-components are visible
        assert info['prompt_builder']['class'] == 'SimplePromptBuilder'
        assert info['llm_client']['class'] == 'OllamaAdapter'
        assert info['response_parser']['class'] == 'MarkdownParser'
        assert info['confidence_scorer']['class'] == 'SemanticScorer'
    
    def test_custom_configuration(self):
        """Test creating generator with custom configuration."""
        config = {
            "prompt_builder": {
                "type": "simple",
                "config": {
                    "max_context_length": 2000,
                    "citation_style": "footnote"
                }
            },
            "llm_client": {
                "type": "ollama",
                "config": {
                    "model_name": "mistral",
                    "temperature": 0.3
                }
            },
            "response_parser": {
                "type": "markdown",
                "config": {
                    "extract_citations": False
                }
            },
            "confidence_scorer": {
                "type": "semantic",
                "config": {
                    "relevance_weight": 0.5,
                    "grounding_weight": 0.3,
                    "quality_weight": 0.2
                }
            }
        }
        
        generator = ComponentFactory.create_generator("adaptive_modular", config=config)
        
        # Verify configuration was applied
        info = generator.get_generator_info()
        assert info['model_name'] == 'mistral'
        assert info['temperature'] == 0.3
    
    @pytest.mark.skipif(
        not _check_ollama_available(),
        reason="Ollama not available for testing"
    )
    def test_generation_with_ollama(self, sample_documents):
        """Test actual generation with Ollama (if available)."""
        generator = ComponentFactory.create_generator("adaptive_modular")
        
        # Generate answer
        query = "What is RISC-V?"
        answer = generator.generate(query, sample_documents)
        
        # Verify answer structure
        assert isinstance(answer, Answer)
        assert answer.text
        assert answer.sources == sample_documents
        assert 0.0 <= answer.confidence <= 1.0
        assert answer.metadata
        
        # Check metadata
        assert 'generator_type' in answer.metadata
        assert answer.metadata['generator_type'] == 'modular'
        assert 'components_used' in answer.metadata
        assert 'generation_time' in answer.metadata
    
    def test_error_handling(self):
        """Test error handling in the generator."""
        generator = ComponentFactory.create_generator("adaptive_modular")
        
        # Test with empty query
        with pytest.raises(ValueError, match="Query cannot be empty"):
            generator.generate("", [])
        
        # Test with invalid context
        with pytest.raises(Exception):  # Will be GenerationError
            generator.generate("test query", None)
    
    def test_performance_metrics(self):
        """Test that performance metrics are tracked."""
        # Clear metrics
        ComponentFactory.reset_performance_metrics()
        
        # Create generator
        generator = ComponentFactory.create_generator("adaptive_modular")
        
        # Check metrics
        metrics = ComponentFactory.get_performance_metrics()
        assert 'generator_adaptive_modular' in metrics
        assert metrics['generator_adaptive_modular']['creation_count'] == 1
        assert metrics['generator_adaptive_modular']['average_time'] > 0


def _check_ollama_available() -> bool:
    """Check if Ollama is available for testing."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])