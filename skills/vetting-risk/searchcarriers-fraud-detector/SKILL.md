---
name: searchcarriers-fraud-detector
description: Detects chameleon carriers and fraud indicator patterns by cross-referencing entity data across DOT numbers. Use when investigating a suspicious carrier or screening for fraud risk.
allowed-tools: Read,Grep,Bash(curl:*),Bash(python:*)
metadata:
  tier: pro
version: 0.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Claude Code or another MCP-capable client; Python 3.10+; network access to searchcarriers.com; an appropriate SearchCarriers API subscription.
tags:
- searchcarriers
- motor-carrier
- vetting-risk
---

# Fraud Detector

## Overview

Chameleon carriers are the freight industry's most dangerous fraud pattern. When an unsafe carrier accumulates a bad safety record — crashes, out-of-service orders, insurance lapses, or FMCSA enforcement actions — they shut down their DOT and reopen under a new one. Same trucks, same drivers, same dangerous operation, but a clean record on paper. The FMCSA estimates that chameleon carriers are involved in a disproportionate number of fatal crashes because they evade the safety oversight system by design.

This skill implements a multi-layered fraud detection analysis. It examines the carrier's own record for FMCSA-flagged indicators (prior revocation), then performs entity-level cross-referencing across officer names, physical addresses, phone numbers, and equipment VINs to find connections to other DOT numbers. Each indicator is scored, and the results are compiled into a fraud risk assessment with evidence for every finding.

## Prerequisites

- **Minimum tier**: Pro
- Environment variable `SEARCHCARRIERS_API_KEY` must be set with a valid Pro-tier API key.
- The carrier's DOT number must be known. If only an MC number or name is available, use the `/search` endpoint first.
- `curl` and `python3` must be available in the execution environment.
- Fraud detection requires multiple cross-referencing searches. Expect 5-15 API calls per analysis depending on the number of entities to cross-reference.

## Instructions

### Step 1: Gather the Carrier's Core Record

Fetch the full carrier record to extract all entity identifiers.

```bash
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?dotNumber={dot}"
```

Extract and store these fields for cross-referencing:
- `dot_number` — The DOT being investigated
- `legal_name` — Legal business name
- `dba_name` — Doing-business-as name (if different)
- `physical_address` — Street, city, state, zip
- `mailing_address` — May differ from physical
- `phone` — Phone number on file
- `company_officers` — List of officer names and titles
- `add_date` — When this DOT was registered
- `status_code` — Current status
- `prior_revoke_flag` — "Y" if FMCSA flagged prior revocation
- `prior_revoke_dot_number` — The previous DOT number
- `power_units` — Number of trucks
- `total_drivers` — Number of drivers
- `carrier_operation` — Type of operation
- `hm_ind` — Hazmat indicator

### Step 2: Check FMCSA-Flagged Indicators

These are indicators that FMCSA itself has flagged in the carrier record.

#### Indicator 1: Prior Revocation Flag

```python
def check_prior_revocation(carrier):
    indicators = []

    if carrier.get("prior_revoke_flag") == "Y":
        prev_dot = carrier.get("prior_revoke_dot_number", "unknown")
        indicators.append(
            {
                "id": "FMCSA_PRIOR_REVOKE",
                "severity": "HIGH",
                "confidence": "CONFIRMED",
                "finding": f"FMCSA has flagged this carrier as previously operating under DOT {prev_dot}, which was revoked.",
                "evidence": f"prior_revoke_flag = 'Y', prior_revoke_dot_number = '{prev_dot}'",
                "action": f"Investigate DOT {prev_dot} to understand why it was revoked.",
            }
        )

        # If we know the previous DOT, fetch its record too
        return indicators, prev_dot

    return indicators, None
```

If a prior DOT exists, fetch its record to understand the revocation:

```bash
# Investigate the previous DOT
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?dotNumber={prior_dot}"
```

Compare the two records: same officers? Same address? Same equipment? This builds the evidentiary chain.

#### Indicator 2: New Authority with Experienced Officers

A truly new carrier would have new-to-industry officers. Experienced officers on a brand-new DOT is suspicious.

```python
from datetime import datetime


def check_new_authority_experienced_officers(carrier):
    indicators = []

    add_date = datetime.strptime(carrier["add_date"], "%Y-%m-%d")
    age_months = (datetime.now() - add_date).days / 30

    if age_months < 18 and carrier.get("company_officers"):
        # Flag for cross-reference investigation
        indicators.append(
            {
                "id": "NEW_DOT_WITH_OFFICERS",
                "severity": "MEDIUM",
                "confidence": "REQUIRES_INVESTIGATION",
                "finding": f"DOT is only {int(age_months)} months old but lists established company officers.",
                "evidence": f"add_date = {carrier['add_date']}, officers = {carrier['company_officers']}",
                "action": "Cross-reference officer names against other DOT numbers.",
            }
        )

    return indicators
```

