# Risk Engine - Technical Specification

## Tech Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Runtime | Python | 3.11+ | MCP server runtime |
| Protocol | MCP (Model Context Protocol) | 1.0+ | Tool registration and invocation |
| HTTP client | httpx | 0.27+ | Async HTTP (for fallback carrier data fetching) |
| Tier gating | shared/tier_gate.py | -- | Shared tier enforcement across all plugins |
| Testing | pytest | 8.0+ | Unit and integration tests |

## Dependencies

```
httpx>=0.27
mcp>=1.0
```

Risk Engine's core scoring logic has zero external dependencies -- it is pure Python computation. `httpx` is included for the fallback case where Risk Engine needs to trigger Carrier Intel data fetching via the SearchCarriers API. `mcp` provides the MCP server framework.

## File Structure

```
searchcarriers-risk-engine/
+-- .claude-plugin/
|   +-- plugin.json                    # Plugin manifest (name, tools, tiers, version)
+-- .mcp.json                          # MCP server configuration (command, args, env)
+-- docs/                              # 6-doc enterprise documentation set
|   +-- 01-BUSINESS-CASE.md
|   +-- 02-PRD.md
|   +-- 03-ARCHITECTURE.md
|   +-- 04-USER-JOURNEY.md
|   +-- 05-TECHNICAL-SPEC.md           # (this file)
|   +-- 06-STATUS.md
+-- commands/                          # Slash command definitions (planned)
|   +-- sc-risk.md                     # /sc-risk -> risk_score
|   +-- sc-vet.md                      # /sc-vet -> vetting_check
+-- agents/                            # Agent definitions (planned)
|   +-- risk-analyst.md                # Autonomous risk analysis agent
+-- skills/                            # Embedded skill (planned)
|   +-- searchcarriers-risk-engine/
|       +-- SKILL.md                   # Claude skill for risk interpretation
+-- scripts/
|   +-- risk_engine_mcp.py             # MCP server implementation
|   +-- scoring.py                     # Risk scoring module (planned)
|   +-- vetting.py                     # Vetting rules engine (planned)
|   +-- normalize.py                   # Data normalization layer (planned)
|   +-- requirements.txt               # Python dependencies
+-- tests/                             # Test suite (planned)
    +-- test_scoring.py                # Scoring algorithm unit tests
    +-- test_vetting.py                # Vetting rules unit tests
    +-- test_normalize.py              # Normalization unit tests
    +-- test_integration.py            # Pipeline integration tests
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SEARCHCARRIERS_API_KEY` | Yes | -- | Bearer token for API authentication. Passed through to Carrier Intel when Risk Engine needs to fetch carrier data. Format: `{id}\|{token}`. |
| `SEARCHCARRIERS_TIER` | No | `free` | User's subscription tier. Determines tool access. Values: `free`, `basic`, `pro`, `proplus`, `smb`, `enterprise`. |
| `SEARCHCARRIERS_API_BASE` | No | `https://searchcarriers.com/api/v1` | API base URL override (for testing against staging environments). |

## MCP Tool Schemas

### risk_score

Computes a composite 0-100 risk score with weighted breakdown across four dimensions.

**Input:**
```json
{
  "dot_number": "string (required) - Carrier's USDOT number",
  "carrier_data": "object (optional) - Pre-fetched carrier data from carrier_profile. If omitted, Risk Engine requests it via Carrier Intel."
}
```

