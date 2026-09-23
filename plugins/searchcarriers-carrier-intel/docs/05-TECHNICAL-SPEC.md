# Carrier Intel - Technical Specification

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

Runtime dependencies are declared in `scripts/requirements.txt`; repository development dependencies are declared in `pyproject.toml`. The current response-contract layer uses explicit Python normalization helpers, while MCP supplies the tool schemas.

## File Structure

```
searchcarriers-carrier-intel/
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
├── commands/                          # Slash command definitions
│   ├── sc-lookup.md                   # /sc-lookup → carrier_lookup
│   └── sc-profile.md                  # /sc-profile → carrier_profile
├── agents/
│   └── carrier-analyst.md             # Autonomous carrier analysis agent
├── skills/
│   └── searchcarriers-carrier-intel/
│       └── SKILL.md                   # Embedded skill for Claude
├── scripts/
│   ├── carrier_intel_mcp.py           # MCP server implementation
│   └── requirements.txt               # Python dependencies
└── README.md                          # Quick start guide
```

## API Endpoints

| Tool | Endpoint | Method | Parameters | Min Tier | Notes |
|------|----------|--------|-----------|----------|-------|
| `carrier_lookup` | `/api/v3/search` plus dedicated v1 SCAC/VIN routes | GET | `superSearchTerm`, `dotNumber`, `docketNumber`, `addressState`, `addressCity`, `zipCode`, `perPage`, `page` | Free | Auto-detects search type and maps the MCP input to the current API contract |
| `carrier_profile` | `/api/v3/company/{dot}` | GET | `fields` | Free | Field-selected company response |
| `entity_map` | `/api/v3/company/{dot}/equipment` plus `/api/v1/search/by-vin/{vin}` | GET | v3 filters and VIN path | Pro | Per-VIN relationship search |
| `fleet_summary` | `/api/v3/company/{dot}/equipment` | GET | v3 filters | Free | Current equipment roster |

**API origin:** `https://searchcarriers.com`; each capability selects its
documented API version.

**Authentication:** All requests include `Authorization: Bearer {SEARCHCARRIERS_API_KEY}` header.

**Pagination:** Search endpoint uses Laravel pagination with `perPage` (default 10, max 100) and `page` parameters. Total results capped at 1,000. Company detail endpoints (authorities, insurances, equipment, vehicles) return all records for the given DOT.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SEARCHCARRIERS_API_KEY` | Yes | -- | Bearer token for API authentication. Format: `{id}\|{token}` (Laravel Sanctum). Get from https://searchcarriers.com/settings/api-tokens |
| `SEARCHCARRIERS_API_BASE` | No | `https://searchcarriers.com` | API origin override (for testing against staging) |
| `SEARCHCARRIERS_TIMEOUT` | No | `10` | HTTP request timeout in seconds |
| `SEARCHCARRIERS_MAX_RETRIES` | No | `3` | Maximum retry attempts for transient failures (429, 504) |
| `SEARCHCARRIERS_LOG_LEVEL` | No | `WARNING` | Logging level: DEBUG, INFO, WARNING, ERROR |

## MCP Tool Schemas

### carrier_lookup

**Input:**
```json
{
  "search_term": "string (required) - DOT, MC, name, VIN, or general search",
  "state": "string (optional) - Two-letter state filter (e.g., 'NE')",
  "city": "string (optional) - City filter",
  "zip_code": "string (optional) - ZIP code filter",
  "per_page": "integer (optional, default 10) - Results per page",
  "page": "integer (optional, default 1) - Page number"
}
```

**Output:**
```json
{
  "meta": {
    "tool": "carrier_lookup",
    "timestamp": "2026-02-26T14:30:00Z",
    "search_term": "Werner Enterprises",
    "search_type": "superSearchTerm",
    "total_results": 3,
    "page": 1,
    "per_page": 10
  },
  "carriers": [
    {
      "dot_number": "69494",
      "legal_name": "WERNER ENTERPRISES INC",
      "dba_name": null,
      "status_code": "A",
      "phy_city": "OMAHA",
      "phy_state": "NE",
      "power_units": 7880,
      "total_drivers": "12525",
      "carrier_operation": "A",
      "safety_rating": "S",
      "docket_numbers": ["MC-14983"]
    }
  ]
}
```

