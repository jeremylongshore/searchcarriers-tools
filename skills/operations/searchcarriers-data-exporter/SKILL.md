---
name: searchcarriers-data-exporter
description: Exports carrier data as CSV, JSON, markdown, or comparison tables with configurable fields. Use when exporting or formatting carrier data.
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
- operations
---

# Data Exporter

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current v3/v2/v1 route map and verified parameter names. Do not infer newer-version routes.

Raw API responses contain selectable v3 company sections in nested JSON -- useful for machines, not for operations teams who need to drop data into spreadsheets, share reports with brokers, or compare carriers side-by-side for lane awards. This skill transforms SearchCarriers API data into clean, formatted output files: flat CSVs for spreadsheet workflows, filtered JSON for downstream integrations, markdown reports for documentation, and comparison tables for decision-making. It handles field selection, data cleaning, multi-carrier aggregation, and related data inclusion (inspections, insurance, authority).

## Prerequisites

- **Minimum tier**: Pro
- **Environment variable**: `SEARCHCARRIERS_API_KEY` must be set in the shell environment
- **Network access**: HTTPS to `searchcarriers.com`
- **Write access**: Permission to write output files (defaults to current directory if no path specified)

## Instructions

### 1. Determine Export Parameters

Parse the user's request to identify:

| Parameter | Detection | Default |
|---|---|---|
| Carrier(s) | DOT numbers, MC numbers, or company names | Required -- at least one |
| Format | "CSV", "JSON", "markdown", "report", "comparison" | CSV |
| Fields | Specific field names or categories (identity, contact, safety, fleet, insurance) | All key fields |
| Output path | File path mentioned by user | `./sc-export-{timestamp}.{format}` |
| Related data | "with inspections", "include insurance", "add authority" | None |

### 2. Fetch Carrier Data

**Single carrier:**

```bash
curl -s "https://searchcarriers.com/api/v3/search?dotNumber=12345" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

**Multiple carriers via export endpoint:**

```bash
curl -s "https://searchcarriers.com/api/v1/export?dot_numbers[]=12345&dot_numbers[]=67890&dot_numbers[]=11111&file_format=json" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

**With related data (per carrier):**

```bash
# Inspections
curl -s "https://searchcarriers.com/api/v1/company/12345/inspections" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"

# Insurance
curl -s "https://searchcarriers.com/api/v1/company/12345/insurances" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"

# Authority
curl -s "https://searchcarriers.com/api/v1/company/12345/authorities" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

### 3. Field Selection

The v3 company response contains selectable nested sections. Group them into selectable categories so users do not need to know field names:

**Identity fields:**
`dot_number`, `legal_name`, `dba_name`, `mc_mx_ff_number`, `entity_type`, `operating_status`, `out_of_service_date`, `duns_number`

**Contact fields:**
`phone`, `fax`, `cell_phone`, `email_address`, `phy_street`, `phy_city`, `phy_state`, `phy_zip`, `carrier_mailing_street`, `carrier_mailing_city`, `carrier_mailing_state`, `carrier_mailing_zip`

**Fleet fields:**
`total_drivers`, `total_power_units`, `carrier_operation`, `hm_flag`, `pc_flag`

**Safety fields:**
`safety_rating`, `safety_rating_date`, `crash_total`, `fatal_crash`, `injury_crash`, `towaway_crash`, `vehicle_inspections`, `vehicle_oos_inspections`, `driver_inspections`, `driver_oos_inspections`

**Insurance fields:**
`bipd_insurance_on_file`, `bipd_insurance_required`, `cargo_insurance_on_file`, `bond_insurance_on_file`

**Cargo fields:**
`general_freight`, `household_goods`, `metal_sheets_coils`, `motor_vehicles`, `drive_away_tow_away`, `logs_poles_beams`, `building_materials`, `mobile_homes`, `machinery_large_objects`, `fresh_produce`, `liquids_gases`, `intermodal_containers`, `passengers`, `oilfield_equipment`, `livestock`, `grain_feed_hay`, `coal_coke`, `meat`, `garbage_refuse`, `us_mail`, `chemicals`, `commodities_dry_bulk`, `refrigerated_food`, `beverages`, `paper_products`, `utilities`, `agricultural_farm_supplies`, `construction`, `water_well`

When the user says "all fields", include every non-null field. When they say a category name, include that group. When they specify individual field names, match against the carrier object keys.

### 4. CSV Export

Flatten the carrier data into a single-row-per-carrier CSV:

```bash
python3 -c "
import json, csv, sys, time, os

