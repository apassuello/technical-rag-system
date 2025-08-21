# Epic 8: API Reference - Cloud-Native Multi-Model RAG Platform

**Version**: 1.0  
**Date**: August 21, 2025  
**API Version**: v1  
**Status**: Phase 1 Implementation

---

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Query Analyzer Service API](#query-analyzer-service-api)
4. [Generator Service API](#generator-service-api)
5. [Common Data Models](#common-data-models)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Health & Monitoring](#health--monitoring)
9. [API Usage Examples](#api-usage-examples)
10. [SDK & Client Libraries](#sdk--client-libraries)

---

## API Overview

### Service Endpoints

| Service | Base URL | Port | Protocol | Status | Documentation |
|---------|----------|------|----------|--------|---------------|
| **Query Analyzer** | `http://localhost:8080` | 8080 | HTTP REST | ✅ Active | `/docs` |
| **Generator** | `http://localhost:8081` | 8081 | HTTP REST | ✅ Active | `/docs` |
| **Retriever** | `http://localhost:8082` | 8082 | HTTP REST | 📋 Planned | N/A |
| **API Gateway** | `http://localhost:80` | 80/443 | HTTP REST | 📋 Planned | N/A |

### API Design Principles

- **RESTful Design**: HTTP methods with resource-based URLs
- **JSON Communication**: Request/response bodies in JSON format
- **OpenAPI 3.0**: Complete API specification with Swagger UI
- **Idempotent Operations**: Safe retry behavior for all endpoints
- **Consistent Error Format**: Standardized error responses across services
- **Semantic Versioning**: API version in URL path (`/api/v1/`)

---

## Authentication & Authorization

### Authentication Methods

**Current Implementation (Phase 1)**:
- **No Authentication**: Development mode for testing
- **CORS Enabled**: Cross-origin requests allowed (configurable)

**Planned Implementation (Phase 3)**:
- **Bearer Token**: API key authentication
- **Rate Limiting**: Per-client request quotas
- **mTLS**: Service-to-service authentication

```http
# Future authentication header
Authorization: Bearer <api-key>
Content-Type: application/json
```

---

## Query Analyzer Service API

**Base URL**: `http://localhost:8080/api/v1`  
**Service**: Query complexity analysis and model recommendation

### Endpoints Overview

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| `POST` | `/analyze` | Analyze single query | ✅ Active |
| `POST` | `/batch-analyze` | Analyze multiple queries | ✅ Active |
| `GET` | `/status` | Service status & metrics | ✅ Active |
| `GET` | `/components` | Component health info | ✅ Active |

---

### POST /api/v1/analyze

**Description**: Analyze a single query for complexity classification and model recommendation.

#### Request Schema

```http
POST /api/v1/analyze
Content-Type: application/json

{
  "query": "What are the key differences between RISC-V and ARM architectures?",
  "context": {
    "user_tier": "premium",
    "max_cost": 0.05,
    "preferred_models": ["openai/gpt-3.5-turbo"],
    "domain": "technical"
  },
  "options": {
    "strategy": "quality_first",
    "include_features": true,
    "include_cost_estimate": true
  }
}
```

**Request Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | ✅ Yes | Query text to analyze (max 10,000 chars) |
| `context` | object | ❌ Optional | User context and preferences |
| `context.user_tier` | string | ❌ Optional | User tier: "free", "premium", "enterprise" |
| `context.max_cost` | number | ❌ Optional | Maximum cost per query (USD) |
| `context.preferred_models` | array[string] | ❌ Optional | Preferred model identifiers |
| `context.domain` | string | ❌ Optional | Query domain: "technical", "general", "creative" |
| `options` | object | ❌ Optional | Analysis options |
| `options.strategy` | string | ❌ Optional | Routing strategy: "cost_optimized", "balanced", "quality_first" |
| `options.include_features` | boolean | ❌ Optional | Include extracted features in response |
| `options.include_cost_estimate` | boolean | ❌ Optional | Include cost estimates for models |

#### Response Schema

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "query": "What are the key differences between RISC-V and ARM architectures?",
  "complexity": "medium",
  "confidence": 0.78,
  "features": {
    "length": 65,
    "vocabulary_complexity": 0.7,
    "technical_terms": ["RISC-V", "ARM", "architectures"],
    "question_type": "comparison",
    "linguistic_features": {
      "num_sentences": 1,
      "avg_word_length": 6.2,
      "technical_density": 0.15
    },
    "structural_features": {
      "has_questions": true,
      "comparative_language": true,
      "specificity_score": 0.8
    }
  },
  "recommended_models": [
    "openai/gpt-3.5-turbo",
    "mistral/mistral-medium",
    "ollama/llama3.2:3b"
  ],
  "cost_estimate": {
    "openai/gpt-3.5-turbo": 0.002,
    "mistral/mistral-medium": 0.004,
    "ollama/llama3.2:3b": 0.0
  },
  "routing_strategy": "quality_first",
  "processing_time": 0.045,
  "metadata": {
    "analyzer_version": "1.0.0",
    "timestamp": 1692633456.789,
    "request_id": "req_123abc456def"
  }
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Original query text |
| `complexity` | string | Complexity level: "simple", "medium", "complex" |
| `confidence` | number | Confidence score (0.0-1.0) for complexity classification |
| `features` | object | Extracted query features (if requested) |
| `recommended_models` | array[string] | Ordered list of recommended models |
| `cost_estimate` | object | Estimated cost per model (USD) |
| `routing_strategy` | string | Applied routing strategy |
| `processing_time` | number | Analysis time in seconds |
| `metadata` | object | Response metadata and tracking info |

---

### POST /api/v1/batch-analyze

**Description**: Analyze multiple queries in a single request for batch processing.

#### Request Schema

```http
POST /api/v1/batch-analyze
Content-Type: application/json

{
  "queries": [
    "What is machine learning?",
    "Explain quantum computing principles",
    "How do transformers work in NLP?"
  ],
  "context": {
    "user_tier": "premium",
    "max_cost": 0.10
  },
  "options": {
    "strategy": "balanced",
    "include_summary": true
  }
}
```

#### Response Schema

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "request_id": "batch_789xyz123",
  "total_queries": 3,
  "successful_analyses": 3,
  "failed_analyses": 0,
  "processing_time": 0.123,
  "complexity_distribution": {
    "simple": 1,
    "medium": 1,
    "complex": 1
  },
  "summary": {
    "average_confidence": 0.82,
    "most_common_complexity": "medium",
    "recommended_strategy": "balanced",
    "estimated_total_cost": 0.008
  },
  "results": [
    {
      "index": 0,
      "query": "What is machine learning?",
      "result": {
        "complexity": "simple",
        "confidence": 0.91,
        "recommended_models": ["ollama/llama3.2:3b"],
        "cost_estimate": {"ollama/llama3.2:3b": 0.0}
      }
    },
    {
      "index": 1,
      "query": "Explain quantum computing principles",
      "result": {
        "complexity": "complex",
        "confidence": 0.85,
        "recommended_models": ["openai/gpt-4", "mistral/mistral-large"],
        "cost_estimate": {
          "openai/gpt-4": 0.008,
          "mistral/mistral-large": 0.006
        }
      }
    }
  ]
}
```

---

### GET /api/v1/status

**Description**: Get current status of the query analyzer service with performance metrics.

#### Request Parameters

```http
GET /api/v1/status?include_performance=true&include_config=false
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_performance` | boolean | `false` | Include performance metrics |
| `include_config` | boolean | `false` | Include configuration details |

#### Response Schema

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "service": "query-analyzer",
  "version": "1.0.0",
  "status": "healthy",
  "initialized": true,
  "uptime_seconds": 3600,
  "analyzer_type": "Epic1QueryAnalyzer",
  "components": {
    "feature_extractor": "healthy",
    "complexity_classifier": "healthy", 
    "model_recommender": "healthy"
  },
  "performance": {
    "total_requests": 1524,
    "avg_response_time_ms": 45.2,
    "requests_per_second": 12.3,
    "error_rate": 0.02,
    "complexity_distribution": {
      "simple": 0.35,
      "medium": 0.45,
      "complex": 0.20
    }
  },
  "last_health_check": "2025-08-21T10:30:45Z"
}
```

---

### GET /api/v1/components

**Description**: Get detailed information about analyzer components and their health status.

#### Response Schema

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "service_info": {
    "name": "query-analyzer",
    "version": "1.0.0",
    "analyzer_type": "Epic1QueryAnalyzer",
    "initialized": true
  },
  "components": {
    "feature_extractor": {
      "status": "healthy",
      "description": "Extracts linguistic, structural, and semantic features from queries",
      "capabilities": [
        "Linguistic analysis (syntax, vocabulary)",
        "Structural analysis (length, complexity)",
        "Semantic analysis (embeddings, topics)",
        "Feature caching for performance"
      ],
      "configuration": {
        "enable_caching": true,
        "cache_size": 1000,
        "extract_linguistic": true,
        "extract_structural": true,
        "extract_semantic": true
      }
    },
    "complexity_classifier": {
      "status": "healthy",
      "description": "Classifies query complexity into simple/medium/complex levels",
      "capabilities": [
        "Multi-factor complexity scoring",
        "Configurable thresholds",
        "Confidence estimation",
        "Real-time classification"
      ],
      "configuration": {
        "thresholds": {
          "simple": 0.3,
          "medium": 0.6,
          "complex": 0.9
        }
      }
    },
    "model_recommender": {
      "status": "healthy", 
      "description": "Recommends optimal models based on complexity and strategy",
      "capabilities": [
        "Multi-model routing (Ollama, OpenAI, Mistral)",
        "Cost-aware recommendations",
        "Strategy-based selection",
        "Fallback chain management"
      ],
      "configuration": {
        "strategy": "balanced",
        "model_mappings": {
          "simple": ["ollama/llama3.2:3b"],
          "medium": ["openai/gpt-3.5-turbo", "ollama/llama3.2:3b"],
          "complex": ["openai/gpt-4", "mistral/mistral-large"]
        }
      }
    }
  }
}
```

---

## Generator Service API

**Base URL**: `http://localhost:8081/api/v1`  
**Service**: Multi-model answer generation with intelligent routing

### Endpoints Overview

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| `POST` | `/generate` | Generate answer with routing | ✅ Active |
| `POST` | `/batch-generate` | Batch answer generation | ✅ Active |
| `GET` | `/models` | Available models info | ✅ Active |
| `GET` | `/status` | Service status & metrics | ✅ Active |
| `POST` | `/test-routing` | Test routing decisions | ✅ Active |

---

### POST /api/v1/generate

**Description**: Generate an answer using multi-model routing with cost optimization.

#### Request Schema

```http
POST /api/v1/generate
Content-Type: application/json

{
  "query": "What are the key advantages of RISC-V over traditional architectures?",
  "context_documents": [
    {
      "content": "RISC-V is an open-source instruction set architecture (ISA) that provides a free, open standard for processor design. Unlike proprietary architectures, RISC-V allows for customization and optimization without licensing fees.",
      "metadata": {
        "source": "risc-v-spec.pdf",
        "page": 1,
        "title": "RISC-V Overview"
      },
      "doc_id": "doc_risc_001",
      "score": 0.95
    },
    {
      "content": "Traditional architectures like x86 and ARM require licensing fees and have restrictions on modifications. RISC-V's modular design allows for custom extensions while maintaining compatibility.",
      "metadata": {
        "source": "processor-comparison.pdf", 
        "page": 3
      },
      "doc_id": "doc_comp_002",
      "score": 0.88
    }
  ],
  "options": {
    "strategy": "balanced",
    "max_cost": 0.05,
    "preferred_model": "openai/gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 500,
    "include_sources": true,
    "format_citations": true
  }
}
```

**Request Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | ✅ Yes | User query to generate answer for |
| `context_documents` | array[object] | ✅ Yes | Relevant documents for context |
| `context_documents[].content` | string | ✅ Yes | Document text content |
| `context_documents[].metadata` | object | ❌ Optional | Document metadata |
| `context_documents[].doc_id` | string | ❌ Optional | Unique document identifier |
| `context_documents[].score` | number | ❌ Optional | Relevance score (0.0-1.0) |
| `options` | object | ❌ Optional | Generation options |
| `options.strategy` | string | ❌ Optional | "cost_optimized", "balanced", "quality_first" |
| `options.max_cost` | number | ❌ Optional | Maximum cost per generation (USD) |
| `options.preferred_model` | string | ❌ Optional | Preferred model identifier |
| `options.temperature` | number | ❌ Optional | Generation temperature (0.0-2.0) |
| `options.max_tokens` | number | ❌ Optional | Maximum response tokens |
| `options.include_sources` | boolean | ❌ Optional | Include source citations |
| `options.format_citations` | boolean | ❌ Optional | Format citations as [1], [2], etc. |

#### Response Schema

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "answer": "RISC-V offers several key advantages over traditional architectures:\n\n1. **Open Source and Free**: Unlike proprietary architectures such as x86 and ARM, RISC-V is completely open-source, eliminating licensing fees and restrictions [1].\n\n2. **Customization and Flexibility**: The modular design allows developers to create custom extensions while maintaining compatibility with the base instruction set [2].\n\n3. **Cost Effectiveness**: Organizations can implement RISC-V without the significant licensing costs associated with traditional architectures.\n\n4. **Innovation Freedom**: The open nature enables rapid innovation and experimentation without legal barriers.\n\nThese advantages make RISC-V particularly attractive for custom silicon development and embedded systems where cost and flexibility are critical factors.",
  "query": "What are the key advantages of RISC-V over traditional architectures?",
  "model_used": "openai/gpt-3.5-turbo",
  "cost": 0.0023,
  "confidence": 0.92,
  "routing_decision": {
    "strategy": "balanced",
    "available_models": [
      "openai/gpt-3.5-turbo",
      "mistral/mistral-medium", 
      "ollama/llama3.2:3b"
    ],
    "selection_reason": "Best balance of cost and quality for medium complexity query",
    "fallback_used": false,
    "cost_estimate": 0.0023,
    "quality_score": 0.89
  },
  "sources": [
    {
      "doc_id": "doc_risc_001",
      "title": "RISC-V Overview",
      "citation": "[1]",
      "relevance": 0.95
    },
    {
      "doc_id": "doc_comp_002", 
      "title": "processor-comparison.pdf",
      "citation": "[2]",
      "relevance": 0.88
    }
  ],
  "processing_time": 1.23,
  "metadata": {
    "generator_version": "1.0.0",
    "timestamp": 1692633456.789,
    "request_id": "gen_456def789abc",
    "context_documents_count": 2,
    "tokens_used": {
      "prompt": 245,
      "completion": 187,
      "total": 432
    }
  }
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Generated answer with optional citations |
| `query` | string | Original query |
| `model_used` | string | Model that generated the response |
| `cost` | number | Actual generation cost (USD) |
| `confidence` | number | Answer quality confidence (0.0-1.0) |
| `routing_decision` | object | Details about model selection process |
| `sources` | array[object] | Source documents with citations |
| `processing_time` | number | Total generation time in seconds |
| `metadata` | object | Response metadata and tracking info |

---

### POST /api/v1/batch-generate

**Description**: Process multiple generation requests in batch with shared context optimization.

#### Request Schema

```http
POST /api/v1/batch-generate
Content-Type: application/json

{
  "requests": [
    {
      "query": "What is RISC-V?",
      "context_documents": [...],
      "options": {"strategy": "cost_optimized"}
    },
    {
      "query": "How does RISC-V compare to ARM?",
      "context_documents": [...],
      "options": {"strategy": "balanced"}
    }
  ],
  "batch_options": {
    "parallel_processing": true,
    "max_parallel": 3,
    "shared_context": true
  }
}
```

#### Response Schema

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "batch_id": "batch_123xyz789",
  "total_requests": 2,
  "successful_generations": 2,
  "failed_generations": 0,
  "total_processing_time": 2.45,
  "total_cost": 0.0045,
  "results": [
    {
      "index": 0,
      "query": "What is RISC-V?",
      "result": {
        "answer": "RISC-V is an open-source instruction set architecture...",
        "model_used": "ollama/llama3.2:3b",
        "cost": 0.0,
        "confidence": 0.87
      }
    },
    {
      "index": 1,
      "query": "How does RISC-V compare to ARM?",
      "result": {
        "answer": "RISC-V and ARM differ in several key aspects...",
        "model_used": "openai/gpt-3.5-turbo",
        "cost": 0.0045,
        "confidence": 0.91
      }
    }
  ]
}
```

---

### GET /api/v1/models

**Description**: Get information about available models and their capabilities.

#### Response Schema

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "available_models": {
    "ollama/llama3.2:3b": {
      "provider": "ollama",
      "model_name": "llama3.2:3b",
      "status": "available",
      "capabilities": {
        "max_tokens": 4096,
        "supports_streaming": true,
        "cost_per_1k_tokens": 0.0
      },
      "performance": {
        "avg_latency_ms": 800,
        "tokens_per_second": 45
      },
      "use_cases": ["simple_queries", "cost_sensitive"]
    },
    "openai/gpt-3.5-turbo": {
      "provider": "openai",
      "model_name": "gpt-3.5-turbo",
      "status": "available",
      "capabilities": {
        "max_tokens": 4096,
        "supports_streaming": true,
        "cost_per_1k_tokens": 0.0015
      },
      "performance": {
        "avg_latency_ms": 1200,
        "tokens_per_second": 120
      },
      "use_cases": ["general_purpose", "balanced_cost_quality"]
    },
    "mistral/mistral-medium": {
      "provider": "mistral",
      "model_name": "mistral-medium",
      "status": "available",
      "capabilities": {
        "max_tokens": 8192,
        "supports_streaming": true,
        "cost_per_1k_tokens": 0.003
      },
      "performance": {
        "avg_latency_ms": 1000,
        "tokens_per_second": 100
      },
      "use_cases": ["complex_reasoning", "quality_focused"]
    }
  },
  "routing_strategies": {
    "cost_optimized": {
      "description": "Minimize cost per query",
      "model_preferences": ["ollama/llama3.2:3b", "openai/gpt-3.5-turbo"],
      "max_cost_per_query": 0.01
    },
    "balanced": {
      "description": "Balance cost and quality",
      "model_preferences": ["openai/gpt-3.5-turbo", "mistral/mistral-medium"],
      "max_cost_per_query": 0.05
    },
    "quality_first": {
      "description": "Maximum answer quality",
      "model_preferences": ["mistral/mistral-large", "openai/gpt-4"],
      "max_cost_per_query": 0.10
    }
  },
  "health_status": {
    "total_models": 4,
    "available_models": 3,
    "unavailable_models": 1,
    "last_health_check": "2025-08-21T10:30:45Z"
  }
}
```

---

### GET /api/v1/status

**Description**: Get current status of the generator service with performance metrics.

#### Response Schema

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "service": "generator",
  "version": "1.0.0",
  "status": "healthy",
  "initialized": true,
  "uptime_seconds": 7200,
  "generator_type": "Epic1AnswerGenerator",
  "components": {
    "adaptive_router": "healthy",
    "cost_tracker": "healthy",
    "llm_adapters": "healthy",
    "prompt_builder": "healthy"
  },
  "performance": {
    "total_requests": 892,
    "successful_generations": 865,
    "failed_generations": 27,
    "avg_response_time_ms": 1340,
    "avg_cost_per_query": 0.0087,
    "model_distribution": {
      "ollama/llama3.2:3b": 0.42,
      "openai/gpt-3.5-turbo": 0.38,
      "mistral/mistral-medium": 0.20
    }
  },
  "cost_tracking": {
    "total_cost_today": 7.65,
    "daily_budget_limit": 100.0,
    "budget_utilization": 0.0765,
    "cost_alerts_enabled": true
  },
  "last_health_check": "2025-08-21T10:30:45Z"
}
```

---

### POST /api/v1/test-routing

**Description**: Test routing decisions without generating answers (cost-free testing).

#### Request Schema

```http
POST /api/v1/test-routing
Content-Type: application/json

{
  "queries": [
    "Simple question about basic concepts",
    "Complex technical analysis requiring detailed reasoning"
  ],
  "options": {
    "strategy": "balanced",
    "include_cost_estimates": true,
    "include_reasoning": true
  }
}
```

#### Response Schema

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "routing_decisions": [
    {
      "query": "Simple question about basic concepts",
      "complexity": "simple",
      "recommended_model": "ollama/llama3.2:3b",
      "strategy_applied": "balanced",
      "cost_estimate": 0.0,
      "reasoning": "Simple query routed to cost-effective local model",
      "fallback_chain": ["ollama/llama3.2:3b", "openai/gpt-3.5-turbo"]
    },
    {
      "query": "Complex technical analysis requiring detailed reasoning",
      "complexity": "complex", 
      "recommended_model": "openai/gpt-3.5-turbo",
      "strategy_applied": "balanced",
      "cost_estimate": 0.0034,
      "reasoning": "Complex query requires higher-quality model",
      "fallback_chain": ["openai/gpt-3.5-turbo", "mistral/mistral-medium", "ollama/llama3.2:3b"]
    }
  ],
  "summary": {
    "total_queries": 2,
    "avg_cost_estimate": 0.0017,
    "strategy_effectiveness": 0.91,
    "routing_confidence": 0.88
  }
}
```

---

## Common Data Models

### Query Context Object

```json
{
  "user_tier": "premium" | "free" | "enterprise",
  "max_cost": 0.05,
  "preferred_models": ["openai/gpt-3.5-turbo"],
  "domain": "technical" | "general" | "creative",
  "session_id": "session_123abc",
  "user_preferences": {
    "language": "en",
    "format": "markdown",
    "citation_style": "numeric"
  }
}
```

### Document Object

```json
{
  "content": "Document text content...",
  "metadata": {
    "source": "filename.pdf",
    "page": 1,
    "title": "Document Title",
    "author": "Author Name",
    "date": "2025-01-01"
  },
  "doc_id": "doc_unique_id",
  "score": 0.95,
  "chunk_id": "chunk_001"
}
```

### Routing Decision Object

```json
{
  "strategy": "balanced",
  "available_models": ["model1", "model2"],
  "selected_model": "model1",
  "selection_reason": "Best balance of cost and quality",
  "cost_estimate": 0.0023,
  "quality_score": 0.89,
  "fallback_used": false,
  "routing_time_ms": 12
}
```

---

## Error Handling

### Standard Error Response

All APIs return errors in a consistent format:

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Query text is required",
    "details": {
      "field": "query",
      "constraint": "min_length",
      "provided": ""
    },
    "request_id": "req_error_123",
    "timestamp": "2025-08-21T10:30:45Z"
  }
}
```

### HTTP Status Codes

| Status Code | Description | When Used |
|-------------|-------------|-----------|
| `200` | Success | Request completed successfully |
| `400` | Bad Request | Invalid request parameters |
| `401` | Unauthorized | Authentication required |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Endpoint not found |
| `422` | Validation Error | Request validation failed |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Unexpected server error |
| `503` | Service Unavailable | Service temporarily unavailable |

### Error Codes

| Error Code | Service | Description |
|------------|---------|-------------|
| `INVALID_REQUEST` | Both | Request validation failed |
| `ANALYSIS_FAILED` | Query Analyzer | Query analysis error |
| `GENERATION_FAILED` | Generator | Answer generation error |
| `MODEL_UNAVAILABLE` | Generator | Selected model not available |
| `BUDGET_EXCEEDED` | Generator | Cost budget limit reached |
| `RATE_LIMIT_EXCEEDED` | Both | Request rate limit exceeded |
| `SERVICE_UNAVAILABLE` | Both | Service temporarily down |

---

## Rate Limiting

### Current Implementation (Phase 1)

**No Rate Limiting**: Development mode allows unlimited requests

### Planned Implementation (Phase 3)

**Per-Client Rate Limiting**:

| Tier | Requests/Minute | Requests/Hour | Requests/Day |
|------|----------------|---------------|--------------|
| **Free** | 10 | 100 | 1,000 |
| **Premium** | 60 | 1,000 | 10,000 |
| **Enterprise** | 300 | 5,000 | 50,000 |

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1692634200
```

