"""Live smoke tests for API Bridge handlers — hits real SearchCarriers API."""

import sys
from pathlib import Path

import pytest

_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root))
sys.path.insert(
    0,
    str(_repo_root / "plugins" / "searchcarriers-api-bridge" / "scripts"),
)

from api_bridge_mcp import (  # noqa: E402
    _api_health,
    _bulk_lookup,
)
from conftest import assert_no_error, save_artifact  # noqa: E402

DOT_PRIMARY = "299569"
DOT_SECONDARY = "80806"


@pytest.mark.integration
class TestSmokeApiBridge:
    """Live smoke tests for the API Bridge handler functions."""

    async def test_api_health_full(self, live_api_key, smoke_reports_dir):
        """Probe all endpoints; result must be a valid health report with endpoint data."""
        result = await _api_health({}, live_api_key)

        assert_no_error(result)
        assert "status" in result, (
            f"Expected 'status' key in result; got keys: {list(result.keys())}"
        )
        assert result["status"] in ("healthy", "degraded", "down"), (
            f"Unexpected aggregate status: {result['status']!r}"
        )
        assert "endpoints" in result, f"Expected 'endpoints' key; got keys: {list(result.keys())}"
        endpoints = result["endpoints"]
        assert isinstance(endpoints, list) and len(endpoints) > 0, (
            "Expected at least one endpoint record in result"
        )
        first = endpoints[0]
        assert "name" in first, f"Endpoint record missing 'name'; got keys: {list(first.keys())}"
        assert "health" in first, (
            f"Endpoint record missing 'health'; got keys: {list(first.keys())}"
        )
        assert "response_ms" in first, (
            f"Endpoint record missing 'response_ms'; got keys: {list(first.keys())}"
        )

        save_artifact(smoke_reports_dir, "api_health", result)

    async def test_api_health_filtered(self, live_api_key, smoke_reports_dir):
        """Filtering by endpoint name returns only the requested endpoint."""
        result = await _api_health({"endpoints": ["v3_search"]}, live_api_key)

        assert_no_error(result)
        assert "endpoints" in result, f"Expected 'endpoints' key; got keys: {list(result.keys())}"
        endpoints = result["endpoints"]
        assert len(endpoints) == 1, (
            f"Expected exactly 1 endpoint for filter ['v3_search']; got {len(endpoints)}"
        )
        assert endpoints[0]["name"] == "v3_search", (
            f"Expected endpoint name 'v3_search'; got {endpoints[0]['name']!r}"
        )

        save_artifact(smoke_reports_dir, "api_health_filtered", result)

    async def test_bulk_lookup(self, live_api_key, smoke_reports_dir):
        """Bulk lookup returns data records keyed to each requested DOT number."""
        dot_numbers = [DOT_PRIMARY, DOT_SECONDARY]
        result = await _bulk_lookup({"dot_numbers": dot_numbers}, live_api_key)

        assert_no_error(result)
        assert "results" in result, f"Expected 'results' key; got keys: {list(result.keys())}"
        assert "total" in result, f"Expected 'total' key; got keys: {list(result.keys())}"
        assert result["total"] == len(dot_numbers), (
            f"Expected total={len(dot_numbers)}; got {result['total']}"
        )
        records = result["results"]
        assert isinstance(records, list) and len(records) > 0, "Expected at least one result record"
        returned_dots = {r["dot_number"] for r in records}
        for dot in dot_numbers:
            assert dot in returned_dots, (
                f"DOT {dot!r} missing from result; returned DOTs: {returned_dots}"
            )
        for record in records:
            assert "data" in record, (
                f"Result record for DOT {record.get('dot_number')!r} missing 'data' key"
            )

        save_artifact(smoke_reports_dir, "bulk_lookup", result)
