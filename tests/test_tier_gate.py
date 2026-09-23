"""Unit tests for plugins.shared.tier_gate."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.shared.tier_gate import (  # noqa: E402
    TIER_ORDER,
    TOOL_TIERS,
    TierError,
    check_tier,
    get_tool_tier,
)


class TestCheckTier:
    """check_tier() — happy path, boundaries, and edge cases."""

    def test_free_tool_with_free_tier(self):
        assert check_tier("carrier_lookup", "free") is True

    def test_free_tool_with_enterprise_tier(self):
        assert check_tier("carrier_lookup", "enterprise") is True

    def test_pro_tool_with_pro_tier(self):
        assert check_tier("entity_map", "pro") is True

    def test_pro_tool_with_higher_tier(self):
        assert check_tier("entity_map", "enterprise") is True

    def test_pro_tool_with_free_tier_raises(self):
        with pytest.raises(TierError) as exc_info:
            check_tier("entity_map", "free")
        assert exc_info.value.tool == "entity_map"
        assert exc_info.value.required == "pro"
        assert exc_info.value.current == "free"

    def test_enterprise_tool_with_smb_raises(self):
        with pytest.raises(TierError):
            check_tier("tms_sync", "smb")

    def test_enterprise_tool_with_enterprise_passes(self):
        assert check_tier("tms_sync", "enterprise") is True

    def test_unknown_tool_defaults_to_free(self):
        assert check_tier("nonexistent_tool", "free") is True

    def test_unknown_tier_defaults_to_free_index(self):
        """Unknown tier string should be treated as free (index 0)."""
        # Free tool should still pass
        assert check_tier("carrier_lookup", "platinum") is True
        # Pro tool should raise since unknown tier = free
        with pytest.raises(TierError):
            check_tier("entity_map", "platinum")

    def test_case_insensitive_tier(self):
        assert check_tier("entity_map", "PRO") is True
        assert check_tier("entity_map", "Pro") is True

    def test_default_tier_is_free(self):
        assert check_tier("carrier_lookup") is True

    def test_default_tier_raises_for_pro_tool(self):
        with pytest.raises(TierError):
            check_tier("entity_map")

    @pytest.mark.parametrize("tier", TIER_ORDER)
    def test_every_tier_can_access_free_tools(self, tier):
        assert check_tier("carrier_lookup", tier) is True

    def test_boundary_basic_cannot_access_pro(self):
        with pytest.raises(TierError):
            check_tier("risk_score", "basic")

    def test_boundary_pro_cannot_access_proplus(self):
        with pytest.raises(TierError):
            check_tier("vetting_check", "pro")
        with pytest.raises(TierError):
            check_tier("qualification_reports", "pro")

    def test_boundary_proplus_cannot_access_smb(self):
        with pytest.raises(TierError):
            check_tier("bulk_lookup", "proplus")


class TestTierError:
    """TierError — attributes and message formatting."""

    def test_attributes(self):
        err = TierError("entity_map", "pro", "free")
        assert err.tool == "entity_map"
        assert err.required == "pro"
        assert err.current == "free"

    def test_message_contains_tool_name(self):
        err = TierError("entity_map", "pro", "free")
        assert "entity_map" in str(err)

    def test_message_contains_required_tier(self):
        err = TierError("entity_map", "pro", "free")
        assert "pro" in str(err)

    def test_message_contains_upgrade_url(self):
        err = TierError("entity_map", "pro", "free")
        assert "searchcarriers.com/pricing" in str(err)

    def test_is_exception(self):
        assert issubclass(TierError, Exception)


class TestGetToolTier:
    """get_tool_tier() — known tools and fallback."""

    def test_known_free_tool(self):
        assert get_tool_tier("carrier_lookup") == "free"

    def test_known_pro_tool(self):
        assert get_tool_tier("entity_map") == "pro"

    def test_known_enterprise_tool(self):
        assert get_tool_tier("tms_sync") == "enterprise"

    def test_unknown_tool_returns_free(self):
        assert get_tool_tier("nonexistent_tool") == "free"

    def test_all_registered_tools_have_valid_tiers(self):
        for tool, tier in TOOL_TIERS.items():
            assert tier in TIER_ORDER, f"Tool '{tool}' has invalid tier '{tier}'"
