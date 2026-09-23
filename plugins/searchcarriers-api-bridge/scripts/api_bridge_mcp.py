#!/usr/bin/env python3
"""SearchCarriers API Bridge MCP Server.

STANDALONE integration plugin (not part of the stackable pipeline):
  API Bridge handles API management, bulk carrier operations, and TMS sync.

Four tools:
  - api_health      : probe each API endpoint for status, latency, and rate-limit headroom
  - bulk_lookup     : fetch one or more data sections for up to 100 DOT numbers in parallel
  - tms_sync        : export carrier data formatted for a TMS, or map TMS records back to
                      SearchCarriers fields for verification
  - webhook_manage  : create/list/update/delete webhook registrations in local config

Tool tier requirements (from shared tier_gate):
  api_health=smb, bulk_lookup=smb, tms_sync=enterprise, webhook_manage=smb
"""

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
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

from plugins.shared.api_contract import (  # noqa: E402
    API_V1_BASE,
    API_V2_BASE,
    API_V3_BASE,
    normalize_v3_company,
)
from plugins.shared.tier_gate import TierError, check_tier  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
API_BASE = API_V1_BASE
SEARCH_BASE = API_V3_BASE
REQUEST_TIMEOUT = 20.0  # seconds
VERSION = "0.2.0"

BULK_BATCH_SIZE = 10
BULK_MAX_DOT_NUMBERS = 100

# Local webhook config path.
WEBHOOK_CONFIG_PATH = Path.home() / ".searchcarriers" / "webhooks.json"

# Endpoints probed by api_health.
# Company-scoped endpoints use DOT 1 as a probe target; a 404 is treated as healthy.
HEALTH_ENDPOINTS: list[dict[str, str]] = [
    {"name": "v3_search", "url": f"{API_V3_BASE}/search", "probe_params": "dotNumber=1"},
    {"name": "v3_company", "url": f"{API_V3_BASE}/company/1", "probe_params": ""},
    {"name": "v3_equipment", "url": f"{API_V3_BASE}/company/1/equipment", "probe_params": ""},
    {
        "name": "v2_qualification",
        "url": f"{API_V2_BASE}/company/1/qualification-reports",
        "probe_params": "",
    },
    {"name": "v1_watches", "url": f"{API_V1_BASE}/company/watch", "probe_params": ""},
]

# Supported data sections for bulk_lookup.
VALID_SECTIONS = {"basics", "authorities", "insurances", "equipment"}

# TMS format identifiers.
VALID_TMS_FORMATS = {"generic", "mcleod", "tms_international", "dat_power"}

# Generic TMS field mapping: SearchCarriers field -> generic TMS field.
GENERIC_FIELD_MAP: dict[str, str] = {
    "dotNumber": "carrier_dot",
    "dot_number": "carrier_dot",
    "mcNumber": "carrier_mc",
    "mc_number": "carrier_mc",
    "legalName": "carrier_name",
    "legal_name": "carrier_name",
    "dbaName": "carrier_dba",
    "dba_name": "carrier_dba",
    "address": "address_street",
    "city": "address_city",
    "state": "address_state",
    "zip": "address_zip",
    "phone": "phone",
    "email": "email",
    "safetyRating": "safety_rating",
    "safety_rating": "safety_rating",
    "operatingStatus": "operating_status",
    "operating_status": "operating_status",
    "entityType": "entity_type",
    "entity_type": "entity_type",
    "powerUnits": "power_units",
    "power_units": "power_units",
    "drivers": "driver_count",
    "mcs150Date": "mcs150_date",
    "mcs_150_date": "mcs150_date",
}

