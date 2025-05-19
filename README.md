# Formula 1 Schedule MCP Server

A Model Context Protocol (MCP) server that provides Formula 1 race schedules for any specified year. The server can retrieve current and historical F1 race calendars with detailed information about each race.

## Features

- Fetch Formula 1 race calendars for any year
- Automatic fallback to previous years if data for the requested year isn't available
- Multiple API sources to ensure data reliability
- Response caching for improved performance
- Comprehensive race information including dates, circuit details, and session times

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

The server exposes the following MCP tool:

### `fetch_f1_calendar`

Retrieves the Formula 1 race calendar for a specified year.

**Parameters:**
- `year` (string): The year for which to fetch the F1 calendar

**Returns:**
- JSON object with Formula 1 calendar information for the specified year

**Example Request:**
```json
{
  "name": "fetch_f1_calendar",
  "parameters": {
    "year": "2025"
  }
}
```

## Configuration

The server can be configured using the `smithery.yaml` file for deployment with [Smithery](https://smithery.ai/).

## Dependencies

- fastmcp: MCP server implementation
- requests: HTTP client for API requests
- beautifulsoup4: HTML parsing library
- typing-extensions: Extended type hints

## Development

The project structure is organized as follows:

- `server.py`: MCP server implementation
- `fetcher.py`: F1 calendar data retrieval logic
- `requirements.txt`: Python dependencies
- `Dockerfile`: Container definition
- `smithery.yaml`: Smithery configuration

## License

See the [LICENSE](LICENSE) file for details.