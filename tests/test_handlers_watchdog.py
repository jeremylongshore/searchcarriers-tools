"""Integration tests for watchdog_mcp handler functions.

Tests exercise the actual handler logic with respx intercepting HTTP calls
at the transport layer. No real API calls are made.
"""

import sys
from pathlib import Path

import httpx
import pytest
import respx

_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root))
sys.path.insert(
    0,
    str(_repo_root / "plugins" / "searchcarriers-watchdog" / "scripts"),
)

from conftest import assert_error_payload  # noqa: E402
from watchdog_mcp import (  # noqa: E402
    API_BASE,
    SEARCH_BASE,
    _categorize_alert,
    _delete,
    _extract_carrier,
    _extract_list,
    _get,
    _get_alerts,
    _manage_watchlist,
    _monitor_compliance,
    _post,
    _route_alert,
)


class TestTransportAndShapeHelpers:
    """Error semantics must distinguish access, absence, throttling, and drift."""

    async def test_get_maps_known_http_failures(self):
        messages = {
            401: "Invalid or missing API key",
            403: "Access forbidden",
            404: "Resource not found",
            500: "Unexpected API response",
        }
        for status, message in messages.items():
            with respx.mock() as router:
                router.get("https://example.test/value").mock(
                    return_value=httpx.Response(status, json={})
                )
                async with httpx.AsyncClient() as client:
                    with pytest.raises(RuntimeError, match=message):
                        await _get(client, "https://example.test/value")

    async def test_get_post_delete_preserve_retry_after(self):
        with respx.mock() as router:
            router.get("https://example.test/value").mock(
                return_value=httpx.Response(429, headers={"Retry-After": "7"})
            )
            router.post("https://example.test/value").mock(
                return_value=httpx.Response(429, headers={"Retry-After": "8"})
            )
            router.delete("https://example.test/value").mock(
                return_value=httpx.Response(429, headers={"Retry-After": "9"})
            )
            async with httpx.AsyncClient() as client:
                with pytest.raises(RuntimeError, match="7 seconds"):
                    await _get(client, "https://example.test/value")
                with pytest.raises(RuntimeError, match="8 seconds"):
                    await _post(client, "https://example.test/value", {})
                with pytest.raises(RuntimeError, match="9 seconds"):
                    await _delete(client, "https://example.test/value")

    async def test_post_and_delete_success(self):
        with respx.mock() as router:
            router.post("https://example.test/value").mock(
                return_value=httpx.Response(201, json={"ok": True})
            )
            router.delete("https://example.test/value").mock(return_value=httpx.Response(204))
            async with httpx.AsyncClient() as client:
                assert await _post(client, "https://example.test/value", {}) == {"ok": True}
                assert await _delete(client, "https://example.test/value") is True

    def test_extractors_accept_supported_envelopes(self):
        record = {"dotNumber": "1234567"}
        for key in ("data", "results", "items", "carriers", "watchlist"):
            assert _extract_list({key: [record]}) == [record]
        assert _extract_list([record]) == [record]
        assert _extract_list("invalid") == []
        assert _extract_carrier({"results": [record]}) == record
        assert _extract_carrier([]) == {}

    @pytest.mark.parametrize(
        ("alert", "category"),
        [
            ({"alertType": "safety-rating"}, "safety_change"),
            ({"type": "insurance-cancelled"}, "insurance_change"),
            ({"changeType": "authority-revoked"}, "authority_change"),
            ({"type": "mcs-150-filed"}, "mcs150_update"),
            ({"policyNumber": "P-1"}, "insurance_change"),
            ({"biennial": "2026-01-01"}, "mcs150_update"),
            ({}, "status_change"),
        ],
    )
    def test_alert_category_is_deterministic(self, alert, category):
        assert _categorize_alert(alert) == category


# ---------------------------------------------------------------------------
# _manage_watchlist
# ---------------------------------------------------------------------------


