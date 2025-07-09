# RAG System - Sub-Component Interaction Diagrams

## 1. Document Processing Sub-Component Interactions

### 1.1 PDF Processing Flow

```mermaid
sequenceDiagram
    participant DP as Document Processor
    participant FD as Format Detector
    participant PDF as PDF Parser
    participant Meta as Metadata Extractor
    participant SBC as Sentence Boundary Chunker
    participant TC as Technical Cleaner
    participant Val as Output Validator

    DP->>FD: detect_format(file_path)
    FD->>FD: check_magic_bytes()
    FD->>FD: verify_extension()
    FD-->>DP: format="PDF"
    
    DP->>PDF: parse(file_path)
    
    rect rgb(245, 255, 245)
        Note over PDF,Meta: PDF Parsing
        PDF->>PDF: initialize_pymupdf()
        PDF->>PDF: extract_pages()
        
        loop For each page
            PDF->>PDF: extract_text()
            PDF->>PDF: preserve_layout()
            PDF->>Meta: extract_page_metadata()
            Meta-->>PDF: metadata
        end
        
        PDF->>PDF: extract_toc()
        PDF->>PDF: build_structure()
        PDF-->>DP: ParsedDocument
    end
    
    rect rgb(255, 245, 245)
        Note over DP,SBC: Chunking Strategy
        DP->>SBC: chunk(text, metadata)
        SBC->>SBC: sentence_tokenize()
        SBC->>SBC: calculate_similarities()
        
        loop Until all text processed
            SBC->>SBC: group_sentences()
            SBC->>SBC: check_chunk_size()
            SBC->>SBC: ensure_overlap()
            SBC->>SBC: preserve_boundaries()
        end
        
        SBC-->>DP: List[Chunk]
    end
    
    rect rgb(245, 245, 255)
        Note over DP,TC: Content Cleaning
        DP->>TC: clean(chunks)
        
        loop For each chunk
            TC->>TC: normalize_whitespace()
            TC->>TC: fix_encoding_issues()
            TC->>TC: remove_artifacts()
            TC->>TC: standardize_terms()
        end
        
        TC-->>DP: List[CleanChunk]
    end
    
    DP->>Val: validate_output(chunks)
    Val->>Val: check_completeness()
    Val->>Val: verify_metadata()
    Val-->>DP: validation_result
```

### 1.2 Semantic Chunking Strategy

```mermaid
flowchart TB
    subgraph "Semantic Chunking Process"
        Input[Raw Text]
        
        subgraph "Sentence Processing"
            ST[Sentence Tokenizer]
            SE[Sentence Embedder]
            SV[(Sentence Vectors)]
        end
        
        subgraph "Similarity Analysis"
            SC[Similarity Calculator]
            TH[Threshold Detector]
            BP[Boundary Predictor]
        end
        
        subgraph "Chunk Formation"
            CG[Chunk Generator]
            CO[Overlap Manager]
            CS[Size Controller]
        end
        
        Output[Semantic Chunks]
        
        Input --> ST
        ST --> SE
        SE --> SV
        SV --> SC
        SC --> TH
        TH --> BP
        BP --> CG
        CG --> CO
        CO --> CS
        CS --> Output
    end
    
    style Input fill:#3498db,color:#fff
    style Output fill:#2ecc71,color:#fff
```

## 2. Embedding Generation Sub-Component Interactions

### 2.1 Batch Processing with Caching

```mermaid
sequenceDiagram
    participant EMB as Embedder
    participant Cache as Embedding Cache
    participant BO as Batch Optimizer
    participant BP as Batch Processor
    participant Model as SBERT Model
    participant GPU as GPU/MPS

    EMB->>EMB: receive_documents(docs)
    
    rect rgb(245, 255, 245)
        Note over EMB,Cache: Cache Lookup Phase
        loop For each document
            EMB->>Cache: get(doc.content_hash)
            alt Cache Hit
                Cache-->>EMB: cached_embedding
                EMB->>EMB: mark_as_cached(doc)
            else Cache Miss
                EMB->>EMB: add_to_batch(doc)
            end
        end
    end
    
    rect rgb(255, 245, 245)
        Note over EMB,GPU: Batch Optimization
        EMB->>BO: optimize_batch_size(texts)
        BO->>GPU: check_available_memory()
        GPU-->>BO: memory_stats
        BO->>BO: calculate_optimal_size()
        BO-->>EMB: batch_size=32
        
        EMB->>BP: process_batch(texts, batch_size)
        
        loop For each batch
            BP->>Model: encode(batch_texts)
            Model->>Model: tokenize()
            Model->>GPU: transfer_to_device()
            GPU->>GPU: parallel_compute()
            GPU-->>Model: embeddings
            Model-->>BP: batch_embeddings
            
            BP->>Cache: put_batch(texts, embeddings)
        end
        
        BP-->>EMB: all_embeddings
    end
```

### 2.2 Multi-Model Embedding Strategy

