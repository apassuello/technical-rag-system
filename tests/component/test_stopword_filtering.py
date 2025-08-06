"""
Unit tests for BM25 stopword filtering functionality.

This module tests the enhanced stopword filtering capabilities
including multiple stopword sets, technical term preservation,
and debug logging functionality.
"""

import unittest
from src.components.retrievers.sparse.bm25_retriever import BM25Retriever
from src.core.interfaces import Document


class TestStopwordFiltering(unittest.TestCase):
    """Test cases for BM25 stopword filtering functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.basic_config = {
            'k1': 1.2, 'b': 0.75, 'lowercase': True,
            'filter_stop_words': True,
            'stop_word_sets': ['english_common'],
            'debug_stop_words': False
        }
        
        self.standard_config = {
            'k1': 1.2, 'b': 0.75, 'lowercase': True,
            'filter_stop_words': True,
            'stop_word_sets': ['english_common'],  # Only standard linguistic stopwords
            'debug_stop_words': False
        }
        
        # Realistic test corpus based on actual technical documentation
        self.test_documents = [
            Document(content='RISC-V is an open standard instruction set architecture (ISA) based on established reduced instruction set computer (RISC) principles. The RISC-V ISA is defined as a base integer ISA, which must be present in any implementation.', 
                     metadata={'source': 'riscv-base-instructions.pdf', 'page': 1, 'chunk_id': 0}),
            Document(content='Vector operations in RISC-V provide high-performance computation for applications requiring data parallelism. The vector extension defines vector registers, vector instructions, and vector memory operations.',
                     metadata={'source': 'RISC-V-VectorExtension-1-1.pdf', 'page': 15, 'chunk_id': 1}),
            Document(content='AI/ML-enabled Software as Medical Device (SaMD) presents unique challenges for regulatory oversight. The FDA guidance emphasizes the importance of software validation and risk management.',
                     metadata={'source': 'AIML-SaMD-Action-Plan.pdf', 'page': 3, 'chunk_id': 2}),
            Document(content='Software validation is the process of confirming that software specifications conform to user needs and intended uses. This process includes verification activities and design controls.',
                     metadata={'source': 'General-Principles-of-Software-Validation.pdf', 'page': 8, 'chunk_id': 3}),
            Document(content='Good Machine Learning Practice (GMLP) for medical device development encompasses the entire ML lifecycle, from data collection to model deployment and monitoring.',
                     metadata={'source': 'GMLP_Guiding_Principles.pdf', 'page': 12, 'chunk_id': 4}),
            Document(content='Digital signal processing applications benefit from RISC-V vector extensions. The vector instruction set enables efficient implementation of filtering, FFT, and matrix operations.',
                     metadata={'source': 'Communications_Signal_Processing_Using_RISC-V_Vector_Extension.pdf', 'page': 25, 'chunk_id': 5})
        ]
    
    def test_stopword_set_initialization(self):
        """Test that stopword sets are properly initialized."""
        retriever = BM25Retriever(self.standard_config)
        
        # Check that only standard linguistic stopwords are loaded
        self.assertEqual(retriever.stop_word_sets, ['english_common'])
        
        # Verify standard linguistic stopwords are present
        self.assertIn('the', retriever.stop_words)    # english_common
        self.assertIn('is', retriever.stop_words)     # english_common
        self.assertIn('and', retriever.stop_words)    # english_common
        
        # Verify discriminative terms are NOT in stopwords (this was the bug)
        self.assertNotIn('napoleon', retriever.stop_words)  # Should be preserved
        self.assertNotIn('paris', retriever.stop_words)     # Should be preserved
        self.assertNotIn('where', retriever.stop_words)     # Should be preserved
        
        # Check total count is reasonable for standard set only
        self.assertGreater(len(retriever.stop_words), 50)
        self.assertLess(len(retriever.stop_words), 120)  # Much smaller than before
        
    def test_irrelevant_query_filtering(self):
        """Test that queries with no relevant content return low scores."""
        retriever = BM25Retriever(self.standard_config)
        retriever.index_documents(self.test_documents)
        
        # Test cases from specification
        irrelevant_queries = [
            "Where is Paris?",
            "Who is Napoleon?",
            "What is the capital of France?"
        ]
        
        for query in irrelevant_queries:
            with self.subTest(query=query):
                results = retriever.search(query, k=5)
                # Should return no results or very low scores
                if results:
                    max_score = max(score for _, score in results)
                    self.assertLess(max_score, 0.3, f"Query '{query}' returned high score {max_score}")
                else:
                    # No results is ideal
                    self.assertEqual(len(results), 0)
    
    def test_technical_query_preservation(self):
        """Test that technical queries work correctly with realistic RISC-V corpus."""
        # Use realistic RISC-V corpus instead of mixed corpus
        riscv_corpus = [
            Document(content='RISC-V base integer instruction set RV32I defines 32-bit integer operations including ADD, SUB, AND, OR instructions.',
                     metadata={'source': 'riscv-spec-base.pdf', 'section': 'Base Instructions'}),
            Document(content='RISC-V vector extension provides vector registers and vector instructions for data parallelism.',
                     metadata={'source': 'riscv-vector-spec.pdf', 'section': 'Vector Architecture'}),
            Document(content='RISC-V privileged architecture defines supervisor mode and machine mode privilege levels.',
                     metadata={'source': 'riscv-privileged.pdf', 'section': 'Privilege Levels'})
        ]
        
        retriever = BM25Retriever(self.standard_config)
        retriever.index_documents(riscv_corpus)
        
        # Test domain-appropriate queries
        technical_queries = [
            ("vector instruction set", "Should match vector extension document"),
            ("base integer operations", "Should match base instruction document"),
            ("privilege levels", "Should match privileged architecture document")
        ]
        
        for query, expected_behavior in technical_queries:
            with self.subTest(query=query):
                results = retriever.search(query, k=3)
                # Should return relevant technical documents for domain queries
                self.assertGreater(len(results), 0, f"Technical query '{query}' returned no results - {expected_behavior}")
                
                # Check that results have reasonable scores (>0.1 indicates meaningful match)
                top_score = results[0][1] if results else 0
                self.assertGreater(top_score, 0.1, f"Top result for '{query}' scored too low: {top_score}")
        
        # Test out-of-domain query returns empty results
        irrelevant_results = retriever.search("napoleon bonaparte france", k=5)
        self.assertEqual(len(irrelevant_results), 0, "Out-of-domain query should return no results")
    
    def test_standard_stopword_filtering(self):
        """Test that standard linguistic stopwords are filtered correctly."""
        retriever = BM25Retriever(self.standard_config)
        
        test_cases = [
            ("The instruction set architecture is important", ["instruction", "set", "architecture", "important"]),
            ("A RISC-V processor has several registers", ["risc-v", "processor", "several", "registers"]),
            ("This is an example of the system", ["example", "system"])
        ]
        
        for query, expected_tokens in test_cases:
            with self.subTest(query=query):
                tokens = retriever.get_query_tokens(query)
                # Check that expected content words are preserved
                for expected in expected_tokens:
                    self.assertIn(expected, tokens, f"Content word '{expected}' was incorrectly filtered from '{query}'")
                
                # Check that common stopwords are removed
                stopwords_to_check = ['the', 'is', 'an', 'of', 'a', 'has']
                for stopword in stopwords_to_check:
                    if stopword in query.lower():
                        self.assertNotIn(stopword, tokens, f"Stopword '{stopword}' was not filtered from '{query}'")
    
    def test_minimum_word_length_filtering(self):
        """Test that short words are filtered based on min_word_length."""
        config = self.basic_config.copy()
        config['min_word_length'] = 3
        config['filter_stop_words'] = False  # Disable stopwords to test length only
        
        retriever = BM25Retriever(config)
        
        query = "A big CPU with I/O"
        tokens = retriever.get_query_tokens(query)
        
        # Should filter out words shorter than 3 characters
        for token in tokens:
            self.assertGreaterEqual(len(token), 3, f"Token '{token}' shorter than min_word_length")
    
    def test_stopword_filtering_disabled(self):
        """Test behavior when stopword filtering is disabled."""
        config = self.basic_config.copy()
        config['filter_stop_words'] = False
        
        retriever = BM25Retriever(config)
        
        query = "The RISC-V is an architecture"
        tokens = retriever.get_query_tokens(query)
        
        # Should preserve common words when filtering is disabled
        self.assertIn('the', tokens)
        self.assertIn('is', tokens)
        self.assertIn('an', tokens)
    
    def test_custom_stopwords(self):
        """Test that custom stopwords are properly applied."""
        config = self.basic_config.copy()
        config['custom_stop_words'] = ['custom', 'domain', 'specific']
        
        retriever = BM25Retriever(config)
        
        query = "This is a custom domain specific test"
        tokens = retriever.get_query_tokens(query)
        
        # Custom stopwords should be filtered
        self.assertNotIn('custom', tokens)
        self.assertNotIn('domain', tokens)
        self.assertNotIn('specific', tokens)
        
        # Regular content should be preserved
        self.assertIn('test', tokens)
    
    def test_performance_impact(self):
        """Test that stopword filtering has minimal performance impact."""
        import time
        
        # Test without stopword filtering
        config_no_filter = self.basic_config.copy()
        config_no_filter['filter_stop_words'] = False
        
        retriever_no_filter = BM25Retriever(config_no_filter)
        start_time = time.time()
        retriever_no_filter.index_documents(self.test_documents)
        time_no_filter = time.time() - start_time
        
        # Test with comprehensive stopword filtering
        retriever_with_filter = BM25Retriever(self.standard_config)
        start_time = time.time()
        retriever_with_filter.index_documents(self.test_documents)
        time_with_filter = time.time() - start_time
        
        # Performance impact should be less than 100ms absolute for practical use
        absolute_impact = time_with_filter - time_no_filter
        self.assertLess(absolute_impact, 0.1, f"Absolute performance impact too high: {absolute_impact*1000:.1f}ms")
        
        # Also check percentage impact isn't extreme (>200%)
        if time_no_filter > 0:
            performance_impact = (time_with_filter - time_no_filter) / time_no_filter * 100
            self.assertLess(performance_impact, 200.0, f"Percentage impact excessive: {performance_impact:.1f}%")
    
    def test_stats_reporting(self):
        """Test that statistics correctly report stopword configuration."""
        retriever = BM25Retriever(self.standard_config)
        stats = retriever.get_stats()
        
        # Check that standard configuration parameters are reported
        self.assertEqual(stats['stop_word_sets'], ['english_common'])
        self.assertEqual(stats['min_word_length'], 2)
        self.assertFalse(stats['debug_stop_words'])
        self.assertGreater(stats['stop_words_count'], 50)
        self.assertLess(stats['stop_words_count'], 120)  # Only standard stopwords
    
    def test_golden_test_cases(self):
        """Test specific cases from the golden test set specification."""
        retriever = BM25Retriever(self.standard_config)
        retriever.index_documents(self.test_documents)
        
        # Test cases for BM25 lexical matching behavior
        test_cases = [
            {
                'query': 'cleopatra ancient egypt',
                'expected_behavior': {'should_answer': False, 'reason': 'No matching terms in corpus'}
            },
            {
                'query': 'Napoleon\'s favorite RISC-V instruction', 
                'expected_behavior': {'should_answer': True, 'reason': 'Matches RISC-V and instruction terms', 'min_coverage': 0.4}
            },
            {
                'query': 'RISC-V vector operations',
                'expected_behavior': {'should_answer': True, 'reason': 'Strong match for RISC-V content', 'min_coverage': 0.8}
            },
            {
                'query': 'FDA medical device validation',
                'expected_behavior': {'should_answer': True, 'reason': 'Strong match for medical device content', 'min_coverage': 0.6}
            }
        ]
        
        for test_case in test_cases:
            query = test_case['query']
            expected = test_case['expected_behavior']
            
            with self.subTest(query=query):
                results = retriever.search(query, k=5)
                
                tokens = retriever.get_query_tokens(query)
                
                if not expected.get('should_answer', True):
                    # Should return no results (no matching terms)
                    self.assertEqual(len(results), 0, 
                                   f"Query '{query}' should return no results (no matching terms): {expected['reason']}")
                else:
                    # Should return results based on lexical matching
                    self.assertGreater(len(results), 0, 
                                     f"Query '{query}' should return results: {expected['reason']}")
                    
                    if results:
                        # Check that results have reasonable term coverage
                        best_result_idx = results[0][0]
                        best_doc = self.test_documents[best_result_idx]
                        doc_tokens = set(retriever.get_query_tokens(best_doc.content.lower()))
                        query_tokens = set(tokens)
                        matches = query_tokens & doc_tokens
                        coverage = len(matches) / len(query_tokens) if query_tokens else 0
                        
                        min_coverage = expected.get('min_coverage', 0.3)
                        self.assertGreaterEqual(coverage, min_coverage,
                                              f"Best result for '{query}' has low term coverage: {coverage:.1%} < {min_coverage:.1%}")


if __name__ == '__main__':
    unittest.main()