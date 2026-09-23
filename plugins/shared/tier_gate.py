"""Shared tier gating for SearchCarriers MCP plugins."""

TIER_ORDER = ["free", "basic", "pro", "proplus", "smb", "enterprise"]

TOOL_TIERS: dict[str, str] = {
    # Carrier Intel
    "carrier_lookup": "free",
    "carrier_profile": "free",
    "entity_map": "pro",
    "fleet_summary": "free",
    # Risk Engine (future)
    "risk_score": "pro",
    "qualification_reports": "proplus",
    "vetting_check": "proplus",
    "insurance_check": "pro",
    "compliance_audit": "pro",
    # Ops Reporter (future)
    "generate_report": "pro",
    "generate_fleet": "pro",
    "generate_compare": "pro",
    "export_data": "pro",
    # Watchdog (future)
    "manage_watchlist": "proplus",
    "get_alerts": "proplus",
    "route_alert": "proplus",
    "monitor_compliance": "proplus",
    # API Bridge (future)
    "api_health": "smb",
    "bulk_lookup": "smb",
    "tms_sync": "enterprise",
    "webhook_manage": "smb",
}


class TierError(Exception):
    """Raised when a user's tier is insufficient to access a tool."""

    def __init__(self, tool: str, required: str, current: str) -> None:
        self.tool = tool
        self.required = required
        self.current = current
        super().__init__(
            f"Tool '{tool}' requires {required} tier or higher. "
            f"Current tier: {current}. "
            f"Upgrade at https://searchcarriers.com/pricing"
        )


def check_tier(tool_name: str, user_tier: str = "free") -> bool:
    """Check whether a user's tier permits access to a tool.

    Args:
        tool_name: The MCP tool name to check.
        user_tier: The caller's subscription tier string. Defaults to "free".

    Returns:
        True when the user has sufficient access.

    Raises:
        TierError: When the user's tier falls below the tool's minimum.
    """
    required = TOOL_TIERS.get(tool_name, "free")
    req_idx = TIER_ORDER.index(required)
    try:
        user_idx = TIER_ORDER.index(user_tier.lower())
    except ValueError:
        user_idx = 0  # Unknown tier defaults to free

    if user_idx < req_idx:
        raise TierError(tool_name, required, user_tier)
    return True


def get_tool_tier(tool_name: str) -> str:
    """Return the minimum tier required for a tool.

    Args:
        tool_name: The MCP tool name to query.

    Returns:
        The minimum tier string, defaulting to "free" for unknown tools.
    """
    return TOOL_TIERS.get(tool_name, "free")