---

## Health & Monitoring

### Health Check Endpoints

All services provide standardized health endpoints:

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `/health` | Detailed health status | JSON with component status |
| `/health/live` | Kubernetes liveness probe | `{"status": "alive"}` |
| `/health/ready` | Kubernetes readiness probe | `{"status": "ready"}` |

### Metrics Endpoint

**Prometheus Metrics**: Available at `/metrics`

```
# Query Analyzer Service Metrics
query_analyzer_requests_total{endpoint="analyze",status="success"} 1524
query_analyzer_request_duration_seconds{endpoint="analyze",quantile="0.95"} 0.045
query_analyzer_complexity_total{complexity="medium"} 687

# Generator Service Metrics
generator_requests_total{endpoint="generate",status="success"} 892
generator_request_duration_seconds{endpoint="generate",quantile="0.95"} 1.34
generator_cost_dollars_total{model="openai/gpt-3.5-turbo"} 7.65
```

---

## API Usage Examples

### Complete Query Flow Example

```bash
# 1. Analyze query complexity
curl -X POST http://localhost:8080/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do transformer architectures enable parallel processing in neural networks?",
    "options": {
      "strategy": "balanced",
      "include_features": true,
      "include_cost_estimate": true
    }
  }'

# Response: complexity="complex", recommended_models=["openai/gpt-3.5-turbo"]

# 2. Generate answer with recommended model
curl -X POST http://localhost:8081/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do transformer architectures enable parallel processing in neural networks?",
    "context_documents": [
      {
        "content": "Transformer architectures use self-attention mechanisms that allow each position in a sequence to attend to all positions in the previous layer, enabling parallelization during training.",
        "metadata": {"source": "attention-paper.pdf", "page": 3}
      }
    ],
    "options": {
      "strategy": "balanced",
      "preferred_model": "openai/gpt-3.5-turbo",
      "include_sources": true
    }
  }'
```

