pytest_plugins = "pytest_asyncio"
from dotenv import load_dotenv
import sys
import os
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import types
import asyncio
from src.alpha_vantage_mcp import server

@pytest.mark.asyncio
async def test_get_top_gainers_losers(monkeypatch):
    # Mock the make_alpha_request function
    async def mock_make_alpha_request(client, function):
        return ["AAPL +5%", "TSLA -3%"]

    monkeypatch.setattr(server, "make_alpha_request", mock_make_alpha_request)

    result = await server.handle_call_tool("get-top-gainers-losers", {})
    assert isinstance(result, list)
    assert any("Top Gainers and Losers" in c.text for c in result if hasattr(c, "text"))
    assert any("AAPL" in c.text for c in result if hasattr(c, "text"))
    assert any("TSLA" in c.text for c in result if hasattr(c, "text"))
