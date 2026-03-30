#!/usr/bin/env python3
"""Simple test of the crew_research system."""

import os
from dotenv import load_dotenv
from agents import run_research

# Load env vars
load_dotenv()

# Check API keys
openai_key = os.getenv("OPENAI_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

print("=" * 60)
print("CREW RESEARCH TEST")
print("=" * 60)
print(f"OpenAI API Key: {'✓ Present' if openai_key else '✗ Missing'}")
print(f"Tavily API Key: {'✓ Present' if tavily_key else '✗ Missing'}")

if not openai_key or not tavily_key:
    print("\n❌ Missing required API keys!")
    exit(1)

print("\nRunning test query...")
try:
    result = run_research("What are the latest advancements in AI in 2026?")
    print("\n✓ SUCCESS!")
    print("\nResult (first 500 chars):")
    print(result[:500])
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
