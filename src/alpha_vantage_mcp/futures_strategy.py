"""
Futures Statistical Trading Strategy Module for Alpha Vantage MCP.

This module provides functions for implementing the complete futures statistical trading 
strategy, combining technical indicators and institutional analysis.
"""

from typing import Dict, List, Any, Tuple, Optional
import httpx
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import local modules
from .technical_indicators import (
    get_price_data,
    get_vix_data,
    get_sector_performance,
    get_stock_sector,
    analyze_market_condition,
    generate_setup_report,
    calculate_position_size,
    format_analysis_report
)

from .institutional_data import (
    analyze_institutional_activity,
    format_institutional_analysis
)

async def analyze_futures_trade_setup(
    client: httpx.AsyncClient,
    symbol: str,
    account_value: float,
    leverage: float = 10.0
) -> Dict[str, Any]:
    """
    Complete analysis of a futures trade setup based on the statistical checklist.
    
    Args:
        client: httpx.AsyncClient instance
        symbol: Stock symbol
        account_value: Trading account value
        leverage: Leverage multiplier
        
    Returns:
        Dictionary with complete trade setup analysis
    """
    try:
        # Step 1: Get market condition data
        vix_df = await get_vix_data(client)
        sp500_df = await get_price_data(client, "^GSPC")
        sector_data = await get_sector_performance(client)
        stock_sector = await get_stock_sector(client, symbol)
        
        # Step 2: Get asset-specific data
        asset_df = await get_price_data(client, symbol)
        
        # Step 3: Analyze market conditions
        market_condition = analyze_market_condition(
            sp500_df,
            vix_df,
            sector_data,
            stock_sector
        )
        
        # Step 4: Generate technical setup report
        setup_report = generate_setup_report(
            symbol,
            asset_df,
            market_condition
        )
        
        # Step 5: Analyze institutional activity
        institutional_analysis = await analyze_institutional_activity(client, symbol)
        
        # Step 6: Calculate position size if setup is valid
        if setup_report["ready_to_trade"]:
            position_sizing = calculate_position_size(
                account_value=account_value,
                entry_price=asset_df['close'].iloc[0],
                stop_loss_percent=7.0,
                risk_percent=3.0,
                leverage=leverage
            )
        else:
            position_sizing = None
        
        # Step 7: Combine all analysis
        trade_signal = setup_report["ready_to_trade"] and institutional_analysis["institutional_activity_detected"]
        
        # Final recommendation
        if trade_signal:
            direction = setup_report["recommendation"]
            recommendation = f"ENTER {direction} POSITION"
        else:
            recommendation = "NO TRADE SETUP DETECTED"
        
        result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "price": asset_df['close'].iloc[0],
            "trade_signal": trade_signal,
            "recommendation": recommendation,
            "technical_analysis": setup_report,
            "institutional_analysis": institutional_analysis,
            "market_condition": market_condition,
            "position_sizing": position_sizing
        }
        
        # Add formatted report
        result["formatted_report"] = format_complete_analysis(result)
        
        return result
    
    except Exception as e:
        return {
            "error": str(e),
            "symbol": symbol,
            "trade_signal": False,
            "recommendation": "ERROR IN ANALYSIS"
        }


def format_complete_analysis(analysis: Dict[str, Any]) -> str:
    """
    Format the complete analysis into a comprehensive report.
    
    Args:
        analysis: Dictionary with complete analysis
        
    Returns:
        Formatted string with complete analysis report
    """
    symbol = analysis["symbol"]
    price = analysis["price"]
    timestamp = analysis["timestamp"]
    recommendation = analysis["recommendation"]
    trade_signal = analysis["trade_signal"]
    
    # Get individual analysis components
    technical = analysis["technical_analysis"]
    institutional = analysis["institutional_analysis"]
    position = analysis["position_sizing"]
    
    # Format header
    lines = [
        f"========= STATISTICAL FUTURES TRADING ANALYSIS =========",
        f"SYMBOL: {symbol} | PRICE: ${price:.2f} | DATE: {timestamp}",
        f"",
        f"RECOMMENDATION: {recommendation}",
        f"",
        f"{'=' * 56}",
        f""
    ]
    
    # Format technical analysis
    lines.append("TECHNICAL SETUP ANALYSIS:")
    lines.append(f"Criteria Met: {technical['confirmed_count']}/{technical['needed_count']}")
    lines.append(f"Mean Reversion Score: {technical['technical_data']['mean_reversion_score']:.2f}")
    lines.append(f"RSI(2): {technical['technical_data']['rsi2']:.2f}")
    lines.append(f"ATR Ratio: {technical['technical_data']['atr_ratio']:.2f}x")
    lines.append("")
    
    # Format institutional analysis
    lines.append("INSTITUTIONAL ACTIVITY ANALYSIS:")
    lines.append(f"Activity Detected: {'Yes' if institutional['institutional_activity_detected'] else 'No'}")
    lines.append(f"Directional Bias: {institutional['directional_bias'].upper()}")
    if 'options_flow_analysis' in institutional and 'call_put_ratio' in institutional['options_flow_analysis']:
        lines.append(f"Call/Put Ratio: {institutional['options_flow_analysis']['call_put_ratio']:.2f}")
    if 'block_trade_analysis' in institutional and 'recent_block_trades' in institutional['block_trade_analysis']:
        lines.append(f"Block Trades: {institutional['block_trade_analysis']['recent_block_trades']}")
    lines.append("")
    
    # Format market condition analysis
    lines.append("MARKET CONDITION ANALYSIS:")
    market = analysis["market_condition"]
    lines.append(f"VIX Change: {market['vix_2day_change']:.2f}%")
    lines.append(f"Sector Performance: {market['sector_performance']:.2f}%")
    lines.append(f"S&P 500 Above MA(20): {'Yes' if market['sp500_above_ma'] else 'No'}")
    lines.append("")
    
    # Format position sizing (if available)
    if position:
        lines.append("POSITION SIZING:")
        lines.append(f"Account Value: ${position['account_value']:.2f}")
        lines.append(f"Risk Amount: ${position['max_risk_amount']:.2f} ({position['max_loss_percent']:.1f}% of account)")
        lines.append(f"Leverage: {position['leverage']:.1f}x")
        lines.append(f"Initial Entry: {position['initial_contracts']} contracts (70%)")
        lines.append(f"Secondary Entry: {position['secondary_contracts']} contracts (30%)")
        lines.append(f"Stop Loss: ${position['stop_loss_price']:.2f}")
        lines.append(f"Target Price: ${position['target_price']:.2f}")
        lines.append(f"Risk/Reward: {position['risk_reward_ratio']:.2f}")
        lines.append("")
    
    # Format trade execution instructions
    lines.append("TRADE EXECUTION INSTRUCTIONS:")
    if trade_signal:
        direction = technical["recommendation"]
        lines.append(f"1. Enter {direction} position using 70% of allocated contracts")
        lines.append(f"2. Use limit orders 0.2% {'below' if direction == 'LONG' else 'above'} current price")
        lines.append(f"3. Set stop loss at ${position['stop_loss_price'] if position else 'N/A'}")
        lines.append(f"4. Set take profit at ${position['target_price'] if position else 'N/A'}")
        lines.append(f"5. Set max holding period of 5 days")
        lines.append(f"6. Consider adding remaining 30% on first pullback")
    else:
        lines.append("No valid setup detected. Continue monitoring.")
    
    return "\n".join(lines)
