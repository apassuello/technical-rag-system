"""
Unit tests for graph components (Epic 2 Week 2).

This module provides comprehensive tests for the graph-based retrieval
components including entity extraction, graph construction, relationship
mapping, and graph retrieval functionality.
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import graph components
try:
    from src.components.retrievers.graph.config.graph_config import (
        GraphConfig, GraphBuilderConfig, EntityExtractionConfig,
        RelationshipDetectionConfig, GraphRetrievalConfig, GraphAnalyticsConfig
    )
    from src.components.retrievers.graph.entity_extraction import EntityExtractor, Entity
    from src.components.retrievers.graph.document_graph_builder import DocumentGraphBuilder, GraphNode, GraphEdge
    from src.components.retrievers.graph.relationship_mapper import RelationshipMapper, Relationship
    from src.components.retrievers.graph.graph_retriever import GraphRetriever, GraphSearchResult
    from src.components.retrievers.graph.graph_analytics import GraphAnalytics, GraphMetrics
    from src.core.interfaces import Document
    GRAPH_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Graph components not available: {e}")
    GRAPH_COMPONENTS_AVAILABLE = False


@unittest.skipUnless(GRAPH_COMPONENTS_AVAILABLE, "Graph components not available")
class TestGraphConfig(unittest.TestCase):
    """Test graph configuration classes."""
    
    def test_graph_config_creation(self):
        """Test creation of GraphConfig with default values."""
        config = GraphConfig()
        
        self.assertTrue(config.enabled)
        self.assertIsInstance(config.builder, GraphBuilderConfig)
        self.assertIsInstance(config.entity_extraction, EntityExtractionConfig)
        self.assertIsInstance(config.relationship_detection, RelationshipDetectionConfig)
        self.assertIsInstance(config.retrieval, GraphRetrievalConfig)
        self.assertIsInstance(config.analytics, GraphAnalyticsConfig)
    
    def test_graph_config_from_dict(self):
        """Test creation of GraphConfig from dictionary."""
        config_dict = {
            "enabled": True,
            "builder": {
                "implementation": "networkx",
                "config": {
                    "node_types": ["concept", "protocol"],
                    "max_graph_size": 5000
                }
            },
            "entity_extraction": {
                "implementation": "spacy",
                "config": {
                    "model": "en_core_web_sm",
                    "confidence_threshold": 0.9
                }
            }
        }
        
        config = GraphConfig.from_dict(config_dict)
        
        self.assertTrue(config.enabled)
        self.assertEqual(config.builder.implementation, "networkx")
        self.assertEqual(config.builder.max_graph_size, 5000)
        self.assertEqual(config.entity_extraction.model, "en_core_web_sm")
        self.assertEqual(config.entity_extraction.confidence_threshold, 0.9)
    
    def test_graph_config_validation(self):
        """Test configuration validation."""
        config = GraphConfig()
        issues = config.validate()
        
        # Should have no validation issues with default config
        self.assertEqual(len(issues), 0)
        
        # Test invalid configuration
        config.builder.max_graph_size = -1
        config.entity_extraction.confidence_threshold = 1.5
        
        issues = config.validate()
        self.assertGreater(len(issues), 0)
        self.assertTrue(any("max_graph_size must be positive" in issue for issue in issues))
        self.assertTrue(any("confidence_threshold must be between 0 and 1" in issue for issue in issues))


@unittest.skipUnless(GRAPH_COMPONENTS_AVAILABLE, "Graph components not available")
class TestEntityExtractor(unittest.TestCase):
    """Test entity extraction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = EntityExtractionConfig(
            implementation="spacy",
            model="en_core_web_sm",
            confidence_threshold=0.5,
            batch_size=2
        )
        
        # Mock spaCy to avoid dependency on actual model
        self.mock_nlp = Mock()
        self.mock_matcher = Mock()
        
    @patch('src.components.retrievers.graph.entity_extraction.spacy')
    def test_entity_extractor_initialization(self, mock_spacy):
        """Test entity extractor initialization."""
        mock_spacy.load.return_value = self.mock_nlp
        mock_spacy.Matcher.return_value = self.mock_matcher
        
        extractor = EntityExtractor(self.config)
        
        self.assertEqual(extractor.config, self.config)
        mock_spacy.load.assert_called_once_with("en_core_web_sm")
    
    @patch('src.components.retrievers.graph.entity_extraction.spacy')
    def test_extract_entities_empty_documents(self, mock_spacy):
        """Test entity extraction with empty document list."""
        mock_spacy.load.return_value = self.mock_nlp
        mock_spacy.Matcher.return_value = self.mock_matcher
        
        extractor = EntityExtractor(self.config)
        result = extractor.extract_entities([])
        
        self.assertEqual(result, {})
    
    @patch('src.components.retrievers.graph.entity_extraction.spacy')
    def test_extract_entities_basic(self, mock_spacy):
        """Test basic entity extraction."""
        # Mock spaCy components
        mock_spacy.load.return_value = self.mock_nlp
        mock_spacy.Matcher.return_value = self.mock_matcher
        
        # Mock document processing
        mock_doc = Mock()
        mock_doc.ents = []
        self.mock_nlp.return_value = mock_doc
        self.mock_matcher.return_value = []
        
        extractor = EntityExtractor(self.config)
        
        # Create test documents
        documents = [
            Document(id="doc1", content="RISC-V is an instruction set architecture"),
            Document(id="doc2", content="The vector extension implements SIMD operations")
        ]
        
        result = extractor.extract_entities(documents)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)
        self.assertIn("doc1", result)
        self.assertIn("doc2", result)


