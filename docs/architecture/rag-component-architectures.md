# RAG System - Component Architecture Block Diagrams

## 1. Platform Orchestrator Architecture

```mermaid
graph TB
    subgraph "Platform Orchestrator"
        direction TB
        
        subgraph "Core"
            PO[Platform Orchestrator Core]
            API[API Gateway]
            Router[Request Router]
        end
        
        subgraph "Configuration Manager"
            CM[Config Manager Interface]
            YCM[YAML Config Manager]
            ECM[Environment Config Manager]
            RCM[Remote Config Manager]
            CV[Config Validator]
        end
        
        subgraph "Lifecycle Manager"
            LM[Lifecycle Manager Interface]
            SLM[Sequential Lifecycle]
            PLM[Parallel Lifecycle]
            RLM[Resilient Lifecycle]
            DG[Dependency Graph]
        end
        
        subgraph "Monitoring Collector"
            MC[Monitoring Interface]
            PMC[Prometheus Collector]
            CWC[CloudWatch Collector]
            CMC[Custom Collector]
            MA[Metric Aggregator]
        end
        
        API --> Router
        Router --> PO
        
        PO --> CM
        CM --> YCM & ECM & RCM
        YCM & ECM & RCM --> CV
        
        PO --> LM
        LM --> SLM & PLM & RLM
        SLM & PLM & RLM --> DG
        
        PO --> MC
        MC --> PMC & CWC & CMC
        PMC & CWC & CMC --> MA
    end
    
    style PO fill:#e74c3c,color:#fff
    style CM fill:#3498db,color:#fff
    style LM fill:#2ecc71,color:#fff
    style MC fill:#f39c12,color:#fff
```

## 2. Document Processor Architecture

```mermaid
graph TB
    subgraph "Document Processor"
        direction TB
        
        subgraph "Core"
            DP[Document Processor Core]
            Pipeline[Processing Pipeline]
            Validator[Output Validator]
        end
        
        subgraph "Document Parser"
            Parser[Parser Interface]
            PDF[PDF Parser<br/>PyMuPDF]
            DOCX[DOCX Parser<br/>python-docx]
            HTML[HTML Parser<br/>BeautifulSoup]
            MD[Markdown Parser<br/>CommonMark]
            FD[Format Detector]
        end
        
        subgraph "Text Chunker"
            Chunker[Chunker Interface]
            SBC[Sentence Boundary<br/>Chunker]
            SC[Semantic<br/>Chunker]
            STC[Structural<br/>Chunker]
            FSC[Fixed Size<br/>Chunker]
            CS[Chunk Strategies]
        end
        
        subgraph "Content Cleaner"
            Cleaner[Cleaner Interface]
            TC[Technical<br/>Cleaner]
            LC[Language<br/>Cleaner]
            PC[PII<br/>Cleaner]
            CN[Content Normalizer]
        end
        
        DP --> Pipeline
        Pipeline --> FD
        FD --> Parser
        Parser --> PDF & DOCX & HTML & MD
        
        Pipeline --> Chunker
        Chunker --> SBC & SC & STC & FSC
        SBC & SC & STC & FSC --> CS
        
        Pipeline --> Cleaner
        Cleaner --> TC & LC & PC
        TC & LC & PC --> CN
        
        Pipeline --> Validator
    end
    
    style DP fill:#2ecc71,color:#fff
    style Parser fill:#3498db,color:#fff
    style Chunker fill:#e74c3c,color:#fff
    style Cleaner fill:#f39c12,color:#fff
```

## 3. Embedder Architecture

```mermaid
graph TB
    subgraph "Embedder Component"
        direction TB
        
        subgraph "Core"
            EMB[Embedder Core]
            Coordinator[Embedding Coordinator]
            QC[Quality Controller]
        end
        
        subgraph "Embedding Model"
            Model[Model Interface]
            SBERT[Sentence<br/>Transformer<br/>all-MiniLM-L6-v2]
            OAI[OpenAI<br/>Embeddings<br/>text-embedding-3]
            Custom[Custom<br/>Fine-tuned<br/>Model]
            Multi[Multilingual<br/>Model<br/>xlm-roberta]
            MLoader[Model Loader]
        end
        
        subgraph "Batch Processor"
            Batch[Batch Interface]
            Dynamic[Dynamic<br/>Batch Processor<br/>GPU Aware]
            Stream[Streaming<br/>Processor<br/>Large Scale]
            Parallel[Parallel<br/>Processor<br/>Multi-GPU]
            BO[Batch Optimizer]
        end
        
        subgraph "Embedding Cache"
            Cache[Cache Interface]
            Mem[In-Memory<br/>Cache<br/>LRU]
            Redis[Redis<br/>Cache<br/>Distributed]
            Disk[Disk<br/>Cache<br/>Persistent]
            CInval[Cache Invalidator]
        end
        
        EMB --> Coordinator
        Coordinator --> QC
        
        Coordinator --> Model
        Model --> SBERT & OAI & Custom & Multi
        SBERT & OAI & Custom & Multi --> MLoader
        
        Coordinator --> Batch
        Batch --> Dynamic & Stream & Parallel
        Dynamic & Stream & Parallel --> BO
        
        Coordinator --> Cache
        Cache --> Mem & Redis & Disk
        Mem & Redis & Disk --> CInval
    end
    
    style EMB fill:#f39c12,color:#fff
    style Model fill:#3498db,color:#fff
    style Batch fill:#2ecc71,color:#fff
    style Cache fill:#e74c3c,color:#fff
```