### Batch Processing Example

```python
import requests
import json

# Batch analyze multiple queries
queries = [
    "What is machine learning?",
    "Explain quantum computing",
    "How do neural networks work?"
]

response = requests.post(
    "http://localhost:8080/api/v1/batch-analyze",
    json={
        "queries": queries,
        "options": {"strategy": "cost_optimized"}
    }
)

batch_analysis = response.json()
print(f"Processed {batch_analysis['total_queries']} queries")
print(f"Complexity distribution: {batch_analysis['complexity_distribution']}")

# Generate answers based on analysis
for result in batch_analysis['results']:
    if result.get('result'):
        complexity = result['result']['complexity']
        recommended_model = result['result']['recommended_models'][0]
        
        # Generate answer with recommended model
        gen_response = requests.post(
            "http://localhost:8081/api/v1/generate",
            json={
                "query": result['query'],
                "context_documents": [],
                "options": {
                    "preferred_model": recommended_model,
                    "strategy": "cost_optimized"
                }
            }
        )
        
        answer = gen_response.json()
        print(f"Query: {result['query']}")
        print(f"Model: {answer['model_used']}")
        print(f"Cost: ${answer['cost']:.4f}")
        print()
```

### Health Monitoring Example

```bash
#!/bin/bash
# Service health monitoring script

check_service() {
    local service_name=$1
    local port=$2
    
    echo "Checking $service_name..."
    
    # Health check
    health=$(curl -s http://localhost:$port/health)
    status=$(echo $health | jq -r '.status')
    
    if [ "$status" = "healthy" ]; then
        echo "✅ $service_name is healthy"
        
        # Get performance metrics
        uptime=$(echo $health | jq -r '.uptime_seconds')
        echo "   Uptime: ${uptime}s"
        
        if [ "$service_name" = "Query Analyzer" ]; then
            requests=$(echo $health | jq -r '.performance.total_requests // 0')
            avg_time=$(echo $health | jq -r '.performance.avg_response_time_ms // 0')
            echo "   Requests: $requests, Avg time: ${avg_time}ms"
        elif [ "$service_name" = "Generator" ]; then
            cost=$(echo $health | jq -r '.cost_tracking.total_cost_today // 0')
            echo "   Total cost today: $${cost}"
        fi
    else
        echo "❌ $service_name is unhealthy: $status"
    fi
    echo
}

# Check all services
check_service "Query Analyzer" 8080
check_service "Generator" 8081
```

