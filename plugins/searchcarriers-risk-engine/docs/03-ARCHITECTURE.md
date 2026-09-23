# Risk Engine - Architecture

## System Context

Risk Engine is the **ANALYSIS** stage of the SearchCarriers stackable pipeline. It consumes structured carrier data from Carrier Intel and produces risk assessments that Ops Reporter formats into deliverables.

```
                    SEARCHCARRIERS STACKABLE PIPELINE
  =====================================================================

  +-----------------------+     +------------------------+     +-------------------------+
  |   CARRIER INTEL       |     |   RISK ENGINE          |     |   OPS REPORTER          |
  |   (INPUT)             |---->|   (ANALYSIS)           |---->|   (OUTPUT)              |
  |                       |     |                        |     |                         |
  |   carrier_lookup      |     |   risk_score           |     |   generate_report       |
  |   carrier_profile     |     |   vetting_check        |     |   generate_fleet        |
  |   entity_map          |     |   insurance_check      |     |   generate_compare      |
  |   fleet_summary       |     |   compliance_audit     |     |   export_data           |
  |                       |     |                        |     |                         |
  |   Min: Free           |     |   Min: Pro             |     |   Min: Pro              |
  +-----------------------+     +------------------------+     +-------------------------+
         ^                              ^                              |
         |                              |                              |
  SearchCarriers API v1         Consumes Carrier Intel         Consumes Risk Engine
  (data source)                 JSON output                    JSON output
```

**Upstream**: Carrier Intel provides the raw carrier data. In the standard pipeline flow, the MCP client calls Carrier Intel first (`carrier_profile`), then passes the structured JSON to Risk Engine tools. Risk Engine does not call the SearchCarriers API directly -- it operates on data, not endpoints.

**Downstream consumers**: Ops Reporter reads Risk Engine output to generate formatted vetting reports, risk summaries, and compliance documents. The risk score, vetting verdict, insurance assessment, and compliance posture all feed into report templates.

**Standalone usage**: Risk Engine can accept a DOT number directly. When it receives a DOT instead of pre-fetched carrier data, the MCP client orchestrates the Carrier Intel lookup automatically before running the risk analysis. From the user's perspective, they just say "score DOT 69494" and get a result.

## Component Design

| Component | Location | Responsibility |
|-----------|----------|---------------|
| **MCP Server** | `scripts/risk_engine_mcp.py` | Registers 4 MCP tools, handles incoming tool calls, delegates to scoring/vetting logic, enforces tier gating, returns structured JSON with assessments and disclaimers. |
| **Risk Scoring Module** | `scripts/scoring.py` (planned) | Pure functions for computing composite risk scores. Accepts normalized carrier data, returns weighted scores per dimension. No I/O, no API calls -- pure computation. |
| **Vetting Rules Module** | `scripts/vetting.py` (planned) | Rule evaluation engine. Accepts carrier data and threshold configuration, evaluates each rule, returns verdict with per-rule results. Stateless and configurable. |
| **Data Normalizer** | `scripts/normalize.py` (planned) | Transforms raw Carrier Intel JSON into a flat, consistent structure that scoring and vetting modules can consume. Handles missing fields, type coercion, and default values. |
| **Commands** | `commands/` (planned) | Slash command definitions mapping user input to MCP tool calls. `/sc-risk` for risk_score, `/sc-vet` for vetting_check. |
| **Embedded Skill** | `skills/` (planned) | Teaches the MCP client how to interpret risk scores, when to escalate REVIEW verdicts, and how to present risk assessments to freight professionals. |

## Data Flow

### Risk Score Computation

```
User: "What's the risk on DOT 69494?"
  |
  v
the MCP client identifies this as a risk assessment request
  |
  +--> Stage 1: Carrier Intel (if carrier data not already in context)
  |    carrier_profile(dot=69494)
  |    Returns: carrier object with selected v3 sections, authorities, insurances
  |
  +--> Stage 2: Risk Engine
  |    risk_score(dot_number="69494", carrier_data={...})
  |
  |    Internal flow:
  |    +--> Normalize carrier data (handle missing fields, type coercion)
  |    +--> Compute safety dimension (35% weight)
  |    |    - Safety rating: S=0, C=40, U=80, None=50
  |    |    - Vehicle OOS rate vs. national average
  |    |    - Driver OOS rate vs. national average
  |    |    - Crash indicator presence
  |    +--> Compute insurance dimension (25% weight)
  |    |    - Active BIPD policy present
  |    |    - BIPD coverage >= $750K
  |    |    - Active cargo insurance present
  |    |    - Days until nearest policy expiration
  |    +--> Compute authority dimension (20% weight)
  |    |    - Common/contract authority active
  |    |    - Authority age (days since grant)
  |    |    - Any revocations in history
  |    +--> Compute operational dimension (20% weight)
  |    |    - MCS-150 filing recency
  |    |    - Power unit count (too few = risk)
  |    |    - Driver-to-unit ratio
  |    |    - Interstate vs. intrastate
  |    +--> Weighted composite: sum(dimension_score * weight)
  |    +--> Classify tier: LOW / MODERATE / ELEVATED / HIGH / CRITICAL
  |    +--> Assess confidence based on data completeness
  |
  v
the MCP client receives risk assessment, presents to user
```

### Vetting Check Pipeline

```
User: "Run our named refrigerated-customer qualification"
  |
  v
the MCP client orchestrates:
  |
  +--> qualification_reports(          [Risk Engine]
  |      dot_number="69494"
  |    )
  |
  |    Internal flow:
  |    +--> Fetch API v2 personal/team qualification results
  |    +--> Select the exact qualification name
  |    +--> Preserve Pass/Review/Fail evidence and missing checks
  |    +--> Return the upstream result without local default thresholds
  |
  v
the MCP client presents: "PASS - Werner Enterprises qualifies on all 8 criteria"
```

