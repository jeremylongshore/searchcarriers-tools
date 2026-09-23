"""Contract tests for current SearchCarriers API routing and normalization."""

import pytest

from plugins.shared.api_contract import (
    API_V1_BASE,
    API_V2_BASE,
    API_V3_BASE,
    V3_SEARCH_FILTERS,
    company_fields,
    data_list,
    normalize_v3_company,
    v3_search_params,
)


def test_versioned_api_roots_are_explicit() -> None:
    assert API_V1_BASE.endswith("/api/v1")
    assert API_V2_BASE.endswith("/api/v2")
    assert API_V3_BASE.endswith("/api/v3")


def test_v3_search_uses_current_parameter_names() -> None:
    assert v3_search_params("260913", "mc", per_page=1) == {
        "docketNumber": "260913",
        "page": 1,
        "perPage": 1,
    }


def test_v3_search_maps_advanced_filters_to_published_wire_names() -> None:
    params = v3_search_params(
        filters={
            "min_power_units": 10,
            "min_bipd_coverage": 1_000_000,
            "cargo_insurance_present": True,
            "include_equipment_types": ["VAN"],
            "lane_origin_state": "AL",
            "lane_destination_state": "TX",
            "lane_destination_radius_miles": 75,
        }
    )
    assert params == {
        "page": 1,
        "perPage": 10,
        "minPowerUnits": 10,
        "minBipdCoverage": 1_000_000,
        "cargoInsurancePresent": True,
        "includeEquipmentTypes[]": ["VAN"],
        "laneOriginState": "AL",
        "laneDestinationState": "TX",
        "laneDestinationRadiusMiles": 75,
    }
    assert "lane_origin_state" in V3_SEARCH_FILTERS


def test_v3_search_rejects_unknown_advanced_filter() -> None:
    with pytest.raises(ValueError, match="Unsupported v3 search filter"):
        v3_search_params(filters={"invented": True})
    assert v3_search_params("Acme", "name", state="tx", city="Dallas") == {
        "superSearchTerm": "Acme",
        "page": 1,
        "perPage": 10,
        "addressState": "TX",
        "addressCity": "Dallas",
    }


def test_company_field_selection_rejects_unknown_sections() -> None:
    assert company_fields("safety", "insurance") == {"fields": "safety,insurance"}
    with pytest.raises(ValueError, match="Unknown v3 company field"):
        company_fields("invented")


def test_v3_company_normalization_preserves_raw_sections_and_adds_aliases() -> None:
    payload = {
        "data": {
            "dot_number": "123",
            "legal_name": "Synthetic Carrier LLC",
            "dot_status": "ACTIVE",
            "power_units": 12,
            "physical_address": {"city": "Mobile", "state": "AL"},
            "contact": {"phone": "5550100", "email_address": "ops@example.invalid"},
            "operation": {"cargo_carried": ["General Freight"]},
            "safety": {
                "total_inspections": 7,
                "total_crashes": 1,
                "safety_rating": "SATISFACTORY",
                "driver_oos_rate": 2,
                "vehicle_oos_rate": 4,
            },
        }
    }
    company = normalize_v3_company(payload)
    assert company["dotNumber"] == "123"
    assert company["legalName"] == "Synthetic Carrier LLC"
    assert company["inspectionTotal"] == 7
    assert company["crashTotal"] == 1
    assert company["phyState"] == "AL"
    assert company["safety"]["total_crashes"] == 1


def test_data_list_fails_loudly_on_shape_drift() -> None:
    assert data_list({"data": [{"dot_number": "123"}]}) == [{"dot_number": "123"}]
    with pytest.raises(ValueError, match="data list"):
        data_list({"data": {"dot_number": "123"}})