class TestManageWatchlist:
    """Tests for the manage_watchlist handler."""

    async def test_invalid_action_error(self, fake_api_key):
        """Invalid action returns structured error."""
        result = await _manage_watchlist({"action": "invalid"}, fake_api_key)
        assert_error_payload(result, "invalid_action")

    async def test_list_returns_carriers(self, fake_api_key):
        """action=list returns carrier list."""
        watchlist_data = {
            "data": [
                {
                    "id": "w1",
                    "dotNumber": "1234567",
                    "carrierName": "EXAMPLE FREIGHT LLC",
                }
            ]
        }
        with respx.mock(base_url=API_BASE) as router:
            router.get("/company/watch").mock(return_value=httpx.Response(200, json=watchlist_data))
            result = await _manage_watchlist({"action": "list"}, fake_api_key)

        assert result["action"] == "list"
        assert result["result"] == "listed"
        assert result["watchlist_count"] == 1
        assert len(result["carriers"]) == 1

    async def test_add_missing_dot_error(self, fake_api_key):
        """action=add without dot_number returns error."""
        result = await _manage_watchlist({"action": "add"}, fake_api_key)
        assert_error_payload(result, "missing_parameter")

    async def test_add_returns_added(self, fake_api_key):
        """action=add with dot_number returns 'added' result."""
        with respx.mock(base_url=API_BASE) as router:
            post_route = router.post("/company/1234567/watch").mock(
                return_value=httpx.Response(
                    201,
                    json={"carrierName": "EXAMPLE FREIGHT LLC", "dotNumber": "1234567"},
                )
            )
            # Follow-up GET for count
            router.get("/company/watch").mock(
                return_value=httpx.Response(
                    200,
                    json={"data": [{"id": "w1", "dotNumber": "1234567"}]},
                )
            )
            result = await _manage_watchlist(
                {"action": "add", "dot_number": "1234567"}, fake_api_key
            )

        assert result["action"] == "add"
        assert result["result"] == "added"
        assert result["dot_number"] == "1234567"
        assert post_route.calls[0].request.read() == b'{"watch_types":["all"]}'

    async def test_required_keys(self, fake_api_key):
        """List response has all required keys."""
        with respx.mock(base_url=API_BASE) as router:
            router.get("/company/watch").mock(return_value=httpx.Response(200, json={"data": []}))
            result = await _manage_watchlist({"action": "list"}, fake_api_key)

        for key in ("action", "watchlist_count", "result", "carriers", "_pipeline"):
            assert key in result, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# _get_alerts
# ---------------------------------------------------------------------------


class TestGetAlerts:
    """The old assumed alerts route now fails truthfully without an HTTP call."""

    async def test_returns_endpoint_unavailable(self, fake_api_key):
        result = await _get_alerts({}, fake_api_key)

        assert_error_payload(result, "endpoint_unavailable")
        assert "/api/v1/carrier-watch/alerts" in str(result)


class TestRouteAlert:
    """Routing formats channel payloads but deliberately does not transmit them."""

    ALERT = {
        "dotNumber": "1234567",
        "carrierName": "EXAMPLE FREIGHT LLC",
        "type": "insurance_cancelled",
        "severity": "critical",
        "summary": "Cargo policy cancelled",
        "timestamp": "2026-09-23T12:00:00Z",
    }

    async def test_formats_each_supported_channel(self, fake_api_key):
        cases = {
            "slack": "blocks",
            "telegram": "chat_id",
            "email": "subject",
            "webhook": "event",
        }
        for channel, expected_key in cases.items():
            result = await _route_alert(
                {
                    "alert": self.ALERT,
                    "channel": channel,
                    "destination": "ops@example.test",
                },
                fake_api_key,
            )
            assert expected_key in result["formatted_payload"]
            assert result["channel"] == channel
            assert "formatted" in result["preview"]

    async def test_requires_alert_channel_and_destination(self, fake_api_key):
        missing_alert = await _route_alert(
            {"channel": "email", "destination": "ops@example.test"}, fake_api_key
        )
        bad_channel = await _route_alert(
            {"alert": self.ALERT, "channel": "sms", "destination": "+15555550100"},
            fake_api_key,
        )
        missing_destination = await _route_alert(
            {"alert": self.ALERT, "channel": "email"}, fake_api_key
        )
        assert_error_payload(missing_alert, "missing_parameter")
        assert_error_payload(bad_channel, "invalid_channel")
        assert_error_payload(missing_destination, "missing_parameter")


# ---------------------------------------------------------------------------
# _monitor_compliance
# ---------------------------------------------------------------------------


class TestMonitorCompliance:
    """Tests for the monitor_compliance handler."""

    async def test_returns_compliance_structure(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Returns compliance structure with checks list."""
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
            result = await _monitor_compliance({"dot_number": "1234567"}, fake_api_key)

        for key in ("dot_number", "compliance_status", "checks", "drift_items", "_pipeline"):
            assert key in result, f"Missing key: {key}"

        assert result["compliance_status"] in ("compliant", "drift", "critical")
        assert isinstance(result["checks"], list)
        assert len(result["checks"]) >= 4  # At least 4 checks always run

        # Each check has required fields
        for check in result["checks"]:
            assert "check" in check
            assert "status" in check
            assert check["status"] in ("pass", "fail")
            assert "message" in check
