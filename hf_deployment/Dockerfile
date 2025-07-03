FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Make startup script executable
RUN chmod +x start_app.sh

# Set Python path to include the app directory
ENV PYTHONPATH="/app:/app/src:$PYTHONPATH"

# Set Streamlit config directory to writable location
ENV STREAMLIT_CONFIG_DIR="/tmp/.streamlit"

# Download NLTK data if needed (for text processing)
RUN python -c "import nltk; nltk.download('punkt', quiet=True)" || true

# Create necessary directories with proper permissions
RUN mkdir -p /app/.streamlit && \
    mkdir -p /tmp/.streamlit && \
    chmod 777 /tmp/.streamlit

# Expose Streamlit port
EXPOSE 8501

# Health check for container monitoring
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run startup script that handles Ollama + Streamlit
ENTRYPOINT ["./start_app.sh"]