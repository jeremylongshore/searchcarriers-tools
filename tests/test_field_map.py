"""Tests for field_map normalization functions.

Verifies that both camelCase fixtures and synthetic snake_case data
produce correct, consistent normalized output.
"""

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

from field_map import (
    _first,
    _format_phone,
    _to_int,
    normalize_authority,
    normalize_carrier,
    normalize_insurance,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestNormalizationPrimitives:
    """Malformed optional fields remain explicit instead of crashing normalization."""

    def test_first_skips_none_and_blank(self):
        assert _first(None, " ", "value") == "value"
        assert _first(None, "") is None

    def test_integer_conversion_is_bounded(self):
        assert _to_int("42") == 42
        assert _to_int(None) is None
        assert _to_int("unknown") is None

    def test_phone_formats_us_numbers_and_preserves_unknown_shapes(self):
        assert _format_phone("5550100000") == "(555) 010-0000"
        assert _format_phone("1-555-010-0000") == "(555) 010-0000"
        assert _format_phone("ext 12") == "ext 12"
        assert _format_phone(None) is None


@pytest.fixture
def camel_carrier():
    data = json.loads((FIXTURES_DIR / "carrier_primary.json").read_text())
    return data["data"][0]


@pytest.fixture
def real_api_data():
    return json.loads((FIXTURES_DIR / "carrier_nested.json").read_text())


# ---------------------------------------------------------------------------
# normalize_carrier
# ---------------------------------------------------------------------------


class TestNormalizeCarrierCamelCase:
    """Test with camelCase fixture data (existing test shape)."""

    def test_legal_name(self, camel_carrier):
        result = normalize_carrier(camel_carrier)
        assert result["legal_name"] == "EXAMPLE FREIGHT LLC"

    def test_operating_status(self, camel_carrier):
        result = normalize_carrier(camel_carrier)
        assert result["operating_status"] == "AUTHORIZED"

    def test_power_units(self, camel_carrier):
        result = normalize_carrier(camel_carrier)
        assert result["power_units"] == 120

    def test_total_drivers(self, camel_carrier):
        result = normalize_carrier(camel_carrier)
        assert result["total_drivers"] == 180

    def test_dot_number(self, camel_carrier):
        result = normalize_carrier(camel_carrier)
        assert result["dot_number"] == "1234567"

    def test_mc_number(self, camel_carrier):
        result = normalize_carrier(camel_carrier)
        assert result["mc_number"] == "765432"

    def test_safety_rating(self, camel_carrier):
        result = normalize_carrier(camel_carrier)
        assert result["safety_rating"] == "Satisfactory"


class TestNormalizeCarrierSnakeCase:
    """Test with synthetic snake_case data."""

    def test_legal_name(self, real_api_data):
        result = normalize_carrier(real_api_data["basics"])
        assert result["legal_name"] == "EXAMPLE FREIGHT LLC"

    def test_status_code_translated(self, real_api_data):
        result = normalize_carrier(real_api_data["basics"])
        assert result["operating_status"] == "Authorized"

    def test_power_units(self, real_api_data):
        result = normalize_carrier(real_api_data["basics"])
        assert result["power_units"] == 12

    def test_total_drivers(self, real_api_data):
        result = normalize_carrier(real_api_data["basics"])
        assert result["total_drivers"] == 18

    def test_address_assembled(self, real_api_data):
        result = normalize_carrier(real_api_data["basics"])
        assert "100 EXAMPLE WAY" in result["address"]
        assert "SAMPLE CITY" in result["address"]
        assert "TX" in result["address"]

    def test_phone_formatted(self, real_api_data):
        result = normalize_carrier(real_api_data["basics"])
        assert result["phone"] == "(555) 010-0000"

    def test_email(self, real_api_data):
        result = normalize_carrier(real_api_data["basics"])
        assert result["email"] == "ops@example.invalid"

    def test_entity_type(self, real_api_data):
        result = normalize_carrier(real_api_data["basics"])
        assert result["entity_type"] == "CORPORATION"

    def test_mcs150_date(self, real_api_data):
        result = normalize_carrier(real_api_data["basics"])
        assert "2025-06-15" in result["mcs150_date"]

    def test_cargo_types_translated(self, real_api_data):
        result = normalize_carrier(real_api_data["basics"])
        assert "General Freight" in result["cargo_types"]
        assert "Grain/Feed/Hay" in result["cargo_types"]
        assert "Dry Bulk" in result["cargo_types"]

    def test_company_officers(self, real_api_data):
        result = normalize_carrier(real_api_data["basics"])
        assert "ALEX EXAMPLE" in result["company_officers"]
        assert "CASEY EXAMPLE" in result["company_officers"]

    def test_no_none_for_populated_fields(self, real_api_data):
        """Key fields that exist in the API data should not be None."""
        result = normalize_carrier(real_api_data["basics"])
        for field in [
            "dot_number",
            "mc_number",
            "legal_name",
            "operating_status",
            "address",
            "phone",
            "email",
            "power_units",
            "total_drivers",
            "mcs150_date",
        ]:
            assert result[field] is not None and result[field] != "", (
                f"Field {field!r} should not be empty, got {result[field]!r}"
            )

    def test_operation_classification_parses_json_string(self):
        result = normalize_carrier({"operation_classifications": '["Interstate"]'})
        assert result["operation_classifications"] == ["Interstate"]

    def test_invalid_operation_classification_stays_visible(self):
        result = normalize_carrier({"operation_classifications": "not-json"})
        assert result["operation_classifications"] == ["not-json"]

    def test_non_list_cargo_is_rejected(self):
        result = normalize_carrier({"cargo_carried": "general_freight"})
        assert result["cargo_types"] == []


# ---------------------------------------------------------------------------
# normalize_authority
# ---------------------------------------------------------------------------


class TestNormalizeAuthoritySnakeCase:
    """Test with snake_case API shape (common_stat/contract_stat/broker_stat)."""

    def test_three_authority_types_from_single_record(self, real_api_data):
        result = normalize_authority(real_api_data["authorities"])
        types = [a["type"] for a in result]
        assert "Common" in types
        assert "Contract" in types
        assert "Broker" in types

    def test_status_translated(self, real_api_data):
        result = normalize_authority(real_api_data["authorities"])
        status_map = {a["type"]: a["status"] for a in result}
        assert status_map["Common"] == "Not Active"
        assert status_map["Contract"] == "Active"
        assert status_map["Broker"] == "Not Active"

    def test_docket_number(self, real_api_data):
        result = normalize_authority(real_api_data["authorities"])
        assert all(a["docket_number"] == "MC765432" for a in result)


class TestNormalizeAuthorityFixture:
    """Test with fixture shape (separate records with type/status)."""

    def test_preserves_fixture_shape(self):
        fixture = [
            {"type": "Common", "status": "Active", "grantedDate": "1985-03-15"},
            {"type": "Contract", "status": "Active", "grantedDate": "1990-07-22"},
        ]
        result = normalize_authority(fixture)
        assert len(result) == 2
        assert result[0]["type"] == "Common"
        assert result[0]["status"] == "Active"
        assert result[1]["type"] == "Contract"

    def test_non_collection_returns_empty(self):
        assert normalize_authority("invalid") == []

    def test_unknown_real_status_is_preserved(self):
        result = normalize_authority({"common_stat": "X", "docket_number": "MC1"})
        assert result == [{"type": "Common", "status": "X", "docket_number": "MC1"}]


# ---------------------------------------------------------------------------
# normalize_insurance
# ---------------------------------------------------------------------------


class TestNormalizeInsuranceSnakeCase:
    """Test with snake_case API shape (ins_type_code, max_cov_amount × 1000)."""

    def test_type_translated(self, real_api_data):
        result = normalize_insurance(real_api_data["insurances"])
        types = [i["type"] for i in result]
        assert "BIPD" in types
        assert "Cargo" in types

    def test_coverage_multiplied(self, real_api_data):
        result = normalize_insurance(real_api_data["insurances"])
        bipd = next(i for i in result if i["type"] == "BIPD")
        assert bipd["coverage"] == 750_000

    def test_zero_coverage_inactive(self, real_api_data):
        result = normalize_insurance(real_api_data["insurances"])
        cargo = next(i for i in result if i["type"] == "Cargo")
        assert cargo["coverage"] == 0
        assert cargo["status"] == "Inactive"

    def test_insurer_name(self, real_api_data):
        result = normalize_insurance(real_api_data["insurances"])
        bipd = next(i for i in result if i["type"] == "BIPD")
        assert bipd["insurer"] == "EXAMPLE INSURANCE COMPANY"

    def test_policy_number(self, real_api_data):
        result = normalize_insurance(real_api_data["insurances"])
        bipd = next(i for i in result if i["type"] == "BIPD")
        assert bipd["policy_number"] == "SYNTHETIC-001"


class TestNormalizeInsuranceFixture:
    """Test with fixture shape (type/coverage/insuranceCarrier)."""

    def test_preserves_fixture_shape(self):
        fixture = [
            {
                "type": "BIPD",
                "insuranceType": "BIPD",
                "status": "Active",
                "coverage": 1000000,
                "insuranceCarrier": "Example Indemnity Co",
                "policyNumber": "WC-2025-001",
                "effectiveDate": "2025-01-01",
            }
        ]
        result = normalize_insurance(fixture)
        assert len(result) == 1
        assert result[0]["type"] == "BIPD"
        assert result[0]["coverage"] == 1000000
        assert result[0]["insurer"] == "Example Indemnity Co"
        assert result[0]["status"] == "Active"

    def test_non_collection_returns_empty(self):
        assert normalize_insurance("invalid") == []

    def test_invalid_coverage_becomes_zero(self):
        result = normalize_insurance(
            [{"type": "Cargo", "coverage": "unknown", "status": "Pending"}]
        )
        assert result[0]["coverage"] == 0

    def test_unknown_real_type_and_invalid_amount_remain_safe(self):
        result = normalize_insurance([{"ins_type_code": "Z", "max_cov_amount": "not-a-number"}])
        assert result[0]["type"] == "Type Z"
        assert result[0]["coverage"] == 0
        assert result[0]["status"] == "Inactive"
