"""Integration tests for api_bridge_mcp handler functions.

Tests exercise the actual handler logic with respx intercepting HTTP calls
at the transport layer. No real API calls are made.

Note: api_bridge's _get() returns (json, response) tuples, and _probe_endpoint
bypasses _get entirely — it uses client.get() directly.
"""

import sys
from pathlib import Path

import httpx
import respx

_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root))
sys.path.insert(
    0,
    str(_repo_root / "plugins" / "searchcarriers-api-bridge" / "scripts"),
)

from api_bridge_mcp import (  # noqa: E402
    API_BASE,
    HEALTH_ENDPOINTS,
    SEARCH_BASE,
    _api_health,
    _bulk_lookup,
    _tms_sync,
    _webhook_manage,
)
from conftest import assert_error_payload  # noqa: E402

# ---------------------------------------------------------------------------
# _api_health
# ---------------------------------------------------------------------------


class TestApiHealth:
    """Tests for the api_health handler."""

    async def test_all_healthy(self, fake_api_key):
        """All endpoints returning 200 produces 'healthy' overall status."""
        with respx.mock() as router:
            for ep in HEALTH_ENDPOINTS:
                router.get(ep["url"]).mock(
                    return_value=httpx.Response(
                        200,
                        json={},
                        headers={
                            "X-RateLimit-Remaining": "100",
                            "X-RateLimit-Limit": "180",
                        },
                    )
                )
            result = await _api_health({}, fake_api_key)

        assert result["status"] == "healthy"
        assert len(result["endpoints"]) == len(HEALTH_ENDPOINTS)

    async def test_endpoint_record_structure(self, fake_api_key):
        """Each endpoint record has the expected fields."""
        with respx.mock() as router:
            for ep in HEALTH_ENDPOINTS:
                router.get(ep["url"]).mock(return_value=httpx.Response(200, json={}))
            result = await _api_health({}, fake_api_key)

        for ep in result["endpoints"]:
            for key in ("name", "url", "status", "health", "response_ms", "rate_limit"):
                assert key in ep, f"Endpoint {ep.get('name', '?')} missing key: {key}"

    async def test_partial_outage_degraded(self, fake_api_key):
        """Mix of healthy and down endpoints produces 'degraded' overall."""
        with respx.mock() as router:
            for i, ep in enumerate(HEALTH_ENDPOINTS):
                if i == 0:
                    # First endpoint is down
                    router.get(ep["url"]).mock(return_value=httpx.Response(500, json={}))
                else:
                    router.get(ep["url"]).mock(return_value=httpx.Response(200, json={}))
            result = await _api_health({}, fake_api_key)

        assert result["status"] == "degraded"

    async def test_all_down(self, fake_api_key):
        """All endpoints returning 500 produces 'down' overall."""
        with respx.mock() as router:
            for ep in HEALTH_ENDPOINTS:
                router.get(ep["url"]).mock(return_value=httpx.Response(500, json={}))
            result = await _api_health({}, fake_api_key)

        assert result["status"] == "down"

    async def test_filter_by_name(self, fake_api_key):
        """Filtering by endpoint name restricts the probe."""
        with respx.mock() as router:
            search_endpoint = next(e for e in HEALTH_ENDPOINTS if e["name"] == "v3_search")
            router.get(search_endpoint["url"]).mock(return_value=httpx.Response(200, json={}))
            result = await _api_health({"endpoints": ["v3_search"]}, fake_api_key)

        assert len(result["endpoints"]) == 1
        assert result["endpoints"][0]["name"] == "v3_search"

    async def test_pipeline_meta(self, fake_api_key):
        """_pipeline metadata is present and correct."""
        with respx.mock() as router:
            for ep in HEALTH_ENDPOINTS:
                router.get(ep["url"]).mock(return_value=httpx.Response(200, json={}))
            result = await _api_health({}, fake_api_key)

        assert result["_pipeline"]["source"] == "api-bridge"
        assert result["_pipeline"]["tool"] == "api_health"


# ---------------------------------------------------------------------------
# _bulk_lookup
# ---------------------------------------------------------------------------


class TestBulkLookup:
    """Tests for the bulk_lookup handler."""

    async def test_empty_dots_error(self, fake_api_key):
        """Empty dot_numbers list returns error."""
        result = await _bulk_lookup({"dot_numbers": []}, fake_api_key)
        assert_error_payload(result, "missing_parameter")

    async def test_exceeds_max_error(self, fake_api_key):
        """More than 100 DOTs returns error."""
        dots = [str(i) for i in range(101)]
        result = await _bulk_lookup({"dot_numbers": dots}, fake_api_key)
        assert_error_payload(result, "too_many_dot_numbers")

    async def test_single_dot_results(self, fake_api_key, carrier_primary):
        """Single DOT lookup returns correct structure."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            result = await _bulk_lookup({"dot_numbers": ["1234567"]}, fake_api_key)

        assert result["total"] == 1
        assert result["succeeded"] == 1
        assert result["failed"] == 0
        assert len(result["results"]) == 1
        assert result["results"][0]["dot_number"] == "1234567"
        assert result["results"][0]["success"] is True

    async def test_sections_filter(self, fake_api_key, carrier_primary, authorities_sample):
        """Include filter restricts which sections are fetched."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json=authorities_sample)
            )
            result = await _bulk_lookup(
                {"dot_numbers": ["1234567"], "include": ["basics", "authorities"]},
                fake_api_key,
            )

        assert result["succeeded"] == 1
        data = result["results"][0]["data"]
        assert "basics" in data
        assert "authorities" in data


