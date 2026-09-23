# Carrier Intel - Product Requirements

## Goals

1. **Enable natural language carrier research.** A user types "look up Werner Enterprises" or "find DOT 69494" and gets structured carrier data in seconds, without leaving an MCP-capable client.
2. **Reduce carrier lookup time from minutes to seconds.** Single lookups complete in under 3 seconds. Full profiles (search + authorities + insurance) complete in under 5 seconds.
3. **Standardize output for downstream plugins.** Every tool produces structured JSON that the Risk Engine and Ops Reporter can consume without transformation. Carrier Intel is the INPUT stage -- its output is the pipeline's raw material.
4. **Make the Free tier genuinely useful.** Three of four tools work on Free. Users experience real value before hitting any paywall.

## Non-Goals

1. **NOT replacing the SearchCarriers web UI.** The web app serves users who want dashboards, saved searches, and visual analytics. This plugin serves users who want answers in their terminal.
2. **NOT doing risk scoring or safety assessment.** That is the Risk Engine plugin (pipeline stage 2). Carrier Intel retrieves data; Risk Engine interprets it. If a user asks "is this carrier safe?", Carrier Intel provides the raw safety fields -- Risk Engine provides the judgment.
3. **NOT generating reports or formatted documents.** That is the Ops Reporter plugin (pipeline stage 3). Carrier Intel returns structured data; Ops Reporter turns it into vetting reports, comparison tables, and export files.
4. **NOT implementing bulk operations.** Bulk carrier processing (CSV input, batch lookups) belongs to the API Bridge plugin. Carrier Intel handles single-carrier operations.
5. **NOT storing or caching data persistently.** Data flows through the plugin and into the model client's context. No local database, no file-based cache, no PII storage.

## User Stories

### US-01: Carrier Lookup by Any Identifier

As a **freight broker**, I want to **search for a carrier by DOT number, MC number, company name, SCAC code, or VIN**, so that **I can quickly find and identify any motor carrier without knowing which specific identifier to use**.

**Acceptance Criteria:**
- Searching by DOT number returns an exact match
- Searching by company name returns ranked results
- Searching by MC number finds the associated carrier
- Searching by VIN returns the carrier(s) associated with that vehicle
- Results include at minimum: legal name, DOT, MC, status, city/state, power units, and carrier operation type
- Empty results return a clear "no carrier found" message, not an error

### US-02: Full Carrier Profile

As a **compliance analyst**, I want to **get a complete carrier profile in a single request -- identity, contact, fleet size, operating authorities, and insurance status**, so that **I can make a vetting decision without opening multiple browser tabs or running multiple queries**.

**Acceptance Criteria:**
- A single command returns carrier search data, authority status, and insurance records
- Authority status shows broker, contract, and common authority with status dates
- Insurance records show active policies with coverage amounts and effective dates
- Output is structured so downstream plugins (Risk Engine) can consume it without transformation
- The command accepts a DOT number as input

### US-03: Entity Discovery

As a **fraud investigator**, I want to **discover companies related to a carrier through shared equipment (VINs)**, so that **I can identify chameleon carriers, shell companies, and undisclosed corporate relationships**.

**Acceptance Criteria:**
- Given a carrier's DOT, the tool retrieves their equipment roster
- For each VIN in the roster, searches for other carriers that have registered the same VIN
- Returns a map of carrier-to-carrier relationships with the shared VINs as evidence
- Clearly identifies when a VIN appears under multiple active carriers (a red flag)
- Requires Pro tier (entity mapping is a premium feature)

### US-04: Fleet Analysis

As a **operations manager**, I want to **see a carrier's fleet composition -- equipment types, makes, models, and total counts**, so that **I can verify they have the right equipment for my freight and assess their operational scale**.

**Acceptance Criteria:**
- Returns equipment breakdown by type (trucks, tractors, trailers, etc.)
- Includes make, model, and year distribution where available
- Shows total power units vs. total drivers ratio
- Includes both detailed equipment records and simplified vehicle list
- Works on Free tier

## Functional Requirements

### FR-01: Multi-Format Search with Auto-Detection

**Description:** The `carrier_lookup` tool accepts a search term and automatically determines the search strategy. If the input looks like a DOT number (all digits), search by `dotNumber`. If it matches MC format (e.g., "MC 1672915"), search by `docketNumber`. If it contains a VIN pattern (17 alphanumeric), search by `vin`. Otherwise, use `superSearchTerm` for fuzzy name matching.

**Acceptance Criteria:**
- Input "69494" searches by dotNumber and returns Werner Enterprises
- Input "MC 123456" searches v3 by `docketNumber`
- Input "Werner" searches by superSearchTerm
- Input "1FUJGHDV0CLBP8834" uses the dedicated v1 VIN path
- State and city use the v3 `addressState` and `addressCity` filters
- Returns paginated results (default 10 per page)

**Priority:** P0

### FR-02: Profile Aggregation

**Description:** The `carrier_profile` tool takes a DOT number and makes one v3
field-selected search request for core carrier, authority, and insurance fields.
It normalizes that response into one structured profile.

