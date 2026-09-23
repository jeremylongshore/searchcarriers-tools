---
name: searchcarriers-vin-decoder
description: Retrieves equipment details and cross-references companies operating the same VINs. Use when decoding VINs or investigating fleet equipment.
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
- search-discovery
---

# VIN Decoder

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current v3/v2/v1 route map and verified parameter names. Do not infer newer-version routes.

Every commercial motor vehicle registered with FMCSA is tracked by VIN back to the carrier operating it. SearchCarriers provides two complementary views: equipment detail for a known carrier (what trucks does DOT X own?) and VIN-based carrier search (who operates this specific truck?). Combined, these let you build a complete picture of a vehicle's operational history, spot mismatched fleet data, identify leasing relationships, and flag equipment-related compliance risks.

## Prerequisites

- **Minimum tier**: Pro
- **Environment variable**: `SEARCHCARRIERS_API_KEY` must be set in the shell environment
- **Network access**: HTTPS to `searchcarriers.com`
- **Context**: For equipment-by-DOT queries, the user must supply or you must first resolve a valid DOT number (use the carrier-lookup skill if needed)

## Instructions

### 1. Detect Query Type

Classify the user's request into one of three patterns:

| User Signal | Query Type | Primary Endpoint |
|---|---|---|
| 17-character VIN string alone | VIN carrier search | `GET /search/by-vin/` |
| DOT number + "equipment" / "fleet" / "trucks" | Equipment roster | `GET /company/{dot}/equipment` |
| DOT number + "vehicles" | Vehicle list | `GET /company/{dot}/vehicles` |
| VIN + "who operates" / "who else" | Cross-carrier VIN search | `GET /search/by-vin/` |
| DOT + specific VIN | Equipment detail + cross-reference | Both endpoints |

### 2. Retrieve Equipment Data by DOT

To list all equipment registered to a carrier:

```bash
curl -s "https://searchcarriers.com/api/v3/company/{dot}/equipment" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

The response returns an array of equipment records. Each record contains:

- `vin` -- 17-character vehicle identification number
- `make` -- manufacturer (e.g., FREIGHTLINER, PETERBILT, VOLVO)
- `model` -- model designation
- `year` -- model year
- `type` -- equipment classification (e.g., Truck Tractor, Straight Truck, Trailer)
- `sub_type` -- specific sub-classification
- `gvwr` -- gross vehicle weight rating in pounds

### 3. Retrieve Vehicle Data by DOT

For a streamlined vehicle view with registration details:

```bash
curl -s "https://searchcarriers.com/api/v1/company/{dot}/vehicles" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Vehicle records include:

- `type` -- vehicle type
- `vin` -- vehicle identification number
- `license_plate_state` -- state of registration
- `make` -- manufacturer

### 4. Search Carriers by VIN

To find every carrier associated with a specific VIN:

```bash
curl -s "https://searchcarriers.com/api/v1/search/by-vin/{vin}" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

This returns carrier records (not equipment records). Each result is a full 143-field carrier object for a company that has reported operating this VIN.

### 5. Format Equipment Results

Present equipment rosters as a table:

| VIN | Year | Make | Model | Type | GVWR |
|---|---|---|---|---|---|
| 1FUJGLDR8BSAX9472 | 2011 | FREIGHTLINER | CASCADIA | Truck Tractor | 52,000 |
| 3AKJGLDR7DSBY1038 | 2013 | FREIGHTLINER | CASCADIA | Truck Tractor | 52,000 |

Follow the table with a fleet summary:

- **Total units**: count
- **Average age**: calculated from current year minus model year
- **Make distribution**: count per manufacturer
- **Type breakdown**: truck tractors vs. straight trucks vs. trailers

### 6. Interpret Equipment Data

Apply these freight-industry interpretations:

**Fleet age analysis**
- Vehicles older than 10 years may indicate deferred capital expenditure or a small owner-operator fleet.
- A mix of very new and very old equipment may indicate recent partial fleet replacement.

**GVWR implications**
- GVWR above 26,001 lbs requires a CDL driver. Flag if carrier reports CDL-exempt operations.
- GVWR below 10,001 lbs typically indicates light-duty / last-mile equipment.

**Type consistency**
- A carrier authorized only for property transport should not have buses.
- Trailer-only fleets with no power units may indicate an intermodal or brokerage operation.

### 7. Cross-Reference Companies Sharing a VIN

When multiple carriers appear for the same VIN, present them as a relationship table:

| DOT | Legal Name | Status | State | Relationship Indicator |
|---|---|---|---|---|
| 12345 | Pacific Transport LLC | ACTIVE | TX | Current operator |
| 67890 | Pacific Leasing Inc | ACTIVE | TX | Possible lessor (shared address) |
| 11111 | Old Pacific Inc | INACTIVE | TX | Previous operator |

Determine relationship indicators by comparing:
- Physical address overlap (same street = likely related entities)
- Shared company officers
- One active / one inactive (suggests rebranding or succession)
- DBA name matches

### 8. Flag Equipment Risks

Scan results and explicitly call out:

- **VIN format errors**: VINs that are not exactly 17 characters or contain invalid characters (I, O, Q)
- **Ghost fleet**: Carrier reports N power units to FMCSA but equipment endpoint returns significantly fewer (or zero)
- **Age outliers**: Vehicles with model year 15+ years ago in an otherwise modern fleet
- **GVWR/authority mismatch**: Equipment weight class inconsistent with carrier operation type
- **Multi-carrier VIN without leasing context**: Same VIN on two active carriers with no apparent business relationship may indicate data errors or unauthorized operation

## Examples

### Example 1: Decode a VIN

**User**: "Decode VIN 1HGBH41JXMN109186"

```bash
curl -s "https://searchcarriers.com/api/v1/search/by-vin/1HGBH41JXMN109186" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Present each carrier operating this VIN with an abbreviated carrier summary (legal name, DOT, status, state, fleet size). If only one carrier is found, provide full detail. If multiple, present the cross-reference table and note potential relationships.

