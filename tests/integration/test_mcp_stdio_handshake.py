"""Integration tests for the public, model-neutral MCP stdio boundary."""

import pytest

from tests.mcp_process import SERVER_NAMES, call_tool, initialize_and_list


@pytest.mark.integration
@pytest.mark.parametrize("server_name", SERVER_NAMES)
async def test_each_server_completes_generic_mcp_handshake(repo_root, server_name):
    initialization, tools = await initialize_and_list(repo_root, server_name)

    assert initialization.serverInfo.name == server_name
    assert tools, f"{server_name} published no MCP tools"
    for tool in tools:
        assert tool.name
        assert tool.description
        assert tool.inputSchema["type"] == "object"


@pytest.mark.integration
@pytest.mark.parametrize("server_name", SERVER_NAMES)
async def test_each_server_rejects_unknown_tools_structurally(repo_root, server_name):
    result = await call_tool(repo_root, server_name, "not_a_real_tool", {})
    assert result["error"]["code"] == "unknown_tool"


@pytest.mark.integration
@pytest.mark.parametrize(
    ("server_name", "paid_tool", "arguments"),
    [
        ("searchcarriers-api-bridge", "bulk_lookup", {"dot_numbers": []}),
        ("searchcarriers-carrier-intel", "entity_map", {"dot_number": "1234567"}),
        ("searchcarriers-ops-reporter", "generate_report", {"dot_number": "1234567"}),
        ("searchcarriers-risk-engine", "risk_score", {"dot_number": "1234567"}),
        ("searchcarriers-watchdog", "manage_watchlist", {"action": "list"}),
    ],
)
async def test_each_server_enforces_tier_before_handler(
    repo_root, server_name, paid_tool, arguments
):
    result = await call_tool(repo_root, server_name, paid_tool, arguments, tier="free")
    assert result["error"]["code"] == "tier_insufficient"
    assert result["error"]["detail"]["tool"] == paid_tool
