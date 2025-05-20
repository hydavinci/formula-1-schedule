import logging
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from fetcher import fetch_f1_calendar_internal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('f1_server')

# Initialize FastMCP with correct service name
mcp = FastMCP("Formula 1 Schedule")


@mcp.tool("fetch_f1_calendar")
async def fetch_f1_calendar(year: str) -> Dict[str, Any]:
    """
    MCP handler to fetch Formula 1 race calendar for a specified year

    Args:
      year (str): The year for which to fetch the F1 calendar

    Returns:
      Dict[str, Any]: F1 calendar information for the specified year
    """
    try:
        races, year_used, status = fetch_f1_calendar_internal(year)
        
        # Format the response in a clean structure
        return {
            "races": races,
            "year": year_used,
            "status": status,
            "count": len(races)
        }
    except Exception as e:
        logger.error(f"Error fetching F1 calendar: {e}")
        return {
            "races": [],
            "year": year,
            "status": "error",
            "error_message": str(e),
            "count": 0        }


if __name__ == "__main__":
    mcp.run()
