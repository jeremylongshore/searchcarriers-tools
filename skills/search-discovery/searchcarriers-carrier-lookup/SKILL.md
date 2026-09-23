---
name: searchcarriers-carrier-lookup
description: Searches carriers by DOT, MC, name, VIN, or SCAC from 4M+ companies and returns formatted summaries. Use when looking up a motor carrier.
allowed-tools: Read,Grep,Bash(curl:*),Bash(python:*)
metadata:
  tier: free
version: 0.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Claude Code or another MCP-capable client; Python 3.10+; network access to searchcarriers.com; an appropriate SearchCarriers API subscription.
tags:
- searchcarriers
- motor-carrier
- search-discovery
---

# Carrier Lookup

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current v3/v2/v1 route map and verified parameter names. Do not infer newer-version routes.

SearchCarriers exposes selectable v3 company sections spanning identity, contact information, fleet composition, operating authority, safety history, and cargo classifications. This skill teaches you how to detect a user's search intent, select the correct endpoint and parameters, execute the lookup, and distill the response into a concise due-diligence summary.

## Prerequisites

- **Minimum tier**: Free
- **Environment variable**: `SEARCHCARRIERS_API_KEY` must be set in the shell environment
- **Network access**: HTTPS to `searchcarriers.com`

## Instructions

### 1. Detect Search Intent

Parse the user's request and classify it into exactly one search type:

| User Signal | Search Type | Endpoint | Key Parameter |
|---|---|---|---|
| 7-digit number, "DOT" prefix | DOT lookup | `GET /search` | `dotNumber` |
| "MC" followed by digits | MC lookup | `GET /search` | `docketNumber` |
| Company name string | Name search | `GET /search` | `superSearchTerm` or `superSearchTerm` |
| 17-character alphanumeric | VIN search | `GET /search` | `vin` |
| 2-4 letter carrier code | SCAC lookup | `GET /search/scac` | `scac` |
| State/city/zip mention | Location search | `GET /api/v3/search` | MCP inputs `state`/`city` map to `addressState`/`addressCity`; `zipCode` passes through |

When a query combines multiple signals (e.g., "Find Pacific trucking in Texas"), use all applicable parameters together on a single call.

If the input is ambiguous, prefer `superSearchTerm` as it searches across multiple fields.

### 2. Build the API Call

Construct the curl command following this pattern:

```bash
curl -s "https://searchcarriers.com/api/v3/search?<params>" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

For SCAC lookups use the dedicated endpoint:

```bash
curl -s "https://searchcarriers.com/api/v1/search/scac?scac=<CODE>" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

**Parameter rules:**
- URL-encode values that contain spaces or special characters.
- Use `perPage` (default 25, max 100) and `page` for pagination.
- Filter by `status=ACTIVE` when the user only wants operating carriers.
- Filter by `carrierOperation` when the user specifies carrier type (e.g., `A` for authorized-for-hire, `B` for exempt-for-hire, `C` for private).

### 3. Format the Response

Structure every carrier result into these sections. Omit a section only when every field in it is null or empty.

**Identity**
- Legal name, DBA name(s), DOT number, MC/MX number, DUNS number
- Entity type, operating status, out-of-service date (if any)

**Contact**
- Physical address, mailing address, phone, email
- Company officers (names and titles)

**Fleet & Operations**
- Total drivers, total power units, total fleet size
- Carrier operation type, shipper/carrier/broker authority status
- HM (hazmat) flag, passenger carrier flag

**Safety**
- Safety rating, rating date
- Crash data (fatal, injury, towaway counts)
- Inspection summary (vehicle and driver OOS rates)
- Most recent snapshot date

**Insurance**
- BIPD (bodily injury / property damage) coverage and status
- Bond/surety status
- Cargo insurance on file

**Cargo Types**
- List all cargo classifications carried (general freight, household goods, metal/sheets/coils, motor vehicles, etc.)

### 4. Highlight Red Flags

After formatting, scan for and explicitly call out any of these conditions:

- **Inactive or revoked status** -- carrier is not authorized to operate
- **No insurance on file** or insurance below FMCSA minimums
- **Conditional or Unsatisfactory safety rating**
- **Out-of-service orders** (company, driver, or vehicle)
- **High OOS inspection rates** (vehicle OOS > 25% or driver OOS > 10% are industry concern thresholds)
- **Zero power units or zero drivers reported** with active authority
- **Recent crashes** with fatalities

Present red flags in a clearly separated block so they are impossible to miss.

### 5. Multi-Result Handling

When a search returns multiple carriers:

1. State the total result count.
2. Present the first 5 results as abbreviated summaries (legal name, DOT, MC, state, status, fleet size).
3. Ask the user which carrier to expand, or offer to refine the search with additional filters.

## Examples

### Example 1: DOT Number Lookup

**User**: "Look up DOT 12345"

```bash
curl -s "https://searchcarriers.com/api/v3/search?dotNumber=12345" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Format the single result into the full summary template. Flag any safety or insurance issues.

### Example 2: Name + Location Search

**User**: "Find carriers named Pacific in Texas"

```bash
curl -s "https://searchcarriers.com/api/v3/search?superSearchTerm=Pacific&addressState=TX&perPage=25" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Present abbreviated multi-result list. Offer to drill into a specific DOT.

### Example 3: MC Number Lookup

**User**: "What's MC 1672915?"

```bash
curl -s "https://searchcarriers.com/api/v3/search?docketNumber=1672915" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Format full summary. If the MC maps to multiple DOT numbers, present all of them.

### Example 4: SCAC Lookup

**User**: "Look up SCAC code HJBT"

```bash
curl -s "https://searchcarriers.com/api/v1/search/scac?scac=HJBT" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

### Example 5: Active Carriers Only

**User**: "Find active hazmat carriers in Ohio"

```bash
curl -s "https://searchcarriers.com/api/v3/search?addressState=OH&status=ACTIVE&perPage=50" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Post-filter results for carriers where the HM flag is true.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| HTTP Status | Meaning | Action |
|---|---|---|
| 401 | Invalid or missing API key | Inform the user to check `SEARCHCARRIERS_API_KEY` |
| 404 | No carrier found for the given identifier | Tell the user no matching carrier exists; suggest alternate search terms |
| 422 | Invalid parameter format | Check parameter types (DOT must be numeric, SCAC must be 2-4 alpha) |
| 429 | Rate limit exceeded | Wait and retry; inform the user of the rate limit |
| 500+ | Server error | Retry once; if persistent, report the issue |

When the API returns an empty result set with a 200 status, explicitly state that no carriers matched rather than presenting an empty table.

## Resources

- SearchCarriers API documentation: `https://searchcarriers.com/docs`
- FMCSA carrier operation codes: A = Authorized For Hire, B = Exempt For Hire, C = Private (Property), D = Private (Passengers), E = Private (Enterprise)
- FMCSA safety rating definitions: Satisfactory, Conditional, Unsatisfactory, Not Rated
- OOS rate benchmarks: National average vehicle OOS ~20%, driver OOS ~5%
- Carrier object field reference: `{baseDir}/docs/carrier-fields.md`
