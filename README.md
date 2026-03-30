# 🔍 MCP Deep Researcher

A multi-agent research system that decomposes complex queries into targeted sub-questions, searches the web in parallel, scores source credibility, and synthesizes findings into structured markdown reports — accessible via **Streamlit UI**, **MCP tool** (Claude Code / Cursor), or **Python API**.

**[Try the live demo →](https://sid12super-mcp-deep-researcher.streamlit.app/)**

---

## What It Does

Give it a broad research question. It returns a structured report with executive summary, key findings, knowledge gaps, and cited sources — in about 10 seconds.

```
"What are the latest developments in multi-agent AI systems?"
```

↓

```markdown
# Research Report: Multi-Agent AI Systems — Latest Developments

## Executive Summary
...

## Key Findings
### How are multi-agent frameworks evolving in 2026?
... [source](https://...) [credibility: high]

## Knowledge Gaps
- No peer-reviewed benchmarks comparing LangGraph vs CrewAI at scale
- ...

## Sources
1. https://arxiv.org/... [high]
2. https://techcrunch.com/... [medium]
```

---

## Architecture

Three-node LangGraph pipeline with typed state, parallel search, and 24-hour result caching:

```
┌──────────┐     ┌────────────────┐     ┌──────────────┐
│ Planner  │────▶│    Searcher    │────▶│ Synthesizer  │
│ (GPT-4o) │     │ (Tavily ×5)   │     │  (GPT-4o)    │
└──────────┘     └────────────────┘     └──────────────┘
     │                  │                      │
     ▼                  ▼                      ▼
 3-5 targeted    Parallel searches      Markdown report
 sub-questions   with credibility       with citations
                 scoring                and knowledge gaps
```

**Planner** — Decomposes the query into 3–5 non-overlapping sub-questions using GPT-4o structured output (Pydantic). Context-aware: follow-up queries build on prior research instead of repeating it.

**Searcher** — Fires all searches concurrently via `ThreadPoolExecutor`. Each result is tagged with a credibility score (high / medium / unverified) based on domain authority. Graceful per-question error handling.

**Synthesizer** — Analyzes all evidence, weights high-credibility sources when findings conflict, and produces a structured report at `temperature=0.2` for consistency.

**Cache** — SHA-256 hash of (query + context + search depth). 24-hour TTL. Repeat queries return in <100ms.

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- API keys for [OpenAI](https://platform.openai.com/api-keys) and [Tavily](https://app.tavily.com/home)

### Install

```bash
git clone https://github.com/sid12super/MCP-Deep-Researcher.git
cd MCP-Deep-Researcher
uv sync
cp .env.example .env
# Add your API keys to .env
```

---

## Usage

### Streamlit UI

```bash
streamlit run app.py
```

Opens at `http://localhost:8501` with:
- Real-time progress tracking (planning → searching → synthesizing)
- Search depth toggle (basic / advanced)
- Multi-turn conversation with context carry-over
- Export full research conversation as HTML, PDF, or JSON
- "New Research Topic" button to reset context

### MCP Server (Claude Code / Cursor)

The MCP server exposes the full research pipeline as a tool with Pydantic-validated input, search depth control, and multi-turn conversation support.

**Start the server:**

```bash
uv run server.py
```

**Configure your MCP client** — create `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "deep_researcher_mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/MCP-Deep-Researcher",
        "run",
        "server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "TAVILY_API_KEY": "tvly-..."
      }
    }
  }
}
```

**Use it in Claude Code:**

```
Use deep_researcher_research to find the latest developments in multi-agent AI systems
```

```
Use deep_researcher_research with search_depth "basic" for a quick comparison of LangGraph vs CrewAI
```

```
Use deep_researcher_research to follow up on that — pass the previous report as conversation_context
```

The tool accepts three parameters:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Research question (3–2000 chars) |
| `search_depth` | `"basic"` \| `"advanced"` | `"advanced"` | Speed vs. thoroughness tradeoff |
| `conversation_context` | string | `""` | Prior research for multi-turn follow-ups |

### Python API

```python
from agents import run_research

# Simple query
report = run_research("What are the latest AI trends in 2026?")

# With options
report = run_research(
    "How does this compare to 2025?",
    conversation_context="Previous findings: ...",
    search_depth="basic",
)

# Full state (for programmatic access)
result = run_research("Your query", return_full_state=True)
# result["report"], result["query"], result["research_questions"]
```

---

## Features

### Search Depth Control
Toggle between `basic` (faster, ~8s) and `advanced` (comprehensive, ~14s) from the Streamlit sidebar or as an MCP parameter. Each depth caches separately.

### Multi-turn Conversation
Follow-up queries automatically receive prior research context. The planner generates deeper, non-redundant questions instead of repeating covered ground. Reset anytime with "New Research Topic."

### Export Formats
Download the full research conversation (all queries and reports) as:
- **HTML** — styled, web-ready
- **PDF** — professional, print-ready (via ReportLab)
- **JSON** — structured, machine-readable

### Source Credibility Scoring
Every source is automatically classified:
- **High** — peer-reviewed, government, major outlets (arxiv.org, reuters.com, nih.gov, etc.)
- **Medium** — established tech/business (techcrunch.com, wikipedia.org, bloomberg.com, etc.)
- **Unverified** — everything else

The synthesizer weights high-credibility sources more heavily when findings conflict.

### Real-time Progress
Streamlit UI shows live status updates as each pipeline stage completes — questions generated, results retrieved, report synthesized. Cache hits display instantly.

### Caching
Results are cached by SHA-256 hash of (query + conversation context + search depth) with a 24-hour TTL. Identical requests return in <100ms at zero cost.

---

## Project Structure

```
├── agents.py          # LangGraph pipeline, nodes, caching, credibility scoring
├── server.py          # MCP server (FastMCP, Pydantic input, async)
├── app.py             # Streamlit UI (chat, exports, progress, sidebar)
├── pyproject.toml     # Dependencies (uv)
├── .env.example       # API key template
├── .mcp.json          # MCP client config (gitignored — contains keys)
├── CLAUDE.md          # Claude Code development context
└── test/              # Import, integration, and pipeline tests
```

---

## Performance

| Stage | Time | Notes |
|-------|------|-------|
| Planner | ~2-3s | GPT-4o structured output |
| Searcher | ~2-3s | Parallel via ThreadPoolExecutor |
| Synthesizer | ~5-8s | GPT-4o at temperature=0.2 |
| **Total** | **~9-14s** | First run |
| **Cached** | **<100ms** | Repeat queries within 24h |

**Cost per unique query:** ~$0.06-0.10 (GPT-4o + Tavily)
**Cost per cached query:** $0.00

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | Run `uv sync` |
| `OpenAI API key not found` | Check `.env` exists with `OPENAI_API_KEY` |
| `Tavily API error` | Verify key at [app.tavily.com](https://app.tavily.com) |
| Port 8501 in use | `streamlit run app.py --server.port 8502` |
| MCP server not found | Ensure `.mcp.json` is at project root (not inside `.claude/`) |
| MCP server failed | Test with `uv run server.py` directly to see errors |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM | [OpenAI GPT-4o](https://platform.openai.com/) |
| Web search | [Tavily](https://tavily.com/) |
| MCP server | [FastMCP](https://modelcontextprotocol.io/) (Python SDK) |
| Web UI | [Streamlit](https://streamlit.io/) |
| PDF export | [ReportLab](https://www.reportlab.com/) |
| Dependency management | [uv](https://github.com/astral-sh/uv) |