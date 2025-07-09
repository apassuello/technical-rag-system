# Component 2: Document Processor

**Component ID**: C2  
**Version**: 1.0  
**References**: [MASTER-ARCHITECTURE.md](./MASTER-ARCHITECTURE.md)  
**Related Components**: [C1-Platform Orchestrator](./COMPONENT-1-PLATFORM-ORCHESTRATOR.md), [C3-Embedder](./COMPONENT-3-EMBEDDER.md)

---

## 1. Component Overview

### 1.1 Purpose & Responsibility

The Document Processor transforms **raw documents into searchable chunks**:
- Multi-format document parsing (PDF, DOCX, HTML, Markdown)
- Intelligent text chunking preserving semantic meaning
- Content cleaning and normalization
- Metadata extraction and preservation

### 1.2 Position in System

**Pipeline Position**: First stage in document ingestion
- **Input**: Raw document files from Platform Orchestrator
- **Output**: Cleaned, chunked documents to Embedder

### 1.3 Key Design Decisions

1. **Modular Sub-components**: Parser, Chunker, Cleaner as separate concerns
2. **Format-Agnostic Interface**: Unified output regardless of input format
3. **Metadata Preservation**: Critical for citation and retrieval quality

---

## 2. Requirements

### 2.1 Functional Requirements

**Core Capabilities**:
- FR1: Parse PDF documents with layout preservation
- FR2: Extract text from DOCX, HTML, Markdown formats
- FR3: Chunk text maintaining semantic boundaries
- FR4: Clean content (normalize, remove artifacts)
- FR5: Extract and preserve document metadata

