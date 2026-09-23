# Ops Reporter - Technical Specification

## Tech Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Runtime | Python | 3.11+ | MCP server runtime |
| Protocol | MCP (Model Context Protocol) | 1.0+ | Tool registration and invocation |
| HTTP client | httpx | 0.27+ | Async SearchCarriers API requests |
| Tier gating | shared/tier_gate.py | -- | Shared tier enforcement across all plugins |
| Testing | pytest | 8.0+ | Unit and integration tests |

## Dependencies

```
httpx>=0.27
mcp>=1.0
```

Ops Reporter's formatting logic is implemented with Python string operations. `httpx` fetches current carrier sections from the documented SearchCarriers routes, and `mcp` provides the MCP server framework.

## File Structure

```
searchcarriers-ops-reporter/
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
|   +-- sc-report.md                   # /sc-report -> generate_report
|   +-- sc-compare.md                  # /sc-compare -> generate_compare
+-- agents/                            # Agent definitions (planned)
|   +-- ops-reporter.md                # Autonomous report generation agent
+-- skills/                            # Embedded skill (planned)
|   +-- searchcarriers-ops-reporter/
|       +-- SKILL.md                   # Claude skill for report generation
+-- scripts/
|   +-- ops_reporter_mcp.py            # MCP server implementation
|   +-- report.py                      # Vetting report generator (planned)
|   +-- compare.py                     # Comparison engine (planned)
|   +-- export.py                      # Multi-format exporter (planned)
|   +-- fleet.py                       # Fleet analysis formatter (planned)
|   +-- templates.py                   # Shared formatting utilities (planned)
|   +-- requirements.txt               # Python dependencies
+-- tests/                             # Test suite (planned)
    +-- test_report.py                 # Report generation unit tests
    +-- test_compare.py                # Comparison engine unit tests
    +-- test_export.py                 # Export formatter unit tests
    +-- test_fleet.py                  # Fleet formatter unit tests
    +-- test_integration.py            # Full pipeline integration tests
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SEARCHCARRIERS_API_KEY` | Yes | -- | Bearer token used directly for SearchCarriers API requests. Format: `{id}\|{token}`. |
| `SEARCHCARRIERS_TIER` | No | `free` | User's subscription tier. Determines tool access. Values: `free`, `basic`, `pro`, `proplus`, `smb`, `enterprise`. |
| `SEARCHCARRIERS_API_BASE` | No | `https://searchcarriers.com` | API origin override for testing against staging environments. |

## MCP Tool Schemas

### generate_report

Generates a formatted, multi-section vetting report from carrier data and risk assessments.

**Input:**
```json
{
  "dot_number": "string (required) - Carrier's USDOT number",
  "carrier_data": "object (optional) - Pre-fetched carrier data from carrier_profile. If omitted, the MCP client fetches via Carrier Intel.",
  "risk_data": "object (optional) - Pre-fetched risk assessment from risk_score, insurance_check, compliance_audit, vetting_check. If omitted, report is generated without risk sections."
}
```

**Output:**
```json
{
  "meta": {
    "tool": "generate_report",
    "timestamp": "2026-02-26T14:30:00Z",
    "dot_number": "69494",
    "format": "markdown",
    "tier": "pro",
    "sources": ["carrier_profile", "risk_score", "insurance_check", "compliance_audit", "vetting_check"],
    "data_completeness": 1.0
  },
  "report": "# CARRIER VETTING REPORT: WERNER ENTERPRISES INC (DOT 69494)\n...",
  "sections_populated": [
    "executive_summary",
    "company_overview",
    "safety_record",
    "insurance_status",
    "operating_authority",
    "risk_assessment",
    "qualification",
    "disclaimer"
  ],
  "sections_missing": [],
  "disclaimer": "This report is informational and does not constitute a compliance guarantee or legal advice."
}
```

**Report Sections:**

| Section | Required Data | Fallback When Missing |
|---------|--------------|----------------------|
| Executive Summary | risk_score, vetting_check | Shows "Not available" for risk metrics |
| Company Overview | carrier_profile | Required -- tool fails without carrier data |
| Safety Record | carrier_profile | Populated from carrier object fields |
| Insurance Status | insurance_check | Basic policy listing from carrier_profile insurances |
| Operating Authority | carrier_profile, compliance_audit | Authority status from carrier_profile; compliance posture marked N/A |
| Risk Assessment | risk_score | "Risk assessment not available" stub |
| Qualification | vetting_check | "Vetting check not available" stub |
| Disclaimer | (static) | Always present |

**Min Tier:** Pro

### generate_fleet

