FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Ollama requirements
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    software-properties-common \
    git \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set Python path to include the app directory
ENV PYTHONPATH="/app:/app/src:$PYTHONPATH"

# Set HOME to app directory to avoid root directory writes
ENV HOME="/app"
ENV USER="appuser"

# Set Streamlit config directory to writable location
ENV STREAMLIT_CONFIG_DIR="/app/.streamlit"

# Disable Streamlit usage statistics to avoid permission issues
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS="false"

# Set HuggingFace cache directory to writable location
ENV HF_HOME="/app/.cache"
ENV SENTENCE_TRANSFORMERS_HOME="/app/.cache/sentence-transformers"

# Download NLTK data if needed (for text processing)
RUN python -c "import nltk; nltk.download('punkt', quiet=True)" || true

# Pre-download the embedding model to avoid runtime permission issues
RUN python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/multi-qa-MiniLM-L6-cos-v1'); print('Model downloaded successfully')" || echo "Model download failed, will retry at runtime"

# Create necessary directories with proper permissions
RUN mkdir -p .streamlit && \
    mkdir -p .cache && \
    mkdir -p .cache/transformers && \
    mkdir -p .cache/sentence-transformers && \
    mkdir -p temp_uploads && \
    chmod -R 777 .cache && \
    chmod 777 temp_uploads && \
    touch .gitconfig && \
    chmod 666 .gitconfig

# Expose Streamlit port
EXPOSE 8501

# Health check for container monitoring
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Pre-pull the Ollama model during build (optional - for faster startup)
# RUN ollama serve & sleep 5 && ollama pull llama3.2:3b && pkill ollama

# Expose ports for both Streamlit and Ollama
EXPOSE 8501 11434

# Create directories with proper permissions for any user
RUN mkdir -p /app/.ollama && \
    mkdir -p /app/.ollama/models && \
    chmod -R 777 /app/.ollama

# Set Ollama environment variables to use app directory
ENV OLLAMA_MODELS=/app/.ollama/models
ENV OLLAMA_HOST=0.0.0.0:11434

# Ensure Ollama can write to its directories
RUN chmod -R 777 /app

# Create startup Python script
COPY startup.py /app/startup.py

# Run startup script that handles both Ollama and Streamlit
ENTRYPOINT ["python", "/app/startup.py"]