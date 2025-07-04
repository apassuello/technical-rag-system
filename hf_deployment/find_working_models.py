#!/usr/bin/env python3
"""
Find models that actually work on HuggingFace Inference API
"""

import os
import requests
import time

def find_working_models():
    """Test a variety of models to find what works."""
    
    print("🔍 Finding Working Models on HuggingFace Inference API\n")
    
    # Get token
    HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    
    # Models to test - covering different tasks
    models_to_test = {
        # Text Generation
        "gpt2": "Hello world",
        "distilgpt2": "Hello world",
        "EleutherAI/gpt-neo-125M": "Hello world",
        "microsoft/DialoGPT-small": "Hello",
        
        # Text2Text Generation (T5 family)
        "t5-small": "translate English to French: Hello world",
        "t5-base": "summarize: The quick brown fox jumps over the lazy dog.",
        "google/flan-t5-small": "What is machine learning?",
        "google/flan-t5-base": "Explain AI in simple terms.",
        
        # Summarization
        "facebook/bart-base": "The quick brown fox jumps over the lazy dog. This is a test.",
        "facebook/bart-large-cnn": "The quick brown fox jumps over the lazy dog. This is a test.",
        "sshleifer/distilbart-cnn-12-6": "The quick brown fox jumps over the lazy dog.",
        
        # Fill-mask models (BERT family)
        "bert-base-uncased": "The capital of France is [MASK].",
        "distilbert-base-uncased": "Hello [MASK]!",
        "roberta-base": "Hello <mask>!",
        
        # Sentence Transformers
        "sentence-transformers/all-MiniLM-L6-v2": "This is a test sentence.",
        
        # Question Answering
        "deepset/roberta-base-squad2": {"question": "What is AI?", "context": "AI is artificial intelligence."},
        "distilbert-base-uncased-distilled-squad": {"question": "What is AI?", "context": "AI is artificial intelligence."},
    }
    
    working_models = {}
    
    for model_id, test_input in models_to_test.items():
        print(f"\n🤖 Testing: {model_id}")
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        
        # Prepare payload
        if isinstance(test_input, dict):
            payload = {"inputs": test_input}
        else:
            payload = {"inputs": test_input}
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ WORKS! Response type: {type(result)}")
                
                # Show sample output
                if isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], dict):
                        preview = str(result[0])[:100]
                    else:
                        preview = str(result)[:100]
                else:
                    preview = str(result)[:100]
                print(f"   Preview: {preview}...")
                
                working_models[model_id] = {
                    "status": "working",
                    "response_type": str(type(result)),
                    "test_input": test_input
                }
                
            elif response.status_code == 503:
                print(f"   ⏳ Model loading")
                working_models[model_id] = {"status": "loading"}
            else:
                print(f"   ❌ Failed: {response.text[:100]}")
                
        except Exception as e:
            print(f"   💥 Exception: {str(e)[:100]}")
        
        time.sleep(0.5)  # Be nice to the API
    
    # Summary
    print("\n" + "="*60)
    print("\n📊 SUMMARY - Working Models:\n")
    
    for model, info in working_models.items():
        if info.get("status") == "working":
            print(f"✅ {model}")
            print(f"   Input: {info['test_input']}")
            print(f"   Response type: {info['response_type']}")
            print()
    
    print("\n🎯 Recommended for RAG:")
    rag_suitable = [m for m in working_models if working_models[m].get("status") == "working" and 
                    any(x in m for x in ["t5", "bart", "gpt", "dialog"])]
    for model in rag_suitable:
        print(f"   - {model}")


if __name__ == "__main__":
    find_working_models()