@unittest.skipUnless(GRAPH_COMPONENTS_AVAILABLE, "Graph components not available")
class TestDocumentGraphBuilder(unittest.TestCase):
    """Test document graph builder functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.builder_config = GraphBuilderConfig(
            implementation="networkx",
            max_graph_size=100
        )
        
        # Mock entity extractor
        self.mock_entity_extractor = Mock()
        self.mock_entity_extractor.extract_entities.return_value = {
            "doc1": [
                Entity(
                    text="RISC-V",
                    label="TECH",
                    start_pos=0,
                    end_pos=6,
                    confidence=0.9,
                    document_id="doc1"
                ),
                Entity(
                    text="instruction set",
                    label="TECH",
                    start_pos=10,
                    end_pos=25,
                    confidence=0.8,
                    document_id="doc1"
                )
            ]
        }
    
    @patch('src.components.retrievers.graph.document_graph_builder.nx')
    def test_graph_builder_initialization(self, mock_nx):
        """Test graph builder initialization."""
        mock_graph = Mock()
        mock_nx.DiGraph.return_value = mock_graph
        
        builder = DocumentGraphBuilder(self.builder_config, self.mock_entity_extractor)
        
        self.assertEqual(builder.config, self.builder_config)
        self.assertEqual(builder.entity_extractor, self.mock_entity_extractor)
        mock_nx.DiGraph.assert_called_once()
    
    @patch('src.components.retrievers.graph.document_graph_builder.nx')
    def test_build_graph_empty_documents(self, mock_nx):
        """Test graph building with empty document list."""
        mock_graph = Mock()
        mock_nx.DiGraph.return_value = mock_graph
        
        builder = DocumentGraphBuilder(self.builder_config, self.mock_entity_extractor)
        result = builder.build_graph([])
        
        self.assertEqual(result, mock_graph)
    
    @patch('src.components.retrievers.graph.document_graph_builder.nx')
    def test_build_graph_basic(self, mock_nx):
        """Test basic graph building."""
        mock_graph = Mock()
        mock_nx.DiGraph.return_value = mock_graph
        
        builder = DocumentGraphBuilder(self.builder_config, self.mock_entity_extractor)
        
        # Create test documents
        documents = [
            Document(id="doc1", content="RISC-V instruction set architecture")
        ]
        
        result = builder.build_graph(documents)
        
        self.assertEqual(result, mock_graph)
        self.mock_entity_extractor.extract_entities.assert_called_once_with(documents)


@unittest.skipUnless(GRAPH_COMPONENTS_AVAILABLE, "Graph components not available")
class TestRelationshipMapper(unittest.TestCase):
    """Test relationship mapping functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = RelationshipDetectionConfig(
            implementation="semantic",
            similarity_threshold=0.7
        )
    
    def test_relationship_mapper_initialization(self):
        """Test relationship mapper initialization."""
        mapper = RelationshipMapper(self.config)
        
        self.assertEqual(mapper.config, self.config)
        self.assertIsInstance(mapper.relationship_patterns, dict)
        self.assertIn("implements", mapper.relationship_patterns)
        self.assertIn("extends", mapper.relationship_patterns)
        self.assertIn("requires", mapper.relationship_patterns)
        self.assertIn("conflicts", mapper.relationship_patterns)
    
    def test_detect_relationships_empty(self):
        """Test relationship detection with empty inputs."""
        mapper = RelationshipMapper(self.config)
        
        result = mapper.detect_relationships([], {})
        self.assertEqual(result, {})


