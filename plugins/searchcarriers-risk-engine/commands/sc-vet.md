# /sc-vet — Named Carrier Qualification

When the user runs `/sc-vet [DOT]`, fetch SearchCarriers personal and team
qualification reports for that USDOT number. When the user supplies a complete
local policy, evaluate that policy explicitly. Never select hidden “standard”
thresholds.

## Parse the input

The first argument is a USDOT number. Resolve names or docket numbers through
`carrier_lookup` before qualification.

Optional flags:

| Flag | Value | Purpose |
|---|---|---|
| `--qualification` | exact name | Select one upstream personal/team qualification. |
| `--policy` | JSON file or supplied object | Apply a complete caller-owned policy through `vetting_check`. |
| `--format` | `full` or `summary` | Control display detail; never remove failed or missing evidence. |

If neither `--qualification` nor `--policy` is supplied, call
`qualification_reports` and list the available named results. Do not guess
which qualification governs the load.

## Execute

1. Call `qualification_reports` with `dot_number`.
2. Match `--qualification` by exact name. If it is ambiguous or absent, return
   Review and show the available names.
3. If `--policy` is supplied, validate all six required keys before calling
   `vetting_check`: `operating_status`, `min_insurance_coverage`,
   `max_oos_rate`, `max_crash_rate_per_pu`, `authority_active`, and
   `mcs150_current`.
4. Preserve each observed value, threshold, source, evidence item, missing
   field, and as-of timestamp.

## Display results

```text
CARRIER QUALIFICATION — DOT {dot_number}
Carrier:        {legal_name}
Qualification:  {exact qualification or caller policy name}
As of:          {timestamp}

VERDICT: PASS | REVIEW | FAIL

Rule | Result | Observed | Threshold | Source | Reason
-----|--------|----------|-----------|--------|-------
...  | ...    | ...      | ...       | ...    | ...

Missing evidence: {none or explicit list}
Next action: {owner plus action}
```

- **PASS** means the carrier met this named policy at this as-of time.
- **REVIEW** means the policy or evidence requires a human decision.
- **FAIL** means at least one rule failed under this named policy.

Never rewrite Review as Pass, and never present the legacy `risk_score` as an
official rating or qualification.

## Error handling

- `invalid_policy`: list the missing keys and stop before API evaluation.
- No named qualification: list available names and request an exact choice.
- Missing evidence: follow the named rule behavior; absent data never silently passes.
- `401`, `403`, `404`, `422`, `429`, timeout: preserve the error class and use
  the recovery behavior in `API-DISCOVERY.md`.

## Follow-up

Send Fail items to remediation, Review items to the named decision owner, and
store the rule-level evidence snapshot with any final onboarding decision.
