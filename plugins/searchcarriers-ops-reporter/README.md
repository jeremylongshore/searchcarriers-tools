# searchcarriers-ops-reporter

**OUTPUT stage** of the SearchCarriers stackable pipeline.

```
Carrier Intel (INPUT) → Risk Engine (ANALYSIS) → Ops Reporter (OUTPUT)
```

Transforms raw carrier data and risk assessments into professional reports, side-by-side comparisons, and structured exports that freight professionals can use for vetting decisions, load tendering, and compliance documentation.

## Quick Start

```bash
# 1. Set API key
export SEARCHCARRIERS_API_KEY="your_id|your_token"

# 2. Install dependencies
pip install -r plugins/searchcarriers-ops-reporter/scripts/requirements.txt

# 3. Start MCP server
python3 plugins/searchcarriers-ops-reporter/scripts/ops_reporter_mcp.py
```

## Tools

| Tool | Description | Min Tier |
|------|-------------|----------|
| `generate_report` | Comprehensive vetting report with safety, insurance, authority, risk assessment | Pro |
| `generate_fleet` | Fleet analysis with equipment roster and fleet-to-driver ratios | Pro |
| `generate_compare` | Side-by-side comparison of 2-5 carriers | Pro |
| `export_data` | Export carrier data in JSON, CSV, or Markdown | Pro |

## Slash Commands

| Command | Description |
|---------|-------------|
| `/sc-report <DOT>` | Generate a full vetting report |
| `/sc-compare <DOT1> <DOT2> [...]` | Compare carriers side-by-side |

## Full Pipeline Example

```
/sc-lookup 12345          → Carrier Intel: get carrier data
/sc-risk 12345            → Risk Engine: assess risk (score: 38, medium)
/sc-report 12345          → Ops Reporter: generate vetting report
/sc-compare 12345 67890   → Ops Reporter: compare two carriers
```

## Report Output

Reports are generated in Markdown by default with professional formatting:
- Company overview with legal name, address, contact
- Operating status and authority details
- Safety summary with OOS rates and crash data
- Insurance coverage table with active policies
- Risk assessment with factor breakdown
- Recommendation: Approved / Conditional / Declined

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