Generates a fleet analysis report with equipment breakdown, make distribution, and fleet age analysis.

**Input:**
```json
{
  "dot_number": "string (required) - Carrier's USDOT number",
  "fleet_data": "object (optional) - Pre-fetched fleet data from fleet_summary. If omitted, the MCP client fetches via Carrier Intel.",
  "carrier_data": "object (optional) - Pre-fetched carrier data for company name and fleet size context."
}
```

**Output:**
```json
{
  "meta": {
    "tool": "generate_fleet",
    "timestamp": "2026-02-26T15:00:00Z",
    "dot_number": "27021",
    "format": "markdown",
    "tier": "pro",
    "sources": ["fleet_summary"],
    "equipment_count": 2156
  },
  "report": "# FLEET ANALYSIS: KLLM TRANSPORT SERVICES INC (DOT 27021)\n...",
  "fleet_summary": {
    "power_units": 2156,
    "total_drivers": 2489,
    "driver_to_unit_ratio": 1.15,
    "equipment_by_type": {
      "Tractor": 987,
      "Reefer Trailer": 842,
      "Dry Van": 198,
      "Flatbed": 67,
      "Other": 62
    },
    "top_makes": {
      "FREIGHTLINER": 612,
      "KENWORTH": 298,
      "PETERBILT": 187,
      "VOLVO": 109,
      "INTERNATIONAL": 78
    },
    "notable": [
      "Reefer-dominant fleet (39.1% reefer trailers)",
      "Modern fleet (57.7% equipment from 2020+)"
    ]
  },
  "disclaimer": "This report is informational and does not constitute a compliance guarantee."
}
```

**Min Tier:** Pro

### generate_compare

Produces a side-by-side comparison table for 2 to 5 carriers.

**Input:**
```json
{
  "carriers": [
    {
      "dot_number": "string (required) - Carrier's USDOT number",
      "carrier_data": "object (optional) - Pre-fetched carrier data",
      "risk_data": "object (optional) - Pre-fetched risk assessment"
    }
  ]
}
```

**Validation:**
- `carriers` array length must be 2 to 5
- Each entry must include `dot_number`
- Duplicate DOT numbers are rejected

**Output:**
```json
{
  "meta": {
    "tool": "generate_compare",
    "timestamp": "2026-02-26T14:45:00Z",
    "dot_numbers": ["69494", "3456789", "27021"],
    "carrier_count": 3,
    "format": "markdown",
    "tier": "pro"
  },
  "report": "# CARRIER COMPARISON\n...",
  "comparison": {
    "metrics": [
      {
        "name": "Risk Score",
        "values": { "69494": 18, "3456789": 47, "27021": 22 },
        "best": "69494",
        "worst": "3456789"
      },
      {
        "name": "Vehicle OOS Rate",
        "values": { "69494": 12.3, "3456789": 31.0, "27021": 15.8 },
        "best": "69494",
        "worst": "3456789"
      }
    ],
    "recommendation": {
      "lowest_risk_dot": "69494",
      "lowest_risk_name": "WERNER ENTERPRISES INC",
      "summary": "Werner Enterprises has the lowest risk score (18) and strongest safety profile."
    }
  },
  "disclaimer": "This comparison is informational and does not constitute a compliance guarantee or legal advice."
}
```

**Comparison Metrics:**

| Metric | Field Source | Lower is Better |
|--------|------------|-----------------|
| Safety Rating | carrier_profile.safety_rating | N/A (categorical) |
| Risk Score | risk_score.composite_score | Yes |
| Risk Tier | risk_score.tier | Yes (LOW < CRITICAL) |
| Vehicle OOS Rate | carrier_profile.oos_rate_vehicle | Yes |
| Driver OOS Rate | carrier_profile.oos_rate_driver | Yes |
| BIPD Coverage | insurance_check.bipd_coverage | No (higher = better) |
| Cargo Coverage | insurance_check.cargo_coverage | No (higher = better) |
| Authority Age | computed from status_since_date | No (older = more established) |
| Power Units | carrier_profile.power_units | N/A (context-dependent) |
| Total Drivers | carrier_profile.total_drivers | N/A (context-dependent) |
| Vetting Verdict | vetting_check.verdict | N/A (PASS > REVIEW > FAIL) |

**Min Tier:** Pro

### export_data

Exports carrier data in JSON, CSV, or Markdown format.

**Input:**
```json
{
  "dot_number": "string (required) - Carrier's USDOT number",
  "carrier_data": "object (optional) - Pre-fetched carrier data from carrier_profile",
  "risk_data": "object (optional) - Pre-fetched risk assessment (included in JSON/Markdown exports)",
  "format": "string (required) - Output format: 'json', 'csv', or 'markdown'"
}
```

