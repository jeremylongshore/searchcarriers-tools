---
name: searchcarriers-tms-connector
description: Formats carrier data for TMS imports mapping fields to TMW, McLeod, and MercuryGate formats. Use when preparing carrier data for TMS onboarding.
allowed-tools: Read,Grep,Bash(curl:*),Bash(python:*)
metadata:
  tier: enterprise
version: 0.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Claude Code or another MCP-capable client; Python 3.10+; network access to searchcarriers.com; an appropriate SearchCarriers API subscription.
tags:
- searchcarriers
- motor-carrier
- operations
---

# TMS Connector

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current v3/v2/v1 route map and verified parameter names. Do not infer newer-version routes.

Transportation Management Systems are the operational backbone of freight brokerages, 3PLs, and shippers. Every TMS maintains a carrier master file, and keeping that file current is a constant manual burden -- new carrier onboarding, quarterly re-verification, insurance updates, and authority status changes. This skill bridges SearchCarriers API data and TMS carrier record formats. It fetches carrier data, maps fields to the conventions of major TMS platforms, generates import-ready files, and provides guidance on the onboarding workflow. This is a helper skill -- it prepares data for import. Actual TMS API integration requires TMS-specific credentials which are outside scope.

## Prerequisites

- **Minimum tier**: Enterprise
- **Environment variable**: `SEARCHCARRIERS_API_KEY` must be set in the shell environment
- **Network access**: HTTPS to `searchcarriers.com`
- **Context**: User should identify their TMS platform so the correct field mapping is used

## Instructions

### 1. Identify the Target TMS Platform

Ask or detect which TMS platform the user needs data formatted for:

| TMS Platform | Common Identifiers | Import Format |
|---|---|---|
| TMW Suite (Trimble) | "TMW", "TruckMate", "Trimble TMS" | CSV with fixed column order |
| McLeod Software | "McLeod", "LoadMaster", "PowerBroker" | CSV or XML |
| MercuryGate | "MercuryGate", "Mercury", "MGTI" | CSV or EDI-style flat file |
| Revenova | "Revenova", "Salesforce TMS" | CSV (Salesforce import format) |
| Aljex | "Aljex" | CSV with specific column headers |
| Rose Rocket | "Rose Rocket", "RoseRocket" | CSV or JSON via API |
| Tai TMS | "Tai", "Tai Software" | CSV with fixed layout |
| Turvo | "Turvo" | JSON or CSV |
| Generic / Unknown | "our TMS", "TMS import", unspecified | Standard CSV with common fields |

If the user does not specify a platform, use the Generic format and note which fields may need manual mapping.

### 2. Fetch Carrier Data

Retrieve the full carrier record:

```bash
curl -s "https://searchcarriers.com/api/v3/search?dotNumber=12345" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

For onboarding workflows that include vetting, also fetch:

```bash
# Insurance status
curl -s "https://searchcarriers.com/api/v1/company/12345/insurances" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"

# Authority status
curl -s "https://searchcarriers.com/api/v1/company/12345/authorities" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

### 3. Field Mapping by TMS Platform

#### TMW Suite (Trimble)

TMW carrier records use these primary fields:

| TMW Field | SearchCarriers Field | Notes |
|---|---|---|
| `CarrierID` | `dot_number` | TMW uses DOT as primary key |
| `CarrierName` | `legal_name` | Max 60 chars in TMW |
| `DBAName` | `dba_name` | Optional |
| `MCNumber` | `mc_mx_ff_number` | Strip "MC-" prefix |
| `DOTNumber` | `dot_number` | |
| `Address1` | `phy_street` | Physical address |
| `Address2` | _(empty)_ | TMW supports line 2 |
| `City` | `phy_city` | |
| `State` | `phy_state` | 2-letter code |
| `Zip` | `phy_zip` | 5 or 9 digit |
| `Phone` | `phone` | Format: (XXX) XXX-XXXX |
| `Fax` | `fax` | |
| `Email` | `email_address` | |
| `SafetyRating` | `safety_rating` | S/C/U/N |
| `InsuranceOnFile` | `bipd_insurance_on_file` | Currency amount |
| `InsuranceRequired` | `bipd_insurance_required` | Currency amount |
| `AuthStatus` | `operating_status` | ACTIVE/INACTIVE |
| `FleetSize` | `total_power_units` | Integer |
| `HazmatCertified` | `hm_flag` | Y/N |

