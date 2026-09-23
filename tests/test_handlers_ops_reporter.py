"""Integration tests for ops_reporter_mcp handler functions.

Tests exercise the actual handler logic with respx intercepting HTTP calls
at the transport layer. No real API calls are made.
"""

import json
import sys
from pathlib import Path

import httpx
import respx

_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root))
sys.path.insert(
    0,
    str(_repo_root / "plugins" / "searchcarriers-ops-reporter" / "scripts"),
)

from conftest import assert_error_payload  # noqa: E402
from ops_reporter_mcp import (  # noqa: E402
    API_BASE,
    SEARCH_BASE,
    _export_data,
    _generate_compare,
    _generate_fleet,
    _generate_report,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_report_routes(router, carrier, authorities, insurances, dot="1234567"):
    """Set up the three standard routes used by report handlers."""
    router.get(f"{SEARCH_BASE}/search").mock(return_value=httpx.Response(200, json=carrier))
    router.get(f"/company/{dot}/authorities").mock(
        return_value=httpx.Response(200, json=authorities)
    )
    router.get(f"/company/{dot}/insurances").mock(return_value=httpx.Response(200, json=insurances))


# ---------------------------------------------------------------------------
# _generate_report
# ---------------------------------------------------------------------------


class TestGenerateReport:
    """Tests for the generate_report handler."""

    async def test_required_keys(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Response has required top-level keys."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_report_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _generate_report({"dot_number": "1234567"}, fake_api_key)

        for key in ("report", "format", "carrier_name", "_pipeline"):
            assert key in result, f"Missing key: {key}"

    async def test_report_starts_with_heading(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Report starts with a markdown heading."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_report_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _generate_report({"dot_number": "1234567"}, fake_api_key)

        assert result["report"].startswith("# ")

    async def test_all_sections_present(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Report contains all 7 expected sections."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_report_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _generate_report({"dot_number": "1234567"}, fake_api_key)

        report = result["report"]
        expected_sections = [
            "Company Overview",
            "Operating Status",
            "Safety Summary",
            "Insurance Coverage",
            "Risk Assessment",
            "Recommendation",
            "Disclaimer",
        ]
        for section in expected_sections:
            assert section in report, f"Missing section: {section}"

    async def test_contains_dot_and_name(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Report contains the carrier's DOT number and name."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_report_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _generate_report({"dot_number": "1234567"}, fake_api_key)

        assert "1234567" in result["report"]
        assert "EXAMPLE FREIGHT" in result["report"]

    async def test_format_text_strips_markdown(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """format=text strips markdown bold/italic/heading syntax."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_report_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _generate_report(
                {"dot_number": "1234567", "format": "text"}, fake_api_key
            )

        assert result["format"] == "text"
        # Should not have markdown heading markers at line starts
        for line in result["report"].split("\n"):
            stripped = line.lstrip()
            if stripped:
                assert not stripped.startswith("# ") or "=" in line

    async def test_format_defaults_to_markdown(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Default format is markdown."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_report_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _generate_report({"dot_number": "1234567"}, fake_api_key)

        assert result["format"] == "markdown"

    async def test_search_failure(self, fake_api_key):
        """Search failure returns error payload."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(return_value=httpx.Response(500, json={}))
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            result = await _generate_report({"dot_number": "1234567"}, fake_api_key)

        assert_error_payload(result, "api_error")

    async def test_empty_search_not_found(self, fake_api_key):
        """Empty search result returns not_found error."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            result = await _generate_report({"dot_number": "1234567"}, fake_api_key)

        assert_error_payload(result, "not_found")


# ---------------------------------------------------------------------------
# _generate_fleet
# ---------------------------------------------------------------------------


class TestGenerateFleet:
    """Tests for the generate_fleet handler."""

    async def test_required_keys(self, fake_api_key, carrier_primary, equipment_sample):
        """Response has required top-level keys."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/equipment").mock(
                return_value=httpx.Response(200, json=equipment_sample)
            )
            result = await _generate_fleet({"dot_number": "1234567"}, fake_api_key)

        for key in ("report", "fleet_size", "_pipeline"):
            assert key in result, f"Missing key: {key}"

    async def test_fleet_overview_and_composition_sections(
        self, fake_api_key, carrier_primary, equipment_sample
    ):
        """Report contains Fleet Overview and Fleet Composition sections."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/equipment").mock(
                return_value=httpx.Response(200, json=equipment_sample)
            )
            result = await _generate_fleet({"dot_number": "1234567"}, fake_api_key)

        assert "Fleet Overview" in result["report"]
        assert "Fleet Composition" in result["report"]

    async def test_fleet_size_dict_structure(self, fake_api_key, carrier_primary, equipment_sample):
        """fleet_size dict has expected keys."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/equipment").mock(
                return_value=httpx.Response(200, json=equipment_sample)
            )
            result = await _generate_fleet({"dot_number": "1234567"}, fake_api_key)

        fs = result["fleet_size"]
        for key in ("power_units", "drivers", "equipment_records", "equipment_types"):
            assert key in fs, f"Missing fleet_size key: {key}"

    async def test_equipment_type_counts(self, fake_api_key, carrier_primary, equipment_sample):
        """Equipment type counts match fixture data."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/equipment").mock(
                return_value=httpx.Response(200, json=equipment_sample)
            )
            result = await _generate_fleet({"dot_number": "1234567"}, fake_api_key)

        types = result["fleet_size"]["equipment_types"]
        assert types["Truck Tractor"] == 2
        assert types["Trailer"] == 1


# ---------------------------------------------------------------------------
# _generate_compare
# ---------------------------------------------------------------------------


class TestGenerateCompare:
    """Tests for the generate_compare handler."""

    async def test_fewer_than_2_carriers_error(self, fake_api_key):
        """Less than 2 DOTs returns an error."""
        result = await _generate_compare({"dot_numbers": ["1234567"]}, fake_api_key)
        assert_error_payload(result, "invalid_input")

    async def test_more_than_5_carriers_error(self, fake_api_key):
        """More than 5 DOTs returns an error."""
        result = await _generate_compare(
            {"dot_numbers": ["1", "2", "3", "4", "5", "6"]}, fake_api_key
        )
        assert_error_payload(result, "invalid_input")

    async def test_required_keys(
        self,
        fake_api_key,
        carrier_primary,
        carrier_secondary,
        authorities_sample,
        insurances_active,
    ):
        """Response has required keys."""
        with respx.mock(base_url=API_BASE) as router:
            # First carrier (Example Freight)
            router.get(f"{SEARCH_BASE}/search", params__contains={"dotNumber": "1234567"}).mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json=authorities_sample)
            )
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json=insurances_active)
            )
            # Second carrier (Sample Logistics)
            router.get(f"{SEARCH_BASE}/search", params__contains={"dotNumber": "7654321"}).mock(
                return_value=httpx.Response(200, json=carrier_secondary)
            )
            router.get("/company/7654321/authorities").mock(
                return_value=httpx.Response(200, json=authorities_sample)
            )
            router.get("/company/7654321/insurances").mock(
                return_value=httpx.Response(200, json=insurances_active)
            )
            result = await _generate_compare({"dot_numbers": ["1234567", "7654321"]}, fake_api_key)

        for key in ("report", "carrier_count", "carriers", "_pipeline"):
            assert key in result, f"Missing key: {key}"

    async def test_side_by_side_and_risk_summary_sections(
        self,
        fake_api_key,
        carrier_primary,
        carrier_secondary,
        authorities_sample,
        insurances_active,
    ):
        """Report contains Side-by-Side and Risk Summary sections."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search", params__contains={"dotNumber": "1234567"}).mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json=authorities_sample)
            )
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json=insurances_active)
            )
            router.get(f"{SEARCH_BASE}/search", params__contains={"dotNumber": "7654321"}).mock(
                return_value=httpx.Response(200, json=carrier_secondary)
            )
            router.get("/company/7654321/authorities").mock(
                return_value=httpx.Response(200, json=authorities_sample)
            )
            router.get("/company/7654321/insurances").mock(
                return_value=httpx.Response(200, json=insurances_active)
            )
            result = await _generate_compare({"dot_numbers": ["1234567", "7654321"]}, fake_api_key)

        assert "Side-by-Side" in result["report"]
        assert "Risk Summary" in result["report"]

    async def test_carrier_count_matches(
        self,
        fake_api_key,
        carrier_primary,
        carrier_secondary,
        authorities_sample,
        insurances_active,
    ):
        """carrier_count matches number of DOTs provided."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search", params__contains={"dotNumber": "1234567"}).mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json=authorities_sample)
            )
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json=insurances_active)
            )
            router.get(f"{SEARCH_BASE}/search", params__contains={"dotNumber": "7654321"}).mock(
                return_value=httpx.Response(200, json=carrier_secondary)
            )
            router.get("/company/7654321/authorities").mock(
                return_value=httpx.Response(200, json=authorities_sample)
            )
            router.get("/company/7654321/insurances").mock(
                return_value=httpx.Response(200, json=insurances_active)
            )
            result = await _generate_compare({"dot_numbers": ["1234567", "7654321"]}, fake_api_key)

        assert result["carrier_count"] == 2


# ---------------------------------------------------------------------------
# _export_data
# ---------------------------------------------------------------------------


class TestExportData:
    """Tests for the export_data handler."""

    async def test_json_valid(self, fake_api_key, carrier_primary):
        """JSON format produces valid JSON in the data field."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/equipment").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            result = await _export_data({"dot_number": "1234567", "format": "json"}, fake_api_key)

        assert result["format"] == "json"
        # data field should be valid JSON
        parsed = json.loads(result["data"])
        assert isinstance(parsed, dict)

    async def test_csv_has_headers(self, fake_api_key, carrier_primary):
        """CSV format contains curated column headers."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/equipment").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            result = await _export_data({"dot_number": "1234567", "format": "csv"}, fake_api_key)

        assert result["format"] == "csv"
        assert "DOT Number" in result["data"]
        assert "Legal Name" in result["data"]

    async def test_markdown_starts_with_heading(self, fake_api_key, carrier_primary):
        """Markdown format starts with a heading."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/equipment").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            result = await _export_data(
                {"dot_number": "1234567", "format": "markdown"}, fake_api_key
            )

        assert result["format"] == "markdown"
        assert result["data"].startswith("# ")

    async def test_sections_filter(self, fake_api_key, carrier_primary):
        """Sections filter limits which data is fetched."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            result = await _export_data(
                {"dot_number": "1234567", "format": "json", "sections": ["basics"]},
                fake_api_key,
            )

        assert result["sections"] == ["basics"]
        parsed = json.loads(result["data"])
        assert "basics" in parsed

    async def test_invalid_format_defaults(self, fake_api_key, carrier_primary):
        """Invalid format string defaults to 'json'."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/equipment").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            result = await _export_data({"dot_number": "1234567", "format": "pdf"}, fake_api_key)

        assert result["format"] == "json"
