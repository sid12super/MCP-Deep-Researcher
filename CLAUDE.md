# CLAUDE.md - Development Context

This file provides guidance to Claude Code when working on this repository.

## Project Overview

**Agentic Deep Researcher** is a multi-agent research system powered by LangGraph, OpenAI GPT-4o, and Tavily web search. It breaks down complex research queries into focused sub-questions, searches comprehensively, and synthesizes findings into detailed markdown reports.

**Key Use Cases**:
- Research tasks & competitive analysis
- Trend research & market analysis
- Fact-gathering & verification
- Knowledge synthesis from multiple sources
- Integration as MCP tool in Claude/Cursor

## Architecture

### System Design: 3-Node LangGraph Pipeline

```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌────────┐
│  Query  │────▶│ Planner  │────▶│  Searcher  │────▶│Synthesizer
└─────────┘     └──────────┘     └────────────┘     └────────┘
                      │                 │                  │
                      ▼                 ▼                  ▼
              3-5 Research      Tavily API Searches   Markdown Report
              Questions         (5 results each)      with Sources
```

### Node Responsibilities

**1. Planner Node** (`agents.py:103-124`)
- Uses GPT-4o with structured output (Pydantic)
- Decomposes user query into 3-5 targeted sub-questions
- Ensures questions are non-overlapping and collectively exhaustive
- Returns `ResearchPlan` model with validated questions

**2. Searcher Node** (`agents.py:127-156`)
- Executes Tavily searches for each research question sequentially
- Uses `search_depth="advanced"` for comprehensive results
- Collects `max_results=5` per question with content & URLs
- Gracefully handles search failures with empty result sets

**3. Synthesizer Node** (`agents.py:159-202`)
- Analyzes all search evidence for patterns and insights
- Creates comprehensive markdown report with:
  - Executive summary (2-3 sentences)
  - Key findings per sub-question (150-250 words each)
  - Knowledge gaps (concrete, specific missing info)
  - Source citations (numbered list with URLs)
- Uses GPT-4o at `temperature=0.2` for consistency
- Optionally incorporates previous conversation context for follow-ups

### Data Flow: State Management

`ResearchState` (TypedDict, `agents.py:30-36`):
```python
{
  "query": str,                             # Original user query
  "research_questions": list[str],          # Planner output
  "search_results": dict[str, list[dict]],  # Searcher output
  "final_report": str,                      # Synthesizer output
  "conversation_context": str               # Optional previous Q&A
}
```

State flows linearly through all three nodes, each enriching it.

## Key Files & Responsibilities

| File | Purpose | Key Functions/Classes |
|------|---------|----------------------|
| `agents.py` | Core LangGraph pipeline | `planner_node()`, `searcher_node()`, `synthesizer_node()`, `build_research_graph()`, `run_research()` |
| `server.py` | MCP FastMCP wrapper | `crew_research()` tool definition |
| `app.py` | Streamlit web UI | Chat interface, session state, API key validation |
| `pyproject.toml` | Dependency management | Specifies LangGraph, Tavily, OpenAI, MCP, Streamlit |
| `.env.example` | Configuration template | Shows required API key format |

## Development Setup

### Environment & Dependencies
```bash
# Install dependencies via UV (Python 3.11+)
uv sync

# Creates .venv and installs from pyproject.toml
```

