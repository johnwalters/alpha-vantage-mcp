"""
Technical indicators module for Alpha Vantage MCP.

This module provides functions for calculating technical indicators and analyzing market conditions
as required by the statistical futures leverage trading strategy.
"""

from typing import Dict, List, Any, Tuple, Optional, Union
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import httpx
import os

ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

if not API_KEY:
    raise ValueError("Missing ALPHA_VANTAGE_API_KEY environment variable")


async def get_price_data(client: httpx.AsyncClient, symbol: str, interval: str = "daily", outputsize: str = "compact") -> pd.DataFrame:
    """
    Fetch historical price data from Alpha Vantage and convert to DataFrame.
    
    Args:
        client: httpx.AsyncClient instance
        symbol: Stock or index symbol
        interval: Time interval ('daily', '60min', etc.)
        outputsize: 'compact' (latest 100 data points) or 'full' (up to 20 years)
        
    Returns:
        DataFrame with OHLCV data
    """
    function = "TIME_SERIES_DAILY" if interval == "daily" else "TIME_SERIES_INTRADAY"
    
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": API_KEY,
        "outputsize": outputsize
    }
    
    if interval != "daily":
        params["interval"] = interval
    
    try:
        response = await client.get(
            ALPHA_VANTAGE_BASE,
            params=params,
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        
        # Extract time series data
        key = f"Time Series ({interval.capitalize()})" if interval == "daily" else f"Time Series ({interval})"
        time_series = data.get(key, {})
        
        if not time_series:
            raise ValueError(f"No time series data found for {symbol}")
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(time_series, orient='index')
        
        # Rename columns
        df.rename(columns={
            '1. open': 'open',
            '2. high': 'high',
            '3. low': 'low',
            '4. close': 'close',
            '5. volume': 'volume'
        }, inplace=True)
        
        # Convert to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        
        # Sort by date (most recent first)
        df.index = pd.to_datetime(df.index)
        df.sort_index(ascending=False, inplace=True)
        
        return df
        
    except Exception as e:
        raise Exception(f"Error fetching price data: {str(e)}")


async def get_vix_data(client: httpx.AsyncClient) -> pd.DataFrame:
    """
    Fetch VIX data from Alpha Vantage.
    
    Args:
        client: httpx.AsyncClient instance
        
    Returns:
        DataFrame with VIX data
    """
    return await get_price_data(client, "^VIX", "daily", "compact")


async def get_sector_performance(client: httpx.AsyncClient) -> Dict[str, float]:
    """
    Fetch sector performance data from Alpha Vantage.
    
    Args:
        client: httpx.AsyncClient instance
        
    Returns:
        Dictionary with sector performance data
    """
    params = {
        "function": "SECTOR",
        "apikey": API_KEY
    }
    
    try:
        response = await client.get(
            ALPHA_VANTAGE_BASE,
            params=params,
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        
        # Get the most recent sector performance
        sectors = data.get("Rank A: Real-Time Performance", {})
        return {k: float(v.strip('%')) for k, v in sectors.items()}
        
    except Exception as e:
        raise Exception(f"Error fetching sector performance: {str(e)}")


async def get_stock_sector(client: httpx.AsyncClient, symbol: str) -> str:
    """
    Get the sector for a given stock symbol.
    
    Args:
        client: httpx.AsyncClient instance
        symbol: Stock symbol
        
    Returns:
        Sector name as a string
    """
    params = {
        "function": "OVERVIEW",
        "symbol": symbol,
        "apikey": API_KEY
    }
    
    try:
        response = await client.get(
            ALPHA_VANTAGE_BASE,
            params=params,
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        
        return data.get("Sector", "Unknown")
        
    except Exception as e:
        raise Exception(f"Error fetching stock sector: {str(e)}")


def calculate_moving_average(df: pd.DataFrame, window: int, column: str = 'close') -> pd.Series:
    """
    Calculate a simple moving average.
    
    Args:
        df: DataFrame with price data
        window: Window size for moving average
        column: Column to use for calculation
        
    Returns:
        Series with moving average values
    """
    return df[column].rolling(window=window).mean()


def calculate_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0, column: str = 'close') -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.
    
    Args:
        df: DataFrame with price data
        window: Window size for moving average
        num_std: Number of standard deviations for bands
        column: Column to use for calculation
        
    Returns:
        Tuple of (middle band, upper band, lower band)
    """
    middle_band = calculate_moving_average(df, window, column)
    std = df[column].rolling(window=window).std()
    upper_band = middle_band + (std * num_std)
    lower_band = middle_band - (std * num_std)
    
    return middle_band, upper_band, lower_band


def calculate_rsi(df: pd.DataFrame, window: int = 2, column: str = 'close') -> pd.Series:
    """
    Calculate the Relative Strength Index (RSI).
    
    Args:
        df: DataFrame with price data
        window: Window size for RSI calculation
        column: Column to use for calculation
        
    Returns:
        Series with RSI values
    """
    delta = df[column].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    
    Args:
        df: DataFrame with price data
        window: Window size for ATR calculation
        
    Returns:
        Series with ATR values
    """
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    
    return true_range.rolling(window=window).mean()


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Calculate Volume Weighted Average Price (VWAP).
    
    Args:
        df: DataFrame with price data
        
    Returns:
        Series with VWAP values
    """
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    return vwap


def calculate_rate_of_change(df: pd.DataFrame, window: int = 3, column: str = 'close') -> pd.Series:
    """
    Calculate Rate of Change.
    
    Args:
        df: DataFrame with price data
        window: Window size for ROC calculation
        column: Column to use for calculation
        
    Returns:
        Series with ROC values (in percentage)
    """
    return df[column].pct_change(periods=window) * 100


def calculate_mean_reversion_score(df: pd.DataFrame, window: int = 20, std_threshold: float = 2.0, column: str = 'close') -> pd.Series:
    """
    Calculate a mean reversion score based on deviations from moving average.
    
    Args:
        df: DataFrame with price data
        window: Window size for moving average
        std_threshold: Standard deviation threshold for triggering
        column: Column to use for calculation
        
    Returns:
        Series with mean reversion scores
    """
    ma = calculate_moving_average(df, window, column)
    std = df[column].rolling(window=window).std()
    
    # Calculate deviations in terms of standard deviations
    deviation = (df[column] - ma) / std
    
    # Create a score where 1.0 means "at the threshold for mean reversion opportunity"
    # Higher absolute values indicate stronger signals
    score = deviation / std_threshold
    
    return score


def check_volume_climax(df: pd.DataFrame, threshold: float = 1.5, window: int = 10) -> pd.Series:
    """
    Check for volume climax (higher than average volume).
    
    Args:
        df: DataFrame with price data
        threshold: Volume threshold as multiple of average
        window: Window size for volume average
        
    Returns:
        Series with boolean values (True for volume climax)
    """
    avg_volume = df['volume'].rolling(window=window).mean()
    return df['volume'] > (avg_volume * threshold)


def is_price_at_bollinger_band(df: pd.DataFrame, window: int = 20, num_std: float = 2.0, column: str = 'close') -> Dict[str, pd.Series]:
    """
    Check if price is at or beyond Bollinger Bands.
    
    Args:
        df: DataFrame with price data
        window: Window size for Bollinger Bands
        num_std: Number of standard deviations for bands
        column: Column to use for calculation
        
    Returns:
        Dict with boolean Series for upper and lower band touches
    """
    middle, upper, lower = calculate_bollinger_bands(df, window, num_std, column)
    
    return {
        'upper_band_touch': df[column] >= upper,
        'lower_band_touch': df[column] <= lower
    }


def analyze_market_condition(
    sp500_df: pd.DataFrame, 
    vix_df: pd.DataFrame,
    sector_data: Dict[str, float],
    stock_sector: str,
    ma_window: int = 20
) -> Dict[str, Any]:
    """
    Analyze overall market conditions.
    
    Args:
        sp500_df: DataFrame with S&P 500 data
        vix_df: DataFrame with VIX data
        sector_data: Dictionary with sector performance
        stock_sector: Sector of the stock being analyzed
        ma_window: Window size for moving average
        
    Returns:
        Dictionary with market condition analysis
    """
    # Calculate S&P 500 position relative to MA
    sp500_ma = calculate_moving_average(sp500_df, ma_window)
    sp500_above_ma = sp500_df['close'][0] > sp500_ma[0]
    
    # Check VIX trend (declining over 2+ days)
    vix_2day_change = vix_df['close'].pct_change(periods=2)[0] * 100
    vix_declining = vix_2day_change < 0
    
    # Check sector performance
    sector_performance = sector_data.get(stock_sector, 0)
    sector_outperforming = sector_performance > 0
    
    return {
        'sp500_above_ma': sp500_above_ma,
        'vix_declining': vix_declining,
        'vix_2day_change': vix_2day_change,
        'sector_performance': sector_performance,
        'sector_outperforming': sector_outperforming
    }


def generate_setup_report(
    symbol: str,
    df: pd.DataFrame,
    market_condition: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a complete trading setup report based on the checklist.
    
    Args:
        symbol: Stock symbol
        df: DataFrame with price data
        market_condition: Dictionary with market condition analysis
        
    Returns:
        Dictionary with analysis results and trading signals
    """
    # Calculate all required technical indicators
    rsi2 = calculate_rsi(df, window=2)
    atr = calculate_atr(df)
    atr_20d_avg = atr[20:].mean()
    atr_ratio = atr[0] / atr_20d_avg
    
    middle_band, upper_band, lower_band = calculate_bollinger_bands(df)
    band_touches = is_price_at_bollinger_band(df)
    
    roc_3day = calculate_rate_of_change(df, window=3)
    roc_percentile = roc_3day.rank(pct=True)[0] * 100
    
    vwap = calculate_vwap(df)
    price_vs_vwap = df['close'][0] - vwap[0]
    
    vol_climax = check_volume_climax(df)
    
    mean_rev_score = calculate_mean_reversion_score(df)
    
    # Assemble the checklist results
    checklist = {
        # Market condition analysis
        'vix_declining': market_condition['vix_declining'],
        'sector_outperforming': market_condition['sector_outperforming'],
        'sp500_above_ma': market_condition['sp500_above_ma'],
        
        # Asset-specific technical setup
        'mean_reversion_opportunity': abs(mean_rev_score[0]) >= 1.0,
        'volume_climax': vol_climax[0],
        'rsi2_oversold': rsi2[0] < 10 if mean_rev_score[0] > 0 else rsi2[0] > 90,
        'at_bollinger_band': band_touches['lower_band_touch'][0] if mean_rev_score[0] > 0 else band_touches['upper_band_touch'][0],
        
        # Momentum confirmation
        'extreme_roc': roc_percentile < 10 if mean_rev_score[0] > 0 else roc_percentile > 90,
        'price_near_vwap': abs(price_vs_vwap / df['close'][0]) < 0.01,
        'high_atr': atr_ratio > 1.2
    }
    
    # Count confirmed criteria
    confirmed_count = sum(1 for v in checklist.values() if v)
    
    # Overall assessment
    ready_to_trade = confirmed_count >= 7
    
    return {
        'symbol': symbol,
        'price': df['close'][0],
        'timestamp': df.index[0],
        'checklist_items': checklist,
        'confirmed_count': confirmed_count,
        'needed_count': 7,
        'ready_to_trade': ready_to_trade,
        'recommendation': 'LONG' if mean_rev_score[0] > 0 else 'SHORT' if mean_rev_score[0] < 0 else 'NEUTRAL',
        'technical_data': {
            'rsi2': rsi2[0],
            'atr': atr[0],
            'atr_ratio': atr_ratio,
            'mean_reversion_score': mean_rev_score[0],
            'vwap': vwap[0],
            'price_vs_vwap': price_vs_vwap,
            'roc_3day': roc_3day[0],
            'roc_percentile': roc_percentile,
            'upper_band': upper_band[0],
            'middle_band': middle_band[0],
            'lower_band': lower_band[0]
        },
        'market_condition': market_condition
    }


def calculate_position_size(account_value: float, entry_price: float, stop_loss_percent: float = 7.0, risk_percent: float = 3.0, leverage: float = 10.0) -> Dict[str, Any]:
    """
    Calculate optimal position size based on risk management rules.
    
    Args:
        account_value: Total account value
        entry_price: Entry price per share/contract
        stop_loss_percent: Stop loss percentage
        risk_percent: Percentage of account to risk
        leverage: Leverage multiplier
        
    Returns:
        Dictionary with position size information
    """
    # Calculate maximum dollar risk
    max_risk = account_value * (risk_percent / 100)
    
    # Calculate contract risk (accounting for leverage)
    contract_risk = entry_price * (stop_loss_percent / 100) * leverage
    
    # Calculate number of contracts
    num_contracts = max_risk / contract_risk
    
    # Calculate split entry (70%/30%)
    initial_contracts = int(num_contracts * 0.7)
    secondary_contracts = int(num_contracts * 0.3)
    
    # Ensure at least 1 contract for each entry if possible
    if initial_contracts == 0 and secondary_contracts == 0:
        initial_contracts = 1
        secondary_contracts = 0
    elif initial_contracts == 0:
        initial_contracts = 1
        secondary_contracts = 0
    
    # Calculate target based on 1:1 or better risk/reward
    target_percent = stop_loss_percent * 1.5
    
    return {
        'account_value': account_value,
        'max_risk_amount': max_risk,
        'contract_risk': contract_risk,
        'total_contracts': initial_contracts + secondary_contracts,
        'initial_contracts': initial_contracts,
        'secondary_contracts': secondary_contracts,
        'entry_price': entry_price,
        'stop_loss_price': entry_price * (1 - stop_loss_percent/100) if mean_rev_score > 0 else entry_price * (1 + stop_loss_percent/100),
        'target_price': entry_price * (1 + target_percent/100) if mean_rev_score > 0 else entry_price * (1 - target_percent/100),
        'leverage': leverage,
        'max_loss_percent': risk_percent,
        'potential_gain_percent': target_percent * leverage,
        'risk_reward_ratio': (target_percent * leverage) / (stop_loss_percent * leverage)
    }


def format_analysis_report(analysis_result: Dict[str, Any]) -> str:
    """
    Format the analysis report into a readable string.
    
    Args:
        analysis_result: Dictionary with analysis results
        
    Returns:
        Formatted string with analysis report
    """
    symbol = analysis_result['symbol']
    price = analysis_result['price']
    timestamp = analysis_result['timestamp']
    checklist = analysis_result['checklist_items']
    confirmed = analysis_result['confirmed_count']
    needed = analysis_result['needed_count']
    ready = analysis_result['ready_to_trade']
    recommendation = analysis_result['recommendation']
    tech_data = analysis_result['technical_data']
    market = analysis_result['market_condition']
    
    # Format the report
    lines = [
        f"STATISTICAL FUTURES TRADING ANALYSIS FOR {symbol}",
        f"Price: ${price:.2f} as of {timestamp}",
        f"Recommendation: {recommendation}",
        "",
        f"CHECKLIST STATUS: {confirmed}/{needed} criteria confirmed {'✅ READY TO TRADE' if ready else '❌ NOT READY'}",
        "",
        "MARKET CONDITION ANALYSIS:",
        f"✓ VIX Declining: {'Yes ✅' if market['vix_declining'] else 'No ❌'} ({market['vix_2day_change']:.2f}% 2-day change)",
        f"✓ Sector Performance: {'Positive ✅' if market['sector_outperforming'] else 'Negative ❌'} ({market['sector_performance']:.2f}%)",
        f"✓ S&P500 Above 20-day MA: {'Yes ✅' if market['sp500_above_ma'] else 'No ❌'}",
        "",
        "TECHNICAL SETUP:",
        f"✓ Mean Reversion Opportunity: {'Yes ✅' if checklist['mean_reversion_opportunity'] else 'No ❌'} (Score: {tech_data['mean_reversion_score']:.2f})",
        f"✓ Volume Climax: {'Yes ✅' if checklist['volume_climax'] else 'No ❌'}",
        f"✓ RSI(2): {'Oversold ✅' if checklist['rsi2_oversold'] else 'Not oversold ❌'} ({tech_data['rsi2']:.2f})",
        f"✓ At Bollinger Band: {'Yes ✅' if checklist['at_bollinger_band'] else 'No ❌'}",
        "",
        "MOMENTUM CONFIRMATION:",
        f"✓ Extreme 3-day ROC: {'Yes ✅' if checklist['extreme_roc'] else 'No ❌'} ({tech_data['roc_3day']:.2f}%, {tech_data['roc_percentile']:.0f} percentile)",
        f"✓ Price vs VWAP: {'Near VWAP ✅' if checklist['price_near_vwap'] else 'Far from VWAP ❌'} ({tech_data['price_vs_vwap']:.2f} points)",
        f"✓ High ATR: {'Yes ✅' if checklist['high_atr'] else 'No ❌'} ({tech_data['atr_ratio']:.2f}x 20-day avg)",
        "",
        "TRADE PARAMETERS:",
        f"Entry Price: ${price:.2f}",
        f"Stop Loss: ${tech_data['lower_band']:.2f} (Bollinger lower band)",
        f"Target: ${tech_data['upper_band']:.2f} (Bollinger upper band)",
        f"Expected Holding Period: 1-5 days",
        "",
        "ADDITIONAL NOTES:",
        "• Ensure institutional activity confirmation via options flow or block trades",
        "• Use 70%/30% split entry approach",
        "• Avoid trading first 30 minutes and last 60 minutes of the session",
        "• Preferred trading days: Tuesday and Wednesday"
    ]
    
    return "\n".join(lines)
