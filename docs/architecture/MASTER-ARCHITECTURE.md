# Master Architecture Specification
## RAG Technical Documentation System

**Version**: 1.0  
**Status**: Production Ready (80.6% Portfolio Score)  
**Last Updated**: July 2025

---

## 1. System Overview

### 1.1 Architecture Vision & Principles

The system implements a **6-component simplified architecture** optimized for:
- **Clarity**: Each component has single responsibility
- **Performance**: Direct wiring eliminates runtime overhead
- **Flexibility**: Pluggable implementations via component factory
- **Quality**: Swiss engineering standards throughout

### 1.2 System Context

**Purpose**: Production-grade RAG system for technical documentation Q&A  
**Domain**: Embedded systems and technical documentation  
**Scale**: 10K-1M documents, sub-second query response  
**Users**: Engineers querying technical manuals and specifications

### 1.3 Technology Stack

- **Language**: Python 3.11+
- **ML Framework**: PyTorch, Sentence Transformers
- **Vector Store**: FAISS (local), Pinecone (cloud)
- **LLM**: Ollama (local), OpenAI API (cloud)
- **Infrastructure**: Apple Silicon optimized, cloud-ready

---

## 2. Global Architecture Decisions

### 2.1 Six-Component Model

**Decision**: Simplified from traditional 10+ component RAG architectures  
**Rationale**: Reduces complexity while maintaining functionality  
**Components**:
1. Platform Orchestrator - System lifecycle
2. Document Processor - Document handling
3. Embedder - Vectorization
4. Retriever - Search & retrieval
5. Answer Generator - Response generation
6. Query Processor - Query workflow

### 2.2 Direct Wiring Pattern

**Decision**: Components hold direct references after initialization  
**Rationale**: 
- 20% faster initialization vs abstract factories
- Simpler debugging and testing
- Clear dependency graph

**Implementation**: See [Component Factory Pattern](#24-component-factory-pattern)

### 2.3 Adapter Pattern Guidelines

**When to Use Adapters**:
- External API integration (LLMs, cloud services)
- Protocol translation (REST, gRPC)
- Format conversion (vendor-specific formats)

**When NOT to Use**:
- Pure algorithms (chunking, scoring)
- Internal transformations
- Simple delegations

**Reference**: [Adapter Pattern Analysis](./rag-adapter-pattern-analysis.md)

### 2.4 Component Factory Pattern

**Purpose**: Centralized component creation with dependency injection  
**Benefits**:
- Type safety with configuration validation
- Consistent error handling
- Easy testing with mock components

---

## 3. Cross-Cutting Concepts

### 3.1 Interface Design Standards

**Principles**:
- All components implement abstract base classes
- Consistent method naming: `process()`, `validate()`, `get_metrics()`
- Clear input/output contracts using dataclasses

**Reference**: [Complete Interface Reference](./rag-interface-reference.md#1-core-data-types)

### 3.2 Configuration Management

**Approach**: YAML-based with environment overrides
```yaml
component:
  type: "implementation_name"
  config:
    param1: value1
    param2: value2
```

**Validation**: Schema-based with detailed error messages  
**Reference**: [Configuration Schemas](./rag-interface-reference.md#4-configuration-schemas)

### 3.3 Error Handling & Resilience

**Patterns**:
- **Circuit Breaker**: For external service calls
- **Graceful Degradation**: Fallback strategies
- **Retry Logic**: Exponential backoff for transient failures

**Error Hierarchy**:
- `ComponentError` - Base for all component errors
- `ConfigurationError` - Invalid configuration
- `ProcessingError` - Runtime processing failures
- `ExternalServiceError` - External dependency failures

### 3.4 Monitoring & Observability

**Metrics Collection**:
- Every component exposes `get_metrics()` method
- Prometheus-compatible format
- Key metrics: latency, throughput, error rate, resource usage

**Health Checks**:
- Component-level health status
- Dependency verification
- Performance degradation detection

### 3.5 Performance Optimization

**Strategies**:
- **Caching**: Multi-level (memory → Redis → disk)
- **Batching**: Dynamic batch sizing for GPU operations
- **Indexing**: Appropriate index selection (exact vs approximate)
- **Parallelization**: Component-level and data-level

**Targets**:
- Document processing: >1M chars/sec
- Retrieval: <10ms average
- End-to-end query: <2s

### 3.6 Security Architecture

**Principles**:
- Input validation at component boundaries
- PII detection and handling in Document Processor
- API key management for external services
- Audit logging for all operations

### 3.7 Testing Philosophy

**Levels**:
1. **Unit Tests**: Individual sub-components
2. **Integration Tests**: Component interactions
3. **End-to-End Tests**: Complete workflows
4. **Performance Tests**: Load and stress testing

**Coverage Target**: >90% for critical paths

---

## 4. Global Code Organization

### 4.1 Project Structure

```
rag-portfolio/
├── src/
│   ├── core/              # Core interfaces and orchestrator
│   ├── components/        # Component implementations
│   ├── shared_utils/      # Shared utilities
│   └── config/           # Configuration management
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── configs/              # Configuration files
└── docs/                # Architecture documentation
```

### 4.2 Module Organization

**Principle**: Components are self-contained modules
- Public interfaces in `__init__.py`
- Sub-components in subdirectories
- Adapters separate from implementations

### 4.3 Naming Conventions

- **Interfaces**: Abstract prefix or suffix (e.g., `AbstractRetriever`, `EmbedderInterface`)
- **Implementations**: Descriptive names (e.g., `SentenceTransformerEmbedder`)
- **Adapters**: Provider + Adapter suffix (e.g., `OpenAIAdapter`)

### 4.4 Dependency Management

- **Core → Components**: One-way dependency
- **No circular dependencies** between components
- **Shared utilities** for common functionality

---

## 5. Data Models & Types

**Reference**: [Core Data Types](./rag-interface-reference.md#1-core-data-types)

Key types:
- `Document` - Fundamental content unit
- `RetrievalResult` - Search results
- `Answer` - Generated responses
- `ComponentConfig` - Configuration structure

---

## 6. Integration Patterns

### 6.1 Component Communication

**Pattern**: Direct method calls with clear contracts
- Synchronous communication for main flow
- Async options for parallel processing

### 6.2 Event Flow

1. **Document Processing**: File → Processor → Embedder → Retriever
2. **Query Processing**: Query → Analyzer → Retriever → Generator → Response

### 6.3 Data Flow

**See**: [Data Flow Diagrams](./rag-component-architectures.md#7-data-flow-between-components)

---

## 7. Deployment & Operations

### 7.1 Deployment Architectures

**Local Development**:
- All components in single process
- Local Ollama for LLM
- FAISS for vector storage

**Production**:
- Containerized components
- Load balancer for API gateway
- Managed services for vector DB and LLM

### 7.2 Scaling Strategies

**Horizontal Scaling**:
- Stateless components (Processor, Embedder)
- Shared storage for vectors

**Vertical Scaling**:
- GPU for embeddings and LLM
- Memory for vector indices

### 7.3 Operational Procedures

- **Deployment**: Blue-green with health checks
- **Monitoring**: Prometheus + Grafana
- **Backup**: Vector indices and configurations
- **Disaster Recovery**: Multi-region capabilities

---

## References

- [Component Architecture Diagrams](./rag-component-architectures.md)
- [Interface Specifications](./rag-interface-reference.md)
- [Sequence Diagrams](./rag-main-sequences.md)
- [Adapter Pattern Analysis](./rag-adapter-pattern-analysis.md)