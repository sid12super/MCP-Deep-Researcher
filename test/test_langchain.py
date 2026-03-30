#!/usr/bin/env python3
"""Test langchain-openai imports"""
import sys

print("Testing imports...")
try:
    print("  - Importing ChatOpenAI from langchain_openai...")
    from langchain_openai import ChatOpenAI
    print("    ✓ Success")
    
    print("  - Importing SystemMessage from langchain_core...")
    from langchain_core.messages import SystemMessage, HumanMessage
    print("    ✓ Success")
    
    print("  - Importing LangGraph StateGraph...")
    from langgraph.graph import StateGraph, START, END
    print("    ✓ Success")
    
    print("  - Importing TavilyClient...")
    from tavily import TavilyClient
    print("    ✓ Success")
    
    print("\n✓ All imports successful!")
    print("\nYou can now run:")
    print("  streamlit run app.py")
    
except ImportError as e:
    print(f"\n✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
