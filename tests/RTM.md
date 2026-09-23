# Requirements Traceability Matrix — searchcarriers-tools
<!-- MoSCoW assignments are policy. Do not weaken a MUST to make a gate pass. -->

| Req ID | MoSCoW | Source | Requirement | Layers | Evidence | Status |
|---|---|---|---|---|---|---|
| SEC-001 | MUST | README security contract | Never print, log, commit, or place API tokens in URLs; do not retain live licensed payloads | L2, L3, L5 | `test_sops_env.py`; CI secret scan; Bandit; receipt-only live fixtures | Covered |
| ID-001 | MUST | Carrier Intel PRD FR-01 | Resolve DOT, docket, VIN, SCAC, and text intent deterministically | L3 | `test_search_type.py`, including Hypothesis properties | Covered |
| EVID-001 | MUST | skill eval specs | Keep source, as-of time, missing evidence, and next action explicit | L3, L7 | `test_skills.py`; all 26 `eval-spec.yaml` files | Covered structurally; semantic runner is P1 |
| POL-001 | MUST | Risk Engine skill | A named human/customer policy owns the decision; missing evidence never silently passes | L3, L7 | `test_handlers_risk_engine.py` vetting policy cases; eval specs | Covered |
| TIER-001 | MUST | plugin PRDs FR tier gates | Gate every public tool before handler/API execution and return structured upgrade context | L3, L6 | `test_tier_gate.py`; five-server stdio tier tests | Covered |
| API-001 | MUST | shared API contract | Use the shared hybrid API contract and exact wire parameter names | L3, L4 | `test_api_contract.py`; handler transport tests | Covered |
| ERR-001 | MUST | plugin PRDs | Distinguish auth, access, not-found, throttling, timeout, and response drift | L3, L4 | handler suites; Watchdog transport matrix | Covered |
| BATCH-001 | SHOULD | API Bridge PRD FR-01 | Bound batches, isolate record failures, and reconcile totals | L3, L4 | `TestBulkLookup`; batch cap and result totals | Partial: retry/checkpoint behavior remains workflow-owned |
| RISK-001 | MUST | Risk Engine PRD FR-01 | Modeled risk stays bounded and advisory with stable factor bands | L3 | risk handler tests and `TestRiskFactorBoundaries` | Covered |
| QUAL-001 | MUST | Risk Engine PRD FR-02 | Preserve policy, threshold, observed value, result, missing evidence, and override | L3 | vetting and qualification report handler tests | Covered |
| REPORT-001 | MUST | Ops Reporter PRD | Preserve upstream facts, provenance, missing sections, and disclaimer | L3 | `test_handlers_ops_reporter.py`; PDF tests | Covered |
| EXPORT-001 | SHOULD | Ops Reporter journey | Return explicit formats and curated, safe exports; reject unsupported formats | L3 | CSV tests; invalid-format regression | Covered |
| WATCH-001 | MUST | Watchdog PRD | Alert feed is unavailable without a published route; configuration is not delivery proof | L3, L4 | `TestGetAlerts`; corrected user journey | Covered |
| EVENT-001 | SHOULD | Watchdog skill/eval specs | Supplied events carry provenance and consequential events are refetched | L7 | skill/eval specs | Partial: semantic eval runner is P1 |
| TMS-001 | MUST | API Bridge PRD FR-03/04 | Import translates locally without network; export maps fetched data; no unsupported write/diff claim | L3, L4 | `TestTmsSync`; corrected PRD | Covered |
| WEBHOOK-001 | MUST | API Bridge PRD FR-05 | Webhook CRUD is explicitly local, validates URLs, and does not claim delivery | L3 | `TestWebhookManage`; corrected PRD | Covered |
| COMP-001 | MUST | compliance skills | A point-in-time snapshot is not represented as historical drift or continuous monitoring | L3, L7 | Watchdog unavailable-route regression; skill contract tests | Covered |
| COMPAT-001 | MUST | MODEL-COMPATIBILITY.md | Runtime is provider-neutral and five servers expose matching MCP schemas | L2, L4, L6 | model SDK import scan; root config test; manifest parity; stdio handshake/call tests | Covered |

Existing plugin-local `FR-*` identifiers are ambiguous across five PRDs. New
cross-repo requirements use the namespace above; future PRD edits should cite
these IDs or namespace local IDs by plugin.