### Prerequisites
1. **OpenAI API Key** - Get from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. **Tavily API Key** - Get from [app.tavily.com](https://app.tavily.com)
3. **Python 3.11+** - Required by project (see `.python-version`)

### Local Configuration
```bash
# Copy template
cp .env.example .env

# Edit with your API keys
# OPENAI_API_KEY=sk-...
# TAVILY_API_KEY=tvly-...
```

## Running the Application

### Option 1: Streamlit UI (Development)
```bash
streamlit run app.py
```
- Opens at `http://localhost:8501`
- Hot-reload on code changes
- Session state persists during session

### Option 2: Direct Python (Testing)
```bash
python -c "from agents import run_research; print(run_research('Your query'))"
```

### Option 3: MCP Server (Integration)
```bash
uv run server.py
```
- Starts FastMCP stdio server
- Integrates with Claude Code / Cursor via `.cursor/mcp.json`
- Exposes `crew_research(query: str)` tool

## Code Patterns & Conventions

### System Prompts
- **PLANNER_SYSTEM_PROMPT** (`agents.py:43-53`): Instructs GPT-4o on question decomposition rules
- **SYNTHESIZER_SYSTEM_PROMPT** (`agents.py:56-96`): Defines markdown structure and citation requirements
- Both use clear, structured instructions with explicit rules

### Error Handling
- Searcher gracefully catches per-question failures (returns empty list, continues)
- Synthesizer never fabricates facts (rule in prompt)
- `run_research()` wraps entire pipeline in try-catch, returns error markdown

### Typing
- Full TypedDict for `ResearchState`
- Pydantic models for structured outputs (`ResearchPlan`)
- Type hints on all functions
- Enables IDE autocomplete and type checking

## Customization Points

Developers can modify:

### 1. LLM Model (`agents.py:110, 180`)
```python
# Change from GPT-4o to other OpenAI models
model="gpt-4-turbo"  # or gpt-4, gpt-3.5-turbo
```

### 2. Search Strategy (`agents.py:140-144`)
```python
response = tavily.search(
  query=question,
  max_results=5,           # Increase for more results
  search_depth="advanced", # "basic" for faster, cheaper searches
  include_raw_content=False
)
```

### 3. Report Structure (`agents.py:56-96`)
Modify `SYNTHESIZER_SYSTEM_PROMPT` to change:
- Markdown formatting (headers, lists, emphasis)
- Citation style (inline, footnotes, numbered)
- Section ordering or additional sections

### 4. Question Generation (`agents.py:43-53`)
Modify `PLANNER_SYSTEM_PROMPT` to request different numbers of questions, different ordering, etc.

## Testing

### Import & Setup Validation
```bash
uv run test_imports_only.py
```
Checks all dependencies import correctly and APIs are configured.

### Integration Tests
```bash
uv run test_crew.py       # Run full pipeline
uv run test_langchain.py  # LangChain + Tavily integration
```

## Deployment

### Streamlit Deployment
- Platforms: Streamlit Cloud, Heroku, AWS, Google Cloud, etc.
- Requires `.env` with API keys (use secrets management)
- Cold start: ~5-10 seconds (dependency loading)

### MCP Server Deployment
- Integrate into IDE config (Cursor, Claude Code, VS Code extensions)
- Runs as subprocess of MCP client
- No direct HTTP exposure (stdio protocol)

### Docker
Create Dockerfile if deploying to containers:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
CMD ["uv", "run", "server.py"]
```

## Performance Characteristics

| Stage | Time | Bottleneck |
|-------|------|-----------|
| Planner (GPT-4o) | 2-3s | LLM latency |
| Searcher (Tavily, 5 queries) | 5-10s | API rate limits |
| Synthesizer (GPT-4o) | 5-8s | LLM reasoning time |
| **Total** | **~15-25s** | Parallel searches could help |

### Cost Estimate
- GPT-4o: ~$0.01-0.05 per query
- Tavily advanced: ~$0.01 per search
- **Total per query: ~$0.06-0.10**

## Common Issues & Solutions

| Problem | Root Cause | Fix |
|---------|-----------|-----|
| `OPENAI_API_KEY not found` | `.env` missing or wrong path | Verify `.env` exists in project root with correct key |
| `TavilyClient initialization fails` | Invalid/expired `TAVILY_API_KEY` | Check key on app.tavily.com, regenerate if needed |
| Planner generates malformed JSON | Model context too large | Reduce query length or max_results |
| Searcher returns empty results | Query too specific or niche | Broad queries get better coverage |
| Streamlit port conflict (8501) | Another process using port | Use `--server.port 8502` flag |
| MCP server not in Claude Code | Config path incorrect | Use absolute path in `.cursor/mcp.json` |

## Git Workflow

### Before Committing
- Run tests: `uv run test_imports_only.py`
- Verify no API keys in staged files (`.env` should be gitignored)
- Check `.gitignore` includes: `*.env`, `*.log`, `.venv/`, `__pycache__/`

### Commit Messages
Use clear, descriptive messages:
- ✅ `"Fix: handle empty search results gracefully"`
- ✅ `"Feature: add conversation context to synthesizer"`
- ❌ `"Update agents.py"`

## Future Enhancements

Possible improvements:
1. **Parallel searching** - Execute Tavily searches concurrently
2. **Multi-turn refinement** - Let LLM request follow-up searches
3. **Source ranking** - Score sources by relevance/authority
4. **Export formats** - PDF, HTML, JSON in addition to markdown
5. **Caching** - Cache search results for identical queries
6. **Alternative models** - Support Anthropic Claude, local Ollama
7. **Custom search tools** - Replace/augment Tavily with other sources

## References

- [LangGraph Documentation](https://github.com/langchain-ai/langgraph)
- [Tavily API Docs](https://tavily.com/docs)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)

## Contact & Support

For questions about this codebase:
1. Check README.md for user-facing documentation
2. Review inline comments in source files
3. Run tests to validate your environment
4. Open an issue with reproduction steps
