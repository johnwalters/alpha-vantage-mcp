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

# Import mean reversion tools
from .mean_reversion_tools import (
    get_vix_trend,
    check_sp500_above_ma,
    get_bollinger_bands,
    calculate_rsi,
    check_volume_climax,
    check_mean_reversion_setup,
    format_mean_reversion_analysis
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
        # Original tools
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
        # Mean reversion tools
        types.Tool(
            name="get-vix-trend",
            description="Check if VIX has been declining for a specified number of days",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to check for declining trend",
                        "default": 3,
                        "minimum": 2,
                        "maximum": 10
                    }
                }
            },
        ),
        types.Tool(
            name="check-market-condition",
            description="Check if S&P 500 is above its moving average",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "integer",
                        "description": "Moving average period in days",
                        "default": 20,
                        "minimum": 5,
                        "maximum": 200
                    }
                }
            },
        ),
        types.Tool(
            name="get-bollinger-bands",
            description="Calculate Bollinger Bands for a given symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, MSFT)"
                    },
                    "period": {
                        "type": "integer",
                        "description": "Period for moving average",
                        "default": 20,
                        "minimum": 5,
                        "maximum": 100
                    },
                    "std_dev": {
                        "type": "integer",
                        "description": "Number of standard deviations",
                        "default": 2,
                        "minimum": 1,
                        "maximum": 3
                    }
                },
                "required": ["symbol"]
            },
        ),
        types.Tool(
            name="calculate-rsi",
            description="Calculate RSI for a given symbol, useful for short-term mean reversion signals",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, MSFT)"
                    },
                    "period": {
                        "type": "integer",
                        "description": "RSI period (2 is recommended for short-term mean reversion)",
                        "default": 2,
                        "minimum": 2,
                        "maximum": 14
                    }
                },
                "required": ["symbol"]
            },
        ),
        types.Tool(
            name="check-volume-climax",
            description="Check if volume is higher than the specified threshold of the 10-day average",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, MSFT)"
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Volume multiple of average to consider a climax",
                        "default": 1.5,
                        "minimum": 1.2,
                        "maximum": 3.0
                    }
                },
                "required": ["symbol"]
            },
        ),
        types.Tool(
            name="analyze-mean-reversion",
            description="Check for a complete mean reversion setup based on multiple indicators",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, MSFT)"
                    },
                    "rsi_threshold": {
                        "type": "number",
                        "description": "RSI level to consider oversold",
                        "default": 10.0,
                        "minimum": 5.0,
                        "maximum": 30.0
                    },
                    "volume_threshold": {
                        "type": "number",
                        "description": "Volume multiple to consider a climax",
                        "default": 1.5,
                        "minimum": 1.2,
                        "maximum": 3.0
                    }
                },
                "required": ["symbol"]
            },
        ),
        types.Tool(
            name="get-sector-performance",
            description="Get sector performance data to identify sectors with positive relative strength",
            inputSchema={
                "type": "object",
                "properties": {}
            },
        ),
        types.Tool(
            name="get-atr",
            description="Calculate Average True Range (ATR) for volatility measurement",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, MSFT)"
                    },
                    "period": {
                        "type": "integer",
                        "description": "ATR period in days",
                        "default": 14,
                        "minimum": 5,
                        "maximum": 30
                    }
                },
                "required": ["symbol"]
            },
        ),
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
        arguments = {}

    # Original tools
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
            
    # Mean Reversion Tool Handlers
    elif name == "get-vix-trend":
        days = arguments.get("days", 3)
        
        async with httpx.AsyncClient() as client:
            is_declining, pct_change = await get_vix_trend(client, days)
            
            result_text = (
                f"VIX Trend Analysis (Last {days} days):\n\n"
                f"Trend: {'DECLINING' if is_declining else 'RISING'}\n"
                f"Percentage Change: {pct_change:.2f}%\n\n"
                f"Mean Reversion Signal: {'FAVORABLE' if is_declining else 'UNFAVORABLE'}"
            )
            
            return [types.TextContent(type="text", text=result_text)]
            
    elif name == "check-market-condition":
        period = arguments.get("period", 20)
        
        async with httpx.AsyncClient() as client:
            above_ma = await check_sp500_above_ma(client, period)
            
            result_text = (
                f"S&P 500 Market Condition Analysis:\n\n"
                f"Current S&P 500 position: {'ABOVE' if above_ma else 'BELOW'} {period}-day Moving Average\n\n"
                f"Mean Reversion Signal (Long): {'FAVORABLE' if above_ma else 'UNFAVORABLE'}\n"
                f"Mean Reversion Signal (Short): {'UNFAVORABLE' if above_ma else 'FAVORABLE'}"
            )
            
            return [types.TextContent(type="text", text=result_text)]
            
    elif name == "get-bollinger-bands":
        symbol = arguments.get("symbol")
        if not symbol:
            return [types.TextContent(type="text", text="Missing symbol parameter")]
            
        symbol = symbol.upper()
        period = arguments.get("period", 20)
        std_dev = arguments.get("std_dev", 2)
        
        async with httpx.AsyncClient() as client:
            bbands = await get_bollinger_bands(client, symbol, period, std_dev)
            
            if "error" in bbands:
                return [types.TextContent(type="text", text=f"Error: {bbands['error']}")]
                
            result_text = (
                f"Bollinger Bands Analysis for {symbol} ({period}-day, {std_dev}-std):\n\n"
                f"Current Price: ${bbands.get('latest_price', 0):.2f}\n"
                f"Upper Band: ${bbands.get('upper_band', 0):.2f}\n"
                f"Middle Band: ${bbands.get('middle_band', 0):.2f}\n"
                f"Lower Band: ${bbands.get('lower_band', 0):.2f}\n"
                f"%B: {bbands.get('percent_b', 0):.2f}\n\n"
                f"Mean Reversion Signal: "
            )
            
            if bbands.get('is_above_upper', False):
                result_text += "POTENTIAL SHORT (Price above upper band)"
            elif bbands.get('is_below_lower', False):
                result_text += "POTENTIAL LONG (Price below lower band)"
            else:
                result_text += "NEUTRAL (Price within bands)"
                
            return [types.TextContent(type="text", text=result_text)]
            
    elif name == "calculate-rsi":
        symbol = arguments.get("symbol")
        if not symbol:
            return [types.TextContent(type="text", text="Missing symbol parameter")]
            
        symbol = symbol.upper()
        period = arguments.get("period", 2)
        
        async with httpx.AsyncClient() as client:
            rsi = await calculate_rsi(client, symbol, period)
            
            if rsi == -1:
                return [types.TextContent(type="text", text=f"Error calculating RSI for {symbol}")]
                
            result_text = (
                f"RSI({period}) Analysis for {symbol}:\n\n"
                f"Current RSI: {rsi:.2f}\n\n"
                f"Mean Reversion Signal: "
            )
            
            if rsi < 10:
                result_text += "STRONG BUY (Extremely oversold)"
            elif rsi < 30:
                result_text += "BUY (Oversold)"
            elif rsi > 90:
                result_text += "STRONG SELL (Extremely overbought)"
            elif rsi > 70:
                result_text += "SELL (Overbought)"
            else:
                result_text += "NEUTRAL"
                
            return [types.TextContent(type="text", text=result_text)]
            
    elif name == "check-volume-climax":
        symbol = arguments.get("symbol")
        if not symbol:
            return [types.TextContent(type="text", text="Missing symbol parameter")]
            
        symbol = symbol.upper()
        threshold = arguments.get("threshold", 1.5)
        
        async with httpx.AsyncClient() as client:
            volume_climax = await check_volume_climax(client, symbol, threshold)
            
            result_text = (
                f"Volume Climax Analysis for {symbol}:\n\n"
                f"Volume climax detected: {'YES' if volume_climax else 'NO'}\n"
                f"Threshold: {threshold}x 10-day average volume\n\n"
                f"Mean Reversion Signal: {'FAVORABLE' if volume_climax else 'UNFAVORABLE'} "
                f"(High volume often precedes reversal points)"
            )
            
            return [types.TextContent(type="text", text=result_text)]
            
    elif name == "analyze-mean-reversion":
        symbol = arguments.get("symbol")
        if not symbol:
            return [types.TextContent(type="text", text="Missing symbol parameter")]
            
        symbol = symbol.upper()
        rsi_threshold = arguments.get("rsi_threshold", 10.0)
        volume_threshold = arguments.get("volume_threshold", 1.5)
        
        async with httpx.AsyncClient() as client:
            analysis = await check_mean_reversion_setup(
                client, 
                symbol,
                rsi_threshold,
                volume_threshold
            )
            
            formatted_analysis = await format_mean_reversion_analysis(analysis)
            return [types.TextContent(type="text", text=formatted_analysis)]
            
    elif name == "get-sector-performance":
        async with httpx.AsyncClient() as client:
            sector_data = await make_alpha_request(
                client,
                "SECTOR",
                None
            )
            
            if isinstance(sector_data, str):
                return [types.TextContent(type="text", text=f"Error: {sector_data}")]
                
            # Format the sector performance data
            result = ["Sector Performance:\n"]
            
            for timeframe, sectors in sector_data.items():
                if timeframe == "Meta Data":
                    continue
                    
                result.append(f"\n{timeframe}:\n")
                for sector, performance in sectors.items():
                    result.append(f"{sector}: {performance}\n")
                    
            strongest_sectors = []
            one_day_sectors = sector_data.get("Rank A: Real-Time Performance", {})
            
            if one_day_sectors:
                # Sort sectors by performance
                sorted_sectors = sorted(
                    one_day_sectors.items(),
                    key=lambda x: float(x[1].strip("%")),
                    reverse=True
                )
                
                strongest_sectors = [f"{s[0]} ({s[1]})" for s in sorted_sectors[:3]]
                
            if strongest_sectors:
                result.append("\nStrongest Sectors (Real-Time):\n")
                for sector in strongest_sectors:
                    result.append(f"- {sector}\n")
                    
            return [types.TextContent(type="text", text="".join(result))]
            
    elif name == "get-atr":
        symbol = arguments.get("symbol")
        if not symbol:
            return [types.TextContent(type="text", text="Missing symbol parameter")]
            
        symbol = symbol.upper()
        period = arguments.get("period", 14)
        
        async with httpx.AsyncClient() as client:
            atr_data = await make_alpha_request(
                client,
                "ATR",
                symbol,
                {
                    "time_period": str(period),
                    "interval": "daily"
                }
            )
            
            if isinstance(atr_data, str):
                return [types.TextContent(type="text", text=f"Error: {atr_data}")]
                
            # Extract the technical data
            tech_data = atr_data.get("Technical Analysis: ATR", {})
            if not tech_data:
                return [types.TextContent(type="text", text="No ATR data available")]
                
            # Get the most recent data points
            dates = list(tech_data.keys())
            if not dates:
                return [types.TextContent(type="text", text="No ATR data available")]
                
            # Calculate 20-day average ATR
            recent_dates = dates[:20] if len(dates) >= 20 else dates
            recent_atr_values = [float(tech_data[date]["ATR"]) for date in recent_dates]
            avg_atr = sum(recent_atr_values) / len(recent_atr_values)
            
            latest_date = dates[0]
            latest_atr = float(tech_data[latest_date]["ATR"])
            
            # Check if ATR is elevated
            atr_ratio = latest_atr / avg_atr
            is_elevated = atr_ratio > 1.2
            
            result_text = (
                f"ATR Analysis for {symbol}:\n\n"
                f"Current ATR ({latest_date}): {latest_atr:.4f}\n"
                f"20-day Average ATR: {avg_atr:.4f}\n"
                f"ATR Ratio: {atr_ratio:.2f}x\n\n"
                f"Volatility Status: {'ELEVATED' if is_elevated else 'NORMAL'}\n"
                f"Mean Reversion Signal: {'FAVORABLE' if is_elevated else 'UNFAVORABLE'} "
                f"(Higher volatility often precedes mean reversion opportunities)"
            )
            
            return [types.TextContent(type="text", text=result_text)]
    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="alpha_vantage_finance",
                server_version="0.2.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

# This is needed if you'd like to connect to a custom client
if __name__ == "__main__":
    asyncio.run(main())
