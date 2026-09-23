# Risk Engine - Product Requirements

## Goals

1. **Produce a composite risk score in under 3 seconds.** Given a carrier's DOT number (or carrier data from Carrier Intel), return a 0-100 risk score with weighted breakdown across safety, insurance, authority, and operational dimensions. No manual data gathering required.
2. **Standardize carrier qualification decisions.** Replace ad-hoc broker judgment with configurable, repeatable vetting rules that produce a PASS/REVIEW/FAIL verdict. Same carrier, same rules, same answer -- regardless of who runs it or when.
3. **Detect insurance coverage gaps before they cause claims.** Automatically identify lapsed policies, insufficient coverage amounts, missing cargo insurance, and approaching expiration dates.
4. **Audit regulatory compliance posture.** Check MCS-150 filing recency, authority status, out-of-service orders, and FMCSA registration completeness in a single call.

## Non-Goals

1. **NOT a compliance guarantee.** Risk Engine provides risk assessment tools, not legal certification. A PASS verdict from `vetting_check` does not mean the carrier is guaranteed safe. It means the carrier met the configured qualification criteria at the time of the check.
2. **NOT legal advice.** Scores and verdicts are advisory. Brokers must exercise their own professional judgment. This is stated in every tool's output.
3. **NOT a replacement for broker judgment.** A carrier with a risk score of 30 (low risk) can still cause a claim. A carrier with 75 (elevated risk) might be the best option for a specific lane. The score informs the decision; it does not make the decision.
4. **NOT a data retrieval tool.** Risk Engine does not call the SearchCarriers API directly for carrier data. It consumes structured output from Carrier Intel. If a user asks for carrier data, the MCP client routes to Carrier Intel first, then passes the result to Risk Engine.
5. **NOT generating reports.** Formatted output (PDF, vetting reports, comparison tables) is the Ops Reporter plugin. Risk Engine produces structured JSON assessments that Ops Reporter consumes.

## User Stories

### US-01: Quick Risk Assessment

As a **freight broker**, I want to **get a numeric risk score for a carrier in seconds**, so that **I can make a quick go/no-go decision before tendering a load without spending 20 minutes on manual research**.

**Acceptance Criteria:**
- Returns a composite score from 0 (lowest risk) to 100 (highest risk)
- Score includes weighted breakdown: safety, insurance, authority, operational
- Response time under 3 seconds
- Works with a DOT number as input
- Includes a human-readable risk tier: LOW / MODERATE / ELEVATED / HIGH / CRITICAL

### US-02: Carrier Qualification Check

As a **compliance manager**, I want to **run a carrier through our company's qualification rules and get a PASS/REVIEW/FAIL verdict**, so that **every carrier is evaluated against the same criteria regardless of which broker is checking**.

**Acceptance Criteria:**
- Returns PASS, REVIEW, or FAIL verdict
- Lists every rule evaluated with individual pass/fail status
- Supports configurable rules (minimum insurance, maximum OOS rate, authority age)
- Failed rules include the specific reason (e.g., "Cargo insurance $50K below $100K minimum")
- REVIEW verdict triggers when some rules pass but others are borderline
- Requires Pro+ tier

### US-03: Insurance Validation

As a **freight broker**, I want to **verify a carrier's insurance coverage is active and adequate before booking**, so that **I do not tender a load to a carrier with lapsed or insufficient insurance**.

**Acceptance Criteria:**
- Reports status of each insurance type (BIPD, cargo, surety bond)
- Flags lapsed or expired policies
- Flags coverage amounts below industry minimums ($750K BIPD, $100K cargo)
- Warns on policies expiring within 30 days
- Identifies carriers with no cargo insurance on file

### US-04: Compliance Audit

As a **compliance analyst**, I want to **audit a carrier's regulatory compliance in one command**, so that **I can quickly identify carriers with stale MCS-150 filings, inactive authorities, or pending investigations**.

**Acceptance Criteria:**
- Checks MCS-150 filing date and flags if older than 24 months (biennial update requirement)
- Verifies all operating authorities are active
- Reports any out-of-service orders
- Flags carriers with "Conditional" or "Unsatisfactory" safety ratings
- Returns a compliance posture summary: COMPLIANT / DEFICIENT / NON-COMPLIANT

## Functional Requirements

### FR-01: Composite Risk Scoring

**Description:** The `risk_score` tool accepts carrier data (DOT number or structured carrier JSON from Carrier Intel) and computes a weighted composite risk score from 0 to 100.

**Scoring Dimensions:**

| Dimension | Weight | Factors |
|-----------|--------|---------|
| Safety | 35% | Safety rating, crash rate, inspection results, OOS rate, driver OOS rate |
| Insurance | 25% | Coverage status, policy amounts, gap history, cargo coverage presence |
| Authority | 20% | Authority age, status (active/revoked/pending), common/contract/broker status |
| Operational | 20% | MCS-150 recency, power unit count, driver-to-unit ratio, operation type |

**Score Tiers:**

| Score | Tier | Meaning |
|-------|------|---------|
| 0-25 | LOW | Stronger observed posture under the modeled factors |
| 26-50 | MEDIUM | Concerns worth human review |
| 51-75 | ELEVATED | Significant modeled concerns requiring resolution |
| 76-100 | HIGH | Highest modeled risk band; human decision required |

**Priority:** P0

### FR-02: Vetting Rules Engine

**Description:** `qualification_reports` preserves SearchCarriers personal and
team named qualification results from API v2. `vetting_check` applies a complete
caller-supplied policy and has no hidden default thresholds.

**Policy requirements:**

- Name the customer, commodity, or company policy that owns the decision.
- Provide every threshold used by `vetting_check`, or use the upstream named
  qualification result.
