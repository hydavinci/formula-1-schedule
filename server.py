from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from fetcher import fetch_race_calendar, fetch_team_standings, fetch_driver_standings

# Initialize FastMCP with correct service name and longer timeout
mcp = FastMCP("Formula 1 Schedule", timeout=60)  # 60 seconds timeout


# Register F1 calendar tool
@mcp.tool("fetch_f1_calendar")
async def fetch_f1_calendar_handler(year: str) -> Dict[str, Any]:
  """
  Fetches Formula 1 calendar data for a specified year
  
  Args:
    year: The year for which to fetch F1 data (e.g., '2024', '2025')
    
  Returns:
    Dictionary with F1 calendar information
  """
  return fetch_race_calendar(year)


# Register F1 team standings tool
@mcp.tool("fetch_f1_team_standings")
async def fetch_f1_team_standings_handler(year: str) -> Dict[str, Any]:
  """
  Fetches Formula 1 team standings data for a specified year
  
  Args:
    year: The year for which to fetch F1 data (e.g., '2024', '2025')
    
  Returns:
    Dictionary with F1 team standings information
  """
  return fetch_team_standings(year)


# Register F1 driver standings tool
@mcp.tool("fetch_f1_driver_standings")
async def fetch_f1_driver_standings_handler(year: str) -> Dict[str, Any]:
  """
  Fetches Formula 1 driver standings data for a specified year
  
  Args:
    year: The year for which to fetch F1 data (e.g., '2024', '2025')
    
  Returns:
    Dictionary with F1 driver standings information
  """
  return fetch_driver_standings(year)


if __name__ == "__main__":
    mcp.run()
