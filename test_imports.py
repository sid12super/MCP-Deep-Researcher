import sys
print('✓ Testing imports...')
try:
    from agents import run_research, research_graph, ResearchState
    print('✓ agents.py imports successful')
    print(f'✓ Graph compiled: {research_graph is not None}')
    print(f'✓ ResearchState fields: {list(ResearchState.__annotations__.keys())}')
    print('\n✓ All checks passed! System is ready.')
except Exception as e:
    print(f'✗ Import error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
