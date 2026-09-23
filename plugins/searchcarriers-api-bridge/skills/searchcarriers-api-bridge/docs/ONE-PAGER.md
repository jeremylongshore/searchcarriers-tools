# Carrier Integration Operator

**Run API health, resumable bulk lookup, dry-run TMS reconciliation, and local downstream webhook configuration.**

`searchcarriers-api-bridge` | SearchCarriers tier: **smb** | Version **0.3.0**

## The customer pain

Integration failures become silent data drift when health, partial success, local webhook ownership, and rollback are not explicit.

## What this skill changes

Run API health, resumable bulk lookup, dry-run TMS reconciliation, and local downstream webhook configuration. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Integration owners connecting carrier evidence to internal systems.
- **When:** “Health-check the API and prepare a resumable 500-carrier refresh.”
- **Evidence:** MCP tools: api_health, bulk_lookup, tms_sync, webhook_manage.
- **Customer receives:** Route health without records, batch run receipts, TMS diff/result, local webhook configuration path, errors, and rollback evidence.

## Decision contract

Return HEALTHY/DEGRADED, COMPLETE/PARTIAL, or PROPOSED/APPLIED with exact scope.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. 403 means tier/access; 429 honors Retry-After; partial runs retain successful records and an error manifest.

## Operational follow-through

Retry only transient failures, review TMS conflicts, and test downstream delivery separately.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