### carrier_profile

**Input:**
```json
{
  "dot_number": "string (required) - DOT number of the carrier"
}
```

**Output:**
```json
{
  "meta": {
    "tool": "carrier_profile",
    "timestamp": "2026-02-26T14:30:00Z",
    "dot_number": "69494",
    "api_calls": 3
  },
  "carrier": { "...143-field carrier object..." },
  "authorities": [
    {
      "dot_number": "69494",
      "docket_number": "MC-14983",
      "broker_authority_status": "A",
      "contract_authority_status": "A",
      "common_authority_status": "A",
      "sub_types": {
        "passenger": false,
        "property": true,
        "household_goods": true
      },
      "status_since_date": "1981-01-27"
    }
  ],
  "insurances": [
    {
      "type": "BIPD",
      "coverage_amount": 5000000,
      "effective_date": "2025-06-01",
      "status": "Active"
    }
  ]
}
```

### entity_map

**Input:**
```json
{
  "dot_number": "string (required) - DOT number of the target carrier"
}
```

**Output:**
```json
{
  "meta": {
    "tool": "entity_map",
    "timestamp": "2026-02-26T14:30:00Z",
    "dot_number": "3891456",
    "vins_scanned": 8,
    "related_carriers_found": 1,
    "tier": "pro"
  },
  "target_carrier": {
    "dot_number": "3891456",
    "legal_name": "QUICK HAUL TRANSPORT LLC"
  },
  "equipment": [
    { "vin": "1FUJGHDV0CLBP8834", "make": "FREIGHTLINER", "year": "2012" }
  ],
  "relationships": [
    {
      "related_dot": "2987123",
      "related_name": "FAST FREIGHT SOLUTIONS INC",
      "related_status": "REVOKED",
      "shared_vins": ["1FUJGHDV0CLBP8834", "3AKJHHDR5KSKL9021"],
      "shared_vin_count": 2
    }
  ]
}
```

### fleet_summary

**Input:**
```json
{
  "dot_number": "string (required) - DOT number of the carrier"
}
```

**Output:**
```json
{
  "meta": {
    "tool": "fleet_summary",
    "timestamp": "2026-02-26T14:30:00Z",
    "dot_number": "27021",
    "equipment_count": 2156,
    "vehicle_count": 2156
  },
  "carrier": {
    "legal_name": "KLLM TRANSPORT SERVICES INC",
    "power_units": 2156,
    "total_drivers": "2489"
  },
  "equipment_by_type": {
    "Tractor": 987,
    "Reefer Trailer": 842,
    "Dry Van": 198,
    "Flatbed": 67,
    "Other": 62
  },
  "top_makes": {
    "FREIGHTLINER": 612,
    "KENWORTH": 298,
    "PETERBILT": 187,
    "VOLVO": 109,
    "INTERNATIONAL": 78
  },
  "equipment": [ "...detailed equipment records..." ],
  "vehicles": [ "...simplified vehicle list..." ]
}
```

## Tier Gating Implementation

```python
TIER_ORDER = ["free", "basic", "pro", "proplus", "smb", "enterprise"]

TOOL_TIERS = {
    "carrier_lookup": "free",
    "carrier_profile": "free",
    "entity_map": "pro",
    "fleet_summary": "free",
}


def check_tier(tool_name: str, user_tier: str) -> bool:
    """Return True if user_tier is sufficient for tool_name."""
    required = TOOL_TIERS[tool_name]
    return TIER_ORDER.index(user_tier) >= TIER_ORDER.index(required)
```

Tier is determined from the API key validation response. If the API returns a 403 on any endpoint, the MCP server surfaces the upgrade message. The tier check happens before any data-fetching API calls to avoid wasting rate-limited requests.

## Testing Strategy

### Unit Tests (mock API)

