from typing import Any, List, Dict, Optional
import asyncio
import httpx
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import os

# Import functions from tools.py
from .tools import (
    make_alpha_request,
    format_quote,
    format_company_info,
    format_crypto_rate,
    format_time_series,
    format_historical_options,
    ALPHA_VANTAGE_BASE,
    API_KEY
)

# Import functions from technical_indicators.py and futures_strategy.py
from .technical_indicators import (
    get_price_data,
    get_vix_data,
    get_sector_performance,
    get_stock_sector,
    analyze_market_condition,
    generate_setup_report,
    format_analysis_report
)

from .institutional_data import (
    analyze_institutional_activity,
    format_institutional_analysis
)

from .futures_strategy import (
    analyze_futures_trade_setup
)

if not API_KEY:
    raise ValueError("Missing ALPHA_VANTAGE_API_KEY environment variable")

server = Server("alpha_vantage_finance")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="get-stock-quote",
            description="Get current stock quote information",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, MSFT)",
                    },
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="get-company-info",
            description="Get detailed company information",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, MSFT)",
                    },
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="get-crypto-exchange-rate",
            description="Get current cryptocurrency exchange rate",
            inputSchema={
                "type": "object",
                "properties": {
                    "crypto_symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol (e.g., BTC, ETH)",
                    },
                    "market": {
                        "type": "string",
                        "description": "Market currency (e.g., USD, EUR)",
                        "default": "USD"
                    }
                },
                "required": ["crypto_symbol"],
            },
        ),
        types.Tool(
            name="get-time-series",
            description="Get daily time series data for a stock",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, MSFT)",
                    },
                    "outputsize": {
                        "type": "string",
                        "description": "compact (latest 100 data points) or full (up to 20 years of data)",
                        "enum": ["compact", "full"],
                        "default": "compact"
                    }
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="get-historical-options",
            description="Get historical options chain data for a stock with sorting capabilities",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, MSFT)",
                    },
                    "date": {
                        "type": "string",
                        "description": "Optional: Trading date in YYYY-MM-DD format (defaults to previous trading day, must be after 2008-01-01)",
                        "pattern": "^20[0-9]{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])$"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Optional: Number of contracts to return (default: 10, use -1 for all contracts)",
                        "default": 10,
                        "minimum": -1
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "Optional: Field to sort by",
                        "enum": [
                            "strike",
                            "expiration",
                            "volume",
                            "open_interest",
                            "implied_volatility",
                            "delta",
                            "gamma",
                            "theta",
                            "vega",
                            "rho",
                            "last",
                            "bid",
                            "ask"
                        ],
                        "default": "strike"
                    },
                    "sort_order": {
                        "type": "string",
                        "description": "Optional: Sort order",
                        "enum": ["asc", "desc"],
                        "default": "asc"
                    }
                },
                "required": ["symbol"],
            },
        ),
        
        # New futures strategy tools
        types.Tool(
            name="analyze-technical-setup",
            description="Analyze technical setup for statistical mean reversion trading",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, MSFT)",
                    }
                },
                "required": ["symbol"],
            },
        ),
        
        types.Tool(
            name="analyze-institutional-activity",
            description="Analyze institutional activity including options flow and block trades",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, MSFT)",
                    }
                },
                "required": ["symbol"],
            },
        ),
        
        types.Tool(
            name="analyze-futures-trade-setup",
            description="Complete analysis of futures trade setup based on the statistical checklist",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, MSFT)",
                    },
                    "account_value": {
                        "type": "number",
                        "description": "Trading account value in dollars",
                        "default": 100000
                    },
                    "leverage": {
                        "type": "number",
                        "description": "Leverage multiplier (e.g., 10 for 10x leverage)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["symbol"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can fetch financial data and notify clients of changes.
    """
    if not arguments:
        return [types.TextContent(type="text", text="Missing arguments for the request")]

    if name == "get-stock-quote":
        symbol = arguments.get("symbol")
        if not symbol:
            return [types.TextContent(type="text", text="Missing symbol parameter")]

        symbol = symbol.upper()

        async with httpx.AsyncClient() as client:
            quote_data = await make_alpha_request(
                client,
                "GLOBAL_QUOTE",
                symbol
            )

            if isinstance(quote_data, str):
                return [types.TextContent(type="text", text=f"Error: {quote_data}")]

            formatted_quote = format_quote(quote_data)
            quote_text = f"Stock quote for {symbol}:\n\n{formatted_quote}"

            return [types.TextContent(type="text", text=quote_text)]

    elif name == "get-company-info":
        symbol = arguments.get("symbol")
        if not symbol:
            return [types.TextContent(type="text", text="Missing symbol parameter")]

        symbol = symbol.upper()

        async with httpx.AsyncClient() as client:
            company_data = await make_alpha_request(
                client,
                "OVERVIEW",
                symbol
            )

            if isinstance(company_data, str):
                return [types.TextContent(type="text", text=f"Error: {company_data}")]

            formatted_info = format_company_info(company_data)
            info_text = f"Company information for {symbol}:\n\n{formatted_info}"

            return [types.TextContent(type="text", text=info_text)]

    elif name == "get-crypto-exchange-rate":
        crypto_symbol = arguments.get("crypto_symbol")
        if not crypto_symbol:
            return [types.TextContent(type="text", text="Missing crypto_symbol parameter")]

        market = arguments.get("market", "USD")
        crypto_symbol = crypto_symbol.upper()
        market = market.upper()

        async with httpx.AsyncClient() as client:
            crypto_data = await make_alpha_request(
                client,
                "CURRENCY_EXCHANGE_RATE",
                None,
                {
                    "from_currency": crypto_symbol,
                    "to_currency": market
                }
            )

            if isinstance(crypto_data, str):
                return [types.TextContent(type="text", text=f"Error: {crypto_data}")]

            formatted_rate = format_crypto_rate(crypto_data)
            rate_text = f"Cryptocurrency exchange rate for {crypto_symbol}/{market}:\n\n{formatted_rate}"

            return [types.TextContent(type="text", text=rate_text)]

    elif name == "get-time-series":
        symbol = arguments.get("symbol")
        if not symbol:
            return [types.TextContent(type="text", text="Missing symbol parameter")]

        symbol = symbol.upper()
        outputsize = arguments.get("outputsize", "compact")

        async with httpx.AsyncClient() as client:
            time_series_data = await make_alpha_request(
                client,
                "TIME_SERIES_DAILY",
                symbol,
                {"outputsize": outputsize}
            )

            if isinstance(time_series_data, str):
                return [types.TextContent(type="text", text=f"Error: {time_series_data}")]

            formatted_series = format_time_series(time_series_data)
            series_text = f"Time series data for {symbol}:\n\n{formatted_series}"

            return [types.TextContent(type="text", text=series_text)]

    elif name == "get-historical-options":
        symbol = arguments.get("symbol")
        date = arguments.get("date")
        limit = arguments.get("limit", 10)
        sort_by = arguments.get("sort_by", "strike")
        sort_order = arguments.get("sort_order", "asc")

        if not symbol:
            return [types.TextContent(type="text", text="Missing symbol parameter")]

        symbol = symbol.upper()

        async with httpx.AsyncClient() as client:
            params = {}
            if date:
                params["date"] = date

            options_data = await make_alpha_request(
                client,
                "HISTORICAL_OPTIONS",
                symbol,
                params
            )

            if isinstance(options_data, str):
                return [types.TextContent(type="text", text=f"Error: {options_data}")]

            formatted_options = format_historical_options(options_data, limit, sort_by, sort_order)
            options_text = f"Historical options data for {symbol}"
            if date:
                options_text += f" on {date}"
            options_text += f":\n\n{formatted_options}"

            return [types.TextContent(type="text", text=options_text)]
            
    # New futures strategy handlers
    elif name == "analyze-technical-setup":
        symbol = arguments.get("symbol")
        if not symbol:
            return [types.TextContent(type="text", text="Missing symbol parameter")]

        symbol = symbol.upper()

        try:
            async with httpx.AsyncClient() as client:
                # Get market condition data
                vix_df = await get_vix_data(client)
                sp500_df = await get_price_data(client, "^GSPC")
                sector_data = await get_sector_performance(client)
                stock_sector = await get_stock_sector(client, symbol)
                
                # Get asset-specific data
                asset_df = await get_price_data(client, symbol)
                
                # Analyze market conditions
                market_condition = analyze_market_condition(
                    sp500_df,
                    vix_df,
                    sector_data,
                    stock_sector
                )
                
                # Generate setup report
                setup_report = generate_setup_report(
                    symbol,
                    asset_df,
                    market_condition
                )
                
                # Format the report
                formatted_report = format_analysis_report(setup_report)
                
                return [types.TextContent(type="text", text=formatted_report)]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error analyzing technical setup: {str(e)}")]
            
    elif name == "analyze-institutional-activity":
        symbol = arguments.get("symbol")
        if not symbol:
            return [types.TextContent(type="text", text="Missing symbol parameter")]

        symbol = symbol.upper()

        try:
            async with httpx.AsyncClient() as client:
                # Analyze institutional activity
                institutional_analysis = await analyze_institutional_activity(client, symbol)
                
                # Format the report
                formatted_report = format_institutional_analysis(institutional_analysis)
                
                return [types.TextContent(type="text", text=formatted_report)]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error analyzing institutional activity: {str(e)}")]
            
    elif name == "analyze-futures-trade-setup":
        symbol = arguments.get("symbol")
        if not symbol:
            return [types.TextContent(type="text", text="Missing symbol parameter")]

        symbol = symbol.upper()
        account_value = float(arguments.get("account_value", 100000))
        leverage = float(arguments.get("leverage", 10))

        try:
            async with httpx.AsyncClient() as client:
                # Complete futures trade setup analysis
                analysis = await analyze_futures_trade_setup(
                    client,
                    symbol,
                    account_value,
                    leverage
                )
                
                if "error" in analysis:
                    return [types.TextContent(type="text", text=f"Error analyzing trade setup: {analysis['error']}")]
                
                # Return the formatted report
                return [types.TextContent(type="text", text=analysis["formatted_report"])]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error analyzing futures trade setup: {str(e)}")]

    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="alpha_vantage_finance",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

# This is needed if you'd like to connect to a custom client
if __name__ == "__main__":
    asyncio.run(main())