**Output:**
```json
{
  "meta": {
    "tool": "risk_score",
    "timestamp": "2026-02-26T14:30:00Z",
    "dot_number": "69494",
    "tier": "pro"
  },
  "assessment": {
    "composite_score": 18,
    "tier": "LOW",
    "confidence": "HIGH",
    "data_completeness": 0.94,
    "breakdown": {
      "safety": {
        "score": 12,
        "weight": 0.35,
        "weighted": 4.2,
        "factors": {
          "safety_rating": { "value": "Satisfactory", "contribution": 0 },
          "vehicle_oos_rate": { "value": 12.3, "national_avg": 21.0, "contribution": 5 },
          "driver_oos_rate": { "value": 4.1, "national_avg": 5.5, "contribution": 0 },
          "crash_indicator": { "value": false, "contribution": 0 }
        }
      },
      "insurance": {
        "score": 10,
        "weight": 0.25,
        "weighted": 2.5,
        "factors": {
          "bipd_active": { "value": true, "contribution": 0 },
          "bipd_coverage": { "value": 5000000, "min": 750000, "contribution": 0 },
          "cargo_active": { "value": true, "contribution": 0 },
          "days_to_expiry": { "value": 188, "threshold": 30, "contribution": 0 }
        }
      },
      "authority": {
        "score": 5,
        "weight": 0.20,
        "weighted": 1.0,
        "factors": {
          "common_active": { "value": true, "contribution": 0 },
          "authority_age_days": { "value": 16437, "min": 90, "contribution": 0 },
          "any_revocations": { "value": false, "contribution": 0 }
        }
      },
      "operational": {
        "score": 15,
        "weight": 0.20,
        "weighted": 3.0,
        "factors": {
          "mcs150_months_ago": { "value": 5, "max": 24, "contribution": 0 },
          "power_units": { "value": 7880, "contribution": 0 },
          "driver_to_unit_ratio": { "value": 1.59, "contribution": 0 }
        }
      }
    },
    "flags": [],
    "disclaimer": "Advisory only. Not a compliance guarantee or legal advice."
  }
}
```

**Min Tier:** Pro

### qualification_reports

Fetches `GET /api/v2/company/{dotNumber}/qualification-reports` and preserves
the upstream personal/team qualification names, Pass/Review/Fail results, and
evidence without applying local defaults.

**Min Tier:** Pro+

### vetting_check

Evaluates a carrier against a complete caller-supplied policy. Returns
PASS/REVIEW/FAIL and rejects missing policy keys before any API request.

**Input:**
```json
{
  "dot_number": "string (required) - Carrier's USDOT number",
  "rules": {
    "operating_status": "string (required)",
    "min_insurance_coverage": "number (required; caller policy)",
    "max_oos_rate": "number (required; caller policy)",
    "max_crash_rate_per_pu": "number (required; caller policy)",
    "authority_active": "boolean (required)",
    "mcs150_current": "boolean (required)"
  }
}
```

**Output:**
```json
{
  "meta": {
    "tool": "vetting_check",
    "timestamp": "2026-02-26T14:30:00Z",
    "dot_number": "69494",
    "tier": "proplus"
  },
  "assessment": {
    "verdict": "PASS",
    "rules_passed": 8,
    "rules_review": 0,
    "rules_failed": 0,
    "rules": [
      {
        "id": "VET-01",
        "description": "Active operating authority",
        "result": "PASS",
        "detail": "Common authority active since 1981-01-27",
        "threshold": "active",
        "actual": "active"
      },
      {
        "id": "VET-02",
        "description": "BIPD insurance >= $750,000",
        "result": "PASS",
        "detail": "$5,000,000 on file",
        "threshold": 750000,
        "actual": 5000000
      },
      {
        "id": "VET-03",
        "description": "Cargo insurance >= $100,000",
        "result": "PASS",
        "detail": "$250,000 on file",
        "threshold": 100000,
        "actual": 250000
      }
    ],
    "overrides_applied": {},
    "disclaimer": "Advisory only. Not a compliance guarantee or legal advice."
  }
}
```

**Min Tier:** Pro+

### insurance_check

Analyzes insurance coverage for adequacy, gaps, and lapse warnings.

**Input:**
```json
{
  "dot_number": "string (required) - Carrier's USDOT number",
  "carrier_data": "object (optional) - Pre-fetched carrier data from carrier_profile"
}
```

