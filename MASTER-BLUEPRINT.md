# 🏗️ SearchCarriers Master Blueprint
# Plugin & Skill Repo - Implementation Plan
# Version: 1.0.0 | Date: 2026-02-26
# Owner: Jeremy Longshore / Intent Solutions
# Repo: jeremylongshore/searchcarriers-tools (public, Apache-2.0)

## Context

SearchCarriers.com is a motor carrier research platform with API access, TMS
integrations, and tiered plans. This independent repository packages plugins
and skills for freight professionals. It began as a private implementation and
is published from a clean, data-free source snapshot. Skills follow the
`/skill-creator` spec as their authoring standard.

## API Reality (Reviewed 2026-09-22)

**API origin**: `https://searchcarriers.com` with v3, v2, and v1 routes selected
by capability. See `API-DISCOVERY.md` for the authoritative contract.

**Auth**: `Authorization: Bearer {id}|{token}` (Laravel Sanctum)

### Confirmed capability routes

| Endpoint | Method | Path | Parameters |
|----------|--------|------|------------|
| Search | GET | `/api/v3/search` | `superSearchTerm`, `dotNumber`, `docketNumber`, `addressState`, `addressCity`, `perPage`, `page` |
| Company profile | GET | `/api/v3/company/{dot}` | `fields` |
| Company equipment | GET | `/api/v3/company/{dot}/equipment` | Pagination/filter parameters |
| Company crashes | GET | `/api/v3/company/{dot}/crashes` | Pagination/filter parameters |
| Qualification reports | GET | `/api/v2/company/{dot}/qualification-reports` | |
| VIN | GET | `/api/v1/search/by-vin/{vin}` | |
| SCAC | GET | `/api/v1/search/scac` | scac |
| Company Inspections | GET | `/api/v1/company/{dot}/inspections` | |
| Company Insurances | GET | `/api/v1/company/{dot}/insurances` | |
| Company Authorities | GET | `/api/v1/company/{dot}/authorities` | |
| Company OOS Orders | GET | `/api/v1/company/{dot}/out-of-service-orders` | |
| Company Equipment | GET | `/api/v1/company/{dot}/equipment` | |
| Company Vehicles | GET | `/api/v1/company/{dot}/vehicles` | |
| Authority History | GET | `/api/v1/authority/{docketNumber}/history` | Requires the MC/MX/FF docket number |
| Export | GET | `/api/v1/export` | dot_numbers[], file_format |
| Watch | GET/POST | `/api/v1/company/{dot}/watch` | |

Risk factors, service areas, and vetting reports are selectable sections of the
v3 company response. The published API does not provide the formerly assumed
alert-feed or webhook-management routes.

### Architecture Principle: Thin Wrapper + Thick Intelligence

#### What the API Already Does (DO NOT Reproduce)
- Carrier search/lookup, insurance, inspections, authority, equipment, OOS, export, watches
- Raw FMCSA data retrieval

#### What We Add (Our Value Layer)
- **Intelligence**: Claude interprets raw data ("is this carrier safe?" not just numbers)
- **Pipeline**: Chain lookups automatically (search -> inspect -> assess -> report)
- **Natural language**: `/sc-lookup JB Hunt in Arkansas` instead of curl
- **Formatted reports**: Turn nested carrier data into human-readable vetting reports
- **Comparison**: Side-by-side carrier analysis (no API endpoint for this)
- **Alert interpretation**: "Insurance lapsed" not raw webhook JSON
- **Custom vetting rules**: User-defined thresholds (min power units, max crash rate)
- **Bulk vetting logic**: Pass/review/fail decisions (API gives data, we add judgment)

MCP servers = thin API callers (no business logic duplication)
Skills = where the value lives (interpretation, rules, reporting templates)

## Nixtla Repo Audit - Action Items for Improvement