### Full Pipeline Chain

```
User: "Vet Werner Enterprises and give me a report"
  |
  v
the MCP client orchestrates three-stage pipeline:
  |
  +--> Stage 1: Carrier Intel
  |    carrier_lookup("Werner Enterprises")  -> find DOT
  |    carrier_profile(dot=69494)            -> full profile
  |
  +--> Stage 2: Risk Engine (consumes Stage 1 output)
  |    risk_score(dot=69494, carrier_data)   -> composite risk: 18 (LOW)
  |    insurance_check(carrier_data)          -> ADEQUATE, no gaps
  |    compliance_audit(carrier_data)         -> COMPLIANT
  |    vetting_check(carrier_data)            -> PASS
  |
  +--> Stage 3: Ops Reporter (consumes Stage 1 + Stage 2 output)
  |    generate_report(carrier + risk + insurance + compliance + vetting)
  |    -> formatted vetting report with all assessments
  |
  v
User receives: complete vetting report with risk score, insurance status,
compliance audit, and qualification verdict
```

## Integration Points

### Input: Carrier Intel Data Contract

Risk Engine expects data in the format produced by Carrier Intel's `carrier_profile` tool:

```json
{
  "carrier": {
    "dot_number": "69494",
    "legal_name": "WERNER ENTERPRISES INC",
    "status_code": "A",
    "safety_rating": "S",
    "safety_rating_date": "2019-03-15",
    "power_units": 7880,
    "total_drivers": "12525",
    "mcs150_date": "2025-09-15",
    "carrier_operation": "A",
    "oos_rate_vehicle": 12.3,
    "oos_rate_driver": 4.1,
    "crash_total": 145
  },
  "authorities": [
    {
      "common_authority_status": "A",
      "contract_authority_status": "A",
      "broker_authority_status": "A",
      "status_since_date": "1981-01-27"
    }
  ],
  "insurances": [
    {
      "type": "BIPD",
      "coverage_amount": 5000000,
      "status": "Active",
      "effective_date": "2025-06-01",
      "expiration_date": "2026-06-01"
    },
    {
      "type": "CARGO",
      "coverage_amount": 250000,
      "status": "Active",
      "effective_date": "2025-06-01",
      "expiration_date": "2026-06-01"
    }
  ]
}
```

Risk Engine normalizes this data internally. If fields are missing, the normalizer substitutes sentinel values and flags them in the confidence assessment.

### Output: Risk Assessment Contract

Risk Engine produces assessments that Ops Reporter consumes:

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
    "breakdown": {
      "safety": { "score": 12, "weight": 0.35, "weighted": 4.2 },
      "insurance": { "score": 10, "weight": 0.25, "weighted": 2.5 },
      "authority": { "score": 5, "weight": 0.20, "weighted": 1.0 },
      "operational": { "score": 15, "weight": 0.20, "weighted": 3.0 }
    },
    "data_completeness": 0.94,
    "flags": [],
    "disclaimer": "Advisory only. Not a compliance guarantee or legal advice."
  }
}
```

## Security Model

**No direct API access:** Risk Engine does not hold or use the SearchCarriers API key. It operates on data passed from Carrier Intel through the model client's context. The API key stays in Carrier Intel's MCP server process.

**No data storage:** Risk Engine is stateless. Carrier data enters as function arguments, gets scored, and the result is returned. Nothing is written to disk, cached, or persisted. No database.

**Scoring transparency:** The composite score breakdown is always included in the response. Users can see exactly which factors contributed to the score. This is a deliberate design choice -- opaque scores erode trust in freight compliance.

**Disclaimers:** Every response from every tool includes the advisory disclaimer. This is not optional and is enforced at the response-building layer, not the presentation layer.

## Error Handling Strategy

| Error | Trigger | Response | Recovery |
|-------|---------|----------|----------|
| No carrier data provided | Tool called without carrier_data or dot_number | "Provide a DOT number or carrier data from carrier_profile" | the MCP client fetches via Carrier Intel |
| Carrier data incomplete | Key fields missing (no safety rating, no insurance) | Score computed with reduced confidence; missing fields flagged | User informed of data gaps |
| Tier insufficient | Free/Basic user calls risk_score | Structured tier error with upgrade URL | No retry; show pricing |
| Invalid DOT format | Non-numeric DOT input | "DOT number must be numeric" | User corrects input |
| Scoring module error | Unexpected data format or calculation error | Structured error with internal error code | Log error; return graceful failure |
| Carrier Intel unavailable | Pipeline stage 1 failed or timed out | "Unable to retrieve carrier data. Try again or provide data manually." | Suggest running carrier_profile first |

## Performance Requirements

| Operation | Target Latency | Max Latency | Notes |
|-----------|---------------|-------------|-------|
| `risk_score` (with pre-fetched data) | < 100ms | 500ms | Pure computation, no I/O |
| `risk_score` (with DOT, needs Carrier Intel) | < 3 seconds | 5 seconds | Includes Carrier Intel API calls |
| `vetting_check` (with pre-fetched data) | < 100ms | 500ms | Rule evaluation, no I/O |
| `insurance_check` | < 50ms | 200ms | Data analysis only |
| `compliance_audit` | < 50ms | 200ms | Data analysis only |
| MCP server startup | < 1 second | 3 seconds | Python import + module load |
| Tier check | < 1ms | N/A | In-memory via shared tier_gate |

Risk Engine is computation-bound, not I/O-bound. The performance bottleneck is always in Stage 1 (Carrier Intel's API calls), not Stage 2 (Risk Engine's scoring). When carrier data is already in the model client's context from a prior lookup, risk scoring adds negligible latency.