**Acceptance Criteria:**
- Returns a unified JSON object with `carrier`, `authorities`, and `insurances` sections
- Handles cases where authority or insurance records are empty
- Total response time under 5 seconds for the profile request
- Surfaces API and response-shape errors explicitly

**Priority:** P0

### FR-03: VIN-Based Entity Mapping

**Description:** The `entity_map` tool takes a DOT number, retrieves the carrier's equipment roster via `GET /company/{dot}/equipment`, extracts all VINs, then searches each VIN via `GET /search/by-vin/` to find other carriers that have registered the same equipment. Returns a relationship map.

**Acceptance Criteria:**
- Retrieves full equipment list for the target carrier
- Searches each unique VIN against the carrier database
- Returns a list of related carriers with the shared VINs as evidence
- Handles large fleets efficiently (100+ VINs should not cause timeouts)
- Gated to Pro tier -- Free users get a clear upgrade message
- Implements rate limiting to stay within 3 req/s API ceiling

**Priority:** P1

### FR-04: Fleet Summary

**Description:** The `fleet_summary` tool takes a DOT number and calls two endpoints: `GET /company/{dot}/equipment` for detailed equipment records (VIN, make, model, GVWR, year) and `GET /company/{dot}/vehicles` for the simplified vehicle list. It returns a combined fleet overview.

**Acceptance Criteria:**
- Returns equipment count by type (truck, tractor, trailer, etc.)
- Includes make/model distribution (top 5 makes)
- Shows detailed records from equipment endpoint alongside simplified vehicle list
- Calculates power unit to driver ratio from carrier data
- Response time under 3 seconds

**Priority:** P1

### FR-05: Tier Gating

**Description:** Every MCP tool checks the user's subscription tier before executing. Free users can access `carrier_lookup`, `carrier_profile`, and `fleet_summary`. Pro users can additionally access `entity_map`. Insufficient tier returns a structured error with the required tier name and an upgrade URL.

**Acceptance Criteria:**
- `carrier_lookup` works on Free tier and above
- `carrier_profile` works on Free tier and above
- `fleet_summary` works on Free tier and above
- `entity_map` requires Pro tier and above
- Tier check happens before any API calls (no wasted requests)
- Error message includes: required tier, current tier, and URL `https://searchcarriers.com/pricing`

**Priority:** P0

### FR-06: Structured JSON Output for Pipeline

**Description:** All four tools return structured JSON responses with consistent schema conventions so that downstream plugins (Risk Engine, Ops Reporter) can consume the data without transformation. Every response includes a `meta` block with tool name, timestamp, DOT number, and tier used.

**Acceptance Criteria:**
- Every response includes `meta: { tool, timestamp, dot_number, tier }`
- Carrier data uses the SearchCarriers 143-field schema as-is (no field renaming)
- Authority data includes `broker_authority_status`, `contract_authority_status`, `common_authority_status`
- Error responses follow a consistent `{ error: { code, message, upgrade_url? } }` format
- JSON is valid and parseable by downstream plugins without preprocessing

**Priority:** P0

## MVP Scope

Historical v0.1.0 planning scope:

- [x] `carrier_lookup` -- multi-format search with auto-detection
- [x] `carrier_profile` -- aggregated profile (search + authorities + insurance)
- [ ] `fleet_summary` -- equipment roster and vehicle list
- [ ] `entity_map` -- VIN-based entity mapping (Pro)
- [x] Tier gating on all four tools
- [x] Structured JSON output with meta blocks
- [x] Error handling for 401, 403, 404, 429, 504

Deferred to v0.2.0:

- SCAC code lookup integration into carrier_lookup
- Cached results with 5-minute TTL to reduce redundant API calls
- Batch mode for carrier_lookup (multiple DOTs in one call)

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|-------------|
| Single lookup latency | Target: < 1 second | Timer in MCP tool handler |
| Profile aggregation latency | Target: < 3 seconds | Timer across 3 API calls |
| Entity map latency (10 VINs) | Target: < 10 seconds | Timer across equipment + VIN searches |
| Error rate (unhandled exceptions) | Target: 0% | Exception logging in MCP server |
| Tier gate accuracy | Target: 100% (no Free user accesses Pro tools) | Integration tests |
| API call efficiency | Target: 0 wasted calls (tier check before API) | Request counter |
| User satisfaction | Target: lookup replaces manual SAFER workflow | User feedback |

## Dependencies

- **SearchCarriers REST API v1** -- all four tools depend on API availability at `https://searchcarriers.com/api/v1`
- **Valid API key** -- `SEARCHCARRIERS_API_KEY` environment variable must be set with a valid Laravel Sanctum bearer token
- **MCP protocol** -- plugin runs as an MCP server; requires Grok Build, Claude Code, or another MCP-capable client
- **httpx** -- async HTTP client for API calls
- **No dependency on other plugins** -- Carrier Intel is the INPUT stage and has zero upstream dependencies. Risk Engine and Ops Reporter depend on Carrier Intel's output, but not the reverse.
