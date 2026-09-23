---
name: searchcarriers-bulk-processor
description: Batch processes carrier lookups from CSV or DOT lists with rate limiting and progress reporting. Use when bulk looking up or mass vetting carriers.
allowed-tools: Read,Grep,Bash(curl:*),Bash(python:*)
metadata:
  tier: smb
version: 0.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Claude Code or another MCP-capable client; Python 3.10+; network access to searchcarriers.com; an appropriate SearchCarriers API subscription.
tags:
- searchcarriers
- motor-carrier
- operations
---

# Bulk Processor

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current v3/v2/v1 route map and verified parameter names. Do not infer newer-version routes.

Operations teams routinely need to vet, audit, or refresh data on dozens to hundreds of carriers at once -- new broker onboarding lists, quarterly compliance reviews, lane bid respondents, or load board lead qualification. Doing this one DOT at a time is not viable. This skill teaches you how to accept bulk carrier input (CSV files, inline lists, or piped data), batch those lookups through the SearchCarriers `/export` endpoint with proper rate limiting, handle per-carrier errors without failing the entire batch, and deliver structured output with summary statistics.

## Prerequisites

- **Minimum tier**: SMB
- **Environment variable**: `SEARCHCARRIERS_API_KEY` must be set in the shell environment
- **Network access**: HTTPS to `searchcarriers.com`
- **Input**: A CSV file with a DOT number column, or a comma/newline-separated list of DOT numbers provided inline

## Instructions

### 1. Parse the Input Source

Determine how the user is providing DOT numbers:

| Input Type | Detection | Action |
|---|---|---|
| CSV file path | User provides a path ending in `.csv` | Read the file header row, detect the DOT column |
| Inline list | Comma-separated or space-separated numbers | Extract all numeric values |
| Clipboard / pasted text | Multi-line DOT numbers | Split on newlines, strip whitespace |

**CSV column detection** -- scan the header row for these column names (case-insensitive):
- `dot`, `dot_number`, `DOT`, `USDOT`, `usdot`, `dot_num`, `DOT_NUMBER`, `DOT Number`, `US DOT`, `USDOT Number`

If no matching column is found, examine the first data row. If a column contains only 5-8 digit integers, it is likely the DOT column. Confirm with the user before proceeding.

```bash
# Read and detect columns from a CSV file
python3 -c "
import csv, sys
with open(sys.argv[1], 'r') as f:
    reader = csv.DictReader(f)
    headers = reader.fieldnames
    dot_cols = [h for h in headers if h.strip().upper().replace(' ','').replace('_','') in ('DOT','DOTNUMBER','USDOT','USDOTNUMBER')]
    print(f'Headers: {headers}')
    print(f'DOT column candidates: {dot_cols}')
    if dot_cols:
        dots = [row[dot_cols[0]].strip() for row in reader if row[dot_cols[0]].strip().isdigit()]
        print(f'Found {len(dots)} DOT numbers')
        print(f'First 5: {dots[:5]}')
" "$CSV_FILE_PATH"
```

### 2. Validate and Deduplicate

Before making any API calls, clean the input:

1. **Strip non-numeric characters** -- remove leading zeros, spaces, dashes.
2. **Validate format** -- DOT numbers are 1-8 digit positive integers. Reject anything else.
3. **Deduplicate** -- remove duplicate DOT numbers, preserving order.
4. **Report** -- tell the user: "Found N unique DOT numbers (M duplicates removed, K invalid entries skipped)."

```bash
python3 -c "
import sys
raw_dots = sys.argv[1:]
seen = set()
valid = []
invalid = []
dupes = 0
for d in raw_dots:
    cleaned = d.strip().lstrip('0') or '0'
    if not cleaned.isdigit() or int(cleaned) < 1 or len(cleaned) > 8:
        invalid.append(d)
        continue
    if cleaned in seen:
        dupes += 1
        continue
    seen.add(cleaned)
    valid.append(cleaned)
print(f'Valid: {len(valid)} | Duplicates removed: {dupes} | Invalid: {len(invalid)}')
if invalid:
    print(f'Invalid entries: {invalid[:10]}')
print(','.join(valid))
" $DOT_LIST
```

### 3. Batch Using the Export Endpoint

The `/export` endpoint accepts an array of DOT numbers and returns carrier data in bulk. This is far more efficient than individual lookups.

```bash
# Build the query string for a batch of DOT numbers
# dot_numbers[] parameter is repeated for each DOT
curl -s "https://searchcarriers.com/api/v1/export?dot_numbers[]=123456&dot_numbers[]=789012&dot_numbers[]=345678&file_format=json" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

**Batch sizing rules:**
- Maximum batch size: **20 DOT numbers per request** (keeps URL length safe and response times reasonable).
- Delay between batches: **1 second** (stays well within the ~3 req/s rate limit).
- For large jobs (100+ carriers), use **10 per batch** with 1-second delays to avoid sustained load.

### 4. Execute with Progress Reporting

Use a Python script to orchestrate the batched requests:

```bash
python3 -c "
import urllib.request, urllib.parse, json, time, os, sys

