# -*- coding: utf-8 -*-
from fastmcp import FastMCP


mcp = FastMCP("get_weather_mcp")


@mcp.tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"{city}天气晴朗，万里碧空飘着朵朵白云!"


if __name__ == "__main__":
    mcp.run()