Mock all HTTP responses using `httpx.MockTransport` or `respx`. Test:

- **Search auto-detection**: Verify DOT input routes to `dotNumber`, MC input routes to `docketNumber`, name input routes to `superSearchTerm`, VIN input routes to `vin`
- **Profile aggregation**: Verify three API calls are made in sequence, response is combined correctly
- **Entity mapping**: Verify VIN extraction from equipment, per-VIN search execution, relationship mapping
- **Fleet summary**: Verify equipment and vehicle data are combined
- **Error handling**: Verify correct user messages for 401, 403, 404, 429, 504
- **Tier gating**: Verify Free user cannot access `entity_map`, Pro user can access all tools

### Integration Tests (real API)

Marked with `@pytest.mark.integration`. Require a valid `SEARCHCARRIERS_API_KEY`. Run against the live API:

- **carrier_lookup("Werner")** returns at least one result with DOT 69494
- **carrier_profile("69494")** returns carrier data, authorities, and insurances
- **fleet_summary("69494")** returns equipment and vehicles for Werner
- **Latency**: carrier_lookup < 3s, carrier_profile < 5s

Integration tests are excluded from CI by default (no API key in CI environment). Run locally with:

```bash
SEARCHCARRIERS_API_KEY="your_key" pytest -v -m integration
```

### Tier Gating Tests

Test the tier check logic without hitting the API:

- `check_tier("carrier_lookup", "free")` returns True
- `check_tier("entity_map", "free")` returns False
- `check_tier("entity_map", "pro")` returns True
- `check_tier("entity_map", "enterprise")` returns True

## Deployment

### Installation

1. Copy the `searchcarriers-carrier-intel/` directory into your Claude Code plugins location:

```bash
cp -r plugins/searchcarriers-carrier-intel/ ~/.claude/plugins/searchcarriers-carrier-intel/
```

2. Or add the MCP server configuration to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "searchcarriers-carrier-intel": {
      "command": "python3",
      "args": ["plugins/searchcarriers-carrier-intel/scripts/carrier_intel_mcp.py"],
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

4. Restart Claude Code. The MCP server starts automatically and registers four tools: `carrier_lookup`, `carrier_profile`, `entity_map`, `fleet_summary`.

5. Verify:

```
/sc-lookup test
```

If configured correctly, this will search for carriers matching "test" and return results. If the API key is missing or invalid, you will see a clear error message with setup instructions.

### Updating

Pull the latest version and copy the updated plugin directory:

```bash
git pull origin main
cp -r plugins/searchcarriers-carrier-intel/ ~/.claude/plugins/searchcarriers-carrier-intel/
```

Restart Claude Code to pick up changes. No database migrations, no config file changes -- the plugin is stateless.

## Performance Benchmarks

| Operation | Target p50 | Target p95 | Target p99 | Bottleneck |
|-----------|-----------|-----------|-----------|-----------|
| `carrier_lookup` (name) | 400ms | 800ms | 1.5s | Single API call + network latency |
| `carrier_lookup` (DOT) | 300ms | 600ms | 1.2s | Single API call, exact match faster |
| `carrier_profile` | 1.2s | 2.5s | 4.0s | 3 sequential API calls |
| `fleet_summary` | 800ms | 1.5s | 3.0s | 2 API calls (can be parallelized) |
| `entity_map` (10 VINs) | 4s | 8s | 12s | 11 API calls, rate-limited at 3/s |
| `entity_map` (50 VINs) | 18s | 25s | 35s | 51 API calls, rate-limited at 3/s |
| `entity_map` (100 VINs) | 35s | 45s | 55s | 101 API calls, rate-limited at 3/s |
| MCP server cold start | 500ms | 1s | 2s | Python import + env validation |
| Tier check | <1ms | <1ms | <1ms | In-memory lookup, no I/O |

Primary bottleneck is network round-trip time to the SearchCarriers API. Entity mapping is the only operation that scales linearly with fleet size due to per-VIN searches. A documented batch VIN endpoint would allow a future optimization.
