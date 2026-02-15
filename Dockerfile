FROM python:3.11-slim

# NOTE: This container requires a llama-server sidecar providing an
# OpenAI-compatible API at the URL specified by LLM_BASE_URL (default:
# http://localhost:11434/v1). Run with docker-compose or provide the
# sidecar separately.

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/

ENV RAG_CONFIG=config/local.yaml

EXPOSE 8000
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