```bash
python3 -c "
import json, csv, sys, time, os

carrier = json.loads(sys.argv[1])

tmw_row = {
    'CarrierID': carrier.get('dot_number', ''),
    'CarrierName': str(carrier.get('legal_name', ''))[:60],
    'DBAName': carrier.get('dba_name', ''),
    'MCNumber': str(carrier.get('mc_mx_ff_number', '')).replace('MC-', '').replace('MC', ''),
    'DOTNumber': carrier.get('dot_number', ''),
    'Address1': carrier.get('phy_street', ''),
    'Address2': '',
    'City': carrier.get('phy_city', ''),
    'State': carrier.get('phy_state', ''),
    'Zip': carrier.get('phy_zip', ''),
    'Phone': carrier.get('phone', ''),
    'Fax': carrier.get('fax', ''),
    'Email': carrier.get('email_address', ''),
    'SafetyRating': str(carrier.get('safety_rating', 'N'))[:1].upper() if carrier.get('safety_rating') else 'N',
    'InsuranceOnFile': carrier.get('bipd_insurance_on_file', ''),
    'InsuranceRequired': carrier.get('bipd_insurance_required', ''),
    'AuthStatus': carrier.get('operating_status', ''),
    'FleetSize': carrier.get('total_power_units', ''),
    'HazmatCertified': 'Y' if carrier.get('hm_flag') in [True, 'Y', 'YES', 'true'] else 'N',
}

outdir = os.environ.get('SC_OUTPUT_DIR', '.')
timestamp = int(time.time())
outpath = os.path.join(outdir, f'sc-tmw-import-{timestamp}.csv')
fields = list(tmw_row.keys())
with open(outpath, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerow(tmw_row)
print(f'TMW import file: {outpath}')
"
```

#### McLeod Software (LoadMaster / PowerBroker)

| McLeod Field | SearchCarriers Field | Notes |
|---|---|---|
| `carrier_id` | `dot_number` | Primary identifier |
| `name` | `legal_name` | |
| `dba` | `dba_name` | |
| `mc_num` | `mc_mx_ff_number` | Numeric only |
| `dot_num` | `dot_number` | |
| `addr_line1` | `phy_street` | |
| `addr_city` | `phy_city` | |
| `addr_state` | `phy_state` | |
| `addr_zip` | `phy_zip` | |
| `phone_num` | `phone` | Digits only, 10 chars |
| `fax_num` | `fax` | Digits only |
| `email` | `email_address` | |
| `contact_name` | _(from officers)_ | First officer listed |
| `safety_rating` | `safety_rating` | Full text |
| `ins_bipd_amt` | `bipd_insurance_on_file` | |
| `ins_cargo_amt` | `cargo_insurance_on_file` | |
| `authority_status` | `operating_status` | |
| `num_trucks` | `total_power_units` | |
| `num_drivers` | `total_drivers` | |
| `carrier_type` | `carrier_operation` | McLeod codes: A/B/C |

