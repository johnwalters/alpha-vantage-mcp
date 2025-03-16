"""
Alpha Vantage MCP - A server for Alpha Vantage API to enable statistical futures trading strategies
"""

__version__ = "0.2.0"

from .tools import (
    make_alpha_request,
    format_quote,
    format_company_info,
    format_crypto_rate,
    format_time_series,
    format_historical_options
)

from .technical_indicators import (
    get_price_data,
    get_vix_data,
    get_sector_performance,
    get_stock_sector,
    analyze_market_condition,
    generate_setup_report,
    calculate_moving_average,
    calculate_bollinger_bands,
    calculate_rsi,
    calculate_atr,
    calculate_vwap,
    calculate_rate_of_change,
    calculate_mean_reversion_score,
    calculate_position_size
)

from .institutional_data import (
    get_options_data,
    process_options_flow,
    detect_block_trades,
    analyze_option_skew,
    analyze_institutional_activity
)

from .futures_strategy import (
    get_day_of_week_edge,
    get_intraday_timing_edge,
    analyze_futures_trade_setup
)

__all__ = [
    "make_alpha_request",
    "format_quote",
    "format_company_info",
    "format_crypto_rate",
    "format_time_series",
    "format_historical_options",
    "get_price_data",
    "get_vix_data",
    "get_sector_performance",
    "get_stock_sector",
    "analyze_market_condition",
    "generate_setup_report",
    "calculate_moving_average",
    "calculate_bollinger_bands",
    "calculate_rsi",
    "calculate_atr",
    "calculate_vwap", 
    "calculate_rate_of_change",
    "calculate_mean_reversion_score",
    "calculate_position_size",
    "get_options_data",
    "process_options_flow",
    "detect_block_trades",
    "analyze_option_skew",
    "analyze_institutional_activity",
    "get_day_of_week_edge",
    "get_intraday_timing_edge",
    "analyze_futures_trade_setup"
]
