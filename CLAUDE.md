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

**2. Searcher Node** (`agents.py:186-226`)
- Executes Tavily searches for each research question **in parallel** using `ThreadPoolExecutor`
- All 3-5 searches fire concurrently instead of sequentially (3-4x speedup)
- Uses `search_depth="advanced"` for comprehensive results
- Collects `max_results=5` per question with content & URLs
- Gracefully handles search failures with empty result sets via per-question error handling

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
| `agents.py` | Core LangGraph pipeline + caching | `planner_node()`, `searcher_node()` (parallel), `synthesizer_node()`, `build_research_graph()`, `run_research()`, `_make_cache_key()`, `_load_cache()`, `_save_cache()` |
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

### 1. LLM Model (`agents.py:168, 252`)
```python
# Change from GPT-4o to other OpenAI models
model="gpt-4-turbo"  # or gpt-4, gpt-3.5-turbo
```

### 2. Search Strategy (`agents.py:202-207`)
```python
response = tavily.search(
  query=question,
  max_results=5,           # Increase for more results
  search_depth="advanced", # "basic" for faster, cheaper searches
  include_raw_content=False
)
```

### 3. Cache Configuration (`agents.py:22-23`)
```python
CACHE_DIR = Path(__file__).parent / "cache"  # Cache directory location
CACHE_TTL_SECONDS = 24 * 60 * 60             # 24 hours; adjust for shorter/longer expiry
```

### 4. Report Structure (`agents.py:131-166`)
Modify `SYNTHESIZER_SYSTEM_PROMPT` to change:
- Markdown formatting (headers, lists, emphasis)
- Citation style (inline, footnotes, numbered)
- Section ordering or additional sections

### 5. Question Generation (`agents.py:101-109`)
Modify `PLANNER_SYSTEM_PROMPT` to request different numbers of questions, different ordering, etc.

## Caching System

The pipeline includes a built-in result caching layer to optimize costs and speed for repeated queries.

### How It Works

- **Cache Key**: SHA-256 hash of (query + conversation_context) — unique per query variant
- **Storage**: `./cache/` directory with JSON files (auto-created)
- **TTL**: 24 hours (configurable via `CACHE_TTL_SECONDS`)
- **Integration**: Transparent — cache check happens in `run_research()` before pipeline execution

### Cache Hit Scenario
```
User Query → Cache Key Hash → Lookup in ./cache/{hash}.json → Found & Valid → Return Instantly
```

### Cache Miss Scenario
```
User Query → Cache Key Hash → Lookup → Not Found or Expired → Run Full Pipeline → Save to Cache → Return
```

### Conversation Context & Caching

The `conversation_context` is included in the cache key, so:
- Query without context → 1 cache entry
- Same query with different context → Different cache entry
- MCP path (always empty context) → Always uses same cache for identical queries
- Streamlit multi-turn → Each turn's context changes the key (cache hits less frequent, but correct)

### Cache Management

Clear cache by deleting the `cache/` directory:
```bash
rm -rf cache/
```

The directory and files will be auto-recreated on the next query execution.

## Testing

### Import & Setup Validation
```bash
uv run test/test_imports_only.py
```
Checks all dependencies import correctly and APIs are configured.

### Integration Tests
```bash
uv run test/test_crew.py       # Run full pipeline
uv run test/test_langchain.py  # LangChain + Tavily integration
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

### Default Run (Full Pipeline)

| Stage | Time | Notes |
|-------|------|-------|
| Planner (GPT-4o) | 2-3s | LLM latency |
| Searcher (Tavily, parallel) | 2-3s | Concurrent searches (3-4x faster than sequential) |
| Synthesizer (GPT-4o) | 5-8s | LLM reasoning time |
| **Total** | **~9-14s** | ✅ 30-40% faster with parallel searches |

### Cached Run (Repeated Query)
| Stage | Time |
|-------|------|
| Cache lookup + return | <100ms | Instant response from `./cache/` directory |

### Cost Estimate
- GPT-4o: ~$0.01-0.05 per query (1st run only)
- Tavily advanced: ~$0.01 per search (1st run only)
- **Cost per unique query: ~$0.06-0.10**
- **Cost per repeated query (within 24h): $0.00** (cache hit)

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

## Completed Enhancements

✅ **Parallel searching** - Tavily searches execute concurrently via `ThreadPoolExecutor` (3-4x speedup)
✅ **Caching** - Full pipeline results cached in `./cache/` with SHA-256 keying and 24h TTL

## Future Enhancements

Possible improvements:
1. **Multi-turn refinement** - Let LLM request follow-up searches based on initial results
2. **Source ranking** - Score sources by relevance/authority/recency
3. **Export formats** - PDF, HTML, JSON in addition to markdown
4. **Streamlit Cloud deployment** - Standalone web app at public URL
5. **Alternative models** - Support Anthropic Claude, local Ollama
6. **Custom search tools** - Replace/augment Tavily with academic databases, news APIs, etc.
7. **Batch processing** - Queue multiple queries for concurrent execution
8. **Cache pruning** - Auto-delete stale cache files based on disk space/age

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
