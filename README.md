# Alpha Vantage MCP Server

A Message Control Protocol (MCP) server that provides real-time access to financial market data through the Alpha Vantage API. This server implements a standardized interface for retrieving stock quotes and company information.

## Features

- Real-time stock quotes with price, volume, and change data
- Detailed company information including sector, industry, and market cap
- Standardized MCP interface for easy integration
- Built-in error handling and rate limit management
- Async implementation for efficient request handling

## Installation

The package requires Python 3.12 or higher. Install it using pip:

```bash
pip install alpha-vantage-mcp
```

## Configuration

Before using the server, you need to configure your Alpha Vantage API key. Replace the `API_KEY` constant in `server.py` with your own key:

```python
API_KEY = "your-api-key-here"  # Replace with your Alpha Vantage API key
```

You can obtain an API key from [Alpha Vantage's website](https://www.alphavantage.co/support/#api-key).

## Usage

The server can be started directly using the installed command:

```bash
alpha-vantage-mcp
```

Or run it as a module:

```bash
python -m alpha_vantage_mcp
```

## Available Tools

### get-stock-quote

Retrieves current stock quote information for a given symbol.

**Input Schema:**
```json
{
    "symbol": {
        "type": "string",
        "description": "Stock symbol (e.g., AAPL, MSFT)"
    }
}
```

**Example Response:**
```
Stock quote for AAPL:

Price: $198.50
Change: $2.50 (+1.25%)
Volume: 58942301
High: $199.62
Low: $197.20
```

### get-company-info

Retrieves detailed company information for a given symbol.

**Input Schema:**
```json
{
    "symbol": {
        "type": "string",
        "description": "Stock symbol (e.g., AAPL, MSFT)"
    }
}
```

**Example Response:**
```
Company information for AAPL:

Name: Apple Inc
Sector: Technology
Industry: Consumer Electronics
Market Cap: $3000000000000
Description: Apple Inc. designs, manufactures, and markets smartphones...
Exchange: NASDAQ
Currency: USD
```

## Error Handling

The server includes comprehensive error handling for various scenarios:

- Rate limit exceeded
- Invalid API key
- Network connectivity issues
- Timeout handling
- Malformed responses

Error messages are returned in a clear, human-readable format.

## Development

### Prerequisites

- Python 3.12 or higher
- httpx
- mcp


### Install

#### Claude Desktop

- On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
- On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  ```
  "mcpServers": {
    "alpha-vantage-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/{INSERT_USER}/YOUR/PATH/TO/alpha-vantage-mcp",
        "run",
        "alpha-vantage-mcp"
      ],
      "env": {
        "ALPHA_VANTAGE_API_KEY": "<insert api key>"
      }
    }
  }
  ```
</details>

## Running Locally

In alpha-vantage-mcp repo: `uv run src/alpha_vantage_mcp/server.py`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.