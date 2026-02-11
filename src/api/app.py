"""
Single-process RAG API server.

Wraps PlatformOrchestrator as a FastAPI application.
Run: uvicorn src.api.app:app --port 8000
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.core.platform_orchestrator import PlatformOrchestrator

logger = logging.getLogger(__name__)

# --- Request / Response schemas ---

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    k: int = Field(5, ge=1, le=50)

class SourceDoc(BaseModel):
    title: str
    content: str
    score: Optional[float] = None

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[SourceDoc]
    metadata: Dict[str, Any] = {}

class HealthResponse(BaseModel):
    status: str
    components: Dict[str, Any] = {}

# --- App lifecycle ---

_orchestrator: Optional[PlatformOrchestrator] = None

def _resolve_config() -> Path:
    """Resolve config path from env or default."""
    import os
    config_name = os.environ.get("RAG_CONFIG", "config/local.yaml")
    path = Path(config_name)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    return path

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _orchestrator
    config_path = _resolve_config()
    logger.info(f"Initializing PlatformOrchestrator from {config_path}")
    _orchestrator = PlatformOrchestrator(config_path=config_path)
    _orchestrator.initialize()
    yield
    _orchestrator = None

app = FastAPI(
    title="RAG System API",
    version="0.1.0",
    lifespan=lifespan,
)

# --- Endpoints ---

@app.get("/health", response_model=HealthResponse)
async def health():
    if _orchestrator is None:
        raise HTTPException(503, "System not initialized")
    info = _orchestrator.get_system_health()
    return HealthResponse(
        status=info.get("status", "unknown"),
        components=info.get("components", {}),
    )

@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    if _orchestrator is None:
        raise HTTPException(503, "System not initialized")
    try:
        answer = _orchestrator.process_query(req.query, k=req.k)
        return QueryResponse(
            answer=answer.text,
            confidence=answer.confidence,
            sources=[
                SourceDoc(
                    title=getattr(doc, "title", ""),
                    content=doc.content[:500],
                    score=getattr(doc, "score", None),
                )
                for doc in answer.sources
            ],
            metadata=answer.metadata or {},
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(500, str(e))
