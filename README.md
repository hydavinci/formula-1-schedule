# Formula 1 Schedule MCP Server

A Model Context Protocol (MCP) server that provides comprehensive Formula 1 data including race schedules, standings, and results for any specified year. Built with FastMCP, this server offers reliable access to current and historical F1 data through web scraping.

## Features

- **🏁 Race Calendar**: Fetch Formula 1 race schedules for any year with dates, locations, and round information
- **🏆 Race Results**: Get detailed race results including winners, finishing positions, lap times, and points
- **🏎️ Team Standings**: Access complete constructor/team standings with points, positions, and win statistics
- **👤 Driver Standings**: Retrieve driver championship standings with nationality, team affiliations, and points
- **🔄 Multi-Year Support**: Query data from current and historical F1 seasons
- **⚡ Fast & Reliable**: Robust web scraping with error handling and request optimization
- **🛠️ Easy Integration**: Simple MCP interface with consistent parameter structure

## Installation

### Prerequisites

- Python 3.10 or higher
- uv (recommended) or pip for dependency management
- Docker (optional, for containerized deployment)

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/hydavinci/formula-1-schedule.git
   cd formula-1-schedule
   ```

2. Install dependencies using uv (recommended):
   ```bash
   uv sync
   ```
   
   Or using pip:
   ```bash
   pip install -e .
   ```

3. Run the server:
   ```bash
   # Using uv
   uv run python src/server.py
   
   # Or using the installed script
   formula-1-schedule-mcp-server
   ```

### Docker Setup

To run the server using Docker:

```bash
docker build -t f1-schedule-mcp .
docker run -p 8000:8000 f1-schedule-mcp
```

## Usage

The server exposes four MCP tools, all following the same simple parameter pattern:

### Available Tools

| Tool Name | Description | Example Response |
|-----------|-------------|------------------|
| `fetch_f1_calendar` | Get race schedule for a year | Race dates, circuits, countries, and round numbers |
| `fetch_f1_race_results` | Get race results for a year | Winners, positions, times, and points for each race |
| `fetch_f1_team_standings` | Get constructor standings | Team rankings, points, wins, and statistics |
| `fetch_f1_driver_standings` | Get driver championship standings | Driver rankings, points, teams, and nationality |

### Tool Parameters

All tools use the same parameter structure:
- `year` (string): The year for which to fetch Formula 1 data (e.g., "2024", "2023")

### Example Usage

```json
{
  "name": "fetch_f1_calendar",
  "parameters": {
    "year": "2024"
  }
}
```

### Response Format

All tools return structured data with:
- **Success**: Array of relevant F1 data objects
- **Error**: Error message with context if data retrieval fails

## Configuration

### MCP Client Integration

To use this server with an MCP client, configure it in your client's settings:

```json
{
  "mcpServers": {
    "formula-1-schedule": {
      "command": "formula-1-schedule-mcp-server",
      "args": []
    }
  }
}
```

### Smithery Deployment

The server can be deployed using [Smithery](https://smithery.ai/) with the included `smithery.yaml` configuration.

## Project Structure

```
formula-1-schedule/
├── src/
│   ├── server.py          # MCP server implementation with tool registration
│   ├── fetcher.py         # Core data retrieval and parsing logic
│   └── middleware.py      # Smithery configuration middleware
├── pyproject.toml         # Project configuration and dependencies
├── uv.lock               # Dependency lock file
├── Dockerfile            # Container build configuration
├── smithery.yaml         # Smithery deployment configuration
├── README.md             # This file
└── LICENSE               # MIT License
```

## Technical Details

### Data Sources
- **Primary**: Official Formula 1 website (formula1.com)
- **Parsing**: BeautifulSoup4 for HTML parsing and data extraction
- **Reliability**: Error handling and retry logic for robust data retrieval

### Dependencies

- **fastmcp**: Modern MCP server implementation framework
- **requests**: HTTP client for web scraping
- **beautifulsoup4**: HTML parsing library for data extraction
- **uvicorn**: ASGI server for hosting (development)
- **starlette**: Web framework components

## Development

### Setting up Development Environment

1. Fork and clone the repository
2. Install development dependencies:
   ```bash
   uv sync --dev
   ```

3. Run tests (if available):
   ```bash
   uv run pytest
   ```

4. Format code:
   ```bash
   uv run black src/
   uv run isort src/
   ```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### Common Issues

- **Connection errors**: Check internet connectivity and F1 website availability
- **Parsing errors**: The F1 website structure may have changed; please file an issue
- **Year not found**: Ensure the requested year has F1 data available

### Logging

The server includes comprehensive logging. Set environment variable for debug output:
```bash
export LOG_LEVEL=DEBUG
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Formula 1 for providing race data through their official website
- The MCP (Model Context Protocol) community for the framework
- FastMCP for the server implementation framework