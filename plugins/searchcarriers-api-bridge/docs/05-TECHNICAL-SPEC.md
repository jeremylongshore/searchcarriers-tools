# API Bridge - Technical Specification

## Tech Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Runtime | Python | 3.10+ | MCP server runtime |
| Protocol | MCP (Model Context Protocol) | 1.0+ | Tool registration and invocation |
| HTTP client | httpx | 0.27+ | Async HTTP requests to SearchCarriers API |
| Validation | pydantic | 2.0+ | Request/response schema validation |
| Testing | pytest | 8.0+ | Unit and integration tests |

## Dependencies

```
httpx>=0.27
mcp>=1.0
```

Specified in `scripts/requirements.txt`. Pydantic recommended for v0.2 response validation but not required for MVP.

## File Structure

```
searchcarriers-api-bridge/
├── .claude-plugin/
│   └── plugin.json                    # Plugin manifest (name, tools, tiers, version)
├── .mcp.json                          # MCP server configuration (command, args, env)
├── docs/                              # 6-doc enterprise documentation set
│   ├── 01-BUSINESS-CASE.md
│   ├── 02-PRD.md
│   ├── 03-ARCHITECTURE.md
│   ├── 04-USER-JOURNEY.md
│   ├── 05-TECHNICAL-SPEC.md           # (this file)
│   └── 06-STATUS.md
├── commands/                          # Slash command definitions (planned)
├── agents/                            # Agent definitions (planned)
├── skills/
│   └── searchcarriers-api-bridge/
│       └── SKILL.md                   # Embedded skill for Claude (planned)
├── scripts/
│   ├── api_bridge_mcp.py             # MCP server implementation
│   ├── batch.py                       # Batch processing engine (planned)
│   ├── rate_limiter.py                # Token bucket rate limiter (planned)
│   ├── health.py                      # API health check module (planned)
│   ├── tms_mapper.py                  # TMS field mapping engine (planned)
│   ├── webhooks.py                    # Webhook CRUD client (planned)
│   └── requirements.txt               # Python dependencies
└── README.md                          # Quick start guide (planned)
```

## API Endpoints

### Used by api_health

| Endpoint | Method | Purpose | Notes |
|----------|--------|---------|-------|
| `/api/v3/search` | GET | Probe current search contract | Uses one known DOT and `perPage=1` |
| `/api/v3/company/{dot}` | GET | Probe field-selected company response | Requests a bounded field set |
| `/api/v3/company/{dot}/equipment` | GET | Probe current equipment route | Uses one known DOT |
| `/api/v2/company/{dot}/qualification-reports` | GET | Probe qualification reports | Uses one known DOT |
| `/api/v1/company/watch` | GET | Probe watch-list compatibility | Treats plan/resource responses structurally |

### Used by bulk_lookup

| Section Level | Endpoints per DOT | Total for 100 DOTs |
|--------------|-------------------|-------------------|
| `basic` | `/search?dotNumber={dot}` (1 call) | 100 calls |
| `standard` | `/search` + `/company/{dot}/authorities` (2 calls) | 200 calls |
| `full` | `/search` + `/authorities` + `/insurances` (3 calls) | 300 calls |

### Used by tms_sync

| Action | Endpoint | Purpose |
|--------|----------|---------|
| `export` | None (pure formatting) | Formats existing carrier data for TMS import |
| `import` | `/api/v3/search?dotNumber={dot}` per carrier | Fetches live data to compare against TMS data |

### Used by webhook_manage

| Action | Endpoint | Method | Notes |
|--------|----------|--------|-------|
| `create` | Local configuration | File write | Creates a downstream webhook record |
| `list` | Local configuration | File read | Lists locally configured webhooks |
| `update` | Local configuration | File write | Updates a local webhook record |
| `delete` | Local configuration | File write | Removes a local webhook record |

**API origin:** `https://searchcarriers.com`; the health probe selects the
documented v3, v2, or v1 route for each capability.

**Authentication:** All requests include `Authorization: Bearer {SEARCHCARRIERS_API_KEY}` header.

