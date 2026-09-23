# Test Audit — searchcarriers-tools

**Date:** 2026-09-23

**Classification:** Python MCP service + plugin/skill/agent collection

**Initial grade:** C (68/100)

**Post-implementation grade:** B (86/100)

The initial 223-test local suite was reliable at its existing scope, but it
proved private handlers and package structure more often than the public process
boundary or customer outcomes. CI skipped tests on pushes to `main`, did not run
Ruff, did not enforce coverage, and had no SAST or dependency audit. Twenty-six
behavioral eval specifications existed without a traceability layer or runner.

## Seven-layer result

| Layer | Before | Implemented result |
|---|---|---|
| L1 hooks and CI | Partial | Validate and two-version Test jobs run on PRs and `main`; live smoke has a scheduled/manual workflow |
| L2 static analysis | Partial | Ruff, Bandit, pip-audit, validation, secret scan, absolute-path scan, and harness conformance in CI |
| L3 unit/function | Strong but unmeasured | 80% branch-enabled combined coverage gate, property tests, factor boundaries, architecture tests |
| L4 integration/contract | Handler-heavy | Five real stdio processes initialize, list, reject unknown tools, enforce tiers, and match manifests |
| L5 system quality | Weak | Security gates and a five-second MCP startup budget; mutation baseline remains P1 |
| L6 smoke | Live tests skipped | Local five-server MCP smoke is blocking; protected live API lane is separate |
| L7 acceptance | Spec-only | RTM, persona, and journey maps added; semantic eval runner remains P1 |

## Deterministic evidence

- Test suite: 304 passed, 27 live tests skipped without a protected credential.
- Coverage: 80.32% combined line/branch coverage; policy floor 80%.
- Ruff: pass after formatting and import-order repair.
- Bandit: pass.
- pip-audit: pass after upgrading pip; editable local package excluded.
- Harness conformance: 23 pass, no failures in the baseline run. Nested plugin
  discovery is a known harness limitation; `scripts/validate.sh` covers all five.
- Harness scan: gitleaks, Syft, link, and README checks passed; optional OSV,
  Semgrep, Markdownlint, and j-rig receipt discovery remained advisory. The
  repository's direct deep validator and j-rig run passed all 26 skills with no
  warnings or errors; the harness cannot consume that output without a bundle.
- Harness heuristics incorrectly reported performance absent despite
  `tests/performance/test_mcp_startup_budget.py`, and migration absent despite
  the explicit no-database waiver. The executable pytest gate is authoritative.
- The bias scanner reported 109 patterns, including 103 broad substring checks.
  Review found these are predominantly contract assertions over structured
  payloads and documentation; the heuristic is advisory pending mutation data.
- Upstream currency reported 18 stale pins inside the vendored harness. This is
  a harness release-maintenance issue and does not change SearchCarriers code.

## Material defects corrected

- Watchdog documentation no longer invents three alerts after the code returns
  `endpoint_unavailable` for the unpublished alert-feed route.
- API Bridge now documents the actual local webhook and TMS translation
  boundaries instead of promising remote CRUD, live diffs, or TMS writes.
- Carrier profile documentation now matches the one-request v3 implementation.
- Risk band documentation now matches the implemented low/medium/elevated/high
  thresholds.
- Unsupported Ops Reporter export formats now fail explicitly before any API
  request instead of silently changing the requested format to JSON.

## Remaining gaps

P1: automate the 26 semantic eval specifications; baseline mutation testing;
configure the protected live-test environment secret; measure optional harness
scanners before promoting them from advisory. P2: add static typing and a
blocking Markdown/link gate.

## Harness notes

The v1.4.0 non-Node installer omitted its schema directory and several wrapper
verbs. The vendored installation was repaired by adding the release schemas and
exposing `classify`, `conform`, `audit`, `scan`, and `currency`. The harness also
generates ignored CRAP/architecture reports during commands advertised as
read-only; those generated files remain outside version control.
