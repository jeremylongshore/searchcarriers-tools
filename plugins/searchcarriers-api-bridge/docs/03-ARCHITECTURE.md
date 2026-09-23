# API Bridge - Architecture

## System Context

API Bridge is a **STANDALONE** integration plugin. It does not participate in the stackable pipeline (Carrier Intel -> Risk Engine -> Ops Reporter). Instead, it provides enterprise integration capabilities that operate alongside the pipeline: bulk data operations, TMS synchronization, API monitoring, and webhook management.

```
                    SEARCHCARRIERS PLUGIN ECOSYSTEM
  =====================================================================

  STACKABLE PIPELINE (per-carrier, on-demand)
  +-------------------+    +------------------+    +-------------------+
  | CARRIER INTEL     |--->| RISK ENGINE      |--->| OPS REPORTER      |
  | (INPUT)           |    | (ANALYSIS)       |    | (OUTPUT)           |
  | Free              |    | Pro              |    | Pro                |
  +-------------------+    +------------------+    +-------------------+

  STANDALONE PLUGINS (operational, batch, monitoring)
  +-------------------+    +-------------------------------------------+
  | WATCHDOG          |    | API BRIDGE                                |
  | (MONITORING)      |    | (INTEGRATION)                            |
  |                   |    |                                           |
  | manage_watchlist  |    | api_health      bulk_lookup               |
  | get_alerts        |    | tms_sync        webhook_manage            |
  | route_alert       |    |                                           |
  | monitor_compliance|    | SMB: api_health, bulk_lookup, webhook_manage |
  |                   |    | Enterprise: + tms_sync                    |
  | Pro+ ($99/mo)     |    | SMB ($199/mo) / Enterprise ($499/mo)     |
  +-------------------+    +-------------------------------------------+
         |                           |
  Carrier Watch API          SearchCarriers REST API v1
  (monitoring data)          (carrier data + webhook config)
```

**Relationship to pipeline plugins**: API Bridge can consume Carrier Intel output. For example, a user might run `carrier_profile` on 50 carriers via Carrier Intel, then pass that data to `tms_sync` for export. But API Bridge does not depend on the pipeline. Its `bulk_lookup` tool calls the SearchCarriers API directly.

**Relationship to Watchdog**: `webhook_manage` configures the same Carrier Watch webhooks that Watchdog's `get_alerts` monitors. They share the Carrier Watch API but serve different purposes -- API Bridge manages the plumbing, Watchdog consumes the data.

## Component Design

| Component | Location | Responsibility |
|-----------|----------|---------------|
| **MCP Server** | `scripts/api_bridge_mcp.py` | Registers 4 MCP tools, handles incoming tool calls, delegates to processing modules, enforces tier gating. Thin I/O shell. |
| **Batch Processor** | `scripts/batch.py` (planned) | Manages bulk_lookup execution: DOT queue, rate limiting, progress tracking, error isolation, result accumulation. |
| **Rate Limiter** | `scripts/rate_limiter.py` (planned) | Token bucket implementation shared across all tools. Tracks API call budget, enforces 3 req/s ceiling, provides remaining budget to api_health. |
| **TMS Mapper** | `scripts/tms_mapper.py` (planned) | Field mapping engine. Loads TMS format definitions, maps SearchCarriers fields to TMS columns, handles date and status code translation. |
| **Health Checker** | `scripts/health.py` (planned) | Endpoint probing logic. Tests each API endpoint, measures response time, parses rate limit headers, computes aggregate health status. |
| **Local Webhook Registry** | `webhook_manage` in the MCP server | Stores downstream delivery configuration locally. It does not call an upstream SearchCarriers webhook API. |
| **Commands** | `commands/` (planned) | Slash command definitions for common operations. |
| **Embedded Skill** | `skills/` (planned) | Teaches Claude when to use API Bridge tools, how to chain bulk_lookup with tms_sync, and how to interpret health check results. |

## Data Flow

### Bulk Lookup

