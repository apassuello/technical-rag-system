#!/usr/bin/env python3
"""
Test BART model specifically to understand its requirements
"""

import os
import requests
import json

def test_bart():
    """Test BART with different input formats."""
    
    print("🧪 Testing BART Model Specifically\n")
    
    # Get token
    HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    
    url = "https://api-inference.huggingface.co/models/facebook/bart-base"
    
    # Test cases with different input formats
    test_cases = [
        {
            "name": "Simple text",
            "payload": {"inputs": "The quick brown fox jumps over the lazy dog."}
        },
        {
            "name": "Longer text for summarization",
            "payload": {
                "inputs": "Artificial intelligence is transforming the world. Machine learning models can now understand and generate human language with remarkable accuracy. Deep learning has enabled breakthroughs in computer vision, natural language processing, and robotics. The future of AI holds tremendous potential for solving complex problems."
            }
        },
        {
            "name": "With parameters",
            "payload": {
                "inputs": "RISC-V is an open-source instruction set architecture based on established RISC principles. Unlike proprietary ISAs, RISC-V is freely available for anyone to use, implement, and modify. This has led to widespread adoption in academia and industry.",
                "parameters": {
                    "max_length": 100,
                    "min_length": 20
                }
            }
        },
        {
            "name": "Question-answer format",
            "payload": {
                "inputs": "Context: RISC-V is an open-source ISA. Question: What is RISC-V? Answer:"
            }
        },
        {
            "name": "With summarize prefix",
            "payload": {
                "inputs": "Summarize: RISC-V provides a base integer ISA, which must be present in any implementation, plus optional extensions to the base ISA. The base integer ISAs are very similar to that of the early RISC processors."
            }
        },
        {
            "name": "Empty parameters object",
            "payload": {
                "inputs": "Test input text for BART model.",
                "parameters": {}
            }
        }
    ]
    
    print("Testing different input formats...\n")
    
    for test in test_cases:
        print(f"📋 Test: {test['name']}")
        print(f"Payload: {json.dumps(test['payload'], indent=2)}")
        
        try:
            response = requests.post(url, headers=headers, json=test['payload'])
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success!")
                print(f"Response: {json.dumps(result, indent=2)[:200]}...")
            else:
                print(f"❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"💥 Exception: {e}")
        
        print("\n" + "-"*60 + "\n")
    
    # Test what happens with very short input
    print("📋 Testing edge cases...\n")
    
    edge_cases = [
        {"inputs": ""},
        {"inputs": " "},
        {"inputs": "Hi"},
        {"inputs": "Test"},
        {"inputs": "What is AI?"},
    ]
    
    for payload in edge_cases:
        print(f"Input: '{payload['inputs']}' (length: {len(payload['inputs'])})")
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        print()


if __name__ == "__main__":
    test_bart()