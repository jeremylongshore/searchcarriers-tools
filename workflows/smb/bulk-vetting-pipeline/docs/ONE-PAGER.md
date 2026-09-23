# Bulk Carrier Qualification Pipeline

**Run named policy qualification across a carrier list with restartable evidence.**

`searchcarriers-bulk-vetting-pipeline` | SearchCarriers tier: **smb** | Version **0.3.0**

## The customer pain

A single bad row or rate limit should not invalidate hundreds of carrier decisions, and default criteria should not be invented.

## What this skill changes

Run named policy qualification across a carrier list with restartable evidence. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Small and midsize brokerages qualifying carrier lists at scale.
- **When:** “Vet this CSV using our automotive-customer qualification.”
- **Evidence:** GET /api/v2/company/{dot}/qualification-reports; bulk_lookup; report/export tools.
- **Customer receives:** Run ID/input hash, qualification version, per-DOT verdict/evidence/as-of, attempts, errors, and reconciled totals.

## Decision contract

Return COMPLETE, PARTIAL, or FAILED; missing evidence follows the named policy and never silently passes.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. Invalid IDs and permanent errors enter review; transient errors retry within a bound.

## Operational follow-through

Resume failed rows, assign Review/Fail cases, and publish the evidence manifest with the output.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
