---
name: searchcarriers-carrier-intel
description: Interprets carrier data from the carrier-intel MCP tools and provides freight industry context. Use when processing carrier lookup results.
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
- plugin
---

# Carrier Intel — Embedded Skill

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current v3/v2/v1 route map and verified parameter names. Do not infer newer-version routes.

This skill provides the intelligence layer for the carrier-intel plugin. It teaches you how to interpret raw data returned by the four MCP tools (`carrier_lookup`, `carrier_profile`, `entity_map`, `fleet_summary`), apply freight industry context, detect red flags, and format output for both human consumption and downstream pipeline stages.

The carrier-intel plugin sits at the INPUT stage of the pipeline. Data it produces flows to the Risk Engine (ANALYSIS) and then to Ops Reporter (OUTPUT). Correct interpretation here determines the quality of all downstream analysis.

## Prerequisites

- **Minimum tier**: Free (entity_map requires Pro)
- MCP server `searchcarriers-carrier-intel` must be running and accessible
- `SEARCHCARRIERS_API_KEY` environment variable set with a valid key
- Familiarity with FMCSA terminology (DOT, MC, SCAC, OOS, BIPD)

## Instructions

### Interpreting carrier_lookup Results

The `carrier_lookup` tool returns an array of carrier objects. Each v3 company response contains the selected nested sections. Key interpretation rules:

**Status Codes**

| Status | Meaning | Implication |
|--------|---------|-------------|
| ACTIVE | Carrier has current FMCSA registration | Can legally operate |
| INACTIVE | Registration lapsed or voluntarily deactivated | Cannot legally operate for-hire |
| NOT AUTHORIZED | Never completed authority process | Cannot operate as for-hire |
| OUT OF SERVICE | FMCSA has issued an OOS order | Imminent safety concern |

**Fleet Size Codes**

| Code | Range | Description |
|------|-------|-------------|
| A | 0 | No units reported |
| B | 1-6 | Owner-operator / micro |
| C | 7-11 | Small fleet |
| D | 12-24 | Small-medium fleet |
| E | 25-99 | Medium fleet |
| F | 100-499 | Large fleet |
| G | 500-999 | Very large fleet |
| H | 1000+ | Mega fleet |

**Operation Type Codes**

| Code | Type | Description |
|------|------|-------------|
| A | Auth For Hire | Authorized motor carrier, common or contract |
| B | Exempt For Hire | Exempt from economic regulation (farm, newspaper, etc.) |
| C | Private (Property) | Hauls own goods only, not for-hire |
| D | Private (Passengers) | Private passenger transport |
| E | Private (Enterprise) | Enterprise carrier, private non-for-hire |
| X | Multiple | Combination of operation types |

### Interpreting carrier_profile Data

The `carrier_profile` tool combines three API calls into one response: the base carrier search record, authority details, and insurance records.

**Authority Statuses**

Each authority type (common, contract, broker) has its own status:

- **ACTIVE**: Authority is in good standing and authorized
- **INACTIVE**: Authority was active but has been deactivated (insurance lapse, voluntary surrender, or revocation)
- **PENDING**: Application filed but not yet granted — carrier cannot operate under this authority yet
- **REVOKED**: FMCSA has revoked this authority — serious compliance failure

A carrier can hold multiple authority types simultaneously. For-hire trucking requires common or contract authority. Brokerage requires broker authority with a BMC-84/85 bond.

**Insurance Interpretation**

- **BIPD (Bodily Injury & Property Damage)**: Required for all for-hire carriers. Minimum $750K for general freight, $1M for hazmat, $5M for bulk hazmat/explosives.
- **Cargo**: Not federally required but industry standard. Absence is a yellow flag for broker vetting.
- **Bond/Trust (BMC-84/85)**: Required only for broker authority. Must be $75K minimum.
- Active insurance means `insurance_status` = active and `cancelled_date` is null.
- A record with a future `cancelled_date` indicates a pending cancellation — time-sensitive concern.

### Pipeline Output Contracts

When preparing data for the Risk Engine (next pipeline stage), structure the output as:

```json
{
  "dot_number": 1234567,
  "carrier": {
    "legal_name": "...",
    "status": "ACTIVE",
    "carrier_operation": "A",
    "power_units": 42,
    "drivers": 55,
    "hm_ind": "N",
    "safety_rating": "SATISFACTORY",
    "mcs150_date": "2024-06-15",
    "fleet_size_code": "E"
  },
  "authorities": [
    {
      "authority_type": "common",
      "status": "ACTIVE",
      "docket_number": "MC-123456"
    }
  ],
  "insurances": [
    {
      "insurance_type": "BIPD",
      "insurance_status": "active",
      "coverage_amount": 1000000,
      "insurance_company": "...",
      "effective_date": "2024-01-15",
      "cancelled_date": null
    }
  ],
  "entity_relationships": [],
  "fleet": {
    "power_units": 42,
    "vehicles": []
  }
}
```

