# searchcarriers-api-bridge

**STANDALONE integration plugin** for API management, bulk operations, and TMS sync.

```
                    ┌──────────────────┐
                    │    API Bridge    │
                    │  (INTEGRATION)   │
                    │                  │
                    │  api_health      │
                    │  bulk_lookup     │
                    │  tms_sync        │
                    │  webhook_manage  │
                    │                  │
                    │  Min: SMB        │
                    └──────────────────┘
```

Provides programmatic access to bulk carrier operations, API health monitoring, TMS data synchronization, and webhook management for larger organizations.

## Quick Start

```bash
# 1. Set API key
export SEARCHCARRIERS_API_KEY="your_id|your_token"

# 2. Install dependencies
pip install -r plugins/searchcarriers-api-bridge/scripts/requirements.txt

# 3. Start MCP server
python3 plugins/searchcarriers-api-bridge/scripts/api_bridge_mcp.py
```

## Tools

| Tool | Description | Min Tier |
|------|-------------|----------|
| `api_health` | API endpoint status, response times, rate limits | SMB |
| `bulk_lookup` | Batch carrier lookups (up to 100 DOTs) | SMB |
| `tms_sync` | Export/import carrier data in TMS-compatible formats | Enterprise |
| `webhook_manage` | CRUD for Carrier Watch webhook endpoints | SMB |

## Slash Commands

| Command | Description |
|---------|-------------|
| `/sc-api` | Check API health and rate limits |
| `/sc-bulk <DOT1> <DOT2> ...` | Batch carrier lookups |

## Bulk Processing

Process up to 100 carriers per batch with rate-limited sequential execution:
- Token bucket rate limiter (3 requests/second)
- Automatic rate limit respect
- Per-carrier error isolation (one failure doesn't block others)
- Configurable data sections (basics, authorities, insurances, equipment)

## TMS Formats

| Format | Description |
|--------|-------------|
| `generic` | Standard field mapping for any TMS |
| `mcleod` | McLeod LoadMaster field mapping |
| `tms_international` | TMW/TMS International field mapping |
| `dat_power` | DAT Power field mapping |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SEARCHCARRIERS_API_KEY` | Yes | API authentication token |
| `SEARCHCARRIERS_TIER` | No | User subscription tier (default: free) |

## Documentation

See `docs/` for enterprise documentation:
- [Business Case](docs/01-BUSINESS-CASE.md)
- [PRD](docs/02-PRD.md)
- [Architecture](docs/03-ARCHITECTURE.md)
- [User Journey](docs/04-USER-JOURNEY.md)
- [Technical Spec](docs/05-TECHNICAL-SPEC.md)
- [Status](docs/06-STATUS.md)
