#!/usr/bin/env python3
"""
Test script to verify container environment setup for Ollama.
This script checks if all necessary components are properly configured.
"""

import os
import sys
import subprocess
import time
import requests

def test_logging():
    """Test that logging works properly."""
    print("🧪 Testing logging to stdout...", file=sys.stdout, flush=True)
    print("🧪 Testing logging to stderr...", file=sys.stderr, flush=True)
    return True

def test_directories():
    """Test that required directories exist and are writable."""
    directories = [
        "/app/.ollama",
        "/app/.ollama/models",
        "/app/.cache",
        "/app/temp_uploads"
    ]
    
    for dir_path in directories:
        if not os.path.exists(dir_path):
            print(f"❌ Directory missing: {dir_path}", file=sys.stderr, flush=True)
            return False
        
        if not os.access(dir_path, os.W_OK):
            print(f"❌ Directory not writable: {dir_path}", file=sys.stderr, flush=True)
            return False
            
        print(f"✅ Directory OK: {dir_path}", file=sys.stderr, flush=True)
    
    return True

def test_ollama_installation():
    """Test that Ollama is properly installed."""
    try:
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Ollama version: {result.stdout.strip()}", file=sys.stderr, flush=True)
            return True
        else:
            print(f"❌ Ollama version check failed: {result.stderr}", file=sys.stderr, flush=True)
            return False
    except Exception as e:
        print(f"❌ Ollama not found: {e}", file=sys.stderr, flush=True)
        return False

def test_environment_variables():
    """Test that environment variables are set correctly."""
    required_vars = {
        'OLLAMA_MODELS': '/app/.ollama/models',
        'OLLAMA_HOST': '0.0.0.0:11434'
    }
    
    for var, expected in required_vars.items():
        actual = os.getenv(var)
        if actual == expected:
            print(f"✅ {var}={actual}", file=sys.stderr, flush=True)
        else:
            print(f"⚠️ {var}={actual} (expected: {expected})", file=sys.stderr, flush=True)
    
    # Show all environment variables for debugging
    print("🔍 All environment variables:", file=sys.stderr, flush=True)
    for key in sorted(os.environ.keys()):
        if any(keyword in key.upper() for keyword in ['OLLAMA', 'HF', 'TOKEN', 'SPACE']):
            value = os.environ[key]
            if 'TOKEN' in key.upper():
                value = value[:8] + '...' if len(value) > 8 else '***'
            print(f"  {key}={value}", file=sys.stderr, flush=True)
    
    return True

def test_startup_script():
    """Test that the Python startup script exists and is valid."""
    startup_script = "/app/startup.py"
    
    if not os.path.exists(startup_script):
        print(f"❌ Startup script missing: {startup_script}", file=sys.stderr, flush=True)
        return False
    
    # Test if it's valid Python
    try:
        with open(startup_script, 'r') as f:
            compile(f.read(), startup_script, 'exec')
        print(f"✅ Startup script is valid Python", file=sys.stderr, flush=True)
        return True
    except SyntaxError as e:
        print(f"❌ Startup script has syntax error: {e}", file=sys.stderr, flush=True)
        return False
    except Exception as e:
        print(f"❌ Could not validate startup script: {e}", file=sys.stderr, flush=True)
        return False

def test_ollama_server():
    """Test if Ollama server can start and respond."""
    print("🧪 Testing Ollama server startup...", file=sys.stderr, flush=True)
    
    try:
        # Start Ollama in background
        process = subprocess.Popen(['ollama', 'serve'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait for startup
        time.sleep(10)
        
        # Test connection
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server responding", file=sys.stderr, flush=True)
            result = True
        else:
            print(f"❌ Ollama server returned {response.status_code}", file=sys.stderr, flush=True)
            result = False
            
    except Exception as e:
        print(f"❌ Ollama server test failed: {e}", file=sys.stderr, flush=True)
        result = False
    finally:
        # Cleanup
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
    
    return result

def main():
    """Run all tests."""
    print("🚀 Starting container environment tests...", file=sys.stderr, flush=True)
    
    tests = [
        ("Logging", test_logging),
        ("Directories", test_directories),
        ("Ollama Installation", test_ollama_installation),
        ("Environment Variables", test_environment_variables),
        ("Startup Script", test_startup_script),
        ("Ollama Server", test_ollama_server)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...", file=sys.stderr, flush=True)
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}", file=sys.stderr, flush=True)
            results[test_name] = False
    
    # Summary
    print("\n📊 Test Results Summary:", file=sys.stderr, flush=True)
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}", file=sys.stderr, flush=True)
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Container should work properly.", file=sys.stderr, flush=True)
        return 0
    else:
        print("\n⚠️ Some tests failed. Check configuration.", file=sys.stderr, flush=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())