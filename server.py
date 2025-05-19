from mcp.server.fastmcp import FastMCP
from fetcher import fetch_f1_calendar_internal

mcp = FastMCP("Region Weather")


@mcp.tool("fetch_f1_calendar")
async def fetch_f1_calendar(year: str):
    """
    MCP handler to fetch Formula 1 race calendar for a specified year

    Args:
      year (str): The year for which to fetch the F1 calendar

    Returns:
      dict: F1 calendar information for the specified year
    """
    return fetch_f1_calendar_internal(year)


if __name__ == "__main__":
    mcp.run()
