import asyncio
from mcp.server.fastmcp import FastMCP
from agents import run_research

# Create FastMCP instance
mcp = FastMCP("crew_research")

@mcp.tool()
async def crew_research(query: str) -> str:
    """Run LangGraph-based research system for given user query using OpenAI and Tavily search.

    Args:
        query (str): The research query or question.

    Returns:
        str: A comprehensive markdown research report with findings, gaps, and sources.
    """
    return run_research(query)


# Run the server
if __name__ == "__main__":
    mcp.run(transport="stdio")


# Add this inside ./.cursor/mcp.json
# {
#   "mcpServers": {
#     "crew_research": {
#       "command": "uv",
#       "args": [
#         "--directory",
#         "/path/to/Multi-Agent-deep-researcher-mcp-windows-linux",
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
