"""Shared test fixtures for SearchCarriers plugin + skill validation."""

import asyncio
import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

ROOT = Path(__file__).parent.parent
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def repo_root():
    return ROOT


# ---------------------------------------------------------------------------
# Integration test fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_api_key():
    """Dummy API key for respx-intercepted tests (never hits real API)."""
    return "test-key-not-real"


@pytest.fixture
def live_api_key():
    """Real API key from environment; skips the test if absent."""
    key = os.environ.get("SEARCHCARRIERS_API_KEY", "").strip()
    if not key:
        pytest.skip("SEARCHCARRIERS_API_KEY not set — skipping live test")

    class RedactedSecret(str):
        """String-compatible secret whose diagnostic representation is redacted."""

        def __repr__(self):
            return "<redacted>"

    return RedactedSecret(key)


@pytest.fixture
def fixtures_dir():
    """Path to the tests/fixtures/ directory."""
    return FIXTURES_DIR


@pytest.fixture
def carrier_primary():
    return json.loads((FIXTURES_DIR / "carrier_primary.json").read_text())


@pytest.fixture
def carrier_secondary():
    return json.loads((FIXTURES_DIR / "carrier_secondary.json").read_text())


@pytest.fixture
def authorities_sample():
    return json.loads((FIXTURES_DIR / "authorities_sample.json").read_text())


@pytest.fixture
def insurances_active():
    return json.loads((FIXTURES_DIR / "insurances_active.json").read_text())


@pytest.fixture
def insurances_empty():
    return json.loads((FIXTURES_DIR / "insurances_empty.json").read_text())


@pytest.fixture
def equipment_sample():
    return json.loads((FIXTURES_DIR / "equipment_sample.json").read_text())


@pytest.fixture
def carrier_nested():
    return json.loads((FIXTURES_DIR / "carrier_nested.json").read_text())


def assert_error_payload(result: dict, expected_code: str) -> None:
    """Assert that a handler result is a structured error envelope."""
    assert "error" in result, f"Expected error payload, got: {result}"
    assert result["error"]["code"] == expected_code
    assert "message" in result["error"]


@pytest.fixture
def all_skill_files(repo_root):
    """Find all SKILL.md files in skills/, plugins/, and workflows/."""
    skills = list(repo_root.glob("skills/**/SKILL.md"))
    skills += list(repo_root.glob("plugins/**/SKILL.md"))
    skills += list(repo_root.glob("workflows/**/SKILL.md"))
    return skills


@pytest.fixture
def all_plugin_dirs(repo_root):
    """Find all plugin directories."""
    plugins_dir = repo_root / "plugins"
    if not plugins_dir.exists():
        return []
    return [d for d in plugins_dir.iterdir() if d.is_dir() and d.name != "shared"]


@pytest.fixture
def all_plugin_jsons(all_plugin_dirs):
    """Find all plugin.json files."""
    jsons = []
    for d in all_plugin_dirs:
        pj = d / ".claude-plugin" / "plugin.json"
        if pj.exists():
            jsons.append(pj)
    return jsons


def parse_frontmatter(skill_path: Path) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    content = skill_path.read_text()
    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    import yaml

    try:
        return yaml.safe_load(parts[1]) or {}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Smoke / live-API fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def smoke_reports_dir():
    """Create and return the reports/smoke/ directory."""
    d = ROOT / "reports" / "smoke"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_artifact(directory: Path, name: str, data) -> Path:
    """Save a structural receipt without persisting licensed API values."""

    def shape(value, depth=0):
        if depth >= 3:
            return type(value).__name__
        if isinstance(value, dict):
            return {
                "type": "object",
                "keys": sorted(str(key) for key in value),
                "children": {
                    str(key): shape(child, depth + 1)
                    for key, child in value.items()
                    if key in {"data", "links", "meta", "error", "_pipeline"}
                },
            }
        if isinstance(value, list):
            return {
                "type": "array",
                "count": len(value),
                "item_shape": shape(value[0], depth + 1) if value else None,
            }
        return type(value).__name__

    path = directory / f"{name}.json"
    path.write_text(json.dumps(shape(data), indent=2, sort_keys=True))
    return path


def assert_no_error(result: dict) -> None:
    """Assert that a handler result does not contain an error envelope."""
    assert "error" not in result, f"Unexpected error: {result.get('error')}"


@pytest.fixture(autouse=True)
async def _rate_limit(request):
    """Pause between integration tests to respect API rate limits."""
    yield
    if request.node.get_closest_marker("integration"):
        await asyncio.sleep(0.4)