#### Indicator 3: Unusually Large Fleet for New Carrier

New carriers typically start small. A new DOT with a large fleet suggests trucks were transferred from a shut-down operation.

```python
def check_fleet_size_vs_age(carrier):
    indicators = []

    add_date = datetime.strptime(carrier["add_date"], "%Y-%m-%d")
    age_months = (datetime.now() - add_date).days / 30
    power_units = int(carrier.get("power_units", 0))

    # Heuristic: new carriers rarely start with more than 10-15 trucks
    if age_months < 12 and power_units > 15:
        indicators.append(
            {
                "id": "LARGE_FLEET_NEW_CARRIER",
                "severity": "MEDIUM",
                "confidence": "HEURISTIC",
                "finding": f"Carrier is {int(age_months)} months old but reports {power_units} power units. "
                f"This is unusual for a new operation.",
                "evidence": f"add_date = {carrier['add_date']}, power_units = {power_units}",
                "action": "Check equipment VINs for transfers from other DOTs.",
            }
        )

    return indicators
```

### Step 3: Entity Cross-Referencing

This is where fraud detection gets powerful. Search for connections between the target carrier and other entities in the FMCSA database.

#### Cross-Reference by Officer Names

For each officer listed on the carrier, search for other DOTs with the same officer.

```bash
# Search for other carriers with the same officer name
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?superSearchTerm=JOHN%20SMITH"
```

For each result that is a **different** DOT number:
- Check if the other DOT is inactive or revoked
- Check if the other DOT has safety violations, crashes, or OOS orders
- If the other DOT was shut down for safety reasons and this officer now appears on the new DOT, this is a strong chameleon indicator

```python
def cross_reference_officers(carrier, search_results_by_officer):
    indicators = []
    target_dot = carrier["dot_number"]

    for officer_name, results in search_results_by_officer.items():
        other_dots = [r for r in results if str(r.get("dot_number")) != str(target_dot)]

        for other in other_dots:
            other_status = other.get("status_code", "")
            connection = {
                "officer": officer_name,
                "other_dot": other["dot_number"],
                "other_name": other.get("legal_name", ""),
                "other_status": other_status,
            }

            if other_status in ["I", "REVOKED", "OOS"]:  # Inactive, Revoked, Out of Service
                indicators.append(
                    {
                        "id": "OFFICER_ON_INACTIVE_DOT",
                        "severity": "HIGH",
                        "confidence": "CONFIRMED",
                        "finding": f"Officer '{officer_name}' also appears on DOT {other['dot_number']} "
                        f"({other.get('legal_name', '')}) which has status '{other_status}'.",
                        "evidence": json.dumps(connection),
                        "action": f"Investigate DOT {other['dot_number']} safety record and reason for shutdown.",
                    }
                )
            elif other_status == "A":  # Active
                indicators.append(
                    {
                        "id": "OFFICER_ON_MULTIPLE_ACTIVE_DOTS",
                        "severity": "LOW",
                        "confidence": "INFORMATIONAL",
                        "finding": f"Officer '{officer_name}' also appears on active DOT {other['dot_number']} "
                        f"({other.get('legal_name', '')}). Multiple active DOTs is not inherently "
                        f"suspicious but warrants awareness.",
                        "evidence": json.dumps(connection),
                        "action": "No immediate action required. Note the connection.",
                    }
                )

    return indicators
```

#### Cross-Reference by Physical Address

Carriers operating from the same physical address may be connected.

```bash
# Search by city and state to find co-located carriers
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?addressCity=DALLAS&addressState=TX&zipCode=75201"
```

Filter results for exact or near-exact address matches. Flag if a co-located carrier is inactive or has a bad safety record.

#### Cross-Reference by Phone Number

Shared phone numbers between DOTs are a strong connection indicator.

```bash
# Search by phone number or use superSearchTerm
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/search?superSearchTerm=2145551234"
```

#### Cross-Reference by Equipment VINs

Equipment transfers are the strongest evidence of a chameleon carrier. The same trucks appearing on a new DOT that were on a shut-down DOT is near-conclusive.

```bash
# Fetch equipment for the target carrier
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v3/company/{dot}/equipment?perPage=50"

# For each VIN, search to see if it appears elsewhere
curl -s -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  "https://searchcarriers.com/api/v1/search/by-vin/{vin_number}"
```