## 4. Unified Retriever Architecture

```mermaid
graph TB
    subgraph "Unified Retriever"
        direction TB
        
        subgraph "Core"
            RET[Retriever Core]
            QE[Query Engine]
            RO[Result Optimizer]
        end
        
        subgraph "Vector Index"
            VIdx[Vector Index Interface]
            FAISS[FAISS<br/>IndexFlatIP<br/>Exact Search]
            HNSW[HNSW<br/>Graph-based<br/>Approximate]
            Annoy[Annoy<br/>Tree-based<br/>Fast]
            Pine[Pinecone<br/>Managed<br/>Cloud]
            IdxOpt[Index Optimizer]
        end
        
        subgraph "Sparse Retriever"
            Sparse[Sparse Interface]
            BM25[BM25<br/>Okapi<br/>Classic]
            TFIDF[TF-IDF<br/>Traditional<br/>Scoring]
            ES[Elasticsearch<br/>Full-text<br/>Advanced]
            SparseOpt[Sparse Optimizer]
        end
        
        subgraph "Fusion Strategy"
            Fusion[Fusion Interface]
            RRF[RRF<br/>Reciprocal<br/>Rank Fusion]
            WF[Weighted<br/>Fusion<br/>Configurable]
            MLF[ML Fusion<br/>Learned<br/>Ranking]
            FusionCal[Fusion Calibrator]
        end
        
        subgraph "Reranker"
            Rerank[Reranker Interface]
            CE[CrossEncoder<br/>BERT-based<br/>Accurate]
            CB[ColBERT<br/>Late<br/>Interaction]
            LLMR[LLM<br/>Reranker<br/>GPT-based]
            RankEval[Ranking Evaluator]
        end
        
        RET --> QE
        QE --> RO
        
        QE --> VIdx
        VIdx --> FAISS & HNSW & Annoy & Pine
        FAISS & HNSW & Annoy & Pine --> IdxOpt
        
        QE --> Sparse
        Sparse --> BM25 & TFIDF & ES
        BM25 & TFIDF & ES --> SparseOpt
        
        RO --> Fusion
        Fusion --> RRF & WF & MLF
        RRF & WF & MLF --> FusionCal
        
        RO --> Rerank
        Rerank --> CE & CB & LLMR
        CE & CB & LLMR --> RankEval
    end
    
    style RET fill:#3498db,color:#fff
    style VIdx fill:#2ecc71,color:#fff
    style Sparse fill:#f39c12,color:#fff
    style Fusion fill:#e74c3c,color:#fff
    style Rerank fill:#9b59b6,color:#fff
```

## 5. Answer Generator Architecture (Adapter Pattern)