api_key = os.environ.get('SEARCHCARRIERS_API_KEY', '')
dots = sys.argv[1].split(',')
batch_size = 20 if len(dots) <= 100 else 10
results = []
errors = []
not_found = []

for i in range(0, len(dots), batch_size):
    batch = dots[i:i+batch_size]
    batch_num = (i // batch_size) + 1
    total_batches = (len(dots) + batch_size - 1) // batch_size
    processed = min(i + batch_size, len(dots))
    print(f'Processing batch {batch_num} of {total_batches} ({processed} carriers processed)', flush=True)

    params = '&'.join([f'dot_numbers[]={d}' for d in batch]) + '&file_format=json'
    url = f'https://searchcarriers.com/api/v1/export?{params}'
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    })

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            if isinstance(data, list):
                found_dots = set()
                for carrier in data:
                    results.append(carrier)
                    found_dots.add(str(carrier.get('dot_number', '')))
                for d in batch:
                    if d not in found_dots:
                        not_found.append(d)
            elif isinstance(data, dict) and 'data' in data:
                found_dots = set()
                for carrier in data['data']:
                    results.append(carrier)
                    found_dots.add(str(carrier.get('dot_number', '')))
                for d in batch:
                    if d not in found_dots:
                        not_found.append(d)
    except urllib.error.HTTPError as e:
        print(f'  Batch {batch_num} error: HTTP {e.code}', flush=True)
        for d in batch:
            errors.append({'dot': d, 'error': f'HTTP {e.code}'})
    except Exception as e:
        print(f'  Batch {batch_num} error: {e}', flush=True)
        for d in batch:
            errors.append({'dot': d, 'error': str(e)})

    if i + batch_size < len(dots):
        time.sleep(1)

print(f'\n--- Summary ---')
print(f'Total requested: {len(dots)}')
print(f'Found: {len(results)}')
print(f'Not found: {len(not_found)}')
print(f'Errors: {len(errors)}')
if not_found:
    print(f'Missing DOTs: {not_found[:20]}')
if errors:
    print(f'Error DOTs: {[e[\"dot\"] for e in errors[:20]]}')

# Write full results to output file
outdir = os.environ.get('SC_OUTPUT_DIR', '.')
outpath = os.path.join(outdir, 'sc-bulk-results.json')
with open(outpath, 'w') as f:
    json.dump(results, f, indent=2)
print(f'Full results written to: {outpath}')
" "$DOT_LIST_COMMA_SEPARATED"
```

### 5. Format Output

After all batches complete, present results in the user's preferred format:

**Summary table (default):**

| DOT | Legal Name | Status | State | MC | Fleet Size | Safety Rating |
|---|---|---|---|---|---|---|
| 123456 | Acme Trucking LLC | ACTIVE | TX | 987654 | 25 | Satisfactory |
| 789012 | Beta Logistics Inc | ACTIVE | OH | 654321 | 8 | Not Rated |

**Full JSON export:**
Write to `./sc-bulk-export-{timestamp}.json` with the complete carrier objects.

**CSV export:**
Flatten key fields into a CSV file at `./sc-bulk-export-{timestamp}.csv`:

```bash
python3 -c "
import json, csv, sys, time, os

outdir = os.environ.get('SC_OUTPUT_DIR', '.')
with open(os.path.join(outdir, 'sc-bulk-results.json'), 'r') as f:
    carriers = json.load(f)

fields = ['dot_number', 'legal_name', 'dba_name', 'mc_mx_ff_number', 'operating_status',
          'phy_city', 'phy_state', 'phy_zip', 'phone', 'email_address',
          'total_drivers', 'total_power_units', 'safety_rating', 'safety_rating_date',
          'carrier_operation', 'hm_flag', 'bipd_insurance_on_file', 'bipd_insurance_required']