# carrier_data should be loaded from the API response
carriers = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []

# Default key fields if user does not specify
fields = [
    'dot_number', 'legal_name', 'dba_name', 'mc_mx_ff_number',
    'operating_status', 'entity_type',
    'phy_street', 'phy_city', 'phy_state', 'phy_zip',
    'phone', 'email_address',
    'total_drivers', 'total_power_units',
    'carrier_operation', 'hm_flag',
    'safety_rating', 'safety_rating_date',
    'bipd_insurance_on_file', 'bipd_insurance_required'
]

outdir = os.environ.get('SC_OUTPUT_DIR', '.')
timestamp = int(time.time())
outpath = os.path.join(outdir, f'sc-export-{timestamp}.csv')
with open(outpath, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    for c in carriers:
        writer.writerow({k: c.get(k, '') for k in fields})

print(f'CSV exported: {outpath} ({len(carriers)} carriers, {len(fields)} columns)')
"
```

**Data cleaning rules for CSV:**
- Replace `None` / `null` with empty string.
- Format phone numbers as `(XXX) XXX-XXXX` if they are 10-digit strings.
- Format dates as `YYYY-MM-DD` where possible.
- Strip leading/trailing whitespace from all string fields.
- Escape commas within field values (the csv module handles this automatically).

### 5. JSON Export

Write filtered or full carrier objects as formatted JSON:

```bash
python3 -c "
import json, time, os

# Load carrier data from API response
carriers = []  # populated from API calls

# If user specified fields, filter each carrier object
selected_fields = None  # set to a list if user specified fields

if selected_fields:
    filtered = [{k: c.get(k) for k in selected_fields} for c in carriers]
else:
    filtered = carriers

outdir = os.environ.get('SC_OUTPUT_DIR', '.')
timestamp = int(time.time())
outpath = os.path.join(outdir, f'sc-export-{timestamp}.json')
with open(outpath, 'w') as f:
    json.dump(filtered, f, indent=2, default=str)

print(f'JSON exported: {outpath} ({len(filtered)} carriers)')
"
```

### 6. Markdown Report

Generate a formatted carrier profile report in markdown:

```markdown
# Carrier Profile: Acme Trucking LLC

**Generated**: 2026-02-26 | **Source**: SearchCarriers API

## Identity
| Field | Value |
|---|---|
| DOT Number | 123456 |
| MC Number | MC-987654 |
| Legal Name | Acme Trucking LLC |
| DBA | Acme Transport |
| Entity Type | Carrier |
| Operating Status | ACTIVE |

## Contact
| Field | Value |
|---|---|
| Phone | (555) 123-4567 |
| Email | dispatch@example.invalid |
| Physical Address | 123 Main St, Dallas, TX 75201 |
| Mailing Address | PO Box 456, Dallas, TX 75201 |

## Fleet & Operations
| Metric | Value |
|---|---|
| Total Drivers | 25 |
| Total Power Units | 30 |
| Carrier Operation | Authorized For Hire |
| Hazmat | No |

## Safety
| Metric | Value |
|---|---|
| Safety Rating | Satisfactory |
| Rating Date | 2024-03-15 |
| Fatal Crashes | 0 |
| Injury Crashes | 1 |
| Vehicle OOS Rate | 18.5% |
| Driver OOS Rate | 4.2% |

## Insurance
| Type | On File | Required |
|---|---|---|
| BIPD | $1,000,000 | $750,000 |
| Cargo | $250,000 | - |
| Bond | $75,000 | - |
```

Build this programmatically:

```bash
python3 -c "
import json, sys

carrier = json.loads(sys.argv[1])

report = f'''# Carrier Profile: {carrier.get('legal_name', 'Unknown')}

**Generated**: $(date +%Y-%m-%d) | **Source**: SearchCarriers API

## Identity
| Field | Value |
|---|---|
| DOT Number | {carrier.get('dot_number', 'N/A')} |
| MC Number | {carrier.get('mc_mx_ff_number', 'N/A')} |
| Legal Name | {carrier.get('legal_name', 'N/A')} |
| DBA | {carrier.get('dba_name', 'N/A')} |
| Operating Status | {carrier.get('operating_status', 'N/A')} |

## Contact
| Field | Value |
|---|---|
| Phone | {carrier.get('phone', 'N/A')} |
| Email | {carrier.get('email_address', 'N/A')} |
| Physical Address | {carrier.get('phy_street', '')}, {carrier.get('phy_city', '')}, {carrier.get('phy_state', '')} {carrier.get('phy_zip', '')} |

## Fleet
| Metric | Value |
|---|---|
| Total Drivers | {carrier.get('total_drivers', 'N/A')} |
| Total Power Units | {carrier.get('total_power_units', 'N/A')} |
| Safety Rating | {carrier.get('safety_rating', 'Not Rated')} |
'''

print(report)
"
```

### 7. Comparison Table

For side-by-side carrier comparison, build a transposed table where rows are fields and columns are carriers:

```bash
python3 -c "
import json, sys

carriers = json.loads(sys.argv[1])
compare_fields = [
    ('DOT Number', 'dot_number'),
    ('Legal Name', 'legal_name'),
    ('Status', 'operating_status'),
    ('State', 'phy_state'),
    ('Fleet Size', 'total_power_units'),
    ('Drivers', 'total_drivers'),
    ('Safety Rating', 'safety_rating'),
    ('BIPD Insurance', 'bipd_insurance_on_file'),
    ('Carrier Operation', 'carrier_operation'),
    ('Hazmat', 'hm_flag'),
    ('MC Number', 'mc_mx_ff_number'),
]

# Build header
names = [c.get('legal_name', f'Carrier {i+1}')[:25] for i, c in enumerate(carriers)]
header = '| Field | ' + ' | '.join(names) + ' |'
sep = '|---|' + '|'.join(['---'] * len(carriers)) + '|'

rows = [header, sep]
for label, key in compare_fields:
    vals = [str(c.get(key, 'N/A')) for c in carriers]
    rows.append(f'| {label} | ' + ' | '.join(vals) + ' |')

print('\n'.join(rows))
"
```

### 8. Include Related Data

When the user requests related data alongside the export, make additional API calls per carrier:

**Inspections:**
```bash
curl -s "https://searchcarriers.com/api/v1/company/12345/inspections?page=1" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Append inspection summary to the carrier record: total inspections, OOS count, date range, most recent inspection date.

**Insurance detail:**
```bash
curl -s "https://searchcarriers.com/api/v1/company/12345/insurances" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Append active policy details: insurer name, policy number, coverage amount, effective dates.

**Authority:**
```bash
curl -s "https://searchcarriers.com/api/v1/company/12345/authorities" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Append authority records: type, status, effective date, application pending flags.

For multi-carrier exports with related data, warn about rate limits: "Fetching related data for N carriers requires up to 3N additional API calls. Estimated time: ~N seconds."

### 9. Write Output

Default output paths follow this pattern:
- CSV: `./sc-export-{timestamp}.csv`
- JSON: `./sc-export-{timestamp}.json`
- Markdown: `./sc-export-{timestamp}.md`
- Comparison: `./sc-comparison-{timestamp}.md`

If the user specifies a path, use it. Confirm the file was written by reporting the path and file size.

After writing, offer follow-up actions:
- "Want me to open this file?"
- "Want me to add more carriers to this export?"
- "Want me to include additional fields?"

## Examples

### Example 1: Single Carrier CSV Export

**User**: "Export DOT 12345 to CSV"

```bash
curl -s "https://searchcarriers.com/api/v3/search?dotNumber=12345" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Parse the response, flatten to CSV with default key fields, write to `./sc-export-{timestamp}.csv`.

### Example 2: Multi-Carrier Comparison

**User**: "Create a comparison report for DOTs 12345, 67890, and 11111"

```bash
curl -s "https://searchcarriers.com/api/v1/export?dot_numbers[]=12345&dot_numbers[]=67890&dot_numbers[]=11111&file_format=json" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Build a side-by-side comparison table. Present it inline and write the markdown to a file.

### Example 3: Fleet Data with Insurance

**User**: "Export fleet data with insurance status to JSON for DOT 12345"

```bash
# Fetch carrier data
curl -s "https://searchcarriers.com/api/v3/search?dotNumber=12345" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"

# Fetch insurance detail
curl -s "https://searchcarriers.com/api/v1/company/12345/insurances" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Merge the insurance data into the carrier object under an `insurance_detail` key. Write the combined JSON to file.

### Example 4: Custom Field Selection

**User**: "Export DOTs 12345 and 67890 with just name, DOT, phone, email, and safety rating"

```bash
curl -s "https://searchcarriers.com/api/v1/export?dot_numbers[]=12345&dot_numbers[]=67890&file_format=json" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Filter each carrier object to only: `legal_name`, `dot_number`, `phone`, `email_address`, `safety_rating`. Write as CSV or JSON per user preference.

### Example 5: Markdown Profile Report

**User**: "Generate a carrier report for DOT 12345"

Fetch full carrier data, build the markdown report template from section 6, write to `./sc-export-{timestamp}.md`, and display the report inline.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| HTTP Status | Meaning | Action |
|---|---|---|
| 401 | Invalid or missing API key | Stop; inform the user to check `SEARCHCARRIERS_API_KEY` |
| 403 | Feature requires Pro tier | Inform the user that data export features require a Pro subscription |
| 404 | Carrier not found | Report which DOT numbers were not found; continue with remaining carriers |
| 422 | Invalid parameter | Check DOT number format and field names |
| 429 | Rate limit exceeded | Wait 5 seconds, retry; reduce concurrent requests |
| 500+ | Server error | Retry once; report failure for affected carriers |

**Data quality handling:**
- Null fields: Omit from markdown reports, show as empty in CSV, include as `null` in JSON.
- Malformed dates: Pass through as-is with a note rather than failing the export.
- Extremely long field values: Truncate to 500 characters in CSV, preserve full length in JSON.
- Unicode characters in company names: Ensure UTF-8 encoding on all output files.

**File write errors:**
- Permission denied: Inform the user and suggest they specify a writable output path.
- Disk full: Report the error; suggest a different output path.

## Resources

- SearchCarriers API documentation: `https://searchcarriers.com/docs`
- Export endpoint: `GET /api/v1/export` accepts `dot_numbers[]` (array) and `file_format` (string)
- Search endpoint: `GET /api/v3/search` accepts `dotNumber`, `docketNumber`, `superSearchTerm`, and current v3 filters.
- Company data: selectable v3 sections spanning contact, operations, safety, insurance, equipment, and risk
- Rate limit: approximately 3 requests per second; cache TTL is 5 minutes
- Carrier object field reference: `{baseDir}/docs/carrier-fields.md`
- Related skill: `searchcarriers-bulk-processor` for batch input handling
- Related skill: `searchcarriers-carrier-lookup` for single-carrier deep dives
