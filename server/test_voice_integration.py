"""
Test script for voice agent integration
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

def test_environment():
    """Test if all required environment variables are set"""
    print("�� Testing environment variables...")
    
    required_vars = ['OPENAI_API_KEY', 'AZURE_KEY', 'DEEPGRAM_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value == f"your_{var.lower()}_here":
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * 20}...{value[-4:]}")
    
    if missing_vars:
        print(f"❌ Missing or invalid environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with valid API keys.")
        return False
    
    print("✅ All environment variables are set!")
    return True

def test_imports():
    """Test if all required modules can be imported"""
    print("\n🔍 Testing imports...")
    
    try:
        from deepgram import DeepgramClient, DeepgramClientOptions
        print("✅ Deepgram SDK imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Deepgram SDK: {e}")
        return False
    
    try:
        from voice_agent import VoiceFormAgent
        print("✅ VoiceFormAgent imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import VoiceFormAgent: {e}")
        return False
    
    try:
        from voice_workflow import voice_enabled_form_workflow
        print("✅ Voice workflow imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import voice workflow: {e}")
        return False
    
    print("✅ All imports successful!")
    return True

def test_config_files():
    """Test if configuration files exist and are valid"""
    print("\n🔍 Testing configuration files...")
    
    # Test deepgram_config.json
    if os.path.exists('deepgram_config.json'):
        try:
            with open('deepgram_config.json', 'r') as f:
                config = json.load(f)
            print("✅ deepgram_config.json exists and is valid JSON")
        except json.JSONDecodeError as e:
            print(f"❌ deepgram_config.json is not valid JSON: {e}")
            return False
    else:
        print("❌ deepgram_config.json not found")
        return False
    
    print("✅ Configuration files are valid!")
    return True

def main():
    """Run all tests"""
    print("🧪 Testing Voice Agent Integration\n")
    
    tests = [
        test_environment,
        test_imports,
        test_config_files
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
        print()  # Add spacing between tests
    
    if all_passed:
        print("🎉 All tests passed! Voice agent integration is ready.")
        print("\nTo run the voice-enabled workflow:")
        print("  python voice_workflow.py")
        print("\nTo test just the voice agent:")
        print("  python voice_agent.py")
    else:
        print("❌ Some tests failed. Please fix the issues above before proceeding.")

if __name__ == "__main__":
    main()