| Issue | What's Wrong | Fix in SearchCarriers |
|-------|-------------|----------------------|
| Doc sprawl (120+ files in 000-docs/) | Overwhelming, docs divorced from code | 6-doc set lives INSIDE each plugin's `docs/` dir. Templates at repo root `templates/` |
| Numbered dirs (003-skills, 005-plugins) | Opaque naming | Flat: `plugins/`, `skills/`, `scripts/`, `tests/` |
| 3 separate validators | Fragmented, confusing | Single `scripts/validate.sh` |
| 9 CI workflows | Overkill for most repos | Single `ci.yml` with tiered jobs |
| 11 plugin stubs (no code) | Misleading | Ship only working plugins. No stubs |
| No free/paid clarity | Must read each README to find cost | Tier matrix in README + tier gating in every MCP server |
| Skill discovery problem | 30 skills, no grouping | Categorized catalog in README with trigger phrases |
| Description max 1024 chars | Exceeds skill-creator spec (200 max) | Follow skill-creator: 200 char max |
| High onboarding friction | Setup script + complex docs | 2 commands, < 2 minutes |
| No premium workflows | All plugins are standalone tools | Add-on workflows: email digests, Slack/Telegram alerts, automated reports |

## Repo Structure

```
searchcarriers/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug-report.yml
│   │   └── skill-request.yml
│   └── workflows/
│       └── ci.yml                           # Single workflow, tiered
├── templates/                               # 6-doc planning templates (adapted from nixtla)
│   ├── 01-BUSINESS-CASE.md
│   ├── 02-PRD.md
│   ├── 03-ARCHITECTURE.md
│   ├── 04-USER-JOURNEY.md
│   ├── 05-TECHNICAL-SPEC.md
│   └── 06-STATUS.md
├── plugins/
│   ├── searchcarriers-carrier-intel/        # STACKABLE 1: INPUT
│   │   ├── .claude-plugin/plugin.json
│   │   ├── .mcp.json
│   │   ├── docs/                            # 6-doc set LIVES WITH the plugin
│   │   │   ├── 01-BUSINESS-CASE.md
│   │   │   ├── 02-PRD.md
│   │   │   ├── 03-ARCHITECTURE.md
│   │   │   ├── 04-USER-JOURNEY.md
│   │   │   ├── 05-TECHNICAL-SPEC.md
│   │   │   └── 06-STATUS.md
│   │   ├── commands/
│   │   │   ├── sc-lookup.md
│   │   │   └── sc-profile.md
│   │   ├── agents/carrier-analyst.md
│   │   ├── skills/searchcarriers-carrier-intel/SKILL.md
│   │   ├── scripts/
│   │   │   ├── carrier_intel_mcp.py
│   │   │   └── requirements.txt
│   │   └── README.md                        # Quick start + data contracts
│   ├── searchcarriers-risk-engine/          # STACKABLE 2: ANALYSIS
│   │   ├── (same structure including docs/)
│   │   ├── commands/ (sc-risk.md, sc-vet.md)
│   │   └── scripts/risk_engine_mcp.py
│   ├── searchcarriers-ops-reporter/         # STACKABLE 3: OUTPUT
│   │   ├── (same structure including docs/)
│   │   ├── commands/ (sc-report.md, sc-compare.md)
│   │   └── scripts/ops_reporter_mcp.py
│   ├── searchcarriers-watchdog/             # STANDALONE: MONITORING
│   │   ├── (same structure including docs/)
│   │   ├── commands/ (sc-watch.md, sc-alerts.md)
│   │   └── scripts/watchdog_mcp.py
│   └── searchcarriers-api-bridge/           # STANDALONE: INTEGRATION
│       ├── (same structure including docs/)
│       ├── commands/ (sc-api.md, sc-bulk.md)
│       └── scripts/api_bridge_mcp.py
├── skills/                                  # 14 standalone skills
│   ├── search-discovery/
│   │   ├── searchcarriers-carrier-lookup/SKILL.md
│   │   ├── searchcarriers-vin-decoder/SKILL.md
│   │   └── searchcarriers-entity-mapper/SKILL.md
│   ├── safety-compliance/
│   │   ├── searchcarriers-safety-scorer/SKILL.md
│   │   ├── searchcarriers-inspection-analyzer/SKILL.md
│   │   └── searchcarriers-compliance-monitor/SKILL.md
│   ├── vetting-risk/
│   │   ├── searchcarriers-insurance-validator/SKILL.md
│   │   ├── searchcarriers-authority-checker/SKILL.md
│   │   ├── searchcarriers-vetting-rules/SKILL.md
│   │   └── searchcarriers-fraud-detector/SKILL.md
│   └── operations/
│       ├── searchcarriers-bulk-processor/SKILL.md
│       ├── searchcarriers-data-exporter/SKILL.md
│       ├── searchcarriers-contact-verifier/SKILL.md
│       └── searchcarriers-tms-connector/SKILL.md
├── inventory/                               # 📊 Tracking CSVs
│   ├── plugins_inventory.csv
│   ├── skills_inventory.csv
│   └── README.md
├── scripts/
│   ├── validate.sh                          # Single validator
│   └── setup-dev.sh                         # < 2 min onboarding
├── tests/
│   ├── test_plugins.py
│   ├── test_skills.py
│   └── conftest.py
├── CLAUDE.md
├── README.md                                # Docs + catalog + tier matrix
├── CHANGELOG.md
├── LICENSE                                  # Apache-2.0
├── VERSION                                  # 0.2.0
├── .gitignore
├── .editorconfig
└── pyproject.toml
```

