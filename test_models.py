#!/usr/bin/env python3
"""
Test script for Meeting Transcriber models
"""

import os
import sys

def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    
    try:
        import summarizer_bedrock
        print("[OK] summarizer_bedrock imported successfully")
    except Exception as e:
        print(f"[FAIL] summarizer_bedrock import failed: {e}")
        return False
    
    try:
        import summarizer_free
        print("[OK] summarizer_free imported successfully")
    except Exception as e:
        print(f"[FAIL] summarizer_free import failed: {e}")
        print("  Note: This requires 'requests' package")
        return False
    
    return True

def test_model_detection():
    """Test model detection logic"""
    print("\nTesting model detection...")
    
    # Test AWS Bedrock models
    bedrock_models = [
        "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "amazon.nova-pro-v1:0",
        "meta.llama3-2-90b-instruct-v1:0",
        "mistral.mistral-large-2407-v1:0"
    ]
    
    # Test free models
    free_models = [
        "ollama:llama3.2",
        "hf:microsoft/DialoGPT-large",
        "openai-free:meta-llama/Llama-2-7b-chat-hf"
    ]
    
    for model in bedrock_models:
        is_free = model.startswith(('ollama:', 'hf:', 'openai-free:'))
        print(f"  {model}: {'FREE' if is_free else 'BEDROCK'}")
    
    for model in free_models:
        is_free = model.startswith(('ollama:', 'hf:', 'openai-free:'))
        print(f"  {model}: {'FREE' if is_free else 'BEDROCK'}")
    
    return True

def test_prompt_creation():
    """Test prompt creation for different model types"""
    print("\nTesting prompt creation...")
    
    try:
        from summarizer_bedrock import create_bedrock_prompt
        
        test_transcript = "John: Hello everyone. Mary: Hi John, let's discuss the project."
        system_prompt = "You are an AI assistant."
        
        # Test Claude prompt
        claude_prompt = create_bedrock_prompt(test_transcript, system_prompt, "anthropic.claude-3-5-sonnet-20241022-v2:0")
        print(f"[OK] Claude prompt created (length: {len(claude_prompt)})")
        
        # Test other model prompt
        titan_prompt = create_bedrock_prompt(test_transcript, system_prompt, "amazon.titan-text-express-v1")
        print(f"[OK] Titan prompt created (length: {len(titan_prompt)})")
        
        return True
    except Exception as e:
        print(f"[FAIL] Prompt creation failed: {e}")
        return False

def test_free_model_functions():
    """Test free model helper functions"""
    print("\nTesting free model functions...")
    
    try:
        from summarizer_free import create_simple_prompt, parse_simple_response
        
        test_transcript = "John: Hello everyone. Mary: Hi John, let's discuss the project."
        
        # Test prompt creation
        prompt = create_simple_prompt(test_transcript)
        print(f"[OK] Free model prompt created (length: {len(prompt)})")
        
        # Test response parsing
        test_response = """
        SUMMARY
        This was a brief meeting between John and Mary about a project.
        
        KEY POINTS
        - John greeted everyone
        - Mary responded and wanted to discuss the project
        
        ACTION ITEMS
        - Continue project discussion
        """
        
        summary, key_points, action_items = parse_simple_response(test_response)
        print(f"[OK] Response parsed: {len(summary)} chars summary, {len(key_points)} key points, {len(action_items)} action items")
        
        return True
    except Exception as e:
        print(f"[FAIL] Free model functions failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Meeting Transcriber Model Tests")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_model_detection,
        test_prompt_creation,
        test_free_model_functions
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"[FAIL] Test {test.__name__} failed with exception: {e}")
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All tests passed! The model updates are working correctly.")
        return 0
    else:
        print("[ERROR] Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())