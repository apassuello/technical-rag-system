"""
Unit tests for Query Processor component.

Tests the query execution workflow functionality introduced in Phase 1
of the architecture migration.
"""

import unittest
from unittest.mock import Mock, MagicMock
from typing import List

from src.core.query_processor import QueryProcessor
from src.core.interfaces import Document, Answer, RetrievalResult


class TestQueryProcessor(unittest.TestCase):
    """Test cases for QueryProcessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock retriever
        self.mock_retriever = Mock()
        
        # Create mock answer generator
        self.mock_generator = Mock()
        
        # Test configuration
        self.test_config = {
            "retrieval_k": 5,
            "min_confidence": 0.5
        }
        
        # Create query processor
        self.processor = QueryProcessor(
            retriever=self.mock_retriever,
            generator=self.mock_generator,
            config=self.test_config
        )
    
    def test_initialization(self):
        """Test query processor initialization."""
        # Verify components are stored
        self.assertEqual(self.processor.retriever, self.mock_retriever)
        self.assertEqual(self.processor.generator, self.mock_generator)
        
        # Verify configuration
        self.assertEqual(self.processor.default_k, 5)
        self.assertEqual(self.processor.min_confidence, 0.5)
    
    def test_process_query_success(self):
        """Test successful query processing."""
        # Set up mock returns
        test_docs = [
            Document(content="Content 1", metadata={"id": "1", "source": "doc1.pdf"}),
            Document(content="Content 2", metadata={"id": "2", "source": "doc2.pdf"})
        ]
        
        test_results = [
            RetrievalResult(document=test_docs[0], score=0.9, retrieval_method="hybrid"),
            RetrievalResult(document=test_docs[1], score=0.7, retrieval_method="hybrid")
        ]
        
        self.mock_retriever.retrieve.return_value = test_results
        
        test_answer = Answer(
            text="Generated answer",
            sources=test_docs,
            confidence=0.85,
            metadata={}
        )
        self.mock_generator.generate.return_value = test_answer
        
        # Process query
        result = self.processor.process("Test query", k=3)
        
        # Verify result
        self.assertEqual(result.text, "Generated answer")
        self.assertEqual(result.confidence, 0.85)
        self.assertEqual(len(result.sources), 2)
        
        # Verify metadata was added
        self.assertIn("query", result.metadata)
        self.assertIn("retrieved_docs", result.metadata)
        self.assertIn("retrieval_scores", result.metadata)
        self.assertEqual(result.metadata["query"], "Test query")
        self.assertEqual(result.metadata["retrieved_docs"], 2)
        
        # Verify method calls
        self.mock_retriever.retrieve.assert_called_once_with("Test query", 3)
        self.mock_generator.generate.assert_called_once_with("Test query", test_docs)
    
    def test_process_query_no_results(self):
        """Test query processing with no retrieval results."""
        # Set up empty retrieval
        self.mock_retriever.retrieve.return_value = []
        
        # Process query
        result = self.processor.process("Test query")
        
        # Verify empty answer
        self.assertEqual(result.text, "No relevant information found for your query.")
        self.assertEqual(result.confidence, 0.0)
        self.assertEqual(len(result.sources), 0)
        
        # Verify generator was not called
        self.mock_generator.generate.assert_not_called()
    
    def test_confidence_filtering(self):
        """Test confidence-based filtering of results."""
        # Set up results with mixed confidence
        test_docs = [
            Document(content="High conf", metadata={"id": "1", "source": "doc1.pdf"}),
            Document(content="Low conf", metadata={"id": "2", "source": "doc2.pdf"}),
            Document(content="Med conf", metadata={"id": "3", "source": "doc3.pdf"})
        ]
        
        test_results = [
            RetrievalResult(document=test_docs[0], score=0.9, retrieval_method="hybrid"),
            RetrievalResult(document=test_docs[1], score=0.3, retrieval_method="hybrid"),  # Below threshold
            RetrievalResult(document=test_docs[2], score=0.6, retrieval_method="hybrid")
        ]
        
        self.mock_retriever.retrieve.return_value = test_results
        
        # Mock generator to return the context it received
        def mock_generate(query, context):
            return Answer(
                text=f"Answer from {len(context)} docs",
                sources=context,
                confidence=0.8,
                metadata={}
            )
        
        self.mock_generator.generate.side_effect = mock_generate
        
        # Process query
        result = self.processor.process("Test query")
        
        # Verify only high-confidence docs were used
        self.assertEqual(len(result.sources), 2)
        self.assertIn("Answer from 2 docs", result.text)
    
    def test_empty_query_handling(self):
        """Test handling of empty queries."""
        with self.assertRaises(ValueError) as context:
            self.processor.process("")
        
        self.assertIn("Query cannot be empty", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            self.processor.process("   ")
        
        self.assertIn("Query cannot be empty", str(context.exception))
    
    def test_default_k_usage(self):
        """Test using default k value."""
        self.mock_retriever.retrieve.return_value = []
        
        # Process without specifying k
        self.processor.process("Test query")
        
        # Verify default k was used
        self.mock_retriever.retrieve.assert_called_with("Test query", 5)
    
    def test_explain_query(self):
        """Test query explanation functionality."""
        explanation = self.processor.explain_query("Test query")
        
        # Verify explanation structure
        self.assertIn("original_query", explanation)
        self.assertIn("analyzed_query", explanation)
        self.assertIn("retrieval_k", explanation)
        self.assertIn("min_confidence", explanation)
        self.assertIn("processing_steps", explanation)
        
        self.assertEqual(explanation["original_query"], "Test query")
        self.assertEqual(explanation["retrieval_k"], 5)
        self.assertEqual(explanation["min_confidence"], 0.5)
        self.assertIsInstance(explanation["processing_steps"], list)
    
    def test_error_propagation(self):
        """Test that errors are properly propagated."""
        # Make retriever raise an error
        self.mock_retriever.retrieve.side_effect = Exception("Retrieval failed")
        
        with self.assertRaises(RuntimeError) as context:
            self.processor.process("Test query")
        
        self.assertIn("Query processing failed", str(context.exception))
    
    def test_minimal_config(self):
        """Test query processor with minimal configuration."""
        # Create processor without config
        processor = QueryProcessor(
            retriever=self.mock_retriever,
            generator=self.mock_generator
        )
        
        # Verify defaults
        self.assertEqual(processor.default_k, 5)
        self.assertEqual(processor.min_confidence, 0.0)
        self.assertEqual(processor.config, {})
    
    def test_metadata_preservation(self):
        """Test that existing answer metadata is preserved."""
        # Set up mock returns
        self.mock_retriever.retrieve.return_value = [
            RetrievalResult(
                document=Document(content="Test", metadata={"id": "1", "source": "test.pdf"}),
                score=0.9,
                retrieval_method="hybrid"
            )
        ]
        
        # Answer with existing metadata
        test_answer = Answer(
            text="Test answer",
            sources=[],
            confidence=0.8,
            metadata={"existing_key": "existing_value"}
        )
        self.mock_generator.generate.return_value = test_answer
        
        # Process query
        result = self.processor.process("Test query")
        
        # Verify existing metadata is preserved
        self.assertEqual(result.metadata["existing_key"], "existing_value")
        # And new metadata is added
        self.assertIn("query", result.metadata)
        self.assertIn("processor", result.metadata)


if __name__ == '__main__':
    unittest.main()