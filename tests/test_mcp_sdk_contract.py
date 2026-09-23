"""The plugin MCP servers register tools with the decorator API of the MCP Python SDK 1.x.

SDK 2.x removed ``Server.list_tools()`` / ``Server.call_tool()``. Every server calls them
inside ``serve()``, which no other test executes, so an open-ended ``mcp>=1.0`` requirement
let a fresh install resolve 2.x and crash at startup while this suite stayed green
(found 2026-09-20). This test pins the contract: it fails if the installed SDK lacks the
API the servers use, and it fails if a requirement is left uncapped while they still use it.
Port the servers to the 2.x registration API, then delete the cap and this test together.
"""

import re
from pathlib import Path

import pytest
from mcp.server import Server

ROOT = Path(__file__).resolve().parent.parent
SERVERS = sorted(ROOT.glob("plugins/*/scripts/*_mcp.py"))
DECORATORS = ("list_tools", "call_tool")


def _uses_decorator_api(path: Path) -> bool:
    return bool(re.search(r"@\w+\.(list_tools|call_tool)\(\)", path.read_text(encoding="utf-8")))


def test_there_are_plugin_servers_to_check():
    assert SERVERS, "no plugins/*/scripts/*_mcp.py found; this contract test is checking nothing"
    assert any(_uses_decorator_api(p) for p in SERVERS)


@pytest.mark.parametrize("attr", DECORATORS)
def test_installed_sdk_has_the_decorator_api_the_servers_use(attr):
    assert hasattr(Server("contract-probe"), attr), (
        f"installed mcp SDK has no Server.{attr}(); the plugin servers would crash in serve()"
    )


@pytest.mark.parametrize("server", SERVERS, ids=lambda p: p.parent.parent.name)
def test_requirement_is_capped_while_the_server_uses_the_decorator_api(server):
    if not _uses_decorator_api(server):
        pytest.skip("server no longer uses the 1.x decorator API")
    req = (server.parent / "requirements.txt").read_text(encoding="utf-8")
    line = next((ln for ln in req.splitlines() if re.match(r"^mcp\b", ln.strip())), None)
    assert line is not None, f"{server.parent.name}: no mcp requirement declared"
    spec = line.split("#")[0]
    assert re.search(r"<\s*2\b", spec), f"{server.parent.name}: '{line}' does not cap mcp below 2"
