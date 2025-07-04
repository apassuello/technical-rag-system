#!/usr/bin/env python3
"""
Check if huggingface_hub version supports chat_completion
"""

try:
    from huggingface_hub import InferenceClient
    from huggingface_hub import __version__ as hf_hub_version
    
    print(f"✅ huggingface_hub version: {hf_hub_version}")
    
    # Check if InferenceClient has chat_completion method
    client = InferenceClient()
    
    if hasattr(client, 'chat_completion'):
        print("✅ InferenceClient has chat_completion method")
    else:
        print("❌ InferenceClient does NOT have chat_completion method")
        print("Available methods:")
        methods = [m for m in dir(client) if not m.startswith('_') and callable(getattr(client, m))]
        for method in sorted(methods):
            print(f"  - {method}")
    
    # Check for chat.completions.create (OpenAI style)
    if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
        print("✅ InferenceClient has chat.completions.create (OpenAI style)")
    else:
        print("❌ InferenceClient does NOT have chat.completions.create")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()