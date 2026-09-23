"""Contract tests for the current carrier-intel API routes."""

import sys
from pathlib import Path

import httpx
import respx

_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root))
sys.path.insert(0, str(_repo_root / "plugins" / "searchcarriers-carrier-intel" / "scripts"))

from carrier_intel_mcp import (  # noqa: E402
    API_V1_BASE,
    API_V3_BASE,
    _carrier_lookup,
    _carrier_profile,
    _entity_map,
    _fleet_summary,
)
from conftest import assert_error_payload  # noqa: E402


def _v3_company(dot: str = "1234567") -> dict:
    return {
        "data": {
            "dot_number": dot,
            "legal_name": "EXAMPLE FREIGHT LLC",
            "dot_status": "ACTIVE",
            "power_units": 12,
            "contact": {"phone": "5550100000", "email_address": "ops@example.invalid"},
            "safety": {"total_inspections": 8, "total_crashes": 0},
            "authorities": [],
            "insurance": [],
            "operation": {"entity_types": ["CARRIER"]},
            "risk_factors": [],
            "vetting_report": {"status": "review"},
        }
    }


class TestCarrierLookup:
    async def test_dot_uses_v3_contract(self, fake_api_key):
        with respx.mock(assert_all_called=True) as router:
            route = router.get(f"{API_V3_BASE}/search").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            result = await _carrier_lookup(
                {"query": "1234567", "state": "tx", "per_page": 25}, fake_api_key
            )

        params = route.calls[0].request.url.params
        assert params["dotNumber"] == "1234567"
        assert params["addressState"] == "TX"
        assert params["perPage"] == "25"
        assert result["api_version"] == "v3"
        assert result["search_type_used"] == "dot"

    async def test_mc_uses_docket_number(self, fake_api_key):
        with respx.mock(assert_all_called=True) as router:
            route = router.get(f"{API_V3_BASE}/search").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            await _carrier_lookup({"query": "MC765432"}, fake_api_key)

        assert route.calls[0].request.url.params["docketNumber"] == "765432"
        assert "mcNumber" not in route.calls[0].request.url.params

    async def test_name_uses_super_search_term(self, fake_api_key):
        with respx.mock(assert_all_called=True) as router:
            route = router.get(f"{API_V3_BASE}/search").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            await _carrier_lookup({"query": "Example Freight", "search_type": "name"}, fake_api_key)

        assert route.calls[0].request.url.params["superSearchTerm"] == "Example Freight"

    async def test_filter_only_lane_and_insurance_search_uses_v3_contract(self, fake_api_key):
        with respx.mock(assert_all_called=True) as router:
            route = router.get(f"{API_V3_BASE}/search").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            result = await _carrier_lookup(
                {
                    "min_power_units": 5,
                    "min_bipd_coverage": 1_000_000,
                    "lane_origin_state": "AL",
                    "lane_destination_state": "TX",
                    "include_equipment_types": ["VAN"],
                },
                fake_api_key,
            )

        params = route.calls[0].request.url.params
        assert params["minPowerUnits"] == "5"
        assert params["minBipdCoverage"] == "1000000"
        assert params["laneOriginState"] == "AL"
        assert params["laneDestinationState"] == "TX"
        assert params.get_list("includeEquipmentTypes[]") == ["VAN"]
        assert result["search_type_used"] == "filters"

    async def test_empty_filter_search_is_rejected_without_api_call(self, fake_api_key):
        result = await _carrier_lookup({}, fake_api_key)
        assert_error_payload(result, "invalid_request")

    async def test_vin_uses_dedicated_v1_path(self, fake_api_key):
        vin = "1M8GDM9AXKP042788"
        with respx.mock(assert_all_called=True) as router:
            route = router.get(f"{API_V1_BASE}/search/by-vin/{vin}").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            result = await _carrier_lookup({"query": vin}, fake_api_key)

        assert route.called
        assert result["api_version"] == "v1"
        assert result["search_type_used"] == "vin"

    async def test_scac_uses_dedicated_v1_path(self, fake_api_key):
        with respx.mock(assert_all_called=True) as router:
            route = router.get(f"{API_V1_BASE}/search/scac", params={"scac": "EXMP"}).mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            result = await _carrier_lookup({"query": "EXMP"}, fake_api_key)

        assert route.called
        assert result["api_version"] == "v1"

    async def test_api_error_is_structured(self, fake_api_key):
        with respx.mock(assert_all_called=True) as router:
            router.get(f"{API_V3_BASE}/search").mock(
                return_value=httpx.Response(401, json={"error": "unauthorized"})
            )
            result = await _carrier_lookup({"query": "1234567"}, fake_api_key)

        assert_error_payload(result, "api_error")