```bash
python3 -c "
import json, csv, sys, time, re, os

carrier = json.loads(sys.argv[1])

def digits_only(val):
    return re.sub(r'\D', '', str(val or ''))

mcleod_row = {
    'carrier_id': carrier.get('dot_number', ''),
    'name': carrier.get('legal_name', ''),
    'dba': carrier.get('dba_name', ''),
    'mc_num': digits_only(carrier.get('mc_mx_ff_number', '')),
    'dot_num': carrier.get('dot_number', ''),
    'addr_line1': carrier.get('phy_street', ''),
    'addr_city': carrier.get('phy_city', ''),
    'addr_state': carrier.get('phy_state', ''),
    'addr_zip': carrier.get('phy_zip', ''),
    'phone_num': digits_only(carrier.get('phone', ''))[:10],
    'fax_num': digits_only(carrier.get('fax', ''))[:10],
    'email': carrier.get('email_address', ''),
    'contact_name': '',
    'safety_rating': carrier.get('safety_rating', ''),
    'ins_bipd_amt': carrier.get('bipd_insurance_on_file', ''),
    'ins_cargo_amt': carrier.get('cargo_insurance_on_file', ''),
    'authority_status': carrier.get('operating_status', ''),
    'num_trucks': carrier.get('total_power_units', ''),
    'num_drivers': carrier.get('total_drivers', ''),
    'carrier_type': carrier.get('carrier_operation', ''),
}

outdir = os.environ.get('SC_OUTPUT_DIR', '.')
timestamp = int(time.time())
outpath = os.path.join(outdir, f'sc-mcleod-import-{timestamp}.csv')
fields = list(mcleod_row.keys())
with open(outpath, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerow(mcleod_row)
print(f'McLeod import file: {outpath}')
"
```

#### MercuryGate

| MercuryGate Field | SearchCarriers Field | Notes |
|---|---|---|
| `SCAC` | _(lookup separately)_ | Not always available in SearchCarriers |
| `CarrierName` | `legal_name` | |
| `DOT` | `dot_number` | |
| `MC` | `mc_mx_ff_number` | |
| `Street` | `phy_street` | |
| `City` | `phy_city` | |
| `StateProvince` | `phy_state` | |
| `PostalCode` | `phy_zip` | |
| `Country` | `"US"` | Default for FMCSA carriers |
| `ContactPhone` | `phone` | |
| `ContactEmail` | `email_address` | |
| `InsuranceAmount` | `bipd_insurance_on_file` | |
| `SafetyScore` | `safety_rating` | |
| `EquipmentCount` | `total_power_units` | |
| `ActiveAuth` | `operating_status` | Boolean: ACTIVE = true |

#### Revenova (Salesforce-based)

| Salesforce Field | SearchCarriers Field | Notes |
|---|---|---|
| `Account Name` | `legal_name` | Salesforce Account record |
| `DBA Name` | `dba_name` | Custom field |
| `DOT Number` | `dot_number` | Custom field |
| `MC Number` | `mc_mx_ff_number` | Custom field |
| `Billing Street` | `phy_street` | |
| `Billing City` | `phy_city` | |
| `Billing State` | `phy_state` | |
| `Billing Zip` | `phy_zip` | |
| `Phone` | `phone` | |
| `Email` | `email_address` | |
| `Safety Rating` | `safety_rating` | Picklist value |
| `Insurance Status` | `bipd_insurance_on_file` | Custom field |
| `Fleet Size` | `total_power_units` | Custom field |
| `Carrier Status` | `operating_status` | Picklist: Active/Inactive |

#### Generic TMS Format

When the platform is unknown, produce a CSV with the most universally needed fields:

