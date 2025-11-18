# Phase 2 Deployment Guide

**Epic 5**: Tool & Function Calling for RAG System
**Phase**: Phase 2 - Agent Orchestration & Query Planning
**Version**: 1.0
**Date**: November 18, 2025

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Environment Variables](#environment-variables)
5. [Production Settings](#production-settings)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Cost Management](#cost-management)
8. [Security Considerations](#security-considerations)
9. [Scaling Recommendations](#scaling-recommendations)
10. [Deployment Checklist](#deployment-checklist)

---

## Prerequisites

### System Requirements

**Hardware**:
- CPU: 4+ cores recommended
- RAM: 8GB minimum, 16GB+ recommended
- Storage: 10GB+ for models and indices

**Operating System**:
- Linux (Ubuntu 20.04+, CentOS 8+, Debian 11+)
- macOS 12+ (development)
- Windows 10/11 with WSL2 (development)

**Python**:
- Python 3.9, 3.10, or 3.11
- `pip` and `venv` installed

---

### Dependencies

**Core Dependencies**:
```txt
# requirements.txt
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-anthropic>=0.1.0
openai>=1.0.0
anthropic>=0.18.0
pydantic>=2.0.0
typing-extensions>=4.0.0
```

**Phase 1 Dependencies** (inherited):
```txt
# From Epic 5 Phase 1
torch>=2.0.0
transformers>=4.30.0
sentence-transformers>=2.2.0
faiss-cpu>=1.7.4
PyMuPDF>=1.22.0
```

**Optional Dependencies**:
```txt
# For production monitoring
prometheus-client>=0.16.0
opentelemetry-api>=1.15.0
opentelemetry-sdk>=1.15.0
```

---

### API Keys

**Required**:
- OpenAI API key (for GPT models) OR
- Anthropic API key (for Claude models)

**Optional**:
- Monitoring service API keys (DataDog, New Relic, etc.)

---

## Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd rag-portfolio/project-1-technical-rag
```

### Step 2: Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install Phase 1 dependencies
pip install torch transformers sentence-transformers faiss-cpu PyMuPDF

# Install Phase 2 dependencies
pip install langchain langchain-openai langchain-anthropic openai anthropic

# Install all project dependencies
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
# Test imports
python -c "
from src.components.query_processors import IntelligentQueryProcessor
from src.components.query_processors.agents import ReActAgent, QueryAnalyzer
print('✓ Phase 2 components imported successfully')
"
```

---

## Configuration

### Configuration Files

Create configuration directory:

```bash
mkdir -p config/production
```

### Agent Configuration (`config/production/agent.yaml`)

```yaml
# Agent configuration for production
agent:
  llm_provider: "openai"  # or "anthropic"
  llm_model: "gpt-4-turbo"
  temperature: 0.7
  max_tokens: 2048
  max_iterations: 10
  max_execution_time: 300  # 5 minutes
  early_stopping: "force"
  verbose: false  # Disable in production

# Tool configuration
tools:
  calculator:
    enabled: true
  document_search:
    enabled: true
    index_path: "data/indices"
    top_k: 5
  code_analyzer:
    enabled: true
    max_file_size: 50000

# Memory configuration
memory:
  conversation:
    max_messages: 100
  working:
    enabled: true
```

### Processor Configuration (`config/production/processor.yaml`)

```yaml
# Intelligent query processor configuration
processor:
  use_agent_by_default: true
  complexity_threshold: 0.7
  max_agent_cost: 0.10  # $0.10 per query
  enable_planning: true
  enable_parallel_execution: true

# Routing configuration
routing:
  force_rag_patterns:  # Always use RAG for these
    - "^What is"
    - "^Define"
    - "^Explain"
  force_agent_patterns:  # Always use agent for these
    - "Calculate"
    - "Analyze code"
    - "Search.*and.*analyze"
```

### Logging Configuration (`config/production/logging.yaml`)

```yaml
# Logging configuration
logging:
  version: 1
  disable_existing_loggers: false

  formatters:
    standard:
      format: "[%(asctime)s] %(levelname)s [%(name)s] %(message)s"
      datefmt: "%Y-%m-%d %H:%M:%S"
    json:
      class: pythonjsonlogger.jsonlogger.JsonFormatter
      format: "%(asctime)s %(name)s %(levelname)s %(message)s"

  handlers:
    console:
      class: logging.StreamHandler
      level: INFO
      formatter: standard
      stream: ext://sys.stdout

    file:
      class: logging.handlers.RotatingFileHandler
      level: INFO
      formatter: json
      filename: logs/rag-system.log
      maxBytes: 10485760  # 10MB
      backupCount: 10

    error_file:
      class: logging.handlers.RotatingFileHandler
      level: ERROR
      formatter: json
      filename: logs/rag-system-errors.log
      maxBytes: 10485760
      backupCount: 10

  loggers:
    src.components.query_processors:
      level: INFO
      handlers: [console, file, error_file]
      propagate: false

    src.components.query_processors.agents:
      level: INFO
      handlers: [console, file, error_file]
      propagate: false

  root:
    level: INFO
    handlers: [console, file]
```

---

## Environment Variables

### Required Variables

Create `.env` file:

```bash
# LLM API Keys (choose one)
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...

# Application settings
ENVIRONMENT=production
LOG_LEVEL=INFO

# Data paths
DATA_DIR=/path/to/data
INDEX_DIR=/path/to/data/indices
CACHE_DIR=/path/to/cache

# Performance settings
MAX_WORKERS=4
QUERY_TIMEOUT=300
```

### Optional Variables

```bash
# Monitoring
PROMETHEUS_PORT=9090
METRICS_ENABLED=true

# Cost limits
MAX_DAILY_COST=10.00  # $10 per day
MAX_QUERY_COST=0.10  # $0.10 per query

# Feature flags
ENABLE_AGENT=true
ENABLE_PLANNING=true
ENABLE_CACHING=true

# Database (if using)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rag_system
DB_USER=rag_user
DB_PASSWORD=secure_password
```

### Loading Environment Variables

```python
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Access variables
openai_key = os.getenv("OPENAI_API_KEY")
environment = os.getenv("ENVIRONMENT", "development")
max_workers = int(os.getenv("MAX_WORKERS", "4"))
```

---

## Production Settings

### Production Initialization Script

Create `scripts/production/initialize.py`:

```python
"""Initialize production RAG system with Phase 2 agent capabilities."""

import os
import logging
from dotenv import load_dotenv
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from src.components.query_processors import IntelligentQueryProcessor
from src.components.query_processors.agents import ReActAgent, QueryAnalyzer
from src.components.query_processors.agents.memory import ConversationMemory
from src.components.query_processors.agents.models import (
    AgentConfig,
    ProcessorConfig
)
from src.components.query_processors.tools.implementations import (
    CalculatorTool,
    DocumentSearchTool,
    CodeAnalyzerTool
)

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)


def create_llm():
    """Create LLM instance based on environment."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("LLM_MODEL", "gpt-4-turbo")

        logger.info(f"Creating OpenAI LLM: {model}")
        return ChatOpenAI(
            model=model,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            api_key=api_key,
            max_retries=3
        )

    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model = os.getenv("LLM_MODEL", "claude-3-sonnet-20240229")

        logger.info(f"Creating Anthropic LLM: {model}")
        return ChatAnthropic(
            model=model,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            api_key=api_key,
            max_retries=3
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def create_tools():
    """Create tool instances."""
    logger.info("Creating tools")

    tools = []

    # Calculator tool
    if os.getenv("ENABLE_CALCULATOR", "true").lower() == "true":
        tools.append(CalculatorTool())
        logger.info("  ✓ Calculator tool enabled")

    # Document search tool
    if os.getenv("ENABLE_DOCUMENT_SEARCH", "true").lower() == "true":
        index_path = os.getenv("INDEX_DIR", "data/indices")
        tools.append(DocumentSearchTool(index_path=index_path))
        logger.info(f"  ✓ Document search tool enabled (index: {index_path})")

    # Code analyzer tool
    if os.getenv("ENABLE_CODE_ANALYZER", "true").lower() == "true":
        tools.append(CodeAnalyzerTool())
        logger.info("  ✓ Code analyzer tool enabled")

    return tools


def create_agent(llm, tools):
    """Create ReAct agent."""
    logger.info("Creating ReAct agent")

    # Memory
    memory = ConversationMemory(
        max_messages=int(os.getenv("MAX_CONVERSATION_MESSAGES", "100"))
    )

    # Agent config
    config = AgentConfig(
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        llm_model=os.getenv("LLM_MODEL", "gpt-4-turbo"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("MAX_TOKENS", "2048")),
        max_iterations=int(os.getenv("MAX_ITERATIONS", "10")),
        max_execution_time=int(os.getenv("MAX_EXECUTION_TIME", "300")),
        verbose=os.getenv("VERBOSE", "false").lower() == "true"
    )

    # Create agent
    agent = ReActAgent(llm, tools, memory, config)
    logger.info("  ✓ Agent created")

    return agent


def create_processor(retriever, generator, agent):
    """Create intelligent query processor."""
    logger.info("Creating intelligent query processor")

    # Processor config
    config = ProcessorConfig(
        use_agent_by_default=os.getenv("USE_AGENT", "true").lower() == "true",
        complexity_threshold=float(os.getenv("COMPLEXITY_THRESHOLD", "0.7")),
        max_agent_cost=float(os.getenv("MAX_AGENT_COST", "0.10")),
        enable_planning=os.getenv("ENABLE_PLANNING", "true").lower() == "true",
        enable_parallel_execution=os.getenv("ENABLE_PARALLEL", "true").lower() == "true"
    )

    # Create processor
    processor = IntelligentQueryProcessor(
        retriever=retriever,
        generator=generator,
        agent=agent,
        query_analyzer=QueryAnalyzer(),
        config=config
    )

    logger.info("  ✓ Processor created")
    return processor


def initialize_production_system(retriever, generator):
    """
    Initialize complete production system.

    Args:
        retriever: Document retriever instance
        generator: Answer generator instance

    Returns:
        IntelligentQueryProcessor ready for production use
    """
    logger.info("="*60)
    logger.info("Initializing Production RAG System (Phase 2)")
    logger.info("="*60)

    # Create components
    llm = create_llm()
    tools = create_tools()
    agent = create_agent(llm, tools)
    processor = create_processor(retriever, generator, agent)

    logger.info("="*60)
    logger.info("Production system initialized successfully")
    logger.info("="*60)

    return processor


# Example usage
if __name__ == "__main__":
    # Assume retriever and generator are created elsewhere
    from src.components.retrievers import create_retriever
    from src.components.generators import create_generator

    retriever = create_retriever()
    generator = create_generator()

    processor = initialize_production_system(retriever, generator)

    # Test query
    test_query = "What is machine learning?"
    answer = processor.process(test_query)
    print(f"\nTest Query: {test_query}")
    print(f"Answer: {answer.answer}")
    print(f"Routing: {answer.metadata.get('routing_decision')}")
```

---

## Monitoring and Logging

### Prometheus Metrics

Create `src/monitoring/metrics.py`:

```python
"""Prometheus metrics for Phase 2."""

from prometheus_client import Counter, Histogram, Gauge
import time

# Request counters
queries_total = Counter(
    'rag_queries_total',
    'Total number of queries processed',
    ['routing_decision', 'query_type']
)

# Latency histograms
query_latency = Histogram(
    'rag_query_latency_seconds',
    'Query processing latency',
    ['routing_decision']
)

# Cost tracking
query_cost = Histogram(
    'rag_query_cost_dollars',
    'Query processing cost in USD',
    ['routing_decision']
)

# Agent-specific metrics
agent_iterations = Histogram(
    'rag_agent_iterations',
    'Number of agent reasoning iterations'
)

agent_tool_calls = Counter(
    'rag_agent_tool_calls_total',
    'Total agent tool calls',
    ['tool_name']
)

# Current state
active_queries = Gauge(
    'rag_active_queries',
    'Number of currently active queries'
)


# Instrumentation decorator
def monitor_query(func):
    """Decorator to monitor query processing."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        active_queries.inc()

        try:
            result = func(*args, **kwargs)

            # Record metrics
            elapsed = time.time() - start_time
            routing = result.metadata.get('routing_decision', 'unknown')
            query_type = result.metadata.get('query_type', 'unknown')

            queries_total.labels(
                routing_decision=routing,
                query_type=query_type
            ).inc()

            query_latency.labels(routing_decision=routing).observe(elapsed)

            if 'total_cost' in result.metadata:
                query_cost.labels(routing_decision=routing).observe(
                    result.metadata['total_cost']
                )

            if routing == 'agent_system':
                reasoning_steps = result.metadata.get('reasoning_trace', [])
                agent_iterations.observe(len(reasoning_steps))

                for tool in result.metadata.get('tools_used', []):
                    agent_tool_calls.labels(tool_name=tool).inc()

            return result

        finally:
            active_queries.dec()

    return wrapper
```

### Health Check Endpoint

```python
"""Health check for production deployment."""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class HealthResponse(BaseModel):
    status: str
    components: dict


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    # Check processor
    processor_status = processor.health_check()

    return {
        "status": "healthy" if processor_status.is_healthy else "unhealthy",
        "components": {
            "processor": "healthy" if processor_status.is_healthy else "unhealthy",
            "retriever": "healthy",
            "generator": "healthy",
            "agent": "healthy"
        }
    }
```

---

## Cost Management

### Cost Tracking

```python
"""Cost tracking and alerting."""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CostTracker:
    """Track and manage query costs."""

    def __init__(self, max_daily_cost: float = 10.0, max_query_cost: float = 0.10):
        self.max_daily_cost = max_daily_cost
        self.max_query_cost = max_query_cost
        self.daily_costs: Dict[str, float] = {}

    def record_cost(self, cost: float, metadata: Dict[str, Any]) -> None:
        """Record query cost."""
        today = datetime.now().strftime("%Y-%m-%d")

        if today not in self.daily_costs:
            self.daily_costs[today] = 0.0

        self.daily_costs[today] += cost

        # Alert if thresholds exceeded
        if cost > self.max_query_cost:
            logger.warning(
                f"Query cost ${cost:.4f} exceeds limit ${self.max_query_cost:.4f}"
            )

        if self.daily_costs[today] > self.max_daily_cost:
            logger.error(
                f"Daily cost ${self.daily_costs[today]:.4f} exceeds limit "
                f"${self.max_daily_cost:.4f}"
            )

    def get_daily_cost(self) -> float:
        """Get today's total cost."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.daily_costs.get(today, 0.0)

    def should_allow_query(self) -> bool:
        """Check if query should be allowed based on budget."""
        return self.get_daily_cost() < self.max_daily_cost


# Global cost tracker
cost_tracker = CostTracker(
    max_daily_cost=float(os.getenv("MAX_DAILY_COST", "10.0")),
    max_query_cost=float(os.getenv("MAX_QUERY_COST", "0.10"))
)
```

---

## Security Considerations

### 1. API Key Security

```python
# ✓ DO: Use environment variables
api_key = os.getenv("OPENAI_API_KEY")

# ✗ DON'T: Hardcode keys
api_key = "sk-..."  # NEVER DO THIS
```

### 2. Input Validation

```python
def validate_query(query: str) -> bool:
    """Validate user query."""
    # Length check
    if len(query) > 10000:
        raise ValueError("Query too long")

    # Content check (no code injection)
    dangerous_patterns = ["import ", "exec(", "eval(", "__"]
    if any(pattern in query.lower() for pattern in dangerous_patterns):
        raise ValueError("Invalid query content")

    return True
```

### 3. Rate Limiting

```python
from functools import wraps
from time import time

def rate_limit(max_calls: int, period: int):
    """Rate limiting decorator."""
    calls = []

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time()
            # Remove old calls
            calls[:] = [c for c in calls if c > now - period]

            if len(calls) >= max_calls:
                raise Exception("Rate limit exceeded")

            calls.append(now)
            return func(*args, **kwargs)

        return wrapper
    return decorator


@rate_limit(max_calls=100, period=60)  # 100 queries per minute
def process_query(query: str):
    return processor.process(query)
```

### 4. Secure Configuration

```bash
# Set restrictive file permissions
chmod 600 .env
chmod 600 config/production/*.yaml

# Use secrets management in production
# AWS Secrets Manager, HashiCorp Vault, etc.
```

---

## Scaling Recommendations

### Horizontal Scaling

```python
"""Multi-worker deployment with load balancing."""

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List

class LoadBalancedProcessor:
    """Load-balanced query processor."""

    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.executor = ThreadPoolExecutor(max_workers=num_workers)
        self.processors = [
            initialize_production_system(retriever, generator)
            for _ in range(num_workers)
        ]

    def process_batch(self, queries: List[str]):
        """Process queries in parallel."""
        futures = []
        for i, query in enumerate(queries):
            processor = self.processors[i % self.num_workers]
            future = self.executor.submit(processor.process, query)
            futures.append(future)

        return [f.result() for f in futures]
```

### Caching Strategy

```python
"""Response caching for common queries."""

from functools import lru_cache
import hashlib

class CachedProcessor:
    """Processor with response caching."""

    def __init__(self, processor, cache_size: int = 1000):
        self.processor = processor
        self.cache_size = cache_size

    @lru_cache(maxsize=1000)
    def _process_cached(self, query_hash: str, query: str):
        """Cache wrapper."""
        return self.processor.process(query)

    def process(self, query: str):
        """Process with caching."""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return self._process_cached(query_hash, query)
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All dependencies installed
- [ ] API keys configured
- [ ] Environment variables set
- [ ] Configuration files created
- [ ] Logs directory created
- [ ] Data/indices available
- [ ] Security review completed
- [ ] Performance testing done

### Deployment

- [ ] Application deployed
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Logging working
- [ ] Cost tracking enabled
- [ ] Rate limiting active
- [ ] Backup strategy in place

### Post-Deployment

- [ ] Test queries executed
- [ ] Metrics validated
- [ ] Alerts configured
- [ ] Documentation updated
- [ ] Team trained
- [ ] Rollback plan ready

---

**Document Version**: 1.0
**Last Updated**: November 18, 2025
**Status**: ✅ Complete
