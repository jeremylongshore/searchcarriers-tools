"""Field mapping and normalization for SearchCarriers API data.

The real API returns snake_case field names (e.g. ``legal_name``, ``status_code``,
``power_units``) while test fixtures use camelCase (``legalName``, ``operatingStatus``,
``totalPowerUnits``).  This module normalizes both shapes into a consistent internal
representation so handlers never produce N/A for fields that actually exist.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Status / code translation maps
# ---------------------------------------------------------------------------

STATUS_CODE_MAP: dict[str, str] = {
    "A": "Authorized",
    "N": "Not Authorized",
    "R": "Revoked",
    "I": "Inactive",
    "O": "Out of Service",
    "C": "Conditional",
}

AUTHORITY_STAT_MAP: dict[str, str] = {
    "A": "Active",
    "N": "Not Active",
    "R": "Revoked",
    "P": "Pending",
    "I": "Inactive",
}

INSURANCE_TYPE_MAP: dict[str, str] = {
    "1": "BIPD",
    "2": "Cargo",
    "3": "Bond",
    "4": "Trust Fund",
}

CARGO_CODE_MAP: dict[str, str] = {
    "genfreight": "General Freight",
    "household": "Household Goods",
    "metalsheet": "Metal/Sheets/Coils",
    "motoveh": "Motor Vehicles",
    "drivetow": "Drive-Away/Tow-Away",
    "logpole": "Logs/Poles/Lumber",
    "bldgmat": "Building Materials",
    "mobilehome": "Mobile Homes",
    "machlrg": "Machinery/Large Objects",
    "produce": "Fresh Produce",
    "liqgas": "Liquids/Gases",
    "intermodal": "Intermodal Containers",
    "passengers": "Passengers",
    "oilfield": "Oilfield Equipment",
    "livestock": "Livestock",
    "grainfeed": "Grain/Feed/Hay",
    "coalcoke": "Coal/Coke",
    "meat": "Meat",
    "garbage": "Garbage/Refuse",
    "usmail": "US Mail",
    "chem": "Chemicals",
    "drybulk": "Dry Bulk",
    "coldfood": "Refrigerated Food",
    "beverages": "Beverages",
    "paperprod": "Paper Products",
    "utility": "Utilities",
    "farmsupp": "Farm Supplies",
    "construct": "Construction",
    "waterwell": "Water Well",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _first(*candidates: Any) -> Any:
    """Return the first truthy value from *candidates*, or ``None``."""
    for v in candidates:
        if v is not None and str(v).strip() != "":
            return v
    return None


def _to_int(val: Any) -> int | None:
    """Coerce *val* to int, returning ``None`` on failure."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _format_phone(raw: Any) -> str | None:
    """Format a 10-digit phone string as (XXX) XXX-XXXX."""
    if not raw:
        return None
    digits = "".join(c for c in str(raw) if c.isdigit())
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    if len(digits) == 11 and digits[0] == "1":
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return str(raw)


# ---------------------------------------------------------------------------
# normalize_carrier
# ---------------------------------------------------------------------------


