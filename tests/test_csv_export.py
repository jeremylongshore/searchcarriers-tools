"""Tests for curated CSV export.

Verifies that CSV output has human-readable headers, no nested JSON,
and proper formatting.
"""

import csv
import io
import json
import sys
from pathlib import Path

import pytest

_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root))
sys.path.insert(
    0,
    str(_repo_root / "plugins" / "searchcarriers-ops-reporter" / "scripts"),
)

from csv_export import generate_carrier_csv
from field_map import normalize_authority, normalize_carrier, normalize_insurance

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def real_api_data():
    return json.loads((FIXTURES_DIR / "carrier_nested.json").read_text())


@pytest.fixture
def normalized_data(real_api_data):
    carrier = normalize_carrier(real_api_data["basics"])
    auths = normalize_authority(real_api_data["authorities"])
    inss = normalize_insurance(real_api_data["insurances"])
    return carrier, auths, inss


class TestCuratedCSV:
    """Tests for curated CSV output."""

    def test_has_expected_headers(self, normalized_data):
        carrier, auths, inss = normalized_data
        output = generate_carrier_csv(carrier, auths, inss)
        reader = csv.reader(io.StringIO(output))
        headers = next(reader)
        assert "DOT Number" in headers
        assert "Legal Name" in headers
        assert "Operating Status" in headers
        assert "Phone" in headers
        assert "Email" in headers
        assert "Power Units" in headers

    def test_no_search_data_column(self, normalized_data):
        carrier, auths, inss = normalized_data
        output = generate_carrier_csv(carrier, auths, inss)
        assert "search_data" not in output

    def test_no_nested_json(self, normalized_data):
        carrier, auths, inss = normalized_data
        output = generate_carrier_csv(carrier, auths, inss)
        # Nested JSON would have { or [ outside of quoted fields
        reader = csv.reader(io.StringIO(output))
        for row in reader:
            for cell in row:
                # Cells should not contain raw JSON objects
                stripped = cell.strip()
                if stripped.startswith("{") or stripped.startswith("[{"):
                    pytest.fail(f"Found nested JSON in CSV: {cell!r}")

    def test_coverage_formatted_as_currency(self, normalized_data):
        carrier, auths, inss = normalized_data
        output = generate_carrier_csv(carrier, auths, inss)
        # BIPD coverage of $750,000 should appear as currency
        assert "$750,000" in output

    def test_lists_joined_with_semicolons(self, normalized_data):
        carrier, auths, inss = normalized_data
        output = generate_carrier_csv(carrier, auths, inss)
        # Cargo types should be joined with semicolons
        assert "General Freight; Grain/Feed/Hay; Dry Bulk" in output

    def test_column_count_reasonable(self, normalized_data):
        carrier, auths, inss = normalized_data
        output = generate_carrier_csv(carrier, auths, inss)
        reader = csv.reader(io.StringIO(output))
        headers = next(reader)
        # Should have ~22 curated columns, not 143
        assert len(headers) <= 25, f"Too many columns: {len(headers)}"
        assert len(headers) >= 15, f"Too few columns: {len(headers)}"

    def test_valid_csv_parseable(self, normalized_data):
        carrier, auths, inss = normalized_data
        output = generate_carrier_csv(carrier, auths, inss)
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)
        # At least headers + 1 carrier row
        assert len(rows) >= 2

    def test_authority_section_present(self, normalized_data):
        carrier, auths, inss = normalized_data
        output = generate_carrier_csv(carrier, auths, inss)
        assert "Authority Type" in output
        assert "Contract" in output

    def test_insurance_section_present(self, normalized_data):
        carrier, auths, inss = normalized_data
        output = generate_carrier_csv(carrier, auths, inss)
        assert "Insurance Type" in output
        assert "BIPD" in output