```mermaid
flowchart LR
    subgraph "Input"
        Text[Text Input]
    end
    
    subgraph "Model Selection"
        MS[Model Selector]
        Lang[Language Detector]
        Dom[Domain Classifier]
    end
    
    subgraph "Embedding Models"
        direction TB
        SBERT[SBERT<br/>General Purpose]
        Multi[Multilingual<br/>XLM-RoBERTa]
        Tech[Technical<br/>SciBERT]
        Custom[Custom<br/>Fine-tuned]
    end
    
    subgraph "Processing"
        Cache[Cache Layer]
        Batch[Batch Processor]
        Norm[Normalizer]
    end
    
    subgraph "Output"
        Emb[Embeddings]
    end
    
    Text --> MS
    MS --> Lang & Dom
    Lang --> Multi
    Dom --> Tech
    MS --> SBERT
    MS --> Custom
    
    SBERT & Multi & Tech & Custom --> Cache
    Cache --> Batch
    Batch --> Norm
    Norm --> Emb
    
    style Text fill:#3498db,color:#fff
    style Emb fill:#2ecc71,color:#fff
```

## 3. Retrieval Sub-Component Interactions

### 3.1 Hybrid Retrieval with Fusion

```mermaid
sequenceDiagram
    participant QE as Query Engine
    participant EMB as Query Embedder
    participant VIdx as Vector Index
    participant Sparse as BM25 Retriever
    participant RRF as RRF Fusion
    participant Rerank as CrossEncoder

    QE->>QE: receive_query(text, k=5)
    
    par Parallel Retrieval
        QE->>EMB: embed_query(text)
        EMB-->>QE: query_vector
        QE->>VIdx: search(query_vector, k*2)
        
        rect rgb(245, 255, 245)
            Note over VIdx: Dense Retrieval
            VIdx->>VIdx: normalize_vector()
            VIdx->>VIdx: search_index()
            VIdx->>VIdx: get_top_k()
            VIdx-->>QE: dense_results
        end
    and
        QE->>Sparse: search(text, k*2)
        
        rect rgb(255, 245, 245)
            Note over Sparse: Sparse Retrieval
            Sparse->>Sparse: tokenize_query()
            Sparse->>Sparse: compute_bm25()
            Sparse->>Sparse: rank_documents()
            Sparse-->>QE: sparse_results
        end
    end
    
    rect rgb(245, 245, 255)
        Note over QE,Rerank: Fusion & Reranking
        QE->>RRF: fuse(dense_results, sparse_results)
        RRF->>RRF: assign_reciprocal_ranks()
        RRF->>RRF: combine_scores()
        RRF->>RRF: normalize_scores()
        RRF-->>QE: fused_results
        
        QE->>Rerank: rerank(query, fused_results)
        loop For each result
            Rerank->>Rerank: encode_pair(query, doc)
            Rerank->>Rerank: compute_relevance()
        end
        Rerank->>Rerank: sort_by_score()
        Rerank-->>QE: final_results
    end
```

### 3.2 Vector Index Selection Strategy

```mermaid
flowchart TB
    subgraph "Index Selection Logic"
        Start[Query + Dataset Info]
        
        Size{Dataset Size?}
        Acc{Accuracy Need?}
        Speed{Speed Priority?}
        
        FAISS[FAISS<br/>IndexFlatIP<br/>Exact Search]
        HNSW[HNSW<br/>Approximate<br/>Fast]
        Annoy[Annoy<br/>Memory Efficient]
        Pine[Pinecone<br/>Managed Cloud]
        
        Start --> Size
        Size -->|< 100K| Acc
        Size -->|> 1M| Speed
        Size -->|100K-1M| HNSW
        
        Acc -->|High| FAISS
        Acc -->|Medium| HNSW
        
        Speed -->|Critical| Annoy
        Speed -->|Flexible| Pine
    end
    
    style Start fill:#3498db,color:#fff
    style FAISS fill:#2ecc71,color:#fff
    style HNSW fill:#f39c12,color:#fff
    style Annoy fill:#e74c3c,color:#fff
    style Pine fill:#9b59b6,color:#fff
```

## 4. Answer Generation Sub-Component Interactions

### 4.1 Adaptive Prompt Building

```mermaid
sequenceDiagram
    participant AG as Answer Generator
    participant QC as Query Classifier
    participant PB as Prompt Builder
    participant TS as Template Selector
    participant CF as Context Formatter
    participant LLM as LLM Client

    AG->>QC: classify_query(query)
    QC->>QC: analyze_complexity()
    QC->>QC: detect_intent()
    QC-->>AG: query_type="technical_explanation"
    
    AG->>PB: build_prompt(query, context, query_type)
    
    rect rgb(245, 255, 245)
        Note over PB,CF: Prompt Construction
        PB->>TS: select_template(query_type)
        TS->>TS: load_template_library()
        TS->>TS: match_best_template()
        TS-->>PB: template="chain_of_thought"
        
        PB->>CF: format_context(documents)
        CF->>CF: rank_by_relevance()
        CF->>CF: trim_to_token_limit()
        CF->>CF: add_citations()
        CF-->>PB: formatted_context
        
        PB->>PB: inject_variables()
        PB->>PB: add_instructions()
        PB->>PB: optimize_token_usage()
        PB-->>AG: final_prompt
    end
    
    AG->>LLM: generate(final_prompt)
```

