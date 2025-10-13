#!/bin/bash

echo "Installing MUNvare dependencies..."

# Upgrade pip and build tools first
echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# Install core dependencies
echo "Installing core dependencies..."
pip install flask flask-cors python-dotenv requests tqdm

# Install AI and ML packages
echo "Installing AI packages..."
pip install google-generativeai

# Install vector DB
echo "Installing ChromaDB..."
pip install chromadb sentence-transformers

# Install audio/ML packages
echo "Installing audio and ML packages..."
pip install "numpy<2.0.0" torch==2.2.1 scipy

# Install other utilities
echo "Installing other utilities..."
pip install vaderSentiment sounddevice markdown beautifulsoup4

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Get Gemini API key: https://makersuite.google.com/app/apikey"
echo "2. Create .env file: cp .env.example .env"
echo "3. Add your key to .env"
echo "4. Run: python start.py"