## Plugin Design

### Stackable Pipeline (Carrier Intelligence)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  Carrier Intel   │───>│   Risk Engine     │───>│   Ops Reporter      │
│  (INPUT)         │    │   (ANALYSIS)      │    │   (OUTPUT)          │
│                  │    │                   │    │                     │
│  carrier_lookup  │    │  risk_score       │    │  generate_report    │
│  carrier_profile │    │  vetting_check    │    │  generate_fleet     │
│  entity_map      │    │  insurance_check  │    │  generate_compare   │
│  fleet_summary   │    │  compliance_audit │    │  export_data        │
│                  │    │                   │    │                     │
│  Min: Free       │    │  Min: Pro         │    │  Min: Pro           │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

**Carrier Intel API Mappings** (thin wrappers over real endpoints):

| MCP Tool | Wraps API Endpoint(s) |
|----------|----------------------|
| `carrier_lookup` | `GET /api/v3/search` with current v3 parameters; dedicated v1 paths for VIN and SCAC |
| `carrier_profile` | `GET /api/v3/company/{dot}?fields=...` |
| `entity_map` | v3 company/equipment plus `GET /api/v1/search/by-vin/{vin}` |
| `fleet_summary` | `GET /api/v3/company/{dot}/equipment` |

Each plugin's MCP tools explicitly document their input/output so Claude can chain them without human guidance.

### Standalone Plugins

**searchcarriers-watchdog** (Min: Pro+)
- manage_watchlist: Add/remove carriers from Carrier Watch
- get_alerts: Pull recent changes (safety, insurance, authority)
- route_alert: Push alerts to Slack, Telegram, email, webhook
- monitor_compliance: Detect compliance drift over time

**searchcarriers-api-bridge** (Min: SMB)
- api_health: Check endpoint status and rate limits
- bulk_lookup: Batch carrier operations (CSV in, structured out)
- tms_sync: Push/pull carrier data to TMS platforms
- webhook_manage: CRUD for Carrier Watch webhooks

## Premium Add-On Workflows (Paid Tier Features)

These are the money-makers - workflows that justify higher tiers:

### Pro Tier Add-Ons
| Workflow | What It Does | Plugin |
|----------|-------------|--------|
| Daily Vetting Digest | Auto-vet all carriers in your watch list, email summary of pass/review/fail | ops-reporter + watchdog |
| Inspection Alert Email | When a watched carrier gets a new inspection, email formatted summary | watchdog |
| Risk Score Change Alerts | When a carrier's safety rating changes, push notification | risk-engine + watchdog |

### Pro+ Tier Add-Ons
| Workflow | What It Does | Plugin |
|----------|-------------|--------|
| Slack Carrier Watch | Route all Carrier Watch alerts to a Slack channel with formatted cards | watchdog |
| Telegram Bot Lookup | `/dot 12345` in Telegram returns carrier summary | carrier-intel + api-bridge |
| Compliance Dashboard Email | Weekly compliance report across all watched carriers | ops-reporter + watchdog |
| Insurance Lapse Alert | Instant Slack/email when a carrier's insurance cancellation is detected | watchdog + risk-engine |

