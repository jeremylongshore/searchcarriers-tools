---
name: searchcarriers-entity-mapper
description: Maps carrier relationships via shared officers, addresses, and equipment. Use when finding related companies or detecting chameleon carriers.
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

# Entity Mapper

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current v3/v2/v1 route map and verified parameter names. Do not infer newer-version routes.

Motor carriers frequently operate through webs of related entities -- parent companies, subsidiaries, DBAs, predecessor companies, and shared-officer networks. FMCSA data captures fragments of these relationships through 143 carrier fields including company officers, physical addresses, phone numbers, DUNS numbers, DBA names, and equipment registrations. This skill teaches you how to systematically extract these signals, execute targeted searches to find connected entities, and assemble the results into a relationship map that reveals corporate structures, operational dependencies, and potential evasion patterns.

## Prerequisites

- **Minimum tier**: Pro
- **Environment variable**: `SEARCHCARRIERS_API_KEY` must be set in the shell environment
- **Network access**: HTTPS to `searchcarriers.com`
- **Recommended**: Start with a known DOT number or legal name as the seed entity. Use the carrier-lookup skill to resolve one if the user provides only a name or partial identifier.

## Instructions

### 1. Establish the Seed Entity

Every relationship map starts from a seed carrier. Retrieve the full carrier record:

```bash
curl -s "https://searchcarriers.com/api/v3/search?dotNumber={dot}" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

From the seed carrier, extract these relationship anchors:

| Field | Relationship Signal | Search Strategy |
|---|---|---|
| `legal_name` | Name variants | Search `superSearchTerm` with base name |
| `dba_name` | Alternate operating names | Search `superSearchTerm` with DBA |
| `company_officers` | Shared principals | Search each officer name via `superSearchTerm` |
| `phy_street`, `phy_city`, `phy_state`, `phy_zip` | Co-located entities | Search by `city` + `state` or `zipCode`, filter by address |
| `phone` | Shared phone number | Search `superSearchTerm` with phone digits |
| `dun_bradstreet_no` | Corporate linkage | Exact DUNS match (post-filter) |
| `mailing_street` | Shared mailing address | Post-filter on search results |
| Equipment VINs | Shared equipment | Search `vin` for each VIN (see vin-decoder skill) |

### 2. Execute Relationship Searches

Work through the anchors systematically. Each search type has different signal strength.

**Officer Search (highest signal)**

Company officers are the strongest relationship indicator. For each officer name from the seed:

```bash
curl -s "https://searchcarriers.com/api/v3/search?superSearchTerm={officer_name}&perPage=100" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Filter results to carriers where `company_officers` contains a matching name. An exact name match across two DOT numbers is a near-certain relationship.

**Name Variant Search (high signal)**

Search the base company name without suffixes (LLC, Inc, Corp, Transport, Trucking, Logistics):

```bash
curl -s "https://searchcarriers.com/api/v3/search?superSearchTerm={base_name}&perPage=100" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Also search the DBA name if one exists:

```bash
curl -s "https://searchcarriers.com/api/v3/search?superSearchTerm={dba_name}&perPage=100" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

**Address Search (medium signal)**

Search by location and then post-filter for address matches:

```bash
curl -s "https://searchcarriers.com/api/v3/search?addressCity={city}&addressState={state}&perPage=100" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Post-filter: compare `phy_street` values from results against the seed carrier's physical address. Exact street match at the same city/state is a strong signal. Same zip code alone is weak.

**Phone Search (medium signal)**

```bash
curl -s "https://searchcarriers.com/api/v3/search?superSearchTerm={phone_digits}&perPage=50" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Post-filter results for matching phone numbers. Shared phone numbers between carriers almost always indicate a direct relationship.

**Equipment Cross-Reference (medium signal)**

If the seed carrier has equipment data (Pro tier), retrieve VINs and search each:

```bash
curl -s "https://searchcarriers.com/api/v3/company/{dot}/equipment" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Then for notable VINs:

```bash
curl -s "https://searchcarriers.com/api/v1/search/by-vin/{vin}" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Shared VINs indicate equipment leasing, corporate fleet sharing, or carrier succession.

