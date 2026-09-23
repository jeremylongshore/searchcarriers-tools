# Carrier Review Queue Digest

**Turn supplied or fetched qualification results into a prioritized human review queue.**

`searchcarriers-daily-vetting-digest` | SearchCarriers tier: **pro** | Version **0.3.0**

## The customer pain

Daily summaries become misleading when they collapse missing evidence into passes or imply email delivery occurred.

## What this skill changes

Turn supplied or fetched qualification results into a prioritized human review queue. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Carrier onboarding managers running a daily review queue.
- **When:** “Build today’s refrigerated-policy carrier review digest.”
- **Evidence:** GET /api/v2/company/{dot}/qualification-reports; Ops Reporter output.
- **Customer receives:** Qualification name, carrier, verdict, reasons, missing evidence, as-of, owner, and next action.

## Decision contract

Return DIGEST READY or INCOMPLETE with counts that reconcile to detail rows.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. Unavailable results remain unresolved and are excluded from pass counts.

## Operational follow-through

Assign Fail and Review items, then send through an explicitly configured delivery system.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
