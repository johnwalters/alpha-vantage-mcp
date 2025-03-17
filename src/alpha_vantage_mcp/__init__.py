"""
Alpha Vantage MCP Server

A Model Context Protocol (MCP) server that provides real-time access to financial 
market data through the Alpha Vantage API.
"""

__version__ = "0.2.0"

from .server import server, handle_list_tools, handle_call_tool
