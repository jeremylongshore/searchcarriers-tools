# API Bridge - Product Requirements

## Goals

1. **Enable batch carrier lookups at scale.** An IT team pastes a list of 100 DOT numbers and gets structured results for all of them in a single operation, with progress reporting and error isolation per carrier.
2. **Provide TMS-ready data exports.** Carrier data comes out in the column format their TMS expects -- McLeod, TMW, MercuryGate, or generic CSV -- without manual reformatting.
3. **Surface API health and rate limit status.** Operations teams see endpoint availability, response times, and remaining rate limit budget before they kick off a bulk job.
4. **Manage Carrier Watch webhooks programmatically.** IT teams configure, update, and remove webhook endpoints from the CLI instead of navigating the SearchCarriers web UI.

## Non-Goals

1. **NOT replacing the SearchCarriers web dashboard.** The web UI provides visual analytics, saved searches, and account management. API Bridge serves teams that need programmatic access and batch operations.
2. **NOT doing individual carrier lookups.** Single-carrier lookups belong to Carrier Intel. API Bridge handles batch operations (multiple carriers per call).
3. **NOT scoring or assessing risk.** Risk Engine handles risk scoring. API Bridge retrieves and formats data. If a user asks "are these carriers safe?", API Bridge provides the raw data -- Risk Engine provides the judgment.
4. **NOT delivering webhooks.** API Bridge manages webhook endpoint configuration (CRUD). The actual webhook delivery is handled server-side by SearchCarriers Carrier Watch infrastructure. API Bridge does not receive, route, or process webhook payloads.
5. **NOT implementing real-time streaming.** Bulk lookups are request-response, not streaming. Results are returned when the full batch completes (or after a configurable timeout with partial results).

## User Stories

### US-01: Batch Carrier Re-Qualification

As an **IT director at a freight brokerage**, I want to **submit a list of 50-100 DOT numbers and get structured carrier data for all of them in one operation**, so that **I can re-qualify our entire carrier panel without running individual lookups for three days**.

**Acceptance Criteria:**
- Accepts a list of up to 100 DOT numbers
- Returns structured carrier data for each DOT, including search data, authorities, and insurance
- Configurable data sections: basic (search only), standard (search + authorities), full (search + authorities + insurance)
- Reports progress during execution (e.g., "34 of 100 complete")
- Isolates errors per carrier -- one failed DOT does not abort the batch
- Returns a summary with success count, failure count, and failed DOTs

### US-02: API Health Check

As a **DevOps engineer supporting a carrier data pipeline**, I want to **check the SearchCarriers API health -- endpoint availability, response times, and rate limit status**, so that **I can diagnose issues before they affect our dispatch team's workflows**.

**Acceptance Criteria:**
- Tests core API endpoints: search, authorities, insurances, equipment, vehicles
- Reports response time per endpoint (ms)
- Reports HTTP status code per endpoint
- Shows current rate limit usage and remaining budget
- Returns overall health status: healthy, degraded, or down
- Completes in under 10 seconds

### US-03: TMS Data Export

As an **operations manager**, I want to **export carrier data in a format my TMS can import directly**, so that **I can update our carrier records without manually re-keying 50 fields per carrier**.

**Acceptance Criteria:**
- Fetches a carrier by DOT and returns a mapped record for `generic`, `mcleod`,
  `tms_international`, or `dat_power`
- Returns the field mapping guide and unmapped source fields beside the record
- Keeps serialization and file creation in the calling workflow

### US-04: TMS Data Import (Enterprise)

As a **systems integrator**, I want to **translate one TMS record into the SearchCarriers field vocabulary**, so that **I can inspect the mapping before a separate reconciliation workflow compares or applies it**.

**Acceptance Criteria:**
- Accepts one structured TMS record
- Maps TMS fields back to SearchCarriers schema
- Returns mapped and unmapped fields without making an API request
- Does not claim to perform a live diff or write into a TMS
- Requires Enterprise tier

### US-05: Webhook Endpoint Management

As an **IT manager**, I want to **maintain a local webhook configuration from the CLI**, so that **a separate delivery service has an explicit, reviewable routing file**.

**Acceptance Criteria:**
- Create a local webhook record with URL and event types
- List locally configured records
- Update an existing local record's URL or events
- Delete a webhook endpoint
- Validate webhook URL format before creating
- Make no claim that SearchCarriers registered the endpoint or delivered an event
- All operations require SMB tier

## Functional Requirements

### FR-01: Batch Carrier Lookup with Progress

**Description:** The `bulk_lookup` tool accepts a list of DOT numbers (up to 100) and a `sections` parameter that controls data depth. For each DOT, it calls the appropriate SearchCarriers API endpoints, respects rate limits, and accumulates results. Progress is reported at configurable intervals.

**Acceptance Criteria:**
- Input: `dot_numbers` (list of strings, max 100), `sections` (basic | standard | full)
- `basic`: 1 API call per DOT (search only)
- `standard`: 2 API calls per DOT (search + authorities)
- `full`: 3 API calls per DOT (search + authorities + insurance)
- Rate limiting: respects 3 req/s API ceiling with client-side token bucket
- Error isolation: failed DOTs are logged with error details, successful DOTs proceed
- Output includes: results array, summary (total, succeeded, failed), failed DOTs with error messages
- Progress reporting via MCP tool progress callback

