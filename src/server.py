
import os
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from middleware import SmitheryConfigMiddleware
from typing import Optional, Dict, Any
from fetcher import fetch_race_calendar, fetch_team_standings, fetch_driver_standings, fetch_race_results

# Initialize FastMCP with correct service name
mcp = FastMCP("Formula 1 Schedule")

def handle_config(config: dict):
    """Handle configuration from Smithery - for backwards compatibility with stdio mode."""
    global _server_token
    if server_token := config.get('serverToken'):
        _server_token = server_token
    # You can handle other session config fields here

# Store server token only for stdio mode (backwards compatibility)
_server_token: Optional[str] = None

def get_request_config() -> dict:
    """Get full config from current request context."""
    try:
        # Access the current request context from FastMCP
        import contextvars
        
        # Try to get from request context if available
        request = contextvars.copy_context().get('request')
        if hasattr(request, 'scope') and request.scope:
            return request.scope.get('smithery_config', {})
    except:
        pass

def get_config_value(key: str, default=None):
    """Get a specific config value from current request."""
    config = get_request_config()
    return config.get(key, default)

def validate_server_access(server_token: Optional[str]) -> bool:
    """Validate server token - accepts any string including empty ones for demo."""
    # In a real app, you'd validate against your server's auth system
    # For demo purposes, we accept any non-empty token
    return server_token is not None and len(server_token.strip()) > 0 if server_token else True

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


# Register F1 race results tool
@mcp.tool("fetch_f1_race_results")
async def fetch_f1_race_results_handler(year: str) -> Dict[str, Any]:
  """
  Fetches Formula 1 race results data for a specified year
  
  Args:
    year: The year for which to fetch F1 data (e.g., '2024', '2025')
    
  Returns:
    Dictionary with F1 race results information
  """
  return fetch_race_results(year)


def main():
    transport_mode = os.getenv("TRANSPORT", "stdio")
    
    if transport_mode == "http":
        # HTTP mode with config extraction from URL parameters
        print("Formula 1 Schedule MCP Server starting in HTTP mode...")
        
        # Setup Starlette app with CORS for cross-origin requests
        app = mcp.streamable_http_app()
        
        # IMPORTANT: add CORS middleware for browser based clients
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["mcp-session-id", "mcp-protocol-version"],
            max_age=86400,
        )

        # Apply custom middleware for config extraction (per-request API key handling)
        app = SmitheryConfigMiddleware(app)

        # Use Smithery-required PORT environment variable
        port = int(os.environ.get("PORT", 8081))
        print(f"Listening on port {port}")

        uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")
    
    else:
        # Optional: add stdio transport for backwards compatibility
        # You can publish this to uv for users to run locally
        print("Formula 1 Schedule MCP Server starting in stdio mode...")
        
        server_token = os.getenv("SERVER_TOKEN")
        # Set the server token for stdio mode (can be None)
        handle_config({"serverToken": server_token})
        
        # Run with stdio transport (default)
        mcp.run()

if __name__ == "__main__":
    main()