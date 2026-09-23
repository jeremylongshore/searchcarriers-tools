# Risk Engine - User Journey

## Persona

**Name:** Sarah Chen
**Role:** Senior Freight Broker at a mid-size 3PL (75 employees, 300 loads/day)
**Goal:** Vet carriers fast enough to keep up with load volume without cutting corners on safety
**Tier:** Pro ($49/month -- she upgraded from Free after using Carrier Intel for a week)
**Current workflow:** She now uses Carrier Intel to pull carrier profiles in seconds instead of browsing FMCSA SAFER. But she still makes vetting decisions based on eyeballing the raw data -- "insurance looks OK, authority is active, rating is Satisfactory, I guess they're fine." There is no score, no consistency, no audit trail.
**Pain:** Last month, she approved a carrier that had a 38% vehicle out-of-service rate and a cargo insurance policy that expired 12 days after the pickup. The load was damaged in transit. The claim was $67,000. Her company's contingent cargo policy covered it, but her manager asked: "How did this carrier get through vetting?"

## Prerequisites

- [ ] SearchCarriers account with Pro tier or above -- upgrade at [searchcarriers.com/pricing](https://searchcarriers.com/pricing)
- [ ] API key set: `export SEARCHCARRIERS_API_KEY="your_id|your_token"`
- [ ] Carrier Intel plugin installed (Risk Engine depends on it for data)
- [ ] Risk Engine plugin installed -- configure in `.mcp.json` or copy to plugins directory
- [ ] Claude Code with MCP support

## Step-by-Step Walkthrough

### Step 1: Quick Risk Score

Sarah has a new carrier requesting to haul a temperature-controlled load from Dallas to Atlanta. The carrier is "COLD STAR LOGISTICS LLC" with DOT 3456789. She wants a quick risk read before spending time on the booking.

```
What's the risk score for DOT 3456789?
```

**What happens behind the scenes:**
1. Claude recognizes this as a risk assessment request
2. Claude calls Carrier Intel's `carrier_profile(dot_number="3456789")` to fetch carrier data
3. Claude passes the carrier data to Risk Engine's `risk_score(dot_number="3456789", carrier_data={...})`
4. Risk Engine normalizes the data, computes weighted scores across 4 dimensions, classifies the tier

**Expected output:**

```
RISK ASSESSMENT: COLD STAR LOGISTICS LLC (DOT 3456789)
=======================================================

COMPOSITE SCORE: 47 / 100   [ELEVATED]
Confidence: HIGH (91% data completeness)

BREAKDOWN
  Dimension        Score    Weight    Weighted    Key Factor
  -----------      -----    ------    --------    ----------
  Safety            58       35%       20.3       Vehicle OOS rate 31% (nat'l avg 21%)
  Insurance         35       25%        8.8       Cargo policy expires in 22 days
  Authority         28       20%        5.6       Active, but granted only 14 months ago
  Operational       30       20%        6.0       MCS-150 filed 19 months ago

FLAGS
  - Vehicle OOS rate (31%) exceeds national average (21%) by 48%
  - Cargo insurance expires 2026-03-20 (22 days from now)
  - Authority age: 14 months (below 18-month seasoning threshold)
  - MCS-150 approaching biennial deadline (19 of 24 months)

ADVISORY: This is a risk assessment tool, not a compliance guarantee.
Risk scores are advisory and do not replace professional judgment.
```

Sarah sees a score of 47 (ELEVATED). Not a dealbreaker, but the flags are specific: high OOS rate, cargo insurance about to expire, young authority. She knows exactly what to investigate further.

### Step 2: Insurance Deep Dive

The cargo insurance expiration flag concerns Sarah. She needs to know the full insurance picture before this carrier gets anywhere near a $200K reefer load.

```
Run an insurance check on DOT 3456789
```

**What happens behind the scenes:**
1. Claude calls `insurance_check` with the carrier data already in context (no additional API call needed)
2. Risk Engine parses insurance records, checks each policy status, coverage amounts, and expiration dates
3. Returns structured assessment

**Expected output:**

```
INSURANCE ANALYSIS: COLD STAR LOGISTICS LLC (DOT 3456789)
==========================================================

OVERALL STATUS: GAPS_DETECTED

POLICIES ON FILE
  Type     Coverage       Status    Effective     Expires       Days Left
  ----     --------       ------    ---------     -------       ---------
  BIPD     $1,000,000     Active    2025-09-01    2026-09-01    188 days
  Cargo    $100,000       Active    2025-03-20    2026-03-20    22 days  <<<
  Bond     --             None      --            --            --

FINDINGS
  [PASS]    BIPD coverage is active and meets minimum ($1M >= $750K)
  [WARNING] Cargo insurance expires in 22 days (threshold: 30 days)
  [WARNING] Cargo coverage $100K is at the minimum threshold
  [FAIL]    No surety bond on file (required if carrier holds broker authority)

RECOMMENDATION
  Do not book loads with this carrier beyond 2026-03-20 without confirming
  policy renewal. Coverage amount of $100K is adequate for general freight
  but insufficient for high-value temperature-controlled loads. Request
  proof of cargo insurance renewal before tendering.

ADVISORY: This is a risk assessment tool, not a compliance guarantee.
```

Sarah now has a clear picture. The cargo insurance is technically active but expires in 22 days, and $100K might not cover her reefer load. She asks the carrier's dispatcher for proof of renewal and requests a certificate of insurance with a higher cargo limit before proceeding.

### Step 3: Compliance Audit

Sarah's compliance manager asks her to run a regulatory check on the same carrier before they decide.

```
Run a compliance audit on DOT 3456789
```

**Expected output:**

```
COMPLIANCE AUDIT: COLD STAR LOGISTICS LLC (DOT 3456789)
========================================================

POSTURE: DEFICIENT

CHECKS
  Check                        Status      Detail
  -----                        ------      ------
  MCS-150 Filing               WARNING     Filed 2024-07-15 (19 months ago)
                                            Biennial update due by 2026-07-15
  Common Authority              PASS       Active since 2024-12-15
  Contract Authority            N/A        Not held
  Broker Authority              N/A        Not held
  Safety Rating                 WARNING     No rating on file (new carrier)
  Out-of-Service Orders         PASS       None on record
  Operating Status              PASS       Authorized For Hire, Interstate

SUMMARY
  2 of 5 applicable checks passed
  2 warnings (MCS-150 approaching deadline, no safety rating)
  0 failures
  Posture: DEFICIENT (warnings present but no critical failures)

NOTE: Carriers without a safety rating have not been audited by FMCSA.
This does not mean they are unsafe -- it means there is no federal
assessment on record. Consider the vehicle OOS rate (31%) as an
alternative safety indicator.

ADVISORY: This is a risk assessment tool, not a compliance guarantee.
```

The compliance manager sees that Cold Star is a newer carrier without a safety rating and an MCS-150 filing that is approaching the biennial deadline. Not disqualifying, but combined with the insurance concerns and the OOS rate, they decide to pass on this carrier for this particular load.

### Step 4: Vetting Check with Custom Rules (Pro+)

Sarah's company configures a named high-value-freight qualification. Its own
approved policy requires $250K minimum cargo insurance.

```
Vet DOT 3456789 with minimum cargo insurance of $250,000
```

**What happens behind the scenes:**
1. Claude calls `qualification_reports` for the named policy when it exists in
   SearchCarriers, or calls `vetting_check` with the complete approved rule set.
2. Risk Engine preserves each observed value, threshold, and missing field.
3. It returns the upstream or caller-policy verdict with per-rule evidence.

**Expected output (Pro+ tier):**

```
VETTING CHECK: COLD STAR LOGISTICS LLC (DOT 3456789)
=====================================================

VERDICT: FAIL

RULES EVALUATED
  Rule    Description                  Result    Detail
  ----    -----------                  ------    ------
  VET-01  Active operating authority   PASS      Common authority active since 2024-12-15
  VET-02  BIPD insurance >= $750K     PASS      $1,000,000 on file
  VET-03  Cargo insurance >= $250K    FAIL      $100,000 on file (custom min: $250K)
  VET-04  Safety rating acceptable    PASS      No rating (treated as acceptable for new carriers)
  VET-05  Vehicle OOS rate <= 40%     REVIEW    31% (below FAIL threshold 40%, above REVIEW threshold 25%)
  VET-06  Driver OOS rate <= 15%      PASS      8.2%
  VET-07  Authority age >= 90 days    PASS      14 months (427 days)
  VET-08  MCS-150 filed < 24 months   PASS      19 months ago

SUMMARY
  6 passed | 1 review | 1 failed
  Verdict: FAIL (1 failed rule: VET-03 cargo insurance below minimum)

FAILED RULES
  VET-03: Cargo insurance is $100,000. Your minimum is $250,000.
          Shortfall: $150,000. Carrier must increase coverage to qualify.

REVIEW RULES
  VET-05: Vehicle OOS rate 31% is between REVIEW threshold (25%) and
          FAIL threshold (40%). National average is 21%.

ADVISORY: This is a risk assessment tool, not a compliance guarantee.
```

**Expected output (Free/Basic tier -- insufficient):**

```
Carrier vetting requires a Pro+ subscription.
Your current tier: Pro

The vetting_check tool evaluates carriers against configurable qualification
rules and returns a PASS/REVIEW/FAIL verdict. It requires Pro+ for custom
rule thresholds.

Upgrade at https://searchcarriers.com/pricing

Tools available on your Pro tier:
  - risk_score: Composite 0-100 risk scoring
  - insurance_check: Insurance coverage analysis and gap detection
  - compliance_audit: MCS-150 filing and regulatory compliance audit
```

### Step 5: Full Pipeline (Vet and Report)

Sarah's manager wants a complete vetting report for a carrier they are considering adding to their preferred carrier list. Werner Enterprises (DOT 69494) -- a large, established carrier.

```
Give me a full vetting report on Werner Enterprises
```

**What happens behind the scenes (three-stage pipeline):**
1. Carrier Intel: `carrier_lookup("Werner Enterprises")` then `carrier_profile(dot=69494)`
2. Risk Engine: `risk_score` + `insurance_check` + `compliance_audit` + `vetting_check`
3. Ops Reporter: `generate_report` with all data combined

**Expected output (abbreviated -- Ops Reporter formats the final report):**

```
CARRIER VETTING REPORT: WERNER ENTERPRISES INC (DOT 69494)
============================================================
Generated: 2026-02-26 | Tier: Pro+

EXECUTIVE SUMMARY
  Risk Score:       18 / 100 (LOW)
  Vetting Verdict:  PASS (8/8 rules passed)
  Insurance Status: ADEQUATE (all policies active, coverage exceeds minimums)
  Compliance:       COMPLIANT (all checks passed)

  Recommendation: Carrier qualifies for preferred carrier list.

[... full report continues with detailed sections from Ops Reporter ...]
```

## Error Scenarios

### Scenario: Carrier Data Not Available

**Trigger:** User asks for a risk score but Carrier Intel cannot find the carrier.

```
What's the risk score for DOT 99999999?
```

**Response:**

```
Unable to retrieve carrier data for DOT 99999999.

Carrier Intel returned: No carrier found for DOT 99999999.

Risk Engine requires carrier data to compute a risk score. Please verify:
  - The DOT number is correct (check for typos)
  - The carrier exists in the FMCSA database
  - Try searching by name: "look up [carrier name]"
```

### Scenario: Sparse Carrier Data

**Trigger:** Scoring a new or small carrier with minimal FMCSA data.

```
Score DOT 4100000
```

**Response:**

```
RISK ASSESSMENT: NEW HORIZONS TRUCKING LLC (DOT 4100000)
=========================================================

COMPOSITE SCORE: 62 / 100   [HIGH]
Confidence: LOW (38% data completeness)

BREAKDOWN
  Dimension        Score    Weight    Weighted    Key Factor
  -----------      -----    ------    --------    ----------
  Safety            70       35%       24.5       No safety rating, no inspection data
  Insurance         50       25%       12.5       No insurance records on file
  Authority         45       20%        9.0       Active, granted 47 days ago
  Operational       40       20%        8.0       MCS-150 filed at registration (new)

DATA GAPS (confidence: LOW)
  - No safety rating on file
  - No inspection or crash data available
  - No insurance filings recorded in FMCSA system
  - Authority age below 90-day seasoning threshold
  - Power units: 3 (very small fleet)

NOTE: This carrier has limited data in the FMCSA system. The elevated
score reflects the absence of a track record, not necessarily poor
performance. New carriers without inspection history default to higher
risk until data accumulates. Request proof of insurance directly from
the carrier.

ADVISORY: This is a risk assessment tool, not a compliance guarantee.
```

### Scenario: API Timeout During Pipeline

**Trigger:** Carrier Intel's API calls time out while Risk Engine is waiting for data.

```
SearchCarriers API timed out while retrieving carrier data for DOT 3456789.

Risk Engine cannot score a carrier without data from Carrier Intel.

Options:
  1. Try again: "score DOT 3456789"
  2. Check API status: https://searchcarriers.com/status
  3. If you already have carrier data, provide it directly and
     Risk Engine can score it without additional API calls.
```

## FAQ

**Q: How is the composite risk score calculated?**
A: The score is a weighted average across four dimensions: Safety (35%), Insurance (25%), Authority (20%), and Operational (20%). Each dimension scores 0-100 based on specific factors (safety rating, OOS rates, insurance coverage, authority age, etc.). The composite is the sum of each dimension score multiplied by its weight. Lower scores indicate lower risk.

**Q: What is the difference between `risk_score`, `qualification_reports`, and `vetting_check`?**
A: `risk_score` is a disclosed legacy advisory model. `qualification_reports`
preserves named SearchCarriers personal/team results. `vetting_check` evaluates
a complete caller-owned policy. Use a named qualification or caller policy for
formal decisions; never present the advisory score as an official rating.

**Q: Can I customize the scoring weights?**
A: The legacy advisory model weights are fixed and disclosed. Formal policy
decisions belong in a named SearchCarriers qualification or the complete rule
set supplied to `vetting_check`.

**Q: What does a LOW confidence score mean?**
A: LOW confidence means less than 50% of the expected data fields were available for scoring. This typically happens with new carriers, very small carriers, or carriers with incomplete FMCSA filings. The risk score still computes, but missing data is treated as a risk factor (absence of data is worse than known data). Take LOW confidence scores with extra scrutiny.

**Q: Does Risk Engine store any data?**
A: No. Risk Engine is completely stateless. Carrier data enters as function arguments, gets scored, and the result is returned. Nothing is cached, logged to disk, or persisted. Your carrier vetting data stays in your Claude Code session.

**Q: Why does `vetting_check` require Pro+ when other tools are Pro?**
A: `vetting_check` supports configurable rules, which is an enterprise feature. Custom qualification criteria (different insurance minimums, OOS thresholds, authority age requirements) are how organizations standardize vetting across their teams. The Pro tools give you scores and assessments; Pro+ gives you configurable policy enforcement.

**Q: Can Risk Engine detect chameleon carriers?**
A: Not directly. Chameleon carrier detection (new authority, reused trucks from a revoked carrier) is done by Carrier Intel's `entity_map` tool. However, Risk Engine's authority dimension does penalize new authorities (< 90 days), and the compliance audit flags carriers without safety ratings. Used together, Carrier Intel's entity mapping + Risk Engine's scoring catch most chameleon patterns.
