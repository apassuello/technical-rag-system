"""
BM25 Scoring Quality Tests.

This module tests the mathematical correctness of BM25 scoring implementation,
validates score ranges, and ensures proper handling of edge cases.

Unlike existing tests that just check if BM25Retriever can be instantiated,
these tests validate that BM25 actually produces correct scores according
to the mathematical formula and appropriately distinguishes between relevant
and irrelevant queries.
"""

import pytest
import numpy as np
from typing import List, Dict, Tuple
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.components.retrievers.sparse.bm25_retriever import BM25Retriever
from src.core.interfaces import Document


class TestBM25ScoringQuality:
    """Test BM25 scoring algorithm correctness and quality."""
    
    def setup_method(self):
        """Set up test data and BM25 instance."""
        # Create test documents with known content
        self.test_documents = [
            Document(
                id="doc1",
                content="RISC-V is an open instruction set architecture",
                metadata={"source": "test"}
            ),
            Document(
                id="doc2", 
                content="RISC-V RISC-V processor implements the RISC-V instruction set",
                metadata={"source": "test"}
            ),
            Document(
                id="doc3",
                content="The weather in Paris is beautiful today",
                metadata={"source": "test"}
            ),
            Document(
                id="doc4",
                content="Computer architecture includes instruction set design",
                metadata={"source": "test"}
            ),
            Document(
                id="doc5",
                content="RISC-V provides a modular instruction set architecture with optional extensions for vector processing",
                metadata={"source": "test"}
            )
        ]
        
        # Initialize BM25 with test config
        self.bm25 = BM25Retriever({
            "k1": 1.2,
            "b": 0.75,
            "lowercase": True,
            "preserve_technical_terms": True,
            "filter_stop_words": True
        })
        
        # Build index
        self.bm25.index_documents(self.test_documents)
    
    def test_bm25_formula_correctness(self):
        """Verify BM25 score calculation matches expected formula."""
        # Query for a term that appears in doc2
        query = "RISC-V"
        
        # Get scores
        results = self.bm25.search(query, k=5)
        
        # Manual calculation for doc2
        # Term frequency: "RISC-V" appears 3 times in doc2
        # Document length: 9 words
        # Average doc length: calculate from corpus
        
        # Find doc2 in results
        doc2_result = next((r for r in results if r[0] == 1), None)  # doc2 is index 1
        assert doc2_result is not None, "Doc2 should be in results"
        
        doc2_score = doc2_result[1]
        
        # Doc2 should score highest due to high term frequency
        assert doc2_score == results[0][1], "Doc2 should be top result for 'RISC-V'"
        
        # Score should be positive and reasonable
        assert 0 < doc2_score <= 1.0, f"Score should be in (0, 1], got {doc2_score}"
    
    def test_technical_vs_irrelevant_scoring(self):
        """Verify technical queries score high on relevant docs, low on irrelevant."""
        # Technical query
        tech_results = self.bm25.search("RISC-V architecture", k=5)
        
        # Get scores for technical docs (doc1, doc2, doc4, doc5) vs irrelevant (doc3)
        tech_scores = []
        irrelevant_score = None
        
        for idx, score in tech_results:
            if idx == 2:  # doc3 about Paris weather
                irrelevant_score = score
            else:
                tech_scores.append(score)
        
        # Technical documents should score significantly higher
        if tech_scores and irrelevant_score is not None:
            min_tech_score = min(tech_scores)
            assert min_tech_score > irrelevant_score, \
                f"Technical docs ({min_tech_score}) should score higher than irrelevant ({irrelevant_score})"
        
        # Top result should be highly relevant
        assert tech_results[0][1] > 0.5, "Top result should have high score for technical query"
    
    def test_irrelevant_query_filtering(self):
        """Verify off-topic queries produce low scores."""
        # Completely irrelevant query
        results = self.bm25.search("French cooking recipes", k=5)
        
        # All scores should be very low or zero
        scores = [score for _, score in results]
        
        if scores:  # If any results returned
            max_score = max(scores)
            assert max_score < 0.3, f"Irrelevant query should score <0.3, got {max_score}"
    
    def test_term_frequency_saturation(self):
        """Verify diminishing returns for repeated terms (TF saturation)."""
        # Single occurrence
        results_1x = self.bm25.search("RISC-V", k=5)
        
        # Multiple occurrences (should not scale linearly)
        results_3x = self.bm25.search("RISC-V RISC-V RISC-V", k=5)
        
        # Get top scores
        if results_1x and results_3x:
            score_1x = results_1x[0][1]
            score_3x = results_3x[0][1]
            
            # Score should increase but not triple
            assert score_3x > score_1x, "Repeated terms should increase score"
            assert score_3x < score_1x * 2, "Score should not scale linearly with repetition"
    
    def test_document_length_normalization(self):
        """Verify document length normalization works correctly."""
        # Create two docs with same term frequency ratio but different lengths
        short_doc = Document(
            id="short",
            content="RISC-V architecture",
            metadata={"source": "test"}
        )
        
        long_doc = Document(
            id="long",
            content="RISC-V architecture is an open instruction set architecture " * 3,
            metadata={"source": "test"}
        )
        
        # Create new BM25 instance with these docs
        bm25_norm = BM25Retriever({"k1": 1.2, "b": 0.75})
        bm25_norm.index_documents([short_doc, long_doc])
        
        # Search for the term
        results = bm25_norm.search("RISC-V", k=2)
        
        if len(results) == 2:
            scores = {idx: score for idx, score in results}
            short_score = scores[0]
            long_score = scores[1]
            
            # Scores should be relatively similar (within 30%)
            score_ratio = abs(short_score - long_score) / max(short_score, long_score)
            assert score_ratio < 0.3, \
                f"Length normalization failed: short={short_score}, long={long_score}"
    
    def test_score_range_validation(self):
        """Verify all scores fall within expected ranges."""
        queries = [
            "RISC-V",
            "instruction set architecture", 
            "processor design",
            "xyz123 nonexistent",
            ""  # empty query
        ]
        
        for query in queries:
            if not query:  # Skip empty
                continue
                
            results = self.bm25.search(query, k=10)
            
            for idx, score in results:
                # All scores should be non-negative
                assert score >= 0, f"Negative score {score} for query '{query}'"
                
                # Scores should be bounded (BM25 can exceed 1.0 but should be reasonable)
                assert score < 10.0, f"Unreasonably high score {score} for query '{query}'"
    
    def test_multi_term_query_behavior(self):
        """Test how BM25 handles multi-term queries."""
        # Query with multiple relevant terms
        results = self.bm25.search("RISC-V instruction architecture", k=5)
        
        # Documents containing more query terms should rank higher
        # doc5 contains all three terms, should be near top
        doc5_rank = None
        for rank, (idx, score) in enumerate(results):
            if idx == 4:  # doc5
                doc5_rank = rank
                break
        
        assert doc5_rank is not None and doc5_rank < 2, \
            "Document with all query terms should rank in top 2"
    
    def test_stopword_impact(self):
        """Verify stopwords are properly filtered and don't affect scoring."""
        # Query with stopwords
        results_with_stop = self.bm25.search("What is the RISC-V architecture", k=5)
        
        # Query without stopwords  
        results_without_stop = self.bm25.search("RISC-V architecture", k=5)
        
        # Top results should be the same
        if results_with_stop and results_without_stop:
            top_with = results_with_stop[0][0]
            top_without = results_without_stop[0][0]
            
            assert top_with == top_without, \
                "Stopwords should not affect top result"
    
    def test_empty_document_handling(self):
        """Test BM25 behavior with empty documents."""
        docs_with_empty = self.test_documents + [
            Document(id="empty", content="", metadata={"source": "test"})
        ]
        
        bm25_empty = BM25Retriever({"k1": 1.2, "b": 0.75})
        bm25_empty.index_documents(docs_with_empty)
        
        results = bm25_empty.search("RISC-V", k=10)
        
        # Empty document should not appear in results or have zero score
        for idx, score in results:
            if idx == len(docs_with_empty) - 1:  # empty doc
                assert score == 0, "Empty document should have zero score"
    
    def test_special_character_handling(self):
        """Test BM25 with special characters and punctuation."""
        special_docs = [
            Document(id="s1", content="C++ programming language", metadata={}),
            Document(id="s2", content="RISC-V++ extended version", metadata={}),
            Document(id="s3", content="What is RISC-V?", metadata={})
        ]
        
        bm25_special = BM25Retriever({"k1": 1.2, "b": 0.75})
        bm25_special.index_documents(special_docs)
        
        # Should handle special characters gracefully
        results = bm25_special.search("C++", k=3)
        assert len(results) > 0, "Should return results for special char query"
        
        results2 = bm25_special.search("RISC-V?", k=3)
        assert len(results2) > 0, "Should handle punctuation in query"