```bash
python3 -c "
import json, csv, sys, time, os

carriers = json.loads(sys.argv[1])  # list of carrier objects

fields = [
    'dot_number', 'mc_number', 'legal_name', 'dba_name',
    'operating_status', 'entity_type',
    'street', 'city', 'state', 'zip',
    'phone', 'fax', 'email',
    'total_drivers', 'total_power_units',
    'safety_rating', 'safety_rating_date',
    'carrier_operation', 'hm_flag',
    'bipd_insurance_on_file', 'bipd_insurance_required',
    'cargo_insurance_on_file', 'bond_insurance_on_file'
]

outdir = os.environ.get('SC_OUTPUT_DIR', '.')
timestamp = int(time.time())
outpath = os.path.join(outdir, f'sc-tms-import-{timestamp}.csv')

with open(outpath, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for c in carriers:
        row = {
            'dot_number': c.get('dot_number', ''),
            'mc_number': c.get('mc_mx_ff_number', ''),
            'legal_name': c.get('legal_name', ''),
            'dba_name': c.get('dba_name', ''),
            'operating_status': c.get('operating_status', ''),
            'entity_type': c.get('entity_type', ''),
            'street': c.get('phy_street', ''),
            'city': c.get('phy_city', ''),
            'state': c.get('phy_state', ''),
            'zip': c.get('phy_zip', ''),
            'phone': c.get('phone', ''),
            'fax': c.get('fax', ''),
            'email': c.get('email_address', ''),
            'total_drivers': c.get('total_drivers', ''),
            'total_power_units': c.get('total_power_units', ''),
            'safety_rating': c.get('safety_rating', ''),
            'safety_rating_date': c.get('safety_rating_date', ''),
            'carrier_operation': c.get('carrier_operation', ''),
            'hm_flag': 'Y' if c.get('hm_flag') in [True, 'Y', 'YES', 'true'] else 'N',
            'bipd_insurance_on_file': c.get('bipd_insurance_on_file', ''),
            'bipd_insurance_required': c.get('bipd_insurance_required', ''),
            'cargo_insurance_on_file': c.get('cargo_insurance_on_file', ''),
            'bond_insurance_on_file': c.get('bond_insurance_on_file', ''),
        }
        writer.writerow(row)

print(f'Generic TMS import file: {outpath} ({len(carriers)} carriers)')
"
```

### 4. Carrier Onboarding Workflow

The standard carrier onboarding process for TMS integration follows this sequence:

**Step 1: Carrier Lookup**

```bash
curl -s "https://searchcarriers.com/api/v3/search?dotNumber=12345" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

**Step 2: Vetting Checks**

Before formatting for TMS import, verify the carrier meets minimum onboarding criteria:

- Operating status must be ACTIVE.
- Authority (common, contract, or broker) must not be revoked.
- BIPD insurance must be on file and meet minimum requirements ($750K for general freight, $1M for HHG, $5M for hazmat).
- Safety rating must not be Unsatisfactory.
- No active out-of-service orders.

```bash
# Check authority status
curl -s "https://searchcarriers.com/api/v1/company/12345/authorities" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"

# Check insurance detail
curl -s "https://searchcarriers.com/api/v1/company/12345/insurances" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

**Step 3: Format for TMS**

After passing vetting, map the carrier data to the target TMS format (see section 3).

**Step 4: Generate Import File**

Write the formatted data to a file the user can import into their TMS.

**Step 5: Report**

Present a summary:
```
Carrier Onboarding Summary:
  Carrier: Acme Trucking LLC (DOT 123456)
  Status: APPROVED for onboarding
  Vetting: All checks passed
  TMS Format: McLeod (LoadMaster)
  Import File: ./sc-mcleod-import-1706000000.csv

  Note: Import this file via McLeod's Carrier Maintenance > Import function.
```

### 5. Batch Onboarding

For multiple carriers, combine the onboarding workflow with batch processing:

```bash
# Fetch all carriers in one call
curl -s "https://searchcarriers.com/api/v1/export?dot_numbers[]=12345&dot_numbers[]=67890&dot_numbers[]=11111&file_format=json" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Then for each carrier:
1. Run vetting checks.
2. Classify as APPROVED, CONDITIONAL (passed with warnings), or REJECTED (failed vetting).
3. Format approved carriers for TMS import.
4. Generate a single combined import file.
5. Generate a separate rejection report with reasons.

Present the batch summary:
```
Batch Onboarding Results:
  Total carriers: 15
  Approved: 12
  Conditional: 2 (insurance expiring within 30 days)
  Rejected: 1 (DOT 99999 - authority revoked)

  Import file: ./sc-tmw-import-1706000000.csv (12 carriers)
  Review file: ./sc-onboard-review-1706000000.csv (2 carriers needing attention)
  Rejection report: ./sc-onboard-rejected-1706000000.csv (1 carrier)