### 4.2 LLM Adapter Pattern Flow

```mermaid
flowchart TB
    subgraph "Unified Interface"
        AG[Answer Generator]
        UI[generate method]
    end
    
    subgraph "Adapter Layer"
        direction LR
        
        subgraph "Ollama Adapter"
            OA[Ollama Adapter]
            OT[Transform to<br/>Ollama Format]
            OC[Ollama Client]
            OR[Parse Ollama<br/>Response]
        end
        
        subgraph "OpenAI Adapter"
            OAA[OpenAI Adapter]
            OAT[Transform to<br/>OpenAI Format]
            OAC[OpenAI Client]
            OAR[Parse OpenAI<br/>Response]
        end
        
        subgraph "HF Adapter"
            HFA[HF Adapter]
            HFT[Transform to<br/>HF Format]
            HFC[HF Client]
            HFR[Parse HF<br/>Response]
        end
    end
    
    subgraph "Common Output"
        Answer[Answer Object]
        Citations[Citations]
        Confidence[Confidence Score]
    end
    
    AG --> UI
    UI --> OA & OAA & HFA
    
    OA --> OT --> OC --> OR
    OAA --> OAT --> OAC --> OAR
    HFA --> HFT --> HFC --> HFR
    
    OR & OAR & HFR --> Answer
    Answer --> Citations & Confidence
    
    style AG fill:#1abc9c,color:#fff
    style Answer fill:#2ecc71,color:#fff
```

## 5. Monitoring & Health Check Interactions

### 5.1 Component Health Monitoring

```mermaid
sequenceDiagram
    participant MC as Monitoring Collector
    participant HM as Health Monitor
    participant Comp as Component
    participant Cache as Metric Cache
    participant Alert as Alert Manager
    participant Dash as Dashboard

    loop Every 30 seconds
        MC->>HM: check_health()
        
        par Parallel Health Checks
            HM->>Comp: get_health_status()
            Comp->>Comp: check_internal_state()
            Comp->>Comp: verify_dependencies()
            Comp->>Comp: test_functionality()
            Comp-->>HM: health_status
        and
            HM->>Comp: get_metrics()
            Comp->>Comp: calculate_metrics()
            Comp-->>HM: current_metrics
        end
        
        HM->>Cache: store_metrics(metrics)
        
        alt Unhealthy Status
            HM->>Alert: trigger_alert(component, issue)
            Alert->>Alert: check_severity()
            Alert->>Alert: notify_channels()
        end
        
        HM->>Dash: update_dashboard(health_data)
    end
```

### 5.2 Performance Optimization Flow

```mermaid
flowchart TB
    subgraph "Monitoring Layer"
        Met[Metrics Collector]
        Perf[Performance Analyzer]
        Opt[Optimizer]
    end
    
    subgraph "Analysis"
        Bottle[Bottleneck Detector]
        Trend[Trend Analyzer]
        Pred[Predictor]
    end
    
    subgraph "Optimization Actions"
        Cache[Adjust Cache Size]
        Batch[Optimize Batch Size]
        Index[Reindex Data]
        Model[Switch Model]
    end
    
    subgraph "Validation"
        Test[A/B Testing]
        Valid[Validation]
        Deploy[Deployment]
    end
    
    Met --> Perf
    Perf --> Bottle & Trend & Pred
    Bottle & Trend & Pred --> Opt
    Opt --> Cache & Batch & Index & Model
    Cache & Batch & Index & Model --> Test
    Test --> Valid
    Valid --> Deploy
    
    style Met fill:#3498db,color:#fff
    style Opt fill:#e74c3c,color:#fff
    style Deploy fill:#2ecc71,color:#fff
```

## 6. Configuration Management Flow

```mermaid
sequenceDiagram
    participant Admin as Admin
    participant CM as Config Manager
    participant YCM as YAML Config
    participant ECM as Env Config
    participant CV as Config Validator
    participant Comp as Components

    Admin->>CM: update_config(changes)
    
    rect rgb(245, 255, 245)
        Note over CM,CV: Configuration Loading
        CM->>YCM: load_base_config()
        YCM->>YCM: parse_yaml()
        YCM-->>CM: base_config
        
        CM->>ECM: load_env_overrides()
        ECM->>ECM: scan_env_vars()
        ECM-->>CM: env_config
        
        CM->>CM: merge_configs(base, env)
        CM->>CV: validate(merged_config)
        
        CV->>CV: check_required_fields()
        CV->>CV: validate_types()
        CV->>CV: verify_constraints()
        CV-->>CM: validation_result
    end
    
    alt Valid Configuration
        CM->>Comp: apply_config(validated_config)
        Comp->>Comp: update_settings()
        Comp-->>CM: success
    else Invalid Configuration
        CM-->>Admin: validation_errors
    end
```