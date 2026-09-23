# Approved TMS Change Application

**Apply an approved carrier change set idempotently and prove the result.**

`searchcarriers-tms-auto-sync` | SearchCarriers tier: **enterprise** | Version **0.3.0**

## The customer pain

Automated status writes can strand loads or overwrite local ownership fields when events are stale, duplicated, or incomplete.

## What this skill changes

Apply an approved carrier change set idempotently and prove the result. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Enterprise TMS and carrier-master-data owners.
- **When:** “Apply this approved SearchCarriers change set to our TMS and verify rereads.”
- **Evidence:** API Bridge tms_sync; current SearchCarriers company/qualification evidence; local TMS adapter.
- **Customer receives:** Approval, event/as-of, idempotency key, before/after, protected fields, write result, reread result, and rollback receipt.

## Decision contract

Return APPLIED, NOOP, CONFLICT, or ROLLED BACK per carrier.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. No approval, stale source data, ambiguous identity, or reread mismatch prevents completion.

## Operational follow-through

Resolve conflicts and rerun only failed idempotency keys.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
