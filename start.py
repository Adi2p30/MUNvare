#!/usr/bin/env python3
"""
MUNvare Startup Script
Starts the backend server and opens the browser
"""

import os
import sys
import time
import webbrowser
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")

    try:
        import flask
        import chromadb
        import sentence_transformers
        print("✓ Core dependencies found")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

    # Check for API keys
    from dotenv import load_dotenv
    load_dotenv()

    has_openai = bool(os.getenv('OPENAI_API_KEY'))
    has_anthropic = bool(os.getenv('ANTHROPIC_API_KEY'))

    if not (has_openai or has_anthropic):
        print("⚠ Warning: No AI API keys found in .env file")
        print("  AI features will not work without API keys")
        print("  Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env")
        print("\nContinuing anyway...")
    else:
        if has_openai:
            print("✓ OpenAI API key found")
        if has_anthropic:
            print("✓ Anthropic API key found")

def check_vectordb():
    """Check if vector database needs initialization"""
    vectordb_path = Path("data/chromadb")

    if not vectordb_path.exists():
        print("\n📚 Vector database not found. It will be initialized on first run.")
        print("   This may take a minute...")

def start_backend():
    """Start the Flask backend server"""
    print("\n" + "="*60)
    print("Starting MUNvare Backend Server...")
    print("="*60)

    backend_path = Path(__file__).parent / "backend" / "app.py"

    if not backend_path.exists():
        print(f"✗ Backend file not found: {backend_path}")
        sys.exit(1)

    # Start backend in a subprocess
    process = subprocess.Popen(
        [sys.executable, str(backend_path)],
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    # Wait for server to start
    print("\nWaiting for server to start...")
    time.sleep(3)

    return process

def open_browser():
    """Open the application in the default browser"""
    url = "http://localhost:5000"
    print(f"\n🌐 Opening browser at {url}")
    webbrowser.open(url)

def main():
    print("""
    ███╗   ███╗██╗   ██╗███╗   ██╗██╗   ██╗ █████╗ ██████╗ ███████╗
    ████╗ ████║██║   ██║████╗  ██║██║   ██║██╔══██╗██╔══██╗██╔════╝
    ██╔████╔██║██║   ██║██╔██╗ ██║██║   ██║███████║██████╔╝█████╗
    ██║╚██╔╝██║██║   ██║██║╚██╗██║╚██╗ ██╔╝██╔══██║██╔══██╗██╔══╝
    ██║ ╚═╝ ██║╚██████╔╝██║ ╚████║ ╚████╔╝ ██║  ██║██║  ██║███████╗
    ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝  ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝

    Complete MUN Assistant Platform
    """)

    # Run checks
    check_dependencies()
    check_vectordb()

    # Start backend
    process = start_backend()

    # Open browser
    time.sleep(2)
    open_browser()

    print("\n" + "="*60)
    print("MUNvare is running!")
    print("="*60)
    print("\n📍 Frontend: http://localhost:5000")
    print("📍 API: http://localhost:5000/api")
    print("\n💡 Press Ctrl+C to stop the server")
    print("="*60 + "\n")

    try:
        # Keep the script running
        process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down MUNvare...")
        process.terminate()
        process.wait()
        print("✓ Server stopped")

if __name__ == "__main__":
    main()
