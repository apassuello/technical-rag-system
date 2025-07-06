"""
Unit tests for core interfaces and data classes.

Tests the Document, RetrievalResult, and Answer dataclasses
to ensure they work correctly with validation.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import (
    Document, 
    RetrievalResult, 
    Answer,
    DocumentProcessor,
    Embedder,
    VectorStore,
    Retriever,
    AnswerGenerator
)


class TestDocument:
    """Test Document dataclass."""
    
    def test_document_creation(self):
        """Test basic document creation."""
        doc = Document(
            content="This is test content",
            metadata={"source": "test.pdf", "page": 1}
        )
        assert doc.content == "This is test content"
        assert doc.metadata["source"] == "test.pdf"
        assert doc.metadata["page"] == 1
        assert doc.embedding is None
    
    def test_document_with_embedding(self):
        """Test document with embedding."""
        embedding = [0.1, 0.2, 0.3, 0.4]
        doc = Document(
            content="Test content",
            metadata={},
            embedding=embedding
        )
        assert doc.embedding == embedding
    
    def test_document_empty_content_raises_error(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="Document content cannot be empty"):
            Document(content="", metadata={})
    
    def test_document_invalid_embedding_type(self):
        """Test that non-list embedding raises TypeError."""
        with pytest.raises(TypeError, match="Embedding must be a list of floats"):
            Document(
                content="Test content",
                metadata={},
                embedding="not a list"
            )
    
    def test_document_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        doc = Document(content="Test content")
        assert doc.metadata == {}


class TestRetrievalResult:
    """Test RetrievalResult dataclass."""
    
    def test_retrieval_result_creation(self):
        """Test basic retrieval result creation."""
        doc = Document(content="Test content", metadata={})
        result = RetrievalResult(
            document=doc,
            score=0.95,
            retrieval_method="semantic"
        )
        assert result.document == doc
        assert result.score == 0.95
        assert result.retrieval_method == "semantic"
    
    def test_retrieval_result_invalid_document_type(self):
        """Test that non-Document raises TypeError."""
        with pytest.raises(TypeError, match="document must be a Document instance"):
            RetrievalResult(
                document="not a document",
                score=0.5,
                retrieval_method="test"
            )
    
    def test_retrieval_result_score_validation(self):
        """Test score validation."""
        doc = Document(content="Test", metadata={})
        
        # Score too high
        with pytest.raises(ValueError, match="Score must be between 0 and 1"):
            RetrievalResult(document=doc, score=1.5, retrieval_method="test")
        
        # Score too low
        with pytest.raises(ValueError, match="Score must be between 0 and 1"):
            RetrievalResult(document=doc, score=-0.1, retrieval_method="test")
        
        # Valid boundary scores
        result1 = RetrievalResult(document=doc, score=0.0, retrieval_method="test")
        assert result1.score == 0.0
        
        result2 = RetrievalResult(document=doc, score=1.0, retrieval_method="test")
        assert result2.score == 1.0


class TestAnswer:
    """Test Answer dataclass."""
    
    def test_answer_creation(self):
        """Test basic answer creation."""
        doc1 = Document(content="Source 1", metadata={})
        doc2 = Document(content="Source 2", metadata={})
        
        answer = Answer(
            text="This is the answer",
            sources=[doc1, doc2],
            confidence=0.9,
            metadata={"model": "gpt-4"}
        )
        
        assert answer.text == "This is the answer"
        assert len(answer.sources) == 2
        assert answer.sources[0] == doc1
        assert answer.confidence == 0.9
        assert answer.metadata["model"] == "gpt-4"
    
    def test_answer_empty_text_raises_error(self):
        """Test that empty answer text raises ValueError."""
        with pytest.raises(ValueError, match="Answer text cannot be empty"):
            Answer(text="", sources=[], confidence=0.5)
    
    def test_answer_confidence_validation(self):
        """Test confidence validation."""
        # Confidence too high
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            Answer(text="Answer", sources=[], confidence=1.1)
        
        # Confidence too low
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            Answer(text="Answer", sources=[], confidence=-0.1)
    
    def test_answer_sources_type_validation(self):
        """Test that sources must be a list."""
        with pytest.raises(TypeError, match="Sources must be a list of Documents"):
            Answer(text="Answer", sources="not a list", confidence=0.5)
    
    def test_answer_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        answer = Answer(text="Answer", sources=[], confidence=0.5)
        assert answer.metadata == {}


class TestAbstractInterfaces:
    """Test that abstract interfaces cannot be instantiated."""
    
    def test_cannot_instantiate_document_processor(self):
        """Test DocumentProcessor is abstract."""
        with pytest.raises(TypeError):
            DocumentProcessor()
    
    def test_cannot_instantiate_embedder(self):
        """Test Embedder is abstract."""
        with pytest.raises(TypeError):
            Embedder()
    
    def test_cannot_instantiate_vector_store(self):
        """Test VectorStore is abstract."""
        with pytest.raises(TypeError):
            VectorStore()
    
    def test_cannot_instantiate_retriever(self):
        """Test Retriever is abstract."""
        with pytest.raises(TypeError):
            Retriever()
    
    def test_cannot_instantiate_answer_generator(self):
        """Test AnswerGenerator is abstract."""
        with pytest.raises(TypeError):
            AnswerGenerator()


class TestConcreteImplementations:
    """Test that concrete implementations work correctly."""
    
    def test_document_processor_implementation(self):
        """Test a concrete DocumentProcessor implementation."""
        
        class SimpleProcessor(DocumentProcessor):
            def process(self, file_path: Path):
                return [Document(content="Test chunk", metadata={"source": str(file_path)})]
            
            def supported_formats(self):
                return [".txt"]
        
        processor = SimpleProcessor()
        docs = processor.process(Path("test.txt"))
        assert len(docs) == 1
        assert docs[0].content == "Test chunk"
        assert processor.supported_formats() == [".txt"]
    
    def test_embedder_implementation(self):
        """Test a concrete Embedder implementation."""
        
        class MockEmbedder(Embedder):
            def embed(self, texts):
                return [[0.1, 0.2, 0.3] for _ in texts]
            
            def embedding_dim(self):
                return 3
        
        embedder = MockEmbedder()
        embeddings = embedder.embed(["text1", "text2"])
        assert len(embeddings) == 2
        assert embedder.embedding_dim() == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])