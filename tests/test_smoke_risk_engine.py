"""Live smoke tests for Risk Engine handlers — hits real SearchCarriers API."""

import sys
from pathlib import Path

import pytest

_repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(_repo_root))
sys.path.insert(
    0,
    str(_repo_root / "plugins" / "searchcarriers-risk-engine" / "scripts"),
)

from conftest import assert_no_error, save_artifact  # noqa: E402
from risk_engine_mcp import (  # noqa: E402
    _compliance_audit,
    _insurance_check,
    _risk_score,
    _vetting_check,
)

DOT_PRIMARY = "1234567"

VALID_RISK_LEVELS = {"low", "medium", "elevated", "high"}


@pytest.mark.integration
class TestSmokeRiskEngine:
    """Live smoke tests for all four Risk Engine handler functions."""

    async def test_risk_score(self, live_api_key, smoke_reports_dir):
        """Risk score returns a 0-100 score, a named risk level, and factor breakdown."""
        result = await _risk_score({"dot_number": DOT_PRIMARY}, live_api_key)

        assert_no_error(result)

        assert "risk_score" in result, (
            f"Expected 'risk_score' key in result; got keys: {list(result.keys())}"
        )
        score = result["risk_score"]
        assert isinstance(score, (int, float)), (
            f"Expected numeric risk_score, got {type(score).__name__}: {score!r}"
        )
        assert 0 <= score <= 100, f"risk_score {score} is outside [0, 100]"

        assert "risk_level" in result, (
            f"Expected 'risk_level' key in result; got keys: {list(result.keys())}"
        )
        assert result["risk_level"] in VALID_RISK_LEVELS, (
            f"risk_level {result['risk_level']!r} not in {VALID_RISK_LEVELS}"
        )

        assert "factors" in result, (
            f"Expected 'factors' key in result; got keys: {list(result.keys())}"
        )
        assert isinstance(result["factors"], list), (
            f"Expected factors to be a list, got {type(result['factors']).__name__}"
        )

        save_artifact(smoke_reports_dir, "risk_score", result)

    async def test_vetting_check(self, live_api_key, smoke_reports_dir):
        """Vetting check returns a PASS/FAIL/REVIEW verdict and a rules_checked count."""
        result = await _vetting_check({"dot_number": DOT_PRIMARY}, live_api_key)

        assert_no_error(result)

        assert "verdict" in result, (
            f"Expected 'verdict' key in result; got keys: {list(result.keys())}"
        )
        assert result["verdict"] in {"PASS", "FAIL", "REVIEW"}, (
            f"verdict {result['verdict']!r} not in expected set"
        )

        has_rules_key = "rules_checked" in result or "checks" in result
        assert has_rules_key, (
            f"Expected 'rules_checked' or 'checks' key in result; got keys: {list(result.keys())}"
        )

        save_artifact(smoke_reports_dir, "vetting_check", result)

    async def test_insurance_check(self, live_api_key, smoke_reports_dir):
        """Insurance check returns status and active/lapsed policy data."""
        result = await _insurance_check({"dot_number": DOT_PRIMARY}, live_api_key)

        assert_no_error(result)

        has_insurance_key = any(
            k in result
            for k in (
                "status",
                "active_policies",
                "active_policy_count",
                "total_coverage",
                "insurances",
            )
        )
        assert has_insurance_key, (
            f"Expected at least one insurance-related key in result; "
            f"got keys: {list(result.keys())}"
        )

        save_artifact(smoke_reports_dir, "insurance_check", result)

    async def test_compliance_audit(self, live_api_key, smoke_reports_dir):
        """Compliance audit returns a checks list with per-check status entries."""
        result = await _compliance_audit({"dot_number": DOT_PRIMARY}, live_api_key)

        assert_no_error(result)

        has_audit_key = any(
            k in result for k in ("checks", "audit", "compliance_status", "summary")
        )
        assert has_audit_key, (
            f"Expected 'checks', 'audit', 'compliance_status', or 'summary' in result; "
            f"got keys: {list(result.keys())}"
        )

        save_artifact(smoke_reports_dir, "compliance_audit", result)
