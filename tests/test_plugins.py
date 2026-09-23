"""Validate all plugin structures and configurations."""

import json
import re

import yaml

from plugins.shared.tier_gate import TOOL_TIERS

REQUIRED_PLUGIN_FIELDS = ["name", "description"]
TIER_VALUES = {"free", "basic", "pro", "proplus", "smb", "enterprise"}
DOC_FILES = [
    "01-BUSINESS-CASE.md",
    "02-PRD.md",
    "03-ARCHITECTURE.md",
    "04-USER-JOURNEY.md",
    "05-TECHNICAL-SPEC.md",
    "06-STATUS.md",
]


class TestPluginJson:
    def test_plugins_dir_exists(self, repo_root):
        assert (repo_root / "plugins").is_dir()

    def test_plugin_json_valid(self, all_plugin_jsons):
        for pj in all_plugin_jsons:
            data = json.loads(pj.read_text())
            assert isinstance(data, dict), f"{pj}: plugin.json must be a JSON object"

    def test_required_fields(self, all_plugin_jsons):
        for pj in all_plugin_jsons:
            data = json.loads(pj.read_text())
            for field in REQUIRED_PLUGIN_FIELDS:
                assert field in data, f"{pj}: Missing required field '{field}'"

    def test_name_format(self, all_plugin_jsons):
        for pj in all_plugin_jsons:
            data = json.loads(pj.read_text())
            name = data.get("name", "")
            assert name.startswith("searchcarriers-"), (
                f"{pj}: Plugin name must start with 'searchcarriers-'"
            )

    def test_manifest_tools_match_runtime_and_tier_registry(self, all_plugin_jsons):
        for pj in all_plugin_jsons:
            data = json.loads(pj.read_text())
            manifest_tools = {tool["name"]: tool["min_tier"] for tool in data.get("tools", [])}
            server_files = list(pj.parent.parent.glob("scripts/*_mcp.py"))
            assert len(server_files) == 1, f"{pj.parent.parent}: expected one MCP server"
            runtime_tools = set(
                re.findall(r'Tool\(\s*name="([a-z0-9_]+)"', server_files[0].read_text())
            )
            assert set(manifest_tools) == runtime_tools, (
                f"{pj}: manifest tools {sorted(manifest_tools)} do not match "
                f"runtime tools {sorted(runtime_tools)}"
            )
            for tool, tier in manifest_tools.items():
                assert TOOL_TIERS.get(tool) == tier, (
                    f"{pj}: {tool} tier {tier} does not match shared registry "
                    f"{TOOL_TIERS.get(tool)!r}"
                )

    def test_package_versions_match_root_release(self, repo_root, all_plugin_jsons):
        release = (repo_root / "VERSION").read_text().strip()
        for pj in all_plugin_jsons:
            assert json.loads(pj.read_text())["version"] == release

        for skill in repo_root.glob("**/SKILL.md"):
            if ".venv" in skill.parts:
                continue
            frontmatter = yaml.safe_load(skill.read_text().split("---", 2)[1])
            assert frontmatter["version"] == release, f"{skill}: version drift"


class TestPluginStructure:
    def test_readme_exists(self, all_plugin_dirs):
        for pd in all_plugin_dirs:
            assert (pd / "README.md").exists(), f"{pd}: Missing README.md"

    def test_scripts_dir_exists(self, all_plugin_dirs):
        for pd in all_plugin_dirs:
            scripts = pd / "scripts"
            if scripts.exists():
                mcp_files = list(scripts.glob("*_mcp.py"))
                assert len(mcp_files) > 0, f"{pd}/scripts/: No MCP server file found"

    def test_docs_completeness(self, all_plugin_dirs):
        for pd in all_plugin_dirs:
            docs = pd / "docs"
            if not docs.exists():
                continue
            for doc in DOC_FILES:
                assert (docs / doc).exists(), f"{pd}/docs/{doc}: Missing from 6-doc set"


class TestTierGating:
    def test_tier_values_valid(self, all_plugin_jsons):
        for pj in all_plugin_jsons:
            data = json.loads(pj.read_text())
            # Plugin-level tier
            plugin_tier = data.get("min_tier", "free")
            assert plugin_tier in TIER_VALUES, f"{pj}: Invalid plugin tier '{plugin_tier}'"
            # Per-tool tiers (tools is a list of dicts)
            tools = data.get("tools", [])
            for tool in tools:
                tier = tool.get("min_tier", "free")
                assert tier in TIER_VALUES, (
                    f"{pj}: Invalid tier '{tier}' for tool '{tool.get('name', '?')}'"
                )