### 3. Score and Classify Relationships

For each discovered entity, tally the relationship evidence:

| Evidence Type | Signal Strength | Points |
|---|---|---|
| Shared company officer (exact name) | Very High | 5 |
| Same physical street address | High | 4 |
| Same phone number | High | 4 |
| Same DUNS number | High | 4 |
| DBA name matches other entity's legal name | High | 4 |
| Shared VINs in equipment | Medium | 3 |
| Same mailing address (different physical) | Medium | 3 |
| Similar legal name (base name match) | Medium | 2 |
| Same city and zip code only | Low | 1 |

Classify the relationship based on accumulated points:

- **8+ points**: Almost certainly the same corporate family. Label as "affiliated entity."
- **5-7 points**: Highly likely related. Label as "probable affiliate."
- **3-4 points**: Possible relationship worth investigating. Label as "possible connection."
- **1-2 points**: Coincidental unless other context supports it. Label as "weak signal."

### 4. Identify Relationship Types

Assign a relationship type to each confirmed connection:

| Pattern | Relationship Type | Indicators |
|---|---|---|
| Same officers, different DOT, both active | **Sibling companies** | Separate authorities for different operations |
| Same officers, one active, one inactive | **Successor / predecessor** | Carrier re-registered under new DOT |
| DBA of entity A = legal name of entity B | **DBA relationship** | Operating under trade name |
| Same address, different officers | **Co-located / shared facility** | May be landlord-tenant or affiliated |
| Same DUNS number | **Corporate parent linkage** | D&B identifies them as same business entity |
| Shared VINs, one entity is leasing company | **Lease arrangement** | Equipment lessor and lessee |
| Same officers, recently created DOT, old DOT has safety issues | **Chameleon carrier** | Evasion of safety enforcement |

### 5. Build the Relationship Map

Present the final map as a structured table:

| DOT | Legal Name | Status | Relationship to Seed | Evidence | Confidence |
|---|---|---|---|---|---|
| 12345 | Pacific Transport LLC | ACTIVE | **Seed entity** | -- | -- |
| 67890 | Pacific Logistics Inc | ACTIVE | Sibling company | Shared officer: John Smith; Same address | High |
| 11111 | Pacific Express LLC | INACTIVE | Predecessor | Same officer: John Smith; Similar name | High |
| 22222 | Smith Family Trucking | ACTIVE | Officer-linked | Shared officer: John Smith | Medium |
| 33333 | ABC Leasing Corp | ACTIVE | Equipment lessor | 3 shared VINs | Medium |

Follow the table with a narrative summary that explains the corporate structure in plain language.

### 6. Detect Chameleon Carrier Patterns

Chameleon carriers are entities that shut down and re-register under a new DOT to escape safety enforcement history. FMCSA considers this a serious compliance violation. Flag any entity network that exhibits these indicators:

**Strong chameleon signals (flag immediately):**
- Same principal officer on an INACTIVE carrier with Unsatisfactory safety rating AND an ACTIVE carrier with a newer DOT creation date
- New DOT registered within 12 months of old DOT going inactive
- Same physical address on both old and new DOT
- Similar or identical legal name with minor variation (e.g., "Pacific Transport" becoming "Pacific Transport Services")

**Supporting chameleon signals:**
- Same phone number across old and new entity
- Equipment VINs transferred from old to new entity
- Same mailing address with different physical address (mail forwarding)
- Old entity had pending enforcement action or imminent hazard OOS order

When chameleon indicators are detected, present them in a clearly labeled warning block and note that this pattern may warrant reporting to FMCSA.

### 7. Iterative Expansion

For thorough investigations, discovered entities may themselves yield new relationship anchors. Apply a breadth-first approach:

1. Map all direct connections from the seed (depth 1).
2. For each high-confidence connection, extract their officers and addresses.
3. Search for depth-2 connections using those new anchors.
4. Stop at depth 2 unless the user requests deeper investigation.

