"""Live smoke tests for Carrier Intel handlers — hits real SearchCarriers API."""

import sys
from pathlib import Path

import pytest

_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root))
sys.path.insert(
    0,
    str(_repo_root / "plugins" / "searchcarriers-carrier-intel" / "scripts"),
)

from carrier_intel_mcp import (  # noqa: E402
    _carrier_lookup,
    _carrier_profile,
    _entity_map,
    _fleet_summary,
)
from conftest import assert_no_error, save_artifact  # noqa: E402

DOT_PRIMARY = "299569"


@pytest.mark.integration
class TestSmokeCarrierIntel:
    """Live smoke tests for all four Carrier Intel handler functions."""

    async def test_dot_lookup(self, live_api_key, smoke_reports_dir):
        """DOT number query auto-detects as dotNumber and returns a carrier record."""
        result = await _carrier_lookup({"query": DOT_PRIMARY}, live_api_key)

        assert_no_error(result)
        assert result["search_type_used"] == "dot"
        assert "results" in result
        data = result["results"].get("data", [])
        assert len(data) > 0, "Expected at least one result for the smoke-test DOT"
        first = data[0]
        assert first.get("legal_name"), (
            f"Expected non-empty legal_name; got keys: {list(first.keys())[:10]}"
        )

        save_artifact(smoke_reports_dir, "carrier_lookup_dot", result)

    async def test_name_search(self, live_api_key, smoke_reports_dir):
        """Free-text name query auto-detects as superSearchTerm."""
        result = await _carrier_lookup({"query": "J B Hunt Transport"}, live_api_key)

        assert_no_error(result)
        assert result["search_type_used"] == "text"
        data = result["results"].get("data", [])
        assert len(data) > 0, "Expected at least one result for the live name query"

        save_artifact(smoke_reports_dir, "carrier_lookup_name", result)

    async def test_scac_lookup(self, live_api_key, smoke_reports_dir):
        """Explicit scac search_type routes to the SCAC endpoint."""
        result = await _carrier_lookup({"query": "HJBT", "search_type": "scac"}, live_api_key)

        assert_no_error(result)
        assert result["search_type_used"] == "scac"
        assert "results" in result

        save_artifact(smoke_reports_dir, "carrier_lookup_scac", result)

    async def test_full_profile(self, live_api_key, smoke_reports_dir):
        """Full profile assembles carrier, authorities, and insurance records."""
        result = await _carrier_profile({"dot_number": DOT_PRIMARY}, live_api_key)

        assert_no_error(result)
        assert "carrier" in result
        assert "authorities" in result
        assert "insurance" in result or "insurances" in result

        save_artifact(smoke_reports_dir, "carrier_profile", result)

    async def test_entity_map(self, live_api_key, smoke_reports_dir):
        """Entity map returns seed_carrier and related_carriers."""
        result = await _entity_map({"dot_number": DOT_PRIMARY}, live_api_key)

        assert_no_error(result)
        assert "seed_carrier" in result, (
            f"Expected 'seed_carrier' in result; got keys: {list(result.keys())}"
        )
        assert "related_carriers" in result, (
            f"Expected 'related_carriers' in result; got keys: {list(result.keys())}"
        )
        assert isinstance(result["related_carriers"], list)

        save_artifact(smoke_reports_dir, "entity_map", result)

    async def test_fleet_summary(self, live_api_key, smoke_reports_dir):
        """Fleet summary returns recognisable fleet data keys."""
        result = await _fleet_summary({"dot_number": DOT_PRIMARY}, live_api_key)

        assert_no_error(result)
        has_fleet_key = any(
            k in result for k in ("summary", "equipment", "vehicles", "total_power_units", "fleet")
        )
        assert has_fleet_key, (
            f"Expected at least one fleet data key in result; got keys: {list(result.keys())}"
        )

        save_artifact(smoke_reports_dir, "fleet_summary", result)
