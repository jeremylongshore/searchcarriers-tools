#!/usr/bin/env python3
"""SearchCarriers Watchdog MCP Server.

STANDALONE monitoring plugin (not part of the stackable pipeline):
  Watchdog monitors carriers on a watch list and routes alerts to external channels.

Four tools:
  - manage_watchlist  : add / remove / list watched carriers
  - get_alerts        : compatibility response explaining alert API availability
  - route_alert       : format an alert as a channel-ready payload (Slack, Telegram, email, webhook)
  - monitor_compliance: check a carrier against federal compliance standards

All four tools require proplus tier.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Path setup: make the shared utilities importable regardless of cwd.
# ---------------------------------------------------------------------------
_PLUGIN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

# ---------------------------------------------------------------------------
# MCP SDK
# ---------------------------------------------------------------------------
from mcp.server import Server  # noqa: E402
from mcp.server.stdio import stdio_server  # noqa: E402
from mcp.types import TextContent, Tool  # noqa: E402

from plugins.shared.api_contract import (  # noqa: E402  # gitleaks:allow -- symbol names
    API_V3_BASE,
    normalize_v3_company,
)
from plugins.shared.tier_gate import TierError, check_tier  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
API_BASE = "https://searchcarriers.com/api/v1"
SEARCH_BASE = API_V3_BASE
REQUEST_TIMEOUT = 20.0  # seconds
VERSION = "0.3.0"

# Federal insurance minimums (USD)
INSURANCE_MIN_GENERAL = 750_000
INSURANCE_MIN_HAZMAT = 5_000_000

# MCS-150 filing freshness threshold
MCS150_MAX_YEARS = 2.0

# Alert categories
ALERT_CATEGORIES = [
    "safety_change",
    "insurance_change",
    "authority_change",
    "mcs150_update",
    "status_change",
]

# ---------------------------------------------------------------------------
# Helpers — infrastructure
# ---------------------------------------------------------------------------


def _api_key() -> str:
    """Return the API key from the environment, raising on absence."""
    key = os.environ.get("SEARCHCARRIERS_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "SEARCHCARRIERS_API_KEY environment variable is not set. "
            "Set it before starting the MCP server."
        )
    return key


def _auth_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def _error_payload(code: str, message: str, detail: Any = None) -> dict[str, Any]:
    """Build a structured error envelope returned as tool output."""
    payload: dict[str, Any] = {"error": {"code": code, "message": message}}
    if detail is not None:
        payload["error"]["detail"] = detail
    return payload


def _pipeline_meta(tool: str, dot_number: str = "") -> dict[str, Any]:
    """Build the standard ``_pipeline`` metadata block for all tool responses."""
    return {
        "source": "watchdog",
        "tool": tool,
        "version": VERSION,
        "dot_number": dot_number,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_date(value: str | None) -> datetime | None:
    """Parse an ISO-8601 or simple date string to a timezone-aware datetime."""
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _years_since(dt: datetime | None) -> float | None:
    """Return fractional years elapsed since a datetime, or None."""
    if dt is None:
        return None
    return (_now_utc() - dt).days / 365.25


async def _get(
    client: httpx.AsyncClient,
    url: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a GET request and return a parsed JSON dict.

    All HTTP-level and network errors are caught and re-raised as plain
    ``RuntimeError`` with a human-readable message so callers can wrap them
    into structured error payloads.
    """
    try:
        response = await client.get(url, params=params)
    except httpx.TimeoutException:
        raise RuntimeError(f"Request to {url} timed out after {REQUEST_TIMEOUT}s")
    except httpx.RequestError as exc:
        raise RuntimeError(f"Network error reaching {url}: {exc}")

    if response.status_code == 200:
        return response.json()

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "unknown")
        raise RuntimeError(f"Rate limit hit (429). Retry after {retry_after} seconds.")

    status_messages = {
        401: "Invalid or missing API key (401). Check SEARCHCARRIERS_API_KEY.",
        403: "Access forbidden (403). Your tier may not cover this endpoint.",
        404: "Resource not found (404).",
    }
    msg = status_messages.get(
        response.status_code,
        f"Unexpected API response: HTTP {response.status_code}",
    )
    raise RuntimeError(msg)


