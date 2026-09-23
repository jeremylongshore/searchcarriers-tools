#!/usr/bin/env python3
"""SearchCarriers Risk Engine MCP Server.

ANALYSIS stage of the stackable pipeline:
  Carrier Intel (INPUT) -> Risk Engine (ANALYSIS) -> Ops Reporter (OUTPUT)

Consumes carrier data from the SearchCarriers API and produces risk
assessments, vetting verdicts, insurance validations, and compliance
audits. All outputs include a ``_pipeline`` key for downstream consumption
by the Ops Reporter plugin.
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
    API_V2_BASE,
    API_V3_BASE,
    normalize_v3_company,
    response_data,
)
from plugins.shared.tier_gate import TierError, check_tier  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
API_BASE = "https://searchcarriers.com/api/v1"
SEARCH_BASE = API_V3_BASE
REQUEST_TIMEOUT = 15.0  # seconds
VERSION = "0.3.0"

# National OOS rate benchmarks (FMCSA 2023 averages)
NATIONAL_OOS_VEHICLE_AVG = 21.0  # percent
NATIONAL_OOS_DRIVER_AVG = 6.0  # percent

# Insurance minimums (USD) by commodity class
MIN_GENERAL_FREIGHT_COVERAGE = 750_000
MIN_HAZMAT_COVERAGE = 5_000_000

# MCS-150 freshness thresholds
MCS150_STALE_YEARS = 2
MCS150_CRITICAL_YEARS = 4

VETTING_RULE_KEYS = {
    "operating_status",
    "min_insurance_coverage",
    "max_oos_rate",
    "max_crash_rate_per_pu",
    "authority_active",
    "mcs150_current",
}


# ---------------------------------------------------------------------------
# Helpers
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
        "source": "risk-engine",
        "tool": tool,
        "version": VERSION,
        "dot_number": dot_number,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_date(value: str | None) -> datetime | None:
    """Parse an ISO-8601 date string to a timezone-aware datetime, or None."""
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
    """Return fractional years elapsed since a datetime, or None if dt is None."""
    if dt is None:
        return None
    delta = _now_utc() - dt
    return delta.days / 365.25


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


def _extract_carrier(data: dict[str, Any]) -> dict[str, Any]:
    """Unwrap common API envelope shapes to get the carrier record.

    The SearchCarriers ``/search`` endpoint may return a paginated envelope
    (``{"data": [...], "total": N}``).  When DOT-number lookup returns a
    single record we normalise to a plain dict.
    """
    if isinstance(data, list):
        return data[0] if data else {}
    for key in ("data", "results", "items"):
        if key in data and isinstance(data[key], list):
            items = data[key]
            return items[0] if items else {}
    return data


def _extract_list(data: Any) -> list[dict[str, Any]]:
    """Unwrap an API response to a list of records."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "results", "items"):
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


# ---------------------------------------------------------------------------
# Risk scoring internals
# ---------------------------------------------------------------------------


def _score_operating_status(carrier: dict[str, Any]) -> tuple[int, str]:
    """Return (penalty, description) for operating status."""
    status = str(carrier.get("operatingStatus") or "").lower()
    if "authorized" in status and "not" not in status:
        return 0, "Operating status is authorized."
    if "not" in status or "inactive" in status or "revoked" in status:
        return 30, f"Operating status is not authorized ({carrier.get('operatingStatus')!r})."
    return 15, f"Operating status is unclear ({carrier.get('operatingStatus')!r})."


def _score_safety_rating(carrier: dict[str, Any]) -> tuple[int, str]:
    """Return (penalty, description) for FMCSA safety rating."""
    raw = str(carrier.get("rating") or carrier.get("safetyRating") or "Not Rated").strip()
    normalized = raw.lower()

    if "satisfactory" in normalized and "un" not in normalized:
        return 0, "Safety rating: Satisfactory."
    if "unsatisfactory" in normalized:
        return 25, "Safety rating: Unsatisfactory — highest risk category."
    if "conditional" in normalized:
        return 15, "Safety rating: Conditional — known deficiencies."
    return 10, f"Safety rating: {raw} — unrated carriers carry unknown risk."


def _score_oos_rate(carrier: dict[str, Any]) -> tuple[int, str]:
    """Return (penalty, description) based on OOS rates vs national averages."""
    try:
        oos_rate = float(carrier.get("oosRate") or carrier.get("oosRateVehicle") or 0)
    except (TypeError, ValueError):
        return 5, "Vehicle OOS rate unavailable; unable to assess."

    if oos_rate <= 0:
        return 0, "OOS rate data unavailable."

    penalty = 0
    parts: list[str] = []

    excess = oos_rate - NATIONAL_OOS_VEHICLE_AVG
    if excess > 20:
        penalty += 20
        parts.append(
            f"Vehicle OOS rate {oos_rate:.1f}% is {excess:.1f}pp above the "
            f"{NATIONAL_OOS_VEHICLE_AVG:.0f}% national average (severe)."
        )
    elif excess > 10:
        penalty += 12
        parts.append(
            f"Vehicle OOS rate {oos_rate:.1f}% is {excess:.1f}pp above the "
            f"{NATIONAL_OOS_VEHICLE_AVG:.0f}% national average (elevated)."
        )
    elif excess > 0:
        penalty += 6
        parts.append(
            f"Vehicle OOS rate {oos_rate:.1f}% is {excess:.1f}pp above the "
            f"{NATIONAL_OOS_VEHICLE_AVG:.0f}% national average (moderate)."
        )
    else:
        parts.append(
            f"Vehicle OOS rate {oos_rate:.1f}% is at or below the "
            f"{NATIONAL_OOS_VEHICLE_AVG:.0f}% national average."
        )

    return penalty, " ".join(parts)


