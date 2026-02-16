/**
 * Mock data for the Technical Documentation RAG System frontend demo.
 *
 * All metric values (accuracy, MAE, R2, feature importance, view weights)
 * come from the real Epic 1 training report and fusion model files.
 * Training queries are sampled from the 679-query dataset.
 * Corpus structure mirrors the actual 73-PDF RISC-V collection.
 * Component registry reflects ComponentFactory type mappings.
 */

export const MOCK_DATA = {
  // -----------------------------------------------------------------------
  // 1. Model metrics — from epic1_complete_training_report_20250810_183906.json
  // -----------------------------------------------------------------------
  modelMetrics: {
    // Weighted average fusion — validation
    val_accuracy: 0.9804,
    val_mae: 0.0428,
    val_r2: 0.9451,
    // Weighted average fusion — test
    test_accuracy: 0.9510,
    test_mae: 0.0417,
    test_r2: 0.9381,
    // Ensemble feature importance (from ensemble fusion model)
    featureImportance: {
      linguistic: 0.3235,
      technical: 0.2582,
      semantic: 0.1593,
      task: 0.1517,
      computational: 0.1073
    },
    // Head-to-head: weighted_average vs ensemble
    fusionComparison: {
      weighted_average: {
        val_accuracy: 0.9804,
        val_mae: 0.0428,
        val_r2: 0.9451,
        test_accuracy: 0.9510,
        test_mae: 0.0417,
        test_r2: 0.9381
      },
      ensemble: {
        val_accuracy: 0.9804,
        val_mae: 0.0445,
        val_r2: 0.9399,
        test_accuracy: 0.9706,
        test_mae: 0.0430,
        test_r2: 0.9282
      }
    },
    // Dataset split
    dataset: {
      total: 679,
      train: 475,
      val: 102,
      test: 102
    }
  },

  // -----------------------------------------------------------------------
  // 2. View weights — from weighted_average_fusion.json
  // -----------------------------------------------------------------------
  viewWeights: {
    technical: 0.2000,
    linguistic: 0.2000,
    task: 0.2000,
    semantic: 0.2000,
    computational: 0.2000,
    // Raw values for tooltip precision
    _raw: {
      technical: 0.19999032962292654,
      linguistic: 0.19998833763905233,
      task: 0.19999828247785890,
      semantic: 0.20000875562698767,
      computational: 0.20001429463317463
    },
    thresholds: {
      simple: 0.35,
      complex: 0.70
    }
  },

  // -----------------------------------------------------------------------
  // 3. Training queries — 20 representative items from 679 dataset
  // -----------------------------------------------------------------------
  trainingQueries: [
    // --- Simple (complexity < 0.35) ---
    {
      query: "What does the LW instruction do?",
      complexity_score: 0.18,
      complexity_level: "simple",
      confidence: 0.90,
      domain_relevance: 0.85,
      view_scores: { technical: 0.21, linguistic: 0.14, task: 0.17, semantic: 0.18, computational: 0.19 }
    },
    {
      query: "What is the program counter in RISC-V?",
      complexity_score: 0.18,
      complexity_level: "simple",
      confidence: 0.90,
      domain_relevance: 0.92,
      view_scores: { technical: 0.21, linguistic: 0.14, task: 0.17, semantic: 0.16, computational: 0.22 }
    },
    {
      query: "What's a function in JavaScript?",
      complexity_score: 0.19,
      complexity_level: "simple",
      confidence: 0.89,
      domain_relevance: 0.10,
      view_scores: { technical: 0.21, linguistic: 0.16, task: 0.18, semantic: 0.20, computational: 0.20 }
    },
    {
      query: "How to install RISC-V toolchain?",
      complexity_score: 0.22,
      complexity_level: "simple",
      confidence: 0.85,
      domain_relevance: 0.92,
      view_scores: { technical: 0.26, linguistic: 0.18, task: 0.23, semantic: 0.20, computational: 0.23 }
    },
    {
      query: "What is a function in programming?",
      complexity_score: 0.22,
      complexity_level: "simple",
      confidence: 0.86,
      domain_relevance: 0.10,
      view_scores: { technical: 0.25, linguistic: 0.18, task: 0.21, semantic: 0.23, computational: 0.23 }
    },
    {
      query: "How to run RISC-V code in QEMU?",
      complexity_score: 0.23,
      complexity_level: "simple",
      confidence: 0.85,
      domain_relevance: 0.92,
      view_scores: { technical: 0.27, linguistic: 0.19, task: 0.24, semantic: 0.21, computational: 0.24 }
    },
    {
      query: "How do RISC-V instruction formats work?",
      complexity_score: 0.33,
      complexity_level: "simple",
      confidence: 0.76,
      domain_relevance: 0.92,
      view_scores: { technical: 0.35, linguistic: 0.30, task: 0.34, semantic: 0.32, computational: 0.34 }
    },
    // --- Medium (0.35 <= complexity < 0.70) ---
    {
      query: "What are the basic RISC-V privileged instructions for system calls?",
      complexity_score: 0.35,
      complexity_level: "medium",
      confidence: 0.88,
      domain_relevance: 0.92,
      view_scores: { technical: 0.38, linguistic: 0.32, task: 0.36, semantic: 0.34, computational: 0.35 }
    },
    {
      query: "How do I handle memory alignment requirements when writing RISC-V assembly code?",
      complexity_score: 0.38,
      complexity_level: "medium",
      confidence: 0.86,
      domain_relevance: 0.94,
      view_scores: { technical: 0.42, linguistic: 0.35, task: 0.39, semantic: 0.37, computational: 0.38 }
    },
    {
      query: "What monitoring tools should I use to track performance metrics for a microservices architecture on Kubernetes?",
      complexity_score: 0.46,
      complexity_level: "medium",
      confidence: 0.83,
      domain_relevance: 0.15,
      view_scores: { technical: 0.50, linguistic: 0.42, task: 0.47, semantic: 0.45, computational: 0.46 }
    },
    {
      query: "How can I implement automated testing for API endpoints using different testing frameworks?",
      complexity_score: 0.47,
      complexity_level: "medium",
      confidence: 0.85,
      domain_relevance: 0.10,
      view_scores: { technical: 0.50, linguistic: 0.43, task: 0.48, semantic: 0.46, computational: 0.48 }
    },
    {
      query: "What's the proper way to implement RISC-V system calls in bare-metal programming?",
      complexity_score: 0.48,
      complexity_level: "medium",
      confidence: 0.85,
      domain_relevance: 0.92,
      view_scores: { technical: 0.51, linguistic: 0.44, task: 0.49, semantic: 0.47, computational: 0.50 }
    },
    {
      query: "How do I implement real-time data streaming from PostgreSQL to Elasticsearch using Debezium?",
      complexity_score: 0.51,
      complexity_level: "medium",
      confidence: 0.80,
      domain_relevance: 0.10,
      view_scores: { technical: 0.55, linguistic: 0.47, task: 0.52, semantic: 0.50, computational: 0.51 }
    },
    {
      query: "How do I implement proper security headers and CSRF protection in a multi-tenant SaaS application?",
      complexity_score: 0.61,
      complexity_level: "medium",
      confidence: 0.86,
      domain_relevance: 0.10,
      view_scores: { technical: 0.64, linguistic: 0.58, task: 0.62, semantic: 0.60, computational: 0.61 }
    },
    // --- Complex (complexity >= 0.70) ---
    {
      query: "What are the scalability challenges and solutions for implementing cache-coherent shared memory in massively parallel RISC-V manycore systems with thousands of cores?",
      complexity_score: 0.75,
      complexity_level: "complex",
      confidence: 0.85,
      domain_relevance: 0.92,
      view_scores: { technical: 0.80, linguistic: 0.70, task: 0.78, semantic: 0.76, computational: 0.73 }
    },
    {
      query: "What are the key considerations for implementing a custom memory allocator that supports both garbage collection and manual memory management with predictable allocation patterns for real-time embedded systems?",
      complexity_score: 0.78,
      complexity_level: "complex",
      confidence: 0.84,
      domain_relevance: 0.10,
      view_scores: { technical: 0.82, linguistic: 0.72, task: 0.80, semantic: 0.79, computational: 0.77 }
    },
    {
      query: "What are the verification and validation challenges for RISC-V implementations targeting safety-critical applications requiring DO-254 and ISO 26262 compliance with formal correctness proofs?",
      complexity_score: 0.82,
      complexity_level: "complex",
      confidence: 0.81,
      domain_relevance: 0.92,
      view_scores: { technical: 0.87, linguistic: 0.76, task: 0.84, semantic: 0.83, computational: 0.80 }
    },
    {
      query: "How can I design a compiler optimization framework that performs automatic parallelization of sequential code while respecting memory dependencies and achieving near-optimal load balancing across heterogeneous architectures?",
      complexity_score: 0.86,
      complexity_level: "complex",
      confidence: 0.81,
      domain_relevance: 0.85,
      view_scores: { technical: 0.90, linguistic: 0.79, task: 0.88, semantic: 0.87, computational: 0.85 }
    },
    {
      query: "How do I design a Byzantine fault-tolerant state machine replication protocol that achieves optimal communication complexity while supporting dynamic view changes and providing liveness guarantees under partial synchrony assumptions?",
      complexity_score: 0.89,
      complexity_level: "complex",
      confidence: 0.78,
      domain_relevance: 0.10,
      view_scores: { technical: 0.94, linguistic: 0.82, task: 0.92, semantic: 0.90, computational: 0.88 }
    },
    {
      query: "How do I implement a compiler optimization pass that uses polyhedral analysis for automatic parallelization with optimal tiling and data locality across heterogeneous compute nodes?",
      complexity_score: 0.90,
      complexity_level: "complex",
      confidence: 0.79,
      domain_relevance: 0.85,
      view_scores: { technical: 0.95, linguistic: 0.84, task: 0.92, semantic: 0.89, computational: 0.90 }
    }
  ],

  // -----------------------------------------------------------------------
  // 4. Corpus structure — actual 73 PDFs from data/riscv_corpus/
  // -----------------------------------------------------------------------
  corpus: {
    totalDocuments: 73,
    categories: [
      {
        name: "Core Specs",
        path: "core-specs",
        count: 8,
        subcategories: [
          {
            name: "Official",
            path: "core-specs/official",
            documents: [
              { file: "riscv-spec-unprivileged-v20250508.pdf", title: "RISC-V Instruction Set Manual Volume I: Unprivileged ISA (May 2025)", size_mb: 4.43 },
              { file: "riscv-spec-privileged-v20250508.pdf", title: "RISC-V Instruction Set Manual Volume II: Privileged Architecture (May 2025)", size_mb: 1.31 }
            ]
          },
          {
            name: "Standards",
            path: "core-specs/standards",
            documents: [
              { file: "riscv-abis-specification.pdf", title: "RISC-V ABIs Specification", size_mb: 0.26 },
              { file: "riscv-debug-specification.pdf", title: "RISC-V Debug Specification", size_mb: 2.38 },
              { file: "riscv-sbi-specification.pdf", title: "RISC-V Supervisor Binary Interface Specification", size_mb: 0.44 }
            ]
          },
          {
            name: "Profiles",
            path: "core-specs/profiles",
            documents: [
              { file: "rva23-profile.pdf", title: "RVA23 Profile Specification", size_mb: 0.14 },
              { file: "rvb23-profile.pdf", title: "RVB23 Profile Specification", size_mb: 0.13 }
            ]
          },
          {
            name: "Extensions",
            path: "core-specs/extensions",
            documents: [
              { file: "vector-intrinsic-specification.pdf", title: "RISC-V Vector C Intrinsic Specification", size_mb: 7.84 }
            ]
          }
        ]
      },
      {
        name: "Implementation",
        path: "implementation",
        count: 10,
        subcategories: [
          {
            name: "Debug",
            path: "implementation/debug",
            documents: [
              { file: "efficient-trace-riscv.pdf", title: "Efficient Trace for RISC-V Specification", size_mb: 0.77 },
              { file: "n-trace-nexus.pdf", title: "RISC-V N-Trace (Nexus-based Trace) Specification", size_mb: 0.54 },
              { file: "trace-control-interface.pdf", title: "RISC-V Trace Control Interface Specification", size_mb: 0.52 },
              { file: "trace-connectors.pdf", title: "RISC-V Trace Connectors Specification", size_mb: 0.13 }
            ]
          },
          {
            name: "System",
            path: "implementation/system",
            documents: [
              { file: "advanced-interrupt-architecture.pdf", title: "RISC-V Advanced Interrupt Architecture", size_mb: 0.50 },
              { file: "platform-interrupt-controller.pdf", title: "RISC-V Platform-Level Interrupt Controller Specification", size_mb: 0.52 },
              { file: "iommu-architecture.pdf", title: "RISC-V IOMMU Architecture Specification", size_mb: 0.99 },
              { file: "semihosting-specification.pdf", title: "RISC-V Semihosting Specification", size_mb: 0.13 }
            ]
          },
          {
            name: "SoC",
            path: "implementation/soc",
            documents: [
              { file: "server-soc-specification.pdf", title: "RISC-V Server SOC Specification", size_mb: 0.37 }
            ]
          },
          {
            name: "Firmware",
            path: "implementation/firmware",
            documents: [
              { file: "uefi-protocol-specification.pdf", title: "RISC-V UEFI Protocol Specification", size_mb: 0.15 }
            ]
          }
        ]
      },
      {
        name: "Research",
        path: "research",
        count: 55,
        subcategories: [
          {
            name: "System",
            path: "research/system",
            documents: [
              { file: "qos-register-interface.pdf", title: "RISC-V Capacity and Bandwidth QoS Register Interface", size_mb: 0.29 },
              { file: "reri-architecture.pdf", title: "RISC-V RERI Architecture Specification", size_mb: 0.18 },
              { file: "functional-fixed-hardware.pdf", title: "RISC-V Functional Fixed Hardware Specification", size_mb: 0.09 },
              { file: "io-mapping-table.pdf", title: "RISC-V IO Mapping Table Specification", size_mb: 0.13 }
            ]
          },
          {
            name: "Debug",
            path: "research/debug",
            documents: [
              { file: "trace-encapsulation.pdf", title: "Unformatted Trace & Diagnostic Data Packet Encapsulation for RISC-V", size_mb: 0.10 }
            ]
          },
          {
            name: "Performance Analysis",
            path: "research/papers/performance-analysis",
            documents: [
              { file: "1607.02318v1.pdf", title: "The Renewed Case for the Reduced Instruction Set Computer: Avoiding ISA Bloat with Macro-Op Fusion for RISC-V", size_mb: 0.43 },
              { file: "1905.06825v1.pdf", title: "Fast TLB Simulation for RISC-V Systems", size_mb: 0.62 },
              { file: "2002.03568v1.pdf", title: "RVCoreP: An optimized RISC-V soft processor of five-stage pipelining", size_mb: 0.23 },
              { file: "2010.16171v1.pdf", title: "RVCoreP-32IM: An effective architecture to implement mul/div instructions for five stage RISC-V soft processors", size_mb: 0.30 },
              { file: "2011.11246v1.pdf", title: "RVCoreP-32IC: A high-performance RISC-V soft processor with an efficient fetch unit supporting the compressed instructions", size_mb: 0.49 },
              { file: "2106.07456v1.pdf", title: "Extending the RISC-V ISA for exploring advanced reconfigurable SIMD instructions", size_mb: 0.71 },
              { file: "2112.11767v1.pdf", title: "Supporting RISC-V Performance Counters through Performance analysis tools for Linux (Perf)", size_mb: 0.58 },
              { file: "2304.10319v1.pdf", title: "Test-driving RISC-V Vector hardware for HPC", size_mb: 0.36 },
              { file: "2304.10324v1.pdf", title: "Backporting RISC-V Vector assembly", size_mb: 0.34 },
              { file: "2304.12309v1.pdf", title: "Optimized Real-Time Assembly in a RISC Simulator", size_mb: 0.59 },
              { file: "2305.00584v2.pdf", title: "MAMBO-V: Dynamic Side-Channel Leakage Analysis on RISC-V", size_mb: 0.55 },
              { file: "2305.09266v1.pdf", title: "Case Study for Running Memory-Bound Kernels on RISC-V CPUs", size_mb: 0.87 },
              { file: "2309.00381v2.pdf", title: "Is RISC-V ready for HPC prime-time: Evaluating the 64-core Sophon SG2042 RISC-V CPU", size_mb: 0.25 },
              { file: "2311.05284v1.pdf", title: "Challenges and Opportunities in the Co-design of Convolutions and RISC-V Vector Processors", size_mb: 0.59 },
              { file: "2405.11062v1.pdf", title: "Vectorization of Gradient Boosting of Decision Trees Prediction in the CatBoost Library for RISC-V Processors", size_mb: 1.09 },
              { file: "2405.15380v1.pdf", title: "Full-stack evaluation of Machine Learning inference workloads for RISC-V systems", size_mb: 0.25 },
              { file: "2407.00026v2.pdf", title: "Preparing for HPC on RISC-V: Examining Vectorization and Distributed Performance of an Astrophysics Application with HPX and Kokkos", size_mb: 1.46 },
              { file: "2407.13326v1.pdf", title: "RISC-V RVV efficiency for ANN algorithms", size_mb: 0.57 },
              { file: "2407.14274v2.pdf", title: "Mixed-precision Neural Networks on RISC-V Cores: ISA extensions for Multi-Pumped Soft SIMD Operations", size_mb: 2.82 },
              { file: "2409.00661v1.pdf", title: "Research on LLM Acceleration Using the High-Performance RISC-V Processor Xiangshan Based on the Open-Source Matrix Instruction Set Extension", size_mb: 0.71 },
              { file: "2409.18835v1.pdf", title: "Accelerating stencils on the Tenstorrent Grayskull RISC-V accelerator", size_mb: 0.29 },
              { file: "2411.12444v2.pdf", title: "Advancing Cloud Computing Capabilities on gem5 by Implementing the RISC-V Hypervisor Extension", size_mb: 0.54 },
              { file: "2412.05286v1.pdf", title: "RISC-V Word-Size Modular Instructions for Residue Number Systems", size_mb: 0.59 },
              { file: "2501.10189v1.pdf", title: "Optimizing Structured-Sparse Matrix Multiplication in RISC-V Vector Processors", size_mb: 13.51 },
              { file: "2502.13839v2.pdf", title: "Performance optimization of BLAS algorithms with band matrices for RISC-V processors", size_mb: 0.76 },
              { file: "2504.05284v1.pdf", title: "FERIVer: An FPGA-assisted Emulated Framework for RTL Verification of RISC-V Processors", size_mb: 0.73 },
              { file: "2505.04567v2.pdf", title: "Flexing RISC-V Instruction Subset Processors (RISPs) to Extreme Edge", size_mb: 2.52 },
              { file: "2505.07112v2.pdf", title: "Efficient Implementation of RISC-V Vector Permutation Instructions", size_mb: 4.57 },
              { file: "2506.06693v1.pdf", title: "Design and Implementation of a RISC-V SoC with Custom DSP Accelerators for Edge Computing", size_mb: 0.30 },
              { file: "2506.08653v1.pdf", title: "Parallel FFTW on RISC-V: A Comparative Study including OpenMP, MPI, and HPX", size_mb: 0.45 },
              { file: "2507.01457v1.pdf", title: "Tensor Program Optimization for the RISC-V Vector Extension Using Probabilistic Programs", size_mb: 0.39 },
              { file: "2507.03773v1.pdf", title: "RVISmith: Fuzzing Compilers for RVV Intrinsics", size_mb: 1.04 }
            ]
          },
          {
            name: "Security Studies",
            path: "research/papers/security-studies",
            documents: [
              { file: "1908.11648v3.pdf", title: "Porting of eChronos RTOS on RISC-V Architecture", size_mb: 0.24 },
              { file: "2007.14995v1.pdf", title: "Return-Oriented Programming in RISC-V", size_mb: 0.12 },
              { file: "2103.08229v1.pdf", title: "Return-Oriented Programming on RISC-V", size_mb: 0.77 },
              { file: "2106.08877v1.pdf", title: "Side-Channel Attacks on RISC-V Processors: Current Progress, Challenges, and Opportunities", size_mb: 1.04 },
              { file: "2107.04175v1.pdf", title: "A Survey on RISC-V Security: Hardware and Architecture", size_mb: 2.24 },
              { file: "2211.10299v2.pdf", title: "Trusted Hart for Mobile RISC-V Security", size_mb: 0.67 },
              { file: "2211.16212v1.pdf", title: "Control-Flow Integrity at RISC: Attacking RISC-V by Jump-Oriented Programming", size_mb: 0.61 },
              { file: "2307.12648v1.pdf", title: "Execution at RISC: Stealth JOP Attacks on RISC-V Applications", size_mb: 0.68 },
              { file: "2502.10194v1.pdf", title: "Translating Common Security Assertions Across Processor Designs: A RISC-V Case Study", size_mb: 0.69 },
              { file: "2503.04846v2.pdf", title: "Honest to a Fault: Root-Causing Fault Attacks with Pre-Silicon RISC Pipeline Characterization", size_mb: 0.89 }
            ]
          },
          {
            name: "Architecture Studies",
            path: "research/papers/architecture-studies",
            documents: [
              { file: "2002.03576v2.pdf", title: "A portable and Linux capable RISC-V computer system in Verilog HDL", size_mb: 0.26 },
              { file: "2206.01901v1.pdf", title: "Enabling Heterogeneous, Multicore SoC Research with RISC-V and ESP", size_mb: 0.97 },
              { file: "2206.08639v1.pdf", title: "Experimental evaluation of neutron-induced errors on a multicore RISC-V platform", size_mb: 0.74 },
              { file: "2312.01455v1.pdf", title: "32-Bit RISC-V CPU Core on Logisim", size_mb: 1.76 },
              { file: "2504.03722v1.pdf", title: "WebRISC-V: A 64-bit RISC-V Pipeline Simulator for Computer Architecture Classes", size_mb: 0.27 },
              { file: "2505.10217v1.pdf", title: "Enabling Syscall Intercept for RISC-V", size_mb: 0.45 },
              { file: "2505.19096v1.pdf", title: "Enable Lightweight and Precision-Scalable Posit/IEEE-754 Arithmetic in RISC-V Cores for Transprecision Computing", size_mb: 0.53 }
            ]
          },
          {
            name: "Benchmarking",
            path: "research/papers/benchmarking",
            documents: [
              { file: "2010.10119v1.pdf", title: "A RISC-V SystemC-TLM simulator", size_mb: 0.64 }
            ]
          }
        ]
      }
    ]
  },

  // -----------------------------------------------------------------------
  // 5. Configs — 23 YAML files from config/
  // -----------------------------------------------------------------------
  configs: [
    { name: "basic.yaml", description: "Basic RAG pipeline with RRF fusion, identity reranker, and mock LLM", features: ["hybrid_pdf", "bm25", "rrf", "mock_llm"] },
    { name: "default.yaml", description: "Epic 1 default config with domain-aware processing and ML-powered analysis", features: ["epic1", "domain_aware", "ml_analyzer", "adaptive_routing"] },
    { name: "demo.yaml", description: "Demo-optimized config with neural reranking and HuggingFace generation", features: ["neural_reranker", "huggingface_llm", "rrf"] },
    { name: "local.yaml", description: "Local development config with FAISS, identity reranker, and llama-server LLM", features: ["faiss", "bm25", "rrf", "local_llm"] },
    { name: "test.yaml", description: "Epic 1 test configuration for CI/CD with domain-aware processing", features: ["epic1", "domain_aware", "mock_llm"] },
    { name: "test-local.yaml", description: "Local test configuration for development machine testing", features: ["faiss", "identity_reranker", "local_llm"] },
    { name: "epic1_multi_model.yaml", description: "Multi-model routing with view-based query analysis and cost-optimized strategies", features: ["multi_model", "cost_tracking", "routing_strategies", "fallback_chain"] },
    { name: "epic1_ml_analyzer.yaml", description: "Epic 1 ML-powered query complexity analyzer configuration", features: ["epic1_ml", "complexity_analysis", "model_recommendation"] },
    { name: "epic1_ml_simple.yaml", description: "Simplified Epic 1 ML analyzer for lightweight deployments", features: ["epic1_ml", "simplified"] },
    { name: "epic1_trained_ml_analyzer.yaml", description: "Epic 1 analyzer using trained view models and fusion weights", features: ["trained_models", "view_models", "fusion_weights"] },
    { name: "epic1_ecs_deployment.yaml", description: "Epic 1 ECS deployment configuration for AWS cloud", features: ["ecs", "aws", "cloud_deployment"] },
    { name: "epic2.yaml", description: "Full Epic 2 config with neural reranking, score-aware fusion, and HuggingFace LLM", features: ["neural_reranker", "score_aware_fusion", "huggingface_llm"] },
    { name: "epic2_graph_enhanced_mock.yaml", description: "Graph-enhanced RRF fusion with mock LLM for testing graph retrieval", features: ["graph_enhanced_rrf", "neural_reranker", "mock_llm"] },
    { name: "epic2_graph_enhanced_hf.yaml", description: "Graph-enhanced RRF fusion with HuggingFace LLM", features: ["graph_enhanced_rrf", "neural_reranker", "huggingface_llm"] },
    { name: "epic2_graph_enhanced_ollama.yaml", description: "Graph-enhanced RRF fusion with Ollama local LLM", features: ["graph_enhanced_rrf", "neural_reranker", "ollama_llm"] },
    { name: "epic2_score_aware_mock.yaml", description: "Score-aware fusion with mock LLM for testing score preservation", features: ["score_aware_fusion", "neural_reranker", "mock_llm"] },
    { name: "epic2_score_aware_hf.yaml", description: "Score-aware fusion with HuggingFace LLM", features: ["score_aware_fusion", "neural_reranker", "huggingface_llm"] },
    { name: "epic2_score_aware_ollama.yaml", description: "Score-aware fusion with Ollama local LLM", features: ["score_aware_fusion", "neural_reranker", "ollama_llm"] },
    { name: "epic5_tools.yaml", description: "Epic 5 Phase 1 tool configuration: calculator, code analyzer, document search", features: ["calculator", "code_analyzer", "document_search", "function_calling"] },
    { name: "epic5_agents.yaml", description: "Epic 5 agent-based RAG with ReAct reasoning, tool use, and intelligent routing", features: ["react_agent", "tool_registry", "intelligent_processor", "memory"] },
    { name: "indices.yaml", description: "Vector index storage and management configuration", features: ["faiss_index", "index_metadata"] },
    { name: "models.yaml", description: "ML model configuration: embedding models, cross-encoders, cache settings", features: ["model_registry", "cache_config", "download_settings"] },
    { name: "mlflow_config.yaml", description: "MLflow experiment tracking and model registry settings", features: ["experiment_tracking", "model_registry", "artifact_storage"] }
  ],

  // -----------------------------------------------------------------------
  // 6. Component registry — from ComponentFactory type mappings
  // -----------------------------------------------------------------------
  componentRegistry: {
    processors: [
      { type: "hybrid_pdf", class: "ModularDocumentProcessor", description: "PDF processing with chunking and metadata extraction" },
      { type: "modular", class: "ModularDocumentProcessor", description: "Alias for hybrid_pdf processor" },
      { type: "pdf_processor", class: "ModularDocumentProcessor", description: "Legacy alias redirected to modular processor" },
      { type: "legacy_pdf", class: "ModularDocumentProcessor", description: "Legacy alias redirected to modular processor" }
    ],
    embedders: [
      { type: "modular", class: "ModularEmbedder", description: "Configurable embedder with model, batch processor, and cache sub-components" },
      { type: "sentence_transformer", class: "SentenceTransformerEmbedder", description: "Direct sentence-transformers embedding" },
      { type: "sentence_transformers", class: "SentenceTransformerEmbedder", description: "Alias for sentence_transformer" }
    ],
    retrievers: [
      { type: "unified", class: "ModularUnifiedRetriever", description: "Unified retriever with vector index, BM25, fusion, and reranking" },
      { type: "modular_unified", class: "ModularUnifiedRetriever", description: "Primary retriever with pluggable sub-components" }
    ],
    generators: [
      { type: "adaptive", class: "Epic1AnswerGenerator", description: "Epic 1 multi-model generator with routing" },
      { type: "adaptive_generator", class: "Epic1AnswerGenerator", description: "Alias for Epic 1 generator" },
      { type: "adaptive_modular", class: "AnswerGenerator", description: "Modular answer generator with pluggable LLM adapters" },
      { type: "answer_generator", class: "AnswerGenerator", description: "Alias for modular generator" },
      { type: "epic1", class: "Epic1AnswerGenerator", description: "Epic 1 multi-model generator" },
      { type: "epic1_multi_model", class: "Epic1AnswerGenerator", description: "Epic 1 multi-model with routing strategies" }
    ],
    queryProcessors: [
      { type: "basic", class: "ModularQueryProcessor", description: "Basic query processing with analysis, selection, and assembly" },
      { type: "modular", class: "ModularQueryProcessor", description: "Modular query processor with pluggable analyzer/selector/assembler" },
      { type: "modular_query_processor", class: "ModularQueryProcessor", description: "Alias for modular processor" },
      { type: "domain_aware", class: "DomainAwareQueryProcessor", description: "Epic 1 Phase 1 domain-aware query processing" },
      { type: "epic1_domain_aware", class: "DomainAwareQueryProcessor", description: "Alias for domain_aware processor" },
      { type: "intelligent", class: "IntelligentQueryProcessor", description: "Epic 5 Phase 2 Block 3 intelligent processor with agent routing" },
      { type: "epic5_intelligent", class: "IntelligentQueryProcessor", description: "Alias for intelligent processor" }
    ],
    subComponents: {
      queryAnalyzers: [
        { type: "nlp", class: "NLPAnalyzer", description: "NLP-based query analysis" },
        { type: "rule_based", class: "RuleBasedAnalyzer", description: "Rule-based query complexity analysis" },
        { type: "epic1", class: "Epic1QueryAnalyzer", description: "Epic 1 multi-view query analyzer" },
        { type: "epic1_ml", class: "Epic1MLAnalyzer", description: "Epic 1 ML-powered analyzer" },
        { type: "epic1_ml_adapter", class: "EpicMLAdapter", description: "Epic 1 adapter using trained models" }
      ],
      tools: [
        { type: "calculator", class: "CalculatorTool", description: "Safe mathematical expression evaluation" },
        { type: "code_analyzer", class: "CodeAnalyzerTool", description: "Python code structure and metrics analysis" },
        { type: "document_search", class: "DocumentSearchTool", description: "RAG-powered document search" }
      ],
      memory: [
        { type: "conversation", class: "ConversationMemory", description: "Multi-turn conversation history" },
        { type: "working", class: "WorkingMemory", description: "Scratchpad for agent reasoning steps" }
      ],
      llmAdapters: [
        { type: "mock", description: "Template-based mock responses for testing" },
        { type: "local", description: "Local llama-server / Ollama LLM" },
        { type: "openai", description: "OpenAI GPT models via API" },
        { type: "mistral", description: "Mistral AI models via API" },
        { type: "anthropic", description: "Anthropic Claude models via API" },
        { type: "huggingface", description: "HuggingFace Inference API models" }
      ],
      fusionStrategies: [
        { type: "rrf", description: "Reciprocal Rank Fusion" },
        { type: "score_aware", description: "Score-aware fusion preserving BM25/semantic scores" },
        { type: "graph_enhanced_rrf", description: "Graph-enhanced RRF with entity and relationship boosting" }
      ],
      rerankers: [
        { type: "identity", description: "Pass-through reranker (no reranking)" },
        { type: "neural", description: "Cross-encoder neural reranking (ms-marco-MiniLM-L6-v2)" }
      ]
    }
  },

  // -----------------------------------------------------------------------
  // 7. Query/response mocks — three full examples
  // -----------------------------------------------------------------------
  queryMocks: {
    simple: {
      query: "What are the base RISC-V integer instruction formats?",
      strategy: "cost_optimized",
      answer: "RISC-V defines six base instruction formats for the 32-bit encoding: R-type for register-register operations (ADD, SUB, SLL), I-type for immediate and load operations (ADDI, LW, JALR), S-type for store operations (SW, SB), B-type for conditional branches (BEQ, BNE), U-type for upper-immediate operations (LUI, AUIPC), and J-type for unconditional jumps (JAL). All formats keep the source register specifiers (rs1, rs2) and destination register (rd) at fixed bit positions to simplify decoding.",
      confidence: 0.92,
      model: "local/all-MiniLM-L6-v2",
      processingTime: { analysis: 45, retrieval: 120, generation: 180 },
      complexity: {
        overall: 0.25,
        label: "simple",
        scores: { technical: 0.30, linguistic: 0.20, semantic: 0.15, computational: 0.10, task: 0.50 }
      },
      sources: [
        { title: "RISC-V Instruction Set Manual Volume I: Unprivileged ISA", score: 0.94, snippet: "The RISC-V ISA keeps the source (rs1 and rs2) and destination (rd) register specifiers at the same position in all formats to simplify decoding. Except for the 5-bit immediates used in CSR instructions, immediates are always sign-extended.", file: "riscv-spec-unprivileged-v20250508.pdf", method: "hybrid" },
        { title: "RISC-V ABIs Specification", score: 0.89, snippet: "RV32I provides six instruction formats (R/I/S/B/U/J), each encoding a 7-bit opcode, function code fields, and register specifiers in a fixed 32-bit word.", file: "riscv-abis-specification.pdf", method: "semantic" },
        { title: "32-Bit RISC-V CPU Core on Logisim", score: 0.85, snippet: "The decoder identifies the instruction format from the opcode field (bits 6:0) and routes operands to the appropriate functional units based on the R, I, S, B, U, or J encoding.", file: "2312.01455v1.pdf", method: "bm25" },
        { title: "WebRISC-V: A 64-bit RISC-V Pipeline Simulator", score: 0.78, snippet: "Each instruction format places the immediate bits in different positions but maintains consistent register specifier locations, enabling a simplified decode stage in the pipeline.", file: "2504.03722v1.pdf", method: "semantic" }
      ],
      cost: { model_cost: 0.0002, retrieval_cost: 0.0001, total: 0.0003 }
    },

    complex: {
      query: "Compare RISC-V PMP versus ARM TrustZone security models in terms of hardware isolation, privilege levels, and side-channel resistance",
      strategy: "quality_first",
      answer: "RISC-V Physical Memory Protection (PMP) and ARM TrustZone take fundamentally different approaches to hardware security. PMP provides per-hart, region-based memory access control configured through CSRs in M-mode, supporting up to 64 regions with configurable read/write/execute permissions and address-matching modes (NAPOT, TOR). TrustZone, by contrast, creates a binary Secure/Non-Secure world partition enforced by the bus fabric, where the NS bit propagates with every transaction. In terms of privilege levels, RISC-V offers three rings (M/S/U) with PMP rules evaluated per ring, while ARM TrustZone overlays its two-world model onto the existing EL0-EL3 exception levels. Regarding side-channel resistance, neither architecture provides inherent protection in the ISA itself. However, RISC-V research demonstrates that PMP's configurable granularity can be combined with temporal partitioning (fence.t proposals) to reduce cache-based side channels, whereas TrustZone relies on cache partitioning and TrustZone-aware cache controllers to mitigate cross-world leakage.",
      confidence: 0.87,
      model: "openai/gpt-4",
      processingTime: { analysis: 85, retrieval: 250, generation: 1200 },
      complexity: {
        overall: 0.82,
        label: "complex",
        scores: { technical: 0.90, linguistic: 0.70, semantic: 0.85, computational: 0.30, task: 0.95 }
      },
      sources: [
        { title: "RISC-V Instruction Set Manual Volume II: Privileged Architecture", score: 0.96, snippet: "PMP entries are statically prioritized; the lowest-numbered PMP entry that matches any byte of an access determines whether that access succeeds or fails. M-mode accesses are checked against PMP only when the L bit is set.", file: "riscv-spec-privileged-v20250508.pdf", method: "hybrid" },
        { title: "A Survey on RISC-V Security: Hardware and Architecture", score: 0.93, snippet: "Unlike ARM TrustZone's binary world separation, RISC-V PMP provides fine-grained memory protection configurable at arbitrary granularity, allowing M-mode software to isolate S-mode and U-mode with flexible region definitions.", file: "2107.04175v1.pdf", method: "hybrid" },
        { title: "Side-Channel Attacks on RISC-V Processors: Current Progress, Challenges, and Opportunities", score: 0.91, snippet: "Cache side-channel attacks on RISC-V processors mirror those on other architectures. Spectre-style transient execution attacks have been demonstrated on BOOM and other out-of-order RISC-V cores.", file: "2106.08877v1.pdf", method: "semantic" },
        { title: "Trusted Hart for Mobile RISC-V Security", score: 0.88, snippet: "The Trusted Hart model proposes a dedicated security hart that provides isolation guarantees analogous to TrustZone's Secure World but leverages RISC-V's PMP and ePMP extensions for finer-grained control.", file: "2211.10299v2.pdf", method: "semantic" },
        { title: "Translating Common Security Assertions Across Processor Designs: A RISC-V Case Study", score: 0.84, snippet: "Security properties such as privilege escalation prevention, memory isolation, and information flow control can be formally specified and verified across different RISC-V implementations using assertion-based verification.", file: "2502.10194v1.pdf", method: "bm25" }
      ],
      cost: { model_cost: 0.045, retrieval_cost: 0.0025, total: 0.0475 }
    },

    agent: {
      query: "How many registers does RV32I define, and what is 2^5?",
      strategy: "balanced",
      answer: "RV32I defines 32 general-purpose registers (x0-x31), where x0 is hardwired to zero. The value 2^5 = 32, which directly corresponds to the register count: the 5-bit register specifier fields in RISC-V instructions can encode exactly 2^5 = 32 distinct register addresses.",
      confidence: 0.95,
      model: "mistral/mistral-medium",
      processingTime: { analysis: 60, retrieval: 180, generation: 800 },
      complexity: {
        overall: 0.45,
        label: "medium",
        scores: { technical: 0.60, linguistic: 0.30, semantic: 0.40, computational: 0.70, task: 0.50 }
      },
      sources: [
        { title: "RISC-V Instruction Set Manual Volume I: Unprivileged ISA", score: 0.96, snippet: "RV32I was designed to be sufficient to form a compiler target and to support modern operating system environments. The ISA was also designed to reduce the hardware required in a minimal implementation. RV32I contains 40 unique instructions. The base integer ISA has a little-endian memory system and uses 32 x registers, each 32 bits wide.", file: "riscv-spec-unprivileged-v20250508.pdf", method: "hybrid" }
      ],
      cost: { model_cost: 0.0034, retrieval_cost: 0.0002, total: 0.0036 },
      reasoningSteps: [
        { type: "THOUGHT", content: "The user wants to know the register count for RV32I and calculate 2^5. I'll search the documentation first, then use the calculator to verify the math." },
        { type: "ACTION", content: "Searching knowledge base for 'RV32I registers'", tool: "search_documents", input: "RV32I register count general-purpose" },
        { type: "OBSERVATION", content: "Found: RV32I contains 40 unique instructions and uses 32 x registers (x0-x31), each 32 bits wide. Register x0 is hardwired to the constant 0." },
        { type: "THOUGHT", content: "I found that RV32I has 32 general-purpose registers. Now I need to calculate 2^5 using the calculator tool." },
        { type: "ACTION", content: "Calculating 2^5", tool: "calculator", input: "2**5" },
        { type: "OBSERVATION", content: "Result: 32" },
        { type: "THOUGHT", content: "2^5 = 32, which matches the register count. This makes architectural sense: RISC-V uses 5-bit fields to encode register specifiers, so 2^5 = 32 is the maximum number of registers addressable with that encoding." },
        { type: "FINAL_ANSWER", content: "RV32I defines 32 general-purpose registers (x0-x31), where x0 is hardwired to zero. The value 2^5 = 32, which directly corresponds to the register count: the 5-bit register specifier fields in RISC-V instructions can encode exactly 2^5 = 32 distinct register addresses." }
      ]
    }
  },

  // -----------------------------------------------------------------------
  // 8. Config comparison — same query through 3 strategies
  // -----------------------------------------------------------------------
  configComparison: {
    query: "Explain RISC-V privilege levels",
    results: [
      {
        config: "cost_optimized",
        model: "local/all-MiniLM-L6-v2",
        confidence: 0.78,
        topScore: 0.91,
        timing: 320,
        cost: 0.0002,
        fusion: "weighted_average",
        reranker: "none",
        answerPreview: "RISC-V defines three privilege levels: Machine (M), Supervisor (S), and User (U). Machine mode has the highest privilege and is the only mandatory level. Supervisor mode provides virtual memory support for operating systems, while User mode runs application code with restricted access."
      },
      {
        config: "balanced",
        model: "mistral/mistral-medium",
        confidence: 0.88,
        topScore: 0.93,
        timing: 890,
        cost: 0.0036,
        fusion: "reciprocal_rank",
        reranker: "cross_encoder",
        answerPreview: "The RISC-V architecture implements a hierarchical privilege model with three distinct levels. Machine mode (M-mode) is the highest privilege level with full hardware access, mandatory in all implementations. Supervisor mode (S-mode) manages virtual memory via the Sv39/Sv48 page tables and handles traps from user code. User mode (U-mode) provides application isolation with restricted CSR access."
      },
      {
        config: "quality_first",
        model: "openai/gpt-4",
        confidence: 0.94,
        topScore: 0.95,
        timing: 2100,
        cost: 0.0475,
        fusion: "ensemble",
        reranker: "neural",
        answerPreview: "RISC-V's privilege architecture provides three levels of execution privilege, each designed for specific system software layers. M-mode operates with unrestricted access to all hardware resources and CSRs, serving as the root of trust. S-mode introduces virtual address translation (Sv32/Sv39/Sv48/Sv57) and trap delegation via medeleg/mideleg CSRs. U-mode enforces the principle of least privilege for application code."
      }
    ]
  },

  // -----------------------------------------------------------------------
  // 9. Example queries for query page
  // -----------------------------------------------------------------------
  exampleQueries: [
    { label: "Instruction Formats", query: "What are the base RISC-V integer instruction formats?", type: "simple" },
    { label: "Memory Model", query: "How does the RISC-V weak memory ordering model work?", type: "simple" },
    { label: "Extensions", query: "What standard extensions are available in RISC-V?", type: "simple" },
    { label: "Privilege Levels", query: "Explain RISC-V privilege levels", type: "simple" },
    { label: "Vector Extension", query: "What is the RISC-V vector extension and what operations does it support?", type: "medium" },
    { label: "PMP Configuration", query: "How does RISC-V handle privilege levels and memory protection?", type: "medium" },
    { label: "Security Comparison", query: "Compare RISC-V PMP versus ARM TrustZone security models in terms of hardware isolation, privilege levels, and side-channel resistance", type: "complex" },
    { label: "Vector Processing", query: "Analyze the performance implications of RISC-V vector extension vs ARM SVE for ML workloads", type: "complex" },
    { label: "Register Calculator", query: "How many registers does RV32I define, and what is 2^5?", type: "agent" },
    { label: "Code Analysis", query: "Analyze the RISC-V instruction decoder function and calculate the number of supported formats", type: "agent" }
  ],

  // -----------------------------------------------------------------------
  // 10. System stats for landing page
  // -----------------------------------------------------------------------
  systemStats: {
    documents: 73,
    trainingQueries: 679,
    configurations: 23,
    components: 30,
    tests: 2700
  }
};
