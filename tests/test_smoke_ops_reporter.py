"""Live smoke tests for Ops Reporter handlers — hits real SearchCarriers API."""

import sys
from pathlib import Path

import pytest

_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root))
sys.path.insert(
    0,
    str(_repo_root / "plugins" / "searchcarriers-ops-reporter" / "scripts"),
)

from conftest import assert_no_error, save_artifact  # noqa: E402
from ops_reporter_mcp import (  # noqa: E402
    _export_data,
    _generate_compare,
    _generate_fleet,
    _generate_report,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DOT_PRIMARY = "1234567"
DOT_SECONDARY = "7654321"


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSmokeOpsReporter:
    """Live smoke tests — require SEARCHCARRIERS_API_KEY in environment."""

    async def test_generate_report(self, live_api_key, smoke_reports_dir):
        """generate_report returns a non-empty markdown report for J.B. Hunt."""
        result = await _generate_report({"dot_number": DOT_PRIMARY}, live_api_key)

        assert_no_error(result)
        assert "report" in result, f"Missing 'report' key in result: {list(result)}"
        assert isinstance(result["report"], str), "report must be a string"
        assert result["report"].strip(), "report must be non-empty"

        save_artifact(smoke_reports_dir, "generate_report", result)

    async def test_generate_fleet(self, live_api_key, smoke_reports_dir):
        """generate_fleet returns fleet-related keys for J.B. Hunt."""
        result = await _generate_fleet({"dot_number": DOT_PRIMARY}, live_api_key)

        assert_no_error(result)
        for key in ("report", "fleet_size"):
            assert key in result, f"Missing key '{key}' in result: {list(result)}"

        save_artifact(smoke_reports_dir, "generate_fleet", result)

    async def test_generate_compare(self, live_api_key, smoke_reports_dir):
        """generate_compare returns comparison data for J.B. Hunt vs Sample Logistics."""
        result = await _generate_compare(
            {"dot_numbers": [DOT_PRIMARY, DOT_SECONDARY]}, live_api_key
        )

        assert_no_error(result)
        for key in ("report", "carrier_count", "carriers"):
            assert key in result, f"Missing key '{key}' in result: {list(result)}"

        save_artifact(smoke_reports_dir, "generate_compare", result)

    async def test_export_data_json(self, live_api_key, smoke_reports_dir):
        """export_data with format=json returns exported data for J.B. Hunt."""
        result = await _export_data({"dot_number": DOT_PRIMARY, "format": "json"}, live_api_key)

        assert_no_error(result)
        assert "data" in result, f"Missing 'data' key in result: {list(result)}"
        assert result["data"], "exported data must be non-empty"

        save_artifact(smoke_reports_dir, "export_data_json", result)

    async def test_export_data_markdown(self, live_api_key, smoke_reports_dir):
        """export_data with format=markdown returns exported data for J.B. Hunt."""
        result = await _export_data({"dot_number": DOT_PRIMARY, "format": "markdown"}, live_api_key)

        assert_no_error(result)
        assert "data" in result, f"Missing 'data' key in result: {list(result)}"
        assert result["data"], "exported data must be non-empty"

        save_artifact(smoke_reports_dir, "export_data_markdown", result)
