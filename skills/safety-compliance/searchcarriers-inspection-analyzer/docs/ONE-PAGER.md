# Inspection Pattern Analyzer

**Find repeat inspection and violation patterns with exposure-aware evidence.**

`searchcarriers-inspection-analyzer` | SearchCarriers tier: **pro** | Version **0.3.0**

## The customer pain

Raw violation totals punish larger fleets and tiny samples make percentages look decisive.

## What this skill changes

Find repeat inspection and violation patterns with exposure-aware evidence. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Safety, compliance, and carrier-management teams.
- **When:** “Analyze two years of inspections for repeated vehicle and driver issues.”
- **Evidence:** GET /api/v1/company/{dot}/inspections; GET /api/v1/company/{dot}/out-of-service-orders; GET /api/v3/company/{dot}?fields=inspections,oos_percents.
- **Customer receives:** Window, inspection count, violations, OOS counts and denominators, repeat categories, trend basis, formal orders, and coverage gaps.

## Decision contract

Return STABLE, DETERIORATING, IMPROVING, or INSUFFICIENT EXPOSURE only when the data supports that comparison.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. No inspections means insufficient exposure. Missing violation detail prevents category conclusions.

## Operational follow-through

Review repeat severe patterns, recent formal orders, or a worsening trend with a safety specialist before qualification.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
