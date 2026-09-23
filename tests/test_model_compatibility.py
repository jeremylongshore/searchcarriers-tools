"""Prove the executable SearchCarriers boundary is model-provider neutral."""

import ast
import json
from pathlib import Path

PROVIDER_SDKS = {
    "anthropic",
    "google.generativeai",
    "groq",
    "openai",
    "vertexai",
    "xai_sdk",
}


def _root_config(repo_root: Path) -> dict:
    return json.loads((repo_root / ".mcp.json").read_text())["mcpServers"]


def test_root_config_aggregates_every_plugin(repo_root):
    root_servers = _root_config(repo_root)
    plugin_configs = {}
    for path in sorted((repo_root / "plugins").glob("*/.mcp.json")):
        plugin_configs.update(json.loads(path.read_text())["mcpServers"])

    assert set(root_servers) == set(plugin_configs)
    for name, config in root_servers.items():
        assert config["command"] == ".venv/bin/python"
        assert config["args"] == plugin_configs[name]["args"]
        assert config["env"] == plugin_configs[name]["env"]
        assert (repo_root / config["args"][0]).is_file()


def test_mcp_runtimes_do_not_import_model_provider_sdks(repo_root):
    imported = set()
    server_files = sorted((repo_root / "plugins").glob("*/scripts/*_mcp.py"))
    assert len(server_files) == 5

    for server_file in server_files:
        tree = ast.parse(server_file.read_text(), filename=str(server_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)

    violations = sorted(
        module
        for module in imported
        if any(module == sdk or module.startswith(f"{sdk}.") for sdk in PROVIDER_SDKS)
    )
    assert not violations, f"MCP runtimes import model-provider SDKs: {violations}"


def test_customer_docs_do_not_claim_a_claude_only_runtime(repo_root):
    banned = (
        "requires Claude Code",
        "Claude invokes",
        "Claude receives",
        "Claude orchestrates",
        "Claude parses",
    )
    customer_docs = [path for path in (repo_root / "plugins").glob("*/docs/0[1-4]-*.md")]
    assert customer_docs
    for path in customer_docs:
        text = path.read_text()
        matches = [phrase for phrase in banned if phrase in text]
        assert not matches, f"{path}: Claude-only runtime wording: {matches}"
