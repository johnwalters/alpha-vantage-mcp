"""
Institutional data analysis module for Alpha Vantage MCP.

This module provides functions for analyzing options flow, block trades, and other institutional
activities as required by the statistical futures leverage trading strategy.
"""

from typing import Dict, List, Any, Tuple, Optional, Union
import pandas as pd
import numpy as np
import httpx
import os
from datetime import datetime, timedelta

# Constants
ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

if not API_KEY:
    raise ValueError("Missing ALPHA_VANTAGE_API_KEY environment variable")


async def get_options_data(client: httpx.AsyncClient, symbol: str, date: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch options chain data from Alpha Vantage.
    
    Args:
        client: httpx.AsyncClient instance
        symbol: Stock symbol
        date: Optional specific date for options chain (YYYY-MM-DD)
        
    Returns:
        Dictionary with options chain data
    """
    params = {
        "function": "HISTORICAL_OPTIONS",
        "symbol": symbol,
        "apikey": API_KEY
    }
    
    if date:
        params["date"] = date
    
    try:
        response = await client.get(
            ALPHA_VANTAGE_BASE,
            params=params,
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        
        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
        
        return data
    except Exception as e:
        raise Exception(f"Error fetching options data: {str(e)}")


def process_options_flow(options_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze options flow for institutional activity signals.
    
    Args:
        options_data: Options chain data from Alpha Vantage
        
    Returns:
        Dictionary with options flow analysis
    """
    options_chain = options_data.get("data", [])
    
    if not options_chain:
        return {
            "has_options_data": False,
            "call_put_ratio": 0,
            "large_call_volume": False,
            "large_put_volume": False,
            "institutional_activity": False
        }
    
    # Convert to DataFrame
    df = pd.DataFrame(options_chain)
    
    # Filter to potentially institutional orders (high volume, high open interest)
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    df['open_interest'] = pd.to_numeric(df['open_interest'], errors='coerce')
    
    # Group by type (call/put)
    grouped = df.groupby('type')
    
    try:
        call_volume = grouped.get_group('call')['volume'].sum()
        put_volume = grouped.get_group('put')['volume'].sum()
        call_oi = grouped.get_group('call')['open_interest'].sum()
        put_oi = grouped.get_group('put')['open_interest'].sum()
        
        # Calculate call/put ratio
        call_put_ratio = call_volume / put_volume if put_volume > 0 else float('inf')
        
        # Look for large volume contracts (potential institutional activity)
        large_volume_threshold = df['volume'].quantile(0.95)
        large_volume_contracts = df[df['volume'] >= large_volume_threshold]
        
        # Check for volume/open interest anomalies
        vol_oi_ratio = df['volume'] / df['open_interest']
        vol_oi_ratio = vol_oi_ratio.replace([np.inf, -np.inf], np.nan).dropna()
        unusual_activity = vol_oi_ratio > vol_oi_ratio.quantile(0.95)
        
        # Detect potential block trades
        large_call_volume = any(large_volume_contracts[large_volume_contracts['type'] == 'call']['volume'] > 0)
        large_put_volume = any(large_volume_contracts[large_volume_contracts['type'] == 'put']['volume'] > 0)
        
        # Institutional activity signal
        institutional_activity = (
            call_put_ratio > 2 or 
            call_put_ratio < 0.5 or 
            large_call_volume or 
            large_put_volume or 
            any(unusual_activity)
        )
        
        return {
            "has_options_data": True,
            "call_volume": int(call_volume),
            "put_volume": int(put_volume),
            "call_open_interest": int(call_oi),
            "put_open_interest": int(put_oi),
            "call_put_ratio": float(call_put_ratio),
            "large_call_volume": bool(large_call_volume),
            "large_put_volume": bool(large_put_volume),
            "unusual_volume_contracts": len(large_volume_contracts),
            "institutional_activity": bool(institutional_activity),
            "bullish_signal": call_put_ratio > 2 or large_call_volume,
            "bearish_signal": call_put_ratio < 0.5 or large_put_volume
        }
    except (KeyError, ValueError) as e:
        # Handle case where there might not be both call and put options
        return {
            "has_options_data": True,
            "error": str(e),
            "call_put_ratio": 0,
            "large_call_volume": False,
            "large_put_volume": False,
            "institutional_activity": False
        }


async def detect_block_trades(client: httpx.AsyncClient, symbol: str, days: int = 5) -> Dict[str, Any]:
    """
    Detect potential block trades by analyzing intraday volume patterns.
    
    Args:
        client: httpx.AsyncClient instance
        symbol: Stock symbol
        days: Number of days to analyze
        
    Returns:
        Dictionary with block trade analysis
    """
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "5min",
        "outputsize": "full",
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
        
        # Extract time series data
        time_series = data.get("Time Series (5min)", {})
        
        if not time_series:
            return {
                "has_block_trades": False,
                "block_trade_detected": False,
                "recent_block_trades": 0
            }
        
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
        
        # Convert index to datetime
        df.index = pd.to_datetime(df.index)
        
        # Sort by date (most recent first)
        df.sort_index(ascending=False, inplace=True)
        
        # Filter to the specified number of days
        start_date = df.index[0] - timedelta(days=days)
        df = df[df.index >= start_date]
        
        # Calculate average volume
        avg_volume = df['volume'].mean()
        
        # Identify potential block trades (5x or more than average volume)
        block_trade_threshold = avg_volume * 5
        potential_blocks = df[df['volume'] >= block_trade_threshold]
        
        # Additional filter: price impact
        price_impact = []
        for idx in potential_blocks.index:
            try:
                # Get previous bar
                prev_idx = df.index[df.index.get_loc(idx) + 1]
                prev_bar = df.loc[prev_idx]
                
                # Calculate price impact
                price_change_pct = (potential_blocks.loc[idx, 'close'] - prev_bar['close']) / prev_bar['close'] * 100
                price_impact.append(abs(price_change_pct))
            except (IndexError, KeyError):
                price_impact.append(0)
        
        if potential_blocks.empty:
            confirmed_blocks = []
        else:
            potential_blocks['price_impact'] = price_impact
            # Confirm block trades with significant price impact (>0.2%)
            confirmed_blocks = potential_blocks[potential_blocks['price_impact'] > 0.2]
        
        return {
            "has_block_trades": True,
            "block_trade_detected": len(confirmed_blocks) > 0,
            "recent_block_trades": len(confirmed_blocks),
            "block_trade_details": [
                {
                    "timestamp": str(timestamp),
                    "volume": int(row['volume']),
                    "normal_volume": int(avg_volume),
                    "multiple": float(row['volume'] / avg_volume),
                    "price": float(row['close']),
                    "price_impact_percent": float(row['price_impact'])
                }
                for timestamp, row in confirmed_blocks.iterrows()
            ] if not confirmed_blocks.empty else []
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "has_block_trades": False,
            "block_trade_detected": False
        }


async def analyze_option_skew(client: httpx.AsyncClient, symbol: str) -> Dict[str, Any]:
    """
    Analyze options skew for sentiment indications.
    
    Args:
        client: httpx.AsyncClient instance
        symbol: Stock symbol
        
    Returns:
        Dictionary with option skew analysis
    """
    options_data = await get_options_data(client, symbol)
    options_chain = options_data.get("data", [])
    
    if not options_chain:
        return {
            "has_skew_data": False,
            "skew_direction": "neutral",
            "implied_move": 0
        }
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(options_chain)
        
        # Ensure numeric columns
        numeric_cols = ['strike', 'implied_volatility', 'delta', 'gamma', 'theta', 'vega', 'rho']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Group by expiration
        expirations = df['expiration'].unique()
        
        # Find nearest expiration (at least 7 days out)
        today = datetime.now().date()
        valid_expirations = []
        
        for exp in expirations:
            try:
                exp_date = datetime.strptime(exp, '%Y-%m-%d').date()
                days_to_expiry = (exp_date - today).days
                if days_to_expiry >= 7:
                    valid_expirations.append((exp, days_to_expiry))
            except ValueError:
                continue
        
        if not valid_expirations:
            return {
                "has_skew_data": False,
                "skew_direction": "neutral",
                "implied_move": 0
            }
        
        # Sort by days to expiry and take the nearest
        valid_expirations.sort(key=lambda x: x[1])
        target_expiration = valid_expirations[0][0]
        
        # Filter to the target expiration
        exp_chain = df[df['expiration'] == target_expiration]
        
        # Separate calls and puts
        calls = exp_chain[exp_chain['type'] == 'call']
        puts = exp_chain[exp_chain['type'] == 'put']
        
        if calls.empty or puts.empty:
            return {
                "has_skew_data": False,
                "skew_direction": "neutral",
                "implied_move": 0
            }
        
        # Find at-the-money options
        current_price = (calls['strike'].min() + calls['strike'].max()) / 2
        calls['distance_from_atm'] = abs(calls['strike'] - current_price)
        puts['distance_from_atm'] = abs(puts['strike'] - current_price)
        
        atm_call = calls.loc[calls['distance_from_atm'].idxmin()]
        atm_put = puts.loc[puts['distance_from_atm'].idxmin()]
        
        # Calculate put/call skew
        if 'implied_volatility' in df.columns:
            otm_calls = calls[calls['strike'] > current_price]
            otm_puts = puts[puts['strike'] < current_price]
            
            if not otm_calls.empty and not otm_puts.empty:
                # Average IV of OTM puts vs OTM calls
                otm_put_iv = otm_puts['implied_volatility'].mean()
                otm_call_iv = otm_calls['implied_volatility'].mean()
                skew_ratio = otm_put_iv / otm_call_iv if otm_call_iv > 0 else 1.0
                
                # Determine skew direction
                if skew_ratio > 1.1:
                    skew_direction = "bearish"  # Put skew (negative tail risk)
                elif skew_ratio < 0.9:
                    skew_direction = "bullish"  # Call skew
                else:
                    skew_direction = "neutral"
                
                # Calculate implied move
                days_to_expiry = valid_expirations[0][1]
                atm_iv = (float(atm_call['implied_volatility']) + float(atm_put['implied_volatility'])) / 2
                implied_move_percent = atm_iv * np.sqrt(days_to_expiry / 365)
                
                return {
                    "has_skew_data": True,
                    "skew_ratio": float(skew_ratio),
                    "skew_direction": skew_direction,
                    "days_to_expiry": days_to_expiry,
                    "atm_iv": float(atm_iv),
                    "implied_move_percent": float(implied_move_percent),
                    "current_price_estimate": float(current_price)
                }
        
        return {
            "has_skew_data": False,
            "skew_direction": "neutral",
            "implied_move": 0
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "has_skew_data": False,
            "skew_direction": "neutral",
            "implied_move": 0
        }


async def analyze_institutional_activity(
    client: httpx.AsyncClient, 
    symbol: str
) -> Dict[str, Any]:
    """
    Comprehensive analysis of institutional activity by combining options flow and block trades.
    
    Args:
        client: httpx.AsyncClient instance
        symbol: Stock symbol
        
    Returns:
        Dictionary with institutional activity analysis
    """
    # Get options data
    options_data = await get_options_data(client, symbol)
    options_analysis = process_options_flow(options_data)
    
    # Get block trade data
    block_trade_analysis = await detect_block_trades(client, symbol)
    
    # Get options skew
    skew_analysis = await analyze_option_skew(client, symbol)
    
    # Combine all institutional signals
    institutional_activity = (
        options_analysis.get("institutional_activity", False) or
        block_trade_analysis.get("block_trade_detected", False)
    )
    
    # Determine directional bias
    if options_analysis.get("bullish_signal", False) and not options_analysis.get("bearish_signal", False):
        directional_bias = "bullish"
    elif options_analysis.get("bearish_signal", False) and not options_analysis.get("bullish_signal", False):
        directional_bias = "bearish"
    else:
        directional_bias = "neutral"
    
    # Additional bias from options skew
    if skew_analysis.get("has_skew_data", False):
        skew_direction = skew_analysis.get("skew_direction", "neutral")
        if skew_direction != "neutral":
            if directional_bias == "neutral":
                directional_bias = skew_direction
            elif directional_bias != skew_direction:
                directional_bias = "mixed"
    
    return {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "institutional_activity_detected": institutional_activity,
        "directional_bias": directional_bias,
        "options_flow_analysis": options_analysis,
        "block_trade_analysis": block_trade_analysis,
        "options_skew_analysis": skew_analysis,
        "confidence_score": sum([
            1 if options_analysis.get("institutional_activity", False) else 0,
            1 if block_trade_analysis.get("block_trade_detected", False) else 0,
            1 if skew_analysis.get("has_skew_data", False) and skew_analysis.get("skew_direction", "neutral") != "neutral" else 0
        ]) / 3
    }


def format_institutional_analysis(analysis: Dict[str, Any]) -> str:
    """
    Format institutional activity analysis into a readable string.
    
    Args:
        analysis: Dictionary with institutional activity analysis
        
    Returns:
        Formatted string with analysis report
    """
    symbol = analysis['symbol']
    timestamp = analysis['timestamp']
    activity = analysis['institutional_activity_detected']
    bias = analysis['directional_bias']
    confidence = analysis['confidence_score']
    
    options = analysis['options_flow_analysis']
    blocks = analysis['block_trade_analysis']
    skew = analysis['options_skew_analysis']
    
    # Format the report
    lines = [
        f"INSTITUTIONAL ACTIVITY ANALYSIS FOR {symbol}",
        f"Analysis as of {timestamp}",
        f"Activity Detected: {'Yes ✅' if activity else 'No ❌'}",
        f"Directional Bias: {bias.upper()}",
        f"Confidence Score: {confidence:.2f} (0-1 scale)",
        "",
        "OPTIONS FLOW ANALYSIS:",
    ]
    
    if options.get("has_options_data", False):
        call_put_ratio = options.get("call_put_ratio", 0)
        lines.extend([
            f"Call/Put Ratio: {call_put_ratio:.2f}",
            f"Call Volume: {options.get('call_volume', 0)}",
            f"Put Volume: {options.get('put_volume', 0)}",
            f"Large Call Volume: {'Yes' if options.get('large_call_volume', False) else 'No'}",
            f"Large Put Volume: {'Yes' if options.get('large_put_volume', False) else 'No'}",
            f"Unusual Volume Contracts: {options.get('unusual_volume_contracts', 0)}"
        ])
    else:
        lines.append("No options data available")
    
    lines.append("")
    lines.append("BLOCK TRADE ANALYSIS:")
    
    if blocks.get("has_block_trades", False):
        block_trades = blocks.get("recent_block_trades", 0)
        lines.append(f"Block Trades Detected: {block_trades}")
        
        details = blocks.get("block_trade_details", [])
        if details:
            lines.append("\nRecent Block Trade Details:")
            for i, trade in enumerate(details[:3]):  # Show at most 3 trades
                lines.extend([
                    f"Block {i+1}: {trade.get('timestamp', '')}",
                    f"  Volume: {trade.get('volume', 0)} ({trade.get('multiple', 0):.1f}x normal)",
                    f"  Price: ${trade.get('price', 0):.2f} (Impact: {trade.get('price_impact_percent', 0):.2f}%)"
                ])
    else:
        lines.append("No block trades detected")
    
    lines.append("")
    lines.append("OPTIONS SKEW ANALYSIS:")
    
    if skew.get("has_skew_data", False):
        lines.extend([
            f"Skew Ratio: {skew.get('skew_ratio', 1):.2f}",
            f"Skew Direction: {skew.get('skew_direction', 'neutral').upper()}",
            f"Days to Expiry: {skew.get('days_to_expiry', 0)}",
            f"ATM Implied Volatility: {skew.get('atm_iv', 0):.2f}%",
            f"Implied Move: {skew.get('implied_move_percent', 0) * 100:.2f}% by expiration"
        ])
    else:
        lines.append("No options skew data available")
    
    lines.append("")
    lines.append("TRADING IMPLICATIONS:")
    
    if activity:
        if bias == "bullish":
            lines.append("• Institutional positioning appears BULLISH")
            lines.append("• Consider aligning with bullish positioning for mean reversion trades")
        elif bias == "bearish":
            lines.append("• Institutional positioning appears BEARISH")
            lines.append("• Consider aligning with bearish positioning for mean reversion trades")
        elif bias == "mixed":
            lines.append("• Mixed institutional signals detected")
            lines.append("• Exercise caution and look for additional confirmation")
        else:
            lines.append("• Institutional activity detected but without clear directional bias")
            lines.append("• Monitor for developing directional signals")
    else:
        lines.append("• No significant institutional activity detected")
        lines.append("• Lack of institutional participation may indicate lower liquidity")
    
    return "\n".join(lines)
