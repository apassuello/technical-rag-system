"""
Unit tests for the Component Registry system.

This module tests the registration, validation, and instantiation functionality
of the ComponentRegistry class and related decorators.
"""

import pytest
from typing import List
from pathlib import Path

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
from src.core.registry import (
    ComponentRegistry, 
    register_component, 
    get_available_components
)


class TestComponentRegistry:
    """Test the ComponentRegistry class."""
    
    def setup_method(self):
        """Clear registry before each test."""
        ComponentRegistry.clear_all()
    
    def test_clear_all(self):
        """Test clearing all registrations."""
        # Register something
        ComponentRegistry.register_processor("test", MockProcessor)
        assert "test" in ComponentRegistry.list_processors()
        
        # Clear and verify empty
        ComponentRegistry.clear_all()
        assert ComponentRegistry.list_processors() == []
        assert ComponentRegistry.list_embedders() == []
        assert ComponentRegistry.list_vector_stores() == []
        assert ComponentRegistry.list_retrievers() == []
        assert ComponentRegistry.list_generators() == []


class TestProcessorRegistration:
    """Test processor registration functionality."""
    
    def setup_method(self):
        """Clear registry before each test."""
        ComponentRegistry.clear_all()
    
    def test_register_valid_processor(self):
        """Test registering a valid processor."""
        ComponentRegistry.register_processor("test_processor", MockProcessor)
        assert "test_processor" in ComponentRegistry.list_processors()
    
    def test_register_invalid_processor_type(self):
        """Test registering an invalid processor type raises TypeError."""
        with pytest.raises(TypeError, match="must implement DocumentProcessor"):
            ComponentRegistry.register_processor("invalid", str)
    
    def test_register_duplicate_processor_name(self):
        """Test registering duplicate processor names raises ValueError."""
        ComponentRegistry.register_processor("duplicate", MockProcessor)
        with pytest.raises(ValueError, match="already registered"):
            ComponentRegistry.register_processor("duplicate", MockProcessor)
    
    def test_register_empty_processor_name(self):
        """Test registering with empty name raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            ComponentRegistry.register_processor("", MockProcessor)
    
    def test_create_valid_processor(self):
        """Test creating a valid processor instance."""
        ComponentRegistry.register_processor("test", MockProcessor)
        processor = ComponentRegistry.create_processor("test", test_param="value")
        assert isinstance(processor, MockProcessor)
        assert processor.test_param == "value"
    
    def test_create_unknown_processor(self):
        """Test creating unknown processor raises ValueError."""
        with pytest.raises(ValueError, match="Unknown processor 'unknown'"):
            ComponentRegistry.create_processor("unknown")
    
    def test_create_processor_with_invalid_args(self):
        """Test creating processor with invalid args raises TypeError."""
        ComponentRegistry.register_processor("test", MockProcessor)
        with pytest.raises(TypeError, match="Failed to create processor"):
            ComponentRegistry.create_processor("test", invalid_arg=True)


class TestEmbedderRegistration:
    """Test embedder registration functionality."""
    
    def setup_method(self):
        """Clear registry before each test."""
        ComponentRegistry.clear_all()
    
    def test_register_valid_embedder(self):
        """Test registering a valid embedder."""
        ComponentRegistry.register_embedder("test_embedder", MockEmbedder)
        assert "test_embedder" in ComponentRegistry.list_embedders()
    
    def test_register_invalid_embedder_type(self):
        """Test registering an invalid embedder type raises TypeError."""
        with pytest.raises(TypeError, match="must implement Embedder"):
            ComponentRegistry.register_embedder("invalid", int)
    
    def test_create_valid_embedder(self):
        """Test creating a valid embedder instance."""
        ComponentRegistry.register_embedder("test", MockEmbedder)
        embedder = ComponentRegistry.create_embedder("test", dimension=384)
        assert isinstance(embedder, MockEmbedder)
        assert embedder.dimension == 384
    
    def test_create_unknown_embedder(self):
        """Test creating unknown embedder raises ValueError."""
        with pytest.raises(ValueError, match="Unknown embedder 'unknown'"):
            ComponentRegistry.create_embedder("unknown")


class TestVectorStoreRegistration:
    """Test vector store registration functionality."""
    
    def setup_method(self):
        """Clear registry before each test."""
        ComponentRegistry.clear_all()
    
    def test_register_valid_vector_store(self):
        """Test registering a valid vector store."""
        ComponentRegistry.register_vector_store("test_store", MockVectorStore)
        assert "test_store" in ComponentRegistry.list_vector_stores()
    
    def test_register_invalid_vector_store_type(self):
        """Test registering an invalid vector store type raises TypeError."""
        with pytest.raises(TypeError, match="must implement VectorStore"):
            ComponentRegistry.register_vector_store("invalid", list)
    
    def test_create_valid_vector_store(self):
        """Test creating a valid vector store instance."""
        ComponentRegistry.register_vector_store("test", MockVectorStore)
        store = ComponentRegistry.create_vector_store("test", index_type="flat")
        assert isinstance(store, MockVectorStore)
        assert store.index_type == "flat"
    
    def test_create_unknown_vector_store(self):
        """Test creating unknown vector store raises ValueError."""
        with pytest.raises(ValueError, match="Unknown vector store 'unknown'"):
            ComponentRegistry.create_vector_store("unknown")


class TestRetrieverRegistration:
    """Test retriever registration functionality."""
    
    def setup_method(self):
        """Clear registry before each test."""
        ComponentRegistry.clear_all()
    
    def test_register_valid_retriever(self):
        """Test registering a valid retriever."""
        ComponentRegistry.register_retriever("test_retriever", MockRetriever)
        assert "test_retriever" in ComponentRegistry.list_retrievers()
    
    def test_register_invalid_retriever_type(self):
        """Test registering an invalid retriever type raises TypeError."""
        with pytest.raises(TypeError, match="must implement Retriever"):
            ComponentRegistry.register_retriever("invalid", dict)
    
    def test_create_valid_retriever(self):
        """Test creating a valid retriever instance."""
        ComponentRegistry.register_retriever("test", MockRetriever)
        retriever = ComponentRegistry.create_retriever("test", top_k=10)
        assert isinstance(retriever, MockRetriever)
        assert retriever.top_k == 10
    
    def test_create_unknown_retriever(self):
        """Test creating unknown retriever raises ValueError."""
        with pytest.raises(ValueError, match="Unknown retriever 'unknown'"):
            ComponentRegistry.create_retriever("unknown")


class TestGeneratorRegistration:
    """Test generator registration functionality."""
    
    def setup_method(self):
        """Clear registry before each test."""
        ComponentRegistry.clear_all()
    
    def test_register_valid_generator(self):
        """Test registering a valid generator."""
        ComponentRegistry.register_generator("test_generator", MockGenerator)
        assert "test_generator" in ComponentRegistry.list_generators()
    
    def test_register_invalid_generator_type(self):
        """Test registering an invalid generator type raises TypeError."""
        with pytest.raises(TypeError, match="must implement AnswerGenerator"):
            ComponentRegistry.register_generator("invalid", tuple)
    
    def test_create_valid_generator(self):
        """Test creating a valid generator instance."""
        ComponentRegistry.register_generator("test", MockGenerator)
        generator = ComponentRegistry.create_generator("test", max_tokens=256)
        assert isinstance(generator, MockGenerator)
        assert generator.max_tokens == 256
    
    def test_create_unknown_generator(self):
        """Test creating unknown generator raises ValueError."""
        with pytest.raises(ValueError, match="Unknown generator 'unknown'"):
            ComponentRegistry.create_generator("unknown")


class TestRegisterComponentDecorator:
    """Test the register_component decorator."""
    
    def setup_method(self):
        """Clear registry before each test."""
        ComponentRegistry.clear_all()
    
    def test_register_processor_decorator(self):
        """Test registering processor with decorator."""
        @register_component("processor", "decorated_processor")
        class DecoratedProcessor(MockProcessor):
            pass
        
        assert "decorated_processor" in ComponentRegistry.list_processors()
        processor = ComponentRegistry.create_processor("decorated_processor")
        assert isinstance(processor, DecoratedProcessor)
    
    def test_register_embedder_decorator(self):
        """Test registering embedder with decorator."""
        @register_component("embedder", "decorated_embedder")
        class DecoratedEmbedder(MockEmbedder):
            pass
        
        assert "decorated_embedder" in ComponentRegistry.list_embedders()
        embedder = ComponentRegistry.create_embedder("decorated_embedder")
        assert isinstance(embedder, DecoratedEmbedder)
    
    def test_register_vector_store_decorator(self):
        """Test registering vector store with decorator."""
        @register_component("vector_store", "decorated_store")
        class DecoratedStore(MockVectorStore):
            pass
        
        assert "decorated_store" in ComponentRegistry.list_vector_stores()
        store = ComponentRegistry.create_vector_store("decorated_store")
        assert isinstance(store, DecoratedStore)
    
    def test_register_retriever_decorator(self):
        """Test registering retriever with decorator."""
        @register_component("retriever", "decorated_retriever")
        class DecoratedRetriever(MockRetriever):
            pass
        
        assert "decorated_retriever" in ComponentRegistry.list_retrievers()
        retriever = ComponentRegistry.create_retriever("decorated_retriever")
        assert isinstance(retriever, DecoratedRetriever)
    
    def test_register_generator_decorator(self):
        """Test registering generator with decorator."""
        @register_component("generator", "decorated_generator")
        class DecoratedGenerator(MockGenerator):
            pass
        
        assert "decorated_generator" in ComponentRegistry.list_generators()
        generator = ComponentRegistry.create_generator("decorated_generator")
        assert isinstance(generator, DecoratedGenerator)
    
    def test_invalid_component_type_decorator(self):
        """Test decorator with invalid component type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid component type 'invalid'"):
            @register_component("invalid", "test")
            class TestClass:
                pass


