"""
Alpha Vantage MCP Mean Reversion Tools Module

This module contains utility functions for implementing a mean reversion trading strategy
using Alpha Vantage API data.
"""

from typing import Any, Dict, List, Optional, Tuple
import httpx
import numpy as np
from datetime import datetime, timedelta
import pandas as pd

from .tools import make_alpha_request

async def get_vix_trend(client: httpx.AsyncClient, days: int = 3) -> Tuple[bool, Optional[float]]:
    """
    Check if VIX has been declining for the specified number of days.
    
    Args:
        client: An httpx AsyncClient instance
        days: Number of days to check for declining trend
        
    Returns:
        Tuple containing:
        - Boolean indicating if VIX has been declining
        - Percentage change in VIX over the period (negative means declining)
    """
    vix_data = await make_alpha_request(
        client,
        "TIME_SERIES_DAILY",
        "^VIX"
    )
    
    if isinstance(vix_data, str):
        # Error occurred
        return False, None
    
    # Extract time series data
    time_series = vix_data.get("Time Series (Daily)", {})
    if not time_series:
        return False, None
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame.from_dict(time_series, orient='index')
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index(ascending=False)
    
    # Check if we have enough data
    if len(df) < days + 1:
        return False, None
    
    # Get the closing prices for the last 'days + 1' days
    closes = df['4. close'].iloc[:days + 1].values
    
    # Check if the VIX has been declining
    is_declining = all(closes[i] < closes[i+1] for i in range(days))
    
    # Calculate the percentage change
    pct_change = ((closes[0] - closes[days]) / closes[days]) * 100
    
    return is_declining, pct_change


async def check_sp500_above_ma(client: httpx.AsyncClient, period: int = 20) -> bool:
    """
    Check if S&P 500 is above its moving average.
    
    Args:
        client: An httpx AsyncClient instance
        period: Moving average period (default: 20 days)
        
    Returns:
        Boolean indicating if S&P 500 is above its moving average
    """
    sp500_data = await make_alpha_request(
        client,
        "TIME_SERIES_DAILY",
        "^GSPC"
    )
    
    if isinstance(sp500_data, str):
        # Error occurred
        return False
    
    # Extract time series data
    time_series = sp500_data.get("Time Series (Daily)", {})
    if not time_series:
        return False
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame.from_dict(time_series, orient='index')
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index(ascending=False)
    
    # Calculate the moving average
    df['MA'] = df['4. close'].rolling(period).mean()
    
    # Check if current price is above MA
    latest_price = df['4. close'].iloc[0]
    latest_ma = df['MA'].iloc[0]
    
    return latest_price > latest_ma


async def get_bollinger_bands(client: httpx.AsyncClient, symbol: str, period: int = 20, std_dev: int = 2) -> Dict[str, Any]:
    """
    Calculate Bollinger Bands for a given symbol.
    
    Args:
        client: An httpx AsyncClient instance
        symbol: The stock symbol
        period: Period for moving average (default: 20)
        std_dev: Number of standard deviations (default: 2)
        
    Returns:
        Dictionary with upper band, middle band, lower band, and % B
    """
    # Get Bollinger Bands directly from Alpha Vantage
    bbands_data = await make_alpha_request(
        client,
        "BBANDS",
        symbol,
        {
            "time_period": str(period),
            "nbdevup": str(std_dev),
            "nbdevdn": str(std_dev),
            "series_type": "close",
            "interval": "daily"
        }
    )
    
    if isinstance(bbands_data, str):
        # Error occurred
        return {"error": bbands_data}
    
    # Extract the technical data
    tech_data = bbands_data.get("Technical Analysis: BBANDS", {})
    if not tech_data:
        return {"error": "No Bollinger Bands data available"}
    
    # Get the most recent data point
    latest_date = list(tech_data.keys())[0]
    latest_data = tech_data[latest_date]
    
    # Get the latest stock price
    quote_data = await make_alpha_request(
        client,
        "GLOBAL_QUOTE",
        symbol
    )
    
    if isinstance(quote_data, str):
        # Error occurred
        return {"error": quote_data}
    
    global_quote = quote_data.get("Global Quote", {})
    latest_price = float(global_quote.get("05. price", 0))
    
    # Calculate %B: (Price - Lower Band) / (Upper Band - Lower Band)
    upper_band = float(latest_data.get("Real Upper Band", 0))
    lower_band = float(latest_data.get("Real Lower Band", 0))
    middle_band = float(latest_data.get("Real Middle Band", 0))
    
    if upper_band == lower_band:
        percent_b = 0.5  # Avoid division by zero
    else:
        percent_b = (latest_price - lower_band) / (upper_band - lower_band)
    
    # Calculate whether price is outside bands (>= 2 standard deviations)
    is_above_upper = latest_price >= upper_band
    is_below_lower = latest_price <= lower_band
    
    return {
        "upper_band": upper_band,
        "middle_band": middle_band,
        "lower_band": lower_band,
        "latest_price": latest_price,
        "percent_b": percent_b,
        "is_above_upper": is_above_upper,
        "is_below_lower": is_below_lower,
        "date": latest_date
    }


