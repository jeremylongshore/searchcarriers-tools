#!/usr/bin/env python3
"""SearchCarriers Ops Reporter MCP Server.

OUTPUT stage of the stackable pipeline:
  Carrier Intel (INPUT) -> Risk Engine (ANALYSIS) -> Ops Reporter (OUTPUT)

Consumes data from the SearchCarriers API and produces formatted reports,
fleet analyses, carrier comparisons, and structured data exports. This is
the presentation layer — outputs are designed to be read directly by freight
professionals or passed downstream to document workflows.

All tools require pro tier and return a ``_pipeline`` key for traceability.
"""

import asyncio
import io
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

from plugins.shared.api_contract import (  # noqa: E402  # gitleaks:allow -- symbol names
    API_V3_BASE,
    normalize_v3_company,
)
from plugins.shared.tier_gate import TierError, check_tier  # noqa: E402

# ---------------------------------------------------------------------------
# Local modules — field normalization, CSV export, PDF rendering
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from csv_export import generate_carrier_csv  # noqa: E402
from field_map import normalize_authority, normalize_carrier, normalize_insurance  # noqa: E402

# ---------------------------------------------------------------------------
# MCP SDK
# ---------------------------------------------------------------------------
from mcp.server import Server  # noqa: E402
from mcp.server.stdio import stdio_server  # noqa: E402
from mcp.types import TextContent, Tool  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
API_BASE = "https://searchcarriers.com/api/v1"
SEARCH_BASE = API_V3_BASE
REQUEST_TIMEOUT = 20.0  # seconds — slightly higher for multi-fetch tools
VERSION = "0.2.0"

# OOS rate benchmarks (FMCSA 2023 national averages)
NATIONAL_OOS_VEHICLE_AVG = 21.0  # percent
NATIONAL_OOS_DRIVER_AVG = 6.0  # percent

# MCS-150 freshness thresholds
MCS150_STALE_YEARS = 2
MCS150_CRITICAL_YEARS = 4

# Maximum carriers allowed in a comparison
MAX_COMPARE_CARRIERS = 5

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


