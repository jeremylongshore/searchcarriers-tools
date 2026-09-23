# Persona Coverage — searchcarriers-tools

| ID | Persona | Critical flows | Evidence | Coverage |
|---|---|---|---|---|
| PER-001 | Freight broker / load planner | search, identity resolution, profile, qualification, compare | Carrier Intel, Risk Engine, Ops Reporter handler suites | 5/5 (100%) |
| PER-002 | Compliance or safety analyst | evidence review, named policy, exception handling, compliance snapshot | Risk Engine and Watchdog tests; eval specs | 4/4 (100%) |
| PER-003 | Operations manager | panel lookup, watch configuration, external event triage, digest/export | API Bridge/Watchdog tests; workflow eval specs | 3/4 (75%): semantic event triage pending |
| PER-004 | IT director / systems integrator | health, bulk refresh, TMS translation, webhook configuration, rollback boundary | API Bridge handler and contract tests | 4/4 (100%) |
| PER-005 | Dispatcher / pickup verifier | identity anomaly hold, callback evidence, release/escalate | fraud/contact skill eval specs | 2/3 (67%): semantic runner pending |
| PER-006 | Audit or management report consumer | stable evidence snapshot, provenance, missing evidence, approved handoff | report/PDF tests and eval specs | 3/4 (75%): UAT semantics pending |

The named examples Sarah Chen, Mike Rodriguez, and David Kim map to PER-001,
PER-003, and PER-004. This registry keeps their responsibilities stable across
plugin-specific journey documents.
