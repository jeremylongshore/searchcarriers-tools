# TMS Reconciliation Planner

**Produce a dry-run carrier change set with idempotent keys and rollback evidence.**

`searchcarriers-tms-connector` | SearchCarriers tier: **enterprise** | Version **0.3.0**

## The customer pain

Blind TMS overwrites destroy local fields, duplicate carriers, and turn stale API data into operational status.

## What this skill changes

Produce a dry-run carrier change set with idempotent keys and rollback evidence. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Carrier operations, data, integration, and TMS teams.
- **When:** “Plan a dry-run sync from SearchCarriers into our TMS.”
- **Evidence:** GET /api/v3/company/{dot}; GET /api/v2/company/{dot}/qualification-reports; local TMS adapter.
- **Customer receives:** Run ID, DOT key, source/as-of, before/after diff, protected fields, conflict reason, action, result, and rollback reference.

## Decision contract

Return NO CHANGE, PROPOSED, APPLIED, PARTIAL, or ROLLED BACK per record.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. Ambiguous DOTs, missing required evidence, or a stale snapshot become conflicts; never auto-create from a name match.

## Operational follow-through

Review the dry run, apply approved changes, reconcile reads after writes, and preserve rollback receipts.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