### SMB/Enterprise Tier Add-Ons
| Workflow | What It Does | Plugin |
|----------|-------------|--------|
| Bulk Vetting Pipeline | Upload CSV of 500+ carriers, get back vetting report with pass/fail per carrier | api-bridge + risk-engine + ops-reporter |
| TMS Auto-Sync | When carrier status changes, auto-update carrier record in TMS | api-bridge + watchdog |
| Fleet Risk Dashboard | Automated weekly fleet risk analysis pushed to Slack/email | all 3 stackable + watchdog |
| Competitive Intel | Monitor competitor carrier panels, alert on changes | carrier-intel + watchdog |
| Automated Onboarding | New carrier added to TMS triggers full vetting pipeline, results emailed to ops team | api-bridge + risk-engine + ops-reporter |

## Per-Plugin Enterprise Documentation (6-Doc Standard)

Each plugin gets a complete `docs/` directory with 6 documents adapted from nixtla's enterprise templates. Docs live WITH the plugin, not in a separate sprawling folder.

| Doc | Purpose | Key Sections |
|-----|---------|-------------|
| `01-BUSINESS-CASE.md` | Why this plugin exists | Problem, target customer, ROI calc, competitive positioning, risks |
| `02-PRD.md` | What it does | Goals/non-goals, user stories, functional requirements (FR-XX), MVP scope, success metrics |
| `03-ARCHITECTURE.md` | How it works | System context diagram, component design, data flow, integrations, security, error handling |
| `04-USER-JOURNEY.md` | How users experience it | Persona, step-by-step walkthrough with real commands/outputs, error scenarios, FAQ |
| `05-TECHNICAL-SPEC.md` | Implementation details | Tech stack, dependencies, file structure, API reference, env vars, testing, performance |
| `06-STATUS.md` | Where it stands | Current state checklist, blockers, next steps, metrics, decision log |

**Templates** live at `templates/` root dir. Copy per-plugin, fill in domain-specific content.

**Improvement over nixtla**: In nixtla, plugin docs were in `000-docs/000a-planned-plugins/implemented/{plugin}/` - completely divorced from code. Here they're at `plugins/{plugin}/docs/` - you open the plugin, the docs are right there.

**README.md per plugin** is NOT the 6-doc set. README is the quick-start (install, configure, run in < 60 seconds). The 6-doc set is the deep reference.

## Skill Standards (Source of Truth: /skill-creator)

### Frontmatter (Required - Baseline)
```yaml
---
name: searchcarriers-carrier-lookup        # lowercase, hyphens, numbers; max 64 chars
description: >                              # max 200 chars, third person, "Use when" pattern
  Search carriers by DOT, MC, or name from 4M+ companies.
  Use when looking up a specific carrier or verifying credentials.
---
```

### Frontmatter (Enterprise - All SearchCarriers skills use this)
```yaml
---
name: searchcarriers-carrier-lookup
description: >
  Search carriers by DOT, MC, or name from 4M+ companies.
  Use when looking up a specific carrier or verifying credentials.
allowed-tools: "Read,Grep,Bash(python:*)"
metadata:
  author: Jeremy Longshore <jeremy@intentsolutions.io>
  version: 1.0.0
  license: Apache-2.0
---
```

### Validation Rules (from skill-creator Go validator)
- **name**: `^[a-z0-9]+(-[a-z0-9]+)*(:[a-z0-9]+(-[a-z0-9]+)*)?$`, max 64 chars, no "anthropic"/"claude"
- **description**: max 200 chars, no XML tags, third person, "use when" pattern
- **body**: warn at 500+ lines, require ## Instructions and ## Examples sections
- **Bash scoping**: `Bash(python:*)` not raw `Bash`
- **Valid tools**: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task, TodoWrite, NotebookEdit, Skill

### `{baseDir}` Pattern (Portable File References)
Skills reference their own files using `{baseDir}` which resolves to the skill directory at runtime:
```markdown
## Instructions
1. Run the lookup script:
   ```bash
   python {baseDir}/scripts/carrier_lookup.py --dot "$DOT_NUMBER"
   ```
2. Load the API reference from `{baseDir}/references/API_ENDPOINTS.md`
3. Use the report template at `{baseDir}/assets/templates/carrier_report.md`
```
- NEVER use absolute paths (`/home/jeremy/...`) - breaks portability
- ALWAYS use `{baseDir}/` for skill-internal references
- Validator warns on absolute paths

