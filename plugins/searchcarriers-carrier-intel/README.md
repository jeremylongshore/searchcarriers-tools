# searchcarriers-carrier-intel

**Stackable Pipeline: INPUT Stage** | Min Tier: Free

Carrier lookup, profile aggregation, entity mapping, and fleet summary from SearchCarriers' 4M+ company database. This is the data retrieval layer — it feeds structured carrier data into the Risk Engine (ANALYSIS) and Ops Reporter (OUTPUT) stages.

## Quick Start

```bash
# Set your API key
export SEARCHCARRIERS_API_KEY="your_id|your_token"

# Try a lookup
/sc-lookup Werner Enterprises

# Get a full profile
/sc-profile 69494
```

## MCP Tools

| Tool | Min Tier | Description |
|------|----------|-------------|
| `carrier_lookup` | Free | Search by DOT, MC, name, VIN, SCAC, or location |
| `carrier_profile` | Free | Combined carrier data + authorities + insurance |
| `entity_map` | Pro | Find related companies via shared equipment VINs |
| `fleet_summary` | Free | Equipment roster + vehicle list with summary stats |

## Commands

| Command | Description |
|---------|-------------|
| `/sc-lookup [query]` | Search for carriers by any identifier |
| `/sc-profile [DOT]` | Full carrier profile with all available data |

## Pipeline Output

Each tool returns structured JSON designed to feed directly into downstream plugins:

```
carrier_lookup  -->  { carriers: [...], pagination: {...} }
carrier_profile -->  { carrier: {...}, authorities: [...], insurances: [...] }
entity_map      -->  { seed_carrier: {...}, related_carriers: [...] }
fleet_summary   -->  { equipment: [...], vehicles: [...], summary: {...} }
```

The Risk Engine consumes these outputs for scoring. The Ops Reporter formats them into reports.

## API Endpoints Used

| Endpoint | Method | Used By |
|----------|--------|---------|
| `/api/v3/search` | GET | carrier_lookup |
| `/api/v3/company/{dot}?fields=...` | GET | carrier_profile, entity_map |
| `/api/v3/company/{dot}/equipment` | GET | entity_map, fleet_summary |
| `/api/v1/search/by-vin/{vin}` | GET | entity_map |
| `/api/v1/search/scac` | GET | carrier_lookup |

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `SEARCHCARRIERS_API_KEY` | Yes | API bearer token from searchcarriers.com/settings/api-tokens |

## Docs

Full enterprise documentation in `docs/`:
- [Business Case](docs/01-BUSINESS-CASE.md)
- [PRD](docs/02-PRD.md)
- [Architecture](docs/03-ARCHITECTURE.md)
- [User Journey](docs/04-USER-JOURNEY.md)
- [Technical Spec](docs/05-TECHNICAL-SPEC.md)
- [Status](docs/06-STATUS.md)