**Output (JSON format):**
```json
{
  "meta": {
    "tool": "export_data",
    "timestamp": "2026-02-26T14:50:00Z",
    "dot_number": "69494",
    "format": "json",
    "tier": "pro"
  },
  "data": {
    "carrier": { "...full carrier object..." },
    "authorities": [ "...authority records..." ],
    "insurances": [ "...insurance records..." ],
    "risk_assessment": { "...if available..." }
  },
  "disclaimer": "This data export is informational and does not constitute a compliance guarantee."
}
```

**Output (CSV format):**
```json
{
  "meta": {
    "tool": "export_data",
    "timestamp": "2026-02-26T14:50:00Z",
    "dot_number": "69494",
    "format": "csv",
    "tier": "pro"
  },
  "data": "dot_number,mc_number,legal_name,dba_name,status,safety_rating,...\n69494,MC-14983,WERNER ENTERPRISES INC,,Active,Satisfactory,...",
  "headers": [
    "dot_number", "mc_number", "legal_name", "dba_name", "status",
    "safety_rating", "power_units", "total_drivers", "phy_street",
    "phy_city", "phy_state", "phy_zip", "phone", "bipd_coverage",
    "bipd_status", "cargo_coverage", "cargo_status", "common_authority",
    "contract_authority", "broker_authority", "carrier_operation"
  ],
  "disclaimer": "This data export is informational and does not constitute a compliance guarantee."
}
```

**CSV Field Mapping:**

| CSV Header | Source Field | Description |
|-----------|-------------|-------------|
| `dot_number` | carrier.dot_number | USDOT number |
| `mc_number` | carrier.docket_numbers[0] | MC/MX docket number |
| `legal_name` | carrier.legal_name | Legal business name |
| `dba_name` | carrier.dba_name | Doing-business-as name |
| `status` | carrier.status_code mapped | Active, Inactive, etc. |
| `safety_rating` | carrier.safety_rating mapped | Satisfactory, Conditional, etc. |
| `power_units` | carrier.power_units | Number of power units |
| `total_drivers` | carrier.total_drivers | Total driver count |
| `phy_street` | carrier.phy_street | Physical street address |
| `phy_city` | carrier.phy_city | Physical city |
| `phy_state` | carrier.phy_state | Physical state (2-letter) |
| `phy_zip` | carrier.phy_zip | Physical ZIP code |
| `phone` | carrier.phone | Business phone number |
| `bipd_coverage` | insurances[BIPD].coverage_amount | BIPD coverage in dollars |
| `bipd_status` | insurances[BIPD].status | BIPD policy status |
| `cargo_coverage` | insurances[CARGO].coverage_amount | Cargo coverage in dollars |
| `cargo_status` | insurances[CARGO].status | Cargo policy status |
| `common_authority` | authorities[0].common_authority_status mapped | Active, Inactive, Revoked |
| `contract_authority` | authorities[0].contract_authority_status mapped | Active, Inactive, Revoked |
| `broker_authority` | authorities[0].broker_authority_status mapped | Active, Inactive, Revoked |
| `carrier_operation` | carrier.carrier_operation mapped | Authorized For Hire, etc. |

**Min Tier:** Pro

## Tier Gating Implementation

Ops Reporter uses the shared `plugins/shared/tier_gate.py` module. All four tools require Pro tier:

```python
# From plugins/shared/tier_gate.py
TOOL_TIERS = {
    "generate_report": "pro",
    "generate_fleet": "pro",
    "generate_compare": "pro",
    "export_data": "pro",
}
```

Tier check is the first operation in every tool handler. If the user's tier is insufficient, a structured error is returned immediately with no further processing.

```python
def tier_error(tool_name: str, user_tier: str) -> dict:
    return {
        "error": {
            "code": "INSUFFICIENT_TIER",
            "message": f"{tool_name} requires Pro tier. Your tier: {user_tier}.",
            "required_tier": "pro",
            "current_tier": user_tier,
            "upgrade_url": "https://searchcarriers.com/pricing",
        }
    }
```

## Report Formatting Implementation

### Template Helpers

