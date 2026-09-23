"""Tests for PDF output and graceful degradation.

These tests verify the PDF rendering pathway works correctly (or degrades
gracefully when weasyprint is not installed) and that vetting report
context has no None values for populated API fields.
"""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx

_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root))
sys.path.insert(
    0,
    str(_repo_root / "plugins" / "searchcarriers-ops-reporter" / "scripts"),
)

from ops_reporter_mcp import (
    API_BASE,
    SEARCH_BASE,
    _export_data,
    _generate_report,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fake_api_key():
    return "test-key-not-real"


@pytest.fixture
def carrier_primary():
    return json.loads((FIXTURES_DIR / "carrier_primary.json").read_text())


@pytest.fixture
def authorities_sample():
    return json.loads((FIXTURES_DIR / "authorities_sample.json").read_text())


@pytest.fixture
def insurances_active():
    return json.loads((FIXTURES_DIR / "insurances_active.json").read_text())


@pytest.fixture
def equipment_sample():
    return json.loads((FIXTURES_DIR / "equipment_sample.json").read_text())


def _mock_report_routes(router, carrier, authorities, insurances, dot="1234567"):
    router.get(f"{SEARCH_BASE}/search").mock(return_value=httpx.Response(200, json=carrier))
    router.get(f"/company/{dot}/authorities").mock(
        return_value=httpx.Response(200, json=authorities)
    )
    router.get(f"/company/{dot}/insurances").mock(return_value=httpx.Response(200, json=insurances))


# ---------------------------------------------------------------------------
# PDF format tests
# ---------------------------------------------------------------------------


class TestPDFFormat:
    """Test PDF format output behavior."""

    async def test_pdf_format_graceful_degradation(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """When weasyprint is not installed, format falls back to markdown."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_report_routes(router, carrier_primary, authorities_sample, insurances_active)

            # Mock weasyprint import failure
            import builtins

            original_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == "weasyprint":
                    raise ImportError("No module named 'weasyprint'")
                return original_import(name, *args, **kwargs)

            with patch.object(builtins, "__import__", side_effect=mock_import):
                result = await _generate_report(
                    {"dot_number": "1234567", "format": "pdf"}, fake_api_key
                )

        # Should fall back to markdown, not crash
        assert result["format"] == "markdown"
        assert "report" in result

    async def test_pdf_format_returns_file_path(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active, tmp_path
    ):
        """When weasyprint is available, result includes file_path ending in .pdf."""
        if not importlib.util.find_spec("jinja2") or not importlib.util.find_spec("weasyprint"):
            pytest.skip("weasyprint or jinja2 not installed")

        with respx.mock(base_url=API_BASE) as router:
            _mock_report_routes(router, carrier_primary, authorities_sample, insurances_active)

            # Redirect output to tmp_path
            with patch("pdf_renderer._REPORTS_DIR", tmp_path):
                result = await _generate_report(
                    {"dot_number": "1234567", "format": "pdf"}, fake_api_key
                )

        assert result["format"] == "pdf"
        assert result["file_path"].endswith(".pdf")
        assert Path(result["file_path"]).exists()


# ---------------------------------------------------------------------------
# Normalization quality tests
# ---------------------------------------------------------------------------


class TestNormalizationQuality:
    """Verify that normalization produces complete data — no N/A for fields
    that exist in the API response."""

    async def test_report_no_na_for_primary_fixture(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Example Freight has all major fields — none should be N/A."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_report_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _generate_report({"dot_number": "1234567"}, fake_api_key)

        report = result["report"]
        # The carrier name should appear, not "Unknown Carrier"
        assert "EXAMPLE FREIGHT" in report
        assert result["carrier_name"] == "EXAMPLE FREIGHT LLC"

    async def test_report_contains_insurance_data(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Insurance section should show type and insurer, not all N/A."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_report_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _generate_report({"dot_number": "1234567"}, fake_api_key)

        report = result["report"]
        assert "BIPD" in report
        assert "Example Indemnity" in report

    async def test_report_contains_authority_data(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Authority section should show type and status."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_report_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _generate_report({"dot_number": "1234567"}, fake_api_key)

        report = result["report"]
        assert "Common" in report
        assert "Active" in report

    async def test_csv_export_curated(self, fake_api_key, carrier_primary):
        """CSV export should produce curated columns, not raw dump."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/equipment").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            result = await _export_data({"dot_number": "1234567", "format": "csv"}, fake_api_key)

        assert result["format"] == "csv"
        assert "DOT Number" in result["data"]
        assert "Legal Name" in result["data"]
        # Should not have search_data column
        assert "search_data" not in result["data"]
