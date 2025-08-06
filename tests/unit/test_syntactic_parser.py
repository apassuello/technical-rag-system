#!/usr/bin/env python3
"""
Unit tests for SyntacticParser utility.

This module tests the syntactic analysis functionality of SyntacticParser,
which is a generic utility that can be used by any system requiring
lightweight syntax analysis without heavy NLP dependencies.
"""

import pytest
import sys
import time
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.components.query_processors.analyzers.utils import SyntacticParser


class TestSyntacticParser:
    """Test SyntacticParser utility."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = SyntacticParser()
    
    def test_clause_detection(self):
        """Test clause counting."""
        assert self.parser.count_clauses("Simple sentence") == 1
        assert self.parser.count_clauses("First clause, and second clause") == 2
        assert self.parser.count_clauses("If this, then that, otherwise something else") == 3
    
    def test_nesting_depth(self):
        """Test nesting depth calculation."""
        assert self.parser.calculate_nesting_depth("Simple") == 0
        assert self.parser.calculate_nesting_depth("(nested)") == 1
        assert self.parser.calculate_nesting_depth("(outer (inner))") == 2
        assert self.parser.calculate_nesting_depth("[a [b [c]]]") == 3
    
    def test_conjunction_detection(self):
        """Test conjunction counting."""
        assert self.parser.count_conjunctions("Simple") == 0
        assert self.parser.count_conjunctions("This and that") == 1
        assert self.parser.count_conjunctions("A and B or C but D") == 3
    
    def test_question_classification(self):
        """Test question type detection."""
        assert self.parser.classify_question("What is RAG?") == 'what'
        assert self.parser.classify_question("How does it work?") == 'how'
        assert self.parser.classify_question("Why use embeddings?") == 'why'
        assert self.parser.classify_question("When should we apply?") == 'when'
        assert self.parser.classify_question("Is it efficient?") == 'yes_no'
        assert self.parser.classify_question("Compare A and B") == 'compare'
        assert self.parser.classify_question("Implement a solution") == 'action'
        assert self.parser.classify_question("Random text") == 'unknown'
    
    def test_punctuation_complexity(self):
        """Test punctuation complexity scoring."""
        assert self.parser.calculate_punctuation_complexity("Simple") == 0.0
        assert self.parser.calculate_punctuation_complexity("A, B, C") > 0
        assert self.parser.calculate_punctuation_complexity("Complex: (a) first; (b) second.") > 0.5
    
    def test_parse_metrics(self):
        """Test comprehensive parsing."""
        text = "How does the transformer model, which uses attention mechanisms, work?"
        metrics = self.parser.parse(text)
        
        assert 'clause_count' in metrics
        assert 'nesting_depth' in metrics
        assert 'conjunction_count' in metrics
        assert 'question_type' in metrics
        assert 'punctuation_complexity' in metrics
        assert metrics['question_type'] == 'how'
    
    def test_performance(self):
        """Test performance meets requirements."""
        text = "Complex query with (nested structures) and multiple, diverse clauses?"
        
        start = time.time()
        self.parser.parse(text)
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 10  # Should be under 10ms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])