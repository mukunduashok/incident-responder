#!/bin/bash

# Quick Setup Script for Incident Responder

echo "🚀 Setting up Incident Responder..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env created. Please edit it with your configuration."
else
    echo "✅ .env file already exists"
fi

# Install dependencies
echo "📦 Installing dependencies..."
if command -v uv &> /dev/null; then
    echo "Using uv package manager..."
    uv sync --all-groups
else
    echo "Using pip..."
    pip install -e ".[test]"
fi

# Initialize mock repo with git
echo "📁 Setting up mock repository..."
if [ ! -d "data/mock_repo/.git" ]; then
    cd data/mock_repo
    git init
    git add .
    git commit -m "Initial commit: Mock application code"
    cd ../..
    echo "✅ Mock repository initialized with git history"
else
    echo "✅ Mock repository already initialized"
fi

# Check if Ollama is available
echo ""
echo "🤖 Checking Ollama availability..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is installed"
    
    # Check if model is available
    if ollama list | grep -q "qwen3-coder"; then
        echo "✅ qwen3-coder model is available"
    else
        echo "⚠️  qwen3-coder model not found"
        echo "   Run: ollama pull qwen3-coder"
    fi
else
    echo "⚠️  Ollama not found. Install from: https://ollama.com"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Start Ollama: ollama serve"
echo "3. Run the app: python main.py"
echo "4. Visit: http://localhost:8000/docs"
