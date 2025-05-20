from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from fetcher import fetch_race_calendar

# Initialize FastMCP with correct service name and longer timeout
mcp = FastMCP("Formula 1 Schedule", timeout=60)  # 60 seconds timeout


@mcp.tool("fetch_f1_calendar")
async def fetch_f1_calendar(year: str) -> Dict[str, Any]:
    """
    MCP handler to fetch Formula 1 race calendar for a specified year

    Args:
      year (str): The year for which to fetch the F1 calendar

    Returns:
      Dict[str, Any]: F1 calendar information for the specified year
    """
    return fetch_race_calendar(year)


if __name__ == "__main__":
    mcp.run()
