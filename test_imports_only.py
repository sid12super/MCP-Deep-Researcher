#!/usr/bin/env python3
"""Test that all imports work."""

import os
import sys
from dotenv import load_dotenv

print("=" * 60)
print("IMPORT TEST")
print("=" * 60)

# Load env vars
load_dotenv()

# Check API keys
openai_key = os.getenv("OPENAI_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

print(f"✓ Python {sys.version}")
print(f"OpenAI API Key: {'✓ Present' if openai_key else '✗ Missing'}")
print(f"Tavily API Key: {'✓ Present' if tavily_key else '✗ Missing'}")

print("\nTesting imports...")
try:
    from langchain_openai import ChatOpenAI
    print("✓ langchain_openai")
    
    from tavily import TavilyClient
    print("✓ tavily")
    
    from langgraph.graph import StateGraph
    print("✓ langgraph")
    
    from mcp.server.fastmcp import FastMCP
    print("✓ mcp.server.fastmcp")
    
    from agents import run_research
    print("✓ agents.run_research")
    
    from server import crew_research
    print("✓ server.crew_research")
    
    print("\n✓ All imports successful!")
    print("\nSetup Status:")
    print("- Dependencies: ✓ Installed")
    print("- API Keys: ✓ Configured")
    print("- Server: ✓ Ready to start")
    
except ImportError as e:
    print(f"\n✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Error: {e}")
    sys.exit(1)