@unittest.skipUnless(GRAPH_COMPONENTS_AVAILABLE, "Graph components not available")
class TestGraphRetriever(unittest.TestCase):
    """Test graph retrieval functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = GraphRetrievalConfig(
            algorithms=["shortest_path"],
            max_graph_results=5
        )
        
        # Mock dependencies
        self.mock_graph_builder = Mock()
        self.mock_embedder = Mock()
        self.mock_embedder.embed.return_value = [[0.1, 0.2, 0.3]]
        
        # Mock graph
        self.mock_graph = Mock()
        self.mock_graph.nodes.return_value = ["node1", "node2"]
        self.mock_graph.nodes.__getitem__ = Mock(return_value={"text": "test", "confidence": 0.8})
        self.mock_graph_builder.get_graph.return_value = self.mock_graph
    
    @patch('src.components.retrievers.graph.graph_retriever.nx')
    def test_graph_retriever_initialization(self, mock_nx):
        """Test graph retriever initialization."""
        retriever = GraphRetriever(self.config, self.mock_graph_builder, self.mock_embedder)
        
        self.assertEqual(retriever.config, self.config)
        self.assertEqual(retriever.graph_builder, self.mock_graph_builder)
        self.assertEqual(retriever.embedder, self.mock_embedder)
    
    @patch('src.components.retrievers.graph.graph_retriever.nx')
    def test_retrieve_empty_graph(self, mock_nx):
        """Test retrieval with empty graph."""
        self.mock_graph.number_of_nodes.return_value = 0
        
        retriever = GraphRetriever(self.config, self.mock_graph_builder, self.mock_embedder)
        result = retriever.retrieve("test query", k=5)
        
        self.assertEqual(result, [])


@unittest.skipUnless(GRAPH_COMPONENTS_AVAILABLE, "Graph components not available")
class TestGraphAnalytics(unittest.TestCase):
    """Test graph analytics functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = GraphAnalyticsConfig(
            enabled=True,
            collect_graph_metrics=True,
            collect_retrieval_metrics=True
        )
    
    def test_graph_analytics_initialization(self):
        """Test graph analytics initialization."""
        analytics = GraphAnalytics(self.config)
        
        self.assertEqual(analytics.config, self.config)
        self.assertEqual(len(analytics.snapshots), 0)
        self.assertEqual(len(analytics.query_history), 0)
    
    def test_collect_graph_metrics_disabled(self):
        """Test graph metrics collection when disabled."""
        config = GraphAnalyticsConfig(collect_graph_metrics=False)
        analytics = GraphAnalytics(config)
        
        mock_graph_builder = Mock()
        result = analytics.collect_graph_metrics(mock_graph_builder)
        
        # Should return empty metrics when disabled
        self.assertEqual(result.nodes, 0)
        self.assertEqual(result.edges, 0)
    
    def test_track_query(self):
        """Test query tracking functionality."""
        analytics = GraphAnalytics(self.config)
        
        analytics.track_query(
            query="test query",
            results_count=5,
            latency_ms=100.0,
            algorithm_used="shortest_path",
            success=True
        )
        
        self.assertEqual(len(analytics.query_history), 1)
        query_record = analytics.query_history[0]
        self.assertEqual(query_record["query"], "test query")
        self.assertEqual(query_record["results_count"], 5)
        self.assertEqual(query_record["latency_ms"], 100.0)
        self.assertTrue(query_record["success"])
    
    def test_generate_report_empty(self):
        """Test report generation with no data."""
        analytics = GraphAnalytics(self.config)
        
        result = analytics.generate_report()
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "No analytics data available")


class TestGraphIntegration(unittest.TestCase):
    """Integration tests for graph components."""
    
    @unittest.skipUnless(GRAPH_COMPONENTS_AVAILABLE, "Graph components not available")
    def test_graph_config_round_trip(self):
        """Test configuration serialization and deserialization."""
        original_config = GraphConfig()
        config_dict = original_config.to_dict()
        restored_config = GraphConfig.from_dict(config_dict)
        
        # Compare key attributes
        self.assertEqual(original_config.enabled, restored_config.enabled)
        self.assertEqual(
            original_config.builder.implementation,
            restored_config.builder.implementation
        )
        self.assertEqual(
            original_config.entity_extraction.model,
            restored_config.entity_extraction.model
        )


if __name__ == "__main__":
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    if GRAPH_COMPONENTS_AVAILABLE:
        suite.addTest(unittest.makeSuite(TestGraphConfig))
        suite.addTest(unittest.makeSuite(TestEntityExtractor))
        suite.addTest(unittest.makeSuite(TestDocumentGraphBuilder))
        suite.addTest(unittest.makeSuite(TestRelationshipMapper))
        suite.addTest(unittest.makeSuite(TestGraphRetriever))
        suite.addTest(unittest.makeSuite(TestGraphAnalytics))
        suite.addTest(unittest.makeSuite(TestGraphIntegration))
    else:
        print("Skipping graph component tests - components not available")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / max(result.testsRun, 1)) * 100:.1f}%")