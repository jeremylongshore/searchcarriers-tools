# SearchCarriers Tools

**Evidence-driven motor carrier operations for Grok, Claude, and MCP clients.**

Search, source, qualify, monitor, and reconcile motor carriers directly from
your terminal. Five plugins, fourteen focused skills, and seven composed
workflows turn SearchCarriers API evidence into bounded operational decisions.

The tools are open source under Apache-2.0. They are an independent client for
the SearchCarriers service; API access and production data use still require an
appropriate [SearchCarriers](https://searchcarriers.com/lander) account and are
subject to its terms.

Built for freight brokers, safety teams, and logistics operations that need
sourceable evidence, visible unknowns, and a concrete next action.

---

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/U5S225PTME)

## Start Here

See the customer-facing capability map at
**[demos.intentsolutions.io/searchcarriers](https://demos.intentsolutions.io/searchcarriers/)**.
Every package also includes its own `docs/ONE-PAGER.md` and canonical
white-glove `docs/ONE-PAGER.pdf`, linked directly from that package's
`SKILL.md`.

Open Grok Build, Claude Code, or another MCP-capable client in this repo and say:

    Walk me through getting started with SearchCarriers

Or paste the repo URL into any LLM and ask it to help you set up.

The runtime is model-agnostic. Grok Build, Claude Code, and other MCP-capable
clients can invoke the same five provider-neutral MCP servers from the root
`.mcp.json`; the servers contain no model-provider SDK. See
**[MODEL-COMPATIBILITY.md](MODEL-COMPATIBILITY.md)** for the tested boundary and
the separate hosted Grok Bot deployment requirement.

---

## Quick Start

Up and running in under 2 minutes:

```bash
git clone https://github.com/jeremylongshore/searchcarriers-tools.git
cd searchcarriers-tools && ./scripts/setup-dev.sh
```

Set your API key:

```bash
export SEARCHCARRIERS_API_KEY="your_id|your_token"
```

Then choose a model client:

```bash
# Grok Build discovers the project .mcp.json automatically
grok inspect
grok mcp doctor searchcarriers-carrier-intel

# Claude Code also discovers the project .mcp.json
claude
```

Try your first lookup:

```
/sc-lookup JB Hunt
```

---

## Plugin Catalog

| Plugin | Type | Pipeline Stage | Min Tier | Description |
|--------|------|----------------|----------|-------------|
| `searchcarriers-carrier-intel` | Stackable (INPUT) | Data retrieval | Free | Carrier lookup, entity mapping, fleet summary, SCAC/VIN resolution |
| `searchcarriers-risk-engine` | Stackable (ANALYSIS) | Risk assessment | Pro | Risk scoring, vetting checks, insurance validation, compliance audit |
| `searchcarriers-ops-reporter` | Stackable (OUTPUT) | Reporting | Pro | Vetting reports, fleet reports, carrier comparisons, data export |
| `searchcarriers-watchdog` | Standalone | Monitoring | Pro+ | Carrier watch management, alert formatting, compliance drift detection |
| `searchcarriers-api-bridge` | Standalone | Integration | SMB | Bulk carrier operations, TMS sync, webhook management, API health checks |

---

## Stackable Pipeline

The three stackable plugins cover retrieval, analysis, and output. The caller
chooses when to pass evidence between stages and remains the decision owner.

```
                        STACKABLE PIPELINE
  ================================================================

  +-----------------------+     +------------------------+     +-------------------------+
  |   CARRIER INTEL       |     |   RISK ENGINE          |     |   OPS REPORTER          |
  |   (INPUT)             |---->|   (ANALYSIS)           |---->|   (OUTPUT)              |
  |                       |     |                        |     |                         |
  |   carrier_lookup      |     |   risk_score           |     |   generate_report       |
  |   carrier_profile     |     |   qualification_reports|     |   generate_fleet        |
  |   entity_map          |     |   vetting_check        |     |   generate_compare      |
  |   fleet_summary       |     |   insurance_check      |     |   export_data           |
  |                       |     |   compliance_audit     |     |                         |
  |                       |     |                        |     |                         |
  |   Min: Free           |     |   Min: Pro             |     |   Min: Pro              |
  +-----------------------+     +------------------------+     +-------------------------+

  Example: "/sc-lookup KLLM" --> carrier data --> risk assessment --> formatted vetting report
```

**Standalone plugins** operate independently:

```
  +------------------------+     +-------------------------+
  |   WATCHDOG             |     |   API BRIDGE            |
  |   (MONITORING)         |     |   (INTEGRATION)         |
  |                        |     |                         |
  |   manage_watchlist     |     |   api_health            |
  |   get_alerts           |     |   bulk_lookup           |
  |   route_alert          |     |   tms_sync              |
  |   monitor_compliance   |     |   webhook_manage        |
  |                        |     |                         |
  |   Min: Pro+            |     |   Min: SMB              |
  +------------------------+     +-------------------------+
```

---

## Skill Catalog

Fourteen skills are organized by carrier job. Each package includes a focused
`SKILL.md`, customer one-pager and PDF, decision playbook, and behavioral
`eval-spec.yaml`.

### Search & Discovery

| Skill | Trigger Phrases | Description |
|-------|----------------|-------------|
| `searchcarriers-carrier-lookup` | "look up carrier", "source this lane", "find DOT" | Resolve identities or source candidates with documented fleet, insurance, equipment, cargo, and lane filters |
| `searchcarriers-vin-decoder` | "decode VIN", "VIN lookup", "who owns this truck" | Resolve VINs to owning carriers and equipment details |
| `searchcarriers-entity-mapper` | "map entity", "related companies", "corporate family" | Map relationships between carriers, brokers, and shippers |

### Safety & Compliance

| Skill | Trigger Phrases | Description |
|-------|----------------|-------------|
| `searchcarriers-safety-scorer` | "explain safety", "how safe is", "review this record" | Interpret ratings, exposure, crashes, and BASIC evidence without inventing an official score |
| `searchcarriers-inspection-analyzer` | "analyze inspections", "violation history", "OOS rate" | Analyze inspection history, violation patterns, and out-of-service trends |
| `searchcarriers-compliance-monitor` | "compliance check", "authority status", "operating authority" | Monitor authority status, insurance requirements, and regulatory compliance |

### Vetting & Risk

| Skill | Trigger Phrases | Description |
|-------|----------------|-------------|
| `searchcarriers-insurance-validator` | "check insurance", "coverage valid", "insurance status" | Reconcile filings with requirements for the exact authority, cargo, entity, and vehicle |
| `searchcarriers-authority-checker` | "check authority", "authority history", "revocation history" | Verify operating authority status and track authority change history |
| `searchcarriers-vetting-rules` | "vet this carrier", "run qualification", "pass/review/fail" | Run a named qualification and preserve rule-level evidence and missing-data handling |
| `searchcarriers-fraud-detector` | "fraud check", "identity mismatch", "suspicious carrier" | Triage identity anomalies and prescribe independent verification without making an accusation |

### Operations

| Skill | Trigger Phrases | Description |
|-------|----------------|-------------|
| `searchcarriers-bulk-processor` | "bulk lookup", "batch carriers", "process CSV" | Batch-process carrier lists from CSV with structured results |
| `searchcarriers-data-exporter` | "export data", "download report", "generate CSV" | Export carrier data in multiple formats (JSON, CSV, Markdown) |
| `searchcarriers-contact-verifier` | "verify contact", "new dispatch email", "check phone" | Compare contact evidence and require a trusted-channel callback for material changes |
| `searchcarriers-tms-connector` | "sync TMS", "push to TMS", "TMS update" | Push/pull carrier data to TMS platforms on status changes |

---

## Tier Matrix

Features available at each SearchCarriers subscription tier:

| Feature | Free | Basic | Pro | Pro+ | SMB | Enterprise |
|---------|:----:|:-----:|:---:|:----:|:---:|:----------:|
| **Carrier Lookup** | x | x | x | x | x | x |
| **Search (DOT/MC/name)** | x | x | x | x | x | x |
| **SCAC Lookup** | x | x | x | x | x | x |
| **VIN Decoder** | - | - | x | x | x | x |
| **Entity Mapper** | - | - | x | x | x | x |
| **Carrier Profile** | - | x | x | x | x | x |
| **Safety Scorer** | x | x | x | x | x | x |
| **Inspection Analyzer** | - | - | x | x | x | x |
| **Compliance Monitor** | - | - | x | x | x | x |
| **Risk Scoring** | - | - | x | x | x | x |
| **Insurance Validator** | - | - | x | x | x | x |
| **Vetting Rules** | - | - | - | x | x | x |
| **Authority Checker** | x | x | x | x | x | x |
| **Fraud Detector** | - | - | x | x | x | x |
| **Vetting Reports** | - | - | x | x | x | x |
| **Carrier Comparison** | - | - | x | x | x | x |
| **Data Export** | - | - | x | x | x | x |
| **Carrier Watch** | - | - | - | x | x | x |
| **Alert Routing (Slack/Telegram)** | - | - | - | x | x | x |
| **Compliance Dashboard** | - | - | - | x | x | x |
| **Contact Verifier** | - | - | x | x | x | x |
| **Bulk Processor** | - | - | - | - | x | x |
| **TMS Sync** | - | - | - | - | - | x |
| **Webhook Management** | - | - | - | - | x | x |
| **Fleet Risk Dashboard** | - | - | - | - | - | x |
| **Automated Onboarding** | - | - | - | - | - | x |

Tier gating is enforced at three layers: MCP server startup (API key check), per-tool tier validation (returns upgrade URL if insufficient), and skill prerequisites (documented in each SKILL.md).

---

## API contract

SearchCarriers capabilities currently span three API versions:

- v3 for search, company field selection, equipment, and crashes
- v2 for qualification reports
- v1 for VIN/SCAC lookup, detailed history, export, and watches

The exact routes, advanced search filters, verified parameter names,
data-handling boundary, and source
links live in **[API-DISCOVERY.md](API-DISCOVERY.md)**. In particular, v3 uses
`docketNumber`, `perPage`, `addressState`, and `addressCity`; older names may be
silently ignored even when the API returns HTTP 200.

The product research behind each workflow is recorded in
**[docs/PAIN-POINT-RESEARCH.md](docs/PAIN-POINT-RESEARCH.md)**.

---

## Composed Workflows

Seven packaged workflows chain the focused skills and MCP tools into larger
carrier operations. The tier names describe the required SearchCarriers API
access; this repository does not sell or provision those subscriptions.

### Pro Tier

| Workflow | What It Does | Plugins Used |
|----------|-------------|--------------|
| Daily Vetting Digest | Build a reconciled Pass/Review/Fail queue; delivery remains explicitly configured | risk-engine + ops-reporter |

### Pro+ Tier

| Workflow | What It Does | Plugins Used |
|----------|-------------|--------------|
| Slack Carrier Watch | Validate and format an externally supplied change event for configured Slack delivery | watchdog |
| Compliance Dashboard | Build an as-of panel dashboard that exposes stale, missing, and high-priority evidence | carrier-intel + risk-engine + watchdog |
| Insurance Lapse Alert | Evaluate an insurance change or current filing and create a bounded response | risk-engine |

### SMB / Enterprise Tier

| Workflow | What It Does | Plugins Used |
|----------|-------------|--------------|
| Bulk Vetting Pipeline | Run named qualification across a carrier list with restartable evidence | api-bridge + risk-engine + ops-reporter |
| TMS Auto-Sync | Apply an approved carrier change set idempotently and prove the result | api-bridge + carrier-intel + risk-engine |
| Fleet Risk Dashboard | Rank a carrier panel by explicit, actionable evidence exceptions | carrier-intel + risk-engine + ops-reporter |

---

## First 10 Minutes

What a new user does after cloning:

**Minute 0-1: Clone and setup.**

```bash
git clone https://github.com/jeremylongshore/searchcarriers-tools.git
cd searchcarriers-tools && ./scripts/setup-dev.sh
```

The setup script installs dependencies, validates your environment, and confirms everything is wired correctly.

**Minute 1-2: Configure your API key.**

Get your key from [SearchCarriers API settings](https://searchcarriers.com/settings/api-tokens), then:

```bash
export SEARCHCARRIERS_API_KEY="your_id|your_token"
```

Add it to your `.env` file for persistence (see `.env.example`).

**Minute 2-4: Run your first carrier lookup.**

Open Claude Code and try:

```
/sc-lookup Werner Enterprises
```

You should see carrier identity, contact information, fleet evidence, and operating authority with source and missing-data context.

**Minute 4-6: Try a carrier profile.**

Get the full picture for a carrier by DOT number:

```
/sc-profile 69494
```

This pulls search results, insurance, authority status, and equipment data into a single view.

**Minute 6-8: Score a carrier's risk (Pro tier).**

```
/sc-risk 69494
```

The risk engine returns sourced safety evidence and an advisory model result. A Pass/Review/Fail decision requires a named SearchCarriers qualification or a complete caller-owned policy.

**Minute 8-10: Generate a vetting report (Pro tier).**

```
/sc-report 69494
```

Produces a formatted vetting report that preserves the underlying verdict, missing evidence, sources, and decision owner.

**What's next:** Add carriers to your watch list with `/sc-watch`, set up Slack alerts, or bulk-process a CSV of carriers with `/sc-bulk`.

---

## Development

### Validate

Run the single validation script to check all plugins and skills:

```bash
./scripts/validate.sh --verbose
```

This validates:
- Plugin manifest (`plugin.json`) required fields
- SKILL.md frontmatter (name format, description length, allowed tools)
- No absolute paths in skills (must use `{baseDir}/`)
- Bash tool scoping (`Bash(python:*)` not raw `Bash`)
- Secret scanning

### Test

```bash
pytest -v
```

Tests cover plugin structure validation, skill spec compliance, and MCP server responses.

### Project Structure

```
searchcarriers/
├── plugins/                     # 5 Claude Code plugins
│   ├── searchcarriers-carrier-intel/    # Stackable: INPUT
│   ├── searchcarriers-risk-engine/      # Stackable: ANALYSIS
│   ├── searchcarriers-ops-reporter/     # Stackable: OUTPUT
│   ├── searchcarriers-watchdog/         # Standalone: MONITORING
│   └── searchcarriers-api-bridge/       # Standalone: INTEGRATION
├── skills/                      # 14 standalone skills
│   ├── search-discovery/        # 3 skills
│   ├── safety-compliance/       # 3 skills
│   ├── vetting-risk/            # 4 skills
│   └── operations/              # 4 skills
├── scripts/
│   ├── validate.sh              # Single validator
│   └── setup-dev.sh             # Onboarding script
├── templates/                   # 6-doc enterprise planning templates
├── inventory/                   # Plugin + skill tracking CSVs
├── tests/                       # pytest suite
├── API-DISCOVERY.md             # Full API reference
├── MASTER-BLUEPRINT.md          # Architecture decisions
├── CHANGELOG.md
├── VERSION                      # 0.3.0
└── LICENSE                      # Apache-2.0
```

### Contributing

Each plugin contains its own `docs/` directory with a 6-document enterprise planning set (Business Case, PRD, Architecture, User Journey, Technical Spec, Status). Start there to understand the design intent before making changes.

Skills follow the `/skill-creator` specification. Required sections in every SKILL.md:

```
## Overview
## Prerequisites        (include API tier requirement)
## Instructions         (use {baseDir}/ for file references)
## Examples             (real freight scenarios)
## Error Handling
## Resources
```

---

## Architecture Note

**Versioned API adapters + evidence-driven skills.**

The MCP servers own authentication, version routing, response normalization,
tier gates, and deterministic operations such as batch checkpoints, policy-rule
evaluation, and report rendering. The shared API contract keeps v3, v2, and v1
capabilities explicit and makes unknown parameters fail visibly.

The skills define the operational decision: which evidence to fetch, how to
separate API facts from policy and inference, how missing data affects the
result, and which person owns the next action. Named qualifications preserve
SearchCarriers Pass/Review/Fail evidence; local vetting requires a complete
caller-owned policy.

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).

Apache-2.0 governs this repository's code. Calls to the hosted
[SearchCarriers](https://searchcarriers.com) API remain subject to the service's
account requirements, subscription tiers, and terms.

Copyright (c) 2026 Intent Solutions, LLC. All rights reserved.