### Skill Directory Structure (Full)
```
searchcarriers-carrier-lookup/
├── SKILL.md                           # Required - frontmatter + instructions
├── scripts/                           # Optional - executable code (0 token cost)
│   ├── carrier_lookup.py
│   └── requirements.txt
├── references/                        # Optional - docs loaded into context (HIGH token cost)
│   └── API_ENDPOINTS.md
├── templates/                         # Optional - boilerplate files (0 token cost)
│   └── carrier_report.md
└── assets/                            # Optional - static resources (0 token cost)
    └── sample_output.json
```

**Token economics**:
- `scripts/` = 0 tokens (executed via Bash, only output costs tokens)
- `references/` = HIGH tokens (loaded into context when skill activates)
- `templates/` = 0 tokens (path-referenced, not loaded)
- `assets/` = 0 tokens (path-referenced, not loaded)

### Required Body Sections
```markdown
# Skill Title
## Overview
## Prerequisites           (include API tier requirement)
## Instructions            (use {baseDir}/ for file refs)
## Examples                (real freight scenarios)
## Error Handling          (tier gating errors, API errors)
## Resources               (related skills, SearchCarriers docs)
```

## Inventory Tracking (CSV + SCHEMA per Plugin)

### Repo-Level Inventory CSVs
```
inventory/
├── plugins_inventory.csv      # WHO/WHAT/WHEN/TARGET/PRODUCTION per plugin
├── skills_inventory.csv       # Category, type, status, tier, has_scripts/refs/templates
└── README.md                  # How to read and update
```

**plugins_inventory.csv columns**: name, type, stage, status, min_tier, who, what, when, target_goal, production, version, docs_complete

**skills_inventory.csv columns**: name, category, type, status, min_tier, plugin_embedded, has_scripts, has_references, has_templates, description

