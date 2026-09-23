"""Current SearchCarriers API routing and response normalization.

SearchCarriers exposes capabilities across three API versions.  Keep the
version choice in one module so individual MCP servers and skills do not drift:

* v3: search, company field selection, equipment, and crashes
* v2: qualification reports
* v1: SCAC/VIN lookup, paginated detail resources, export, and watches

The v3 normalizer adds the legacy aliases consumed by the existing analysis and
reporting code.  It never invents absent values; missing fields remain ``None``.
"""

from __future__ import annotations

from typing import Any

API_ORIGIN = "https://searchcarriers.com"
API_V1_BASE = f"{API_ORIGIN}/api/v1"
API_V2_BASE = f"{API_ORIGIN}/api/v2"
API_V3_BASE = f"{API_ORIGIN}/api/v3"

V3_COMPANY_SECTIONS = (
    "contact",
    "inspections",
    "safety",
    "oos_orders",
    "oos_percents",
    "authorities",
    "insurance",
    "equipment",
    "operation",
    "service_areas",
    "risk_factors",
    "basic_scores",
    "vetting_report",
)

# Public API v3 search filters.  The MCP layer accepts Python-friendly names
# and this table is the single translation point to the published query names.
# Keep this list synchronized with API-DISCOVERY.md and the route-contract tests.
V3_SEARCH_FILTERS = {
    "company_types": "companyTypes[]",
    "radius_zipcode": "radiusZipcode",
    "radius_miles": "radiusMiles",
    "min_power_units": "minPowerUnits",
    "max_power_units": "maxPowerUnits",
    "min_trailers": "minTrailers",
    "max_trailers": "maxTrailers",
    "safety_score_present": "safetyScorePresent",
    "min_bipd_coverage": "minBipdCoverage",
    "max_bipd_coverage": "maxBipdCoverage",
    "cargo_insurance_present": "cargoInsurancePresent",
    "dot_registered_since": "dotRegisteredSince",
    "dot_registered_before": "dotRegisteredBefore",
    "latest_authority_granted_since": "latestAuthorityGrantedSince",
    "latest_authority_granted_before": "latestAuthorityGrantedBefore",
    "min_authority_age": "minAuthorityAge",
    "max_authority_age": "maxAuthorityAge",
    "include_authorities": "includeAuthorities[]",
    "exclude_authorities": "excludeAuthorities[]",
    "include_operation_types": "includeOperationTypes[]",
    "exclude_operation_types": "excludeOperationTypes[]",
    "include_equipment_types": "includeEquipmentTypes[]",
    "include_cargo_carried": "includeCargoCarried[]",
    "lane_origin_state": "laneOriginState",
    "lane_origin_county_geoid": "laneOriginCountyGeoid",
    "lane_origin_latitude": "laneOriginLatitude",
    "lane_origin_longitude": "laneOriginLongitude",
    "lane_origin_radius_miles": "laneOriginRadiusMiles",
    "lane_destination_state": "laneDestinationState",
    "lane_destination_county_geoid": "laneDestinationCountyGeoid",
    "lane_destination_latitude": "laneDestinationLatitude",
    "lane_destination_longitude": "laneDestinationLongitude",
    "lane_destination_radius_miles": "laneDestinationRadiusMiles",
}


def company_fields(*sections: str) -> dict[str, str]:
    """Return the v3 ``fields`` parameter after validating section names."""
    selected = sections or V3_COMPANY_SECTIONS
    unknown = sorted(set(selected) - set(V3_COMPANY_SECTIONS))
    if unknown:
        raise ValueError(f"Unknown v3 company field sections: {', '.join(unknown)}")
    return {"fields": ",".join(selected)}


def response_data(payload: Any) -> Any:
    """Unwrap a SearchCarriers ``data`` envelope when present."""
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def data_list(payload: Any) -> list[dict[str, Any]]:
    """Return an enveloped list without treating malformed payloads as empty."""
    value = response_data(payload)
    if not isinstance(value, list):
        raise ValueError("SearchCarriers response did not contain a data list")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError("SearchCarriers data list contained a non-object item")
    return value


def company_object(payload: Any) -> dict[str, Any]:
    """Return an enveloped company object and fail loudly on contract drift."""
    value = response_data(payload)
    if not isinstance(value, dict):
        raise ValueError("SearchCarriers response did not contain a company object")
    return value


def normalize_v3_company(payload: Any) -> dict[str, Any]:
    """Add stable legacy aliases to a v3 company object.

    Existing risk and reporting functions predate v3 and consume camelCase
    fields.  Keeping the aliases here permits a staged migration while the raw
    nested v3 sections remain available to new callers.
    """
    company = dict(company_object(payload))
    if not company:
        return {}
    safety = company.get("safety") if isinstance(company.get("safety"), dict) else {}
    operation = company.get("operation") if isinstance(company.get("operation"), dict) else {}
    contact = company.get("contact") if isinstance(company.get("contact"), dict) else {}
    physical = (
        company.get("physical_address") if isinstance(company.get("physical_address"), dict) else {}
    )

    aliases = {
        "dotNumber": company.get("dot_number"),
        "legalName": company.get("legal_name"),
        "dbaName": company.get("dba_name"),
        "operatingStatus": company.get("dot_status"),
        "totalPowerUnits": company.get("power_units"),
        "inspectionTotal": safety.get("total_inspections"),
        "crashTotal": safety.get("total_crashes"),
        "safetyRating": safety.get("safety_rating"),
        "rating": safety.get("safety_rating"),
        "oosRate": safety.get("driver_oos_rate"),
        "oosRateDriver": safety.get("driver_oos_rate"),
        "oosRateVehicle": safety.get("vehicle_oos_rate"),
        "cargo_carried": operation.get("cargo_carried"),
        "operation_classifications": operation.get("operation_classifications"),
        "carrierType": operation.get("entity_types"),
        "phone": contact.get("phone"),
        "email": contact.get("email_address"),
        "phyStreet": physical.get("street"),
        "phyCity": physical.get("city"),
        "phyState": physical.get("state"),
        "phyZip": physical.get("zip"),
    }
    for key, value in aliases.items():
        if key not in company:
            company[key] = value
    return company


def v3_search_params(
    query: str = "",
    search_type: str = "filters",
    *,
    page: int = 1,
    per_page: int = 10,
    state: str | None = None,
    city: str | None = None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map public search intent to parameters accepted by API v3."""
    mapping = {
        "dot": "dotNumber",
        "mc": "docketNumber",
        "name": "superSearchTerm",
        "text": "superSearchTerm",
    }
    if search_type not in {*mapping, "filters"}:
        raise ValueError(f"Unsupported v3 search type: {search_type}")
    params: dict[str, Any] = {
        "page": page,
        "perPage": per_page,
    }
    if search_type != "filters":
        if not query:
            raise ValueError("A query is required for identifier or text search")
        params[mapping[search_type]] = query
    if state:
        params["addressState"] = state.upper()
    if city:
        params["addressCity"] = city
    for public_name, value in (filters or {}).items():
        if value is None or value == "" or value == []:
            continue
        api_name = V3_SEARCH_FILTERS.get(public_name)
        if api_name is None:
            raise ValueError(f"Unsupported v3 search filter: {public_name}")
        params[api_name] = value
    return params