# TMS-specific field mapping guides (SearchCarriers field -> TMS field).
TMS_FIELD_GUIDES: dict[str, dict[str, str]] = {
    "mcleod": {
        "carrier_dot": "CARRIER_ID",
        "carrier_mc": "MC_NUM",
        "carrier_name": "NAME",
        "carrier_dba": "DBA_NAME",
        "address_street": "ADDRESS1",
        "address_city": "CITY",
        "address_state": "STATE",
        "address_zip": "ZIP",
        "phone": "PHONE",
        "safety_rating": "SAFETY_RATING",
        "operating_status": "STATUS",
        "power_units": "EQUIP_COUNT",
        "driver_count": "DRIVER_COUNT",
        "mcs150_date": "MCS150_DATE",
    },
    "tms_international": {
        "carrier_dot": "DotNumber",
        "carrier_mc": "McNumber",
        "carrier_name": "LegalName",
        "carrier_dba": "DbaName",
        "address_street": "StreetAddress",
        "address_city": "City",
        "address_state": "StateCode",
        "address_zip": "PostalCode",
        "phone": "PhoneNumber",
        "safety_rating": "SafetyRating",
        "operating_status": "OperatingStatus",
        "power_units": "NumberOfPowerUnits",
        "driver_count": "NumberOfDrivers",
        "mcs150_date": "Mcs150FormDate",
    },
    "dat_power": {
        "carrier_dot": "dot_num",
        "carrier_mc": "mc_num",
        "carrier_name": "legal_name",
        "carrier_dba": "dba_name",
        "address_street": "phys_addr",
        "address_city": "phys_city",
        "address_state": "phys_state",
        "address_zip": "phys_zip",
        "phone": "phone_num",
        "safety_rating": "safety_rtg",
        "operating_status": "op_status",
        "power_units": "pwr_units",
        "driver_count": "num_drivers",
        "mcs150_date": "mcs150_dt",
    },
}


# ---------------------------------------------------------------------------
# Infrastructure helpers
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


def _pipeline_meta(tool: str, context: str = "") -> dict[str, Any]:
    """Build the standard ``_pipeline`` metadata block for all tool responses."""
    return {
        "source": "api-bridge",
        "tool": tool,
        "version": VERSION,
        "context": context,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def _get(
    client: httpx.AsyncClient,
    url: str,
    params: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], httpx.Response]:
    """Execute a GET request and return (parsed_json, response).

    Raises RuntimeError with a human-readable message on HTTP errors,
    timeouts, and network failures.
    """
    try:
        response = await client.get(url, params=params)
    except httpx.TimeoutException:
        raise RuntimeError(f"Request to {url} timed out after {REQUEST_TIMEOUT}s")
    except httpx.RequestError as exc:
        raise RuntimeError(f"Network error reaching {url}: {exc}")

    if response.status_code == 200:
        return response.json(), response

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


def _extract_rate_limit(headers: httpx.Headers) -> dict[str, int | None]:
    """Parse X-RateLimit-* headers into a dict."""

    def _int_or_none(value: str | None) -> int | None:
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    return {
        "remaining": _int_or_none(headers.get("X-RateLimit-Remaining")),
        "limit": _int_or_none(headers.get("X-RateLimit-Limit")),
    }


def _extract_carrier(data: Any) -> dict[str, Any]:
    """Unwrap common API envelope shapes to the first carrier record."""
    if isinstance(data, list):
        return data[0] if data else {}
    if isinstance(data, dict):
        for key in ("data", "results", "items", "carriers"):
            if key in data and isinstance(data[key], list):
                items = data[key]
                return items[0] if items else {}
    return data if isinstance(data, dict) else {}


