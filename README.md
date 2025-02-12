# Alpha Vantage MCP Server

A Model Context Protocol (MCP) server that provides real-time access to financial market data through the free [Alpha Vantage API](https://www.alphavantage.co/documentation/). This server implements a standardized interface for retrieving stock quotes and company information.

<a href="https://glama.ai/mcp/servers/0wues5td08"><img width="380" height="200" src="https://glama.ai/mcp/servers/0wues5td08/badge" alt="AlphaVantage-MCP MCP server" /></a>

## Features

- Real-time stock quotes with price, volume, and change data
- Detailed company information including sector, industry, and market cap
- Real-time cryptocurrency exchange rates with bid/ask prices
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

### Install packages
```
uv install -e .
```

### Running

After connecting Claude client with the MCP tool via json file and installing the packages, Claude should see the server's mcp tools:

You can run the sever yourself via:
In alpha-vantage-mcp repo: 
```
uv run src/alpha_vantage_mcp/server.py
```

with inspector
```
* npx @modelcontextprotocol/inspector uv --directory /Users/{INSERT_USER}/YOUR/PATH/TO/alpha-vantage-mcp run src/alpha_vantage_mcp/server.py `
```

## Available Tools

The server implements four tools:
- `get-stock-quote`: Get the latest stock quote for a specific company
- `get-company-info`: Get stock-related information for a specific company
- `get-crypto-exchange-rate`: Get current cryptocurrency exchange rates
- `get-time-series`: Get historical daily price data for a stock

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

### get-crypto-exchange-rate

Retrieves real-time cryptocurrency exchange rates with additional market data.

**Input Schema:**
```json
{
    "crypto_symbol": {
        "type": "string",
        "description": "Cryptocurrency symbol (e.g., BTC, ETH)"
    },
    "market": {
        "type": "string",
        "description": "Market currency (e.g., USD, EUR)",
        "default": "USD"
    }
}
```

**Example Response:**
```
Cryptocurrency exchange rate for BTC/USD:

From: Bitcoin (BTC)
To: United States Dollar (USD)
Exchange Rate: 43521.45000
Last Updated: 2024-12-17 19:45:00 UTC
Bid Price: 43521.00000
Ask Price: 43522.00000
```

### get-time-series

Retrieves daily time series (OHLCV) data.

**Input Schema:**
```json
{
    "symbol": {
        "type": "string",
        "description": "Stock symbol (e.g., AAPL, MSFT)"
    },
    "outputsize": {
        "type": "string",
        "description": "compact (latest 100 data points) or full (up to 20 years of data)",
        "default": "compact"
    }
}
```
**Example Response:**
```
Time Series Data for AAPL (Last Refreshed: 2024-12-17 16:00:00):

Date: 2024-12-16
Open: $195.09
High: $197.68
Low: $194.83
Close: $197.57
Volume: 55,751,011
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

## License
This MCP server is licensed under the MIT License. 
This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