class TestCarrierProfile:
    async def test_profile_is_one_v3_field_selected_request(self, fake_api_key):
        with respx.mock(assert_all_called=True) as router:
            route = router.get(f"{API_V3_BASE}/company/1234567").mock(
                return_value=httpx.Response(200, json=_v3_company())
            )
            result = await _carrier_profile({"dot_number": " 1234567 "}, fake_api_key)

        assert route.call_count == 1
        assert "fields" in route.calls[0].request.url.params
        assert result["api_version"] == "v3"
        assert result["carrier"]["legalName"] == "EXAMPLE FREIGHT LLC"
        assert result["dot_number"] == "1234567"

    async def test_contract_drift_is_visible(self, fake_api_key):
        with respx.mock(assert_all_called=True) as router:
            router.get(f"{API_V3_BASE}/company/1234567").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            result = await _carrier_profile({"dot_number": "1234567"}, fake_api_key)

        assert_error_payload(result, "api_error")


class TestEntityMap:
    async def test_no_vins_returns_empty_related(self, fake_api_key):
        with respx.mock(assert_all_called=True) as router:
            router.get(f"{API_V3_BASE}/company/1234567").mock(
                return_value=httpx.Response(200, json=_v3_company())
            )
            router.get(f"{API_V3_BASE}/company/1234567/equipment").mock(
                return_value=httpx.Response(200, json={"data": [{"make": "Example"}]})
            )
            result = await _entity_map({"dot_number": "1234567"}, fake_api_key)

        assert result["related_carriers"] == []

    async def test_vin_relationship_uses_v1_path(self, fake_api_key):
        vin = "1M8GDM9AXKP042788"
        with respx.mock(assert_all_called=True) as router:
            router.get(f"{API_V3_BASE}/company/1234567").mock(
                return_value=httpx.Response(200, json=_v3_company())
            )
            router.get(f"{API_V3_BASE}/company/1234567/equipment").mock(
                return_value=httpx.Response(200, json={"data": [{"vin": vin}]})
            )
            vin_route = router.get(f"{API_V1_BASE}/search/by-vin/{vin}").mock(
                return_value=httpx.Response(
                    200,
                    json={"data": [{"dotNumber": "7654321", "legalName": "RELATED LLC"}]},
                )
            )
            result = await _entity_map({"dot_number": "1234567"}, fake_api_key)

        assert vin_route.called
        assert result["related_carriers"][0]["dot"] == "7654321"


class TestFleetSummary:
    async def test_fleet_uses_v3_equipment(self, fake_api_key):
        with respx.mock(assert_all_called=True) as router:
            route = router.get(f"{API_V3_BASE}/company/1234567/equipment").mock(
                return_value=httpx.Response(
                    200,
                    json={"data": [{"equipment_type": "TRACTOR"}, {"type": "TRAILER"}]},
                )
            )
            result = await _fleet_summary({"dot_number": "1234567"}, fake_api_key)

        assert route.called
        assert result["api_version"] == "v3"
        assert result["summary"] == {
            "total_equipment": 2,
            "types": {"TRACTOR": 1, "TRAILER": 1},
        }