```
User: "Look up these 50 DOT numbers: 69494, 27021, 3456789, ..."
  |
  v
Claude invokes bulk_lookup(dot_numbers=[...], sections="standard")
  |
  v
MCP Server: bulk_lookup
  |
  +--> Tier check: is user's tier >= smb? (yes)
  |
  +--> Batch Processor initializes:
  |    - DOT queue: [69494, 27021, 3456789, ...]
  |    - Rate limiter: 3 tokens, refill 1/sec
  |    - Results accumulator: []
  |    - Error log: []
  |
  +--> Processing loop (per DOT):
  |    |
  |    +--> Acquire rate limit token (wait if exhausted)
  |    +--> HTTP GET /search?dotNumber={dot}
  |    +--> If sections == "standard" or "full":
  |    |    +--> Acquire token
  |    |    +--> HTTP GET /company/{dot}/authorities
  |    +--> If sections == "full":
  |    |    +--> Acquire token
  |    |    +--> HTTP GET /company/{dot}/insurances
  |    |
  |    +--> On success: append to results
  |    +--> On error: log error, continue to next DOT
  |    +--> Report progress: "34 of 50 complete"
  |
  +--> Build response:
       {
         meta: { tool, timestamp, total, succeeded, failed, sections },
         results: [ { dot_number, carrier, authorities?, insurances? }, ... ],
         errors: [ { dot_number, error_code, message }, ... ]
       }
  |
  v
Claude receives batch results, formats for user
```

### API Health Check

```
User: "Check the SearchCarriers API health"
  |
  v
MCP Server: api_health
  |
  +--> Tier check: is user's tier >= smb? (yes)
  |
  +--> Probe endpoints (sequential, using known DOT 69494):
  |    +--> GET /search?dotNumber=69494          --> measure latency, capture status
  |    +--> GET /company/69494/authorities       --> measure latency, capture status
  |    +--> GET /company/69494/insurances        --> measure latency, capture status
  |    +--> GET /company/69494/equipment         --> measure latency, capture status
  |    +--> GET /company/69494/vehicles          --> measure latency, capture status
  |
  +--> Parse rate limit headers from responses:
  |    X-RateLimit-Limit, X-RateLimit-Remaining, Retry-After
  |
  +--> Classify each endpoint: ok (<2000ms), slow (>=2000ms), error (non-2xx)
  |
  +--> Compute overall status:
  |    - healthy: all endpoints ok
  |    - degraded: any endpoint slow or errored, but not all
  |    - down: all endpoints errored
  |
  +--> Build response with per-endpoint details and rate limit info
```

### TMS Sync (Export)

```
User: "Export the bulk lookup results to McLeod CSV format"
  |
  v
MCP Server: tms_sync(action="export", carrier_data=[...], format="mcleod")
  |
  +--> Tier check: is user's tier >= enterprise? (yes)
  |
  +--> TMS Mapper:
  |    +--> Load McLeod field mapping definition
  |    +--> For each carrier in carrier_data:
  |    |    +--> Map SearchCarriers fields to McLeod columns
  |    |    +--> Convert dates: ISO 8601 -> MM/DD/YYYY
  |    |    +--> Translate status codes: "A" -> "Active"
  |    |    +--> Handle missing fields: empty string, not error
  |    |
  |    +--> Generate CSV with McLeod column headers
  |    +--> Append metadata row (source, timestamp, version)
  |
  +--> Return CSV content as string
```

### Webhook Management

```
User: "Create a webhook for carrier authority changes at https://hooks.example.com/carriers"
  |
  v
MCP Server: webhook_manage(action="create", url="https://hooks.example.com/carriers",
                           events=["authority_change"], secret="optional_hmac_secret")
  |
  +--> Tier check: is user's tier >= smb? (yes)
  |
  +--> Validate URL: must be HTTPS, valid format
  +--> Validate events: must be in known event type list
  |
  +--> Write a local downstream webhook record:
  |    ~/.searchcarriers/webhooks.json
  |    { url, events, secret }
  |
  +--> Return: { webhook_id, url, events, status: "active", created_at }
```

## Batch Processing Architecture

Bulk operations are the core complexity in API Bridge. The batch processor manages three concerns:

**1. Rate Limiting**

The SearchCarriers API recommends a 3 requests/second ceiling. The batch processor uses a token bucket with 3 tokens, refilling 1 token per second. When a bulk_lookup of 100 DOTs with `standard` sections (2 API calls per DOT = 200 total calls) runs, the rate limiter spaces requests to avoid 429 responses.

Estimated batch times at 3 req/s:
- 100 DOTs, basic (1 call each): ~34 seconds
- 100 DOTs, standard (2 calls each): ~67 seconds
- 100 DOTs, full (3 calls each): ~100 seconds

**2. Error Isolation**

A single failed DOT must not abort the entire batch. The batch processor wraps each DOT's API calls in a try/catch block, logs the error with the DOT number and HTTP status code, and continues to the next DOT. The final response includes both the successful results and the error log.

**3. Progress Reporting**

Long-running batches (60-100+ seconds) need progress feedback. The batch processor reports progress at regular intervals via the MCP tool's progress callback mechanism. Format: `"Processing: 34/100 complete (2 errors so far)"`.