```mermaid
graph TB
    subgraph "Answer Generator"
        direction TB
        
        subgraph "Core Adapter"
            AG[Adaptive Answer Generator<br/>Orchestrator]
            UI[Unified Interface]
            QM[Quality Monitor]
        end
        
        subgraph "Prompt Builder"
            PB[Prompt Builder Interface]
            Simple[Simple<br/>Prompt<br/>Basic Q&A]
            CoT[Chain of<br/>Thought<br/>Reasoning]
            FewShot[Few-Shot<br/>Examples<br/>Learning]
            Adaptive[Adaptive<br/>Dynamic<br/>Selection]
            PT[Prompt Templates]
        end
        
        subgraph "LLM Client Adapters"
            LLM[LLM Client Interface]
            
            subgraph "Ollama Adapter"
                OA[Ollama<br/>Generator]
                OF[Ollama<br/>Formatter]
            end
            
            subgraph "OpenAI Adapter"
                OAI[OpenAI<br/>Generator]
                OAIF[OpenAI<br/>Formatter]
            end
            
            subgraph "HuggingFace Adapter"
                HF[HuggingFace<br/>Generator]
                HFF[HF<br/>Formatter]
            end
            
            subgraph "Custom Adapter"
                CA[Custom<br/>Generator]
                CF[Custom<br/>Formatter]
            end
        end
        
        subgraph "Response Parser"
            RP[Parser Interface]
            MDP[Markdown<br/>Parser<br/>Formatted]
            JP[JSON<br/>Parser<br/>Structured]
            CP[Citation<br/>Parser<br/>References]
            PV[Parse Validator]
        end
        
        subgraph "Confidence Scorer"
            CS[Scorer Interface]
            PS[Perplexity<br/>Scorer<br/>Model-based]
            SS[Semantic<br/>Scorer<br/>Similarity]
            CovS[Coverage<br/>Scorer<br/>Completeness]
            ES[Ensemble<br/>Scorer<br/>Combined]
            SC[Score Calibrator]
        end
        
        AG --> UI
        UI --> QM
        
        AG --> PB
        PB --> Simple & CoT & FewShot & Adaptive
        Simple & CoT & FewShot & Adaptive --> PT
        
        AG --> LLM
        LLM --> OA & OAI & HF & CA
        OA --> OF
        OAI --> OAIF
        HF --> HFF
        CA --> CF
        
        AG --> RP
        RP --> MDP & JP & CP
        MDP & JP & CP --> PV
        
        AG --> CS
        CS --> PS & SS & CovS & ES
        PS & SS & CovS & ES --> SC
    end
    
    style AG fill:#1abc9c,color:#fff
    style PB fill:#3498db,color:#fff
    style LLM fill:#e74c3c,color:#fff
    style RP fill:#f39c12,color:#fff
    style CS fill:#9b59b6,color:#fff
```

## 6. Query Processor Architecture

```mermaid
graph TB
    subgraph "Query Processor"
        direction TB
        
        subgraph "Core"
            QP[Query Processor Core]
            WF[Workflow Engine]
            RM[Result Manager]
        end
        
        subgraph "Query Analyzer"
            QA[Analyzer Interface]
            NLP[NLP<br/>Analyzer<br/>spaCy-based]
            LLMA[LLM<br/>Analyzer<br/>GPT-based]
            Rule[Rule-based<br/>Analyzer<br/>Patterns]
            QC[Query Classifier]
        end
        
        subgraph "Context Selector"
            CS[Selector Interface]
            MMR[MMR<br/>Selector<br/>Diversity]
            Div[Diversity<br/>Selector<br/>Coverage]
            Token[Token Limit<br/>Selector<br/>Optimal]
            CSO[Selection Optimizer]
        end
        
        subgraph "Response Assembler"
            RA[Assembler Interface]
            Std[Standard<br/>Assembler<br/>Basic]
            Rich[Rich<br/>Assembler<br/>Enhanced]
            Stream[Streaming<br/>Assembler<br/>Progressive]
            RF[Response Formatter]
        end
        
        QP --> WF
        WF --> RM
        
        WF --> QA
        QA --> NLP & LLMA & Rule
        NLP & LLMA & Rule --> QC
        
        WF --> CS
        CS --> MMR & Div & Token
        MMR & Div & Token --> CSO
        
        RM --> RA
        RA --> Std & Rich & Stream
        Std & Rich & Stream --> RF
    end
    
    style QP fill:#e74c3c,color:#fff
    style QA fill:#3498db,color:#fff
    style CS fill:#2ecc71,color:#fff
    style RA fill:#f39c12,color:#fff
```

## 7. Data Flow Between Components

```mermaid
graph LR
    subgraph "Input Layer"
        Doc[Documents]
        Query[Queries]
    end
    
    subgraph "Processing Layer"
        DP[Document<br/>Processor]
        QP[Query<br/>Processor]
    end
    
    subgraph "Transformation Layer"
        EMB[Embedder]
        QA[Query<br/>Analyzer]
    end
    
    subgraph "Storage & Retrieval"
        RET[Unified<br/>Retriever]
        VIdx[(Vector<br/>Index)]
        SIdx[(Sparse<br/>Index)]
    end
    
    subgraph "Generation Layer"
        AG[Answer<br/>Generator]
        LLM[LLM<br/>Clients]
    end
    
    subgraph "Output Layer"
        Answer[Answers]
        Metrics[Metrics]
    end
    
    Doc --> DP
    DP --> EMB
    EMB --> RET
    RET --> VIdx & SIdx
    
    Query --> QP
    QP --> QA
    QA --> RET
    RET --> AG
    AG --> LLM
    LLM --> Answer
    
    DP & EMB & RET & AG --> Metrics
    
    style DP fill:#2ecc71
    style EMB fill:#f39c12
    style RET fill:#3498db
    style AG fill:#1abc9c
    style QP fill:#e74c3c
```