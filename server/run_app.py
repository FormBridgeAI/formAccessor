#!/usr/bin/env python3
"""
Startup script for the Voice-Enabled Form Filling Web Application
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """Check if the environment is properly set up"""
    print("🔍 Checking environment...")
    
    # Check if .env file exists
    env_file = Path("../.env")
    if not env_file.exists():
        print("❌ .env file not found. Please create it with your API keys.")
        return False
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Virtual environment not detected. Please activate your virtual environment first.")
        print("   Run: source venv/bin/activate")
        return False
    
    print("✅ Environment looks good!")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_requirements():
    """Create requirements.txt file"""
    requirements = [
        "flask==3.1.2",
        "flask-cors==6.0.1",
        "python-dotenv==1.0.0",
        "azure-ai-documentintelligence==1.0.0b4",
        "azure-core==1.30.2",
        "openai==1.51.0",
        "deepgram-sdk==3.2.7",
        "pyaudio==0.2.11",
        "pillow==10.4.0",
        "pymupdf==1.26.4"
    ]
    
    with open("requirements.txt", "w") as f:
        f.write("\n".join(requirements))
    
    print("✅ Created requirements.txt")

def main():
    """Main startup function"""
    print("🚀 Starting Voice-Enabled Form Filling Web Application")
    print("=" * 60)
    
    # Create requirements.txt if it doesn't exist
    if not Path("requirements.txt").exists():
        create_requirements()
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above and try again.")
        return
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies. Please check the error messages above.")
        return
    
    print("\n🌐 Starting web server...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Start the Flask app
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")

if __name__ == "__main__":
    main()