class TestTmsSync:
    """Behavioral coverage for TMS import and export boundaries."""

    async def test_import_reverse_maps_generic_record_without_http(self, fake_api_key):
        result = await _tms_sync(
            {
                "dot_number": "1234567",
                "direction": "import",
                "tms_format": "generic",
                "tms_record": {
                    "carrier_dot": "1234567",
                    "carrier_name": "EXAMPLE FREIGHT LLC",
                    "private_note": "keep local",
                },
            },
            fake_api_key,
        )

        assert result["carrier_data"]["dot_number"] == "1234567"
        assert result["carrier_data"]["legal_name"] == "EXAMPLE FREIGHT LLC"
        assert result["unmapped_fields"] == ["private_note"]

    async def test_import_requires_record(self, fake_api_key):
        result = await _tms_sync({"dot_number": "1234567", "direction": "import"}, fake_api_key)
        assert_error_payload(result, "missing_parameter")

    async def test_rejects_unknown_direction_and_format(self, fake_api_key):
        invalid_direction = await _tms_sync(
            {"dot_number": "1234567", "direction": "merge"}, fake_api_key
        )
        invalid_format = await _tms_sync(
            {
                "dot_number": "1234567",
                "direction": "export",
                "tms_format": "unknown",
            },
            fake_api_key,
        )
        assert_error_payload(invalid_direction, "invalid_direction")
        assert_error_payload(invalid_format, "invalid_tms_format")

    async def test_generic_export_fetches_and_maps_live_shape(
        self,
        fake_api_key,
        carrier_primary,
        authorities_sample,
        insurances_active,
        equipment_sample,
    ):
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json=authorities_sample)
            )
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json=insurances_active)
            )
            router.get("/company/1234567/equipment").mock(
                return_value=httpx.Response(200, json=equipment_sample)
            )
            result = await _tms_sync(
                {
                    "dot_number": "1234567",
                    "direction": "export",
                    "tms_format": "generic",
                },
                fake_api_key,
            )

        assert result["direction"] == "export"
        assert result["carrier_data"]["carrier_dot"] == "1234567"
        assert result["_pipeline"]["tool"] == "tms_sync"


class TestWebhookManage:
    """The webhook tool manages local configuration and never claims delivery."""

    async def test_create_list_update_delete_round_trip(self, fake_api_key, tmp_path, monkeypatch):
        import api_bridge_mcp

        config_path = tmp_path / "webhooks.json"
        monkeypatch.setattr(api_bridge_mcp, "WEBHOOK_CONFIG_PATH", config_path)

        created = await _webhook_manage(
            {
                "action": "create",
                "webhook_url": "https://example.test/carrier-events",
                "events": ["insurance.cancelled"],
            },
            fake_api_key,
        )
        webhook_id = created["webhook"]["id"]
        assert created["webhooks_total"] == 1
        assert config_path.is_file()

        listed = await _webhook_manage({"action": "list"}, fake_api_key)
        assert [item["id"] for item in listed["webhooks"]] == [webhook_id]

        updated = await _webhook_manage(
            {
                "action": "update",
                "webhook_id": webhook_id,
                "events": ["authority.changed"],
            },
            fake_api_key,
        )
        assert updated["webhook"]["events"] == ["authority.changed"]

        deleted = await _webhook_manage(
            {"action": "delete", "webhook_id": webhook_id}, fake_api_key
        )
        assert deleted["webhooks_total"] == 0

    async def test_rejects_invalid_action_url_and_unknown_id(
        self, fake_api_key, tmp_path, monkeypatch
    ):
        import api_bridge_mcp

        monkeypatch.setattr(api_bridge_mcp, "WEBHOOK_CONFIG_PATH", tmp_path / "webhooks.json")
        invalid_action = await _webhook_manage({"action": "send"}, fake_api_key)
        invalid_url = await _webhook_manage(
            {"action": "create", "webhook_url": "ftp://example.test/hook"}, fake_api_key
        )
        unknown_id = await _webhook_manage(
            {"action": "delete", "webhook_id": "missing"}, fake_api_key
        )
        assert_error_payload(invalid_action, "invalid_action")
        assert_error_payload(invalid_url, "invalid_url")
        assert_error_payload(unknown_id, "not_found")