**Output:**
```json
{
  "meta": {
    "tool": "insurance_check",
    "timestamp": "2026-02-26T14:30:00Z",
    "dot_number": "69494",
    "tier": "pro"
  },
  "assessment": {
    "status": "ADEQUATE",
    "policies": [
      {
        "type": "BIPD",
        "coverage_amount": 5000000,
        "status": "Active",
        "effective_date": "2025-06-01",
        "expiration_date": "2026-06-01",
        "days_remaining": 188,
        "meets_minimum": true,
        "minimum_required": 750000
      },
      {
        "type": "CARGO",
        "coverage_amount": 250000,
        "status": "Active",
        "effective_date": "2025-06-01",
        "expiration_date": "2026-06-01",
        "days_remaining": 188,
        "meets_minimum": true,
        "minimum_required": 100000
      }
    ],
    "findings": [
      { "severity": "PASS", "message": "BIPD coverage active and meets minimum ($5M >= $750K)" },
      { "severity": "PASS", "message": "Cargo coverage active and meets minimum ($250K >= $100K)" },
      { "severity": "PASS", "message": "All policies have 180+ days remaining" }
    ],
    "gaps": [],
    "disclaimer": "Advisory only. Not a compliance guarantee or legal advice."
  }
}
```

**Status values:** `ADEQUATE` | `GAPS_DETECTED` | `LAPSED` | `NO_COVERAGE`

**Min Tier:** Pro

### compliance_audit

Audits MCS-150 filing, authority status, and regulatory compliance posture.

**Input:**
```json
{
  "dot_number": "string (required) - Carrier's USDOT number",
  "carrier_data": "object (optional) - Pre-fetched carrier data from carrier_profile"
}
```

**Output:**
```json
{
  "meta": {
    "tool": "compliance_audit",
    "timestamp": "2026-02-26T14:30:00Z",
    "dot_number": "69494",
    "tier": "pro"
  },
  "assessment": {
    "posture": "COMPLIANT",
    "checks": [
      {
        "check": "MCS-150 Filing",
        "status": "PASS",
        "detail": "Filed 2025-09-15 (5 months ago). Biennial deadline: 2027-09-15.",
        "threshold": "< 24 months",
        "actual": "5 months"
      },
      {
        "check": "Common Authority",
        "status": "PASS",
        "detail": "Active since 1981-01-27",
        "threshold": "active",
        "actual": "active"
      },
      {
        "check": "Safety Rating",
        "status": "PASS",
        "detail": "Satisfactory (rated 2019-03-15)",
        "threshold": "Satisfactory or Conditional",
        "actual": "Satisfactory"
      },
      {
        "check": "Out-of-Service Orders",
        "status": "PASS",
        "detail": "None on record",
        "threshold": "none",
        "actual": "none"
      },
      {
        "check": "Operating Status",
        "status": "PASS",
        "detail": "Authorized For Hire, Interstate",
        "threshold": "authorized",
        "actual": "authorized"
      }
    ],
    "summary": {
      "passed": 5,
      "warnings": 0,
      "failed": 0,
      "not_applicable": 0
    },
    "disclaimer": "Advisory only. Not a compliance guarantee or legal advice."
  }
}
```

**Posture values:** `COMPLIANT` | `DEFICIENT` | `NON_COMPLIANT`

**Min Tier:** Pro

## Scoring Algorithm Detail

### Safety Dimension (35% weight)

```python
def score_safety(carrier: dict) -> int:
    """Compute safety dimension score (0-100). Higher = more risk."""
    score = 0

    # Safety rating: S=0, C=40, U=80, None=50
    rating = carrier.get("safety_rating")
    rating_scores = {"S": 0, "C": 40, "U": 80}
    score += rating_scores.get(rating, 50)  # No rating = 50 (unknown risk)

    # Vehicle OOS rate vs national average (21.0%)
    oos_vehicle = carrier.get("oos_rate_vehicle", 0)
    if oos_vehicle > 40:
        score += 30
    elif oos_vehicle > 25:
        score += 15
    elif oos_vehicle > 21:
        score += 5

    # Driver OOS rate vs national average (5.5%)
    oos_driver = carrier.get("oos_rate_driver", 0)
    if oos_driver > 15:
        score += 20
    elif oos_driver > 10:
        score += 10
    elif oos_driver > 5.5:
        score += 3

    # Crash indicator
    if carrier.get("crash_total", 0) > 0:
        score += 10

    return min(score, 100)
```

### Insurance Dimension (25% weight)