```python
def format_header(carrier_name: str, dot: str, timestamp: str) -> str:
    """Generate report header."""
    return (
        f"# CARRIER VETTING REPORT: {carrier_name} (DOT {dot})\n"
        f"Generated: {timestamp} | Source: SearchCarriers API\n\n"
        f"---\n"
    )


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Generate Markdown table."""
    header_row = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["------"] * len(headers)) + " |"
    data_rows = "\n".join("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    return f"{header_row}\n{separator}\n{data_rows}"


def format_disclaimer() -> str:
    """Generate standard disclaimer text."""
    return (
        "\n---\n\n"
        "*This report is informational and does not constitute a compliance "
        "guarantee or legal advice. Risk scores and vetting verdicts are "
        "advisory. Carrier qualification decisions require professional "
        "judgment.*\n\n"
        "*Data source: SearchCarriers API (searchcarriers.com) | "
        "Report generated by Ops Reporter v0.2.0*"
    )


def format_currency(amount: int) -> str:
    """Format dollar amount: 5000000 -> '$5,000,000'."""
    return f"${amount:,}"


def format_percentage(value: float) -> str:
    """Format percentage: 12.3 -> '12.3%'."""
    return f"{value:.1f}%"


STATUS_MAP = {"A": "Active", "I": "Inactive", "R": "Revoked", "N": "Not Authorized"}
RATING_MAP = {"S": "Satisfactory", "C": "Conditional", "U": "Unsatisfactory"}
```

### Section Builders

Each report section is an independent function:

```python
def build_executive_summary(risk_data: dict | None, vetting_data: dict | None) -> str:
    if not risk_data:
        return (
            "## Executive Summary\n\n"
            "| Metric | Value |\n|--------|-------|\n"
            "| Risk Score | *Not available* |\n"
            "| Vetting Verdict | *Not available* |\n\n"
            "**Recommendation:** Risk assessment data not available.\n"
        )
    # ... build from risk_data and vetting_data

def build_company_overview(carrier: dict) -> str:
    # ... extract fields, build table

def build_safety_record(carrier: dict) -> str:
    # ... safety rating, OOS rates, crash data

def build_insurance_status(insurance_data: dict | None, raw_insurances: list) -> str:
    # ... policy table, findings list

def build_risk_assessment(risk_data: dict | None) -> str:
    if not risk_data:
        return "## Risk Assessment\n\n*Risk assessment not available.*\n"
    # ... composite score, breakdown table, flags

def build_qualification(vetting_data: dict | None) -> str:
    if not vetting_data:
        return "## Qualification\n\n*Vetting check not available.*\n"
    # ... verdict, rules table, failed rule details
```

## Testing Strategy

### Unit Tests (report generation)

Test each section builder with known carrier data and expected Markdown output:

- **Complete data**: Werner Enterprises with full risk assessment. All sections populated. Verify Markdown structure, table formatting, correct field values.
- **Missing risk data**: Carrier data only, no risk assessment. Verify graceful degradation -- risk sections show "not available" stubs.
- **Missing insurance records**: Carrier with empty insurance array. Verify insurance section handles absence.
- **Sparse data**: New carrier with minimal FMCSA data. Verify missing fields show "N/A" or "--" consistently.

### Unit Tests (comparison engine)

- **2 carriers**: Minimum comparison. Verify table has 2 data columns.
- **5 carriers**: Maximum comparison. Verify table has 5 data columns.
- **Mixed data quality**: One carrier with complete data, one with sparse data. Verify "N/A" handling in table cells.
- **Best/worst identification**: Verify correct carrier identified as best and worst for each metric.
- **Boundary validation**: Test with 1 carrier (error), 6 carriers (error).

### Unit Tests (export formatter)

- **JSON export**: Verify valid JSON output with json.loads(). Check meta block, carrier data, authorities, insurances.
- **CSV export**: Verify parseable CSV with csv.reader(). Check header row, data row, correct field count.
- **Markdown export**: Verify output matches generate_report format.
- **Invalid format**: Verify error message for unsupported format.

### Unit Tests (fleet formatter)

- **Complete fleet data**: Verify equipment breakdown percentages sum to 100%.
- **Single equipment type**: Verify table renders correctly with one row.
- **Empty equipment list**: Verify graceful handling with "no equipment records" message.
- **Notable characteristics detection**: Verify auto-detection of reefer-dominant, aging fleet, etc.

### Integration Tests (pipeline)

Require Carrier Intel and Risk Engine running with a valid API key. Marked with `@pytest.mark.integration`:

- **Full pipeline**: `carrier_profile("69494")` -> `risk_score(carrier_data)` -> `generate_report(carrier_data, risk_data)`. Verify complete report with all sections.
- **Comparison pipeline**: 3 carriers -> profiles -> risk scores -> `generate_compare`. Verify comparison table.
- **Export pipeline**: `carrier_profile("69494")` -> `export_data(format="csv")`. Verify CSV output.
- **Latency**: `generate_report` with pre-fetched data < 500ms.
- **Tier gating**: Confirm Free tier gets structured error from all 4 tools.