The Risk Engine expects these exact top-level keys. Missing keys cause scoring gaps. Always populate `dot_number` and `carrier` at minimum.

### Red Flag Detection Rules

Apply these checks to every carrier record. When a flag triggers, include it in a clearly separated warning block in the output.

| Priority | Condition | Flag | Severity |
|----------|-----------|------|----------|
| 1 | `status` is INACTIVE, OUT OF SERVICE, or NOT AUTHORIZED | Cannot legally operate | CRITICAL |
| 2 | No active BIPD insurance record exists | No liability insurance | CRITICAL |
| 3 | `safety_rating` is UNSATISFACTORY | Failed safety review | CRITICAL |
| 4 | `safety_rating` is CONDITIONAL | Safety deficiencies found | HIGH |
| 5 | Active authority but zero power units AND zero drivers | Possible shell/paper carrier | HIGH |
| 6 | `mcs150_date` is more than 2 years old | Registration data may be stale | MEDIUM |
| 7 | Carrier registered < 6 months ago (new entrant) | Limited operating history | MEDIUM |
| 8 | Vehicle OOS rate > 25% | Equipment maintenance concerns | MEDIUM |
| 9 | Driver OOS rate > 10% | Driver compliance concerns | MEDIUM |
| 10 | Active authority with pending insurance cancellation | Coverage may lapse soon | HIGH |

### Formatting Guidelines

**For human-readable output** (slash commands, chat responses):

- Use markdown tables for structured data
- Bold carrier name and DOT in headings
- Separate red flags into a distinct warning section
- Format dollar amounts with commas and $ prefix
- Show dates as YYYY-MM-DD
- Include national averages next to OOS rates for context
- Offer next-step suggestions with specific commands

**For pipeline output** (passing to Risk Engine):

- Use the JSON contract structure defined above
- Include all available fields — do not pre-filter
- Set missing fields to `null`, not empty strings
- Ensure numeric fields are numbers, not strings

## Examples

### Example 1: Single Carrier Lookup

User asks: "Look up DOT 1234567"

1. Call `carrier_lookup` with `dot_number: 1234567`
2. Receive single carrier object
3. Format as full summary with all sections
4. Check red flags — if safety_rating is CONDITIONAL, flag it
5. Suggest `/sc-profile 1234567` for the combined view

### Example 2: Name Search with Multiple Results

User asks: "Find carriers named Werner"

1. Call `carrier_lookup` with `search_term: "Werner"`
2. Receive array of 10+ results
3. Show top 5 in compact table (DOT, name, city/state, status, fleet size)
4. State total count
5. Ask user which to expand, or offer to refine

### Example 3: Pipeline Handoff

After a carrier_profile call, prepare the pipeline output:

1. Extract carrier base fields into `carrier` object
2. Map authority records into `authorities` array
3. Map insurance records into `insurances` array
4. If entity_map was also called, include relationships
5. Validate all required keys are present
6. Pass structured object to Risk Engine

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| MCP tool not available | Server not started or misconfigured | Check `.mcp.json` config and restart the MCP server |
| 401 from API | Invalid or missing API key | Verify `SEARCHCARRIERS_API_KEY` is set and valid |
| 404 for DOT lookup | DOT number not in FMCSA database | Suggest searching by name or MC number instead |
| 422 invalid parameters | Wrong parameter types or format | DOT must be numeric, SCAC must be 2-4 alpha |
| 429 rate limit | Too many requests | Wait for `Retry-After` header duration; cache results with 5-min TTL |
| Empty result set (200) | No carriers match the query | Report "no results found" — do not show empty tables |
| entity_map returns 403 | User tier below Pro | Explain entity mapping requires Pro tier |
| Incomplete profile data | API returned partial fields | Process available data, note which sections are missing |

## Resources

- Carrier object field reference: `{baseDir}/docs/carrier-fields.md`
- Plugin configuration: `{baseDir}/.claude-plugin/plugin.json`
- MCP server source: `{baseDir}/scripts/carrier_intel_mcp.py`
- Pipeline architecture: `{baseDir}/docs/03-ARCHITECTURE.md`
- FMCSA carrier operation codes: A/B/C/D/E/X (see table above)
- FMCSA safety rating definitions: Satisfactory, Conditional, Unsatisfactory, Not Rated
- National OOS benchmarks: vehicle ~20%, driver ~5%
- Insurance minimums: 49 CFR Part 387
