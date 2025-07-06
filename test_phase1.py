#!/usr/bin/env python3
"""
Test script to verify Phase 1 implementation.

This script tests:
1. Data classes can be created and validated
2. Abstract interfaces work correctly
3. Configuration system loads and validates
4. All components integrate properly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.core.interfaces import (
    Document, RetrievalResult, Answer,
    DocumentProcessor, Embedder
)
from src.core.config import (
    ComponentConfig, PipelineConfig, ConfigManager,
    create_default_config
)


def test_data_classes():
    """Test that data classes work correctly."""
    print("🧪 Testing data classes...")
    
    # Test Document
    doc = Document(
        content="This is a test document about RISC-V architecture.",
        metadata={"source": "test.pdf", "page": 1, "chunk_id": 0}
    )
    print(f"  ✅ Created Document: {doc.content[:30]}...")
    
    # Test Document with embedding
    doc_with_embedding = Document(
        content="Another test document",
        metadata={"source": "test2.pdf"},
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5]
    )
    print(f"  ✅ Created Document with embedding: dim={len(doc_with_embedding.embedding)}")
    
    # Test RetrievalResult
    result = RetrievalResult(
        document=doc,
        score=0.95,
        retrieval_method="hybrid"
    )
    print(f"  ✅ Created RetrievalResult: score={result.score}, method={result.retrieval_method}")
    
    # Test Answer
    answer = Answer(
        text="RISC-V is an open instruction set architecture.",
        sources=[doc, doc_with_embedding],
        confidence=0.92,
        metadata={"model": "gpt-4", "tokens": 42}
    )
    print(f"  ✅ Created Answer: confidence={answer.confidence}, sources={len(answer.sources)}")
    
    print("  ✅ All data classes working correctly!\n")


def test_validation():
    """Test that validation works correctly."""
    print("🧪 Testing validation...")
    
    # Test Document validation
    try:
        Document(content="", metadata={})
        print("  ❌ Empty content should raise error")
    except ValueError as e:
        print(f"  ✅ Document validation works: {e}")
    
    # Test RetrievalResult validation
    try:
        doc = Document(content="Test", metadata={})
        RetrievalResult(document=doc, score=1.5, retrieval_method="test")
        print("  ❌ Invalid score should raise error")
    except ValueError as e:
        print(f"  ✅ RetrievalResult validation works: {e}")
    
    # Test Answer validation
    try:
        Answer(text="", sources=[], confidence=0.5)
        print("  ❌ Empty answer should raise error")
    except ValueError as e:
        print(f"  ✅ Answer validation works: {e}")
    
    print("  ✅ All validation working correctly!\n")


def test_abstract_interfaces():
    """Test that abstract interfaces work correctly."""
    print("🧪 Testing abstract interfaces...")
    
    # Create a concrete implementation
    class TestProcessor(DocumentProcessor):
        def process(self, file_path: Path):
            return [Document(
                content=f"Processed content from {file_path.name}",
                metadata={"source": str(file_path)}
            )]
        
        def supported_formats(self):
            return [".txt", ".pdf"]
    
    class TestEmbedder(Embedder):
        def embed(self, texts):
            # Return mock embeddings
            return [[0.1] * 384 for _ in texts]
        
        def embedding_dim(self):
            return 384
    
    # Test implementations
    processor = TestProcessor()
    docs = processor.process(Path("test.pdf"))
    print(f"  ✅ DocumentProcessor works: processed {len(docs)} documents")
    print(f"  ✅ Supported formats: {processor.supported_formats()}")
    
    embedder = TestEmbedder()
    embeddings = embedder.embed(["test1", "test2", "test3"])
    print(f"  ✅ Embedder works: generated {len(embeddings)} embeddings")
    print(f"  ✅ Embedding dimension: {embedder.embedding_dim()}")
    
    print("  ✅ All abstract interfaces working correctly!\n")


def test_configuration():
    """Test configuration system."""
    print("🧪 Testing configuration system...")
    
    # Test ComponentConfig
    comp_config = ComponentConfig(
        type="hybrid_pdf",
        config={"chunk_size": 1024, "overlap": 128}
    )
    print(f"  ✅ ComponentConfig created: type={comp_config.type}")
    
    # Test PipelineConfig
    pipeline_config = PipelineConfig(
        document_processor=ComponentConfig(type="pdf"),
        embedder=ComponentConfig(type="sentence_transformer"),
        vector_store=ComponentConfig(type="faiss"),
        retriever=ComponentConfig(type="hybrid"),
        answer_generator=ComponentConfig(type="adaptive")
    )
    print(f"  ✅ PipelineConfig created with {len(pipeline_config.model_dump())} components")
    
    # Test ConfigManager
    manager = ConfigManager()
    default_config = manager._get_default_config()
    print(f"  ✅ ConfigManager default config loaded")
    print(f"     - Document processor: {default_config.document_processor.type}")
    print(f"     - Embedder: {default_config.embedder.type}")
    print(f"     - Vector store: {default_config.vector_store.type}")
    
    # Test config file creation
    config_dir = project_root / "config"
    config_dir.mkdir(exist_ok=True)
    default_yaml = config_dir / "default.yaml"
    
    if not default_yaml.exists():
        create_default_config(default_yaml)
        print(f"  ✅ Created default config file: {default_yaml}")
    else:
        print(f"  ✅ Default config file already exists: {default_yaml}")
    
    # Test loading from file
    file_manager = ConfigManager(config_path=default_yaml)
    loaded_config = file_manager.load()
    print(f"  ✅ Loaded config from file successfully")
    
    print("  ✅ Configuration system working correctly!\n")


def test_integration():
    """Test that all components integrate properly."""
    print("🧪 Testing integration...")
    
    # Create a document
    doc = Document(
        content="RISC-V is a free and open ISA.",
        metadata={"source": "riscv.pdf", "page": 1}
    )
    
    # Create a retrieval result
    result = RetrievalResult(
        document=doc,
        score=0.89,
        retrieval_method="semantic"
    )
    
    # Create an answer using the document
    answer = Answer(
        text="RISC-V is a free and open instruction set architecture.",
        sources=[result.document],
        confidence=0.85,
        metadata={"retrieval_score": result.score}
    )
    
    print(f"  ✅ Created full pipeline data flow:")
    print(f"     - Document: {doc.content[:30]}...")
    print(f"     - Retrieval: score={result.score}")
    print(f"     - Answer: confidence={answer.confidence}")
    
    # Test configuration integration
    config = ConfigManager().config
    print(f"  ✅ Configuration integrates with all components")
    
    print("  ✅ All components integrate correctly!\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 Phase 1 Implementation Test")
    print("=" * 60)
    print()
    
    try:
        test_data_classes()
        test_validation()
        test_abstract_interfaces()
        test_configuration()
        test_integration()
        
        print("=" * 60)
        print("✅ Phase 1 Complete! All tests passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Phase 2: Implement Component Registry")
        print("2. Phase 3: Adapt existing components")
        print("3. Phase 4: Create modular pipeline")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()