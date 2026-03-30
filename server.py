import asyncio
from enum import Enum
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict
from agents import run_research

# ============================================================================
# MCP SERVER — deep_researcher_mcp
# ============================================================================

mcp = FastMCP("deep_researcher_mcp")


# ============================================================================
# INPUT MODELS
# ============================================================================

class SearchDepth(str, Enum):
    """Tavily search depth control."""
    BASIC = "basic"
    ADVANCED = "advanced"


class ResearchInput(BaseModel):
    """Validated input for the deep research tool."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    query: str = Field(
        ...,
        description="The research query or question (e.g., 'What are the latest trends in agentic AI?')",
        min_length=3,
        max_length=2000,
    )
    search_depth: SearchDepth = Field(
        default=SearchDepth.ADVANCED,
        description="Search quality/speed tradeoff: 'advanced' (thorough, ~15s) or 'basic' (faster, ~8s)",
    )
    conversation_context: str = Field(
        default="",
        description="Optional prior research context for multi-turn follow-ups. Pass previous report summaries here to get deeper, non-redundant follow-up research.",
        max_length=5000,
    )


# ============================================================================
# TOOLS
# ============================================================================

@mcp.tool(
    name="deep_researcher_research"
)
async def deep_researcher_research(params: ResearchInput) -> str:
    """Run a multi-agent research pipeline that decomposes a query into sub-questions,
    searches the web in parallel via Tavily, scores source credibility, and synthesizes
    a comprehensive markdown report with findings, knowledge gaps, and cited sources.

    The pipeline has three stages:
      1. Planner — breaks the query into 3-5 targeted sub-questions (GPT-4o)
      2. Searcher — runs parallel Tavily web searches with credibility scoring
      3. Synthesizer — produces a structured markdown report (GPT-4o)

    Results are cached for 24 hours. Identical (query + context + depth) combinations
    return instantly on subsequent calls.

    Args:
        params (ResearchInput): Validated input containing:
            - query (str): The research question (3-2000 chars)
            - search_depth (SearchDepth): 'basic' for speed or 'advanced' for depth
            - conversation_context (str): Prior research for multi-turn follow-ups

    Returns:
        str: Markdown research report with executive summary, key findings per
             sub-question, knowledge gaps, and numbered source citations with
             credibility tags (high/medium/unverified).
    """
    try:
        report = await asyncio.to_thread(
            run_research,
            params.query,
            conversation_context=params.conversation_context,
            search_depth=params.search_depth.value,
        )
        return report
    except Exception as e:
        error_type = type(e).__name__
        if "OPENAI_API_KEY" in str(e) or "openai" in str(e).lower():
            return f"Error: OpenAI API key is missing or invalid. Set OPENAI_API_KEY in your environment. ({error_type})"
        if "TAVILY" in str(e) or "tavily" in str(e).lower():
            return f"Error: Tavily API key is missing or invalid. Set TAVILY_API_KEY in your environment. ({error_type})"
        return f"Error: Research pipeline failed — {error_type}: {str(e)[:200]}. Try a shorter or broader query."


# ============================================================================
# ENTRYPOINT
# ============================================================================

if __name__ == "__main__":
    mcp.run(transport="stdio")


# ============================================================================
# MCP CLIENT CONFIGURATION
# ============================================================================
# Add to .cursor/mcp.json or .claude/mcp.json:
#
# {
#   "mcpServers": {
#     "deep_researcher_mcp": {
#       "command": "uv",
#       "args": [
#         "--directory",
#         "/absolute/path/to/MCP-Deep-Researcher",
#         "run",
#         "server.py"
#       ],
#       "env": {
#         "OPENAI_API_KEY": "sk-...",
#         "TAVILY_API_KEY": "tvly-..."
#       }
#     }
#   }
# }