async def calculate_rsi(client: httpx.AsyncClient, symbol: str, period: int = 2) -> float:
    """
    Calculate RSI for a given symbol.
    
    Args:
        client: An httpx AsyncClient instance
        symbol: The stock symbol
        period: RSI period (default: 2)
        
    Returns:
        RSI value or -1 if error
    """
    rsi_data = await make_alpha_request(
        client,
        "RSI",
        symbol,
        {
            "time_period": str(period),
            "series_type": "close",
            "interval": "daily"
        }
    )
    
    if isinstance(rsi_data, str):
        # Error occurred
        return -1
    
    # Extract the technical data
    tech_data = rsi_data.get("Technical Analysis: RSI", {})
    if not tech_data:
        return -1
    
    # Get the most recent data point
    latest_date = list(tech_data.keys())[0]
    latest_data = tech_data[latest_date]
    
    return float(latest_data.get("RSI", -1))


async def check_volume_climax(client: httpx.AsyncClient, symbol: str, threshold: float = 1.5) -> bool:
    """
    Check if volume is higher than the specified threshold of the 10-day average.
    
    Args:
        client: An httpx AsyncClient instance
        symbol: The stock symbol
        threshold: Volume multiple of average to consider a climax (default: 1.5)
        
    Returns:
        Boolean indicating if volume climax is detected
    """
    volume_data = await make_alpha_request(
        client,
        "TIME_SERIES_DAILY",
        symbol,
        {"outputsize": "compact"}
    )
    
    if isinstance(volume_data, str):
        # Error occurred
        return False
    
    # Extract time series data
    time_series = volume_data.get("Time Series (Daily)", {})
    if not time_series:
        return False
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame.from_dict(time_series, orient='index')
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index(ascending=False)
    
    # Calculate the 10-day average volume
    avg_volume = df['5. volume'].iloc[1:11].mean()
    latest_volume = df['5. volume'].iloc[0]
    
    return latest_volume > (avg_volume * threshold)


async def check_mean_reversion_setup(
    client: httpx.AsyncClient, 
    symbol: str,
    rsi_threshold: float = 10.0,
    volume_threshold: float = 1.5
) -> Dict[str, Any]:
    """
    Check for a complete mean reversion setup based on multiple indicators.
    
    Args:
        client: An httpx AsyncClient instance
        symbol: The stock symbol
        rsi_threshold: RSI level to consider oversold
        volume_threshold: Volume multiple to consider a climax
        
    Returns:
        Dictionary with all indicators and an overall recommendation
    """
    # Check market conditions
    vix_declining, vix_change = await get_vix_trend(client)
    sp500_above_ma = await check_sp500_above_ma(client)
    
    # Check asset-specific conditions
    bbands = await get_bollinger_bands(client, symbol)
    rsi = await calculate_rsi(client, symbol)
    volume_climax = await check_volume_climax(client, symbol, volume_threshold)
    
    # Determine if we have a valid setup
    # For long setup: price below lower band, RSI(2) < threshold, declining VIX, S&P500 above MA
    is_long_setup = (
        bbands.get("is_below_lower", False) and
        rsi < rsi_threshold and
        vix_declining and
        sp500_above_ma and
        volume_climax
    )
    
    # For short setup: price above upper band, RSI(2) > (100 - threshold), declining VIX, S&P500 below MA
    is_short_setup = (
        bbands.get("is_above_upper", False) and
        rsi > (100 - rsi_threshold) and
        vix_declining and
        not sp500_above_ma and
        volume_climax
    )
    
    return {
        "symbol": symbol,
        "vix_declining": vix_declining,
        "vix_change": vix_change,
        "sp500_above_ma": sp500_above_ma,
        "bbands": bbands,
        "rsi": rsi,
        "volume_climax": volume_climax,
        "is_long_setup": is_long_setup,
        "is_short_setup": is_short_setup,
        "recommendation": "LONG" if is_long_setup else "SHORT" if is_short_setup else "NEUTRAL"
    }


async def format_mean_reversion_analysis(analysis: Dict[str, Any]) -> str:
    """
    Format mean reversion analysis into a readable string.
    
    Args:
        analysis: Output from check_mean_reversion_setup
        
    Returns:
        Formatted string for display
    """
    bbands = analysis.get("bbands", {})
    
    return (
        f"Mean Reversion Analysis for {analysis.get('symbol', 'Unknown')}:\n\n"
        f"RECOMMENDATION: {analysis.get('recommendation', 'UNKNOWN')}\n\n"
        f"Market Conditions:\n"
        f"- VIX Trend: {'Declining' if analysis.get('vix_declining', False) else 'Rising'} "
        f"({analysis.get('vix_change', 0):.2f}%)\n"
        f"- S&P 500 above 20-day MA: {'Yes' if analysis.get('sp500_above_ma', False) else 'No'}\n\n"
        f"Technical Signals:\n"
        f"- Price: ${bbands.get('latest_price', 0):.2f}\n"
        f"- Bollinger Bands (20, 2):\n"
        f"  Upper: ${bbands.get('upper_band', 0):.2f}\n"
        f"  Middle: ${bbands.get('middle_band', 0):.2f}\n"
        f"  Lower: ${bbands.get('lower_band', 0):.2f}\n"
        f"  %B: {bbands.get('percent_b', 0):.2f}\n"
        f"- RSI(2): {analysis.get('rsi', 0):.2f}\n"
        f"- Volume Climax: {'Yes' if analysis.get('volume_climax', False) else 'No'}\n\n"
        f"Setup Quality:\n"
        f"- Valid Long Setup: {'Yes' if analysis.get('is_long_setup', False) else 'No'}\n"
        f"- Valid Short Setup: {'Yes' if analysis.get('is_short_setup', False) else 'No'}\n"
        f"- Date: {bbands.get('date', 'Unknown')}\n"
    )
