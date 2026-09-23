# Carrier Intel - Architecture

## System Context

Carrier Intel is the **INPUT** stage of the SearchCarriers stackable pipeline. It retrieves raw carrier data from the SearchCarriers REST API and produces structured JSON that downstream plugins consume.

```
                    SEARCHCARRIERS STACKABLE PIPELINE
  =====================================================================

  +-----------------------+     +------------------------+     +-------------------------+
  |   CARRIER INTEL       |     |   RISK ENGINE          |     |   OPS REPORTER          |
  |   (INPUT)             |---->|   (ANALYSIS)           |---->|   (OUTPUT)              |
  |                       |     |                        |     |                         |
  |   carrier_lookup      |     |   risk_score           |     |   generate_report       |
  |   carrier_profile     |     |   vetting_check        |     |   generate_fleet        |
  |   entity_map          |     |   insurance_check      |     |   generate_compare      |
  |   fleet_summary       |     |   compliance_audit     |     |   export_data           |
  |                       |     |                        |     |                         |
  |   Min: Free           |     |   Min: Pro             |     |   Min: Pro              |
  +-----------------------+     +------------------------+     +-------------------------+
         ^                              |                              |
         |                              |                              |
  SearchCarriers API v1         Consumes Carrier Intel         Consumes Risk Engine
  (data source)                 JSON output                    JSON output
```

**Upstream**: SearchCarriers REST API at `https://searchcarriers.com/api/v1`. This is the only external dependency.

**Downstream consumers**: Risk Engine reads Carrier Intel's carrier data, authority status, and insurance records to compute risk scores. Ops Reporter reads both Carrier Intel and Risk Engine output to generate formatted reports. Claude handles the data routing -- when a user asks "vet this carrier", Claude calls Carrier Intel first, passes the result to Risk Engine, then passes both to Ops Reporter.

**Standalone usage**: Carrier Intel works independently. A user can look up a carrier, get a full profile, map entities, or summarize a fleet without ever touching Risk Engine or Ops Reporter.

## Component Design

| Component | Location | Responsibility |
|-----------|----------|---------------|
| **MCP Server** | `scripts/carrier_intel_mcp.py` | Registers 4 MCP tools, handles incoming tool calls, makes HTTP requests to SearchCarriers API, enforces tier gating, returns structured JSON. This is a thin wrapper -- no business logic, no data interpretation, no risk scoring. |
| **Commands** | `commands/sc-lookup.md`, `commands/sc-profile.md` | Slash command definitions that map user input to MCP tool calls. `/sc-lookup` maps to `carrier_lookup`, `/sc-profile` maps to `carrier_profile`. Commands handle argument parsing and output formatting. |
| **Embedded Skill** | `skills/searchcarriers-carrier-intel/SKILL.md` | Teaches Claude how to use Carrier Intel tools effectively: when to use which tool, how to interpret the 143-field carrier object, how to chain tools together, and how to present results to a freight professional. |
| **Agent** | `agents/carrier-analyst.md` | Autonomous agent definition for complex carrier analysis workflows. Given a carrier name or DOT, runs lookup, profile, fleet summary, and optionally entity mapping, then synthesizes findings into a natural language briefing. |

## Data Flow

### Single Carrier Lookup

```
User: "look up JB Hunt"
  |
  v
Claude parses natural language, identifies carrier_lookup tool
  |
  v
MCP Server: carrier_lookup(search_term="JB Hunt")
  |
  +--> Tier check: is user's tier >= free? (yes)
  |
  +--> Auto-detect search type: "JB Hunt" is not DOT/MC/VIN -> use superSearchTerm
  |
  +--> HTTP GET https://searchcarriers.com/api/v3/search?superSearchTerm=JB+Hunt
  |
  +--> Parse response: extract carrier records from paginated result
  |
  +--> Build response JSON: { meta: {...}, carriers: [...] }
  |
  v
Claude receives structured JSON, formats for user
  |
  v
User sees: carrier name, DOT, MC, status, location, fleet size, operation type
```

### Full Profile Aggregation

```
User: "/sc-profile 69494"
  |
  v
MCP Server: carrier_profile(dot_number="69494")
  |
  +--> Tier check: is user's tier >= free? (yes)
  |
  +--> HTTP GET /search?dotNumber=69494              --> carrier data with selected v3 sections
  +--> HTTP GET /company/69494/authorities           --> authority records
  +--> HTTP GET /company/69494/insurances            --> insurance records
  |
  +--> Combine into unified response:
  |    {
  |      meta: { tool: "carrier_profile", dot_number: "69494", timestamp: "..." },
  |      carrier: { legal_name: "WERNER ENTERPRISES INC", ... },
  |      authorities: [ { broker_authority_status: "A", ... } ],
  |      insurances: [ { ... } ]
  |    }
  |
  v
Claude receives unified profile, formats for user
  |
  v
User sees: complete carrier identity, all authority statuses, insurance coverage
```

### Pipeline Chain (Carrier Intel -> Risk Engine -> Ops Reporter)