```python
def score_insurance(insurances: list[dict]) -> int:
    """Compute insurance dimension score (0-100). Higher = more risk."""
    if not insurances:
        return 90  # No insurance records = very high risk

    score = 0
    has_bipd = False
    has_cargo = False

    for policy in insurances:
        ptype = policy.get("type", "").upper()
        status = policy.get("status", "").lower()
        amount = policy.get("coverage_amount", 0)

        if "bipd" in ptype or "bodily" in ptype:
            has_bipd = True
            if status != "active":
                score += 40
            elif amount < 750000:
                score += 20
        elif "cargo" in ptype:
            has_cargo = True
            if status != "active":
                score += 30
            elif amount < 100000:
                score += 15

        # Expiration proximity
        days_left = policy.get("days_remaining", 365)
        if days_left < 30:
            score += 15
        elif days_left < 60:
            score += 5

    if not has_bipd:
        score += 40
    if not has_cargo:
        score += 25

    return min(score, 100)
```

### Authority Dimension (20% weight)

```python
def score_authority(carrier: dict, authorities: list[dict]) -> int:
    """Compute authority dimension score (0-100). Higher = more risk."""
    score = 0

    # Check for any active common or contract authority
    has_active = False
    for auth in authorities:
        if auth.get("common_authority_status") == "A":
            has_active = True
        if auth.get("contract_authority_status") == "A":
            has_active = True

    if not has_active:
        return 95  # No active operating authority = critical risk

    # Authority age (days since earliest active authority)
    authority_age_days = carrier.get("authority_age_days", 0)
    if authority_age_days < 90:
        score += 40  # Very new authority
    elif authority_age_days < 180:
        score += 20  # New authority
    elif authority_age_days < 365:
        score += 10  # Less than a year

    # Any revocations in history
    for auth in authorities:
        for field in [
            "common_authority_status",
            "contract_authority_status",
            "broker_authority_status",
        ]:
            if auth.get(field) == "R":  # Revoked
                score += 30
                break

    return min(score, 100)
```

### Operational Dimension (20% weight)

```python
def score_operational(carrier: dict) -> int:
    """Compute operational dimension score (0-100). Higher = more risk."""
    score = 0

    # MCS-150 filing recency
    mcs150_months = carrier.get("mcs150_months_ago", 36)
    if mcs150_months > 24:
        score += 30  # Overdue biennial filing
    elif mcs150_months > 18:
        score += 10  # Approaching deadline

    # Fleet size (very small fleets = higher risk)
    power_units = carrier.get("power_units", 0)
    if power_units < 3:
        score += 20  # Single-truck operation
    elif power_units < 10:
        score += 10  # Very small fleet

    # Driver to unit ratio (< 1.0 suggests underreporting or issues)
    drivers = int(carrier.get("total_drivers", 0) or 0)
    if power_units > 0 and drivers > 0:
        ratio = drivers / power_units
        if ratio < 0.8:
            score += 15  # Significantly fewer drivers than trucks

    return min(score, 100)
```

### Composite Calculation

```python
WEIGHTS = {
    "safety": 0.35,
    "insurance": 0.25,
    "authority": 0.20,
    "operational": 0.20,
}


def composite_score(safety: int, insurance: int, authority: int, operational: int) -> int:
    raw = (
        safety * WEIGHTS["safety"]
        + insurance * WEIGHTS["insurance"]
        + authority * WEIGHTS["authority"]
        + operational * WEIGHTS["operational"]
    )
    return round(min(raw, 100))
```

## Tier Gating Implementation

Risk Engine uses the shared `plugins/shared/tier_gate.py` module. Tool tiers are registered in `TOOL_TIERS`:

```python
# From plugins/shared/tier_gate.py
TOOL_TIERS = {
    "risk_score": "pro",
    "qualification_reports": "proplus",
    "vetting_check": "proplus",
    "insurance_check": "pro",
    "compliance_audit": "pro",
}
```

Tier check is called before any computation. If the user's tier is insufficient, a structured error is returned with the upgrade URL. No scoring computation is wasted on gated requests.

## Testing Strategy

### Unit Tests (scoring algorithms)

Test the scoring functions with known carrier data and expected outcomes:

- **Werner Enterprises (DOT 69494)**: Satisfactory rating, large fleet, long authority history. Expected: LOW risk (< 25).
- **New carrier, no data**: No rating, no insurance, 30-day authority. Expected: HIGH/CRITICAL risk (> 70).
- **Carrier with lapsed insurance**: Active authority, Satisfactory rating, but expired cargo policy. Expected: ELEVATED risk (45-65).
- **Carrier with high OOS rate**: Good insurance, good authority, but 35% vehicle OOS rate. Expected: ELEVATED risk (45-60).
- **Edge case: all zeros**: Every field is 0 or None. Expected: graceful handling, HIGH risk with LOW confidence.

