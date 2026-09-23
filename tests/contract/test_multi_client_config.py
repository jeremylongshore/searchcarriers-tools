"""Contract tests for model-neutral client configuration and server schemas."""

import json

import pytest

from tests.mcp_process import SERVER_NAMES, initialize_and_list, root_config


@pytest.mark.contract
def test_root_config_uses_portable_project_relative_commands(repo_root):
    servers = root_config(repo_root)
    assert set(servers) == set(SERVER_NAMES)
    for config in servers.values():
        assert config["command"] == ".venv/bin/python"
        assert not config["args"][0].startswith("/")
        assert (repo_root / config["args"][0]).is_file()


@pytest.mark.contract
@pytest.mark.parametrize("server_name", SERVER_NAMES)
async def test_stdio_tool_names_match_plugin_manifest(repo_root, server_name):
    _, tools = await initialize_and_list(repo_root, server_name)
    manifest_path = repo_root / "plugins" / server_name / ".claude-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text())
    manifest_names = {tool["name"] for tool in manifest["tools"]}
    assert {tool.name for tool in tools} == manifest_names
