# Alpha Vantage MCP Server

A Model Context Protocol (MCP) server that provides real-time access to financial market data through the free [Alpha Vantage API](https://www.alphavantage.co/documentation/). This server implements a standardized interface for retrieving stock quotes and company information.

## Features

- Real-time stock quotes with price, volume, and change data
- Detailed company information including sector, industry, and market cap
- Built-in error handling and rate limit management

## Installation

#### Claude Desktop

- On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
- On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<summary>Development/Unpublished Servers Configuration</summary>

```json
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


### Running Locally
After connecting Claude client with the MCP tool via json file, run the server:
In alpha-vantage-mcp repo: `uv run src/alpha_vantage_mcp/server.py`

## Available Tools

The server implements two tools:
- `get-stock-quote`: Get the latest stock quote for a specific company
- `get-company-info`: Get stock-related information for a specific company

### get-stock-quote

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

## Prerequisites

- Python 3.12 or higher
- httpx
- mcp

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.