# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Customer-facing Markdown and one-page PDF briefs for all 26 skills, embedded plugin
  skills, and composed workflows.
- A deterministic one-pager generator with drift checks in the repository validation lane.
- A root multi-client MCP configuration, model-compatibility guide, and live protocol
  handshake tests for all five MCP servers.

### Changed

- Link every package to its one-page brief and PDF, and document the public capability
  page alongside the package catalog.
- Describe Grok Build, Claude Code, and generic MCP use explicitly while keeping hosted
  Grok Bot transport requirements separate from the local stdio implementation.

## [0.3.0] - 2026-09-23

### Added

- Pain-point research tying carrier sourcing, identity, insurance,
  qualification, bulk operations, and TMS workflows to current authoritative
  sources.
- Decision playbooks and behavioral eval specifications for all 26 skills and
  workflows.
- API v3 advanced search filters for fleet size, insurance, registration,
  authority age, equipment, cargo, and lane origin/destination criteria.
- Risk Engine `qualification_reports` tool for the API v2 named qualification
  endpoint.

### Changed

- Rebuilt every skill around one bounded operational job, sourced evidence,
  missing-data behavior, and a concrete next action.
- `vetting_check` now requires a complete caller-owned policy and no longer
  applies hidden default thresholds.
- Labeled the numeric Risk Engine score as a legacy advisory model rather than
  an official rating or named qualification.

## [0.2.0] - 2026-09-22

### Added

- Shared hybrid API contract for v3 search/company data, v2 qualification
  reports, and documented v1 specialty, history, export, and watch routes.
- Contract tests for v3 parameters, dedicated VIN/SCAC paths, company field
  selection, and cross-version health probes.
- Public contribution, security, support, conduct, ownership, and dependency
  maintenance files.

### Changed

- Carrier Intel now uses v3 search and field-selected company requests. MC
  lookup uses `docketNumber`; pagination uses `perPage`; location filters use
  `addressState` and `addressCity`.
- API Bridge, Risk Engine, Ops Reporter, and Watchdog current-state checks now
  use v3 search while retaining documented v1 detail resources.
- Watch management now uses the published company watch routes and removes a
  watch by synchronizing an empty `watch_types` array.
- Skills and workflows reference one API contract instead of independently
  copying route tables.
- Live smoke receipts retain response structure only, never carrier values.
- Test fixtures are fully synthetic and use reserved example domains.
- Project license changed from BSL 1.1 to Apache-2.0 for the public source
  release. SearchCarriers API use still requires an appropriate account.

### Fixed

- Removed calls to assumed alert-feed and upstream webhook CRUD routes that are
  absent from the published API.
- Encrypted environment launcher no longer sources decrypted dotenv data or
  interprets token metacharacters as shell syntax.
- Live-test secret fixtures redact their diagnostic representation so pytest
  failures cannot print bearer tokens.
- Removed obsolete `mcNumber`, `legalName`, `state`, `city`, `per_page`, and
  query-string VIN guidance from current skills.

### Additional fixes
- pyproject.toml: removed unused setuptools-scm, added `packages = []` to fix editable install
- README.md tier matrix: Contact Verifier corrected to Pro (was SMB), TMS Sync corrected to Enterprise-only (was SMB)
- Aligned all SKILL.md metadata versions to 0.1.0 (15 files were incorrectly at 1.0.0)
- validate.sh: fixed `find` alias conflict (use /usr/bin/find), fixed `set -e` with `$VERBOSE &&` pattern
- Added workflows/ to validator and test fixture scan paths
- Added embedded skills and workflow skills to skills_inventory.csv (12 new entries)
- API endpoints: corrected flat pattern (/authorities) to path pattern (/company/{dot}/authorities) in 4 MCP servers
- Insurance validation: fixed sum vs max logic for BIPD minimum coverage check
- Risk engine SKILL.md: weight model table now matches actual additive penalty implementation
- Removed `/tmp/` hardcoded output paths from 3 standalone skills (tms-connector, data-exporter, bulk-processor); now use `SC_OUTPUT_DIR` env var or current directory
- Removed "real-time" claims from api-bridge architecture doc and risk-engine SCHEMA.md
- Fixed api-bridge README claiming parallel execution (actual design is sequential with rate limiting)

### Additional changes
- All 5 business cases: "ROI Calculation" renamed to "Efficiency Gains", removed unsupported dollar/percentage claims
- All 5 PRDs: success metrics prefixed with "Target:" (goals, not measured results)
- README: replaced "actionable freight intelligence" with "structured carrier data", rewrote architecture note to be factual
- User journeys: removed specific time-savings claims, fixed api-bridge TMS journey to match v0.1 reality

## [0.1.0] - 2026-02-26

### Added

#### Foundation (Phase 1-2)
- Repository structure, CI/CD, core configuration
- 6-doc enterprise planning templates (Business Case through Status)
- Inventory tracking CSVs for plugins and skills
- Single validation script (`scripts/validate.sh`)
- Developer onboarding script (`scripts/setup-dev.sh`)
- GitHub Actions CI workflow (tiered: validate + test)
- API discovery documentation with 11 confirmed endpoints

#### 14 Standalone Skills (Phase 3)
- Search & Discovery: carrier-lookup (Free), vin-decoder (Pro), entity-mapper (Pro)
- Safety & Compliance: safety-scorer (Free), inspection-analyzer (Pro), compliance-monitor (Pro)
- Vetting & Risk: insurance-validator (Pro), authority-checker (Free), vetting-rules (Pro+), fraud-detector (Pro)
- Operations: bulk-processor (SMB), data-exporter (Pro), contact-verifier (Pro), tms-connector (Enterprise)

#### Stackable Pipeline (Phases 4-6)
- **searchcarriers-carrier-intel** (INPUT): 4 MCP tools (carrier_lookup, carrier_profile, entity_map, fleet_summary), auto-detect search type, slash commands (/sc-lookup, /sc-profile), carrier-analyst agent
- **searchcarriers-risk-engine** (ANALYSIS): 4 MCP tools (risk_score, vetting_check, insurance_check, compliance_audit), 7-factor risk scoring algorithm, configurable vetting rules with PASS/REVIEW/FAIL verdicts, slash commands (/sc-risk, /sc-vet), risk-analyst agent
- **searchcarriers-ops-reporter** (OUTPUT): 4 MCP tools (generate_report, generate_fleet, generate_compare, export_data), professional vetting reports, side-by-side carrier comparison, multi-format export (JSON/CSV/Markdown), slash commands (/sc-report, /sc-compare), ops-reporter agent
- Shared tier gating utility (`plugins/shared/tier_gate.py`)
- Pipeline output contracts (`_pipeline` envelope in all tool responses)

#### Standalone Plugins (Phases 7-8)
- **searchcarriers-watchdog** (MONITORING): 4 MCP tools (manage_watchlist, get_alerts, route_alert, monitor_compliance), multi-channel alert routing (Slack/Telegram/email/webhook), compliance drift detection, slash commands (/sc-watch, /sc-alerts), watchdog-monitor agent
- **searchcarriers-api-bridge** (INTEGRATION): 4 MCP tools (api_health, bulk_lookup, tms_sync, webhook_manage), batch processing up to 100 carriers, TMS field mapping (generic/McLeod/TMW/DAT), local webhook config, slash commands (/sc-api, /sc-bulk), integration-manager agent

#### Per-Plugin Enterprise Documentation
- Complete 6-doc set (Business Case, PRD, Architecture, User Journey, Technical Spec, Status) for all 5 plugins
- Embedded SKILL.md, agent definition, and SCHEMA.md per plugin
