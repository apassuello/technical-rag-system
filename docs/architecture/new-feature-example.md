# Example: Documenting a New Feature

## Scenario: Adding Multi-Modal Embeddings to the Embedder Component

This example shows how to update the architecture documentation when adding a significant new feature.

---

## 1. Update Component Documentation

### Edit: `docs/architecture/components/COMPONENT-3-EMBEDDER.md`

```markdown
# Component 3: Embedder

**Component ID**: C3  
**Version**: 1.1  <!-- Increment version -->
**References**: [MASTER-ARCHITECTURE.md](./MASTER-ARCHITECTURE.md)  
**Related Components**: [C2-Document Processor](./COMPONENT-2-DOCUMENT-PROCESSOR.md), [C4-Retriever](./COMPONENT-4-RETRIEVER.md)

---

## Change Log
- v1.1 (2025-02): Added multi-modal embedding support for images

---

## 1. Component Overview

### 1.1 Purpose & Responsibility

The Embedder transforms **text and images into vector representations** for semantic search:
- Generate high-quality embeddings from text chunks
- **NEW**: Generate embeddings from images and diagrams  <!-- Highlight changes -->
- Optimize batch processing for efficiency
- Cache embeddings to avoid recomputation
- Support multiple embedding models

[...]

## 3. Architecture Design

### 3.2 Sub-Components

**Embedding Model**:
- **Purpose**: Core embedding generation
- **Implementation**: Mixed (Direct for local, Adapter for APIs)
- **Decision**: External APIs need format conversion
- **Variants**: 
  - SentenceTransformer (direct) - Text only
  - OpenAI (adapter) - Text only
  - **NEW**: CLIP (adapter) - Multi-modal  <!-- Add new variant -->
  - **NEW**: ImageBind (direct) - Multi-modal

**NEW: Image Preprocessor**:  <!-- New sub-component -->
- **Purpose**: Prepare images for embedding
- **Implementation**: Direct implementation
- **Decision**: Image processing is internal logic
- **Variants**: ResizePreprocessor, NormalizePreprocessor

[...]

## 9. Future Enhancements

### Planned Features

1. ~~Multi-modal Embeddings~~: ✅ Implemented in v1.1
2. Fine-tuned Models: Domain-specific embeddings
3. Quantized Models: Reduced memory usage
4. Cross-lingual: Multilingual embedding support
```

---

## 2. Update Master Architecture

### Edit: `docs/architecture/MASTER-ARCHITECTURE.md`

```markdown
## 3.5 Performance Optimization

**Strategies**:
- **Caching**: Multi-level (memory → Redis → disk)
- **Batching**: Dynamic batch sizing for GPU operations
  - **NEW**: Separate batch queues for text and image processing
- **Indexing**: Appropriate index selection (exact vs approximate)
- **Parallelization**: Component-level and data-level

[...]

## 7.2 Scaling Strategies

**Horizontal Scaling**:
- Stateless components (Processor, Embedder)
  - **NEW**: Image embedding workers can scale independently
- Shared storage for vectors

**Vertical Scaling**:
- GPU for embeddings and LLM
  - **NEW**: Multi-GPU support for parallel text/image processing
```

---

## 3. Update Related Components

### Edit: `docs/architecture/components/COMPONENT-2-DOCUMENT-PROCESSOR.md`

```markdown
## 4. Interfaces

### 4.1 Provided Interfaces

See [Document Processor Interface](./rag-interface-reference.md#31-document-processing-sub-components)

**Main Interface**:
- `process(file_path) -> List[Document]`
- `supported_formats() -> List[str]`
- `validate_document(file_path) -> ValidationResult`

**NEW in v1.1**:
- `extract_images(file_path) -> List[Image]`  <!-- New method -->
- Image extraction supported for PDF and DOCX formats

### 4.3 Events Published

- Document processing started/completed
- Processing errors/warnings
- Metrics (pages processed, chunks created)
- **NEW**: Images extracted count  <!-- New event -->
```

---

## 4. Create Architecture Decision Record

### Create: `docs/decisions/005-multimodal-embeddings.md`

