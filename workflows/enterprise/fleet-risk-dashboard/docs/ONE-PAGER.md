# Fleet Risk Exception Dashboard

**Rank a carrier panel by actionable evidence exceptions without hiding uncertainty behind a composite score.**

`searchcarriers-fleet-risk-dashboard` | SearchCarriers tier: **enterprise** | Version **0.3.0**

## The customer pain

Large panels need triage, but opaque scores and missing-data rows can send analysts to the wrong carriers.

## What this skill changes

Rank a carrier panel by actionable evidence exceptions without hiding uncertainty behind a composite score. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Enterprise carrier-risk leaders managing large carrier panels.
- **When:** “Build this week’s fleet exception dashboard for our carrier panel.”
- **Evidence:** Carrier Intel, Risk Engine, qualification reports, and Ops Reporter MCP tools.
- **Customer receives:** Panel hash/run, policy, per-carrier verdict, evidence exceptions, modeled-factor disclosure, missing data, freshness, owner, and action.

## Decision contract

Return READY, PARTIAL, or STALE; the top queue is based on explicit exceptions and policy results.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. Missing and stale records have their own priority queue and do not receive reassuring scores.

## Operational follow-through

Assign exception owners, refresh stale records, and retain the run snapshot for comparison.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
