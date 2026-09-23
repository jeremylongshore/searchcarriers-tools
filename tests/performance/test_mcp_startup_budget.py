"""Bound the latency of the local MCP startup path used by model clients."""

from time import monotonic

import pytest

from tests.mcp_process import initialize_and_list


@pytest.mark.performance
async def test_carrier_intel_initializes_within_five_seconds(repo_root):
    started = monotonic()
    initialization, tools = await initialize_and_list(repo_root, "searchcarriers-carrier-intel")
    elapsed = monotonic() - started

    assert initialization.serverInfo.name == "searchcarriers-carrier-intel"
    assert tools
    assert elapsed < 5.0, f"MCP startup took {elapsed:.2f}s (budget: 5.00s)"
