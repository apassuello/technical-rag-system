# RAG System - Complete Interface Reference Guide

## Quick Navigation

1. [Core Data Types](#1-core-data-types)
2. [Main Component Interfaces](#2-main-component-interfaces)
3. [Sub-Component Interfaces](#3-sub-component-interfaces)
4. [Configuration Schemas](#4-configuration-schemas)
5. [Implementation Examples](#5-implementation-examples)

---

## 1. Core Data Types

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Iterator
from abc import ABC, abstractmethod
import numpy as np
from pathlib import Path

# --- Universal Data Types ---

@dataclass
class Document:
    """Fundamental unit of content"""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

@dataclass
class Chunk:
    """Text chunk with position info"""
    content: str
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RetrievalResult:
    """Result from retrieval operations"""
    document: Document
    score: float
    retrieval_method: str  # "dense", "sparse", "hybrid"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Answer:
    """Generated response with metadata"""
    text: str
    sources: List[Document]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Citation:
    """Citation reference"""
    chunk_id: str
    text: str
    score: float
    page: Optional[int] = None

# --- Configuration Types ---

@dataclass
class ComponentConfig:
    """Configuration for a component"""
    type: str
    implementation: str
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemConfig:
    """Complete system configuration"""
    document_processor: ComponentConfig
    embedder: ComponentConfig
    retriever: ComponentConfig
    answer_generator: ComponentConfig
    query_processor: ComponentConfig
    monitoring: Dict[str, Any] = field(default_factory=dict)

# --- Operational Types ---

@dataclass
class HealthStatus:
    """Component health status"""
    healthy: bool
    component: str
    message: str
    metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QueryOptions:
    """Query processing options"""
    k: int = 5
    rerank: bool = True
    max_tokens: int = 2048
    temperature: float = 0.7
    stream: bool = False

@dataclass
class ValidationResult:
    """Validation outcome"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
```

---

## 2. Main Component Interfaces

```python
# --- Platform Orchestrator ---

class PlatformOrchestrator:
    """Central system coordinator"""
    
    def __init__(self, config_path: Path) -> None:
        """Initialize with configuration file"""
        
    def process_document(self, file_path: Path) -> int:
        """Process and index a document"""
        
    def process_query(self, query: str, k: int = 5) -> Answer:
        """Process user query and return answer"""
        
    def get_system_health(self) -> Dict[str, HealthStatus]:
        """Get health status of all components"""
        
    def get_deployment_readiness(self) -> Dict[str, Any]:
        """Assess production readiness"""

# --- Document Processor ---

class DocumentProcessor(ABC):
    """Transform raw documents into searchable chunks"""
    
    @abstractmethod
    def process(self, file_path: Path) -> List[Document]:
        """Process document into chunks"""
        
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Return supported file extensions"""
        
    @abstractmethod
    def validate_document(self, file_path: Path) -> ValidationResult:
        """Validate document before processing"""

# --- Embedder ---

class Embedder(ABC):
    """Convert text into vector representations"""
    
    @abstractmethod
    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts"""
        
    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for single query"""
        
    @abstractmethod
    def get_dimension(self) -> int:
        """Return embedding dimension"""
        
    @abstractmethod
    def batch_embed(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Batch process embeddings"""

# --- Retriever ---

class Retriever(ABC):
    """Information storage and retrieval"""
    
    @abstractmethod
    def retrieve(self, query: str, k: int = 5) -> List[RetrievalResult]:
        """Retrieve relevant documents"""
        
    @abstractmethod
    def index_documents(self, documents: List[Document]) -> None:
        """Index new documents"""
        
    @abstractmethod
    def delete_documents(self, doc_ids: List[str]) -> int:
        """Delete documents by ID"""
        
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics"""

# --- Answer Generator ---

class AnswerGenerator(ABC):
    """Generate contextual answers"""
    
    @abstractmethod
    def generate(self, query: str, context: List[Document]) -> Answer:
        """Generate answer from query and context"""
        
    @abstractmethod
    def generate_streaming(self, query: str, context: List[Document]) -> Iterator[str]:
        """Stream answer generation"""
        
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""

# --- Query Processor ---

class QueryProcessor:
    """Handle query execution workflow"""
    
    def __init__(self, retriever: Retriever, generator: AnswerGenerator) -> None:
        """Initialize with dependencies"""
        
    def process(self, query: str, options: QueryOptions) -> Answer:
        """Process query end-to-end"""
        
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query characteristics"""
```

---

## 3. Sub-Component Interfaces

### 3.1 Document Processing Sub-Components

```python
# --- Document Parser ---

class DocumentParser(ABC):
    """Extract text and structure from documents"""
    
    @abstractmethod
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse document and extract content"""
        
    @abstractmethod
    def extract_metadata(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Extract document metadata"""
        
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Return supported formats"""

# --- Text Chunker ---

class TextChunker(ABC):
    """Split documents into semantic chunks"""
    
    @abstractmethod
    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """Split text into chunks"""
        
    @abstractmethod
    def get_chunk_strategy(self) -> str:
        """Return chunking strategy name"""

# --- Content Cleaner ---

class ContentCleaner(ABC):
    """Clean and normalize document content"""
    
    @abstractmethod
    def clean(self, text: str) -> str:
        """Clean text content"""
        
    @abstractmethod
    def remove_pii(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Remove PII and return entities found"""
        
    @abstractmethod
    def normalize(self, text: str) -> str:
        """Normalize text formatting"""
```

### 3.2 Embedding Sub-Components

```python
# --- Embedding Model ---

class EmbeddingModel(ABC):
    """Core embedding generation"""
    
    @abstractmethod
    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts to embeddings"""
        
    @abstractmethod
    def get_model_name(self) -> str:
        """Return model identifier"""
        
    @abstractmethod
    def get_embedding_dim(self) -> int:
        """Return embedding dimension"""

# --- Batch Processor ---

class BatchProcessor(ABC):
    """Optimize batch processing"""
    
    @abstractmethod
    def process_batch(self, texts: List[str], batch_size: int) -> np.ndarray:
        """Process texts in batches"""
        
    @abstractmethod
    def optimize_batch_size(self, sample_texts: List[str]) -> int:
        """Determine optimal batch size"""

# --- Embedding Cache ---

class EmbeddingCache(ABC):
    """Cache computed embeddings"""
    
    @abstractmethod
    def get(self, text: str) -> Optional[np.ndarray]:
        """Retrieve cached embedding"""
        
    @abstractmethod
    def put(self, text: str, embedding: np.ndarray) -> None:
        """Store embedding in cache"""
        
    @abstractmethod
    def invalidate(self, pattern: str) -> int:
        """Invalidate cache entries"""
```

### 3.3 Retrieval Sub-Components

```python
# --- Vector Index ---

class VectorIndex(ABC):
    """Store and search vector embeddings"""
    
    @abstractmethod
    def add(self, vectors: np.ndarray, ids: List[str]) -> None:
        """Add vectors to index"""
        
    @abstractmethod
    def search(self, query_vector: np.ndarray, k: int) -> List[Tuple[str, float]]:
        """Search for similar vectors"""
        
    @abstractmethod
    def delete(self, ids: List[str]) -> int:
        """Delete vectors by ID"""

# --- Sparse Retriever ---

class SparseRetriever(ABC):
    """Keyword-based retrieval"""
    
    @abstractmethod
    def index(self, documents: List[Document]) -> None:
        """Index documents for sparse retrieval"""
        
    @abstractmethod
    def search(self, query: str, k: int) -> List[Tuple[str, float]]:
        """Search using sparse methods"""

# --- Fusion Strategy ---

class FusionStrategy(ABC):
    """Combine multiple retrieval results"""
    
    @abstractmethod
    def fuse(self, results_lists: List[List[Tuple[str, float]]]) -> List[Tuple[str, float]]:
        """Fuse multiple result lists"""
        
    @abstractmethod
    def get_weights(self) -> Dict[str, float]:
        """Return fusion weights"""

# --- Reranker ---

class Reranker(ABC):
    """Rerank retrieval results"""
    
    @abstractmethod
    def rerank(self, query: str, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Rerank results for query"""
        
    @abstractmethod
    def get_reranker_type(self) -> str:
        """Return reranker type"""
```

### 3.4 Generation Sub-Components

```python
# --- Prompt Builder ---

class PromptBuilder(ABC):
    """Construct prompts for LLMs"""
    
    @abstractmethod
    def build_prompt(self, query: str, context: List[Document]) -> str:
        """Build prompt from query and context"""
        
    @abstractmethod
    def get_template(self) -> str:
        """Return prompt template"""

# --- LLM Client ---

class LLMClient(ABC):
    """Interface to language models"""
    
    @abstractmethod
    def generate(self, prompt: str, params: Dict[str, Any]) -> str:
        """Generate response from prompt"""
        
    @abstractmethod
    def generate_streaming(self, prompt: str, params: Dict[str, Any]) -> Iterator[str]:
        """Stream response generation"""
        
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Return model information"""

# --- Response Parser ---

class ResponseParser(ABC):
    """Parse and structure LLM responses"""
    
    @abstractmethod
    def parse(self, raw_response: str) -> Dict[str, Any]:
        """Parse raw response"""
        
    @abstractmethod
    def extract_citations(self, response: Dict[str, Any]) -> List[Citation]:
        """Extract citations from response"""

# --- Confidence Scorer ---

class ConfidenceScorer(ABC):
    """Score answer confidence"""
    
    @abstractmethod
    def score(self, query: str, answer: str, context: List[Document]) -> float:
        """Calculate confidence score"""
        
    @abstractmethod
    def get_scoring_method(self) -> str:
        """Return scoring method name"""
```

---

## 4. Configuration Schemas

```yaml
# Complete System Configuration Schema

system:
  name: "technical-docs-rag"
  version: "1.0.0"
  environment: "production"  # development, staging, production

# Document Processor Configuration
document_processor:
  type: "modular"
  
  parser:
    implementation: "pymupdf"  # pymupdf, pdfplumber, tika
    config:
      extract_images: false
      preserve_layout: true
      max_file_size_mb: 100
      
  chunker:
    implementation: "sentence_boundary"  # sentence_boundary, semantic, structural, fixed_size
    config:
      chunk_size: 1000
      chunk_overlap: 200
      min_chunk_size: 100
      preserve_sentences: true
      
  cleaner:
    implementation: "technical"  # technical, language, pii
    config:
      remove_code_artifacts: true
      normalize_terms: true
      detect_pii: true
      pii_action: "redact"  # redact, remove, flag

# Embedder Configuration
embedder:
  type: "modular"
  
  model:
    implementation: "sentence_transformer"  # sentence_transformer, openai, custom, multilingual
    config:
      model_name: "all-MiniLM-L6-v2"
      device: "mps"  # cpu, cuda, mps
      
  batch_processor:
    implementation: "dynamic"  # dynamic, streaming, parallel
    config:
      initial_batch_size: 32
      max_batch_size: 128
      optimize_for_memory: true
      
  cache:
    implementation: "redis"  # memory, redis, disk
    config:
      host: "localhost"
      port: 6379
      ttl_seconds: 3600
      max_entries: 10000

# Retriever Configuration
retriever:
  type: "unified_modular"
  
  vector_index:
    implementation: "faiss"  # faiss, hnsw, annoy, pinecone
    config:
      index_type: "IndexFlatIP"
      dimension: 384
      metric: "cosine"
      
  sparse_retriever:
    implementation: "bm25"  # bm25, tfidf, elasticsearch
    config:
      k1: 1.2
      b: 0.75
      
  fusion_strategy:
    implementation: "rrf"  # rrf, weighted, ml_fusion
    config:
      k: 60
      weights:
        dense: 0.7
        sparse: 0.3
        
  reranker:
    implementation: "cross_encoder"  # cross_encoder, colbert, llm_reranker
    config:
      model_name: "cross-encoder/ms-marco-MiniLM-L-6-v2"
      batch_size: 16

# Answer Generator Configuration
answer_generator:
  type: "adaptive_modular"
  
  prompt_builder:
    implementation: "adaptive"  # simple, chain_of_thought, few_shot, adaptive
    config:
      max_context_tokens: 2048
      include_metadata: true
      
  llm_client:
    implementation: "ollama"  # ollama, openai, huggingface, custom
    config:
      model: "llama3.2"
      temperature: 0.7
      max_tokens: 512
      
  response_parser:
    implementation: "markdown"  # markdown, json, citation
    config:
      extract_citations: true
      validate_format: true
      
  confidence_scorer:
    implementation: "ensemble"  # perplexity, semantic, coverage, ensemble
    config:
      methods:
        - perplexity: 0.3
        - semantic: 0.4
        - coverage: 0.3

# Query Processor Configuration
query_processor:
  type: "modular"
  
  query_analyzer:
    implementation: "nlp"  # nlp, llm, rule_based
    config:
      model: "en_core_web_sm"
      extract_entities: true
      
  context_selector:
    implementation: "mmr"  # mmr, diversity, token_limit
    config:
      lambda_param: 0.5
      max_tokens: 2048
      
  response_assembler:
    implementation: "rich"  # standard, rich, streaming
    config:
      include_sources: true
      format_citations: true

# Monitoring Configuration
monitoring:
  collector:
    implementation: "prometheus"  # prometheus, cloudwatch, custom
    config:
      port: 9090
      scrape_interval: 30
      
  health_checks:
    enabled: true
    interval: 60
    timeout: 10
    
  alerts:
    enabled: true
    channels:
      - email
      - slack
```

---

## 5. Implementation Examples

### 5.1 Custom Document Parser Implementation

```python
class TechnicalPDFParser(DocumentParser):
    """PDF parser optimized for technical documentation"""
    
    def __init__(self, preserve_equations: bool = True, extract_diagrams: bool = False):
        self.preserve_equations = preserve_equations
        self.extract_diagrams = extract_diagrams
        self._init_parser()
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse technical PDF with special handling for equations and code"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            parsed_content = {
                'text': '',
                'metadata': {},
                'sections': [],
                'equations': [],
                'code_blocks': []
            }
            
            for page_num, page in enumerate(doc):
                # Extract text with layout preservation
                text = page.get_text("text")
                parsed_content['text'] += text
                
                # Extract metadata
                if page_num == 0:
                    parsed_content['metadata'] = self.extract_metadata(doc)
                
                # Find equations if enabled
                if self.preserve_equations:
                    equations = self._extract_equations(page)
                    parsed_content['equations'].extend(equations)
                
                # Extract code blocks
                code_blocks = self._extract_code_blocks(text)
                parsed_content['code_blocks'].extend(code_blocks)
            
            doc.close()
            return parsed_content
            
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")
    
    def extract_metadata(self, document: Any) -> Dict[str, Any]:
        """Extract PDF metadata"""
        metadata = document.metadata
        return {
            'title': metadata.get('title', ''),
            'author': metadata.get('author', ''),
            'subject': metadata.get('subject', ''),
            'pages': document.page_count,
            'creation_date': metadata.get('creationDate', ''),
            'format': 'PDF',
            'producer': metadata.get('producer', '')
        }
    
    def supported_formats(self) -> List[str]:
        """Return supported formats"""
        return ['.pdf']
    
    def _extract_equations(self, page) -> List[Dict[str, Any]]:
        """Extract mathematical equations"""
        # Implementation for equation extraction
        pass
    
    def _extract_code_blocks(self, text: str) -> List[Dict[str, Any]]:
        """Extract code blocks from text"""
        # Implementation for code block extraction
        pass
```

### 5.2 Custom Reranker Implementation

```python
class DomainAwareReranker(Reranker):
    """Reranker with domain-specific knowledge"""
    
    def __init__(self, domain_terms: List[str], boost_factor: float = 1.5):
        self.domain_terms = set(term.lower() for term in domain_terms)
        self.boost_factor = boost_factor
        self._load_models()
    
    def rerank(self, query: str, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Rerank with domain awareness"""
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        reranked_results = []
        
        for result in results:
            # Calculate domain relevance
            doc_text_lower = result.document.content.lower()
            domain_score = self._calculate_domain_score(doc_text_lower, query_terms)
            
            # Cross-encoder scoring
            cross_score = self._cross_encode(query, result.document.content)
            
            # Combine scores
            final_score = (0.6 * cross_score + 0.4 * domain_score) * result.score
            
            # Apply domain boost if applicable
            if any(term in doc_text_lower for term in self.domain_terms):
                final_score *= self.boost_factor
            
            reranked_results.append(
                RetrievalResult(
                    document=result.document,
                    score=final_score,
                    retrieval_method=f"reranked_{result.retrieval_method}",
                    metadata={
                        **result.metadata,
                        'domain_score': domain_score,
                        'cross_score': cross_score,
                        'original_score': result.score
                    }
                )
            )
        
        # Sort by final score
        reranked_results.sort(key=lambda x: x.score, reverse=True)
        return reranked_results
    
    def get_reranker_type(self) -> str:
        """Return reranker type"""
        return "domain_aware_cross_encoder"
    
    def _calculate_domain_score(self, text: str, query_terms: Set[str]) -> float:
        """Calculate domain-specific relevance score"""
        # Implementation for domain scoring
        pass
    
    def _cross_encode(self, query: str, document: str) -> float:
        """Cross-encode query and document"""
        # Implementation for cross-encoding
        pass
```

### 5.3 Factory Usage Example

```python
def create_rag_system(config_path: Path) -> PlatformOrchestrator:
    """Create RAG system with custom components"""
    
    # Load configuration
    config = load_config(config_path)
    
    # Create orchestrator (handles all sub-component creation)
    orchestrator = PlatformOrchestrator(config_path)
    
    # System is ready to use
    return orchestrator

# Usage
orchestrator = create_rag_system(Path("config.yaml"))

# Process documents
doc_id = orchestrator.process_document(Path("technical_manual.pdf"))

# Query the system
answer = orchestrator.process_query(
    "How do I configure the RISC-V interrupt controller?",
    k=5
)

print(f"Answer: {answer.text}")
print(f"Confidence: {answer.confidence}")
print(f"Sources: {len(answer.sources)}")
```

---

## Interface Design Principles Summary

1. **Consistency**: All sub-components of the same type share identical interfaces
2. **Flexibility**: Multiple implementations available for different use cases
3. **Testability**: Every interface designed for easy mocking and testing
4. **Observability**: Built-in metrics and health checks in all components
5. **Configuration**: Behavior controlled through YAML, not code changes
6. **Extensibility**: New implementations can be added without changing interfaces
7. **Error Handling**: Comprehensive validation and error reporting
8. **Performance**: Interfaces support batching, caching, and optimization

This reference guide provides the complete blueprint for implementing a production-grade RAG system with modular sub-components following enterprise architecture standards.