```python
def cross_reference_equipment(target_dot, equipment_records):
    indicators = []

    for equip in equipment_records:
        vin = equip.get("vin", "")
        if not vin:
            continue

        # Search for this VIN across all carriers
        # (Assume vin_search_results comes from the API call above)
        for match in vin_search_results:
            if str(match.get("dot_number")) != str(target_dot):
                indicators.append(
                    {
                        "id": "SHARED_EQUIPMENT",
                        "severity": "CRITICAL",
                        "confidence": "CONFIRMED",
                        "finding": f"VIN {vin} ({equip.get('year', '')} {equip.get('make', '')} "
                        f"{equip.get('model', '')}) also registered to DOT "
                        f"{match['dot_number']} ({match.get('legal_name', '')}).",
                        "evidence": f"VIN = {vin}, target DOT = {target_dot}, "
                        f"other DOT = {match['dot_number']}",
                        "action": f"Investigate DOT {match['dot_number']} status and safety record. "
                        f"Equipment transfers from shut-down carriers are strong chameleon evidence.",
                    }
                )

    return indicators
```

**Note on VIN cross-referencing**: This is API-intensive. For carriers with large fleets, consider sampling a subset of VINs (e.g., 10-20) rather than checking every single one. Prioritize newer equipment additions.

### Step 4: Calculate the Fraud Risk Score

Aggregate all indicators into a risk score.

```python
def calculate_fraud_risk(indicators):
    severity_weights = {"CRITICAL": 40, "HIGH": 25, "MEDIUM": 10, "LOW": 3}

    total_score = sum(severity_weights.get(i["severity"], 0) for i in indicators)

    if total_score == 0:
        risk_level = "LOW"
        assessment = "No fraud indicators detected. Carrier appears legitimate."
    elif total_score <= 15:
        risk_level = "LOW"
        assessment = (
            "Minor indicators found but no pattern of fraud. "
            "Standard vetting procedures are sufficient."
        )
    elif total_score <= 35:
        risk_level = "MEDIUM"
        assessment = (
            "Multiple indicators suggest possible connections to other entities. "
            "Enhanced due diligence recommended before tendering freight."
        )
    elif total_score <= 60:
        risk_level = "HIGH"
        assessment = (
            "Strong pattern of fraud indicators detected. "
            "Carrier shows characteristics consistent with a chameleon operation. "
            "Do not tender freight without thorough manual investigation."
        )
    else:
        risk_level = "CRITICAL"
        assessment = (
            "Overwhelming evidence of chameleon carrier pattern. "
            "Multiple confirmed connections to shut-down or revoked entities. "
            "Refuse to broker. Report to FMCSA. Document all evidence."
        )

    return {
        "score": total_score,
        "risk_level": risk_level,
        "assessment": assessment,
        "indicator_count": len(indicators),
        "critical_count": sum(1 for i in indicators if i["severity"] == "CRITICAL"),
        "high_count": sum(1 for i in indicators if i["severity"] == "HIGH"),
        "medium_count": sum(1 for i in indicators if i["severity"] == "MEDIUM"),
        "low_count": sum(1 for i in indicators if i["severity"] == "LOW"),
    }
```

### Step 5: Generate the Fraud Analysis Report

```
========================================
FRAUD ANALYSIS REPORT
========================================
Target DOT: {dot_number}
Carrier: {legal_name}
Report Date: {today}
Analysis Type: Chameleon Carrier / Fraud Indicator Screen

CARRIER PROFILE
  DOT: {dot_number}
  Legal Name: {legal_name}
  DBA: {dba_name}
  Status: {status_code}
  Registered: {add_date} ({age} months ago)
  Officers: {company_officers}
  Address: {physical_address}
  Phone: {phone}
  Fleet: {power_units} trucks, {total_drivers} drivers

========================================
FMCSA-FLAGGED INDICATORS
========================================
  Prior Revocation: {Y/N}
  Prior DOT: {number or N/A}
  {Details of prior DOT investigation if applicable}

========================================
ENTITY CROSS-REFERENCE RESULTS
========================================

OFFICER CONNECTIONS
  {For each officer}
    {officer_name}: {count} other DOTs found
      DOT {number} — {name} — Status: {status} — {finding}

ADDRESS CONNECTIONS
  {physical_address}: {count} other carriers at this address
      DOT {number} — {name} — Status: {status}

PHONE CONNECTIONS
  {phone}: {count} other DOTs with this number
      DOT {number} — {name} — Status: {status}

EQUIPMENT CONNECTIONS
  VINs checked: {count}
  VINs found on other DOTs: {count}
      VIN {vin} — {year} {make} {model} — Also on DOT {number} ({name})

========================================
INDICATOR SUMMARY
========================================
  {For each indicator}
  [{severity}] {id}
    Finding: {finding}
    Evidence: {evidence}
    Action: {action}

========================================
RISK ASSESSMENT
========================================
  Fraud Risk Score: {score}/100+
  Risk Level: {LOW / MEDIUM / HIGH / CRITICAL}

  Indicators Found: {total}
    Critical: {count}
    High: {count}
    Medium: {count}
    Low: {count}

  Assessment: {assessment paragraph}

========================================
RECOMMENDED ACTIONS
========================================
  {Based on risk level}
```

