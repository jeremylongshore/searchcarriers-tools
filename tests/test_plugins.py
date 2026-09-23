"""Validate all plugin structures and configurations."""

import json

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