Run integration tests:

```bash
SEARCHCARRIERS_API_KEY="your_key" SEARCHCARRIERS_TIER="pro" pytest -v -m integration
```

## Performance Benchmarks

| Operation | Target p50 | Target p95 | Target p99 | Bottleneck |
|-----------|-----------|-----------|-----------|-----------|
| `generate_report` (pre-fetched data) | 20ms | 80ms | 200ms | String concatenation |
| `generate_report` (needs upstream data) | 3s | 5s | 8s | Carrier Intel + Risk Engine |
| `generate_fleet` (pre-fetched data) | 15ms | 50ms | 150ms | Equipment iteration |
| `generate_compare` (2 carriers, pre-fetched) | 25ms | 80ms | 200ms | Table construction |
| `generate_compare` (5 carriers, pre-fetched) | 50ms | 150ms | 400ms | Table construction |
| `generate_compare` (5 carriers, needs data) | 5s | 10s | 15s | 5x upstream data fetch |
| `export_data` (JSON) | 5ms | 15ms | 50ms | JSON serialization |
| `export_data` (CSV) | 10ms | 30ms | 80ms | Field mapping + CSV generation |
| `export_data` (Markdown) | 20ms | 80ms | 200ms | Delegates to report generator |
| MCP server cold start | 300ms | 700ms | 1.5s | Python import |
| Tier check | <1ms | <1ms | <1ms | In-memory lookup |

Ops Reporter is pure formatting with no computation and no external I/O. With pre-fetched data, every tool completes in under 500ms at p99. The only performance concern is upstream data fetching, which is bounded by Carrier Intel's API latency and Risk Engine's scoring time.

## Deployment

> **Multi-client path:** From the repository root, run `./scripts/setup-dev.sh`,
> export `SEARCHCARRIERS_API_KEY`, and let Grok Build, Claude Code, or another
> MCP client load the root `.mcp.json`. The client-specific copy steps below
> describe optional Claude plugin packaging. See
> [`MODEL-COMPATIBILITY.md`](../../../MODEL-COMPATIBILITY.md).

### Installation

1. Ensure Carrier Intel is installed (required for data):

```bash
ls plugins/searchcarriers-carrier-intel/.claude-plugin/plugin.json
```

2. Ensure Risk Engine is installed (recommended for complete reports):

```bash
ls plugins/searchcarriers-risk-engine/.claude-plugin/plugin.json
```

3. Add Ops Reporter MCP server to your `.mcp.json`:

```json
{
  "mcpServers": {
    "searchcarriers-ops-reporter": {
      "command": "python3",
      "args": ["plugins/searchcarriers-ops-reporter/scripts/ops_reporter_mcp.py"],
      "env": {
        "SEARCHCARRIERS_API_KEY": "${SEARCHCARRIERS_API_KEY}"
      }
    }
  }
}
```

4. Set environment variables:

```bash
export SEARCHCARRIERS_API_KEY="your_id|your_token"
export SEARCHCARRIERS_TIER="pro"
```

5. Restart Claude Code. The MCP server registers four tools: `generate_report`, `generate_fleet`, `generate_compare`, `export_data`.

6. Verify:

```
Give me a vetting report on DOT 69494
```

If configured correctly, this generates a complete vetting report for Werner Enterprises. If Carrier Intel or Risk Engine is not installed, the report includes available sections and notes what is missing.

### Full Pipeline Configuration

For the complete three-stage pipeline, your `.mcp.json` should include all three plugins:

```json
{
  "mcpServers": {
    "searchcarriers-carrier-intel": {
      "command": "python3",
      "args": ["plugins/searchcarriers-carrier-intel/scripts/carrier_intel_mcp.py"],
      "env": { "SEARCHCARRIERS_API_KEY": "${SEARCHCARRIERS_API_KEY}" }
    },
    "searchcarriers-risk-engine": {
      "command": "python3",
      "args": ["plugins/searchcarriers-risk-engine/scripts/risk_engine_mcp.py"],
      "env": { "SEARCHCARRIERS_API_KEY": "${SEARCHCARRIERS_API_KEY}" }
    },
    "searchcarriers-ops-reporter": {
      "command": "python3",
      "args": ["plugins/searchcarriers-ops-reporter/scripts/ops_reporter_mcp.py"],
      "env": { "SEARCHCARRIERS_API_KEY": "${SEARCHCARRIERS_API_KEY}" }
    }
  }
}
```

All three plugins share the same API key and run as independent MCP server processes. The MCP client orchestrates the data flow between them.