async def _post(
    client: httpx.AsyncClient,
    url: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    """Execute a POST request with a JSON body and return a parsed JSON dict."""
    try:
        response = await client.post(url, json=body)
    except httpx.TimeoutException:
        raise RuntimeError(f"POST to {url} timed out after {REQUEST_TIMEOUT}s")
    except httpx.RequestError as exc:
        raise RuntimeError(f"Network error reaching {url}: {exc}")

    if response.status_code in (200, 201):
        return response.json()

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "unknown")
        raise RuntimeError(f"Rate limit hit (429). Retry after {retry_after} seconds.")

    status_messages = {
        401: "Invalid or missing API key (401). Check SEARCHCARRIERS_API_KEY.",
        403: "Access forbidden (403). Your tier may not cover this endpoint.",
        404: "Resource not found (404).",
        409: "Conflict (409). Carrier may already be on the watch list.",
    }
    msg = status_messages.get(
        response.status_code,
        f"Unexpected API response: HTTP {response.status_code}",
    )
    raise RuntimeError(msg)


async def _delete(
    client: httpx.AsyncClient,
    url: str,
) -> bool:
    """Execute a DELETE request; return True on 200/204."""
    try:
        response = await client.delete(url)
    except httpx.TimeoutException:
        raise RuntimeError(f"DELETE to {url} timed out after {REQUEST_TIMEOUT}s")
    except httpx.RequestError as exc:
        raise RuntimeError(f"Network error reaching {url}: {exc}")

    if response.status_code in (200, 204):
        return True

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "unknown")
        raise RuntimeError(f"Rate limit hit (429). Retry after {retry_after} seconds.")

    status_messages = {
        401: "Invalid or missing API key (401). Check SEARCHCARRIERS_API_KEY.",
        403: "Access forbidden (403). Your tier may not cover this endpoint.",
        404: "Watch list entry not found (404).",
    }
    msg = status_messages.get(
        response.status_code,
        f"Unexpected API response: HTTP {response.status_code}",
    )
    raise RuntimeError(msg)


# ---------------------------------------------------------------------------
# Helpers — data extraction
# ---------------------------------------------------------------------------