### Per-Plugin SCHEMA.md
Each plugin gets a `SCHEMA.md` (like nixtla's SCHEMA-{name}.md) containing:
- Directory tree (planned + actual)
- Plugin manifest field table with status
- MCP tools table (name, purpose, min tier)
- Slash commands table
- Skills registry
- Agents registry
- Non-functional requirements (latency, reliability)
- CSV inventory reference (WHO/WHAT/WHEN/TARGET/PRODUCTION)

## API Key Gating Strategy

Three layers, no silent failures:

**Layer 1 - MCP Server Startup**: Check `SEARCHCARRIERS_API_KEY` env var, return helpful error if missing

**Layer 2 - Per-Tool Tier Check**: Each MCP tool knows its min tier. Returns upgrade URL if insufficient:
```python
TIER_ORDER = ["free", "basic", "pro", "proplus", "smb", "enterprise"]
TOOL_TIERS = {
    "carrier_lookup": "free",
    "carrier_profile": "pro",
    "risk_score": "pro",
    "vetting_check": "proplus",
    "bulk_lookup": "smb",
    "tms_sync": "enterprise",
}
```

**Layer 3 - SKILL.md Prerequisites**: Every skill states its min tier in `## Prerequisites`

## CI/CD (Single Workflow, Tiered)

**`.github/workflows/ci.yml`**:
- **Job 1 `validate`** (every push, < 30s): JSON lint, plugin.json required fields, SKILL.md frontmatter, secret scan
- **Job 2 `test`** (PRs only, needs validate): Python setup, pytest, full validation with --verbose

## Build Phases

### Phase 1: Repo Foundation
1. Create the original private development repo, then publish a clean source snapshot
2. Configure maintainers through the public repository's GitHub permissions
3. Initialize structure: `.github/`, `plugins/`, `skills/`, `scripts/`, `tests/`, `templates/`, `inventory/`
4. Write LICENSE (Apache-2.0), CLAUDE.md, README.md, .gitignore, .editorconfig, VERSION, pyproject.toml
5. Write 6-doc enterprise templates in `templates/` (adapted from nixtla's 000a-dev-planning-templates)
6. Write inventory CSVs with all 5 plugins + 19 skills (status: ⬜ planned)
7. Write inventory README explaining CSV columns

### Phase 2: Validation & CI
5. Write `scripts/validate.sh` (single validator aligned with skill-creator rules)
6. Write `scripts/setup-dev.sh` (< 2 min onboarding)
7. Write `.github/workflows/ci.yml` (single tiered workflow)
8. Write test files (`test_plugins.py`, `test_skills.py`, `conftest.py`)

### Phase 3: Scaffold All 14 Skills
9. Use `/skill-creator` to generate all 14 standalone SKILL.md files
10. Move into category directories
11. Edit each with SearchCarriers-specific API endpoints, tier requirements, domain examples
12. Validate: `./scripts/validate.sh --skills-only`

### Phase 4: Plugin 1 - Carrier Intel (INPUT)
15. Scaffold plugin structure (plugin.json, .mcp.json, README, SCHEMA.md, docs/)
16. Write 6-doc set from templates (Business Case, PRD, Architecture, User Journey, Tech Spec, Status)
17. Write `carrier_intel_mcp.py` (4 MCP tools with tier gating)
18. Write commands (`sc-lookup.md`, `sc-profile.md`)
19. Write embedded skill (using `{baseDir}/` refs) + agent
20. Update inventory CSVs (status: 🟢 working)
21. Test with Claude Code

### Phase 5: Plugin 2 - Risk Engine (ANALYSIS)
19. Scaffold + 6-doc set
20. Write `risk_engine_mcp.py` (4 MCP tools)
21. Test pipeline: carrier-intel output flows into risk-engine

### Phase 6: Plugin 3 - Ops Reporter (OUTPUT)
22. Scaffold + 6-doc set
23. Write `ops_reporter_mcp.py` (4 MCP tools + report templates)
24. Test full pipeline: Intel -> Risk -> Report

### Phase 7: Standalone Plugins
25. Watchdog plugin (scaffold + 6-doc set + monitoring + alert routing to Slack/Telegram/email)
26. API Bridge plugin (scaffold + 6-doc set + bulk ops + TMS sync)

### Phase 8: Premium Workflows
27. Wire up stackable workflows (vetting digest, compliance dashboard)
28. Add Slack/Telegram/email integration scripts
29. Document premium workflows in README with tier requirements

### Phase 9: Quality Pass
30. Validate all skills against skill-creator spec (`skill validate --strict`)
31. Verify all 6-doc sets are complete per plugin
32. Verify tier gating end-to-end
33. Verify all SKILL.md files use `{baseDir}/` (no absolute paths)
34. Test onboarding flow (fresh clone -> working in < 2 min)
35. Historical milestone: update CHANGELOG.md and tag the initial v0.1.0

## Verification

- `./scripts/validate.sh --verbose` passes with 0 errors
- `skill validate --strict skills/**/*` passes (skill-creator validation)
- `pytest -v` all tests green
- Each plugin's MCP server starts and responds to tool calls
- Stackable pipeline: `/sc-lookup` -> `/sc-risk` -> `/sc-report` completes
- Tier gating: Free user gets clear upgrade message on Pro tools
- All SKILL.md use `{baseDir}/` (zero absolute paths)
- Each plugin has complete 6-doc set in `docs/`
- `adrenallen` can clone, run setup-dev.sh, and be working in < 2 min
- CI passes on GitHub (validate job on push, test job on PR)

## Key Files

| File | Purpose |
|------|---------|
| `README.md` | Catalog, tier matrix, pipeline diagram, onboarding |
| `CLAUDE.md` | AI instructions, conventions, directory layout |
| `templates/01-06` | Enterprise 6-doc templates (Business Case through Status) |
| `scripts/validate.sh` | Single validator (skill-creator rules + plugin checks) |
| `plugins/*/docs/01-06` | Per-plugin enterprise documentation (PRD, Architecture, etc.) |
| `plugins/*/scripts/*_mcp.py` | MCP servers with tier gating |
| `skills/*/SKILL.md` | Standalone skills with `{baseDir}/` refs |
| `LICENSE` | Apache-2.0; API use still requires a SearchCarriers subscription |

## Reference Repos (Source Material)

| Repo | What to Use |
|------|------------|
| `/home/jeremy/000-projects/nixtla/` | 6-doc templates, plugin structure, CI patterns |
| `/home/jeremy/000-projects/create-agent-skill/` | Skill validation rules (Go source of truth) |
| `/home/jeremy/000-projects/claude-code-plugins/` | Plugin manifest spec, marketplace standards |