## TMS Field Mapping

TMS field mapping is a configuration-driven layer. Each supported TMS has a mapping definition that translates SearchCarriers carrier object fields to TMS-specific column names, date formats, and status vocabularies.

```
SearchCarriers Field    McLeod Column         TMW Column          Generic CSV
--------------------    -------------         ----------          -----------
legal_name              CarrierName           carrier_name        legal_name
dot_number              DOTNumber             dot_num             dot_number
mc_mx_ff_numbers        MCNumber              mc_number           mc_number
phy_street              Address1              addr_line1          address
phy_city                City                  city                city
phy_state               State                 state               state
phy_zip                 Zip                   zip                 zip_code
phone                   Phone                 phone_num           phone
status_code             Status (Active/Inactive)  status          status_code
safety_rating           SafetyRating          safety_rtg          safety_rating
power_units             PowerUnits            pwr_units           power_units
total_drivers           TotalDrivers          drivers             total_drivers
```

Mappings are stored as Python dictionaries in `scripts/tms_mapper.py`. Adding a new TMS format requires adding a new mapping dictionary and registering it in the format registry. No code changes to the core mapper logic.

## Security Model

**API key handling:** Same as other plugins. `SEARCHCARRIERS_API_KEY` from environment, Bearer token in Authorization header, never logged or written to disk.

**Bulk operation scope:** A single `bulk_lookup` call can generate 100-300 API requests. The API key's rate limit and tier determine what is permitted. API Bridge respects the API's rate limit responses (429) and does not attempt to circumvent them.

**Webhook secrets:** When creating a webhook, the user can provide an HMAC secret. This secret is sent to the Carrier Watch API for server-side signature validation. API Bridge stores no secrets locally -- the secret passes through to the server and is not retained.

**TMS data handling:** Carrier data formatted for TMS export is returned as a string (CSV or JSON content). It is not written to disk by the MCP server. The user receives it in Claude's context and can save it to a file themselves. No PII beyond FMCSA-reported business contact information.

## Error Handling Strategy

| Error | Trigger | Response | Recovery |
|-------|---------|----------|----------|
| Tier insufficient | SMB user calls tms_sync | Structured tier error with upgrade URL | No retry; show Enterprise pricing |
| Bulk lookup -- single DOT fails | One DOT returns 404 in a batch | Error logged, batch continues | Include failed DOT in error summary |
| Bulk lookup -- rate limited | 429 during batch processing | Pause, wait for Retry-After, resume | Automatic; transparent to user |
| Bulk lookup -- too many DOTs | Input exceeds 100 DOTs | "Maximum 100 DOT numbers per batch" | User splits input |
| API health -- endpoint down | Probe returns 5xx | Report endpoint as "error" with status code | Include in degraded/down status |
| Webhook -- invalid URL | Non-HTTPS or malformed URL | "Webhook URL must be HTTPS" | User corrects URL |
| Webhook -- invalid event type | Unknown event type provided | "Unknown event type: {type}. Valid types: ..." | User selects valid type |
| TMS export -- unknown format | Unsupported TMS format requested | "Supported formats: mcleod, tmw, generic_csv, json" | User selects valid format |
| Network error | Cannot reach API | "Cannot reach SearchCarriers API. Check network." | Surface immediately |

## Performance Requirements

| Operation | Target Latency | Max Latency | Notes |
|-----------|---------------|-------------|-------|
| `api_health` (5 endpoints) | < 5 seconds | 10 seconds | 5 sequential probes |
| `bulk_lookup` (10 DOTs, basic) | < 5 seconds | 10 seconds | 10 API calls at 3/s |
| `bulk_lookup` (100 DOTs, basic) | < 40 seconds | 60 seconds | 100 API calls at 3/s |
| `bulk_lookup` (100 DOTs, standard) | < 70 seconds | 100 seconds | 200 API calls at 3/s |
| `tms_sync` export (50 carriers) | < 200ms | 500ms | Pure formatting, no I/O |
| `tms_sync` import + diff (50 carriers) | < 25 seconds | 40 seconds | 50 API calls + comparison |
| `webhook_manage` (any action) | < 2 seconds | 5 seconds | Single API call |
| MCP server cold start | < 2 seconds | 5 seconds | Python import + env validation |
| Tier check | < 1ms | N/A | In-memory lookup |

Primary bottleneck is the SearchCarriers API rate limit. Bulk operations scale linearly with DOT count and section depth. The rate limiter ensures predictable execution time: total_api_calls / 3 = seconds (approximately).
