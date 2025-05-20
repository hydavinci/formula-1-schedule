from typing import Dict, Any, Callable
from mcp.server.fastmcp import FastMCP
from fetcher import fetch_race_calendar, fetch_team_standings, fetch_driver_standings

# Initialize FastMCP with correct service name and longer timeout
mcp = FastMCP("Formula 1 Schedule", timeout=60)  # 60 seconds timeout


# Helper function to register tools with consistent naming and behavior
def register_f1_tool(name_suffix: str, fetcher_func: Callable):
    """
    Register an MCP tool with standardized naming and documentation.
    
    Args:
        name_suffix: Suffix for the tool name after 'fetch_f1_'
        fetcher_func: The implementation function to call
    """
    @mcp.tool(f"fetch_f1_{name_suffix}")
    async def handler(year: str) -> Dict[str, Any]:
        """
        Fetches Formula 1 {name_suffix.replace('_', ' ')} data for a specified year
        
        Args:
            year: The year for which to fetch F1 data (e.g., '2024', '2025')
            
        Returns:
            Dictionary with F1 {name_suffix.replace('_', ' ')} information
        """
        return fetcher_func(year)


# Register all tools
register_f1_tool("calendar", fetch_race_calendar)
register_f1_tool("team_standings", fetch_team_standings)
register_f1_tool("driver_standings", fetch_driver_standings)


if __name__ == "__main__":
    mcp.run()