def _extract_list(data: Any) -> list[dict[str, Any]]:
    """Unwrap an API response to a list of records."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "results", "items", "carriers", "watchlist"):
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


def _extract_carrier(data: Any) -> dict[str, Any]:
    """Unwrap common API envelope shapes to get the first carrier record."""
    if isinstance(data, list):
        return data[0] if data else {}
    if isinstance(data, dict):
        for key in ("data", "results", "items"):
            if key in data and isinstance(data[key], list):
                items = data[key]
                return items[0] if items else {}
    return data if isinstance(data, dict) else {}


def _carrier_name(carrier: dict[str, Any]) -> str:
    """Return the best available display name for a carrier."""
    return (
        carrier.get("legalName")
        or carrier.get("legal_name")
        or carrier.get("name")
        or "Unknown Carrier"
    )


def _watchlist_entry_name(entry: dict[str, Any]) -> str:
    """Extract a display name from a watch list entry."""
    return (
        entry.get("carrierName")
        or entry.get("carrier_name")
        or entry.get("legalName")
        or entry.get("name")
        or "Unknown Carrier"
    )


def _watchlist_entry_dot(entry: dict[str, Any]) -> str:
    """Extract the DOT number from a watch list entry."""
    return str(entry.get("dotNumber") or entry.get("dot_number") or entry.get("dot") or "")


def _categorize_alert(alert: dict[str, Any]) -> str:
    """Map an alert record to one of the known category strings."""
    alert_type = str(
        alert.get("alertType")
        or alert.get("alert_type")
        or alert.get("type")
        or alert.get("changeType")
        or alert.get("change_type")
        or ""
    ).lower()

    mapping: dict[str, str] = {
        "safety": "safety_change",
        "insurance": "insurance_change",
        "authority": "authority_change",
        "mcs150": "mcs150_update",
        "mcs-150": "mcs150_update",
        "status": "status_change",
    }
    for keyword, category in mapping.items():
        if keyword in alert_type:
            return category
    # Default: infer from field presence.
    if any(k in alert for k in ("safetyRating", "safety_rating", "oos_rate")):
        return "safety_change"
    if any(k in alert for k in ("insuranceAmount", "insurance_amount", "policyNumber")):
        return "insurance_change"
    if any(k in alert for k in ("authority", "operatingAuthority")):
        return "authority_change"
    if any(k in alert for k in ("mcs150", "mcs_150", "biennial")):
        return "mcs150_update"
    return "status_change"


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def _manage_watchlist(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Add, remove, or list watched carriers.

    SearchCarriers v1 exposes a collection GET and a company-scoped GET/POST.
    Removal is expressed by syncing an empty ``watch_types`` list; there is no
    documented DELETE endpoint.
    """
    action: str = str(arguments.get("action", "")).strip().lower()
    dot_number: str = str(arguments.get("dot_number", "")).strip()

    if action not in ("add", "remove", "list"):
        return _error_payload(
            "invalid_action",
            f"action must be 'add', 'remove', or 'list'; got '{action}'.",
        )
    if action in ("add", "remove") and not dot_number:
        return _error_payload(
            "missing_parameter",
            f"dot_number is required for action='{action}'.",
        )

    watch_types = arguments.get("watch_types") or ["all"]
    watchlist_url = f"{API_BASE}/company/watch"
    company_watch_url = f"{API_BASE}/company/{dot_number}/watch"

    async with httpx.AsyncClient(headers=_auth_headers(api_key), timeout=REQUEST_TIMEOUT) as client:
        if action == "list":
            try:
                raw = await _get(client, watchlist_url)
            except RuntimeError as exc:
                return _error_payload("api_error", str(exc))

            entries = _extract_list(raw)
            carriers_out = [
                {
                    "id": e.get("id"),
                    "dot_number": _watchlist_entry_dot(e),
                    "carrier_name": _watchlist_entry_name(e),
                }
                for e in entries
            ]
            return {
                "action": "list",
                "dot_number": "",
                "carrier_name": "",
                "watchlist_count": len(carriers_out),
                "result": "listed",
                "carriers": carriers_out,
                "_pipeline": _pipeline_meta("manage_watchlist"),
            }

        if action == "add":
            try:
                result = await _post(client, company_watch_url, {"watch_types": watch_types})
            except RuntimeError as exc:
                return _error_payload("api_error", str(exc))

            # Fetch current count and carrier name from result or a follow-up GET.
            carrier_name = (
                result.get("carrierName")
                or result.get("carrier_name")
                or result.get("legalName")
                or ""
            )
            # Best-effort watchlist count.
            try:
                raw_list = await _get(client, watchlist_url)
                count = len(_extract_list(raw_list))
            except RuntimeError:
                count = -1

            return {
                "action": "add",
                "dot_number": dot_number,
                "carrier_name": carrier_name,
                "watchlist_count": count,
                "result": "added",
                "carriers": [],
                "_pipeline": _pipeline_meta("manage_watchlist", dot_number),
            }

        # action == "remove": synchronize the company to zero watch types.
        try:
            result = await _post(client, company_watch_url, {"watch_types": []})
        except RuntimeError as exc:
            return _error_payload("api_error", str(exc))

        carrier_name = (
            result.get("carrierName") or result.get("carrier_name") or result.get("legalName") or ""
        )
        try:
            remaining = len(_extract_list(await _get(client, watchlist_url)))
        except RuntimeError:
            remaining = -1
        return {
            "action": "remove",
            "dot_number": dot_number,
            "carrier_name": carrier_name,
            "watchlist_count": remaining,
            "result": "removed",
            "carriers": [],
            "_pipeline": _pipeline_meta("manage_watchlist", dot_number),
        }


