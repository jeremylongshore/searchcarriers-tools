# User Journey Coverage — searchcarriers-tools

| ID | Journey | Essential path | Test mapping | Status |
|---|---|---|---|---|
| JRN-001 | Source to tender decision | search → resolve → profile → evidence → named qualification → report → human decision | Carrier Intel/Risk Engine/Ops Reporter suites | Covered at handler/contract layers |
| JRN-002 | Pickup identity anomaly | mismatch → hold → compare evidence → trusted callback → release/escalate | skill eval specs | Partial: semantic runner pending |
| JRN-003 | Batch panel requalification | validate/dedupe → bounded lookup → isolated failures → totals → review/export | API Bridge bulk tests + workflow eval | Partial: checkpoint/retry remains workflow-owned |
| JRN-004 | Watch setup and external event review | configure watch → readback → receive external event → validate → route payload | Watchdog and webhook tests | Covered through local handoff boundary |
| JRN-005 | Insurance cancellation response | validate event → refetch evidence → classify → assign hold/owner | insurance workflow eval | Partial: semantic runner pending |
| JRN-006 | TMS reconciliation and application | translate → snapshot → dry run → approval → idempotent apply → reread/rollback | translation tests + workflow eval | Partial: external TMS adapter intentionally absent |
| JRN-007 | Compliance dashboard | pin panel/policy → collect evidence → separate decision/errors → age → assign owner | handler tests + dashboard eval | Partial: semantic runner pending |
| JRN-008 | Auditable report/export | preserve verdict → expose unknowns → provenance → safe export → delivery | report, CSV, PDF tests | Covered through artifact generation |
| JRN-009 | Degraded-service recovery | tier denial / 401 / 403 / 404 / 429 / timeout → bounded response | transport, tier, and handler error tests | Covered |

The repository has no browser or database surface, so journey evidence stops at
the MCP/artifact boundary. External delivery, TMS writes, and stakeholder UAT
belong to deployment-specific adapters and acceptance runs.
