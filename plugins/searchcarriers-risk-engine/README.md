# searchcarriers-risk-engine

**ANALYSIS stage** of the SearchCarriers stackable pipeline.

```
Carrier Intel (INPUT) → Risk Engine (ANALYSIS) → Ops Reporter (OUTPUT)
```

Consumes carrier data from Carrier Intel or the API and produces advisory risk
evidence, named qualification reports, caller-policy verdicts, insurance
reconciliation, and compliance snapshots.

## Quick Start

```bash
# 1. Set API key
export SEARCHCARRIERS_API_KEY="your_id|your_token"

# 2. Install dependencies
pip install -r plugins/searchcarriers-risk-engine/scripts/requirements.txt

# 3. Start MCP server
python3 plugins/searchcarriers-risk-engine/scripts/risk_engine_mcp.py
```

## Tools

| Tool | Description | Min Tier |
|------|-------------|----------|
| `risk_score` | Disclosed legacy advisory model; never an official safety rating | Pro |
| `qualification_reports` | Upstream named personal/team qualifications with Pass/Review/Fail evidence | Pro+ |
| `vetting_check` | Carrier qualification against a complete caller-supplied policy; no hidden thresholds | Pro+ |
| `insurance_check` | Insurance coverage analysis with gap detection and lapse warnings | Pro |
| `compliance_audit` | MCS-150 filing, authority status, and regulatory compliance audit | Pro |

## Slash Commands

| Command | Description |
|---------|-------------|
| `/sc-risk <DOT>` | Calculate risk score for a carrier |
| `/sc-vet <DOT>` | Run vetting check with qualification rules |

## Legacy advisory score ranges

These bands belong to this client's legacy model. They are not FMCSA ratings,
SearchCarriers qualifications, or a substitute for a named company policy.

| Score | Level | Meaning |
|-------|-------|---------|
| 0-25 | Low | Minimal risk indicators |
| 26-50 | Medium | Some concerns, review recommended |
| 51-75 | Elevated | Significant risk factors present |
| 76-100 | High | Critical issues, investigation required |

## Pipeline Output

All tools include a `_pipeline` envelope for downstream consumption by Ops Reporter:

```json
{
  "_pipeline": {
    "source": "risk-engine",
    "tool": "risk_score",
    "version": "0.3.0",
    "dot_number": "12345",
    "timestamp": "2026-02-26T10:00:00Z"
  },
  "risk_score": 42,
  "risk_level": "medium",
  "factors": [...]
}
```

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
