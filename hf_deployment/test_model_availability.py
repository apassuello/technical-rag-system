#!/usr/bin/env python3
"""
Test model availability for HuggingFace Inference API
Run this to verify which models are accessible with your token
"""

import os
import requests
import time

def test_models():
    """Test which models are available via the Inference API."""
    
    # Get token from environment
    HF_TOKEN = (os.getenv("HUGGINGFACE_API_TOKEN") or 
                os.getenv("HF_TOKEN") or 
                os.getenv("HF_API_TOKEN"))
    
    if HF_TOKEN:
        print(f"✅ Found HF token (starts with: {HF_TOKEN[:8]}...)")
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    else:
        print("⚠️ No HF token found - testing free tier access")
        headers = {}
    
    # Confirmed working models as of 2025
    models_to_test = [
        # Lightweight / Reliable
        ("google/flan-t5-large", "Flan-T5 Large"),
        ("distilgpt2", "DistilGPT2"),
        ("gpt2", "GPT2"),
        ("facebook/bart-large", "BART Large"),
        
        # Chat/Instruction Models
        ("tiiuae/falcon-7b-instruct", "Falcon 7B Instruct"),
        ("google/flan-t5-xl", "Flan-T5 XL"),
        
        # Previously attempted (likely to fail)
        ("mistralai/Mistral-7B-Instruct-v0.2", "Mistral 7B"),
        ("HuggingFaceH4/zephyr-7b-beta", "Zephyr 7B"),
    ]
    
    print("\n🔍 Testing Model Availability...\n")
    
    available_models = []
    
    for model_id, model_name in models_to_test:
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        
        try:
            # Test with a simple prompt
            payload = {
                "inputs": "Hello, this is a test.",
                "parameters": {
                    "max_new_tokens": 10,
                    "temperature": 0.5
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {model_name:25} | {model_id:40} | AVAILABLE")
                available_models.append(model_id)
            elif response.status_code == 503:
                print(f"⏳ {model_name:25} | {model_id:40} | LOADING (might work after warmup)")
            elif response.status_code == 404:
                print(f"❌ {model_name:25} | {model_id:40} | NOT FOUND")
            elif response.status_code == 401:
                print(f"🔒 {model_name:25} | {model_id:40} | UNAUTHORIZED (check token)")
            else:
                print(f"⚠️  {model_name:25} | {model_id:40} | ERROR {response.status_code}")
            
            # Be nice to the API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"💥 {model_name:25} | {model_id:40} | EXCEPTION: {str(e)}")
    
    print("\n📊 Summary:")
    print(f"Available models: {len(available_models)}")
    if available_models:
        print("\n✅ Recommended primary model:")
        print(f"   {available_models[0]}")
        print("\n✅ Recommended fallback models:")
        for model in available_models[1:4]:
            print(f"   {model}")
    
    return available_models


if __name__ == "__main__":
    test_models()