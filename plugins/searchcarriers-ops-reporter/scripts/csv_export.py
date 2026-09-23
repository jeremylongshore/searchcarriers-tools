"""Curated CSV export for carrier data.

Produces clean, human-readable CSVs that open correctly in Excel — no nested
JSON blobs, no 143-column raw dumps.  Uses normalized data from ``field_map``.
"""

from __future__ import annotations

import csv
import io
from typing import Any

# ---------------------------------------------------------------------------
# Column definitions — (internal_key, display_header)
# ---------------------------------------------------------------------------

CARRIER_COLUMNS: list[tuple[str, str]] = [
    ("dot_number", "DOT Number"),
    ("mc_number", "MC Number"),
    ("legal_name", "Legal Name"),
    ("dba_name", "DBA"),
    ("operating_status", "Operating Status"),
    ("entity_type", "Entity Type"),
    ("street", "Street"),
    ("city", "City"),
    ("state", "State"),
    ("zip", "Zip"),
    ("phone", "Phone"),
    ("email", "Email"),
    ("power_units", "Power Units"),
    ("total_drivers", "Drivers"),
    ("safety_rating", "Safety Rating"),
    ("crash_total", "Crashes"),
    ("inspection_total", "Inspections"),
    ("oos_rate_vehicle", "Vehicle OOS Rate"),
    ("oos_rate_driver", "Driver OOS Rate"),
    ("mcs150_date", "MCS-150 Date"),
    ("cargo_types", "Cargo Types"),
    ("company_officers", "Primary Officers"),
]

AUTHORITY_COLUMNS: list[tuple[str, str]] = [
    ("type", "Authority Type"),
    ("status", "Status"),
    ("docket_number", "Docket Number"),
]

INSURANCE_COLUMNS: list[tuple[str, str]] = [
    ("type", "Insurance Type"),
    ("status", "Status"),
    ("coverage", "Coverage Amount"),
    ("policy_number", "Policy Number"),
    ("insurer", "Insurance Company"),
    ("effective_date", "Effective Date"),
]


def _format_cell(key: str, value: Any) -> str:
    """Format a single cell value for CSV output."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    if key == "coverage" and isinstance(value, (int, float)) and value > 0:
        return f"${value:,.0f}"
    return str(value)


def generate_carrier_csv(
    carrier: dict[str, Any],
    authorities: list[dict[str, Any]] | None = None,
    insurances: list[dict[str, Any]] | None = None,
) -> str:
    """Generate a clean, curated CSV string from normalized carrier data.

    Args:
        carrier: Normalized carrier dict (output of ``normalize_carrier``).
        authorities: Normalized authority list (output of ``normalize_authority``).
        insurances: Normalized insurance list (output of ``normalize_insurance``).

    Returns:
        A CSV string with proper quoting, ready for Excel.
    """
    buf = io.StringIO()

    # --- Carrier section ---
    headers = [col[1] for col in CARRIER_COLUMNS]
    writer = csv.DictWriter(buf, fieldnames=headers, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    row = {col[1]: _format_cell(col[0], carrier.get(col[0])) for col in CARRIER_COLUMNS}
    writer.writerow(row)

    # --- Authorities section ---
    if authorities:
        buf.write("\n")
        auth_headers = [col[1] for col in AUTHORITY_COLUMNS]
        auth_writer = csv.DictWriter(buf, fieldnames=auth_headers, quoting=csv.QUOTE_ALL)
        auth_writer.writeheader()
        for auth in authorities:
            auth_row = {col[1]: _format_cell(col[0], auth.get(col[0])) for col in AUTHORITY_COLUMNS}
            auth_writer.writerow(auth_row)

    # --- Insurance section ---
    if insurances:
        buf.write("\n")
        ins_headers = [col[1] for col in INSURANCE_COLUMNS]
        ins_writer = csv.DictWriter(buf, fieldnames=ins_headers, quoting=csv.QUOTE_ALL)
        ins_writer.writeheader()
        for ins in insurances:
            ins_row = {col[1]: _format_cell(col[0], ins.get(col[0])) for col in INSURANCE_COLUMNS}
            ins_writer.writerow(ins_row)

    return buf.getvalue()
