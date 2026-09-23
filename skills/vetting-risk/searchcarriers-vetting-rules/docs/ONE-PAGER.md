# Policy Qualification Runner

**Apply named company or customer criteria and return reproducible Pass, Review, or Fail evidence.**

`searchcarriers-vetting-rules` | SearchCarriers tier: **proplus** | Version **0.3.0**

## The customer pain

Informal checklists drift between analysts, while hidden defaults create decisions no one can audit.

## What this skill changes

Apply named company or customer criteria and return reproducible Pass, Review, or Fail evidence. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Carrier onboarding, risk, compliance, and brokerage operations teams.
- **When:** “Run our refrigerated-customer qualification for DOT 1234567.”
- **Evidence:** GET /api/v2/company/{dot}/qualification-reports; GET /api/v3/company/{dot}?fields=vetting_report,risk_factors,authorities,insurance,safety,operation.
- **Customer receives:** Qualification name, criteria/as-of, per-rule observed value and source, Pass/Review/Fail result, missing evidence, and override record.

## Decision contract

Return the upstream or deterministic policy verdict. Missing evidence must follow the rule policy and may never silently pass.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. If no named policy is supplied, ask for one or return evidence-only REVIEW; do not invent industry-standard thresholds.

## Operational follow-through

Send failures to remediation, reviews to a human queue, and store the evidence snapshot with the decision.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
