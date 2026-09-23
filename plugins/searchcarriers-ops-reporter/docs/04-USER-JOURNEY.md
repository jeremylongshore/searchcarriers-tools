# Ops Reporter - User Journey

## Persona

**Name:** Sarah Chen
**Role:** Senior Freight Broker and Compliance Lead at a mid-size 3PL (75 employees, 300 loads/day)
**Goal:** Produce professional vetting reports and carrier comparisons fast enough to keep up with load volume, with a standardized format that her compliance team and operations managers can rely on
**Tier:** Pro ($49/month -- she upgraded from Free after using Carrier Intel for a week, then added Risk Engine after the $67K cargo claim incident)
**Current workflow:** She uses Carrier Intel to pull carrier profiles and Risk Engine to score them. But when she needs to share findings with her team, she copies Claude's output into a Google Doc, reformats it, adds her own summary paragraph, and emails it. This takes 15 to 20 minutes per report. For carrier comparisons, she pastes multiple carrier profiles into a spreadsheet and manually aligns the columns. That takes 30 to 45 minutes.
**Pain:** Her operations manager just asked for vetting reports on 8 carriers by end of day. At 20 minutes each, that is 2.5 hours of formatting work. She has already spent the morning on data gathering and risk scoring -- now she needs the output stage.

## Prerequisites

