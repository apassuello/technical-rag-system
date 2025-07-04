#!/usr/bin/env python3
"""
Test different HuggingFace API endpoints to find what works
"""

import os
import requests
import time

def test_api_endpoints():
    """Test various API endpoint formats."""
    
    print("🔍 Testing HuggingFace API Endpoints\n")
    
    # Get token
    HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
    if HF_TOKEN:
        print(f"✅ Using token: {HF_TOKEN[:8]}...")
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    else:
        print("⚠️ No token found")
        headers = {}
    
    print("\n" + "="*60 + "\n")
    
    # Test different endpoint formats
    test_cases = [
        # Standard inference API
        {
            "name": "Standard Inference API - GPT2",
            "url": "https://api-inference.huggingface.co/models/gpt2",
            "payload": {"inputs": "Hello world"},
            "method": "POST"
        },
        {
            "name": "Standard Inference API - BART",
            "url": "https://api-inference.huggingface.co/models/facebook/bart-base",
            "payload": {"inputs": "Summarize: The quick brown fox jumps over the lazy dog."},
            "method": "POST"
        },
        # Test GET request for model info
        {
            "name": "Model Info - GPT2",
            "url": "https://huggingface.co/api/models/gpt2",
            "payload": None,
            "method": "GET"
        },
        # Test with different model IDs
        {
            "name": "Without org prefix",
            "url": "https://api-inference.huggingface.co/models/bart-base",
            "payload": {"inputs": "Test"},
            "method": "POST"
        },
        # Test specific tasks
        {
            "name": "Text Generation Pipeline",
            "url": "https://api-inference.huggingface.co/pipeline/text-generation/gpt2",
            "payload": {"inputs": "Hello"},
            "method": "POST"
        },
    ]
    
    for test in test_cases:
        print(f"📋 {test['name']}")
        print(f"URL: {test['url']}")
        
        try:
            if test['method'] == 'POST':
                response = requests.post(
                    test['url'], 
                    headers=headers, 
                    json=test['payload'],
                    timeout=10
                )
            else:
                response = requests.get(
                    test['url'],
                    headers=headers,
                    timeout=10
                )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Success!")
                if test['method'] == 'POST':
                    result = response.json()
                    print(f"Response type: {type(result)}")
                    print(f"Response preview: {str(result)[:150]}...")
            else:
                print(f"❌ Failed")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"💥 Exception: {str(e)}")
        
        print("\n" + "-"*60 + "\n")
        time.sleep(0.5)
    
    # Test the models that are definitely available
    print("📋 Testing models from HuggingFace Models page...\n")
    
    # These are popular models that should be available
    popular_models = [
        "bert-base-uncased",
        "gpt2",
        "distilbert-base-uncased",
        "facebook/bart-base",
        "t5-small",
        "roberta-base",
    ]
    
    for model in popular_models:
        url = f"https://api-inference.huggingface.co/models/{model}"
        print(f"Testing {model}...")
        
        # Try a simple request
        response = requests.post(
            url,
            headers=headers,
            json={"inputs": "Test input"},
            timeout=10
        )
        
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ Available!")
        elif response.status_code == 503:
            print(f"  ⏳ Loading (might work after warmup)")
        else:
            print(f"  ❌ Not available: {response.text[:50]}")
        
        time.sleep(0.5)


if __name__ == "__main__":
    test_api_endpoints()