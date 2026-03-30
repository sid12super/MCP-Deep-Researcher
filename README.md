# 🔍 Agentic Deep Researcher

A sophisticated multi-agent research system that breaks down broad queries into focused research questions, searches the web comprehensively, and synthesizes findings into detailed markdown reports.

**Perfect for**: Research tasks, competitive analysis, trend research, fact-gathering, and knowledge synthesis across multiple sources.

## Technology Stack

- **[LangGraph](https://github.com/langchain-ai/langgraph)** — Graph-based agent orchestration with typed state
- **[OpenAI GPT-4o](https://platform.openai.com/)** — LLM for planning and synthesizing research
- **[Tavily](https://tavily.com/)** — Advanced web search with source citations
- **[Streamlit](https://streamlit.io/)** — Interactive web UI for research queries
- **[MCP](https://modelcontextprotocol.io/)** — Model Context Protocol for Claude/Cursor integration

## Architecture

The system uses a **3-node LangGraph pipeline**:

```
User Query → Planner → Searcher → Synthesizer → Markdown Report
```

1. **Planner Node** — Decomposes the broad query into 3-5 targeted research questions using GPT-4o with structured output
2. **Searcher Node** — Executes web searches for each question using Tavily API, collecting results with source URLs
3. **Synthesizer Node** — Analyzes search results and creates a comprehensive markdown report with findings, knowledge gaps, and citations

Output is clean, well-structured markdown with:
- Executive summary
- Key findings per research question
- Identified knowledge gaps
- Properly cited sources

## Quick Start

### Prerequisites

You'll need API keys for:
- **OpenAI** (GPT-4o): Get from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Tavily** (Web search): Get from [app.tavily.com/home](https://app.tavily.com/home)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/sid12super/MCP-Deep-Researcher.git
cd MCP-Deep-Researcher
```

2. Install dependencies using UV:
```bash
uv sync
```

3. Create your `.env` file from the template:
```bash
cp .env.example .env
```

4. Edit `.env` and add your API keys:
```env
OPENAI_API_KEY=sk-your-key-here
TAVILY_API_KEY=tvly-your-key-here
```

## Features

### Phase 1: Search Depth Control
- Toggle between "basic" (faster) and "advanced" (comprehensive) search modes
- Adjustable via sidebar selectbox
- Different search depths get separate cache entries

### Phase 2: Multi-turn Conversation
- Build on previous queries with full conversation context
- "New Research Topic" button to reset and start fresh
- Previous research findings automatically used to avoid duplicating work

### Phase 3: Export in Multiple Formats
- **HTML** — Styled web-ready reports with proper formatting
- **PDF** — Professional documents ready for sharing/printing
- **JSON** — Structured data for programmatic access
- Exports include **full conversation history** (all queries and reports)

### Phase 4: Source Credibility Scoring
- Automatic classification of sources: **high** (peer-reviewed/government), **medium** (established tech/business), **unverified**
- Synthesizer weights high-credibility sources more heavily when findings conflict
- Transparent credibility tags visible in reports

### Phase 5: Real-time Progress Updates
- Visual status block showing live progress through each pipeline stage
- Per-stage metrics: questions generated, search results retrieved
- Instant cache hits show "Loaded from cache" without re-running pipeline

## Live Deployment

**Try it now**: https://sid12super-mcp-deep-researcher.streamlit.app/

Deployed on Streamlit Cloud with:
- Zero cold-start fees
- Automatic dependency management
- API key secrets securely stored
- Instant git-based updates

## Usage

### Option 1: Streamlit Web UI (Recommended for Users)

```bash
streamlit run app.py
```

Opens interactive chat at `http://localhost:8501`:
- Submit research queries in natural language
- View real-time progress (planning → searching → synthesizing)
- Get comprehensive markdown reports with sources
- Build on previous queries with conversation context

- Export full conversation in HTML/PDF/JSON formats
### Option 2: Direct Python API

```bash
python -c "from agents import run_research; print(run_research('What are the latest AI trends in 2026?'))"
```

Or in your Python code:
```python
from agents import run_research

result = run_research("Your research query here")
print(result)
```

### Option 3: MCP Server (For Claude Code / Cursor)

Start the MCP server:
```bash
uv run server.py
```

Then configure in your MCP client (e.g., `.cursor/mcp.json` or `.claude/.mcp.json`):

```json
{
  "mcpServers": {
    "crew_research": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/agentic-deep-researcher",
        "run",
        "server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here",
        "TAVILY_API_KEY": "tvly-your-key-here"
      }
    }
  }
}
```

The MCP server exposes a `crew_research(query: str)` tool that returns markdown research reports. Use it like:
> Use the crew_research tool to find AI trends in 2026

## Configuration & Customization

### Modify LLM Model
Edit `agents.py:110` to use different models:
```python
llm = ChatOpenAI(model="gpt-4-turbo", ...)  # or gpt-4, gpt-3.5-turbo
```

### Adjust Search Depth
Edit `agents.py:143` for speed vs. quality tradeoff:
```python
search_depth="basic",    # Fast but less comprehensive
search_depth="advanced", # Slower but more thorough (default)
```

### Change Report Format
Edit the `SYNTHESIZER_SYSTEM_PROMPT` in `agents.py:56` to customize the markdown structure, citation style, or output format.

## Development

### Project Structure
```
├── agents.py          # LangGraph pipeline & state management
├── server.py          # MCP FastMCP server wrapper
├── app.py             # Streamlit UI
├── pyproject.toml     # Dependencies via UV
├── .env.example       # API key template
└── test/              # Test suite & verification scripts
```

### Running Tests
```bash
# Quick environment verification
bash test/verify_setup.sh

# Test imports and environment setup
uv run test/test_imports_only.py

# Verify LangChain & Tavily integration
uv run test/test_langchain.py

# Run full pipeline integration tests
uv run test/test_crew.py
```

### Environment Variables
- `OPENAI_API_KEY` - Required for GPT-4o
- `TAVILY_API_KEY` - Required for web search

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'dotenv'` | Run `uv sync` to install dependencies |
| `OpenAI API key not found` | Ensure `.env` exists and `OPENAI_API_KEY` is set |
| `Tavily API error` | Verify `TAVILY_API_KEY` is valid and not expired |
| `Port 8501 already in use` (Streamlit) | Run on different port: `streamlit run app.py --server.port 8502` |
| `MCP server not responding` | Check absolute path in `.cursor/mcp.json` matches your installation |

## Performance Notes

- **Planning**: ~2-3 seconds (GPT-4o structured output)
- **Searching**: ~2-3 seconds (parallel Tavily searches, 3-4x faster)
- **Synthesizing**: ~5-8 seconds (GPT-4o markdown generation)
- **Total**: ~9-14 seconds per query (30-40% faster with parallelization)

**Cached queries**: <100ms (instant retrieval from cache)

Costs:
- OpenAI GPT-4o: ~$0.01-0.05 per query (1st run only)
- Tavily: ~$0.01 per search (advanced mode, 1st run only)
- **Repeat queries within 24h**: Free (cached results)