- [ ] SearchCarriers account with Pro tier or above -- upgrade at [searchcarriers.com/pricing](https://searchcarriers.com/pricing)
- [ ] API key set: `export SEARCHCARRIERS_API_KEY="your_id|your_token"`
- [ ] Carrier Intel plugin installed (Ops Reporter depends on it for data)
- [ ] Risk Engine plugin installed (recommended for complete reports; optional for basic output)
- [ ] Ops Reporter plugin installed -- configure in `.mcp.json` or copy to plugins directory
- [ ] Claude Code with MCP support

## Journey 1: Full Pipeline Vetting Report

Sarah needs a complete vetting report for a carrier her team is considering adding to their preferred carrier list. She wants the full picture: company profile, safety, insurance, risk score, and a qualification verdict.

### Step 1: Trigger the Full Pipeline

```
Give me a full vetting report on Werner Enterprises
```

**What happens behind the scenes (three-stage pipeline):**
1. Claude calls Carrier Intel: `carrier_lookup("Werner Enterprises")` to find DOT 69494
2. Claude calls Carrier Intel: `carrier_profile(dot_number="69494")` for full profile
3. Claude calls Risk Engine: `risk_score`, `insurance_check`, `compliance_audit`, `vetting_check`
4. Claude calls Ops Reporter: `generate_report` with all upstream data combined

**Expected output:**

```markdown
# CARRIER VETTING REPORT: WERNER ENTERPRISES INC (DOT 69494)
Generated: 2026-02-26 14:30 UTC | Source: SearchCarriers API

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Risk Score | 18 / 100 (LOW) |
| Vetting Verdict | PASS |
| Insurance Status | ADEQUATE |
| Compliance Posture | COMPLIANT |

**Recommendation:** Carrier qualifies on all criteria. Strong safety record,
adequate insurance coverage, established operating authority. Suitable for
preferred carrier list.

## Company Overview

| Field | Value |
|-------|-------|
| Legal Name | WERNER ENTERPRISES INC |
| DBA | -- |
| DOT | 69494 |
| MC | MC-14983 |
| Entity Type | Carrier, Broker |
| Status | Active (since 1981-01-27) |
| Address | 14507 FRONTIER RD, OMAHA, NE 68138 |
| Phone | (402) 895-6640 |
| DUNS | 00-601-3120 |
| Power Units | 7,880 |
| Total Drivers | 12,525 |
| CDL Drivers | 12,525 |
| Operation | Authorized For Hire, Interstate |
| Cargo Types | General Freight, Household Goods, Metal/Sheets/Coils, Motor Vehicles, Refrigerated Food, Beverages, Chemicals |

## Safety Record

| Metric | Value | National Avg | Assessment |
|--------|-------|-------------|------------|
| Safety Rating | Satisfactory | -- | PASS |
| Rating Date | 2019-03-15 | -- | -- |
| Vehicle OOS Rate | 12.3% | 21.0% | Below average (good) |
| Driver OOS Rate | 4.1% | 5.5% | Below average (good) |
| Crash Indicator | Yes (large fleet) | -- | Expected for fleet size |
| Hazmat | Yes | -- | -- |

## Insurance Status

| Type | Coverage | Status | Effective | Expires | Days Left |
|------|----------|--------|-----------|---------|-----------|
| BIPD | $5,000,000 | Active | 2025-06-01 | 2026-06-01 | 95 |
| Cargo | $250,000 | Active | 2025-06-01 | 2026-06-01 | 95 |
| Surety Bond (Broker) | $75,000 | Active | 2025-06-01 | 2026-06-01 | 95 |

**Findings:**
- BIPD coverage active and exceeds minimum ($5M >= $750K)
- Cargo coverage active and exceeds minimum ($250K >= $100K)
- Broker surety bond active
- All policies have 90+ days remaining

## Operating Authority

| Authority Type | Status | Since |
|---------------|--------|-------|
| Common | Active | 1981-01-27 |
| Contract | Active | 1981-01-27 |
| Broker | Active | 2006-04-14 |
| Property | Yes | -- |
| Household Goods | Yes | -- |

**Compliance Posture:** COMPLIANT
- MCS-150 filed 2025-09-15 (5 months ago; biennial deadline: 2027-09-15)
- All authorities active
- No out-of-service orders

## Risk Assessment

**Composite Score: 18 / 100 (LOW)**
Confidence: HIGH (94% data completeness)

| Dimension | Score | Weight | Weighted | Key Factor |
|-----------|-------|--------|----------|------------|
| Safety | 12 | 35% | 4.2 | Satisfactory rating, OOS rates below average |
| Insurance | 10 | 25% | 2.5 | Full coverage, all policies active |
| Authority | 5 | 20% | 1.0 | 45-year operating history |
| Operational | 15 | 20% | 3.0 | Large fleet, adequate driver ratio |

**Flags:** None

## Qualification

**Verdict: PASS** (8 of 8 rules passed)

| Rule | Description | Result | Detail |
|------|------------|--------|--------|
| VET-01 | Active operating authority | PASS | Common authority active since 1981 |
| VET-02 | BIPD insurance >= $750K | PASS | $5,000,000 on file |
| VET-03 | Cargo insurance >= $100K | PASS | $250,000 on file |
| VET-04 | Safety rating acceptable | PASS | Satisfactory |
| VET-05 | Vehicle OOS rate <= 40% | PASS | 12.3% |
| VET-06 | Driver OOS rate <= 15% | PASS | 4.1% |
| VET-07 | Authority age >= 90 days | PASS | 16,437 days |
| VET-08 | MCS-150 filed < 24 months | PASS | 5 months ago |

---

*This report is informational and does not constitute a compliance guarantee
or legal advice. Risk scores and vetting verdicts are advisory. Carrier
qualification decisions require professional judgment.*

*Data source: SearchCarriers API (searchcarriers.com) | Report generated by
Ops Reporter v0.2.0*
```

Sarah copies this report and sends it directly to her operations manager. No reformatting needed. The report has every section her company requires for carrier qualification, with risk scores and per-rule vetting results that she used to assemble by hand.

### Step 2: Review the Report

Sarah scans the Executive Summary first: Risk Score 18 (LOW), Verdict PASS, Insurance ADEQUATE, Compliance COMPLIANT. Werner qualifies. She can move on to the next carrier.

If the Executive Summary showed anything other than PASS, she would scroll to the specific section for details. The report is designed for progressive disclosure: summary first, details below.

## Journey 2: Carrier Comparison for Load Tendering

Sarah has a high-value reefer load from Dallas to Atlanta. Three carriers have expressed interest. She needs to compare them objectively before making the tendering decision.

### Step 1: Request the Comparison

```
Compare these carriers for a reefer load:
- DOT 69494 (Werner Enterprises)
- DOT 3456789 (Cold Star Logistics)
- DOT 27021 (KLLM Transport)
```

**What happens behind the scenes:**
1. Claude fetches profiles and risk scores for all three carriers (Carrier Intel + Risk Engine)
2. Claude calls Ops Reporter: `generate_compare` with all three carrier data sets

**Expected output:**

```markdown
# CARRIER COMPARISON
Generated: 2026-02-26 14:45 UTC | Carriers: 3

| Metric | Werner Enterprises | Cold Star Logistics | KLLM Transport |
|--------|-------------------|--------------------|--------------------|
| DOT | 69494 | 3456789 | 27021 |
| MC | MC-14983 | MC-1108234 | MC-167291 |
| Status | Active | Active | Active |
| Safety Rating | Satisfactory | None | Satisfactory |
| **Risk Score** | **18 (LOW)** | 47 (ELEVATED) | **22 (MODERATE)** |
| Vehicle OOS Rate | 12.3% | 31.0% | 15.8% |
| Driver OOS Rate | 4.1% | 8.2% | 5.1% |
| BIPD Coverage | $5,000,000 | $1,000,000 | $5,000,000 |
| Cargo Coverage | $250,000 | $100,000 | $250,000 |
| Authority Age | 45 years | 14 months | 38 years |
| Power Units | 7,880 | 42 | 2,156 |
| Total Drivers | 12,525 | 55 | 2,489 |
| **Vetting Verdict** | **PASS** | REVIEW | **PASS** |

## Summary

**Lowest Risk:** Werner Enterprises (DOT 69494) -- Risk Score 18 (LOW)

**Comparison Notes:**
- Werner Enterprises and KLLM Transport both PASS all vetting criteria with
  low-to-moderate risk scores. Both are established carriers with 35+ year
  operating histories.
- Cold Star Logistics has ELEVATED risk (47) due to high vehicle OOS rate
  (31%), cargo insurance near minimum ($100K), and young authority (14 months).
  Verdict: REVIEW.
- For a high-value reefer load, KLLM Transport may be the best fit: they
  operate a large reefer fleet (842 reefer trailers) with a Satisfactory
  safety rating and moderate risk score.

---

*This comparison is informational and does not constitute a compliance
guarantee or legal advice.*
```

### Step 2: Make the Tendering Decision

Sarah sees the comparison table and makes her decision in 30 seconds:

- Werner is the safest overall, but is a massive truckload carrier -- she might not get capacity.
- KLLM specializes in reefer and has the second-best risk score. Best fit for this load.
- Cold Star is in REVIEW status. She would need to address the OOS rate and insurance coverage before considering them.

She tenders the load to KLLM and moves on to the next one.

## Journey 3: Data Export for TMS Import

Sarah's operations coordinator needs to add Werner Enterprises to their TMS (transportation management system). The TMS accepts CSV imports with standard field headers.

### Step 1: Request the Export

```
Export carrier data for DOT 69494 as CSV
```

**What happens behind the scenes:**
1. Claude checks if carrier data is already in context (it is, from the vetting report earlier)
2. Claude calls Ops Reporter: `export_data(dot_number="69494", carrier_data={...}, format="csv")`

**Expected output:**

```csv
dot_number,mc_number,legal_name,dba_name,status,safety_rating,power_units,total_drivers,phy_street,phy_city,phy_state,phy_zip,phone,bipd_coverage,bipd_status,cargo_coverage,cargo_status,common_authority,contract_authority,broker_authority,carrier_operation
69494,MC-14983,WERNER ENTERPRISES INC,,Active,Satisfactory,7880,12525,14507 FRONTIER RD,OMAHA,NE,68138,(402) 895-6640,5000000,Active,250000,Active,Active,Active,Active,Authorized For Hire Interstate
```

The operations coordinator copies this into a file, imports it into the TMS, and the carrier record is created without retyping a single field.

### Step 2: JSON Export for Developer Integration

Sarah's dev team is building an internal carrier dashboard. They need carrier data in JSON format.

```
Export DOT 69494 as JSON
```

**Expected output:**

```json
{
  "meta": {
    "tool": "export_data",
    "timestamp": "2026-02-26T14:50:00Z",
    "dot_number": "69494",
    "format": "json",
    "source": "SearchCarriers API"
  },
  "carrier": {
    "dot_number": "69494",
    "legal_name": "WERNER ENTERPRISES INC",
    "dba_name": null,
    "mc_number": "MC-14983",
    "status_code": "A",
    "safety_rating": "S",
    "safety_rating_date": "2019-03-15",
    "power_units": 7880,
    "total_drivers": "12525",
    "phy_city": "OMAHA",
    "phy_state": "NE",
    "phy_zip": "68138",
    "phy_street": "14507 FRONTIER RD",
    "phone": "(402) 895-6640",
    "carrier_operation": "A",
    "hazmat": true,
    "mcs150_date": "2025-09-15"
  },
  "authorities": [
    {
      "docket_number": "MC-14983",
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
  ],
  "disclaimer": "This data export is informational and does not constitute a compliance guarantee."
}
```

## Journey 4: Fleet Analysis Report

Sarah's load planner needs to verify that a carrier has reefer capacity before booking a temperature-controlled shipment.

### Step 1: Request Fleet Report

```
Generate a fleet report for DOT 27021
```

**What happens behind the scenes:**
1. Claude calls Carrier Intel: `fleet_summary(dot_number="27021")` for equipment data
2. Claude calls Ops Reporter: `generate_fleet(dot_number="27021", fleet_data={...})`

**Expected output:**

```markdown
# FLEET ANALYSIS: KLLM TRANSPORT SERVICES INC (DOT 27021)
Generated: 2026-02-26 15:00 UTC | Source: SearchCarriers API

## Fleet Overview

| Metric | Value |
|--------|-------|
| Power Units | 2,156 |
| Total Drivers | 2,489 |
| Driver/Unit Ratio | 1.15 |
| Fleet Category | Large (1,000+) |

## Equipment Breakdown

| Type | Count | % of Fleet |
|------|-------|-----------|
| Tractors | 987 | 45.8% |
| Reefer Trailers | 842 | 39.1% |
| Dry Vans | 198 | 9.2% |
| Flatbeds | 67 | 3.1% |
| Other | 62 | 2.8% |

## Top Makes

| Manufacturer | Units |
|-------------|-------|
| Freightliner | 612 |
| Kenworth | 298 |
| Peterbilt | 187 |
| Volvo | 109 |
| International | 78 |

## Fleet Age Distribution

| Year Range | Count | % of Fleet |
|-----------|-------|-----------|
| 2020-2026 | 1,245 | 57.7% |
| 2015-2019 | 634 | 29.4% |
| 2010-2014 | 198 | 9.2% |
| Pre-2010 | 79 | 3.7% |

## Notable Characteristics

- **Reefer-dominant fleet**: 39.1% of equipment is reefer trailers,
  indicating temperature-controlled freight specialization
- **Modern fleet**: 57.7% of equipment is from 2020 or later
- **Healthy driver ratio**: 1.15 drivers per power unit suggests
  adequate staffing without excessive turnover indicators

---

*This report is informational and does not constitute a compliance guarantee.*
*Data source: SearchCarriers API (searchcarriers.com)*
```

Sarah's load planner confirms KLLM has 842 reefer trailers with a modern fleet -- exactly what they need for the Dallas-Atlanta reefer run.

## Error Scenarios

### Scenario: Insufficient Tier

**Trigger:** Free user attempts to generate a vetting report.

```
Give me a vetting report on DOT 69494
```

**Response:**

```
Report generation requires a Pro subscription.
Your current tier: Free

Ops Reporter produces formatted vetting reports, carrier comparisons,
fleet analyses, and data exports. All four tools require Pro tier.

Upgrade at https://searchcarriers.com/pricing

Tools available on your Free tier (via Carrier Intel):
  - carrier_lookup: Search carriers by DOT, MC, name, or VIN
  - carrier_profile: Full profile with authorities and insurance
  - fleet_summary: Equipment roster and fleet breakdown
```

### Scenario: Risk Data Not Available

**Trigger:** User requests a vetting report but Risk Engine is not installed or has not been run.

```
Generate a report for DOT 69494
```

**Response (partial report):**

```markdown
# CARRIER VETTING REPORT: WERNER ENTERPRISES INC (DOT 69494)
Generated: 2026-02-26 15:10 UTC | Source: SearchCarriers API

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Risk Score | *Not available* |
| Vetting Verdict | *Not available* |
| Insurance Status | *Not available* |
| Compliance Posture | *Not available* |

**Recommendation:** Risk assessment data not available. Report contains
carrier profile data only. Run risk_score and vetting_check for a
complete vetting report.

## Company Overview
[... populated from Carrier Intel data ...]

## Safety Record
[... populated from Carrier Intel data ...]

## Insurance Status
*Insurance analysis not available. Run insurance_check for DOT 69494
to include coverage assessment in this report.*

## Risk Assessment
*Risk assessment not available. Run risk_score for DOT 69494 to
include risk analysis in this report.*

## Qualification
*Vetting check not available. Run vetting_check for DOT 69494 to
include qualification results in this report.*

---
*This report is informational and does not constitute a compliance guarantee.*
```

The report degrades gracefully. Carrier profile sections are populated from Carrier Intel data. Risk-dependent sections indicate what is missing and how to get it. The user gets the best report possible with the available data.

### Scenario: Too Many Carriers for Comparison

**Trigger:** User requests comparison of more than 5 carriers.

```
Compare DOT 69494, DOT 3456789, DOT 27021, DOT 12345, DOT 67890,
DOT 11111, DOT 22222
```

**Response:**

```
Carrier comparison supports a maximum of 5 carriers. You provided 7.

Please select 5 or fewer carriers to compare. For individual carrier
analysis, use generate_report with a single DOT number.
```

### Scenario: Single Carrier Comparison Request

**Trigger:** User requests comparison with only 1 carrier.

```
Compare DOT 69494
```

**Response:**

```
Comparison requires at least 2 carriers. You provided 1.

For a single carrier analysis, use:
  - generate_report: Full vetting report with risk assessment
  - generate_fleet: Fleet composition and equipment analysis
  - export_data: Export carrier data in JSON, CSV, or Markdown
```

### Scenario: Invalid Export Format

**Trigger:** User requests export in an unsupported format.

```
Export DOT 69494 as PDF
```

**Response:**

```
PDF export is not supported in this version. Supported formats:
  - json: Structured JSON with full carrier data
  - csv: Flat CSV for TMS import or spreadsheet analysis
  - markdown: Formatted report (same as generate_report output)

Tip: For PDF output, export as Markdown and convert with pandoc:
  pandoc report.md -o report.pdf
```

## FAQ

**Q: Does Ops Reporter make API calls?**
A: No. Ops Reporter formats data that has already been retrieved by Carrier Intel and analyzed by Risk Engine. It is a pure formatting layer. The only network-dependent step is the upstream data fetching, which Claude handles before calling Ops Reporter.

**Q: Can I generate a report without Risk Engine?**
A: Yes. Ops Reporter generates a partial report using only Carrier Intel data. The Company Overview, Safety Record, and basic Insurance sections are populated. The Risk Assessment, Qualification, and Insurance Analysis sections show "not available" with instructions to run the relevant Risk Engine tools.

**Q: What if some carriers in a comparison are missing data?**
A: The comparison table shows "N/A" for any missing metrics. A footnote explains which carriers had incomplete data. The comparison proceeds with whatever data is available rather than failing.

**Q: Can I customize the report format?**
A: Not in v0.1. The report template is standardized. Custom templates (section order, included/excluded sections, company branding) are planned for v0.2.

**Q: How do I save the report to a file?**
A: Copy the Markdown output and save it as a `.md` file. For automated saving, pipe Claude Code output to a file. The report is plain Markdown text -- no special tooling needed to save or share it.

**Q: What CSV headers does export_data use?**
A: The CSV headers map to standard TMS fields: `dot_number`, `mc_number`, `legal_name`, `dba_name`, `status`, `safety_rating`, `power_units`, `total_drivers`, `phy_street`, `phy_city`, `phy_state`, `phy_zip`, `phone`, `bipd_coverage`, `bipd_status`, `cargo_coverage`, `cargo_status`, `common_authority`, `contract_authority`, `broker_authority`, `carrier_operation`. Headers are lowercase with underscores for compatibility with most import tools.

**Q: Can I compare carriers across different reports generated at different times?**
A: Each report and comparison is a point-in-time snapshot. Ops Reporter does not store previous reports or support temporal comparison. If you need to compare a carrier's data from two different dates, you would need to generate both reports and compare manually. Historical comparison is planned for v0.2.

**Q: Why is everything Pro tier? Why not offer basic reports on Free?**
A: Ops Reporter's value depends on the full pipeline -- Carrier Intel data plus Risk Engine analysis. Since Risk Engine is Pro, and the most useful reports embed risk scores and vetting verdicts, gating Ops Reporter at Pro maintains a clean tier boundary. Free users get raw data via Carrier Intel; Pro users get the complete workflow from data to analysis to formatted output.