**Interface Contracts**: See [Document Processor Interface](./rag-interface-reference.md#2-main-component-interfaces)

**Behavioral Specifications**:
- Must preserve code blocks and technical formatting
- Must handle corrupt/malformed documents gracefully
- Must maintain document structure metadata

### 2.2 Quality Requirements

**Performance**:
- Processing speed: >1M chars/second
- Memory usage: <500MB for 100MB document
- Chunking efficiency: <50ms per 10KB text

**Reliability**:
- Handle all supported formats without crashes
- Graceful degradation for unsupported content
- Consistent output format

**Scalability**:
- Process documents up to 500MB
- Batch processing capability
- Stateless for parallel processing

---

## 3. Architecture Design

### 3.1 Internal Structure

```
Document Processor
├── Document Parser (sub-component)
├── Text Chunker (sub-component)
├── Content Cleaner (sub-component)
└── Pipeline Coordinator
```

### 3.2 Sub-Components

**Document Parser**:
- **Purpose**: Extract text and structure from various formats
- **Implementation**: Adapter pattern for external libraries
- **Decision**: Different parsing libraries have incompatible APIs
- **Variants**: PyMuPDF (PDF), python-docx (DOCX), BeautifulSoup (HTML)

**Text Chunker**:
- **Purpose**: Split documents into retrieval-sized chunks
- **Implementation**: Direct implementation (pure algorithms)
- **Decision**: No external dependencies, just text processing
- **Variants**: Sentence-boundary, Semantic, Structural, Fixed-size

**Content Cleaner**:
- **Purpose**: Normalize and clean text content
- **Implementation**: Direct implementation
- **Decision**: Pure text transformation algorithms
- **Variants**: Technical, Language-specific, PII

See detailed rationale in [Adapter Pattern Analysis](./rag-adapter-pattern-analysis.md)

### 3.3 Adapter vs Direct

**Uses Adapters For**:
- Document parsers (PyMuPDF, Tika, python-docx)
- External format conversion services

**Direct Implementation For**:
- All chunking strategies
- Content cleaning algorithms
- Metadata extraction logic

### 3.4 State Management

**Stateless Processing**:
- Each document processed independently
- No state carried between documents
- Thread-safe for parallel processing

---

## 4. Interfaces

### 4.1 Provided Interfaces

See [Document Processor Interface](./rag-interface-reference.md#31-document-processing-sub-components)

**Main Interface**:
- `process(file_path) -> List[Document]`
- `supported_formats() -> List[str]`
- `validate_document(file_path) -> ValidationResult`

### 4.2 Required Interfaces

- File system access for document reading
- Embedder interface for passing processed documents

### 4.3 Events Published

- Document processing started/completed
- Processing errors/warnings
- Metrics (pages processed, chunks created)

---

## 5. Design Rationale

### Architectural Decisions

**AD1: Separate Parser/Chunker/Cleaner**
- **Decision**: Three distinct sub-components vs monolithic
- **Rationale**: Single responsibility, easier testing
- **Trade-off**: More coordination complexity

**AD2: Adapter Pattern for Parsers**
- **Decision**: Wrap external libraries with adapters
- **Rationale**: Libraries have incompatible APIs
- **Trade-off**: Extra abstraction layer

**AD3: Metadata-Rich Chunks**
- **Decision**: Preserve extensive metadata with each chunk
- **Rationale**: Better retrieval and citation quality
- **Trade-off**: Increased storage requirements

### Alternatives Considered

1. **Unified Parsing Library**: No single library handles all formats well
2. **Cloud Parsing Services**: Rejected for latency and privacy
3. **Simple String Split**: Loses semantic boundaries

---

## 6. Implementation Guidelines

### Current Implementation Notes

- PyMuPDF selected for superior PDF handling
- Sentence-boundary chunking with 200 token overlap
- Achieved 1.2M chars/sec processing speed

### Best Practices

1. **Validate file format** before processing
2. **Set reasonable size limits** to prevent OOM
3. **Preserve original formatting** in metadata
4. **Log parsing errors** with context

### Common Pitfalls

- Don't assume document structure consistency
- Don't lose formatting in code blocks
- Don't create chunks smaller than embedding window
- Don't ignore document metadata

### Performance Considerations

- Stream large documents vs loading fully
- Batch small documents for efficiency
- Cache parsed results for repeated processing
- Use parallel processing for multiple documents

---

## 7. Configuration

### Configuration Schema

```yaml
document_processor:
  parser:
    type: "hybrid_pdf"  # or "tika", "native"
    config:
      max_file_size_mb: 100
      extract_images: false
      preserve_layout: true
      
  chunker:
    type: "sentence_boundary"  # or "semantic", "fixed"
    config:
      chunk_size: 1000
      chunk_overlap: 200
      min_chunk_size: 100
      
  cleaner:
    type: "technical"  # or "general", "pii"
    config:
      normalize_whitespace: true
      remove_special_chars: false
      detect_pii: false
```

---

## 8. Operations

### Health Checks

- Verify parser libraries loaded
- Test parsing small sample document
- Check available memory for processing

### Metrics Exposed

- `processor_documents_total`
- `processor_chunks_created_total`
- `processor_processing_time_seconds`
- `processor_errors_total{type="parse|chunk|clean"}`

### Logging Strategy

- DEBUG: Chunk boundaries and decisions
- INFO: Document processing summary
- WARN: Recoverable parsing issues
- ERROR: Failed document processing

### Troubleshooting Guide

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| Slow parsing | Complex PDF structure | Try alternative parser |
| Lost formatting | Wrong parser settings | Enable layout preservation |
| OOM errors | Large documents | Increase memory or stream |
| Bad chunks | Poor boundaries | Adjust chunking strategy |

---

## 9. Future Enhancements

### Planned Features

1. **Table Extraction**: Structured data from documents
2. **OCR Support**: Handle scanned documents
3. **Multi-lingual**: Language-specific chunking
4. **Diagram Extraction**: Technical drawings and figures

### Extension Points

- Custom document parsers
- Pluggable chunking strategies
- Domain-specific cleaners
- Format converters

### Known Limitations

- No OCR capability currently
- Limited table extraction
- English-optimized chunking
- No image extraction