async def _get_alerts(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Return a truthful compatibility error for the removed assumed route."""
    del arguments, api_key
    return _error_payload(
        "endpoint_unavailable",
        "SearchCarriers' published API does not expose an alert-feed endpoint. "
        "Use manage_watchlist to configure watches, then consume notifications "
        "through the delivery channel configured in SearchCarriers.",
        {
            "deprecated_assumption": "/api/v1/carrier-watch/alerts",
            "documented_routes": [
                "GET /api/v1/company/watch",
                "GET /api/v1/company/{dotNumber}/watch",
                "POST /api/v1/company/{dotNumber}/watch",
            ],
        },
    )


def _format_slack(alert: dict[str, Any], destination: str) -> dict[str, Any]:
    """Return a Slack Block Kit JSON payload ready to POST to a webhook."""
    category = alert.get("_category") or _categorize_alert(alert)
    dot = str(alert.get("dotNumber") or alert.get("dot_number") or "N/A")
    carrier = str(alert.get("carrierName") or alert.get("carrier_name") or "Unknown Carrier")
    summary = str(
        alert.get("summary")
        or alert.get("message")
        or alert.get("description")
        or "Alert details not available."
    )
    ts = str(alert.get("timestamp") or alert.get("created_at") or alert.get("alertDate") or "")
    severity = str(alert.get("severity") or "info").lower()

    # Pick an emoji based on severity/category.
    emoji_map = {
        "critical": ":red_circle:",
        "warning": ":large_yellow_circle:",
        "info": ":large_blue_circle:",
    }
    emoji = emoji_map.get(severity, ":large_blue_circle:")

    return {
        "username": "SearchCarriers Watchdog",
        "icon_emoji": ":truck:",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Carrier Alert: {category.replace('_', ' ').title()}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Carrier:*\n{carrier}"},
                    {"type": "mrkdwn", "text": f"*DOT:*\n{dot}"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Category:*\n{category.replace('_', ' ').title()}",
                    },
                    {"type": "mrkdwn", "text": f"*Severity:*\n{severity.capitalize()}"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Details:*\n{summary}"},
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Timestamp: {ts}" if ts else "SearchCarriers Watchdog",
                    },
                ],
            },
        ],
    }


def _format_telegram(alert: dict[str, Any], destination: str) -> dict[str, Any]:
    """Return a Telegram sendMessage body with Markdown formatting."""
    category = alert.get("_category") or _categorize_alert(alert)
    dot = str(alert.get("dotNumber") or alert.get("dot_number") or "N/A")
    carrier = str(alert.get("carrierName") or alert.get("carrier_name") or "Unknown Carrier")
    summary = str(
        alert.get("summary")
        or alert.get("message")
        or alert.get("description")
        or "Alert details not available."
    )
    ts = str(alert.get("timestamp") or alert.get("created_at") or alert.get("alertDate") or "")
    severity = str(alert.get("severity") or "info").lower()

    severity_prefix = {"critical": "CRITICAL", "warning": "WARNING", "info": "INFO"}.get(
        severity, "INFO"
    )

    lines = [
        f"*[{severity_prefix}] Carrier Alert*",
        "",
        f"*Carrier:* {carrier}",
        f"*DOT:* {dot}",
        f"*Type:* {category.replace('_', ' ').title()}",
        f"*Severity:* {severity.capitalize()}",
        "",
        f"*Details:* {summary}",
    ]
    if ts:
        lines += ["", f"_Timestamp: {ts}_"]

    return {
        "chat_id": destination,
        "text": "\n".join(lines),
        "parse_mode": "Markdown",
    }


def _format_email(alert: dict[str, Any], destination: str) -> dict[str, Any]:
    """Return a structured email payload with subject and HTML body."""
    category = alert.get("_category") or _categorize_alert(alert)
    dot = str(alert.get("dotNumber") or alert.get("dot_number") or "N/A")
    carrier = str(alert.get("carrierName") or alert.get("carrier_name") or "Unknown Carrier")
    summary = str(
        alert.get("summary")
        or alert.get("message")
        or alert.get("description")
        or "Alert details not available."
    )
    ts = str(alert.get("timestamp") or alert.get("created_at") or alert.get("alertDate") or "")
    severity = str(alert.get("severity") or "info").lower()

    subject = f"[SearchCarriers Watchdog] {severity.upper()}: {carrier} (DOT {dot}) — {category.replace('_', ' ').title()}"

    color_map = {"critical": "#d93025", "warning": "#f4a522", "info": "#1a73e8"}
    color = color_map.get(severity, "#1a73e8")

    html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background-color: {color}; padding: 16px; border-radius: 4px 4px 0 0;">
    <h2 style="color: white; margin: 0;">Carrier Alert: {category.replace("_", " ").title()}</h2>
  </div>
  <div style="border: 1px solid #e0e0e0; border-top: none; padding: 16px; border-radius: 0 0 4px 4px;">
    <table style="width: 100%; border-collapse: collapse;">
      <tr><td style="padding: 6px; font-weight: bold; width: 120px;">Carrier</td><td style="padding: 6px;">{carrier}</td></tr>
      <tr style="background: #f8f8f8;"><td style="padding: 6px; font-weight: bold;">DOT Number</td><td style="padding: 6px;">{dot}</td></tr>
      <tr><td style="padding: 6px; font-weight: bold;">Alert Type</td><td style="padding: 6px;">{category.replace("_", " ").title()}</td></tr>
      <tr style="background: #f8f8f8;"><td style="padding: 6px; font-weight: bold;">Severity</td><td style="padding: 6px;">{severity.capitalize()}</td></tr>
    </table>
    <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 16px 0;">
    <p><strong>Details:</strong><br>{summary}</p>
    {"<p style='color: #757575; font-size: 12px;'>Timestamp: " + ts + "</p>" if ts else ""}
    <p style="color: #757575; font-size: 12px; margin-top: 24px;">
      This alert was generated by SearchCarriers Watchdog. Manage your watch list at
      <a href="https://searchcarriers.com">searchcarriers.com</a>.
    </p>
  </div>
</body>
</html>"""

    return {
        "to": destination,
        "subject": subject,
        "html_body": html_body,
        "text_body": (
            f"{subject}\n\n"
            f"Carrier: {carrier}\n"
            f"DOT: {dot}\n"
            f"Alert Type: {category.replace('_', ' ').title()}\n"
            f"Severity: {severity.capitalize()}\n\n"
            f"Details: {summary}\n" + (f"\nTimestamp: {ts}\n" if ts else "")
        ),
    }


def _format_webhook(alert: dict[str, Any], destination: str) -> dict[str, Any]:
    """Return a generic JSON POST body for webhook delivery."""
    category = alert.get("_category") or _categorize_alert(alert)
    dot = str(alert.get("dotNumber") or alert.get("dot_number") or "N/A")
    carrier = str(alert.get("carrierName") or alert.get("carrier_name") or "Unknown Carrier")
    summary = str(alert.get("summary") or alert.get("message") or alert.get("description") or "")
    ts = str(alert.get("timestamp") or alert.get("created_at") or alert.get("alertDate") or "")
    severity = str(alert.get("severity") or "info").lower()

    return {
        "event": "carrier_alert",
        "source": "searchcarriers-watchdog",
        "version": VERSION,
        "timestamp": ts or _now_utc().isoformat(),
        "alert": {
            "category": category,
            "severity": severity,
            "dot_number": dot,
            "carrier_name": carrier,
            "summary": summary,
            "raw": alert,
        },
    }


async def _route_alert(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Format an alert as a channel-ready payload.

    Supported channels: slack, telegram, email, webhook.
    This tool FORMATS the payload only — it does not transmit.
    """
    alert: dict[str, Any] = arguments.get("alert") or {}
    channel: str = str(arguments.get("channel", "")).strip().lower()
    destination: str = str(arguments.get("destination", "")).strip()

    if not alert:
        return _error_payload("missing_parameter", "'alert' dict is required.")
    if channel not in ("slack", "telegram", "email", "webhook"):
        return _error_payload(
            "invalid_channel",
            f"channel must be 'slack', 'telegram', 'email', or 'webhook'; got '{channel}'.",
        )
    if not destination:
        return _error_payload("missing_parameter", "'destination' is required.")

    formatters = {
        "slack": _format_slack,
        "telegram": _format_telegram,
        "email": _format_email,
        "webhook": _format_webhook,
    }
    formatted_payload = formatters[channel](alert, destination)

    # Build a short human-readable preview.
    dot = str(alert.get("dotNumber") or alert.get("dot_number") or "N/A")
    carrier = str(alert.get("carrierName") or alert.get("carrier_name") or "Unknown Carrier")
    category = alert.get("_category") or _categorize_alert(alert)
    severity = str(alert.get("severity") or "info").lower()
    preview = (
        f"[{severity.upper()}] {carrier} (DOT {dot}) — "
        f"{category.replace('_', ' ').title()} alert formatted for {channel}."
    )

    return {
        "channel": channel,
        "formatted_payload": formatted_payload,
        "destination": destination,
        "preview": preview,
        "_pipeline": _pipeline_meta("route_alert", dot),
    }


async def _monitor_compliance(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Check a carrier against federal compliance standards.

    Fetches carrier basics, authorities, and insurances in parallel.
    Returns a compliance_status of 'compliant', 'drift', or 'critical'
    along with itemized checks and a drift_items list.
    """
    dot: str = str(arguments.get("dot_number", "")).strip()
    if not dot:
        return _error_payload("missing_parameter", "dot_number is required.")

    search_url = f"{SEARCH_BASE}/search"

    async with httpx.AsyncClient(headers=_auth_headers(api_key), timeout=REQUEST_TIMEOUT) as client:
        search_task = _get(client, search_url, params={"dotNumber": dot, "perPage": 1})
        authorities_task = _get(client, f"{API_BASE}/company/{dot}/authorities")
        insurances_task = _get(client, f"{API_BASE}/company/{dot}/insurances")

        search_result, authorities_result, insurances_result = await asyncio.gather(
            search_task, authorities_task, insurances_task, return_exceptions=True
        )

    # Surface any hard API failures.
    if isinstance(search_result, Exception):
        return _error_payload("api_error", f"Carrier lookup failed: {search_result}")
    if isinstance(authorities_result, Exception):
        authorities_result = {}  # Non-fatal; we check below.
    if isinstance(insurances_result, Exception):
        insurances_result = {}  # Non-fatal; we check below.

    carrier = normalize_v3_company(_extract_carrier(search_result))
    carrier_name = _carrier_name(carrier)

    authorities_list = _extract_list(authorities_result)
    insurances_list = _extract_list(insurances_result)

    # -----------------------------------------------------------------------
    # Run compliance checks
    # -----------------------------------------------------------------------
    checks: list[dict[str, Any]] = []
    drift_items: list[str] = []

    def _check(
        name: str,
        passed: bool,
        severity: str,
        message_pass: str,
        message_fail: str,
    ) -> None:
        status = "pass" if passed else "fail"
        checks.append(
            {
                "check": name,
                "status": status,
                "severity": severity,
                "message": message_pass if passed else message_fail,
            }
        )
        if not passed:
            drift_items.append(message_fail)

    # 1. Operating authority active.
    active_authorities = [
        a
        for a in authorities_list
        if str(a.get("status") or a.get("authorityStatus") or "").lower()
        in ("active", "authorized")
    ]
    has_active_authority = len(active_authorities) > 0
    _check(
        "operating_authority_active",
        has_active_authority,
        "critical",
        f"Operating authority is active ({len(active_authorities)} active authority/ies).",
        "No active operating authority found — carrier may not be authorized to operate.",
    )

    # 2. No revoked authorities.
    revoked_authorities = [
        a
        for a in authorities_list
        if str(a.get("status") or a.get("authorityStatus") or "").lower()
        in ("revoked", "inactive", "revocated")
    ]
    has_revoked = len(revoked_authorities) > 0
    _check(
        "no_revoked_authorities",
        not has_revoked,
        "critical",
        "No revoked authorities on record.",
        f"{len(revoked_authorities)} revoked authority/ies found.",
    )

    # 3. No Unsatisfactory safety rating.
    safety_rating = str(
        carrier.get("safetyRating") or carrier.get("safety_rating") or carrier.get("rating") or ""
    ).lower()
    is_unsatisfactory = safety_rating in ("unsatisfactory", "unsat", "u")
    _check(
        "safety_rating_not_unsatisfactory",
        not is_unsatisfactory,
        "critical",
        f"Safety rating is '{safety_rating or 'not rated'}' — not Unsatisfactory.",
        "Safety rating is Unsatisfactory — carrier has a critical safety deficiency.",
    )

    # 4. Insurance coverage — general freight minimum ($750k).
    general_policies = [
        p
        for p in insurances_list
        if str(p.get("insuranceType") or p.get("insurance_type") or p.get("type") or "").lower()
        not in ("hazmat", "hm-126")
    ]
    max_general_coverage = max(
        (
            float(p.get("insuranceAmount") or p.get("amount") or p.get("coverage") or 0)
            for p in general_policies
        ),
        default=0.0,
    )
    meets_general_minimum = max_general_coverage >= INSURANCE_MIN_GENERAL
    _check(
        "insurance_general_freight_minimum",
        meets_general_minimum,
        "critical",
        f"General freight insurance meets federal minimum (${max_general_coverage:,.0f} >= ${INSURANCE_MIN_GENERAL:,}).",
        f"General freight insurance below federal minimum of ${INSURANCE_MIN_GENERAL:,} "
        f"(found: ${max_general_coverage:,.0f}).",
    )

    # 5. Insurance coverage — hazmat minimum ($5M) — only if carrier hauls hazmat.
    hazmat_policies = [
        p
        for p in insurances_list
        if str(p.get("insuranceType") or p.get("insurance_type") or p.get("type") or "").lower()
        in ("hazmat", "hm-126", "hazardous")
    ]
    if hazmat_policies:
        max_hazmat_coverage = max(
            (
                float(p.get("insuranceAmount") or p.get("amount") or p.get("coverage") or 0)
                for p in hazmat_policies
            ),
            default=0.0,
        )
        meets_hazmat_minimum = max_hazmat_coverage >= INSURANCE_MIN_HAZMAT
        _check(
            "insurance_hazmat_minimum",
            meets_hazmat_minimum,
            "critical",
            f"Hazmat insurance meets federal minimum (${max_hazmat_coverage:,.0f} >= ${INSURANCE_MIN_HAZMAT:,}).",
            f"Hazmat insurance below federal minimum of ${INSURANCE_MIN_HAZMAT:,} "
            f"(found: ${max_hazmat_coverage:,.0f}).",
        )

    # 6. MCS-150 filed within 2 years.
    mcs150_date_raw = (
        carrier.get("mcs150Date")
        or carrier.get("mcs_150_date")
        or carrier.get("lastFilingDate")
        or carrier.get("biennial_date")
    )
    mcs150_dt = _parse_date(str(mcs150_date_raw)) if mcs150_date_raw else None
    years_since_mcs150 = _years_since(mcs150_dt)

    if years_since_mcs150 is None:
        _check(
            "mcs150_filed_within_2_years",
            False,
            "drift",
            "MCS-150 filing date is current.",
            "MCS-150 filing date unavailable — cannot verify compliance.",
        )
    else:
        mcs150_current = years_since_mcs150 <= MCS150_MAX_YEARS
        years_str = f"{years_since_mcs150:.1f}"
        _check(
            "mcs150_filed_within_2_years",
            mcs150_current,
            "drift",
            f"MCS-150 filed {years_str} years ago — within the 2-year requirement.",
            f"MCS-150 filed {years_str} years ago — exceeds the 2-year filing requirement.",
        )

    # -----------------------------------------------------------------------
    # Determine overall compliance status.
    # -----------------------------------------------------------------------
    failed_checks = [c for c in checks if c["status"] == "fail"]
    critical_failures = [c for c in failed_checks if c["severity"] == "critical"]
    drift_failures = [c for c in failed_checks if c["severity"] == "drift"]

    if critical_failures:
        compliance_status = "critical"
    elif drift_failures:
        compliance_status = "drift"
    else:
        compliance_status = "compliant"

    return {
        "dot_number": dot,
        "carrier_name": carrier_name,
        "compliance_status": compliance_status,
        "checks": checks,
        "drift_items": drift_items,
        "last_checked": _now_utc().isoformat(),
        "_pipeline": _pipeline_meta("monitor_compliance", dot),
    }


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

_TOOL_DEFINITIONS: list[Tool] = [
    Tool(
        name="manage_watchlist",
        description=(
            "Add, remove, or list carriers on the SearchCarriers watch list. "
            "Use action='add' with a DOT number to start monitoring a carrier, "
            "action='remove' to stop monitoring, or action='list' to see all "
            "currently watched carriers. Min tier: proplus."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "remove", "list"],
                    "description": "The watch list operation to perform.",
                },
                "dot_number": {
                    "type": "string",
                    "description": (
                        "The carrier's USDOT number. Required for action='add' and action='remove'."
                    ),
                },
                "watch_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Watch categories to synchronize when adding. Defaults "
                        "to ['all']; examples include details and inspections."
                    ),
                },
            },
            "required": ["action"],
        },
    ),
    Tool(
        name="get_alerts",
        description=(
            "Compatibility tool for older clients. The published SearchCarriers "
            "API does not expose an alert-feed route, so this returns a structured "
            "endpoint_unavailable response with the documented watch routes. "
            "Min tier: proplus."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "dot_number": {
                    "type": "string",
                    "description": "Filter alerts to a single carrier DOT number.",
                },
                "since": {
                    "type": "string",
                    "description": "ISO 8601 date string; only return alerts after this timestamp.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of alerts to return (default: 50).",
                    "default": 50,
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="route_alert",
        description=(
            "Format a carrier alert as a channel-ready payload for Slack, Telegram, "
            "email, or a generic webhook. Returns the fully structured payload — "
            "the caller is responsible for transmitting it. "
            "Slack output uses Block Kit JSON; Telegram uses sendMessage with "
            "parse_mode=Markdown; email includes subject + HTML body; webhook "
            "returns a generic JSON envelope. Min tier: proplus."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "alert": {
                    "type": "object",
                    "description": "The alert dict to format (as returned by get_alerts).",
                },
                "channel": {
                    "type": "string",
                    "enum": ["slack", "telegram", "email", "webhook"],
                    "description": "Target delivery channel.",
                },
                "destination": {
                    "type": "string",
                    "description": (
                        "Channel-specific destination: Slack webhook URL, "
                        "Telegram chat_id, email address, or webhook URL."
                    ),
                },
            },
            "required": ["alert", "channel", "destination"],
        },
    ),
    Tool(
        name="monitor_compliance",
        description=(
            "Run a federal compliance check on a carrier by DOT number. "
            "Fetches carrier basics, authorities, and insurance data in parallel "
            "and evaluates against federal minimums: active operating authority, "
            "no revoked authorities, no Unsatisfactory safety rating, "
            "general freight insurance >= $750k, hazmat insurance >= $5M (if applicable), "
            "and MCS-150 filing within 2 years. "
            "Returns compliance_status: 'compliant', 'drift', or 'critical'. "
            "Min tier: proplus."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "dot_number": {
                    "type": "string",
                    "description": "The carrier's USDOT number.",
                },
            },
            "required": ["dot_number"],
        },
    ),
]