**Rate Limit Headers:** Responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `Retry-After` (when rate limited). The rate limiter module parses these to stay within budget.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SEARCHCARRIERS_API_KEY` | Yes | -- | Bearer token for API authentication. Format: `{id}\|{token}` (Laravel Sanctum). Get from https://searchcarriers.com/settings/api-tokens |
| `SEARCHCARRIERS_API_BASE` | No | `https://searchcarriers.com` | API origin override (for testing against staging) |
| `SEARCHCARRIERS_TIMEOUT` | No | `10` | HTTP request timeout in seconds per individual request |
| `SEARCHCARRIERS_MAX_RETRIES` | No | `3` | Maximum retry attempts for transient failures (429, 504) |
| `SEARCHCARRIERS_BATCH_CONCURRENCY` | No | `3` | Max concurrent API requests during bulk operations |
| `SEARCHCARRIERS_LOG_LEVEL` | No | `WARNING` | Logging level: DEBUG, INFO, WARNING, ERROR |

## MCP Tool Schemas

### api_health

**Input:**
```json
{
  "include_rate_limits": "boolean (optional, default true) - Include rate limit info in response"
}
```

**Output:**
```json
{
  "meta": {
    "tool": "api_health",
    "timestamp": "2026-02-26T08:15:03Z",
    "tier": "enterprise"
  },
  "endpoints": [
    {
      "path": "/search",
      "status": "ok",
      "response_time_ms": 312,
      "http_status": 200
    },
    {
      "path": "/company/{dot}/authorities",
      "status": "ok",
      "response_time_ms": 287,
      "http_status": 200
    },
    {
      "path": "/company/{dot}/insurances",
      "status": "slow",
      "response_time_ms": 2876,
      "http_status": 200
    },
    {
      "path": "/company/{dot}/equipment",
      "status": "ok",
      "response_time_ms": 298,
      "http_status": 200
    },
    {
      "path": "/company/{dot}/vehicles",
      "status": "ok",
      "response_time_ms": 256,
      "http_status": 200
    }
  ],
  "rate_limits": {
    "limit": 180,
    "remaining": 175,
    "reset_seconds": 42
  },
  "overall_status": "degraded",
  "average_response_time_ms": 606
}
```

**Status classification:**
- `ok`: response time < 2000ms and HTTP 2xx
- `slow`: response time >= 2000ms and HTTP 2xx
- `error`: HTTP non-2xx or connection failure

**Overall status:**
- `healthy`: all endpoints `ok`
- `degraded`: any endpoint `slow` or `error`, but not all `error`
- `down`: all endpoints `error`

### bulk_lookup

**Input:**
```json
{
  "dot_numbers": ["string (required) - list of DOT numbers, max 100"],
  "sections": "string (optional, default 'standard') - basic | standard | full"
}
```

**Output:**
```json
{
  "meta": {
    "tool": "bulk_lookup",
    "timestamp": "2026-02-26T08:18:45Z",
    "total": 50,
    "succeeded": 48,
    "failed": 2,
    "sections": "standard",
    "duration_seconds": 36.4,
    "api_calls": 100,
    "tier": "enterprise"
  },
  "results": [
    {
      "dot_number": "69494",
      "carrier": {
        "legal_name": "WERNER ENTERPRISES INC",
        "dot_number": "69494",
        "status_code": "A",
        "safety_rating": "S",
        "power_units": 7880,
        "total_drivers": "12525",
        "phy_city": "OMAHA",
        "phy_state": "NE"
      },
      "authorities": [
        {
          "docket_number": "MC-14983",
          "common_authority_status": "A",
          "contract_authority_status": "A",
          "broker_authority_status": "A"
        }
      ]
    }
  ],
  "errors": [
    {
      "dot_number": "9012345",
      "error_code": "NOT_FOUND",
      "message": "No carrier found for DOT 9012345",
      "http_status": 404
    }
  ]
}
```

### tms_sync

**Input:**
```json
{
  "action": "string (required) - export | import",
  "carrier_data": "array (required for export) - carrier data from bulk_lookup or carrier_profile",
  "format": "string (required) - mcleod | tmw | generic_csv | json",
  "tms_data": "string (required for import) - CSV or JSON content from TMS export"
}
```

**Output (export):**
```json
{
  "meta": {
    "tool": "tms_sync",
    "action": "export",
    "timestamp": "2026-02-26T08:22:41Z",
    "format": "mcleod",
    "carrier_count": 48,
    "tier": "enterprise"
  },
  "content": "CarrierName,DOTNumber,MCNumber,...\n\"WERNER ENTERPRISES INC\",69494,...",
  "content_type": "text/csv",
  "column_count": 15,
  "row_count": 48
}
```

