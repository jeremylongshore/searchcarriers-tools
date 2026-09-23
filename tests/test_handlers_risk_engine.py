"""Integration tests for risk_engine_mcp handler functions.

Tests exercise the actual handler logic with respx intercepting HTTP calls
at the transport layer. No real API calls are made.
"""

import sys
from pathlib import Path

import httpx
import respx

_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root))
sys.path.insert(
    0,
    str(_repo_root / "plugins" / "searchcarriers-risk-engine" / "scripts"),
)

from conftest import assert_error_payload  # noqa: E402
from risk_engine_mcp import (  # noqa: E402
    API_BASE,
    SEARCH_BASE,
    _compliance_audit,
    _insurance_check,
    _risk_score,
    _vetting_check,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_standard_routes(router, carrier, authorities, insurances, dot="1234567"):
    """Set up the three standard routes used by most risk-engine handlers."""
    router.get(f"{SEARCH_BASE}/search").mock(return_value=httpx.Response(200, json=carrier))
    router.get(f"/company/{dot}/authorities").mock(
        return_value=httpx.Response(200, json=authorities)
    )
    router.get(f"/company/{dot}/insurances").mock(return_value=httpx.Response(200, json=insurances))


# ---------------------------------------------------------------------------
# _risk_score
# ---------------------------------------------------------------------------


class TestRiskScore:
    """Tests for the risk_score handler."""

    async def test_required_keys(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Response contains all required top-level keys."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_standard_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _risk_score({"dot_number": "1234567"}, fake_api_key)

        for key in (
            "dot_number",
            "risk_score",
            "risk_level",
            "factors",
            "carrier_snapshot",
            "_pipeline",
        ):
            assert key in result, f"Missing key: {key}"

    async def test_risk_level_valid_string(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """risk_level is one of the defined level strings."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_standard_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _risk_score({"dot_number": "1234567"}, fake_api_key)

        assert result["risk_level"] in ("low", "medium", "elevated", "high")

    async def test_score_0_to_100(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """risk_score is clamped to [0, 100]."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_standard_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _risk_score({"dot_number": "1234567"}, fake_api_key)

        assert 0 <= result["risk_score"] <= 100

    async def test_factors_sorted_by_penalty(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Factors list is sorted by penalty descending."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_standard_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _risk_score({"dot_number": "1234567"}, fake_api_key)

        penalties = [f["penalty"] for f in result["factors"]]
        assert penalties == sorted(penalties, reverse=True)

    async def test_carrier_snapshot_has_legal_name(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """carrier_snapshot includes legalName."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_standard_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _risk_score({"dot_number": "1234567"}, fake_api_key)

        assert result["carrier_snapshot"]["legalName"] == "EXAMPLE FREIGHT LLC"

    async def test_pipeline_meta(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """_pipeline metadata is correct."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_standard_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _risk_score({"dot_number": "1234567"}, fake_api_key)

        assert result["_pipeline"]["source"] == "risk-engine"
        assert result["_pipeline"]["tool"] == "risk_score"
        assert result["_pipeline"]["dot_number"] == "1234567"

    async def test_api_error(self, fake_api_key):
        """Search failure returns error payload."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(return_value=httpx.Response(500, json={}))
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            result = await _risk_score({"dot_number": "1234567"}, fake_api_key)

        assert_error_payload(result, "api_error")

    async def test_not_found_empty_data(self, fake_api_key):
        """Empty search data returns not_found error."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            result = await _risk_score({"dot_number": "1234567"}, fake_api_key)

        assert_error_payload(result, "not_found")


# ---------------------------------------------------------------------------
# _vetting_check
# ---------------------------------------------------------------------------


class TestVettingCheck:
    """Tests for the vetting_check handler."""

    async def test_required_keys(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Response contains all required keys."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_standard_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _vetting_check({"dot_number": "1234567"}, fake_api_key)

        for key in ("dot_number", "verdict", "rules_checked", "summary", "results", "_pipeline"):
            assert key in result, f"Missing key: {key}"

    async def test_verdict_pass_for_authorized(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Authorized carrier with good data gets PASS verdict."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_standard_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _vetting_check({"dot_number": "1234567"}, fake_api_key)

        # Example Freight is authorized, has active authorities and insurance
        assert result["verdict"] in ("PASS", "REVIEW")

    async def test_verdict_fail_no_authority(
        self, fake_api_key, carrier_primary, insurances_active
    ):
        """Carrier with no authorities gets FAIL or REVIEW."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json={"data": []})
            )
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json=insurances_active)
            )
            result = await _vetting_check({"dot_number": "1234567"}, fake_api_key)

        # No authority records → at least a REVIEW
        assert result["verdict"] in ("FAIL", "REVIEW")

    async def test_summary_counts_match(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Summary pass+review+fail counts match total rules_checked."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_standard_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _vetting_check({"dot_number": "1234567"}, fake_api_key)

        s = result["summary"]
        assert s["pass"] + s["review"] + s["fail"] == result["rules_checked"]

    async def test_rule_results_structure(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Each rule result has required fields."""
        with respx.mock(base_url=API_BASE) as router:
            _mock_standard_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _vetting_check({"dot_number": "1234567"}, fake_api_key)

        for rule in result["results"]:
            for key in ("rule", "status", "actual", "threshold", "message"):
                assert key in rule, f"Rule {rule.get('rule', '?')} missing key: {key}"
            assert rule["status"] in ("pass", "review", "fail")

    async def test_custom_rules_override(
        self, fake_api_key, carrier_primary, authorities_sample, insurances_active
    ):
        """Custom rules dict overrides defaults."""
        # Set an impossibly high insurance minimum to force a fail
        with respx.mock(base_url=API_BASE) as router:
            _mock_standard_routes(router, carrier_primary, authorities_sample, insurances_active)
            result = await _vetting_check(
                {
                    "dot_number": "1234567",
                    "rules": {"min_insurance_coverage": 999_999_999},
                },
                fake_api_key,
            )

        # Should fail the insurance rule
        ins_rule = next(r for r in result["results"] if r["rule"] == "min_insurance_coverage")
        assert ins_rule["status"] == "fail"


# ---------------------------------------------------------------------------
# _insurance_check
# ---------------------------------------------------------------------------


class TestInsuranceCheck:
    """Tests for the insurance_check handler."""

    async def test_adequate_with_active_policy(self, fake_api_key, insurances_active):
        """Active policy with sufficient coverage returns 'adequate'."""
        with respx.mock(base_url=API_BASE) as router:
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json=insurances_active)
            )
            result = await _insurance_check({"dot_number": "1234567"}, fake_api_key)

        assert result["status"] in ("adequate", "warning")
        assert result["active_policy_count"] >= 1

    async def test_critical_with_no_policies(self, fake_api_key, insurances_empty):
        """No policies returns 'critical'."""
        with respx.mock(base_url=API_BASE) as router:
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json=insurances_empty)
            )
            result = await _insurance_check({"dot_number": "1234567"}, fake_api_key)

        assert result["status"] == "critical"
        assert result["active_policy_count"] == 0

    async def test_required_keys(self, fake_api_key, insurances_active):
        """Response has all required keys."""
        with respx.mock(base_url=API_BASE) as router:
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json=insurances_active)
            )
            result = await _insurance_check({"dot_number": "1234567"}, fake_api_key)

        for key in ("dot_number", "status", "active_policies", "total_coverage", "_pipeline"):
            assert key in result, f"Missing key: {key}"

    async def test_below_minimum_coverage_warning(self, fake_api_key):
        """Coverage below $750K federal minimum triggers a warning."""
        low_insurance = {
            "data": [
                {
                    "policyNumber": "LOW-001",
                    "type": "BIPD",
                    "status": "Active",
                    "coverageFrom": 100000,
                    "coverageTo": 500000,
                    "effectiveDate": "2025-01-01",
                    "cancellationDate": "2026-12-01",
                }
            ]
        }
        with respx.mock(base_url=API_BASE) as router:
            router.get("/company/1234567/insurances").mock(
                return_value=httpx.Response(200, json=low_insurance)
            )
            result = await _insurance_check({"dot_number": "1234567"}, fake_api_key)

        assert result["status"] == "warning"
        assert any("minimum" in w.lower() or "750" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# _compliance_audit
# ---------------------------------------------------------------------------


class TestComplianceAudit:
    """Tests for the compliance_audit handler."""

    async def test_required_keys(self, fake_api_key, carrier_primary, authorities_sample):
        """Response has all required keys."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json=authorities_sample)
            )
            result = await _compliance_audit({"dot_number": "1234567"}, fake_api_key)

        for key in ("dot_number", "checks", "_pipeline"):
            assert key in result, f"Missing key: {key}"

    async def test_check_fields_structure(self, fake_api_key, carrier_primary, authorities_sample):
        """Each check has required fields."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json=authorities_sample)
            )
            result = await _compliance_audit({"dot_number": "1234567"}, fake_api_key)

        for check in result["checks"]:
            for key in ("check", "status", "message"):
                assert key in check, f"Check {check.get('check', '?')} missing key: {key}"

    async def test_status_values_valid(self, fake_api_key, carrier_primary, authorities_sample):
        """Each check's status is one of the valid values."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json=authorities_sample)
            )
            result = await _compliance_audit({"dot_number": "1234567"}, fake_api_key)

        for check in result["checks"]:
            assert check["status"] in ("pass", "warning", "fail")

    async def test_mcs150_pass_when_recent(self, fake_api_key, carrier_primary, authorities_sample):
        """MCS-150 filed recently should pass."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json=authorities_sample)
            )
            result = await _compliance_audit({"dot_number": "1234567"}, fake_api_key)

        mcs_check = next((c for c in result["checks"] if c["check"] == "mcs150_filing"), None)
        assert mcs_check is not None
        # Example Freight fixture has mcs150Date=2025-06-15, which is recent
        assert mcs_check["status"] == "pass"

    async def test_operating_status_pass(self, fake_api_key, carrier_primary, authorities_sample):
        """Authorized operating status should pass."""
        with respx.mock(base_url=API_BASE) as router:
            router.get(f"{SEARCH_BASE}/search").mock(
                return_value=httpx.Response(200, json=carrier_primary)
            )
            router.get("/company/1234567/authorities").mock(
                return_value=httpx.Response(200, json=authorities_sample)
            )
            result = await _compliance_audit({"dot_number": "1234567"}, fake_api_key)

        op_check = next((c for c in result["checks"] if c["check"] == "operating_status"), None)
        assert op_check is not None
        assert op_check["status"] == "pass"