class TestGetAvailableComponents:
    """Test the get_available_components function."""
    
    def setup_method(self):
        """Clear registry before each test."""
        ComponentRegistry.clear_all()
    
    def test_empty_registry(self):
        """Test getting components from empty registry."""
        components = get_available_components()
        expected = {
            "processors": [],
            "embedders": [],
            "vector_stores": [],
            "retrievers": [],
            "generators": []
        }
        assert components == expected
    
    def test_populated_registry(self):
        """Test getting components from populated registry."""
        ComponentRegistry.register_processor("proc1", MockProcessor)
        ComponentRegistry.register_embedder("emb1", MockEmbedder)
        ComponentRegistry.register_vector_store("store1", MockVectorStore)
        ComponentRegistry.register_retriever("ret1", MockRetriever)
        ComponentRegistry.register_generator("gen1", MockGenerator)
        
        components = get_available_components()
        assert "proc1" in components["processors"]
        assert "emb1" in components["embedders"]
        assert "store1" in components["vector_stores"]
        assert "ret1" in components["retrievers"]
        assert "gen1" in components["generators"]


# Mock implementations for testing
class MockProcessor(DocumentProcessor):
    """Mock DocumentProcessor for testing."""
    
    def __init__(self, test_param="default"):
        self.test_param = test_param
    
    def process(self, file_path: Path) -> List[Document]:
        """Mock process method."""
        return [Document(content="test", metadata={"source": str(file_path)})]
    
    def supported_formats(self) -> List[str]:
        """Mock supported formats."""
        return [".txt", ".pdf"]