Limit API calls to a reasonable number. For each depth level, prioritize officer-based searches over address-based searches.

## Examples

### Example 1: Map All Related Companies

**User**: "Map all companies related to DOT 12345"

Step 1 -- Get seed carrier:

```bash
curl -s "https://searchcarriers.com/api/v3/search?dotNumber=12345" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Step 2 -- Extract anchors from seed (officers, address, phone, DBA, DUNS).

Step 3 -- Search each officer name:

```bash
curl -s "https://searchcarriers.com/api/v3/search?superSearchTerm=John%20Smith&perPage=100" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Step 4 -- Search base company name:

```bash
curl -s "https://searchcarriers.com/api/v3/search?superSearchTerm=Pacific%20Transport&perPage=100" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Step 5 -- Compile results into relationship map table with evidence and confidence scores.

### Example 2: Entity Network from Company Name

**User**: "Show me entities connected to Pacific Transport"

```bash
curl -s "https://searchcarriers.com/api/v3/search?superSearchTerm=Pacific%20Transport&perPage=100" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Group results by shared characteristics (address clusters, officer clusters). Present clusters as probable corporate families. Offer to drill into a specific cluster.

### Example 3: Chameleon Carrier Investigation

**User**: "Check if DOT 12345 might be a chameleon carrier"

Retrieve the seed carrier. Note its creation date, officers, and address. Search for other DOTs sharing officers or address. If any INACTIVE DOTs appear with safety issues and the seed DOT was created shortly after, flag the chameleon pattern with full evidence.

### Example 4: Officer Network Trace

**User**: "What other companies does the owner of DOT 12345 run?"

Retrieve the seed carrier. Extract all names from `company_officers`. For each officer:

```bash
curl -s "https://searchcarriers.com/api/v3/search?superSearchTerm={officer_name}&perPage=100" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Filter to carriers where the officer name appears in `company_officers`. Present as an officer-centric network: "John Smith is an officer at the following carriers: ..."

### Example 5: Address Cluster Analysis

**User**: "What other carriers operate from 123 Main St, Dallas, TX?"

```bash
curl -s "https://searchcarriers.com/api/v3/search?addressCity=Dallas&addressState=TX&perPage=100" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Post-filter for results where `phy_street` contains "123 Main". Present all matches, noting which share officers or other attributes beyond just the address.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| HTTP Status | Meaning | Action |
|---|---|---|
| 401 | Invalid or missing API key | Inform the user to check `SEARCHCARRIERS_API_KEY` |
| 403 | Feature requires Pro tier | Entity mapping relies on Pro-tier endpoints; inform the user |
| 404 | Seed DOT not found | Verify the DOT number; suggest searching by name instead |
| 422 | Invalid parameter format | Check parameter encoding; names with special characters need URL encoding |
| 429 | Rate limit exceeded | Entity mapping is API-intensive; pace requests and inform the user of limits |
| 500+ | Server error | Retry once; if persistent, report the issue |

**Mapping-specific guidance:**
- If a search returns 100+ results, narrow with additional filters (state, status) rather than paginating through all results.
- If no relationships are found, state this clearly. A carrier with zero connections is a valid finding -- it may be a sole proprietor with one DOT.
- When the relationship map grows beyond 10 entities, summarize clusters rather than listing every entity individually.

## Resources

- FMCSA chameleon carrier guidance: Carriers that re-register to evade safety records; reportable under 49 CFR 385.337
- Dun & Bradstreet DUNS numbers: 9-digit identifiers linking business entities to corporate hierarchies
- Common carrier naming patterns: Base name + suffix (LLC, Inc, Corp) + descriptor (Transport, Trucking, Logistics, Express, Freight)
- FMCSA entity types: Carrier, Broker, Freight Forwarder, Cargo Tank Facility, Shipper
- SearchCarriers API documentation: `https://searchcarriers.com/docs`
- Carrier object field reference: `{baseDir}/docs/carrier-fields.md`