# Map tool names to their implementation coroutines.
_TOOL_HANDLERS = {
    "manage_watchlist": _manage_watchlist,
    "get_alerts": _get_alerts,
    "route_alert": _route_alert,
    "monitor_compliance": _monitor_compliance,
}


async def serve() -> None:
    """Entry point: create the MCP server and run it over stdio."""
    try:
        api_key = _api_key()
    except RuntimeError as exc:
        print(f"[watchdog] Startup error: {exc}", file=sys.stderr)
        sys.exit(1)

    user_tier = os.environ.get("SEARCHCARRIERS_TIER", "free").strip().lower()

    server = Server("searchcarriers-watchdog")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return _TOOL_DEFINITIONS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        # Tier gate — returns a structured error payload on failure.
        try:
            check_tier(name, user_tier)
        except TierError as exc:
            result = _error_payload(
                "tier_insufficient",
                str(exc),
                {
                    "tool": exc.tool,
                    "required_tier": exc.required,
                    "current_tier": exc.current,
                    "upgrade_url": "https://searchcarriers.com/pricing",
                },
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        handler = _TOOL_HANDLERS.get(name)
        if handler is None:
            result = _error_payload("unknown_tool", f"No handler registered for tool '{name}'.")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        try:
            result = await handler(arguments, api_key)
        except Exception as exc:  # Final safety net — should not reach here.
            result = _error_payload("internal_error", f"Unexpected error: {exc}")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(serve())