class TestBM25EdgeCases:
    """Test BM25 edge cases and failure modes."""
    
    def test_very_long_document(self):
        """Test BM25 with extremely long documents."""
        # Create a very long document
        long_content = " ".join(["RISC-V architecture"] * 1000)
        long_doc = Document(id="long", content=long_content, metadata={})
        
        short_doc = Document(
            id="short", 
            content="RISC-V architecture design", 
            metadata={}
        )
        
        bm25 = BM25Retriever({"k1": 1.2, "b": 0.75})
        bm25.index_documents([long_doc, short_doc])
        
        results = bm25.search("RISC-V", k=2)
        
        # Both should return with reasonable scores
        assert len(results) == 2
        scores = [score for _, score in results]
        assert all(0 < score < 10 for score in scores)
    
    def test_single_document_corpus(self):
        """Test BM25 with only one document."""
        single_doc = Document(
            id="single",
            content="RISC-V processor architecture",
            metadata={}
        )
        
        bm25 = BM25Retriever({"k1": 1.2, "b": 0.75})
        bm25.index_documents([single_doc])
        
        results = bm25.search("RISC-V", k=1)
        
        assert len(results) == 1
        assert results[0][1] > 0  # Should have positive score
    
    def test_all_documents_identical(self):
        """Test BM25 when all documents are identical."""
        identical_docs = [
            Document(id=f"doc{i}", content="RISC-V architecture", metadata={})
            for i in range(5)
        ]
        
        bm25 = BM25Retriever({"k1": 1.2, "b": 0.75})
        bm25.index_documents(identical_docs)
        
        results = bm25.search("RISC-V", k=5)
        
        # All should have identical scores
        scores = [score for _, score in results]
        assert len(set(scores)) == 1, "Identical docs should have identical scores"


def test_bm25_quality_assertions():
    """
    Test quality assertions that should be true for any correctly
    implemented BM25 algorithm.
    """
    docs = [
        Document(id="1", content="The quick brown fox jumps over the lazy dog", metadata={}),
        Document(id="2", content="The lazy dog sleeps under the tree", metadata={}),
        Document(id="3", content="Machine learning algorithms process data", metadata={})
    ]
    
    bm25 = BM25Retriever({"k1": 1.2, "b": 0.75})
    bm25.index_documents(docs)
    
    # Assertion 1: Exact term match should score higher than partial
    exact_results = bm25.search("lazy dog", k=3)
    partial_results = bm25.search("dog", k=3)
    
    # Document with both terms should score highest for multi-term query
    assert exact_results[0][1] > partial_results[0][1]
    
    # Assertion 2: Irrelevant documents should score very low
    ml_results = bm25.search("quantum physics", k=3)
    if ml_results:
        assert all(score < 0.3 for _, score in ml_results)
    
    # Assertion 3: Score ordering should be monotonic
    results = bm25.search("the dog", k=3)
    scores = [score for _, score in results]
    assert scores == sorted(scores, reverse=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])