#!/usr/bin/env python3
"""
Test HuggingFace API token and model availability
Run this locally to verify your setup before deploying
"""

import os
import requests
import json
import time

def test_token_and_models():
    """Test HF token and model availability."""
    
    print("🔍 Testing HuggingFace API Setup\n")
    
    # Try to get token from environment
    HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_API_TOKEN")
    
    if HF_TOKEN:
        print(f"✅ Found HF token (starts with: {HF_TOKEN[:8]}...)")
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    else:
        print("⚠️ No HF token found in environment")
        print("Set one of: HF_TOKEN, HUGGINGFACE_API_TOKEN, or HF_API_TOKEN")
        headers = {}
    
    print("\n" + "="*50 + "\n")
    
    # Test basic token validity
    print("📋 Testing Token Validity...")
    test_url = "https://api-inference.huggingface.co/models/gpt2"
    r = requests.get(test_url, headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print("✅ Token is valid!")
    elif r.status_code == 401:
        print("❌ Token is invalid or missing!")
        print("Response:", r.text)
    else:
        print(f"⚠️ Unexpected status: {r.text}")
    
    print("\n" + "="*50 + "\n")
    
    # Test actual model inference
    def query_model(model_id, prompt="Hello world"):
        """Test a specific model."""
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        response = requests.post(url, headers=headers, json={"inputs": prompt})
        print(f"\n🤖 Testing {model_id}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Model works!")
            print("Response type:", type(result))
            
            # Handle different response formats
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    # GPT-2 style: [{"generated_text": "..."}]
                    output = result[0].get("generated_text", result[0].get("summary_text", str(result[0])))
                elif isinstance(result[0], list):
                    # BART style: [[{"summary_text": "..."}]]
                    output = result[0][0].get("summary_text", str(result[0][0])) if result[0] else str(result)
                else:
                    output = str(result[0])
                print("Output:", output[:100] + "...")
            elif isinstance(result, dict):
                output = result.get("generated_text", result.get("summary_text", str(result)))
                print("Output:", output[:100] + "...")
            else:
                print("Output:", str(result)[:100] + "...")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print("Response:", response.text[:200])
            return False
    
    # Test the confirmed working models
    print("📋 Testing Confirmed Working Models...")
    
    working_models = []
    models_to_test = [
        ("gpt2", "The meaning of life is"),
        ("distilgpt2", "Technology is"),
        ("google/flan-t5-small", "Question: What is AI? Answer:"),
        ("facebook/bart-base", "Summarize: Artificial intelligence is transforming the world."),
    ]
    
    for model_id, test_prompt in models_to_test:
        if query_model(model_id, test_prompt):
            working_models.append(model_id)
        time.sleep(1)  # Be nice to the API
    
    print("\n" + "="*50 + "\n")
    
    # Test some models that might NOT work (for comparison)
    print("📋 Testing Models That Might Not Work...")
    
    unlikely_models = [
        ("mistralai/Mistral-7B-Instruct-v0.2", "Hello"),
        ("meta-llama/Llama-2-7b-chat-hf", "Hello"),
    ]
    
    for model_id, test_prompt in unlikely_models:
        query_model(model_id, test_prompt)
        time.sleep(1)
    
    print("\n" + "="*50 + "\n")
    
    # Summary
    print("📊 SUMMARY\n")
    
    if HF_TOKEN:
        print("✅ Token found and configured")
    else:
        print("❌ No token found - using free tier")
    
    if working_models:
        print(f"\n✅ Working models ({len(working_models)}):")
        for model in working_models:
            print(f"   - {model}")
        
        print(f"\n🎯 Recommended primary model: {working_models[0]}")
        print("🔧 Update your deployment to use these models!")
    else:
        print("\n❌ No models worked - check your token and internet connection")
    
    print("\n💡 TIP: Export your token before running:")
    print("   export HF_TOKEN='hf_your_token_here'")
    print("   python test_hf_token.py")


if __name__ == "__main__":
    test_token_and_models()