```
User: "vet Werner Enterprises and give me a report"
  |
  v
Claude orchestrates three-stage pipeline:
  |
  +--> Stage 1: Carrier Intel
  |    carrier_lookup("Werner Enterprises") -> carrier data
  |    carrier_profile(dot=69494) -> authorities + insurance
  |
  +--> Stage 2: Risk Engine (consumes Stage 1 output)
  |    risk_score(carrier_data) -> risk assessment
  |    insurance_check(insurance_data) -> coverage validation
  |
  +--> Stage 3: Ops Reporter (consumes Stage 1 + Stage 2 output)
  |    generate_report(carrier_data + risk_data) -> formatted vetting report
  |
  v
User receives: formatted vetting report with carrier details, risk scores, and recommendation
```

## Integration Points

| Endpoint | Method | Used By | Purpose |
|----------|--------|---------|---------|
| `/api/v3/search` | GET | `carrier_lookup` | Search carriers by DOT, docket, name, or location filters |
| `/api/v3/company/{dot}` | GET | `carrier_profile`, `entity_map` | Retrieve selected company sections |
| `/api/v1/search/by-vin/{vin}` | GET | `entity_map` | Resolve carrier relationships for a VIN |
| `/api/v3/company/{dot}/equipment` | GET | `entity_map`, `fleet_summary` | Current equipment roster with VINs |

All endpoints use GET method, accept `Authorization: Bearer {token}` header, and return JSON with Laravel-standard pagination where applicable.

## Security Model

**API key handling:**
- API key is stored in the `SEARCHCARRIERS_API_KEY` environment variable
- The MCP server reads this at startup; if missing, the server fails with a clear error message directing the user to `https://searchcarriers.com/settings/api-tokens`
- The key is passed as a Bearer token in the Authorization header on every API request
- The key is never logged, never written to disk, never included in tool output

**Data classification:**
- Carrier data from SearchCarriers is derived from public FMCSA records. Legal name, DOT, MC, address, fleet size, safety ratings, and authority status are all public information
- Contact fields (phone, fax, email) are included in the carrier object and are FMCSA-reported -- not private PII, but should be handled with standard care
- No user-specific data is stored. No session state. No local database. Data flows from API through the MCP server into Claude's context and is handled according to Claude's data retention policies

**What gets logged:**
- Tool invocations (tool name, search term type, DOT number) for debugging
- API response status codes and latency for performance monitoring
- Error conditions (timeouts, rate limits, auth failures)

**What does NOT get logged:**
- Full API responses (carrier data stays in context only)
- API keys or tokens
- User identity or session information

## Error Handling Strategy

| Error | HTTP Code | User Message | Recovery Action |
|-------|----------|-------------|----------------|
| API key not set | N/A (startup) | "SEARCHCARRIERS_API_KEY not set. Get your key at https://searchcarriers.com/settings/api-tokens" | Block all tool calls until key is configured |
| Invalid API key | 401 | "Invalid API key. Verify your key at https://searchcarriers.com/settings/api-tokens" | No retry -- user must fix key |
| Insufficient tier | 403 | "entity_map requires Pro tier. Your tier: Free. Upgrade at https://searchcarriers.com/pricing" | No retry -- show upgrade path |
| Carrier not found | 404 | "No carrier found for DOT 99999999. Try searching by name with carrier_lookup." | Suggest alternative search |
| Rate limited | 429 | "Rate limit reached. Retrying in {n} seconds..." | Respect `Retry-After` header, retry up to 3 times with exponential backoff |
| API timeout | 504 | "SearchCarriers API timed out. Retrying..." | Retry up to 3 times with 2s/4s/8s backoff |
| API server error | 500/502/503 | "SearchCarriers API returned an error. Try again in a moment." | Retry once after 2 seconds |
| Invalid DOT format | 422 | "DOT number must be numeric. Got: '{input}'" | No retry -- user must fix input |
| Network error | N/A | "Cannot reach SearchCarriers API. Check your network connection." | No retry -- surface immediately |

All errors return structured JSON: `{ "error": { "code": "RATE_LIMITED", "message": "...", "upgrade_url": "..." } }`

## Performance Requirements

| Operation | Target Latency | Max Latency | Notes |
|-----------|---------------|-------------|-------|
| `carrier_lookup` (single search) | < 1 second | 3 seconds | Single API call |
| `carrier_profile` (3 API calls) | < 3 seconds | 5 seconds | Sequential: search + authorities + insurance |
| `entity_map` (10 VINs) | < 10 seconds | 30 seconds | 1 equipment call + up to 10 VIN searches (rate-limited) |
| `entity_map` (50 VINs) | < 30 seconds | 60 seconds | Batched VIN searches respecting 3 req/s limit |
| `fleet_summary` (2 API calls) | < 2 seconds | 5 seconds | Parallel: equipment + vehicles |
| MCP server startup | < 2 seconds | 5 seconds | Import + API key validation |
| Tier check | < 1 millisecond | N/A | In-memory comparison, no API call |

**Caching strategy (v0.2):** Client-side cache with 5-minute TTL. Same DOT lookup within 5 minutes returns cached data without hitting the API. Reduces redundant calls during pipeline chains (carrier_lookup followed by carrier_profile would reuse the search result).

**Rate limit management:** The MCP server maintains a simple token bucket (3 tokens, refill 1/second) to stay within the API's ~3 req/s recommended limit. Entity mapping with large fleets is the primary concern -- a carrier with 100 VINs needs 101 API calls, which at 3 req/s takes ~34 seconds.