### Step 6: Recommended Actions by Risk Level

| Risk Level | Recommended Actions |
|------------|---------------------|
| **LOW** | Proceed with standard vetting. No additional fraud screening needed. |
| **MEDIUM** | Conduct enhanced due diligence. Verify officer identities independently. Request additional documentation (insurance certificates direct from insurer, vehicle titles). Monitor for 90 days after onboarding. |
| **HIGH** | Do not tender freight without manual investigation. Contact previous DOT's insurance company. Verify physical address via satellite imagery or in-person visit. Check state-level business registrations. Require face-to-face meeting or video verification with officers. |
| **CRITICAL** | Refuse to broker or tender freight. Report findings to FMCSA National Consumer Complaint Database (1-888-DOT-SAFT). Report to the FMCSA Safety Hotline. Document all evidence. Alert your compliance team. If freight was already tendered, monitor shipment closely and prepare contingency. |

### Reporting to FMCSA

If fraud is suspected, provide the user with reporting instructions:

- **FMCSA National Consumer Complaint Database**: https://nccdb.fmcsa.dot.gov
- **FMCSA Safety Hotline**: 1-888-368-7238 (1-888-DOT-SAFT)
- **FMCSA Fraud Tip Line**: Report through the OIG hotline at https://www.oig.dot.gov/hotline
- **Information to include**: Both DOT numbers (old and new), officer names, evidence of connections (shared VINs, addresses, phone numbers), safety records of the previous DOT

## Examples

### Basic fraud check

**User prompt**: "Check DOT 12345 for fraud indicators"

Fetch the carrier record, check FMCSA-flagged indicators, cross-reference officers, address, and phone. Check equipment VINs if the fleet is small enough (under 50 units). Produce the full fraud analysis report.

### Chameleon carrier investigation

**User prompt**: "Is this a chameleon carrier?"

Run the full fraud detection workflow. Focus especially on prior_revoke_flag, officer cross-referencing, and equipment VIN matches. Explain what a chameleon carrier is and present the evidence for or against this carrier being one.

### New carrier fraud screening

**User prompt**: "Run fraud analysis on this new carrier"

Emphasize indicators that are specific to new carriers: fleet size vs. age anomaly, officer experience vs. DOT age, prior revocation flag. If the carrier is genuinely new (no connections found, small fleet, new officers), report LOW risk. If connections to shut-down entities are found, escalate appropriately.

### Cross-referencing a specific officer

**User prompt**: "Check if the officers at DOT 12345 appear on any other DOTs"

Extract officer names from the carrier record and search for each one. Present all connections found, with status of each connected DOT. Highlight any connections to inactive, revoked, or OOS carriers.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| Error | Cause | Resolution |
|---|---|---|
| `401 Unauthorized` | Invalid or expired API key | Verify `SEARCHCARRIERS_API_KEY` is set with Pro-tier access |
| `404 Not Found` | DOT number does not exist | Verify the DOT number; this itself could be a fraud indicator if a carrier claims a DOT that does not exist |
| `429 Too Many Requests` | Rate limit exceeded (fraud detection is API-intensive) | Implement delays between cross-reference searches; prioritize high-value checks |
| No officers listed | Carrier record has empty company_officers | Note as a finding — legitimate carriers typically list officers. Search by carrier name and address instead. |
| VIN search returns no results | VIN not found in SearchCarriers database | This is not an error — it means the VIN was not found on another DOT, which is actually a good sign |
| Prior DOT record not found | The prior_revoke_dot_number points to a DOT that has been fully purged | Note that the previous DOT record is unavailable; the prior_revoke_flag itself is still a confirmed indicator |
| Too many search results | Common name search returns hundreds of results | Narrow by state/city or use additional identifying information to filter |

Fraud detection is inherently probabilistic. Never state with certainty that a carrier IS fraudulent based on API data alone. Present indicators, evidence, and risk levels. Let the human investigator make the final determination.

## Resources

- FMCSA Chameleon Carrier Information: https://www.fmcsa.dot.gov/safety/carrier-safety/chameleon-carriers
- FMCSA New Entrant Safety Assurance Program: 49 CFR Part 385 Subpart D
- FMCSA URS (Unified Registration System): 49 CFR Part 365
- OIG DOT Fraud Hotline: https://www.oig.dot.gov/hotline
- NCCDB Consumer Complaint Database: https://nccdb.fmcsa.dot.gov
- SearchCarriers API documentation: https://searchcarriers.com/docs/api and the repository `API-DISCOVERY.md`
- Entity cross-reference methodology: `{baseDir}/docs/fraud-detection.md`
- FMCSA SAFER System: https://safer.fmcsa.dot.gov
