# Compliance Snapshot Builder

**Produce a point-in-time carrier compliance snapshot and identify what must be rechecked.**

`searchcarriers-compliance-monitor` | SearchCarriers tier: **pro** | Version **0.3.0**

## The customer pain

One-time onboarding checks age immediately, and teams often mistake a current snapshot for continuous monitoring.

## What this skill changes

Produce a point-in-time carrier compliance snapshot and identify what must be rechecked. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Safety, compliance, and carrier-management teams.
- **When:** “Build a current compliance snapshot and tell me what is not continuously monitored.”
- **Evidence:** GET /api/v3/company/{dot}?fields=authorities,insurance,safety,oos_orders,operation,risk_factors; GET /api/v1/company/{dot}/watch.
- **Customer receives:** DOT status, authorities, insurance filings, safety/OOS evidence, watch state, missing data, policy source, and as-of timestamp.

## Decision contract

Return CURRENTLY CLEAR, ACTION REQUIRED, or REVIEW REQUIRED; separately state whether monitoring is configured.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. API or field absence creates REVIEW. Watch configuration without an alert feed is not proof that delivery is working.

## Operational follow-through

Set the appropriate watch types and define an external review cadence or notification input.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