def _extract_list(data: Any) -> list[dict[str, Any]]:
    """Unwrap an API response to a list of records."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "results", "items", "carriers"):
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


# ---------------------------------------------------------------------------
# Tool: api_health
# ---------------------------------------------------------------------------


async def _probe_endpoint(
    client: httpx.AsyncClient,
    name: str,
    path: str,
    probe_params: str,
) -> dict[str, Any]:
    """Probe a single endpoint and return its health record."""
    full_url = path if path.startswith("https://") else f"{API_BASE}{path}"
    params: dict[str, str] = {}
    if probe_params:
        for pair in probe_params.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                params[k] = v

    start = time.monotonic()
    try:
        response = await client.get(full_url, params=params)
        elapsed_ms = round((time.monotonic() - start) * 1000)
        http_status = response.status_code
        rate_limit = _extract_rate_limit(response.headers)

        # Treat 200 and 404 (legitimate "not found" for probe DOT) as healthy.
        if http_status in (200, 404):
            endpoint_status = "healthy"
        elif http_status == 429:
            endpoint_status = "degraded"
        elif http_status >= 500:
            endpoint_status = "down"
        else:
            endpoint_status = "degraded"

    except httpx.TimeoutException:
        elapsed_ms = round(REQUEST_TIMEOUT * 1000)
        http_status = 0
        rate_limit = {"remaining": None, "limit": None}
        endpoint_status = "down"

    except httpx.RequestError:
        elapsed_ms = round((time.monotonic() - start) * 1000)
        http_status = 0
        rate_limit = {"remaining": None, "limit": None}
        endpoint_status = "down"

    return {
        "name": name,
        "url": path,
        "status": http_status,
        "health": endpoint_status,
        "response_ms": elapsed_ms,
        "rate_limit": rate_limit,
    }


async def _api_health(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Probe each SearchCarriers API endpoint for health, latency, and rate-limit headroom.

    Args:
        arguments: Tool input. Optional key ``endpoints`` is a list of endpoint
                   name strings to restrict the probe (default: all).
        api_key:   Bearer token for the SearchCarriers API.

    Returns:
        Structured health report with per-endpoint results and an overall status.
    """
    requested: list[str] = arguments.get("endpoints") or []

    if requested:
        unknown = [n for n in requested if n not in {e["name"] for e in HEALTH_ENDPOINTS}]
        if unknown:
            valid_names = [e["name"] for e in HEALTH_ENDPOINTS]
            return _error_payload(
                "unknown_endpoint",
                f"Unknown endpoint name(s): {unknown}. Valid names: {valid_names}.",
            )
        endpoints_to_probe = [e for e in HEALTH_ENDPOINTS if e["name"] in requested]
    else:
        endpoints_to_probe = HEALTH_ENDPOINTS

    async with httpx.AsyncClient(headers=_auth_headers(api_key), timeout=REQUEST_TIMEOUT) as client:
        tasks = [
            _probe_endpoint(client, ep["name"], ep["url"], ep["probe_params"])
            for ep in endpoints_to_probe
        ]
        results = await asyncio.gather(*tasks)

    # Determine aggregate status.
    statuses = {r["health"] for r in results}
    if "down" in statuses:
        overall = "down" if all(r["health"] == "down" for r in results) else "degraded"
    elif "degraded" in statuses:
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "status": overall,
        "endpoints": list(results),
        "checked_at": _now_utc().isoformat(),
        "_pipeline": _pipeline_meta("api_health"),
    }


# ---------------------------------------------------------------------------
# Tool: bulk_lookup
# ---------------------------------------------------------------------------


async def _fetch_section(
    client: httpx.AsyncClient,
    dot: str,
    section: str,
) -> tuple[str, dict[str, Any] | list[Any] | None, str | None]:
    """Fetch one data section for a single DOT number.

    Returns:
        (section, data_or_none, error_message_or_none)
    """
    if section == "basics":
        url = f"{API_V3_BASE}/search"
        params: dict[str, str] | None = {"dotNumber": dot, "perPage": "1"}
    else:
        section_path = {
            "authorities": "authorities",
            "insurances": "insurances",
            "equipment": "equipment",
        }[section]
        url = f"{API_BASE}/company/{dot}/{section_path}"
        params = None

    try:
        data, _ = await _get(client, url, params=params)
        if section == "basics":
            return section, normalize_v3_company(_extract_carrier(data)), None
        return section, _extract_list(data), None
    except RuntimeError as exc:
        return section, None, str(exc)