**Output (import -- diff report):**
```json
{
  "meta": {
    "tool": "tms_sync",
    "action": "import",
    "timestamp": "2026-02-26T08:30:00Z",
    "format": "mcleod",
    "carriers_compared": 48,
    "carriers_changed": 5,
    "tier": "enterprise"
  },
  "changes": [
    {
      "dot_number": "3456789",
      "legal_name": "COLD STAR LOGISTICS LLC",
      "fields_changed": [
        {
          "field": "status_code",
          "tms_value": "Active",
          "live_value": "Inactive",
          "critical": true
        },
        {
          "field": "power_units",
          "tms_value": "12",
          "live_value": "8",
          "critical": false
        }
      ]
    }
  ],
  "unchanged": 43,
  "not_found": 0,
  "critical_changes": 1
}
```

### webhook_manage

**Input:**
```json
{
  "action": "string (required) - create | list | update | delete",
  "url": "string (required for create/update) - HTTPS webhook endpoint URL",
  "events": ["string (required for create, optional for update) - event types"],
  "secret": "string (optional for create) - HMAC signing secret",
  "webhook_id": "string (required for update/delete) - webhook identifier",
  "active": "boolean (optional for update) - enable/disable webhook"
}
```

**Output (create):**
```json
{
  "meta": {
    "tool": "webhook_manage",
    "action": "create",
    "timestamp": "2026-02-26T08:25:12Z",
    "tier": "smb"
  },
  "webhook": {
    "id": "wh_8f3a2b1c",
    "url": "https://hooks.example.com/carriers",
    "events": ["authority_change", "insurance_change"],
    "status": "active",
    "created_at": "2026-02-26T08:25:12Z"
  }
}
```

**Output (list):**
```json
{
  "meta": {
    "tool": "webhook_manage",
    "action": "list",
    "timestamp": "2026-02-26T08:30:00Z",
    "tier": "smb"
  },
  "webhooks": [
    {
      "id": "wh_8f3a2b1c",
      "url": "https://hooks.example.com/carriers",
      "events": ["authority_change", "insurance_change"],
      "status": "active",
      "created_at": "2026-02-26T08:25:12Z"
    }
  ],
  "total": 1
}
```

**Known event types:**
- `authority_change` -- broker, common, or contract authority status changed
- `insurance_change` -- insurance policy added, removed, or coverage changed
- `safety_rating_change` -- safety rating upgraded or downgraded
- `status_change` -- carrier operating status changed (active/inactive)
- `mcs150_update` -- MCS-150 filing updated
- `oos_order` -- out-of-service order issued or lifted

## Tier Gating Implementation

```python
TIER_ORDER = ["free", "basic", "pro", "proplus", "smb", "enterprise"]

TOOL_TIERS = {
    "api_health": "smb",
    "bulk_lookup": "smb",
    "webhook_manage": "smb",
    "tms_sync": "enterprise",
}


def check_tier(tool_name: str, user_tier: str) -> bool:
    """Return True if user_tier is sufficient for tool_name."""
    required = TOOL_TIERS[tool_name]
    return TIER_ORDER.index(user_tier) >= TIER_ORDER.index(required)
```

Tier is determined from the API key validation response. If the API returns 403 on any endpoint, the MCP server surfaces the upgrade message. The tier check happens before any data-fetching API calls.

## Batch Processing Strategy

### Token Bucket Rate Limiter

```python
class TokenBucket:
    """Rate limiter for SearchCarriers API (3 req/s recommended)."""

    def __init__(self, rate: float = 3.0, capacity: int = 3):
        self.rate = rate  # tokens per second
        self.capacity = capacity  # max burst
        self.tokens = capacity
        self.last_refill = time.monotonic()

    async def acquire(self):
        """Wait until a token is available, then consume it."""
        while self.tokens < 1:
            self._refill()
            if self.tokens < 1:
                await asyncio.sleep(1.0 / self.rate)
        self._refill()
        self.tokens -= 1

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now
```

