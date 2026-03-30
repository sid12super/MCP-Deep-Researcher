#!/bin/bash
set -e

echo "======================================"
echo "Verifying LangGraph Deep Researcher Setup"
echo "======================================"
echo ""

# Check .env file
if [ -f .env ]; then
    echo "✓ .env file exists"
    if grep -q "OPENAI_API_KEY" .env; then
        echo "  ✓ OPENAI_API_KEY is set"
    else
        echo "  ✗ OPENAI_API_KEY not found in .env"
    fi
    if grep -q "TAVILY_API_KEY" .env; then
        echo "  ✓ TAVILY_API_KEY is set"
    else
        echo "  ✗ TAVILY_API_KEY not found in .env"
    fi
else
    echo "✗ .env file not found"
fi

echo ""

# Check key files
echo "Checking implementation files:"
for file in agents.py app.py server.py pyproject.toml .env.example README.md; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file"
    fi
done

echo ""
echo "======================================"
echo "Setup verification complete!"
echo "======================================"