async def _lookup_single(
    client: httpx.AsyncClient,
    dot: str,
    sections: list[str],
) -> dict[str, Any]:
    """Fetch all requested sections for one DOT number concurrently."""
    tasks = [_fetch_section(client, dot, section) for section in sections]
    section_results = await asyncio.gather(*tasks, return_exceptions=True)

    carrier_data: dict[str, Any] = {}
    errors: list[str] = []

    for item in section_results:
        if isinstance(item, Exception):
            errors.append(str(item))
            continue
        section, data, error = item
        if error:
            errors.append(f"{section}: {error}")
        else:
            carrier_data[section] = data

    return {
        "dot_number": dot,
        "data": carrier_data,
        "errors": errors,
        "success": len(errors) == 0,
    }


async def _bulk_lookup(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Fetch one or more data sections for up to 100 DOT numbers in parallel batches.

    Args:
        arguments: Tool input containing ``dot_numbers`` (required, list[str], max 100)
                   and optional ``include`` (list of section names to fetch).
        api_key:   Bearer token for the SearchCarriers API.

    Returns:
        Aggregated results with per-DOT data, error counts, and processing time.
    """
    dot_numbers: list[str] = [str(d).strip() for d in (arguments.get("dot_numbers") or [])]
    include: list[str] = list(arguments.get("include") or ["basics"])

    if not dot_numbers:
        return _error_payload("missing_parameter", "dot_numbers is required and must not be empty.")
    if len(dot_numbers) > BULK_MAX_DOT_NUMBERS:
        return _error_payload(
            "too_many_dot_numbers",
            f"Maximum {BULK_MAX_DOT_NUMBERS} DOT numbers per request; received {len(dot_numbers)}.",
        )

    invalid_sections = [s for s in include if s not in VALID_SECTIONS]
    if invalid_sections:
        return _error_payload(
            "invalid_section",
            f"Unknown section(s): {invalid_sections}. Valid sections: {sorted(VALID_SECTIONS)}.",
        )

    start_time = time.monotonic()
    all_results: list[dict[str, Any]] = []
    all_errors: list[dict[str, str]] = []

    # Process in batches of BULK_BATCH_SIZE to respect API rate limits.
    async with httpx.AsyncClient(headers=_auth_headers(api_key), timeout=REQUEST_TIMEOUT) as client:
        for batch_start in range(0, len(dot_numbers), BULK_BATCH_SIZE):
            batch = dot_numbers[batch_start : batch_start + BULK_BATCH_SIZE]
            batch_tasks = [_lookup_single(client, dot, include) for dot in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for dot, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    all_errors.append({"dot_number": dot, "error": str(result)})
                elif result.get("success"):
                    all_results.append(result)
                else:
                    # Partial failures: still include the record, errors noted separately.
                    all_results.append(result)
                    for err in result.get("errors", []):
                        all_errors.append({"dot_number": dot, "error": err})

    processing_time = round(time.monotonic() - start_time, 3)
    succeeded = sum(1 for r in all_results if r.get("success"))
    failed = len(dot_numbers) - succeeded

    return {
        "total": len(dot_numbers),
        "succeeded": succeeded,
        "failed": failed,
        "results": all_results,
        "errors": all_errors,
        "processing_time_s": processing_time,
        "_pipeline": _pipeline_meta("bulk_lookup", f"{len(dot_numbers)} DOTs"),
    }


# ---------------------------------------------------------------------------
# Tool: tms_sync
# ---------------------------------------------------------------------------


def _build_generic_record(carrier: dict[str, Any]) -> dict[str, Any]:
    """Map raw carrier fields to the generic TMS schema using GENERIC_FIELD_MAP."""
    record: dict[str, Any] = {}
    mapped_source_keys: set[str] = set()

    for src_key, tms_key in GENERIC_FIELD_MAP.items():
        if src_key in carrier:
            # Prefer the first mapping that populates a given TMS key.
            if tms_key not in record:
                record[tms_key] = carrier[src_key]
            mapped_source_keys.add(src_key)

    return record


def _unmapped_fields(carrier: dict[str, Any]) -> list[str]:
    """Return carrier keys that have no entry in GENERIC_FIELD_MAP."""
    mapped_keys = set(GENERIC_FIELD_MAP.keys())
    return [k for k in carrier if k not in mapped_keys]


def _build_tms_specific_guide(tms_format: str) -> dict[str, str]:
    """Return the SearchCarriers -> TMS-specific field name mapping guide."""
    if tms_format == "generic":
        # For generic, the guide IS the generic field map (reversed perspective).
        return {sc: tms for sc, tms in GENERIC_FIELD_MAP.items()}
    guide = TMS_FIELD_GUIDES.get(tms_format, {})
    # Combine: SearchCarriers -> generic -> TMS-specific
    result: dict[str, str] = {}
    for sc_field, generic_field in GENERIC_FIELD_MAP.items():
        tms_field = guide.get(generic_field)
        if tms_field:
            result[sc_field] = tms_field
    return result


def _map_import_to_searchcarriers(tms_record: dict[str, Any], tms_format: str) -> dict[str, Any]:
    """Reverse-map a TMS carrier record to SearchCarriers field names."""
    if tms_format == "generic":
        # Reverse the generic map: generic TMS key -> SearchCarriers canonical key.
        reverse_map = {tms: sc for sc, tms in GENERIC_FIELD_MAP.items()}
    else:
        guide = TMS_FIELD_GUIDES.get(tms_format, {})
        # generic TMS key -> TMS-specific key (need to invert to TMS-specific -> generic -> SC).
        tms_to_generic = {v: k for k, v in guide.items()}
        generic_to_sc = {tms: sc for sc, tms in GENERIC_FIELD_MAP.items()}
        reverse_map = {
            tms_key: generic_to_sc[generic_key]
            for tms_key, generic_key in tms_to_generic.items()
            if generic_key in generic_to_sc
        }

    mapped: dict[str, Any] = {}
    unmapped: list[str] = []
    for field, value in tms_record.items():
        sc_field = reverse_map.get(field)
        if sc_field:
            mapped[sc_field] = value
        else:
            unmapped.append(field)

    return {"mapped": mapped, "unmapped": unmapped}


async def _tms_sync(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Export carrier data formatted for a TMS, or map TMS records back to SearchCarriers.

    Export direction: fetches carrier data from SearchCarriers API and formats it
    in the requested TMS schema. For ``generic`` format this produces a fully mapped
    record. For TMS-specific formats the tool returns the raw carrier data plus a
    field mapping guide showing how SearchCarriers fields correspond to that TMS's
    field names.

    Import direction: accepts a TMS carrier record, reverse-maps field names to
    SearchCarriers format, and returns the translated record for verification.

    Args:
        arguments: Tool input with ``dot_number``, ``direction``, and ``tms_format``.
        api_key:   Bearer token for the SearchCarriers API.

    Returns:
        Structured payload with direction, format, carrier data, and field mapping.
    """
    dot: str = str(arguments.get("dot_number", "")).strip()
    direction: str = str(arguments.get("direction", "")).strip().lower()
    tms_format: str = str(arguments.get("tms_format", "generic")).strip().lower()
    tms_record: dict[str, Any] = arguments.get("tms_record") or {}

    if not dot:
        return _error_payload("missing_parameter", "dot_number is required.")
    if direction not in ("export", "import"):
        return _error_payload(
            "invalid_direction",
            f"direction must be 'export' or 'import'; got '{direction}'.",
        )
    if tms_format not in VALID_TMS_FORMATS:
        return _error_payload(
            "invalid_tms_format",
            f"tms_format must be one of {sorted(VALID_TMS_FORMATS)}; got '{tms_format}'.",
        )

    if direction == "import":
        if not tms_record:
            return _error_payload(
                "missing_parameter",
                "tms_record is required for direction='import'.",
            )
        result = _map_import_to_searchcarriers(tms_record, tms_format)
        return {
            "direction": "import",
            "tms_format": tms_format,
            "dot_number": dot,
            "carrier_data": result["mapped"],
            "field_mapping": _build_tms_specific_guide(tms_format),
            "unmapped_fields": result["unmapped"],
            "_pipeline": _pipeline_meta("tms_sync", f"import:{dot}"),
        }

    # direction == "export": fetch carrier data from API.
    async with httpx.AsyncClient(headers=_auth_headers(api_key), timeout=REQUEST_TIMEOUT) as client:
        search_task = _get(
            client,
            f"{API_V3_BASE}/search",
            {"dotNumber": dot, "perPage": "1"},
        )
        authorities_task = _get(client, f"{API_BASE}/company/{dot}/authorities")
        insurances_task = _get(client, f"{API_BASE}/company/{dot}/insurances")
        equipment_task = _get(client, f"{API_BASE}/company/{dot}/equipment")

        raw_results = await asyncio.gather(
            search_task,
            authorities_task,
            insurances_task,
            equipment_task,
            return_exceptions=True,
        )

    search_data, auth_data, ins_data, equip_data = raw_results

    if isinstance(search_data, Exception):
        return _error_payload("api_error", f"Carrier lookup failed: {search_data}")

    carrier = normalize_v3_company(_extract_carrier(search_data[0]))

    # Merge authority / insurance / equipment summaries into carrier dict.
    if not isinstance(auth_data, Exception):
        auth_list = _extract_list(auth_data[0])
        carrier["_authorities"] = auth_list
        active = [
            a for a in auth_list if str(a.get("status") or "").lower() in ("active", "authorized")
        ]
        carrier["activeAuthorityCount"] = len(active)

    if not isinstance(ins_data, Exception):
        ins_list = _extract_list(ins_data[0])
        carrier["_insurances"] = ins_list
        carrier["insurancePolicyCount"] = len(ins_list)

    if not isinstance(equip_data, Exception):
        equip_list = _extract_list(equip_data[0])
        carrier["_equipment"] = equip_list
        carrier["equipmentCount"] = len(equip_list)

    field_mapping = _build_tms_specific_guide(tms_format)

    if tms_format == "generic":
        formatted_carrier = _build_generic_record(carrier)
        unmapped = _unmapped_fields(carrier)
    else:
        # For TMS-specific formats, map through generic -> TMS-specific.
        generic_record = _build_generic_record(carrier)
        guide = TMS_FIELD_GUIDES.get(tms_format, {})
        formatted_carrier = {guide.get(k, k): v for k, v in generic_record.items()}
        unmapped = _unmapped_fields(carrier)

    return {
        "direction": "export",
        "tms_format": tms_format,
        "dot_number": dot,
        "carrier_data": formatted_carrier,
        "field_mapping": field_mapping,
        "unmapped_fields": unmapped,
        "_pipeline": _pipeline_meta("tms_sync", f"export:{dot}"),
    }


# ---------------------------------------------------------------------------
# Tool: webhook_manage
# ---------------------------------------------------------------------------


def _load_webhook_config() -> dict[str, Any]:
    """Load the local webhook config, returning an empty structure if absent."""
    if WEBHOOK_CONFIG_PATH.exists():
        try:
            return json.loads(WEBHOOK_CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"webhooks": []}


def _save_webhook_config(config: dict[str, Any]) -> None:
    """Persist the local webhook config to disk, creating the directory if needed."""
    WEBHOOK_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    WEBHOOK_CONFIG_PATH.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _validate_webhook_url(url: str) -> str | None:
    """Return an error message if the webhook URL is not valid, else None."""
    url = url.strip()
    if not url:
        return "webhook_url must not be empty."
    if not (url.startswith("http://") or url.startswith("https://")):
        return "webhook_url must begin with http:// or https://."
    return None


async def _webhook_manage(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Create, list, update, or delete webhook registrations in local config.

    SearchCarriers does not yet expose webhook CRUD endpoints; registrations are
    maintained in ``~/.searchcarriers/webhooks.json`` for local management.

    Args:
        arguments: Tool input with ``action``, plus action-specific fields:
                   - create : ``webhook_url`` (required), ``events`` (optional)
                   - list   : no additional fields
                   - update : ``webhook_id`` (required), ``webhook_url``
                              and/or ``events`` (at least one required)
                   - delete : ``webhook_id`` (required)
        api_key:   Not used for local config operations; included for signature parity.

    Returns:
        Structured result with the affected webhook record and total count.
    """
    action: str = str(arguments.get("action", "")).strip().lower()
    webhook_url: str = str(arguments.get("webhook_url") or "").strip()
    webhook_id: str = str(arguments.get("webhook_id") or "").strip()
    events: list[str] = list(arguments.get("events") or [])

    if action not in ("create", "list", "update", "delete"):
        return _error_payload(
            "invalid_action",
            f"action must be 'create', 'list', 'update', or 'delete'; got '{action}'.",
        )

    config = _load_webhook_config()
    webhooks: list[dict[str, Any]] = config.get("webhooks", [])

    # ------------------------------------------------------------------
    # list
    # ------------------------------------------------------------------
    if action == "list":
        return {
            "action": "list",
            "webhook": None,
            "webhooks": webhooks,
            "webhooks_total": len(webhooks),
            "_pipeline": _pipeline_meta("webhook_manage", "list"),
        }

    # ------------------------------------------------------------------
    # create
    # ------------------------------------------------------------------
    if action == "create":
        url_error = _validate_webhook_url(webhook_url)
        if url_error:
            return _error_payload("invalid_url", url_error)

        new_webhook: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "url": webhook_url,
            "events": events,
            "created_at": _now_utc().isoformat(),
            "updated_at": _now_utc().isoformat(),
        }
        webhooks.append(new_webhook)
        config["webhooks"] = webhooks

        try:
            _save_webhook_config(config)
        except OSError as exc:
            return _error_payload("config_write_error", f"Failed to save webhook config: {exc}")

        return {
            "action": "create",
            "webhook": new_webhook,
            "webhooks_total": len(webhooks),
            "_pipeline": _pipeline_meta("webhook_manage", new_webhook["id"]),
        }

    # ------------------------------------------------------------------
    # update / delete — require webhook_id
    # ------------------------------------------------------------------
    if not webhook_id:
        return _error_payload(
            "missing_parameter",
            f"webhook_id is required for action='{action}'.",
        )

    target_idx = next(
        (i for i, w in enumerate(webhooks) if w.get("id") == webhook_id),
        None,
    )
    if target_idx is None:
        return _error_payload(
            "not_found",
            f"No webhook found with id '{webhook_id}'.",
        )

    # ------------------------------------------------------------------
    # update
    # ------------------------------------------------------------------
    if action == "update":
        if not webhook_url and not events:
            return _error_payload(
                "missing_parameter",
                "At least one of webhook_url or events must be provided for action='update'.",
            )
        if webhook_url:
            url_error = _validate_webhook_url(webhook_url)
            if url_error:
                return _error_payload("invalid_url", url_error)
            webhooks[target_idx]["url"] = webhook_url
        if events:
            webhooks[target_idx]["events"] = events

        webhooks[target_idx]["updated_at"] = _now_utc().isoformat()
        config["webhooks"] = webhooks

        try:
            _save_webhook_config(config)
        except OSError as exc:
            return _error_payload("config_write_error", f"Failed to save webhook config: {exc}")

        return {
            "action": "update",
            "webhook": webhooks[target_idx],
            "webhooks_total": len(webhooks),
            "_pipeline": _pipeline_meta("webhook_manage", webhook_id),
        }

    # ------------------------------------------------------------------
    # delete
    # ------------------------------------------------------------------
    deleted = webhooks.pop(target_idx)
    config["webhooks"] = webhooks

    try:
        _save_webhook_config(config)
    except OSError as exc:
        return _error_payload("config_write_error", f"Failed to save webhook config: {exc}")

    return {
        "action": "delete",
        "webhook": deleted,
        "webhooks_total": len(webhooks),
        "_pipeline": _pipeline_meta("webhook_manage", webhook_id),
    }


# ---------------------------------------------------------------------------
# MCP Server — tool definitions and dispatch
# ---------------------------------------------------------------------------

_TOOL_DEFINITIONS: list[Tool] = [
    Tool(
        name="api_health",
        description=(
            "Probe SearchCarriers API endpoints to check availability, response time, "
            "and rate-limit headroom. Returns a per-endpoint health report and an "
            "aggregate status of 'healthy', 'degraded', or 'down'. "
            "Optionally restrict the probe to specific endpoint names. "
            "Min tier: smb."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "endpoints": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Optional list of endpoint names to check. "
                        "Valid names: search, authorities, insurances, equipment, "
                        "carrier_watch, alerts. Defaults to all endpoints."
                    ),
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="bulk_lookup",
        description=(
            "Fetch carrier data for up to 100 DOT numbers in a single call. "
            "Specify which data sections to include: 'basics' (carrier profile), "
            "'authorities', 'insurances', and/or 'equipment'. "
            "Processes in batches of 10 with concurrent requests. "
            "Returns per-DOT results, error details, and total processing time. "
            "Min tier: smb."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "dot_numbers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of USDOT numbers to look up (max 100).",
                },
                "include": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["basics", "authorities", "insurances", "equipment"],
                    },
                    "description": ("Data sections to fetch for each DOT. Defaults to ['basics']."),
                    "default": ["basics"],
                },
            },
            "required": ["dot_numbers"],
        },
    ),
    Tool(
        name="tms_sync",
        description=(
            "Synchronize carrier data between SearchCarriers and a TMS. "
            "export: fetches carrier data from SearchCarriers and formats it in "
            "the target TMS schema. "
            "import: accepts a TMS carrier record and reverse-maps fields back "
            "to SearchCarriers format for verification. "
            "Supported TMS formats: generic, mcleod, tms_international, dat_power. "
            "Min tier: enterprise."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "dot_number": {
                    "type": "string",
                    "description": "The carrier's USDOT number.",
                },
                "direction": {
                    "type": "string",
                    "enum": ["export", "import"],
                    "description": (
                        "export: SearchCarriers -> TMS format. "
                        "import: TMS record -> SearchCarriers fields."
                    ),
                },
                "tms_format": {
                    "type": "string",
                    "enum": ["generic", "mcleod", "tms_international", "dat_power"],
                    "description": "Target TMS schema. Defaults to 'generic'.",
                    "default": "generic",
                },
                "tms_record": {
                    "type": "object",
                    "description": (
                        "TMS carrier record to map back to SearchCarriers fields. "
                        "Required when direction='import'."
                    ),
                },
            },
            "required": ["dot_number", "direction"],
        },
    ),
    Tool(
        name="webhook_manage",
        description=(
            "Manage webhook registrations stored in a local config file at "
            "~/.searchcarriers/webhooks.json. "
            "create: register a new webhook URL (with optional event filter). "
            "list: return all registered webhooks. "
            "update: change the URL and/or events for an existing webhook by id. "
            "delete: remove a webhook registration by id. "
            "Min tier: smb."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "list", "update", "delete"],
                    "description": "The webhook management operation to perform.",
                },
                "webhook_url": {
                    "type": "string",
                    "description": "The webhook endpoint URL. Required for create; optional for update.",
                },
                "webhook_id": {
                    "type": "string",
                    "description": "The webhook id (UUID). Required for update and delete.",
                },
                "events": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Event types to subscribe to (e.g. 'authority_change', "
                        "'insurance_change'). Omit to subscribe to all events."
                    ),
                },
            },
            "required": ["action"],
        },
    ),
]

_TOOL_HANDLERS = {
    "api_health": _api_health,
    "bulk_lookup": _bulk_lookup,
    "tms_sync": _tms_sync,
    "webhook_manage": _webhook_manage,
}


async def serve() -> None:
    """Entry point: create the MCP server and run it over stdio."""
    try:
        api_key = _api_key()
    except RuntimeError as exc:
        print(f"[api-bridge] Startup error: {exc}", file=sys.stderr)
        sys.exit(1)

    user_tier = os.environ.get("SEARCHCARRIERS_TIER", "free").strip().lower()

    server = Server("searchcarriers-api-bridge")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return _TOOL_DEFINITIONS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        # Tier gate — returns a structured error payload on insufficient tier.
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
        except Exception as exc:  # Final safety net.
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