The rate limiter is shared across all tools in a single MCP server session. If `api_health` consumes 5 tokens and `bulk_lookup` starts immediately after, the bulk processor waits for tokens to refill.

### Batch Execution Loop

```python
async def execute_batch(dot_numbers: list[str], sections: str, rate_limiter: TokenBucket):
    results = []
    errors = []

    for i, dot in enumerate(dot_numbers):
        try:
            carrier_data = await fetch_carrier(dot, sections, rate_limiter)
            results.append(carrier_data)
        except CarrierNotFoundError as e:
            errors.append({"dot_number": dot, "error_code": "NOT_FOUND", "message": str(e)})
        except APIError as e:
            errors.append({"dot_number": dot, "error_code": e.code, "message": str(e)})

        # Progress callback every 10 carriers or on completion
        if (i + 1) % 10 == 0 or i == len(dot_numbers) - 1:
            report_progress(i + 1, len(dot_numbers), len(errors))

    return {"results": results, "errors": errors}
```

Error isolation is per-DOT. Each DOT's API calls are wrapped in try/catch. A 404 on DOT #23 does not affect DOT #24. The final response includes both the successful results and the error log.

## TMS Format Specifications

### McLeod LoadMaster CSV

```python
MCLEOD_MAPPING = {
    "legal_name": "CarrierName",
    "dot_number": "DOTNumber",
    "mc_mx_ff_numbers": "MCNumber",
    "phy_street": "Address1",
    "phy_city": "City",
    "phy_state": "State",
    "phy_zip": "Zip",
    "phone": "Phone",
    "status_code": "Status",  # A -> Active, I -> Inactive
    "safety_rating": "SafetyRating",  # S -> Satisfactory, C -> Conditional, U -> Unsatisfactory
    "power_units": "PowerUnits",
    "total_drivers": "TotalDrivers",
    "common_authority_status": "CommonAuthority",
    "contract_authority_status": "ContractAuthority",
    "broker_authority_status": "BrokerAuthority",
}

MCLEOD_DATE_FORMAT = "%m/%d/%Y"  # MM/DD/YYYY

MCLEOD_STATUS_MAP = {
    "A": "Active",
    "I": "Inactive",
    "N": "Not Authorized",
}
```

### TMW Suite CSV

```python
TMW_MAPPING = {
    "legal_name": "carrier_name",
    "dot_number": "dot_num",
    "mc_mx_ff_numbers": "mc_number",
    "phy_street": "addr_line1",
    "phy_city": "city",
    "phy_state": "state",
    "phy_zip": "zip",
    "phone": "phone_num",
    "status_code": "status",
    "safety_rating": "safety_rtg",
    "power_units": "pwr_units",
    "total_drivers": "drivers",
}

TMW_DATE_FORMAT = "%Y%m%d"  # YYYYMMDD
```

### Generic CSV

Uses SearchCarriers field names directly. No field mapping. Dates in ISO 8601 format. Status codes as-is. This format works with any TMS that supports CSV import with manual column mapping.

## Testing Strategy

### Unit Tests (mock API)

Mock all HTTP responses using `httpx.MockTransport` or `respx`. Test:

- **api_health**: Verify 5 endpoints probed, response times measured, status classification correct, rate limit headers parsed
- **bulk_lookup**: Verify batch processing, error isolation (one failed DOT does not abort), progress reporting at correct intervals, rate limiting enforced
- **tms_sync export**: Verify field mapping for each TMS format, date conversion, status translation, CSV header generation, handling of missing fields
- **tms_sync import**: Verify reverse mapping, live data fetch, diff report generation, critical change flagging
- **webhook_manage**: Verify CRUD actions, URL validation (HTTPS required), event type validation
- **Tier gating**: Verify SMB user cannot access tms_sync, Enterprise user can access all tools, Free user cannot access any tools
- **Rate limiter**: Verify token bucket behavior, burst handling, wait times

### Integration Tests (real API)

Marked with `@pytest.mark.integration`. Require a valid `SEARCHCARRIERS_API_KEY`:

- **api_health**: All 5 endpoints return 200, response times are populated
- **bulk_lookup**: 5 DOTs with basic sections returns results, Werner (69494) always succeeds
- **webhook_manage list**: Returns current webhook configuration without error
- **Latency**: api_health < 10s, bulk_lookup (5 DOTs, basic) < 10s

