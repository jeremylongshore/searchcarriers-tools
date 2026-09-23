"""Architecture fitness rules for the five independently deployable MCP servers."""

import ast


def _imports(path):
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def test_shared_modules_never_import_plugin_implementations(repo_root):
    for path in (repo_root / "plugins" / "shared").glob("*.py"):
        violations = [name for name in _imports(path) if name.endswith("_mcp")]
        assert not violations, f"{path} imports plugin runtime(s): {violations}"


def test_plugin_servers_never_import_sibling_plugin_runtimes(repo_root):
    server_paths = sorted((repo_root / "plugins").glob("*/scripts/*_mcp.py"))
    runtime_names = {path.stem for path in server_paths}
    for path in server_paths:
        violations = sorted((set(_imports(path)) & runtime_names) - {path.stem})
        assert not violations, f"{path} imports sibling runtime(s): {violations}"


def test_api_endpoint_constants_have_one_owner(repo_root):
    shared_contract = repo_root / "plugins" / "shared" / "api_contract.py"
    assert shared_contract.is_file()
    for path in (repo_root / "plugins").glob("*/scripts/api_contract.py"):
        raise AssertionError(f"plugin-local API contract duplicates shared owner: {path}")