### Example 2: Equipment Roster for a DOT

**User**: "What equipment does DOT 12345 have?"

```bash
curl -s "https://searchcarriers.com/api/v3/company/12345/equipment" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Render the equipment table, fleet summary, and age analysis. Flag any risk indicators.

### Example 3: Who Else Operates This VIN

**User**: "Who else operates VIN 3AKJGLDR7DSBY1038?"

```bash
curl -s "https://searchcarriers.com/api/v1/search/by-vin/3AKJGLDR7DSBY1038" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Build the cross-carrier relationship table. Compare addresses, officers, and operational status to classify relationships (lessor, predecessor, sibling entity, or unrelated).

### Example 4: Combined Equipment + Vehicle View

**User**: "Show me everything about DOT 12345's fleet"

Run both calls:

```bash
curl -s "https://searchcarriers.com/api/v3/company/12345/equipment" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

```bash
curl -s "https://searchcarriers.com/api/v1/company/12345/vehicles" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Merge the data: equipment provides make/model/year/GVWR; vehicles provides license plate state. Present a unified table and fleet analysis.

### Example 5: Lease Relationship Investigation

**User**: "Is VIN 1FUJGLDR8BSAX9472 leased?"

```bash
curl -s "https://searchcarriers.com/api/v1/search/by-vin/1FUJGLDR8BSAX9472" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

If multiple carriers share the VIN, compare their entity types and addresses. A pattern of one company being a leasing/rental entity (often identifiable by name or large fleet size with no operating authority) and another being an operating carrier strongly suggests a lease arrangement.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| HTTP Status | Meaning | Action |
|---|---|---|
| 401 | Invalid or missing API key | Inform the user to check `SEARCHCARRIERS_API_KEY` |
| 403 | Feature requires Pro tier | Inform the user that VIN decode and equipment endpoints require a Pro subscription |
| 404 | DOT number not found or no equipment on file | Confirm the DOT is valid; carrier may have zero registered equipment |
| 422 | Invalid VIN format or DOT format | VIN must be exactly 17 alphanumeric characters; DOT must be numeric |
| 429 | Rate limit exceeded | Wait and retry; inform the user of the rate limit |
| 500+ | Server error | Retry once; if persistent, report the issue |

When the equipment endpoint returns an empty array for a valid DOT, this means the carrier has no equipment registered with FMCSA. This is notable -- report it as a finding rather than treating it as an error.

## Resources

- VIN structure reference: Positions 1-3 = World Manufacturer Identifier, 4-8 = Vehicle Descriptor, 9 = Check digit, 10 = Model year, 11 = Assembly plant, 12-17 = Sequential number
- Common CMV manufacturers: FREIGHTLINER, PETERBILT, KENWORTH, VOLVO, INTERNATIONAL, MACK, WESTERN STAR
- GVWR classes: Class 1 (0-6,000 lbs) through Class 8 (33,001+ lbs); Class 7-8 are heavy-duty CMVs
- CDL threshold: 26,001 lbs GVWR or 10,001+ lbs for placarded hazmat
- SearchCarriers API documentation: `https://searchcarriers.com/docs`
- Carrier object field reference: `{baseDir}/docs/carrier-fields.md`