Integration tests excluded from CI. Run locally:

```bash
SEARCHCARRIERS_API_KEY="your_key" pytest -v -m integration
```

### Batch Processing Tests

Synthetic tests with mock API to verify batch behavior at scale:

- **100 DOTs, all succeed**: Verify all results returned, progress reported 10 times
- **100 DOTs, 10 fail**: Verify 90 results + 10 errors, batch not aborted
- **100 DOTs, rate limited mid-batch**: Verify pause and resume, 429 handled gracefully
- **100 DOTs, API timeout on 5**: Verify retry logic, 5 errors after max retries
- **0 DOTs**: Verify empty input handled, no API calls made
- **101 DOTs**: Verify rejection with "max 100" error message

### TMS Mapping Tests

Test field mapping accuracy for each supported TMS format:

- **McLeod export**: Known carrier data -> expected McLeod CSV columns and values
- **TMW export**: Known carrier data -> expected TMW CSV columns and values
- **Generic CSV**: Known carrier data -> SearchCarriers field names as headers
- **Date conversion**: ISO 8601 -> McLeod MM/DD/YYYY, TMW YYYYMMDD
- **Status translation**: "A" -> "Active" (McLeod), "A" -> "A" (generic)
- **Missing fields**: Carrier with null phone -> empty cell, not error

## Deployment

> **Multi-client path:** From the repository root, run `./scripts/setup-dev.sh`,
> export `SEARCHCARRIERS_API_KEY`, and let Grok Build, Claude Code, or another
> MCP client load the root `.mcp.json`. The client-specific copy steps below
> describe optional Claude plugin packaging. See
> [`MODEL-COMPATIBILITY.md`](../../../MODEL-COMPATIBILITY.md).

### Installation

1. Copy the plugin directory:

```bash
cp -r plugins/searchcarriers-api-bridge/ ~/.claude/plugins/searchcarriers-api-bridge/
```

2. Or add the MCP server configuration to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "searchcarriers-api-bridge": {
      "command": "python3",
      "args": ["plugins/searchcarriers-api-bridge/scripts/api_bridge_mcp.py"],
      "env": {
        "SEARCHCARRIERS_API_KEY": "${SEARCHCARRIERS_API_KEY}"
      }
    }
  }
}
```

3. Set your API key:

```bash
export SEARCHCARRIERS_API_KEY="your_id|your_token"
```

4. Restart Claude Code. The MCP server registers four tools: `api_health`, `bulk_lookup`, `tms_sync`, `webhook_manage`.

5. Verify:

```
Check SearchCarriers API health
```

If configured correctly, this will probe all API endpoints and return health status. If the API key is missing, invalid, or has insufficient tier, you will see a clear error message with setup instructions.

## Performance Benchmarks

| Operation | Target p50 | Target p95 | Target p99 | Bottleneck |
|-----------|-----------|-----------|-----------|-----------|
| `api_health` | 2s | 5s | 8s | 5 sequential API probes |
| `bulk_lookup` (10 DOTs, basic) | 4s | 6s | 10s | 10 API calls, rate-limited |
| `bulk_lookup` (50 DOTs, basic) | 18s | 25s | 35s | 50 API calls, rate-limited |
| `bulk_lookup` (100 DOTs, basic) | 35s | 45s | 55s | 100 API calls, rate-limited |
| `bulk_lookup` (100 DOTs, standard) | 68s | 85s | 100s | 200 API calls, rate-limited |
| `bulk_lookup` (100 DOTs, full) | 100s | 120s | 150s | 300 API calls, rate-limited |
| `tms_sync` export (50 carriers) | 50ms | 150ms | 300ms | String formatting only |
| `tms_sync` import (50 carriers) | 18s | 25s | 35s | 50 API calls + comparison |
| `webhook_manage` (any CRUD) | 300ms | 800ms | 1.5s | Single API call |
| MCP server cold start | 500ms | 1s | 2s | Python import + env validation |
| Tier check | <1ms | <1ms | <1ms | In-memory lookup |

Primary bottleneck is the SearchCarriers API rate limit (3 req/s). Bulk operations scale linearly: estimated_seconds = total_api_calls / 3. TMS export is pure formatting with no I/O -- it is the fastest operation in the plugin.