---

## SDK & Client Libraries

### Python SDK (Planned)

```python
from epic8_client import Epic8Client

# Initialize client
client = Epic8Client(
    query_analyzer_url="http://localhost:8080",
    generator_url="http://localhost:8081",
    api_key="your-api-key"  # Future authentication
)

# Analyze query
analysis = await client.analyze_query(
    query="What is machine learning?",
    strategy="balanced"
)

# Generate answer
answer = await client.generate_answer(
    query="What is machine learning?",
    context_documents=documents,
    routing_decision=analysis.routing_decision
)

print(f"Answer: {answer.text}")
print(f"Cost: ${answer.cost:.4f}")
print(f"Model: {answer.model_used}")
```

### JavaScript SDK (Planned)

```javascript
import { Epic8Client } from '@epic8/client';

const client = new Epic8Client({
    queryAnalyzerUrl: 'http://localhost:8080',
    generatorUrl: 'http://localhost:8081',
    apiKey: 'your-api-key'
});

// Complete query processing
const result = await client.processQuery({
    query: 'What is machine learning?',
    contextDocuments: documents,
    options: {
        strategy: 'balanced',
        maxCost: 0.05
    }
});

console.log(`Answer: ${result.answer}`);
console.log(`Cost: $${result.cost}`);
console.log(`Model: ${result.modelUsed}`);
```

---

## Conclusion

Epic 8 APIs provide comprehensive interfaces for cloud-native multi-model RAG operations with:

- **✅ RESTful Design**: HTTP-based APIs with JSON communication
- **✅ OpenAPI Documentation**: Complete API specifications with Swagger UI
- **✅ Microservices Architecture**: Independent, scalable service endpoints
- **✅ Production Features**: Health checks, metrics, error handling
- **✅ Swiss Engineering**: Precision, reliability, and comprehensive documentation

The APIs are designed for easy integration, testing, and production deployment, supporting the transition from monolithic to cloud-native architecture while maintaining operational excellence.

**Current Status**: Phase 1 APIs operational and ready for Phase 2 integration with additional services.

---

*This API reference provides complete documentation for Epic 8 Phase 1 implementation with forward compatibility for planned phases.*