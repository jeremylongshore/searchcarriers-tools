"""Shared helpers for exercising the public MCP stdio process boundary."""

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_NAMES = (
    "searchcarriers-api-bridge",
    "searchcarriers-carrier-intel",
    "searchcarriers-ops-reporter",
    "searchcarriers-risk-engine",
    "searchcarriers-watchdog",
)


def root_config(repo_root: Path) -> dict:
    """Load the client-neutral project MCP configuration."""
    return json.loads((repo_root / ".mcp.json").read_text())["mcpServers"]


def server_parameters(repo_root: Path, server_name: str, tier: str = "free"):
    """Build process parameters with a synthetic key and explicit product tier."""
    config = root_config(repo_root)[server_name]
    return StdioServerParameters(
        command=sys.executable,
        args=config["args"],
        env={
            **os.environ,
            "SEARCHCARRIERS_API_KEY": "test|model-neutral-contract",
            "SEARCHCARRIERS_TIER": tier,
        },
    )


async def initialize_and_list(repo_root: Path, server_name: str):
    """Start one server, initialize JSON-RPC, and return its advertised tools."""
    parameters = server_parameters(repo_root, server_name)

    async with asyncio.timeout(15):
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                initialization = await session.initialize()
                tools = (await session.list_tools()).tools
    return initialization, tools


async def call_tool(
    repo_root: Path, server_name: str, tool_name: str, arguments: dict, tier="free"
):
    """Call a tool through JSON-RPC and parse the server's JSON text envelope."""
    parameters = server_parameters(repo_root, server_name, tier=tier)
    async with asyncio.timeout(15):
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
    assert not result.isError
    return json.loads(result.content[0].text)