def normalize_carrier(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw carrier record to a consistent internal shape.

    Handles both real API snake_case and fixture camelCase field names.
    """
    # Identity
    dot = str(_first(raw.get("dot_number"), raw.get("dotNumber")) or "")
    mc = str(_first(raw.get("mc_number"), raw.get("mcNumber")) or "")
    legal_name = _first(raw.get("legal_name"), raw.get("legalName")) or ""
    dba = _first(raw.get("dba_name"), raw.get("dbaName")) or ""

    # Status — real API uses single-letter status_code, fixtures use full words
    raw_status = _first(raw.get("status_code"), raw.get("operatingStatus")) or ""
    operating_status = STATUS_CODE_MAP.get(str(raw_status).strip(), str(raw_status))

    # Entity / operation type
    entity_type = (
        _first(
            raw.get("entityType"),
            raw.get("carrierType"),
            raw.get("business_org_desc"),
        )
        or ""
    )

    # Address — real API uses phy_street etc, fixtures use phyStreet
    street = _first(raw.get("phy_street"), raw.get("phyStreet"), raw.get("street")) or ""
    city = _first(raw.get("phy_city"), raw.get("phyCity"), raw.get("city")) or ""
    state = _first(raw.get("phy_state"), raw.get("phyState"), raw.get("state")) or ""
    zipcode = _first(raw.get("phy_zip"), raw.get("phyZip"), raw.get("zip")) or ""
    address_parts = [p for p in [street, city, state, zipcode] if p]
    address = ", ".join(address_parts) if address_parts else ""

    # Contact
    phone_raw = _first(raw.get("phone"), raw.get("telephone"))
    phone = _format_phone(phone_raw) or str(phone_raw or "")
    email = str(_first(raw.get("email_address"), raw.get("email")) or "")

    # Fleet
    power_units = _to_int(_first(raw.get("power_units"), raw.get("totalPowerUnits")))
    total_drivers = _to_int(_first(raw.get("total_drivers"), raw.get("totalDrivers")))

    # Safety
    safety_rating = str(
        _first(raw.get("safety_rating"), raw.get("rating"), raw.get("safetyRating")) or ""
    )
    if not safety_rating:
        safety_rating = "Not Rated"

    crash_total = _to_int(_first(raw.get("crashTotal"), raw.get("crashes")))
    inspection_total = _to_int(_first(raw.get("inspectionTotal"), raw.get("inspections")))
    oos_rate_vehicle = _first(raw.get("oosRate"), raw.get("oosRateVehicle"))
    oos_rate_driver = raw.get("oosRateDriver")

    # MCS-150
    mcs150_date = str(
        _first(raw.get("mcs150_date"), raw.get("mcs150Date"), raw.get("mcs150FormDate")) or ""
    )

    # Cargo
    cargo_carried = raw.get("cargo_carried") or []
    if isinstance(cargo_carried, list):
        cargo_types = [CARGO_CODE_MAP.get(c, c) for c in cargo_carried]
    else:
        cargo_types = []

    # Officers
    company_officers = raw.get("company_officers") or []
    if not company_officers:
        o1 = raw.get("company_officer_1") or ""
        o2 = raw.get("company_officer_2") or ""
        company_officers = [o for o in [o1, o2] if o]

    # Operation classifications
    op_class = raw.get("operation_classifications") or []
    if isinstance(op_class, str):
        import json as _json

        try:
            op_class = _json.loads(op_class)
        except (ValueError, TypeError):
            op_class = [op_class]

    return {
        "dot_number": dot,
        "mc_number": mc,
        "legal_name": legal_name,
        "dba_name": dba,
        "operating_status": operating_status,
        "entity_type": entity_type,
        "address": address,
        "street": street,
        "city": city,
        "state": state,
        "zip": zipcode,
        "phone": phone,
        "email": email,
        "power_units": power_units,
        "total_drivers": total_drivers,
        "safety_rating": safety_rating,
        "crash_total": crash_total,
        "inspection_total": inspection_total,
        "oos_rate_vehicle": oos_rate_vehicle,
        "oos_rate_driver": oos_rate_driver,
        "mcs150_date": mcs150_date,
        "cargo_types": cargo_types,
        "company_officers": company_officers,
        "operation_classifications": op_class,
    }


# ---------------------------------------------------------------------------
# normalize_authority
# ---------------------------------------------------------------------------


def normalize_authority(raw: Any) -> list[dict[str, Any]]:
    """Normalize authority data to a list of ``{type, status, docket_number}`` dicts.

    Handles two shapes:
    1. **Real API** — a single record with ``common_stat``, ``contract_stat``,
       ``broker_stat`` as single-letter codes.
    2. **Fixture** — separate records with ``type``/``authorityType`` and ``status``.
    """
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return []

    results: list[dict[str, Any]] = []

    for record in raw:
        # Real API shape: one record with multiple stat fields
        if "common_stat" in record or "contract_stat" in record or "broker_stat" in record:
            docket = str(record.get("docket_number") or "")
            for stat_field, auth_type in [
                ("common_stat", "Common"),
                ("contract_stat", "Contract"),
                ("broker_stat", "Broker"),
            ]:
                code = str(record.get(stat_field) or "").strip()
                if code:
                    status = AUTHORITY_STAT_MAP.get(code, code)
                    results.append(
                        {
                            "type": auth_type,
                            "status": status,
                            "docket_number": docket,
                        }
                    )
        else:
            # Fixture shape: already separated
            auth_type = str(_first(record.get("type"), record.get("authorityType")) or "Unknown")
            status = str(record.get("status") or "Unknown")
            docket = str(_first(record.get("docket_number"), record.get("docketNumber")) or "")
            granted = str(_first(record.get("grantedDate"), record.get("effectiveDate")) or "")
            results.append(
                {
                    "type": auth_type,
                    "status": status,
                    "docket_number": docket,
                    "granted_date": granted,
                }
            )

    return results


# ---------------------------------------------------------------------------
# normalize_insurance
# ---------------------------------------------------------------------------


def normalize_insurance(raw: Any) -> list[dict[str, Any]]:
    """Normalize insurance data to a list of clean dicts.

    Handles two shapes:
    1. **Real API** — ``ins_type_code``, ``max_cov_amount`` (in thousands),
       ``name_company``, ``policy_no``, ``effective_date``.
    2. **Fixture** — ``type``/``insuranceType``, ``coverage``/``coverageAmount``,
       ``insuranceCarrier``/``insurerName``, ``policyNumber``, ``effectiveDate``.
    """
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return []

    results: list[dict[str, Any]] = []

    for record in raw:
        # Detect shape by checking for real API fields
        if "ins_type_code" in record:
            # Real API shape
            type_code = str(record.get("ins_type_code") or "")
            ins_type = INSURANCE_TYPE_MAP.get(type_code, f"Type {type_code}")

            # max_cov_amount is in thousands (e.g. "00750" = $750,000)
            raw_amount = str(record.get("max_cov_amount") or "0").lstrip("0") or "0"
            try:
                coverage = int(raw_amount) * 1000
            except (TypeError, ValueError):
                coverage = 0

            insurer = str(record.get("name_company") or "")
            policy = str(record.get("policy_no") or "")
            effective = str(record.get("effective_date") or "")
            status = "Active" if coverage > 0 else "Inactive"

            results.append(
                {
                    "type": ins_type,
                    "status": status,
                    "coverage": coverage,
                    "policy_number": policy,
                    "insurer": insurer,
                    "effective_date": effective,
                }
            )
        else:
            # Fixture shape
            ins_type = str(_first(record.get("type"), record.get("insuranceType")) or "Unknown")
            coverage = record.get("coverage") or record.get("coverageAmount") or 0
            try:
                coverage = int(coverage)
            except (TypeError, ValueError):
                coverage = 0

            insurer = str(
                _first(
                    record.get("insuranceCarrier"),
                    record.get("insurerName"),
                    record.get("insurer"),
                )
                or ""
            )
            policy = str(_first(record.get("policyNumber"), record.get("policy_number")) or "")
            status = str(record.get("status") or "Unknown")
            effective = str(_first(record.get("effectiveDate"), record.get("inceptionDate")) or "")
            cancellation = str(
                _first(record.get("cancellationDate"), record.get("expirationDate")) or ""
            )

            results.append(
                {
                    "type": ins_type,
                    "status": status,
                    "coverage": coverage,
                    "policy_number": policy,
                    "insurer": insurer,
                    "effective_date": effective,
                    "cancellation_date": cancellation,
                }
            )

    return results
