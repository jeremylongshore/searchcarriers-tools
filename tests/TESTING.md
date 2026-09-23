# Testing Context — searchcarriers-tools
<!-- TESTING.md schema v1. Managed by audit-tests + implement-tests. -->

## Classification (policy)
Repo type: service + plugin collection
Primary language(s): python, markdown, yaml, json
Applicable layers: L1, L2, L3, L4-integration, L4-contract, L5-security, L5-performance, L6-smoke, L7-acceptance-spec
Waived layers: L4-migration (no database or schema migrations), L5-a11y (no UI), L6-browser (no browser surface)
Compliance overlay: none

## Thresholds (policy, hash-pinned)
coverage.line: 80
coverage.branch: 65
mutation.kill_rate: 70 (advisory until baseline exists)
crap.prod_max: 30
crap.test_max: 15
crap.project_avg: 10
flaky.tolerance: 0/3runs
test.complexity_ceiling: 15
perf.mcp_startup_seconds: 5
personas.flow_coverage_min: 80
journeys.step_coverage_min: 85

## Installed gates (observational)
L0: vendored @intentsolutions/audit-harness 1.4.0
L1: GitHub Actions Validate + Test on pull requests and main; scheduled/manual live smoke
L2: Ruff format/lint, Bandit, pip-audit, plugin/skill validation, secret and absolute-path scans
L3: pytest, pytest-cov branch coverage, Hypothesis property tests, architecture fitness tests
L4-integration: respx HTTP boundary tests and generic MCP stdio process tests
L4-contract: shared API contract tests, manifest/tool-schema parity, scheduled live API contract lane
L5-security: Bandit + pip-audit; harness scan remains advisory
L5-performance: bounded local MCP startup test
L6-smoke: five-server initialize/list/call stdio smoke; live upstream smoke runs separately
L7-acceptance-spec: 26 eval-spec files mapped through RTM; semantic eval runner remains P1

## Frameworks (observational)
unit: pytest 9.x
property: Hypothesis 6.x
http integration: respx 0.21+
protocol integration: MCP Python SDK 1.x
coverage: coverage.py 7.x via pytest-cov 7.x
security: Bandit + pip-audit

## Last audit (observational)
date: 2026-09-23
grade: B (86/100)
auditor: audit-tests + implement-tests
p0_gaps: 0
p1_gaps: 4
  - 26 behavioral eval specifications do not yet have an automated judge runner
  - mutation testing has a policy floor but no measured baseline or CI lane
  - live API smoke requires the protected SEARCHCARRIERS_API_KEY environment secret
  - harness scan remains advisory while optional scanners are unavailable
p2_gaps: 2
  - no static type checker
  - no Markdown prose/link gate in blocking CI

## Traceability (observational, updated by audit-tests)
rtm.total_requirements: 18
rtm.by_moscow:
  must: 14 (14 covered, 0 uncovered)
  should: 4 (2 covered, 2 partial)
  could: 0
  wont: 0
rtm.orphaned_tests: legacy tests remain mapped by subsystem rather than inline requirement tags
personas.declared: 6
personas.under_threshold: 2 (dispatcher and report consumer depend on semantic eval automation)
journeys.declared: 9
journeys.fully_covered: 3
journeys.partial: 6

## Hash manifest
version: 1
last_init: 2026-09-23 by audit-harness init
protected_files:
  - tests/TESTING.md policy sections
  - tests/RTM.md MoSCoW assignments
  - pyproject.toml coverage policy
  - .github/workflows/*.yml
