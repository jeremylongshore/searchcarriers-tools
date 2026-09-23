# Resumable Carrier Batch Runner

**Process a carrier panel with bounded concurrency, per-record receipts, and safe restart.**

`searchcarriers-bulk-processor` | SearchCarriers tier: **smb** | Version **0.3.0**

## The customer pain

Large panels fail partially because of rate limits, bad identifiers, or tier errors; rerunning everything wastes quota and hides which records changed.

## What this skill changes

Process a carrier panel with bounded concurrency, per-record receipts, and safe restart. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Carrier operations, data, integration, and TMS teams.
- **When:** “Refresh our 500-carrier panel and make the run resumable.”
- **Evidence:** GET /api/v1/export; GET /api/v3/company/{dot}; GET /api/v2/company/{dot}/qualification-reports.
- **Customer receives:** Input hash, run ID, per-DOT status, response source/as-of, attempts, error class, checkpoint, and final success/review/failure counts.

## Decision contract

Return COMPLETE, PARTIAL, or FAILED with a machine-readable error manifest; never discard successful rows because one carrier failed.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. Unknown DOTs and permanent 4xx errors stay in the manifest. A 429 or 5xx is retryable within a bounded budget.

## Operational follow-through

Resume from the checkpoint, then route completed evidence into qualification or export.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
