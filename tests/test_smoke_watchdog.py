"""Live smoke tests for Watchdog handlers — hits real SearchCarriers API."""

import sys
from pathlib import Path

import pytest

_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root))
sys.path.insert(
    0,
    str(_repo_root / "plugins" / "searchcarriers-watchdog" / "scripts"),
)

from conftest import assert_no_error, save_artifact  # noqa: E402
from watchdog_mcp import (  # noqa: E402
    _get_alerts,
    _manage_watchlist,
    _monitor_compliance,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DOT_PRIMARY = "299569"


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestWatchdogSmoke:
    """Live smoke tests for the three Watchdog MCP handlers.

    Skipped automatically when SEARCHCARRIERS_API_KEY is not set.
    The ``add`` action is intentionally omitted to avoid side effects on the
    real account.  ``_route_alert`` is a pure formatter with no API calls and
    is covered by unit tests instead.
    """

    @pytest.mark.xfail(reason="Watch endpoint returns 404 when no watchlist configured")
    async def test_list_watchlist(self, live_api_key, smoke_reports_dir):
        """_manage_watchlist action='list' returns watchlist data without error."""
        result = await _manage_watchlist({"action": "list"}, live_api_key)

        assert_no_error(result)
        assert result.get("action") == "list"
        assert "watchlist_count" in result, f"Missing 'watchlist_count' in result: {result}"
        assert "carriers" in result, f"Missing 'carriers' in result: {result}"
        assert isinstance(result["carriers"], list), (
            f"'carriers' must be a list, got: {type(result['carriers'])}"
        )

        save_artifact(smoke_reports_dir, "watchlist_list", result)

    @pytest.mark.xfail(reason="Alerts endpoint returns 404 when no watchlist configured")
    async def test_get_alerts(self, live_api_key, smoke_reports_dir):
        """_get_alerts returns alert summary keys without error."""
        result = await _get_alerts({}, live_api_key)

        assert_no_error(result)
        assert "alert_count" in result, f"Missing 'alert_count' in result: {result}"
        assert "alerts" in result, f"Missing 'alerts' in result: {result}"
        assert "categories" in result, f"Missing 'categories' in result: {result}"
        assert isinstance(result["alerts"], list), (
            f"'alerts' must be a list, got: {type(result['alerts'])}"
        )
        assert isinstance(result["categories"], dict), (
            f"'categories' must be a dict, got: {type(result['categories'])}"
        )

        save_artifact(smoke_reports_dir, "get_alerts", result)

    async def test_monitor_compliance(self, live_api_key, smoke_reports_dir):
        """_monitor_compliance returns a structured compliance report for a known carrier."""
        result = await _monitor_compliance({"dot_number": DOT_PRIMARY}, live_api_key)

        assert_no_error(result)
        assert result.get("dot_number") == DOT_PRIMARY, (
            f"Expected dot_number={DOT_PRIMARY!r}, got: {result.get('dot_number')!r}"
        )
        assert "compliance_status" in result, f"Missing 'compliance_status' in result: {result}"
        assert result["compliance_status"] in ("compliant", "drift", "critical"), (
            f"Unexpected compliance_status value: {result['compliance_status']!r}"
        )
        assert "checks" in result, f"Missing 'checks' in result: {result}"
        assert isinstance(result["checks"], list), (
            f"'checks' must be a list, got: {type(result['checks'])}"
        )
        assert "drift_items" in result, f"Missing 'drift_items' in result: {result}"

        save_artifact(smoke_reports_dir, "monitor_compliance", result)
