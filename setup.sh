#!/bin/bash
# Setup script for planwise development environment

set -e  # Exit on any error

echo "🚀 Setting up planwise development environment..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is required but not installed. Please install uv first:"
    echo "   pip install uv"
    exit 1
fi

echo "✅ uv found"

# Install the package in development mode with all dependencies
echo "📦 Installing planwise in development mode..."
uv pip install -e ".[all]"

# Install pre-commit hooks
echo "🪝 Setting up pre-commit hooks..."
pre-commit install

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Available commands:"
echo "  make test          - Run tests"
echo "  make format        - Format code"
echo "  make lint          - Run linting"
echo "  make app           - Run Streamlit app"
echo ""
echo "Try running: make test"