class MockEmbedder(Embedder):
    """Mock Embedder for testing."""
    
    def __init__(self, dimension=384):
        self.dimension = dimension
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Mock embed method."""
        return [[0.1] * self.dimension for _ in texts]
    
    def embedding_dim(self) -> int:
        """Mock embedding dimension."""
        return self.dimension


class MockVectorStore(VectorStore):
    """Mock VectorStore for testing."""
    
    def __init__(self, index_type="flat"):
        self.index_type = index_type
        self.documents = []
    
    def add(self, documents: List[Document]) -> None:
        """Mock add method."""
        self.documents.extend(documents)
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[RetrievalResult]:
        """Mock search method."""
        results = []
        for i, doc in enumerate(self.documents[:k]):
            result = RetrievalResult(
                document=doc,
                score=1.0 - i * 0.1,
                retrieval_method="mock"
            )
            results.append(result)
        return results
    
    def delete(self, doc_ids: List[str]) -> None:
        """Mock delete method."""
        pass
    
    def clear(self) -> None:
        """Mock clear method."""
        self.documents.clear()


class MockRetriever(Retriever):
    """Mock Retriever for testing."""
    
    def __init__(self, top_k=5):
        self.top_k = top_k
    
    def retrieve(self, query: str, k: int = 5) -> List[RetrievalResult]:
        """Mock retrieve method."""
        doc = Document(content=f"Result for: {query}", metadata={})
        return [RetrievalResult(document=doc, score=0.9, retrieval_method="mock")]


class MockGenerator(AnswerGenerator):
    """Mock AnswerGenerator for testing."""
    
    def __init__(self, max_tokens=512):
        self.max_tokens = max_tokens
    
    def generate(self, query: str, context: List[Document]) -> Answer:
        """Mock generate method."""
        return Answer(
            text=f"Mock answer for: {query}",
            sources=context,
            confidence=0.8,
            metadata={"max_tokens": self.max_tokens}
        )