```markdown
# ADR-005: Multi-Modal Embedding Support

**Status**: Accepted  
**Date**: 2025-02-01  
**Deciders**: ML Team, Architecture Team  

## Context

Technical documentation increasingly includes diagrams, schematics, and visual elements that contain critical information not present in text. Our current text-only embedding approach misses this visual information.

Related: [COMPONENT-3-EMBEDDER.md](../architecture/components/COMPONENT-3-EMBEDDER.md)

## Decision

We will extend the Embedder component to support multi-modal embeddings using:
1. CLIP model for unified text-image embedding space
2. Separate preprocessing pipeline for images
3. Extended Document model to include image references

## Consequences

### Positive
- Better retrieval for visual technical content
- Unified embedding space for text and images
- Maintains backward compatibility

### Negative
- Increased model size and memory usage
- Higher processing time for documents with images
- More complex caching strategy needed

### Neutral
- Requires GPU for reasonable performance
- Need to update Retriever for multi-modal search

## Implementation Notes

See implementation plan in [COMPONENT-3-EMBEDDER.md v1.1](../architecture/components/COMPONENT-3-EMBEDDER.md)
```

---

## 5. Update Code with Documentation References

### In: `src/components/embedders/multimodal_embedder.py`

```python
"""
Multi-Modal Embedder Implementation.

Architecture Specification: docs/architecture/components/COMPONENT-3-EMBEDDER.md#multi-modal
Design Decision: docs/decisions/005-multimodal-embeddings.md
Interface Reference: docs/architecture/diagrams/rag-interface-reference.md#embedder

Version: 1.1
Added: 2025-02
"""

from typing import List, Union
import numpy as np

from src.core.interfaces import Embedder, Document, Image
from src.components.embedders.adapters import CLIPAdapter

class MultiModalEmbedder(Embedder):
    """
    Embedder supporting both text and image inputs.
    
    Uses CLIP model for unified embedding space.
    See architecture documentation for design rationale.
    """
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        # Implementation
        pass
```

---

## 6. Update Test Documentation

### In: `tests/integration/test_multimodal_pipeline.py`

```python
"""
Multi-Modal Pipeline Integration Tests.

Tests the enhanced pipeline with image support as specified in:
- Architecture: docs/architecture/components/COMPONENT-3-EMBEDDER.md#multi-modal
- Sequence Flow: docs/architecture/diagrams/rag-main-sequences.md#document-processing

Test Scenarios:
1. Text-only documents (backward compatibility)
2. Documents with embedded images
3. Mixed text and image retrieval
"""
```

---

## 7. Communication Template

### Pull Request Description

```markdown
## Add Multi-Modal Embedding Support

### Overview
Extends the Embedder component to support image embeddings alongside text, enabling better retrieval for technical documentation with diagrams.

### Architecture Updates
- Updated [COMPONENT-3-EMBEDDER.md](docs/architecture/components/COMPONENT-3-EMBEDDER.md) to v1.1
- Added [ADR-005](docs/decisions/005-multimodal-embeddings.md) documenting the decision
- Updated related component interfaces

### Implementation
- New `MultiModalEmbedder` class with CLIP support
- Image preprocessing pipeline
- Extended caching for image embeddings

### Testing
- Integration tests for multi-modal pipeline
- Performance benchmarks included
- Backward compatibility verified

Closes #123
```

---

## 8. Review Checklist

```markdown
## Architecture Review Checklist

### Documentation Updates
- [ ] Component specification updated with version bump
- [ ] Master architecture updated if needed
- [ ] Related components updated
- [ ] ADR created for significant decisions
- [ ] Change log updated

### Code Integration
- [ ] Code includes documentation references
- [ ] Interfaces match specification
- [ ] Tests reference architecture docs

### Cross-References
- [ ] All cross-references valid
- [ ] Run `scripts/check_doc_references.py`
- [ ] Navigation still makes sense

### Communication
- [ ] Team notified of architecture changes
- [ ] PR description includes doc updates
- [ ] Any breaking changes highlighted
```