```

### 6. Change Detection and Update Workflow

Use the watch endpoint to monitor carriers already in your TMS:

```bash
# Check if a carrier is on your watchlist
curl -s "https://searchcarriers.com/api/v1/company/12345/watch" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"

# Add a carrier to your watchlist
curl -s -X POST "https://searchcarriers.com/api/v1/company/12345/watch" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

**Update workflow:**
1. Fetch current data from SearchCarriers for watched carriers.
2. Compare against the last known TMS record (user provides or describes the current TMS data).
3. Flag fields that have changed: address updates, insurance changes, safety rating changes, authority status changes.
4. Generate an update import file with only the changed records.
5. Recommend adding newly onboarded carriers to the watchlist.

### 7. Data Freshness Assessment

When generating TMS import files, include a freshness assessment:

- **MCS-150 date**: How recently did the carrier update their FMCSA filing?
- **Insurance effective dates**: Are policies current or expiring soon?
- **Safety rating date**: When was the last safety audit?
- **Data retrieval date**: Timestamp the export so the user knows when this snapshot was taken.

Flag carriers whose TMS records are likely stale:
```
Data Freshness Warnings:
  DOT 12345: MCS-150 filed 28 months ago — contact info may be outdated
  DOT 67890: Insurance policy expires in 14 days — verify before onboarding
  DOT 11111: Safety rating from 2019 — consider requesting updated review
```

## Examples

Read `{baseDir}/references/examples.md` for the detailed single-carrier, batch, and exception scenarios. The examples use synthetic identifiers.

## Output

Return the requested TMS-ready CSV or JSON payload, an explicit field-mapping
summary, vetting disposition, freshness warnings, and any rows that require
manual completion. Never persist raw SearchCarriers API responses.

## Error Handling

| HTTP Status | Meaning | Action |
|---|---|---|
| 401 | Invalid or missing API key | Stop; inform the user to check `SEARCHCARRIERS_API_KEY` |
| 403 | Feature requires Enterprise tier | Inform the user that TMS connector features require an Enterprise subscription |
| 404 | Carrier not found | Report the DOT as not found; cannot onboard a nonexistent carrier |
| 422 | Invalid parameter | Check DOT number format |
| 429 | Rate limit exceeded | Wait 5 seconds and retry; relevant for batch onboarding |
| 500+ | Server error | Retry once; report failure |

**TMS-specific error handling:**
- If a required TMS field is missing from the SearchCarriers data (e.g., no email for a TMS that requires it), flag it in the import file as needing manual completion rather than leaving it blank silently.
- If field value exceeds TMS character limits (e.g., TMW's 60-char carrier name limit), truncate and note the truncation.
- If the carrier fails vetting but the user explicitly requests the import file anyway, generate it with a prominent warning header.

**Onboarding rejection reasons to track:**
- Authority revoked or not granted
- Insurance below minimum or expired
- Unsatisfactory safety rating
- Active out-of-service order
- Operating status not ACTIVE

## Resources

- SearchCarriers API documentation: `https://searchcarriers.com/docs`
- TMW Suite documentation: `https://www.trimble.com/transportation` (carrier setup module)
- McLeod Software: `https://www.mcleodsoftware.com` (LoadMaster carrier maintenance)
- MercuryGate: `https://www.mercurygate.com` (carrier management module)
- Revenova: `https://www.revenova.com` (Salesforce carrier records)
- FMCSA minimum insurance requirements: $750K BIPD for general freight, $1M for household goods, $5M for hazmat
- Carrier operation codes: A = Auth For Hire, B = Exempt For Hire, C = Private Property, D = Private Passengers
- Carrier object field reference: `{baseDir}/docs/carrier-fields.md`
- Related skill: `searchcarriers-carrier-lookup` for individual carrier lookups
- Related skill: `searchcarriers-bulk-processor` for batch carrier data retrieval
- Related skill: `searchcarriers-contact-verifier` for pre-onboarding contact validation