### Unit Tests (vetting rules)

- **All rules pass**: A complete caller policy is satisfied. Verdict: PASS.
- **One rule fails**: Cargo insurance below minimum. Verdict: FAIL.
- **Review condition**: OOS rate between REVIEW and FAIL thresholds. Verdict: REVIEW.
- **Caller policy threshold**: Policy requires a value the carrier does not meet. Verdict: FAIL.
- **Missing data**: No insurance records. VET-02 and VET-03 should FAIL.
- **Missing policy**: Reject before any API call with `invalid_policy`.
- **Named qualification**: Preserve the API v2 result and evidence unchanged.

### Integration Tests (pipeline)

Require Carrier Intel running and a valid API key. Marked with `@pytest.mark.integration`:

- **Full pipeline**: `carrier_profile("69494")` -> `risk_score(carrier_data)` -> verify score is LOW.
- **Latency**: `risk_score` with pre-fetched data < 500ms.
- **Tier gating**: Confirm Free tier gets structured error from `risk_score`.

Run integration tests:

```bash
SEARCHCARRIERS_API_KEY="your_key" SEARCHCARRIERS_TIER="pro" pytest -v -m integration
```

## Performance Benchmarks

| Operation | Target p50 | Target p95 | Target p99 | Bottleneck |
|-----------|-----------|-----------|-----------|-----------|
| `risk_score` (pre-fetched data) | 10ms | 50ms | 100ms | Pure computation |
| `risk_score` (needs carrier data) | 1.5s | 3.0s | 5.0s | Carrier Intel API calls |
| `vetting_check` (pre-fetched) | 5ms | 20ms | 50ms | Rule evaluation loop |
| `insurance_check` | 3ms | 10ms | 30ms | Insurance record parsing |
| `compliance_audit` | 3ms | 10ms | 30ms | Compliance check loop |
| MCP server cold start | 300ms | 700ms | 1.5s | Python import |
| Tier check | <1ms | <1ms | <1ms | In-memory lookup |

Risk Engine is the fastest stage in the pipeline. All tools with pre-fetched data complete in under 100ms at p99. The only scenario where Risk Engine approaches the 3-second target is when it needs to trigger Carrier Intel for data fetching, which involves external API calls.

## Deployment

> **Multi-client path:** From the repository root, run `./scripts/setup-dev.sh`,
> export `SEARCHCARRIERS_API_KEY`, and let Grok Build, Claude Code, or another
> MCP client load the root `.mcp.json`. The client-specific copy steps below
> describe optional Claude plugin packaging. See
> [`MODEL-COMPATIBILITY.md`](../../../MODEL-COMPATIBILITY.md).

### Installation

1. Ensure Carrier Intel is installed (Risk Engine depends on it for data):

```bash
ls plugins/searchcarriers-carrier-intel/.claude-plugin/plugin.json
```

2. Add Risk Engine MCP server to your `.mcp.json`:

```json
{
  "mcpServers": {
    "searchcarriers-risk-engine": {
      "command": "python3",
      "args": ["plugins/searchcarriers-risk-engine/scripts/risk_engine_mcp.py"],
      "env": {
        "SEARCHCARRIERS_API_KEY": "${SEARCHCARRIERS_API_KEY}"
      }
    }
  }
}
```

3. Set environment variables:

```bash
export SEARCHCARRIERS_API_KEY="your_id|your_token"
export SEARCHCARRIERS_TIER="pro"  # or "proplus" for vetting_check
```

4. Restart Claude Code. The MCP server registers five tools: `risk_score`,
   `qualification_reports`, `vetting_check`, `insurance_check`, and
   `compliance_audit`.

5. Verify:

```
What's the risk score for DOT 69494?
```

If configured correctly, this returns a risk assessment for Werner Enterprises. If the API key is missing, Carrier Intel is not installed, or the tier is insufficient, you will see a clear error message.