def _score_crash_rate(carrier: dict[str, Any]) -> tuple[int, str]:
    """Return (penalty, description) based on crash rate per power unit."""
    try:
        crashes = float(carrier.get("crashTotal") or 0)
        power_units = float(carrier.get("totalPowerUnits") or 0)
    except (TypeError, ValueError):
        return 5, "Crash/fleet data unavailable; unable to assess crash rate."

    if power_units <= 0:
        return 5, "Fleet size unknown; crash rate cannot be calculated."

    rate = crashes / power_units
    if rate == 0:
        return 0, "No recorded crashes — zero crash rate."
    if rate > 1.0:
        return 20, (
            f"High crash rate: {rate:.2f} crashes/power unit "
            f"({int(crashes)} crashes, {int(power_units)} units)."
        )
    if rate > 0.5:
        return 12, (
            f"Elevated crash rate: {rate:.2f} crashes/power unit "
            f"({int(crashes)} crashes, {int(power_units)} units)."
        )
    if rate > 0.2:
        return 6, (
            f"Moderate crash rate: {rate:.2f} crashes/power unit "
            f"({int(crashes)} crashes, {int(power_units)} units)."
        )
    return 0, (
        f"Low crash rate: {rate:.2f} crashes/power unit "
        f"({int(crashes)} crashes, {int(power_units)} units)."
    )


def _score_insurance(insurances: list[dict[str, Any]]) -> tuple[int, str]:
    """Return (penalty, description) for insurance status."""
    if not insurances:
        return 20, "No insurance records found — coverage cannot be confirmed."

    active = [
        ins for ins in insurances if str(ins.get("status") or "").lower() in ("active", "current")
    ]
    if not active:
        return 20, "No active insurance policies found — carrier may be uninsured."

    # Check for cancellation dates within 30 days
    now = _now_utc()
    expiring_soon: list[str] = []
    for ins in active:
        cancel_dt = _parse_date(ins.get("cancellationDate"))
        if cancel_dt:
            days_remaining = (cancel_dt - now).days
            if 0 < days_remaining <= 30:
                policy_num = ins.get("policyNumber") or "unknown"
                expiring_soon.append(f"Policy {policy_num} cancels in {days_remaining}d.")

    if expiring_soon:
        return 10, (
            f"{len(active)} active policy/policies; near-term cancellations: "
            + " ".join(expiring_soon)
        )

    return 0, f"{len(active)} active insurance policy/policies confirmed."


def _score_authority(authorities: list[dict[str, Any]]) -> tuple[int, str]:
    """Return (penalty, description) for authority status."""
    if not authorities:
        return 20, "No authority records found — cannot confirm operating authority."

    active_types: list[str] = []
    revoked_types: list[str] = []
    for auth in authorities:
        status = str(auth.get("status") or "").lower()
        auth_type = auth.get("type") or auth.get("authorityType") or "unknown"
        if "active" in status or "authorized" in status:
            active_types.append(str(auth_type))
        elif "revoked" in status or "inactive" in status:
            revoked_types.append(str(auth_type))

    if revoked_types and not active_types:
        return 20, f"All authorities revoked or inactive: {', '.join(revoked_types)}."
    if revoked_types:
        return 8, (
            f"Mixed authority status — active: {', '.join(active_types)}; "
            f"revoked/inactive: {', '.join(revoked_types)}."
        )
    if active_types:
        return 0, f"Active operating authority confirmed: {', '.join(active_types)}."

    return 10, "Authority records present but status is unclear."


def _score_mcs150(carrier: dict[str, Any]) -> tuple[int, str]:
    """Return (penalty, description) for MCS-150 filing freshness."""
    raw_date = carrier.get("mcs150Date") or carrier.get("mcs150FormDate")
    dt = _parse_date(str(raw_date) if raw_date else None)
    age_years = _years_since(dt)

    if age_years is None:
        return 8, "MCS-150 filing date unavailable — freshness cannot be assessed."
    if age_years > MCS150_CRITICAL_YEARS:
        return 10, (
            f"MCS-150 filed {age_years:.1f} years ago — critically overdue "
            f"(FMCSA requires biennial filing)."
        )
    if age_years > MCS150_STALE_YEARS:
        return 5, (f"MCS-150 filed {age_years:.1f} years ago — past the 2-year filing cycle.")
    return 0, f"MCS-150 is current (filed {age_years:.1f} years ago)."