- Keep observed values, thresholds, missing evidence, and overrides in the
  result.
- Treat missing required evidence according to the named policy; never pass it
  silently.

**Verdict Logic:**
- **PASS**: All rules pass
- **REVIEW**: No FAIL rules, but one or more REVIEW rules triggered
- **FAIL**: One or more FAIL rules triggered

**Priority:** P0

### FR-03: Insurance Coverage Analysis

**Description:** The `insurance_check` tool analyzes a carrier's insurance records for coverage adequacy, gaps, and lapse warnings.

**Acceptance Criteria:**
- Parses insurance records from Carrier Intel's `carrier_profile` output
- Checks for active BIPD, cargo, and surety bond policies
- Flags any policy with status other than "Active"
- Compares coverage amounts against configurable minimums
- Calculates days until policy expiration and warns at 30/60/90 day thresholds
- Returns structured assessment: ADEQUATE / GAPS_DETECTED / LAPSED / NO_COVERAGE

**Priority:** P0

### FR-04: Regulatory Compliance Audit

**Description:** The `compliance_audit` tool audits a carrier's regulatory posture based on FMCSA registration data.

**Checks Performed:**
- MCS-150 filing date vs. biennial requirement (must be updated every 2 years)
- Operating authority status for all authority types
- Safety rating status and date
- Out-of-service orders
- Entity type verification (carrier vs. broker vs. both)

**Priority:** P1

### FR-05: Tier Gating

**Description:** All tools enforce subscription tier requirements before processing.

| Tool | Min Tier | Gate Behavior |
|------|----------|--------------|
| `risk_score` | Pro ($49/mo) | Returns tier error with upgrade URL |
| `insurance_check` | Pro ($49/mo) | Returns tier error with upgrade URL |
| `compliance_audit` | Pro ($49/mo) | Returns tier error with upgrade URL |
| `vetting_check` | Pro+ ($99/mo) | Returns tier error with upgrade URL |

**Priority:** P0

### FR-06: Structured Output for Pipeline

**Description:** All tools return structured JSON with consistent schema conventions for downstream consumption by Ops Reporter.

**Every response includes:**
- `meta` block: tool name, timestamp, DOT number, tier used
- `assessment` block: score/verdict/status with breakdown
- `disclaimer`: "Advisory only. Not a compliance guarantee."
- `data_completeness`: percentage of expected fields that were populated

**Priority:** P0

### FR-07: Missing Data Handling

**Description:** When carrier data is incomplete (missing safety rating, no insurance records, sparse FMCSA data), the engine must produce a meaningful result rather than failing.

**Strategy:**
- Each scoring dimension reports a confidence level based on data availability
- Missing safety data defaults to ELEVATED (absence of safety data is itself a risk factor)
- Missing insurance records flag as NO_COVERAGE (absence of records is worse than known bad records)
- Overall score includes a `confidence` field: HIGH (>80% data), MEDIUM (50-80%), LOW (<50%)

**Priority:** P0

### FR-08: Configurable Thresholds

**Description:** The `vetting_check` tool requires a complete caller-owned
policy. It never fills absent rules from package defaults.

**Accepted Overrides:**
- `min_bipd`: Minimum BIPD coverage amount
- `min_cargo`: Minimum cargo insurance amount
- `max_oos_rate`: Maximum vehicle OOS rate
- `max_driver_oos_rate`: Maximum driver OOS rate
- `min_authority_age_days`: Minimum authority age in days
- `max_mcs150_age_months`: Maximum MCS-150 filing age in months

**Priority:** P0

## MVP Scope

Historical v0.1.0 planning scope:

- [ ] `risk_score` -- composite 0-100 scoring with weighted breakdown
- [ ] `insurance_check` -- coverage analysis with gap detection
- [ ] `compliance_audit` -- MCS-150, authority, and regulatory checks
- [ ] `vetting_check` -- configurable rules engine with PASS/REVIEW/FAIL
- [ ] `qualification_reports` -- API v2 named qualification evidence
- [ ] Tier gating on all five tools
- [ ] Structured JSON output with meta blocks and disclaimers
- [ ] Missing data handling with confidence indicators

Deferred to v0.2.0:

- Historical trend analysis (score changes over time)
- Batch risk scoring (multiple DOTs in one call)
- Custom scoring weights (user-defined dimension weights)
- Score comparison (side-by-side risk profiles)

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|-------------|
| Risk score latency | Target: < 3 seconds | Timer in MCP tool handler |
| Vetting check latency | Target: < 3 seconds | Timer in MCP tool handler |
| Insurance check latency | Target: < 2 seconds | Timer (no additional API calls, data-only analysis) |
| False positive rate (HIGH risk for safe carriers) | Target: < 5% | Comparison against known carrier outcomes |
| False negative rate (LOW risk for bad carriers) | Target: < 2% | Comparison against carriers with claims/crashes |
| Tier gate accuracy | Target: 100% | Integration tests |
| Data completeness handling | Target: 100% (no unhandled missing fields) | Edge case tests with sparse carrier data |

## Dependencies

- **Carrier Intel plugin** -- Risk Engine consumes carrier data, authority records, and insurance records from Carrier Intel's structured output. If Carrier Intel is not available, Risk Engine cannot score carriers.
- **SearchCarriers REST API v1** -- Indirectly, via Carrier Intel. Risk Engine does not make direct API calls in the standard pipeline flow. However, it may accept a DOT number and call Carrier Intel on behalf of the user.
- **Shared tier_gate module** -- `plugins/shared/tier_gate.py` provides the `check_tier` function and `TOOL_TIERS` registry used by all plugins.
- **MCP protocol** -- Plugin runs as an MCP server; requires Grok Build, Claude Code, or another MCP-capable client.
