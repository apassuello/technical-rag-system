#!/bin/bash
set -e

echo "🚀 Starting Technical RAG Assistant..."

# Start Ollama service in background
echo "📦 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
sleep 5

# Check if model exists, if not download it
echo "🔍 Checking for Llama 3.2 model..."
if ! ollama list | grep -q "llama3.2:3b"; then
    echo "⬇️  Downloading Llama 3.2 (3B) model (this may take a few minutes)..."
    ollama pull llama3.2:3b
    echo "✅ Model downloaded successfully!"
else
    echo "✅ Llama 3.2 model already available!"
fi

# Verify model is ready
echo "🔧 Verifying model availability..."
if ollama list | grep -q "llama3.2:3b"; then
    echo "✅ Ollama and Llama 3.2 ready!"
else
    echo "❌ Model verification failed!"
    exit 1
fi

# Start Streamlit app
echo "🌟 Starting Streamlit application..."
exec streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false