**Priority:** P0

### FR-02: API Health Dashboard

**Description:** The `api_health` tool probes the SearchCarriers API endpoints and reports their status. It makes one lightweight request per endpoint using a known-good DOT (e.g., Werner DOT 69494) and measures response time. Rate limit headers are parsed and included.

**Acceptance Criteria:**
- Tests endpoints: `/search`, `/company/{dot}/authorities`, `/company/{dot}/insurances`, `/company/{dot}/equipment`, `/company/{dot}/vehicles`
- Reports per endpoint: HTTP status, response time (ms), status classification (ok / slow / error)
- "Slow" threshold: > 2000ms
- Parses rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`
- Returns overall status: healthy (all ok), degraded (some slow or errored), down (all errored)
- Total execution time under 10 seconds

**Priority:** P0

### FR-03: TMS Record Export with Field Mapping

**Description:** The `tms_sync` tool in export mode fetches one carrier by DOT,
maps its fields to the selected TMS vocabulary, and returns a structured record
plus a mapping guide. The caller owns CSV/JSON serialization and import.

**Acceptance Criteria:**
- Supported formats: `generic`, `mcleod`, `tms_international`, `dat_power`
- Field mapping per format: SearchCarriers field name -> TMS column name
- Output includes pipeline source, timestamp, and version metadata
- Handles missing fields gracefully (empty cell, not error)

**Priority:** P1

### FR-04: TMS Import Translation

**Description:** The `tms_sync` tool in import mode accepts one structured TMS
record and reverse-maps known fields into the SearchCarriers vocabulary. This is
a translation step, not a live comparison or TMS write.

**Acceptance Criteria:**
- Accepts a structured record in a supported TMS format
- Reverse field mapping: TMS column name -> SearchCarriers field
- Returns unmapped input fields explicitly
- Makes no API request in import mode
- Requires Enterprise tier

**Priority:** P2

### FR-05: Local Webhook Configuration CRUD

**Description:** The `webhook_manage` tool supports create, list, update, and
delete against a local JSON configuration. SearchCarriers does not currently
publish remote webhook CRUD routes.

**Acceptance Criteria:**
- `create`: accepts URL and event types; returns a local webhook ID
- `list`: returns configured records with ID, URL, and events
- `update`: accepts webhook ID and URL and/or events
- `delete`: accepts webhook ID, confirms deletion, returns success/failure
- URL validation: must begin with HTTP or HTTPS
- Does not transmit events or prove remote registration
- All actions require SMB tier

**Priority:** P1

### FR-06: Tier Gating

**Description:** Every tool checks the user's subscription tier before executing. SMB users can access `api_health`, `bulk_lookup`, and `webhook_manage`. Enterprise users can additionally access `tms_sync`. Insufficient tier returns a structured error with the required tier and upgrade URL.

**Acceptance Criteria:**
- `api_health` requires SMB tier
- `bulk_lookup` requires SMB tier
- `webhook_manage` requires SMB tier
- `tms_sync` requires Enterprise tier
- Tier check before any API calls
- Error: `{ "error": { "code": "TIER_INSUFFICIENT", "required": "enterprise", "current": "smb", "upgrade_url": "https://searchcarriers.com/pricing" } }`

**Priority:** P0

## MVP Scope

Current implemented scope:

- [x] `api_health` -- endpoint probing with response times and rate limit status
- [x] `bulk_lookup` -- bounded batch carrier lookups with per-record isolation
- [x] `webhook_manage` -- local configuration create, list, update, and delete
- [x] `tms_sync` -- one-record import translation and export field mapping
- [x] Tier gating on all four tools
- [x] Structured JSON output with pipeline metadata
- [x] Structured API errors

Deferred to v0.2.0:

- Live TMS reconciliation, approved writes, reread, and rollback
- Remote webhook registration and delivery receipts
- CSV/file serialization owned by a dedicated export workflow
- Configurable progress reporting intervals
- Batch size auto-tuning based on rate limit headroom

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|-------------|
| Bulk lookup throughput (100 DOTs, basic) | Target: < 45 seconds | Timer across batch with rate limiting |
| Bulk lookup throughput (100 DOTs, standard) | Target: < 90 seconds | Timer across batch with rate limiting |
| API health check latency | Target: < 10 seconds | Timer across 5 endpoint probes |
| Local webhook CRUD latency | Target: < 2 seconds per operation | Timer per local operation |
| TMS export accuracy | Target: 100% field mapping correctness | Integration test against known carrier data |
| Error isolation rate | Target: 100% (one failed DOT never aborts the batch) | Unit tests with mixed success/failure inputs |
| Tier gate accuracy | Target: 100% | Integration tests |

## Dependencies

- **SearchCarriers REST API v1** -- all tools depend on API availability at `https://searchcarriers.com/api/v1`
- **Local filesystem** -- `webhook_manage` stores routing configuration under the user's home directory
- **Valid API key** -- `SEARCHCARRIERS_API_KEY` environment variable with SMB or Enterprise tier permissions
- **MCP protocol** -- plugin runs as an MCP server; requires Grok Build, Claude Code, or another MCP-capable client
- **httpx** -- async HTTP client for API calls
- **No dependency on other plugins** -- API Bridge is a standalone integration plugin. It can consume output from Carrier Intel (e.g., passing carrier_profile data to tms_sync), but does not require any other plugin to function.