timestamp = int(time.time())
outpath = os.path.join(outdir, f'sc-bulk-export-{timestamp}.csv')
with open(outpath, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    for c in carriers:
        writer.writerow({k: c.get(k, '') for k in fields})
print(f'CSV written to: {outpath} ({len(carriers)} rows)')
"
```

### 6. Build Summary Statistics

Always conclude a bulk operation with aggregate statistics:

- **Total processed**: N carriers
- **Found**: N carriers with valid data
- **Not found**: N DOT numbers returned no results (list them)
- **API errors**: N requests failed (list DOTs and error codes)
- **Status breakdown**: N active, N inactive, N authorized, N revoked
- **State distribution**: Top 5 states represented
- **Fleet size range**: Smallest to largest fleet in the batch
- **Safety concerns**: N carriers with Conditional/Unsatisfactory ratings, N with no insurance

### 7. Optional Post-Lookup Enrichment

After bulk data is retrieved, offer the user these follow-up actions:

- **Safety scan**: "Want me to flag carriers with safety concerns from this batch?"
- **Insurance check**: "Want me to identify carriers missing required insurance?"
- **Contact export**: "Want me to extract phone/email contacts for outreach?"
- **Watchlist**: "Want me to add these carriers to your watchlist for change monitoring?"

For any enrichment that requires per-carrier API calls (inspections, insurance detail), warn about rate limits and estimated time: "Fetching inspection data for 50 carriers will take approximately 20 seconds."

## Examples

### Example 1: Process a CSV File

**User**: "Process carriers from /tmp/carrier_list.csv"

1. Read the CSV, detect the DOT column.
2. Extract and validate DOT numbers.
3. Batch through `/export` with progress reporting.
4. Present summary table and write full results to JSON.

```bash
# Step 1: Detect DOT column
python3 -c "
import csv
with open('/tmp/carrier_list.csv', 'r') as f:
    reader = csv.DictReader(f)
    print(f'Columns: {reader.fieldnames}')
    dots = []
    for row in reader:
        for h in reader.fieldnames:
            if h.strip().upper().replace(' ','').replace('_','') in ('DOT','DOTNUMBER','USDOT'):
                dots.append(row[h].strip())
                break
    print(f'Found {len(dots)} DOT numbers')
"
```

Then proceed with the batch workflow from steps 2-6.

### Example 2: Inline DOT List

**User**: "Bulk lookup these DOTs: 12345, 67890, 111111, 222222, 333333"

```bash
curl -s "https://searchcarriers.com/api/v1/export?dot_numbers[]=12345&dot_numbers[]=67890&dot_numbers[]=111111&dot_numbers[]=222222&dot_numbers[]=333333&file_format=json" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Small lists (under 20) can be handled in a single API call. Format results as a summary table.

### Example 3: Large Batch with CSV Output

**User**: "Export data for all carriers in my CSV to a spreadsheet-friendly format"

1. Parse CSV input.
2. Batch through `/export` in groups of 20.
3. Flatten results to CSV with key operational fields.
4. Report: "Exported 147 carriers to ./sc-bulk-export-1706000000.csv"

### Example 4: Batch with Enrichment

**User**: "Process these DOTs and flag anyone with safety issues"

1. Run the standard bulk workflow.
2. Filter results where `safety_rating` is Conditional or Unsatisfactory.
3. Filter results where `operating_status` is not ACTIVE.
4. Check for carriers with zero insurance on file.
5. Present a dedicated "Flagged Carriers" table with the specific concern for each.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| HTTP Status | Meaning | Action |
|---|---|---|
| 401 | Invalid or missing API key | Stop processing; inform the user to check `SEARCHCARRIERS_API_KEY` |
| 403 | Feature requires SMB tier or higher | Inform the user that bulk export requires an SMB subscription |
| 404 | Endpoint not found | Check URL construction; ensure `dot_numbers[]` parameter is formatted correctly |
| 422 | Invalid parameter format | One or more DOT numbers are malformed; log and skip them |
| 429 | Rate limit exceeded | Back off for 5 seconds, then retry the failed batch; reduce batch size if persistent |
| 500+ | Server error | Retry the failed batch once after 3 seconds; log and skip on second failure |

**Per-carrier error handling** -- never fail the entire batch for one bad DOT:
- If a DOT returns no data within a successful batch response, add it to the "not found" list.
- If an entire batch fails, log all DOTs in that batch as errors and continue with the next batch.
- At the end, report all errors with their DOT numbers so the user can investigate individually.

**Timeout handling** -- for very large exports (500+ carriers), the API response may be slow:
- Set a 30-second timeout per batch request.
- If a batch times out, retry with a smaller batch size (halve it).

## Resources

- SearchCarriers API documentation: `https://searchcarriers.com/docs`
- Export endpoint: `GET /api/v1/export` accepts `dot_numbers[]` (array) and `file_format` (string: json)
- Rate limit: approximately 3 requests per second; cache TTL is 5 minutes
- Maximum recommended batch size: 20 DOT numbers per `/export` call
- Carrier object field reference: `{baseDir}/docs/carrier-fields.md`
- Related skill: `searchcarriers-carrier-lookup` for single-carrier deep dives
- Related skill: `searchcarriers-data-exporter` for advanced output formatting
