# Formula 1 Schedule MCP Server

A Model Context Protocol (MCP) server that provides Formula 1 race schedules for any specified year. The server can retrieve current and historical F1 race calendars with detailed information about each race.

## Features

- **Race Data**: Fetch Formula 1 race calendars for any year with dates, locations and round information
- **Team Stats**: Get complete team standings with points and positions for current/past seasons
- **Driver Stats**: Access driver standings with details including nationality, team, and code
- **Data Reliability**: Robust parsing of Formula 1 website with error handling
- **Simple Integration**: Easy-to-use MCP interface with consistent parameter structure

## Installation

### Prerequisites

- Python 3.8 or higher
- Docker (optional, for containerized deployment)

### Local Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd formula-1-schedule
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the server:
   ```
   python server.py
   ```

### Docker Setup

To run the server using Docker:

```
docker build -t f1-schedule-mcp .
docker run -p 8000:8000 f1-schedule-mcp
```

## Usage

The server exposes three MCP tools, all following the same simple parameter pattern:

### Available Tools

| Tool Name | Description | Example Use |
|-----------|-------------|-------------|
| `fetch_f1_calendar` | Get race schedule for a year | `{"name": "fetch_f1_calendar", "parameters": {"year": "2025"}}` |
| `fetch_f1_team_standings` | Get team standings | `{"name": "fetch_f1_team_standings", "parameters": {"year": "2025"}}` |
| `fetch_f1_driver_standings` | Get driver standings | `{"name": "fetch_f1_driver_standings", "parameters": {"year": "2025"}}` |

### Parameters

All tools use the same parameter:
- `year` (string): The year for which to fetch Formula 1 data

## Configuration

The server can be configured using the `smithery.yaml` file for deployment with [Smithery](https://smithery.ai/).

## Project Structure

| File | Description |
|------|-------------|
| `server.py` | MCP server implementation with tool registration |
| `fetcher.py` | Core data retrieval logic with shared parsing functions |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Container build configuration |
| `smithery.yaml` | Smithery deployment configuration |

## Dependencies

- **fastmcp**: MCP server implementation
- **requests**: HTTP client for API requests
- **beautifulsoup4**: HTML parsing for data extraction
- **typing-extensions**: Type hints

## License

See the [LICENSE](LICENSE) file for details.