def _pipeline_meta(tool: str, dot_number: str) -> dict[str, Any]:
    """Build the standard ``_pipeline`` metadata block for all tool responses."""
    return {
        "source": "ops-reporter",
        "tool": tool,
        "version": VERSION,
        "dot_number": dot_number,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _report_date() -> str:
    """Return today's date formatted for report headers."""
    return _now_utc().strftime("%B %d, %Y")


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


# ---------------------------------------------------------------------------
# Helpers — data extraction
# ---------------------------------------------------------------------------


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


def _extract_list(data: Any) -> list[dict[str, Any]]:
    """Unwrap an API response to a list of records."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "results", "items"):
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


def _carrier_name(carrier: dict[str, Any]) -> str:
    """Return the best available display name for a carrier."""
    return (
        carrier.get("legalName")
        or carrier.get("legal_name")
        or carrier.get("name")
        or "Unknown Carrier"
    )


def _safe_str(value: Any, fallback: str = "N/A") -> str:
    """Convert any value to a display string, replacing None/empty with fallback."""
    if value is None or str(value).strip() == "":
        return fallback
    return str(value).strip()


def _safe_int(value: Any, fallback: int = 0) -> int:
    """Safely coerce a value to int."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return fallback


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    """Safely coerce a value to float."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return fallback


def _format_currency(amount: Any) -> str:
    """Format a numeric amount as a USD currency string."""
    try:
        val = float(amount or 0)
        if val >= 1_000_000:
            return f"${val / 1_000_000:.1f}M"
        if val >= 1_000:
            return f"${val / 1_000:.0f}K"
        return f"${val:.0f}"
    except (TypeError, ValueError):
        return "N/A"


# ---------------------------------------------------------------------------
# Helpers — inline risk assessment (used by generate_report)
# ---------------------------------------------------------------------------


def _quick_risk(
    carrier: dict[str, Any],
    authorities: list[dict[str, Any]],
    insurances: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    """Compute a lightweight risk level and list of risk notes.

    Accepts both normalized (``operating_status``) and raw (``operatingStatus``)
    field names for backward compatibility.

    Returns:
        A (risk_level, notes) pair where risk_level is one of
        ``low`` / ``medium`` / ``elevated`` / ``high``.
    """
    score = 0
    notes: list[str] = []

    # Operating status — normalized key first, then raw
    op_status = str(carrier.get("operating_status") or carrier.get("operatingStatus") or "").lower()
    if "authorized" in op_status and "not" not in op_status:
        notes.append("Operating status is authorized.")
    elif "not" in op_status or "inactive" in op_status or "revoked" in op_status:
        score += 30
        raw_val = carrier.get("operating_status") or carrier.get("operatingStatus")
        notes.append(f"Operating status is NOT authorized ({raw_val!r}).")
    else:
        score += 15
        raw_val = carrier.get("operating_status") or carrier.get("operatingStatus")
        notes.append(f"Operating status is unclear ({raw_val!r}).")

    # Safety rating
    rating = str(
        carrier.get("safety_rating")
        or carrier.get("rating")
        or carrier.get("safetyRating")
        or "Not Rated"
    ).strip()
    if "satisfactory" in rating.lower() and "un" not in rating.lower():
        notes.append("Safety rating: Satisfactory.")
    elif "unsatisfactory" in rating.lower():
        score += 25
        notes.append("Safety rating: Unsatisfactory — highest risk category.")
    elif "conditional" in rating.lower():
        score += 15
        notes.append("Safety rating: Conditional — known deficiencies present.")
    else:
        score += 10
        notes.append(f"Safety rating: {rating} — unrated carriers carry unknown risk.")

    # MCS-150 freshness
    raw_mcs = (
        carrier.get("mcs150_date") or carrier.get("mcs150Date") or carrier.get("mcs150FormDate")
    )
    mcs_dt = _parse_date(str(raw_mcs) if raw_mcs else None)
    mcs_age = _years_since(mcs_dt)
    if mcs_age is None:
        score += 8
        notes.append("MCS-150 filing date unavailable.")
    elif mcs_age > MCS150_CRITICAL_YEARS:
        score += 10
        notes.append(f"MCS-150 filed {mcs_age:.1f} years ago — critically overdue.")
    elif mcs_age > MCS150_STALE_YEARS:
        score += 5
        notes.append(f"MCS-150 filed {mcs_age:.1f} years ago — past biennial cycle.")
    else:
        notes.append(f"MCS-150 is current (filed {mcs_age:.1f} years ago).")

    # Insurance
    active_ins = [
        ins for ins in insurances if str(ins.get("status") or "").lower() in ("active", "current")
    ]
    if not active_ins:
        score += 20
        notes.append("No active insurance policies confirmed.")
    else:
        # Check for near-term cancellations
        now = _now_utc()
        expiring: list[str] = []
        for ins in active_ins:
            cancel_dt = _parse_date(ins.get("cancellation_date") or ins.get("cancellationDate"))
            if cancel_dt:
                days_remaining = (cancel_dt - now).days
                if 0 < days_remaining <= 30:
                    pol = ins.get("policy_number") or ins.get("policyNumber") or "unknown"
                    expiring.append(f"policy {pol} in {days_remaining}d")
        if expiring:
            score += 10
            notes.append(f"Near-term cancellation: {', '.join(expiring)}.")
        else:
            notes.append(f"{len(active_ins)} active insurance policy/policies confirmed.")

    # Authority
    active_auth = [
        a
        for a in authorities
        if "active" in str(a.get("status") or "").lower()
        or "authorized" in str(a.get("status") or "").lower()
    ]
    if not authorities:
        score += 20
        notes.append("No authority records found.")
    elif not active_auth:
        score += 20
        notes.append("All authority records are revoked or inactive.")
    else:
        auth_types = [str(a.get("type") or a.get("authorityType") or "") for a in active_auth]
        notes.append(f"Active authority: {', '.join(t for t in auth_types if t)}.")

    # Map score to level
    if score <= 25:
        level = "low"
    elif score <= 50:
        level = "medium"
    elif score <= 75:
        level = "elevated"
    else:
        level = "high"

    return level, notes


# ---------------------------------------------------------------------------
# Helpers — markdown formatting primitives
# ---------------------------------------------------------------------------


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render a Markdown table from headers and row lists.

    Column widths are padded to the widest content in each column for
    clean alignment in monospace contexts (terminals, PDF renderers).
    """
    if not rows:
        return "_No data available._"

    # Compute column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))

    def _pad(cells: list[str]) -> str:
        parts = []
        for i, cell in enumerate(cells):
            w = widths[i] if i < len(widths) else len(cell)
            parts.append(str(cell).ljust(w))
        return "| " + " | ".join(parts) + " |"

    separator = "| " + " | ".join("-" * w for w in widths) + " |"
    lines = [_pad(headers), separator] + [_pad(row) for row in rows]
    return "\n".join(lines)


def _divider() -> str:
    return "\n---\n"


def _section(title: str, body: str) -> str:
    return f"\n## {title}\n\n{body}\n"


def _recommendation_badge(level: str) -> str:
    """Map a risk level to a compliance recommendation string."""
    mapping = {
        "low": "**APPROVED** — Carrier meets standard vetting criteria.",
        "medium": "**CONDITIONAL APPROVAL** — Review flagged items before booking.",
        "elevated": "**CONDITIONAL APPROVAL** — Significant issues require resolution.",
        "high": "**DECLINED** — Carrier presents unacceptable risk. Do not use.",
    }
    return mapping.get(level, "**REVIEW REQUIRED** — Risk level undetermined.")


# ---------------------------------------------------------------------------
# Tool implementation: generate_report
# ---------------------------------------------------------------------------


async def _generate_report(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Generate a comprehensive carrier vetting report.

    Fetches carrier search data, authorities, and insurance records in
    parallel, normalizes all fields, then renders a professional report.
    Supports ``markdown``, ``text``, and ``pdf`` output formats.
    """
    dot: str = str(arguments["dot_number"]).strip()
    include_risk: bool = bool(arguments.get("include_risk", True))
    fmt: str = str(arguments.get("format", "markdown")).lower()
    if fmt not in ("markdown", "text", "pdf"):
        fmt = "markdown"

    search_url = f"{SEARCH_BASE}/search"

    async with httpx.AsyncClient(headers=_auth_headers(api_key), timeout=REQUEST_TIMEOUT) as client:
        search_task = _get(client, search_url, params={"dotNumber": dot, "perPage": 1})
        authorities_task = _get(client, f"{API_BASE}/company/{dot}/authorities")
        insurances_task = _get(client, f"{API_BASE}/company/{dot}/insurances")

        results = await asyncio.gather(
            search_task, authorities_task, insurances_task, return_exceptions=True
        )

    search_raw, authorities_raw, insurances_raw = results

    if isinstance(search_raw, Exception):
        return _error_payload("api_error", f"Carrier lookup failed: {search_raw}")

    raw_carrier = normalize_v3_company(_extract_carrier(search_raw))
    if not raw_carrier:
        return _error_payload("not_found", f"No carrier found for DOT {dot}.")

    raw_auth_list: list[dict[str, Any]] = (
        _extract_list(authorities_raw) if not isinstance(authorities_raw, Exception) else []
    )
    raw_ins_list: list[dict[str, Any]] = (
        _extract_list(insurances_raw) if not isinstance(insurances_raw, Exception) else []
    )

    # Normalize data through field_map
    carrier = normalize_carrier(raw_carrier)
    authorities = normalize_authority(raw_auth_list)
    insurances = normalize_insurance(raw_ins_list)

    name = carrier["legal_name"] or "Unknown Carrier"
    mc_number = _safe_str(carrier["mc_number"])
    dba = _safe_str(carrier["dba_name"])
    address = _safe_str(carrier["address"])
    phone = _safe_str(carrier["phone"])
    email = _safe_str(carrier["email"])
    op_status = _safe_str(carrier["operating_status"])
    safety_rating = _safe_str(carrier["safety_rating"], fallback="Not Rated")
    power_units = carrier["power_units"] or 0
    drivers = carrier["total_drivers"] or 0
    crashes = carrier["crash_total"] or 0
    inspections = carrier["inspection_total"] or 0
    oos_rate_vehicle = _safe_float(carrier["oos_rate_vehicle"])
    oos_rate_driver = _safe_float(carrier["oos_rate_driver"])
    entity_type = _safe_str(carrier["entity_type"])
    mcs_date_str = _safe_str(carrier["mcs150_date"])

    # Active authority types
    active_auth_types: list[str] = []
    inactive_auth_types: list[str] = []
    for auth in authorities:
        status = str(auth.get("status") or "").lower()
        atype = str(auth.get("type") or "Unknown")
        if "active" in status or "authorized" in status:
            active_auth_types.append(atype)
        else:
            inactive_auth_types.append(atype)

    # Active insurance policies
    active_ins = [
        ins for ins in insurances if str(ins.get("status") or "").lower() in ("active", "current")
    ]

    # Risk assessment (inline)
    risk_level: str = "medium"
    risk_notes: list[str] = []
    if include_risk:
        risk_level, risk_notes = _quick_risk(carrier, authorities, insurances)

    # ---------------------------------------------------------------------------
    # PDF output path
    # ---------------------------------------------------------------------------
    if fmt == "pdf":
        try:
            from pdf_renderer import render_pdf, report_output_path

            # Determine verdict badge
            if risk_level == "low":
                verdict = "APPROVED"
            elif risk_level == "high":
                verdict = "DECLINED"
            else:
                verdict = "CONDITIONAL"

            recommendation = _recommendation_badge(risk_level)

            pdf_path = report_output_path("vetting", dot)
            rendered = render_pdf(
                "vetting_report.html",
                {
                    "carrier": carrier,
                    "authorities": authorities,
                    "insurances": insurances,
                    "risk_level": risk_level,
                    "risk_notes": risk_notes,
                    "verdict": verdict,
                    "recommendation": recommendation,
                    "report_date": _report_date(),
                },
                pdf_path,
            )

            return {
                "report": f"PDF report written to {rendered}",
                "format": "pdf",
                "file_path": rendered,
                "carrier_name": name,
                "_pipeline": _pipeline_meta("generate_report", dot),
            }
        except RuntimeError:
            # Graceful degradation — fall back to markdown
            fmt = "markdown"
            # Continue to markdown rendering below

    # ---------------------------------------------------------------------------
    # Build report sections (markdown / text)
    # ---------------------------------------------------------------------------
    lines: list[str] = []

    # Header
    lines.append("# Carrier Vetting Report")
    lines.append("")
    lines.append("| Field       | Value                      |")
    lines.append("|-------------|----------------------------|")
    lines.append(f"| DOT Number  | {dot}                      |")
    lines.append(f"| MC Number   | {mc_number}                |")
    lines.append(f"| Carrier     | {name}                     |")
    lines.append(f"| Report Date | {_report_date()}           |")
    lines.append(f"| Generated   | Ops Reporter v{VERSION}    |")

    # Company Overview
    lines.append(_divider())
    lines.append("## Company Overview")
    lines.append("")
    overview_rows = [
        ["Legal Name", name],
        ["DBA / Trade Name", dba],
        ["Entity Type", entity_type],
        ["Physical Address", address],
        ["Phone", phone],
        ["Email", email],
        ["MC Number", mc_number],
        ["DOT Number", dot],
        ["MCS-150 Date", mcs_date_str],
    ]
    lines.append(_md_table(["Field", "Value"], overview_rows))

    # Operating Status & Authority
    lines.append(_divider())
    lines.append("## Operating Status & Authority")
    lines.append("")
    lines.append(f"**Operating Status:** {op_status}")
    lines.append("")

    if authorities:
        auth_rows = []
        for auth in authorities:
            atype = _safe_str(auth.get("type"))
            astatus = _safe_str(auth.get("status"))
            docket = _safe_str(auth.get("docket_number") or auth.get("granted_date"))
            auth_rows.append([atype, astatus, docket])
        lines.append(_md_table(["Authority Type", "Status", "Docket / Granted"], auth_rows))
    else:
        lines.append("_No authority records returned for this carrier._")

    if active_auth_types:
        lines.append(f"\nActive authorities: {', '.join(active_auth_types)}")
    if inactive_auth_types:
        lines.append(f"Inactive/revoked: {', '.join(inactive_auth_types)}")

    # Safety Summary
    lines.append(_divider())
    lines.append("## Safety Summary")
    lines.append("")
    safety_rows = [
        ["FMCSA Safety Rating", safety_rating],
        ["Power Units", str(power_units) if power_units else "N/A"],
        ["Total Drivers", str(drivers) if drivers else "N/A"],
        ["Total Crashes", str(crashes)],
        ["Total Inspections", str(inspections)],
        [
            "Vehicle OOS Rate",
            f"{oos_rate_vehicle:.1f}% (national avg {NATIONAL_OOS_VEHICLE_AVG:.0f}%)"
            if oos_rate_vehicle
            else "N/A",
        ],
        [
            "Driver OOS Rate",
            f"{oos_rate_driver:.1f}% (national avg {NATIONAL_OOS_DRIVER_AVG:.0f}%)"
            if oos_rate_driver
            else "N/A",
        ],
    ]
    lines.append(_md_table(["Metric", "Value"], safety_rows))

    # Insurance Coverage
    lines.append(_divider())
    lines.append("## Insurance Coverage")
    lines.append("")
    if insurances:
        ins_rows = []
        for ins in insurances:
            ins_type = _safe_str(ins.get("type"))
            ins_status = _safe_str(ins.get("status"))
            coverage = _format_currency(ins.get("coverage"))
            policy_num = _safe_str(ins.get("policy_number"))
            insurer = _safe_str(ins.get("insurer"))
            effective = _safe_str(ins.get("effective_date"))
            cancellation = _safe_str(ins.get("cancellation_date"))
            ins_rows.append(
                [ins_type, ins_status, coverage, policy_num, insurer, effective, cancellation]
            )
        lines.append(
            _md_table(
                ["Type", "Status", "Coverage", "Policy No.", "Insurer", "Effective", "Cancels"],
                ins_rows,
            )
        )
        lines.append(f"\n**Active Policies:** {len(active_ins)} of {len(insurances)} total")
    else:
        lines.append("_No insurance records returned for this carrier._")

    # Risk Assessment
    if include_risk:
        lines.append(_divider())
        lines.append("## Risk Assessment")
        lines.append("")
        risk_label = risk_level.upper()
        lines.append(f"**Overall Risk Level: {risk_label}**")
        lines.append("")
        lines.append("**Factors evaluated:**")
        lines.append("")
        for note in risk_notes:
            lines.append(f"- {note}")

    # Recommendation
    lines.append(_divider())
    lines.append("## Recommendation")
    lines.append("")
    rec_level = risk_level if include_risk else "medium"
    lines.append(_recommendation_badge(rec_level))
    lines.append("")
    if rec_level == "low":
        lines.append(
            "This carrier presents a low risk profile. No material issues identified "
            "across operating status, safety record, insurance, and authority checks."
        )
    elif rec_level in ("medium", "elevated"):
        lines.append(
            "One or more items require attention before or during the engagement. "
            "Review the flagged factors in the Risk Assessment section above and "
            "document your disposition in the carrier file."
        )
    else:
        lines.append(
            "This carrier does not meet minimum vetting standards. Do not tender loads "
            "until all disqualifying factors have been resolved and re-verified."
        )

    # Disclaimer
    lines.append(_divider())
    lines.append("## Disclaimer")
    lines.append("")
    lines.append(
        "_This report is generated from data provided by the SearchCarriers API and "
        "reflects FMCSA-sourced information at the time of retrieval. It is intended "
        "as a compliance aid only and does not constitute legal advice. Always verify "
        "critical details directly with FMCSA SAFER and the carrier before tendering loads._"
    )

    report = "\n".join(lines)

    # Plain-text post-processing: strip markdown syntax
    if fmt == "text":
        import re

        report = re.sub(r"\*\*(.+?)\*\*", r"\1", report)
        report = re.sub(r"\*(.+?)\*", r"\1", report)
        report = re.sub(r"^#{1,3} ", "", report, flags=re.MULTILINE)
        report = re.sub(r"^---$", "=" * 60, report, flags=re.MULTILINE)
        report = re.sub(r"_(.+?)_", r"\1", report)

    return {
        "report": report,
        "format": fmt,
        "carrier_name": name,
        "_pipeline": _pipeline_meta("generate_report", dot),
    }


# ---------------------------------------------------------------------------
# Tool implementation: generate_fleet
# ---------------------------------------------------------------------------


async def _generate_fleet(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Generate a fleet analysis report for a carrier.

    Fetches carrier basics and equipment data in parallel, normalizes fields,
    then renders a structured fleet analysis.  Supports ``pdf`` format.
    """
    dot: str = str(arguments["dot_number"]).strip()
    fmt: str = str(arguments.get("format", "markdown")).lower()

    search_url = f"{SEARCH_BASE}/search"

    async with httpx.AsyncClient(headers=_auth_headers(api_key), timeout=REQUEST_TIMEOUT) as client:
        search_task = _get(client, search_url, params={"dotNumber": dot, "perPage": 1})
        equipment_task = _get(client, f"{API_BASE}/company/{dot}/equipment")

        results = await asyncio.gather(search_task, equipment_task, return_exceptions=True)

    search_raw, equipment_raw = results

    if isinstance(search_raw, Exception):
        return _error_payload("api_error", f"Carrier lookup failed: {search_raw}")

    raw_carrier = normalize_v3_company(_extract_carrier(search_raw))
    if not raw_carrier:
        return _error_payload("not_found", f"No carrier found for DOT {dot}.")

    equipment_list: list[dict[str, Any]] = (
        _extract_list(equipment_raw) if not isinstance(equipment_raw, Exception) else []
    )

    # Normalize carrier data
    carrier = normalize_carrier(raw_carrier)
    name = carrier["legal_name"] or "Unknown Carrier"
    power_units = carrier["power_units"] or 0
    drivers = carrier["total_drivers"] or 0

    # Equipment type breakdown
    type_counts: dict[str, int] = {}
    roster: list[dict[str, str]] = []
    for item in equipment_list:
        eq_type = str(
            item.get("equipmentType") or item.get("equipment_type") or item.get("type") or "Unknown"
        )
        type_counts[eq_type] = type_counts.get(eq_type, 0) + 1

        # Extract VIN detail if available
        vin_detail = item.get("vin_detail") or {}
        year = _safe_str(vin_detail.get("model_year") or item.get("year") or item.get("modelYear"))
        make = _safe_str(vin_detail.get("make") or item.get("make") or item.get("manufacturer"))
        model = _safe_str(vin_detail.get("model") or item.get("model"))
        vin = _safe_str(item.get("vin") or item.get("VIN"))

        roster.append(
            {
                "year": year if year != "N/A" else "",
                "make": make if make != "N/A" else "",
                "model": model if model != "N/A" else "",
                "type": eq_type,
                "vin": vin if vin != "N/A" else "",
            }
        )

    # Fleet-to-driver ratio
    if power_units > 0 and drivers > 0:
        ratio = drivers / power_units
        if ratio < 0.8:
            ratio_note = (
                f"Driver-to-unit ratio is {ratio:.2f} — fewer drivers than power units. "
                "May indicate equipment-heavy operation or driver shortage."
            )
        elif ratio <= 1.5:
            ratio_note = f"Driver-to-unit ratio is {ratio:.2f} — within normal operating range."
        else:
            ratio_note = (
                f"Driver-to-unit ratio is {ratio:.2f} — significantly more drivers than "
                "units. May indicate team driving, LTL relay operation, or data anomaly."
            )
    elif power_units > 0:
        ratio_note = "Driver count unavailable; ratio cannot be computed."
    else:
        ratio_note = "Fleet size data unavailable from carrier record."

    # ---------------------------------------------------------------------------
    # PDF output
    # ---------------------------------------------------------------------------
    if fmt == "pdf":
        try:
            from pdf_renderer import render_pdf, report_output_path

            sorted_types = sorted(type_counts.items(), key=lambda x: -x[1])
            pdf_path = report_output_path("fleet", dot)
            rendered = render_pdf(
                "fleet_report.html",
                {
                    "carrier": carrier,
                    "equipment_count": len(equipment_list),
                    "type_count": len(type_counts),
                    "type_counts": sorted_types,
                    "ratio_note": ratio_note,
                    "roster": roster[:25],
                    "report_date": _report_date(),
                },
                pdf_path,
            )

            return {
                "report": f"PDF fleet report written to {rendered}",
                "format": "pdf",
                "file_path": rendered,
                "fleet_size": {
                    "power_units": power_units,
                    "drivers": drivers,
                    "equipment_records": len(equipment_list),
                    "equipment_types": type_counts,
                },
                "_pipeline": _pipeline_meta("generate_fleet", dot),
            }
        except RuntimeError:
            fmt = "markdown"

    # ---------------------------------------------------------------------------
    # Build report (markdown)
    # ---------------------------------------------------------------------------
    lines: list[str] = []
    lines.append("# Fleet Analysis Report")
    lines.append("")
    lines.append(f"**Carrier:** {name}  ")
    lines.append(f"**DOT Number:** {dot}  ")
    lines.append(f"**Report Date:** {_report_date()}")

    lines.append(_divider())
    lines.append("## Fleet Overview")
    lines.append("")
    fleet_rows = [
        ["Power Units (FMCSA)", str(power_units) if power_units else "N/A"],
        ["Total Drivers (FMCSA)", str(drivers) if drivers else "N/A"],
        ["Equipment Records (API)", str(len(equipment_list))],
        ["Equipment Types", str(len(type_counts))],
    ]
    lines.append(_md_table(["Metric", "Value"], fleet_rows))

    lines.append(_divider())
    lines.append("## Fleet Composition")
    lines.append("")
    lines.append(f"_{ratio_note}_")
    lines.append("")

    if type_counts:
        total_eq = sum(type_counts.values())
        type_rows = [
            [eq_type, str(count), f"{count / total_eq * 100:.1f}%"]
            for eq_type, count in sorted(type_counts.items(), key=lambda x: -x[1])
        ]
        lines.append(_md_table(["Equipment Type", "Count", "Share"], type_rows))
    else:
        lines.append("_No equipment records returned for this carrier._")

    if roster:
        lines.append(_divider())
        lines.append("## Equipment Roster (Sample)")
        lines.append("")
        sample = roster[:25]
        roster_rows = [
            [
                r.get("year", "N/A"),
                r.get("make", "N/A"),
                r.get("model", "N/A"),
                r.get("type", "N/A"),
                r.get("vin", "N/A"),
            ]
            for r in sample
        ]
        lines.append(_md_table(["Year", "Make", "Model", "Type", "VIN"], roster_rows))
        if len(equipment_list) > 25:
            lines.append(f"\n_Showing 25 of {len(equipment_list)} equipment records._")

    report = "\n".join(lines)

    fleet_size = {
        "power_units": power_units,
        "drivers": drivers,
        "equipment_records": len(equipment_list),
        "equipment_types": type_counts,
    }

    return {
        "report": report,
        "fleet_size": fleet_size,
        "_pipeline": _pipeline_meta("generate_fleet", dot),
    }


# ---------------------------------------------------------------------------
# Tool implementation: generate_compare
# ---------------------------------------------------------------------------


async def _generate_compare(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Generate a side-by-side carrier comparison table.

    Fetches search data for all requested carriers in parallel, normalizes
    all fields, and renders a comparison.  Supports ``pdf`` format.
    """
    raw_dots: list[Any] = arguments.get("dot_numbers") or []
    dot_numbers = [str(d).strip() for d in raw_dots if str(d).strip()]
    fmt: str = str(arguments.get("format", "markdown")).lower()

    if len(dot_numbers) < 2:
        return _error_payload(
            "invalid_input",
            "At least 2 DOT numbers are required for a comparison.",
        )
    if len(dot_numbers) > MAX_COMPARE_CARRIERS:
        return _error_payload(
            "invalid_input",
            f"A maximum of {MAX_COMPARE_CARRIERS} carriers can be compared at once.",
        )

    search_url = f"{SEARCH_BASE}/search"

    async with httpx.AsyncClient(headers=_auth_headers(api_key), timeout=REQUEST_TIMEOUT) as client:
        # Fire all fetches in parallel — 3 requests per carrier
        tasks: list[Any] = []
        for dot in dot_numbers:
            tasks.append(_get(client, search_url, params={"dotNumber": dot, "perPage": 1}))
            tasks.append(_get(client, f"{API_BASE}/company/{dot}/authorities"))
            tasks.append(_get(client, f"{API_BASE}/company/{dot}/insurances"))

        all_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Repackage results: [(search, authorities, insurances), ...]
    carrier_data: list[tuple[Any, Any, Any]] = []
    for i, dot in enumerate(dot_numbers):
        base = i * 3
        carrier_data.append((all_results[base], all_results[base + 1], all_results[base + 2]))

    # ---------------------------------------------------------------------------
    # Normalize all carrier data
    # ---------------------------------------------------------------------------
    normalized_carriers: list[dict[str, Any]] = []
    normalized_auths: list[list[dict[str, Any]]] = []
    normalized_inss: list[list[dict[str, Any]]] = []
    carrier_names: list[str] = []

    for dot, (search_raw, auth_raw, ins_raw) in zip(dot_numbers, carrier_data):
        if isinstance(search_raw, Exception):
            normalized_carriers.append({"_error": str(search_raw), "dot_number": dot})
        else:
            raw_c = normalize_v3_company(_extract_carrier(search_raw))
            if raw_c:
                nc = normalize_carrier(raw_c)
                nc["dot_number"] = nc["dot_number"] or dot
                normalized_carriers.append(nc)
            else:
                normalized_carriers.append({"_error": "empty", "dot_number": dot})

        raw_auth = _extract_list(auth_raw) if not isinstance(auth_raw, Exception) else []
        raw_ins = _extract_list(ins_raw) if not isinstance(ins_raw, Exception) else []
        normalized_auths.append(normalize_authority(raw_auth))
        normalized_inss.append(normalize_insurance(raw_ins))

    carrier_names = [
        "ERROR" if "_error" in c else (c.get("legal_name") or "Unknown Carrier")
        for c in normalized_carriers
    ]

    def _row_for_field(
        label: str,
        extractor: Any,  # callable(carrier, authorities, insurances) -> str
    ) -> list[str]:
        cells = [label]
        for c, auths, inss in zip(normalized_carriers, normalized_auths, normalized_inss):
            if "_error" in c:
                cells.append("(fetch error)")
            else:
                try:
                    cells.append(str(extractor(c, auths, inss)))
                except Exception:
                    cells.append("N/A")
        return cells

    # Risk indicator per carrier
    risk_levels: list[str] = []
    for c, auths, inss in zip(normalized_carriers, normalized_auths, normalized_inss):
        if "_error" in c:
            risk_levels.append("N/A")
        else:
            level, _ = _quick_risk(c, auths, inss)
            risk_levels.append(level)

    # Build comparison table rows
    rows: list[list[str]] = []

    rows.append(
        _row_for_field(
            "DOT Number",
            lambda c, a, i: c.get("dot_number") or "N/A",
        )
    )
    rows.append(
        _row_for_field(
            "Legal Name",
            lambda c, a, i: c.get("legal_name") or "Unknown Carrier",
        )
    )
    rows.append(
        _row_for_field(
            "Operating Status",
            lambda c, a, i: _safe_str(c.get("operating_status")),
        )
    )
    rows.append(
        _row_for_field(
            "Entity Type",
            lambda c, a, i: _safe_str(c.get("entity_type")),
        )
    )
    rows.append(
        _row_for_field(
            "State",
            lambda c, a, i: _safe_str(c.get("state")),
        )
    )
    rows.append(
        _row_for_field(
            "Power Units",
            lambda c, a, i: str(c.get("power_units") or 0) or "N/A",
        )
    )
    rows.append(
        _row_for_field(
            "Drivers",
            lambda c, a, i: str(c.get("total_drivers") or 0) or "N/A",
        )
    )
    rows.append(
        _row_for_field(
            "Safety Rating",
            lambda c, a, i: _safe_str(c.get("safety_rating"), fallback="Not Rated"),
        )
    )
    rows.append(
        _row_for_field(
            "Vehicle OOS Rate",
            lambda c, a, i: (
                f"{_safe_float(c.get('oos_rate_vehicle')):.1f}%"
                if c.get("oos_rate_vehicle")
                else "N/A"
            ),
        )
    )
    rows.append(
        _row_for_field(
            "Crashes",
            lambda c, a, i: str(c.get("crash_total") or 0),
        )
    )
    rows.append(
        _row_for_field(
            "Inspections",
            lambda c, a, i: str(c.get("inspection_total") or 0),
        )
    )
    rows.append(
        _row_for_field(
            "Active Insurance",
            lambda c, a, i: (
                str(
                    sum(
                        1
                        for ins in i
                        if str(ins.get("status") or "").lower() in ("active", "current")
                    )
                )
                + " polic"
                + (
                    "ies"
                    if sum(
                        1
                        for ins in i
                        if str(ins.get("status") or "").lower() in ("active", "current")
                    )
                    != 1
                    else "y"
                )
            ),
        )
    )
    rows.append(
        _row_for_field(
            "Authority Status",
            lambda c, a, i: (
                "Active"
                if any(
                    "active" in str(auth.get("status") or "").lower()
                    or "authorized" in str(auth.get("status") or "").lower()
                    for auth in a
                )
                else ("Revoked/Inactive" if a else "No records")
            ),
        )
    )
    # Risk row appended manually
    risk_row = ["Risk Indicator"] + risk_levels
    rows.append(risk_row)

    # For the comparison we use a simplified single-line header
    headers_simple = ["Field"] + [
        f"{name} ({dot})" for name, dot in zip(carrier_names, dot_numbers)
    ]

    # ---------------------------------------------------------------------------
    # PDF output
    # ---------------------------------------------------------------------------
    if fmt == "pdf":
        try:
            from pdf_renderer import render_pdf, report_output_path

            comparison_rows = [{"label": row[0], "values": row[1:]} for row in rows]
            risk_pairs = list(zip(normalized_carriers, risk_levels))
            pdf_path = report_output_path("compare", "_".join(dot_numbers))
            rendered = render_pdf(
                "compare_report.html",
                {
                    "carriers": [c for c in normalized_carriers if "_error" not in c],
                    "comparison_rows": comparison_rows,
                    "risk_pairs": risk_pairs,
                    "report_date": _report_date(),
                },
                pdf_path,
            )

            return {
                "report": f"PDF comparison report written to {rendered}",
                "format": "pdf",
                "file_path": rendered,
                "carrier_count": len(dot_numbers),
                "carriers": carrier_names,
                "_pipeline": {
                    "source": "ops-reporter",
                    "tool": "generate_compare",
                    "version": VERSION,
                    "dot_numbers": dot_numbers,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }
        except RuntimeError:
            pass  # Fall through to markdown

    # ---------------------------------------------------------------------------
    # Markdown output
    # ---------------------------------------------------------------------------
    lines: list[str] = []
    lines.append("# Carrier Comparison Report")
    lines.append("")
    lines.append(f"**Carriers compared:** {len(dot_numbers)}  ")
    lines.append(f"**Report Date:** {_report_date()}  ")
    lines.append(f"**DOT Numbers:** {', '.join(dot_numbers)}")

    lines.append(_divider())
    lines.append("## Side-by-Side Comparison")
    lines.append("")
    lines.append(_md_table(headers_simple, rows))

    lines.append(_divider())
    lines.append("## Risk Summary")
    lines.append("")
    for cn, dot, lvl in zip(carrier_names, dot_numbers, risk_levels):
        lines.append(f"- **{cn}** (DOT {dot}): Risk level **{lvl.upper()}**")

    lines.append(_divider())
    lines.append(
        "_Data sourced from SearchCarriers API (FMCSA-derived). "
        "Verify all figures directly before making carrier decisions._"
    )

    report = "\n".join(lines)

    return {
        "report": report,
        "carrier_count": len(dot_numbers),
        "carriers": carrier_names,
        "_pipeline": {
            "source": "ops-reporter",
            "tool": "generate_compare",
            "version": VERSION,
            "dot_numbers": dot_numbers,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


# ---------------------------------------------------------------------------
# Tool implementation: export_data
# ---------------------------------------------------------------------------


async def _export_data(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Export structured carrier data in JSON, CSV, or Markdown format.

    Fetches the requested data sections in parallel, normalizes the data,
    and serialises it according to the caller's preferred format.
    CSV now produces a clean, curated spreadsheet instead of a 143-column dump.
    """
    dot: str = str(arguments["dot_number"]).strip()
    fmt: str = str(arguments.get("format", "json")).lower()
    if fmt not in ("json", "csv", "markdown"):
        fmt = "json"

    all_sections = ["basics", "authorities", "insurances", "equipment"]
    raw_sections: list[Any] = arguments.get("sections") or all_sections
    requested_sections = [str(s).lower() for s in raw_sections if str(s).lower() in all_sections]
    if not requested_sections:
        requested_sections = all_sections

    # Map section names to (url, params) tuples.
    section_urls: dict[str, tuple[str, dict[str, Any] | None]] = {
        "basics": (f"{SEARCH_BASE}/search", {"dotNumber": dot, "perPage": 1}),
        "authorities": (f"{API_BASE}/company/{dot}/authorities", None),
        "insurances": (f"{API_BASE}/company/{dot}/insurances", None),
        "equipment": (f"{API_BASE}/company/{dot}/equipment", None),
    }

    async with httpx.AsyncClient(headers=_auth_headers(api_key), timeout=REQUEST_TIMEOUT) as client:
        tasks = [
            _get(client, section_urls[s][0], params=section_urls[s][1]) for s in requested_sections
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect raw data per section
    section_data: dict[str, Any] = {}
    for section, result in zip(requested_sections, results):
        if isinstance(result, Exception):
            section_data[section] = {"error": str(result)}
        elif section == "basics":
            section_data[section] = normalize_v3_company(_extract_carrier(result))
        else:
            section_data[section] = _extract_list(result)

    # Normalize data for curated output
    norm_carrier = None
    norm_auths = None
    norm_inss = None

    raw_basics = section_data.get("basics")
    if isinstance(raw_basics, dict) and "error" not in raw_basics:
        norm_carrier = normalize_carrier(raw_basics)

    raw_auth = section_data.get("authorities")
    if isinstance(raw_auth, list):
        norm_auths = normalize_authority(raw_auth)

    raw_ins = section_data.get("insurances")
    if isinstance(raw_ins, list):
        norm_inss = normalize_insurance(raw_ins)

    # ---------------------------------------------------------------------------
    # Format output
    # ---------------------------------------------------------------------------
    output: str
    file_path: str | None = None

    if fmt == "json":
        output = json.dumps(section_data, indent=2, default=str)

    elif fmt == "csv":
        # Use curated CSV export instead of raw dump
        if norm_carrier:
            output = generate_carrier_csv(norm_carrier, norm_auths, norm_inss)
        else:
            # Fallback for error cases
            buf = io.StringIO()
            buf.write("ERROR,Could not normalize carrier data\n")
            output = buf.getvalue()

        # Write CSV to disk
        from pdf_renderer import report_output_path

        csv_path = report_output_path("export", dot, "csv")
        csv_path.write_text(output, encoding="utf-8")
        file_path = str(csv_path.resolve())

    else:  # markdown
        md_lines: list[str] = []
        md_lines.append(f"# Carrier Data Export — DOT {dot}")
        md_lines.append(f"\n**Report Date:** {_report_date()}\n")

        def _flatten_dict_to_rows(d: dict[str, Any]) -> list[list[str]]:
            return [[str(k), str(v)] for k, v in d.items() if v is not None]

        for section in requested_sections:
            data = section_data.get(section)
            md_lines.append(f"\n## {section.capitalize()}\n")
            if isinstance(data, dict) and "error" in data:
                md_lines.append(f"_Error: {data['error']}_\n")
            elif isinstance(data, dict):
                md_lines.append(_md_table(["Field", "Value"], _flatten_dict_to_rows(data)))
            elif isinstance(data, list):
                if not data:
                    md_lines.append("_No records returned._\n")
                else:
                    all_keys = list(data[0].keys()) if data else []
                    rows = [[str(rec.get(k, "")) for k in all_keys] for rec in data]
                    md_lines.append(_md_table(all_keys, rows))
            else:
                md_lines.append("_No data._\n")

        output = "\n".join(md_lines)

    result: dict[str, Any] = {
        "data": output,
        "format": fmt,
        "sections": requested_sections,
        "_pipeline": _pipeline_meta("export_data", dot),
    }
    if file_path:
        result["file_path"] = file_path

    return result


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

_TOOL_DEFINITIONS: list[Tool] = [
    Tool(
        name="generate_report",
        description=(
            "Generate a comprehensive carrier vetting report by DOT number. "
            "Fetches carrier basics, operating authority, and insurance records "
            "in parallel, then renders a professional markdown report with sections "
            "for company overview, operating status, safety summary, insurance "
            "coverage, risk assessment, recommendation, and disclaimer. "
            "Suitable for placement in a compliance file. Min tier: pro."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "dot_number": {
                    "type": "string",
                    "description": "The carrier's USDOT number.",
                },
                "include_risk": {
                    "type": "boolean",
                    "description": (
                        "When true (default), compute an inline risk assessment and "
                        "include it in the report alongside the recommendation."
                    ),
                    "default": True,
                },
                "format": {
                    "type": "string",
                    "enum": ["markdown", "text", "pdf"],
                    "description": (
                        "Output format. 'markdown' (default) returns formatted markdown "
                        "with headers and tables. 'text' strips markdown syntax for plain "
                        "text environments. 'pdf' writes a professional PDF to disk."
                    ),
                    "default": "markdown",
                },
            },
            "required": ["dot_number"],
        },
    ),
    Tool(
        name="generate_fleet",
        description=(
            "Generate a fleet analysis report for a carrier by DOT number. "
            "Fetches the carrier's basic record and equipment roster in parallel, "
            "then renders a report covering fleet size, driver-to-unit ratio analysis, "
            "equipment type breakdown, and a sample equipment roster. Min tier: pro."
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
    Tool(
        name="generate_compare",
        description=(
            "Generate a side-by-side carrier comparison report for 2 to 5 DOT numbers. "
            "Fetches carrier basics, authority, and insurance records for all carriers "
            "in parallel, then renders a structured markdown comparison table covering "
            "company basics, fleet size, safety metrics, insurance, authority status, "
            "and an overall risk indicator. Min tier: pro."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "dot_numbers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 5,
                    "description": "List of 2 to 5 USDOT numbers to compare.",
                },
            },
            "required": ["dot_numbers"],
        },
    ),
    Tool(
        name="export_data",
        description=(
            "Export structured carrier data in JSON, CSV, or Markdown format. "
            "Selectively fetch one or more data sections (basics, authorities, "
            "insurances, equipment) by DOT number. Useful for piping data into "
            "TMS systems, spreadsheets, or document workflows. Min tier: pro."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "dot_number": {
                    "type": "string",
                    "description": "The carrier's USDOT number.",
                },
                "format": {
                    "type": "string",
                    "enum": ["json", "csv", "markdown"],
                    "description": (
                        "Output format: 'json' (default) for structured data, "
                        "'csv' for clean spreadsheet export (curated columns), "
                        "'markdown' for document embedding."
                    ),
                    "default": "json",
                },
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["basics", "authorities", "insurances", "equipment"],
                    },
                    "description": (
                        "Data sections to include. Defaults to all four: "
                        "basics, authorities, insurances, equipment."
                    ),
                },
            },
            "required": ["dot_number"],
        },
    ),
]

# Map tool names to their implementation coroutines.
_TOOL_HANDLERS = {
    "generate_report": _generate_report,
    "generate_fleet": _generate_fleet,
    "generate_compare": _generate_compare,
    "export_data": _export_data,
}


async def serve() -> None:
    """Entry point: create the MCP server and run it over stdio."""
    # Fail fast if the API key is absent.
    try:
        api_key = _api_key()
    except RuntimeError as exc:
        print(f"[ops-reporter] Startup error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Read caller tier from environment (optional; defaults to "free").
    user_tier = os.environ.get("SEARCHCARRIERS_TIER", "free").strip().lower()

    server = Server("searchcarriers-ops-reporter")

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
            result = _error_payload(
                "unknown_tool",
                f"No handler registered for tool '{name}'.",
            )
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
