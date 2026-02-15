#!/usr/bin/env python3
"""
Unit tests for TechnicalTermManager utility.

This module tests the technical term detection and analysis functionality
of TechnicalTermManager, which is a generic utility that can be used
by any system requiring technical vocabulary detection.
"""

import pytest
import time

from src.components.query_processors.analyzers.utils import TechnicalTermManager


class TestTechnicalTermManager:
    """Test TechnicalTermManager utility."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'domains': ['ml', 'rag', 'llm'],
            'min_term_length': 3,
            'case_sensitive': False
        }
        self.manager = TechnicalTermManager(self.config)
    
    def test_initialization(self):
        """Test proper initialization."""
        assert self.manager is not None
        assert len(self.manager.terms) > 0
        assert 'ml' in self.manager.domain_terms
        assert 'rag' in self.manager.domain_terms
        assert 'llm' in self.manager.domain_terms
    
    def test_contains_term(self):
        """Test term detection."""
        # Should detect known ML terms
        assert self.manager.contains_term('transformer')
        assert self.manager.contains_term('embedding')
        assert self.manager.contains_term('neural')
        
        # Should not detect non-technical terms
        assert not self.manager.contains_term('hello')
        assert not self.manager.contains_term('the')
        assert not self.manager.contains_term('is')
        
        # Test minimum length
        assert not self.manager.contains_term('ai')  # Too short
    
    def test_extract_terms(self):
        """Test term extraction from text."""
        text = "The transformer architecture uses attention mechanisms for embeddings"
        terms = self.manager.extract_terms(text)
        
        assert 'transformer' in terms
        assert 'attention' in terms
        assert 'embeddings' in terms or 'embedding' in terms
    
    def test_pattern_detection(self):
        """Test pattern-based technical term detection."""
        text = "We use GPT-4 and BERT-base models with F1-score metrics"
        terms = self.manager.extract_terms(text)
        
        # Should detect model names and metrics
        assert any('GPT' in term for term in terms)
        assert any('BERT' in term for term in terms)
        assert any('F1' in term for term in terms)
    
    def test_calculate_density(self):
        """Test density calculation."""
        text = "How does transformer attention work with embeddings?"
        density = self.manager.calculate_density(text)
        
        assert isinstance(density, float)
        assert 0.0 <= density <= 1.0
        
        # Test with purely technical text
        technical_text = "transformer attention mechanism with embeddings and neural networks"
        tech_density = self.manager.calculate_density(technical_text)
        assert tech_density > 0.0
    
    def test_performance(self):
        """Test performance meets requirements."""
        text = "The transformer model uses multi-head attention for sequence-to-sequence tasks"
        
        start = time.time()
        self.manager.extract_terms(text)
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 5  # Should be under 5ms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])