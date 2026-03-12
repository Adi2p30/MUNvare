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

PORT = 8000

# Auto-activate venv: if a .venv exists and we're not already inside it, re-exec with its Python
_root = Path(__file__).parent
_venv_python = _root / '.venv' / 'bin' / 'python'
if _venv_python.exists() and sys.executable != str(_venv_python):
    os.execv(str(_venv_python), [str(_venv_python)] + sys.argv)

def check_dependencies():
    import importlib.util
    print("Checking dependencies...")
    missing = [pkg for pkg in ('flask', 'flask_socketio') if importlib.util.find_spec(pkg) is None]
    if missing:
        print(f"✗ Missing dependencies: {', '.join(missing)}")
        print("\nPlease install dependencies:")
        print("  pip install -r backend/requirements.txt")
        sys.exit(1)
    print("✓ Core dependencies found")

    from dotenv import load_dotenv
    load_dotenv()

    has_gemini = bool(os.getenv('GEMINI_API_KEY'))

    if not has_gemini:
        print("⚠ Warning: GEMINI_API_KEY not found in .env file")
        print("  AI features will not work without it")
        print("  Please set GEMINI_API_KEY in your .env file")
        print("\nContinuing anyway...")
    else:
        print("✓ Gemini API key found")

def check_vectordb():
    vectordb_path = Path("data/chromadb")
    if not vectordb_path.exists():
        print("\n📚 Vector database not found. It will be initialized on first run.")
        print("   This may take a minute...")

def start_backend():
    print("\n" + "="*60)
    print("Starting MUNvare Backend Server...")
    print("="*60)

    backend_path = Path(__file__).parent / "backend" / "app.py"

    if not backend_path.exists():
        print(f"✗ Backend file not found: {backend_path}")
        sys.exit(1)

    process = subprocess.Popen(
        [sys.executable, str(backend_path)],
        cwd=str(Path(__file__).parent),
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    print("\nWaiting for server to start...")
    time.sleep(3)
    return process

def open_browser():
    url = f"http://localhost:{PORT}"
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

    check_dependencies()
    check_vectordb()

    process = start_backend()

    time.sleep(2)
    open_browser()

    print("\n" + "="*60)
    print("MUNvare is running!")
    print("="*60)
    print(f"\n📍 App:      http://localhost:{PORT}")
    print(f"📍 Chair:    http://localhost:{PORT}/chair")
    print(f"📍 Delegate: http://localhost:{PORT}/delegate")
    print(f"📍 API:      http://localhost:{PORT}/api")
    print("\n💡 Press Ctrl+C to stop the server")
    print("="*60 + "\n")

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down MUNvare...")
        process.terminate()
        process.wait()
        print("✓ Server stopped")

if __name__ == "__main__":
    main()