def _risk_level(score: int) -> str:
    """Map a numeric risk score to a named risk level."""
    if score <= 25:
        return "low"
    if score <= 50:
        return "medium"
    if score <= 75:
        return "elevated"
    return "high"


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def _risk_score(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Calculate a composite risk score for a carrier.

    Fetches carrier data from the SearchCarriers API and evaluates
    multiple risk dimensions. Returns a score from 0 (safest) to 100
    (highest risk), a named risk level, factor-by-factor breakdown, and
    a carrier snapshot for downstream pipeline stages.
    """
    dot: str = str(arguments["dot_number"]).strip()

    search_url = f"{SEARCH_BASE}/search"

    async with httpx.AsyncClient(headers=_auth_headers(api_key), timeout=REQUEST_TIMEOUT) as client:
        search_task = _get(client, search_url, params={"dotNumber": dot, "perPage": 1})
        authorities_task = _get(client, f"{API_BASE}/company/{dot}/authorities")
        insurances_task = _get(client, f"{API_BASE}/company/{dot}/insurances")

        results = await asyncio.gather(
            search_task, authorities_task, insurances_task, return_exceptions=True
        )

    search_result, authorities_result, insurances_result = results

    if isinstance(search_result, Exception):
        return _error_payload("api_error", f"Carrier lookup failed: {search_result}")

    carrier = normalize_v3_company(_extract_carrier(search_result))
    if not carrier:
        return _error_payload("not_found", f"No carrier found for DOT {dot}.")

    authorities = (
        [] if isinstance(authorities_result, Exception) else _extract_list(authorities_result)
    )
    insurances = (
        [] if isinstance(insurances_result, Exception) else _extract_list(insurances_result)
    )

    # Evaluate each risk dimension.
    factors: list[dict[str, Any]] = []
    total_score = 0

    def _add_factor(
        name: str,
        penalty: int,
        description: str,
        weight: str = "medium",
    ) -> None:
        nonlocal total_score
        total_score += penalty
        factors.append(
            {
                "factor": name,
                "penalty": penalty,
                "description": description,
                "weight": weight,
            }
        )

    op_penalty, op_desc = _score_operating_status(carrier)
    _add_factor("operating_status", op_penalty, op_desc, weight="high")

    rating_penalty, rating_desc = _score_safety_rating(carrier)
    _add_factor("safety_rating", rating_penalty, rating_desc, weight="high")

    oos_penalty, oos_desc = _score_oos_rate(carrier)
    _add_factor("oos_rate", oos_penalty, oos_desc, weight="medium")

    crash_penalty, crash_desc = _score_crash_rate(carrier)
    _add_factor("crash_rate", crash_penalty, crash_desc, weight="medium")

    ins_penalty, ins_desc = _score_insurance(insurances)
    _add_factor("insurance_status", ins_penalty, ins_desc, weight="high")

    auth_penalty, auth_desc = _score_authority(authorities)
    _add_factor("authority_status", auth_penalty, auth_desc, weight="high")

    mcs_penalty, mcs_desc = _score_mcs150(carrier)
    _add_factor("mcs150_age", mcs_penalty, mcs_desc, weight="low")

    # Clamp score to [0, 100].
    risk_score = min(max(total_score, 0), 100)
    level = _risk_level(risk_score)

    return {
        "dot_number": dot,
        "risk_score": risk_score,
        "risk_level": level,
        "factors": sorted(factors, key=lambda f: f["penalty"], reverse=True),
        "carrier_snapshot": {
            "legalName": carrier.get("legalName") or carrier.get("name"),
            "operatingStatus": carrier.get("operatingStatus"),
            "rating": carrier.get("rating") or carrier.get("safetyRating"),
            "totalDrivers": carrier.get("totalDrivers"),
            "totalPowerUnits": carrier.get("totalPowerUnits"),
            "oosRate": carrier.get("oosRate") or carrier.get("oosRateVehicle"),
            "crashTotal": carrier.get("crashTotal"),
            "inspectionTotal": carrier.get("inspectionTotal"),
            "mcs150Date": carrier.get("mcs150Date") or carrier.get("mcs150FormDate"),
        },
        "_pipeline": _pipeline_meta("risk_score", dot),
    }


async def _vetting_check(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Evaluate a carrier against a set of vetting rules.

    Each rule returns a status of ``pass``, ``review``, or ``fail``.
    The overall verdict is PASS when all rules pass, FAIL when any rule
    fails, and REVIEW when there are no failures but at least one review.

    The caller must provide the complete policy through ``rules``. This tool
    deliberately has no hidden default thresholds; use ``qualification_reports``
    when SearchCarriers owns the named qualification.
    """
    dot: str = str(arguments["dot_number"]).strip()
    rules: dict[str, Any] = arguments.get("rules") or {}
    missing_rules = sorted(VETTING_RULE_KEYS - set(rules))
    if missing_rules:
        return _error_payload(
            "invalid_policy",
            "vetting_check requires a complete caller-owned policy; "
            f"missing keys: {', '.join(missing_rules)}. Use qualification_reports "
            "for SearchCarriers named qualification results.",
        )

    search_url = f"{SEARCH_BASE}/search"

    async with httpx.AsyncClient(headers=_auth_headers(api_key), timeout=REQUEST_TIMEOUT) as client:
        search_task = _get(client, search_url, params={"dotNumber": dot, "perPage": 1})
        authorities_task = _get(client, f"{API_BASE}/company/{dot}/authorities")
        insurances_task = _get(client, f"{API_BASE}/company/{dot}/insurances")

        results = await asyncio.gather(
            search_task, authorities_task, insurances_task, return_exceptions=True
        )

    search_result, authorities_result, insurances_result = results

    if isinstance(search_result, Exception):
        return _error_payload("api_error", f"Carrier lookup failed: {search_result}")

    carrier = normalize_v3_company(_extract_carrier(search_result))
    if not carrier:
        return _error_payload("not_found", f"No carrier found for DOT {dot}.")

    authorities = (
        [] if isinstance(authorities_result, Exception) else _extract_list(authorities_result)
    )
    insurances = (
        [] if isinstance(insurances_result, Exception) else _extract_list(insurances_result)
    )

    rule_results: list[dict[str, Any]] = []

    def _rule(
        name: str,
        status: str,
        actual: Any,
        threshold: Any,
        message: str,
    ) -> None:
        """Append a rule result record."""
        rule_results.append(
            {
                "rule": name,
                "status": status,
                "actual": actual,
                "threshold": threshold,
                "message": message,
            }
        )

    # Rule 1: Operating status.
    op_status = str(carrier.get("operatingStatus") or "").lower()
    if "authorized" in op_status and "not" not in op_status:
        _rule(
            "operating_status",
            "pass",
            carrier.get("operatingStatus"),
            rules["operating_status"],
            "Carrier is currently authorized to operate.",
        )
    else:
        _rule(
            "operating_status",
            "fail",
            carrier.get("operatingStatus"),
            rules["operating_status"],
            f"Carrier is not authorized (status: {carrier.get('operatingStatus')!r}).",
        )

    # Rule 2: Insurance coverage minimum.
    # Uses max() across individual policy amounts — the $750K minimum applies
    # per-policy, not in aggregate across all policies.
    active_insurances = [
        ins for ins in insurances if str(ins.get("status") or "").lower() in ("active", "current")
    ]
    policy_amounts: list[float] = []
    for ins in active_insurances:
        try:
            coverage = float(ins.get("coverageTo") or ins.get("coverageFrom") or 0)
            if coverage > 0:
                policy_amounts.append(coverage)
        except (TypeError, ValueError):
            pass
    max_coverage = max(policy_amounts, default=0.0)

    min_coverage = float(rules["min_insurance_coverage"])
    if active_insurances and max_coverage >= min_coverage:
        _rule(
            "min_insurance_coverage",
            "pass",
            max_coverage,
            min_coverage,
            f"Highest single-policy coverage ${max_coverage:,.0f} meets the ${min_coverage:,.0f} minimum.",
        )
    elif active_insurances and max_coverage > 0:
        _rule(
            "min_insurance_coverage",
            "fail",
            max_coverage,
            min_coverage,
            f"Highest single-policy coverage ${max_coverage:,.0f} is below the ${min_coverage:,.0f} minimum.",
        )
    elif active_insurances:
        # Active policies exist but no parseable coverage amounts in API data.
        _rule(
            "min_insurance_coverage",
            "review",
            "coverage amounts unavailable",
            min_coverage,
            "Active policies found but coverage amounts could not be parsed — manual review required.",
        )
    else:
        _rule(
            "min_insurance_coverage",
            "fail",
            "no active policies",
            min_coverage,
            "No active insurance policies found.",
        )

    # Rule 3: OOS rate.
    try:
        oos_rate = float(carrier.get("oosRate") or carrier.get("oosRateVehicle") or -1)
    except (TypeError, ValueError):
        oos_rate = -1

    max_oos = float(rules["max_oos_rate"])
    if oos_rate < 0:
        _rule(
            "max_oos_rate",
            "review",
            "unavailable",
            f"<= {max_oos}%",
            "OOS rate data unavailable — manual review required.",
        )
    elif oos_rate <= max_oos:
        _rule(
            "max_oos_rate",
            "pass",
            f"{oos_rate:.1f}%",
            f"<= {max_oos}%",
            f"Vehicle OOS rate {oos_rate:.1f}% is within the {max_oos:.0f}% threshold.",
        )
    else:
        _rule(
            "max_oos_rate",
            "fail",
            f"{oos_rate:.1f}%",
            f"<= {max_oos}%",
            f"Vehicle OOS rate {oos_rate:.1f}% exceeds the {max_oos:.0f}% threshold.",
        )

    # Rule 4: Crash rate per power unit.
    try:
        crashes = float(carrier.get("crashTotal") or 0)
        power_units = float(carrier.get("totalPowerUnits") or 0)
        crash_rate = crashes / power_units if power_units > 0 else -1.0
    except (TypeError, ValueError, ZeroDivisionError):
        crash_rate = -1.0

    max_crash_rate = float(rules["max_crash_rate_per_pu"])
    if crash_rate < 0:
        _rule(
            "max_crash_rate_per_pu",
            "review",
            "unavailable",
            f"<= {max_crash_rate}",
            "Crash rate cannot be calculated — fleet size data unavailable.",
        )
    elif crash_rate <= max_crash_rate:
        _rule(
            "max_crash_rate_per_pu",
            "pass",
            f"{crash_rate:.3f}",
            f"<= {max_crash_rate}",
            f"Crash rate {crash_rate:.3f}/PU is within the {max_crash_rate} threshold.",
        )
    else:
        _rule(
            "max_crash_rate_per_pu",
            "fail",
            f"{crash_rate:.3f}",
            f"<= {max_crash_rate}",
            f"Crash rate {crash_rate:.3f}/PU exceeds the {max_crash_rate} threshold.",
        )

    # Rule 5: Active operating authority.
    active_authorities = [
        a
        for a in authorities
        if "active" in str(a.get("status") or "").lower()
        or "authorized" in str(a.get("status") or "").lower()
    ]
    if not authorities:
        _rule(
            "authority_active",
            "review",
            "no records",
            True,
            "No authority records returned — manual verification required.",
        )
    elif active_authorities:
        auth_types = [
            str(a.get("type") or a.get("authorityType") or "unknown") for a in active_authorities
        ]
        _rule(
            "authority_active",
            "pass",
            True,
            True,
            f"Active authority confirmed: {', '.join(auth_types)}.",
        )
    else:
        _rule(
            "authority_active",
            "fail",
            False,
            True,
            "No active operating authority found — all authorities are revoked or inactive.",
        )

    # Rule 6: MCS-150 currency.
    raw_mcs = carrier.get("mcs150Date") or carrier.get("mcs150FormDate")
    mcs_dt = _parse_date(str(raw_mcs) if raw_mcs else None)
    mcs_age = _years_since(mcs_dt)

    if mcs_age is None:
        _rule(
            "mcs150_current",
            "review",
            "unavailable",
            f"<= {MCS150_STALE_YEARS} years",
            "MCS-150 filing date not available — cannot confirm currency.",
        )
    elif mcs_age <= MCS150_STALE_YEARS:
        _rule(
            "mcs150_current",
            "pass",
            f"{mcs_age:.1f} years",
            f"<= {MCS150_STALE_YEARS} years",
            f"MCS-150 filed {mcs_age:.1f} years ago — within the 2-year filing cycle.",
        )
    else:
        _rule(
            "mcs150_current",
            "fail",
            f"{mcs_age:.1f} years",
            f"<= {MCS150_STALE_YEARS} years",
            f"MCS-150 is {mcs_age:.1f} years old — overdue for biennial re-filing.",
        )

    # Determine overall verdict.
    statuses = {r["status"] for r in rule_results}
    if "fail" in statuses:
        verdict = "FAIL"
    elif "review" in statuses:
        verdict = "REVIEW"
    else:
        verdict = "PASS"

    fail_count = sum(1 for r in rule_results if r["status"] == "fail")
    review_count = sum(1 for r in rule_results if r["status"] == "review")
    pass_count = sum(1 for r in rule_results if r["status"] == "pass")

    return {
        "dot_number": dot,
        "verdict": verdict,
        "rules_checked": len(rule_results),
        "summary": {
            "pass": pass_count,
            "review": review_count,
            "fail": fail_count,
        },
        "results": rule_results,
        "carrier_summary": {
            "legalName": carrier.get("legalName") or carrier.get("name"),
            "operatingStatus": carrier.get("operatingStatus"),
            "rating": carrier.get("rating") or carrier.get("safetyRating"),
            "totalPowerUnits": carrier.get("totalPowerUnits"),
            "totalDrivers": carrier.get("totalDrivers"),
        },
        "_pipeline": _pipeline_meta("vetting_check", dot),
    }


async def _qualification_reports(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Fetch SearchCarriers personal and team qualification results.

    The upstream service owns qualification names, criteria, evidence, and
    Pass/Review/Fail evaluation.  This wrapper intentionally preserves that
    response instead of translating it into the Risk Engine's legacy defaults.
    """
    dot = str(arguments["dot_number"]).strip()
    async with httpx.AsyncClient(headers=_auth_headers(api_key), timeout=REQUEST_TIMEOUT) as client:
        try:
            raw = await _get(
                client,
                f"{API_V2_BASE}/company/{dot}/qualification-reports",
            )
        except RuntimeError as exc:
            return _error_payload("api_error", str(exc))

    return {
        "dot_number": dot,
        "api_version": "v2",
        "qualification_reports": response_data(raw),
        "decision_owner": "upstream_named_qualification",
        "_pipeline": _pipeline_meta("qualification_reports", dot),
    }


async def _insurance_check(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Analyze insurance coverage depth and quality for a carrier.

    Examines active policy count, total declared coverage, near-term
    cancellation exposure, and any detected gaps or lapses.  Returns an
    overall status of ``adequate``, ``warning``, or ``critical``.
    """
    dot: str = str(arguments["dot_number"]).strip()

    async with httpx.AsyncClient(headers=_auth_headers(api_key), timeout=REQUEST_TIMEOUT) as client:
        try:
            raw = await _get(client, f"{API_BASE}/company/{dot}/insurances")
        except RuntimeError as exc:
            return _error_payload("api_error", str(exc))

    insurances = _extract_list(raw)
    now = _now_utc()

    active_policies: list[dict[str, Any]] = []
    lapsed_policies: list[dict[str, Any]] = []
    gaps: list[str] = []
    warnings: list[str] = []
    total_coverage = 0

    for ins in insurances:
        status = str(ins.get("status") or "").lower()
        is_active = status in ("active", "current")

        policy_record: dict[str, Any] = {
            "policyNumber": ins.get("policyNumber"),
            "type": ins.get("type") or ins.get("insuranceType"),
            "insurerName": ins.get("insurerName"),
            "status": ins.get("status"),
            "effectiveDate": ins.get("effectiveDate"),
            "cancellationDate": ins.get("cancellationDate"),
            "coverageFrom": ins.get("coverageFrom"),
            "coverageTo": ins.get("coverageTo"),
        }

        if is_active:
            # Accumulate coverage amount.
            try:
                coverage = float(ins.get("coverageTo") or ins.get("coverageFrom") or 0)
                total_coverage += coverage
                policy_record["coverage"] = coverage
            except (TypeError, ValueError):
                policy_record["coverage"] = None

            # Check for near-term cancellation.
            cancel_dt = _parse_date(ins.get("cancellationDate"))
            if cancel_dt:
                days_remaining = (cancel_dt - now).days
                if days_remaining < 0:
                    gaps.append(
                        f"Policy {ins.get('policyNumber') or 'unknown'} "
                        f"({ins.get('type') or 'unknown type'}) cancelled "
                        f"{abs(days_remaining)} days ago."
                    )
                elif days_remaining <= 30:
                    warnings.append(
                        f"Policy {ins.get('policyNumber') or 'unknown'} "
                        f"({ins.get('type') or 'unknown type'}) cancels in "
                        f"{days_remaining} days on {ins.get('cancellationDate')}."
                    )
                elif days_remaining <= 90:
                    warnings.append(
                        f"Policy {ins.get('policyNumber') or 'unknown'} "
                        f"({ins.get('type') or 'unknown type'}) cancels in "
                        f"{days_remaining} days — note for renewal tracking."
                    )

            active_policies.append(policy_record)
        else:
            # Check whether the lapse is recent (within 12 months).
            cancel_dt = _parse_date(ins.get("cancellationDate"))
            if cancel_dt:
                months_lapsed = (now - cancel_dt).days / 30
                if months_lapsed <= 12:
                    gaps.append(
                        f"Policy {ins.get('policyNumber') or 'unknown'} "
                        f"({ins.get('type') or 'unknown type'}) lapsed "
                        f"{months_lapsed:.0f} months ago."
                    )
            lapsed_policies.append(policy_record)

    # Check for minimum general freight coverage.
    if active_policies and total_coverage > 0:
        if total_coverage < MIN_GENERAL_FREIGHT_COVERAGE:
            warnings.append(
                f"Total active coverage ${total_coverage:,.0f} is below the FMCSA "
                f"general freight minimum of ${MIN_GENERAL_FREIGHT_COVERAGE:,.0f}."
            )

    # Coverage type checks — flag if no liability policy found.
    active_types = [str(p.get("type") or "").lower() for p in active_policies]
    has_liability = any("liab" in t or "public" in t for t in active_types)
    if active_policies and not has_liability:
        warnings.append(
            "No liability insurance policy identified among active policies — "
            "verify coverage types manually."
        )

    # Determine overall status.
    if not active_policies or gaps:
        overall_status = "critical"
    elif warnings:
        overall_status = "warning"
    else:
        overall_status = "adequate"

    return {
        "dot_number": dot,
        "status": overall_status,
        "active_policies": active_policies,
        "lapsed_policies": lapsed_policies,
        "total_coverage": total_coverage,
        "active_policy_count": len(active_policies),
        "gaps": gaps,
        "warnings": warnings,
        "_pipeline": _pipeline_meta("insurance_check", dot),
    }


async def _compliance_audit(arguments: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Audit a carrier's regulatory compliance posture.

    Checks MCS-150 filing freshness, operating authority status, and
    authority type coverage (common, contract, broker, hazmat).  Returns
    a list of granular compliance checks, each with a status of
    ``pass``, ``warning``, or ``fail``.
    """
    dot: str = str(arguments["dot_number"]).strip()

    search_url = f"{SEARCH_BASE}/search"

    async with httpx.AsyncClient(headers=_auth_headers(api_key), timeout=REQUEST_TIMEOUT) as client:
        search_task = _get(client, search_url, params={"dotNumber": dot, "perPage": 1})
        authorities_task = _get(client, f"{API_BASE}/company/{dot}/authorities")

        results = await asyncio.gather(search_task, authorities_task, return_exceptions=True)

    search_result, authorities_result = results

    if isinstance(search_result, Exception):
        return _error_payload("api_error", f"Carrier lookup failed: {search_result}")

    carrier = normalize_v3_company(_extract_carrier(search_result))
    if not carrier:
        return _error_payload("not_found", f"No carrier found for DOT {dot}.")

    authorities = (
        [] if isinstance(authorities_result, Exception) else _extract_list(authorities_result)
    )

    checks: list[dict[str, Any]] = []

    def _check(
        name: str,
        status: str,
        message: str,
        detail: Any = None,
    ) -> None:
        record: dict[str, Any] = {
            "check": name,
            "status": status,
            "message": message,
        }
        if detail is not None:
            record["detail"] = detail
        checks.append(record)

    # Check 1: MCS-150 filing freshness.
    raw_mcs = carrier.get("mcs150Date") or carrier.get("mcs150FormDate")
    mcs_dt = _parse_date(str(raw_mcs) if raw_mcs else None)
    mcs_age = _years_since(mcs_dt)
    mcs_info: dict[str, Any] = {
        "filingDate": raw_mcs,
        "ageYears": round(mcs_age, 2) if mcs_age is not None else None,
        "isCurrentWithinTwoYears": (mcs_age is not None and mcs_age <= MCS150_STALE_YEARS),
    }

    if mcs_age is None:
        _check(
            "mcs150_filing",
            "warning",
            "MCS-150 filing date not available — cannot verify biennial filing compliance.",
        )
    elif mcs_age > MCS150_CRITICAL_YEARS:
        _check(
            "mcs150_filing",
            "fail",
            f"MCS-150 is {mcs_age:.1f} years old — critically overdue. "
            "FMCSA requires biennial filing under 49 CFR 390.19.",
            {"age_years": round(mcs_age, 2), "threshold_years": MCS150_STALE_YEARS},
        )
    elif mcs_age > MCS150_STALE_YEARS:
        _check(
            "mcs150_filing",
            "warning",
            f"MCS-150 is {mcs_age:.1f} years old — past the 2-year cycle. "
            "Carrier should have filed a renewal.",
            {"age_years": round(mcs_age, 2), "threshold_years": MCS150_STALE_YEARS},
        )
    else:
        _check(
            "mcs150_filing",
            "pass",
            f"MCS-150 is current (filed {mcs_age:.1f} years ago).",
        )

    # Check 2: Operating status.
    op_status = str(carrier.get("operatingStatus") or "").strip()
    op_lower = op_status.lower()
    if "authorized" in op_lower and "not" not in op_lower:
        _check(
            "operating_status",
            "pass",
            f"Operating status is authorized ({op_status!r}).",
        )
    elif op_status:
        _check(
            "operating_status",
            "fail",
            f"Operating status is not authorized: {op_status!r}.",
            {"status": op_status},
        )
    else:
        _check(
            "operating_status",
            "warning",
            "Operating status not available in carrier record.",
        )

    # Check 3: Active operating authority presence.
    active_auths = [
        a
        for a in authorities
        if "active" in str(a.get("status") or "").lower()
        or "authorized" in str(a.get("status") or "").lower()
    ]
    if not authorities:
        _check(
            "operating_authority",
            "warning",
            "No operating authority records returned — manual verification needed.",
        )
    elif active_auths:
        auth_types = [
            str(a.get("type") or a.get("authorityType") or "unknown") for a in active_auths
        ]
        _check(
            "operating_authority",
            "pass",
            f"Active operating authority on file: {', '.join(auth_types)}.",
        )
    else:
        revoked = [str(a.get("type") or a.get("authorityType") or "unknown") for a in authorities]
        _check(
            "operating_authority",
            "fail",
            f"No active operating authority — revoked/inactive types: {', '.join(revoked)}.",
            {"revoked_types": revoked},
        )

    # Check 4: Common carrier authority.
    common_auths = [
        a
        for a in authorities
        if "common" in str(a.get("type") or a.get("authorityType") or "").lower()
    ]
    active_common = [a for a in common_auths if "active" in str(a.get("status") or "").lower()]
    if active_common:
        _check(
            "common_carrier_authority",
            "pass",
            "Active common carrier authority confirmed.",
        )
    elif common_auths:
        _check(
            "common_carrier_authority",
            "warning",
            "Common carrier authority on record but not active.",
        )
    else:
        _check(
            "common_carrier_authority",
            "warning",
            "No common carrier authority found — may be contract-only or broker.",
        )

    # Check 5: Contract carrier authority.
    contract_auths = [
        a
        for a in authorities
        if "contract" in str(a.get("type") or a.get("authorityType") or "").lower()
    ]
    active_contract = [a for a in contract_auths if "active" in str(a.get("status") or "").lower()]
    if active_contract:
        _check(
            "contract_carrier_authority",
            "pass",
            "Active contract carrier authority confirmed.",
        )
    elif contract_auths:
        _check(
            "contract_carrier_authority",
            "warning",
            "Contract carrier authority on record but not active.",
        )
    else:
        _check(
            "contract_carrier_authority",
            "warning",
            "No contract carrier authority found.",
        )

    # Check 6: Broker authority (informational).
    broker_auths = [
        a
        for a in authorities
        if "broker" in str(a.get("type") or a.get("authorityType") or "").lower()
    ]
    active_broker = [a for a in broker_auths if "active" in str(a.get("status") or "").lower()]
    if active_broker:
        _check(
            "broker_authority",
            "pass",
            "Active broker authority on file.",
        )
    elif broker_auths:
        _check(
            "broker_authority",
            "warning",
            "Broker authority on record but not active.",
        )
    # No broker authority is normal for pure carriers; skip rather than flag.

    # Check 7: Hazmat authority (if any hazmat record exists).
    hazmat_auths = [
        a
        for a in authorities
        if "hazmat" in str(a.get("type") or a.get("authorityType") or "").lower()
        or "hm" in str(a.get("type") or a.get("authorityType") or "").lower()
    ]
    if hazmat_auths:
        active_hazmat = [a for a in hazmat_auths if "active" in str(a.get("status") or "").lower()]
        if active_hazmat:
            _check(
                "hazmat_authority",
                "pass",
                "Active hazmat authority on file — carrier is authorized for hazardous materials.",
            )
        else:
            _check(
                "hazmat_authority",
                "fail",
                "Hazmat authority records exist but none are active — "
                "carrier must not transport hazardous materials.",
            )

    # Determine overall compliance status.
    check_statuses = {c["status"] for c in checks}
    if "fail" in check_statuses:
        compliance_status = "critical"
    elif "warning" in check_statuses:
        compliance_status = "issues"
    else:
        compliance_status = "compliant"

    # Build normalized authority list for the response.
    authority_records = [
        {
            "type": a.get("type") or a.get("authorityType"),
            "status": a.get("status"),
            "grantDate": a.get("grantDate") or a.get("startDate"),
            "revokedDate": a.get("revokedDate") or a.get("endDate"),
        }
        for a in authorities
    ]

    fail_count = sum(1 for c in checks if c["status"] == "fail")
    warning_count = sum(1 for c in checks if c["status"] == "warning")
    pass_count = sum(1 for c in checks if c["status"] == "pass")

    return {
        "dot_number": dot,
        "compliance_status": compliance_status,
        "summary": {
            "pass": pass_count,
            "warning": warning_count,
            "fail": fail_count,
        },
        "checks": checks,
        "mcs150": mcs_info,
        "authorities": authority_records,
        "carrier_name": carrier.get("legalName") or carrier.get("name"),
        "_pipeline": _pipeline_meta("compliance_audit", dot),
    }


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

_TOOL_DEFINITIONS: list[Tool] = [
    Tool(
        name="risk_score",
        description=(
            "Calculate a disclosed legacy advisory score (0-100, lower is safer) for a carrier "
            "identified by DOT number. Evaluates operating status, safety rating, OOS "
            "rates vs national averages, crash rate per power unit, insurance status, "
            "operating authority, and MCS-150 filing age. Returns a named risk level "
            "(low / medium / elevated / high) and a factor-by-factor breakdown. "
            "Min tier: pro."
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
        name="vetting_check",
        description=(
            "Evaluate a carrier against a complete caller-supplied rule set and return a "
            "PASS / REVIEW / FAIL verdict. This tool has no hidden default thresholds; "
            "prefer qualification_reports for SearchCarriers named qualifications. "
            "Min tier: proplus."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "dot_number": {
                    "type": "string",
                    "description": "The carrier's USDOT number.",
                },
                "rules": {
                    "type": "object",
                    "description": (
                        "Required complete caller-owned policy. Accepted keys: "
                        "operating_status (str), min_insurance_coverage (number), "
                        "max_oos_rate (number, percent), max_crash_rate_per_pu (number), "
                        "authority_active (bool), mcs150_current (bool)."
                    ),
                },
            },
            "required": ["dot_number", "rules"],
        },
    ),
    Tool(
        name="qualification_reports",
        description=(
            "Fetch SearchCarriers personal and team qualification results for a DOT "
            "number from the API v2 qualification-reports endpoint. Preserves upstream "
            "Pass / Review / Fail evidence and named criteria without applying the "
            "Risk Engine's legacy default thresholds. Min tier: proplus."
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
        name="insurance_check",
        description=(
            "Analyze insurance coverage for a carrier by DOT number. Returns active "
            "and lapsed policies, total declared coverage amount, any near-term "
            "cancellations (within 30 or 90 days), recent gaps/lapses, and an overall "
            "status of adequate / warning / critical. "
            "Min tier: pro."
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
        name="compliance_audit",
        description=(
            "Audit a carrier's regulatory compliance posture by DOT number. Checks MCS-150 "
            "biennial filing currency, operating status, active operating authority, and "
            "authority type coverage (common, contract, broker, hazmat). Returns individual "
            "check results and an overall compliance status of compliant / issues / critical. "
            "Min tier: pro."
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
    "risk_score": _risk_score,
    "vetting_check": _vetting_check,
    "qualification_reports": _qualification_reports,
    "insurance_check": _insurance_check,
    "compliance_audit": _compliance_audit,
}


async def serve() -> None:
    """Entry point: create the MCP server and run it over stdio."""
    # Fail fast if the API key is absent.
    try:
        api_key = _api_key()
    except RuntimeError as exc:
        print(f"[risk-engine] Startup error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Read caller tier from environment (optional; defaults to "free").
    user_tier = os.environ.get("SEARCHCARRIERS_TIER", "free").strip().lower()

    server = Server("searchcarriers-risk-engine")

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
