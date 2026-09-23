# Auditable Carrier Exporter

**Create a minimal, traceable carrier export that is safe to open and lawful to retain.**

`searchcarriers-data-exporter` | SearchCarriers tier: **pro** | Version **0.3.0**

## The customer pain

Exports lose field provenance, leak unnecessary contacts, or execute spreadsheet formulas when opened.

## What this skill changes

Create a minimal, traceable carrier export that is safe to open and lawful to retain. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Carrier operations, data, integration, and TMS teams.
- **When:** “Export our approved carrier panel to formula-safe CSV with provenance.”
- **Evidence:** GET /api/v1/export; GET /api/v3/company/{dot} with explicit fields.
- **Customer receives:** Selected fields, schema version, source routes, as-of, input hash, record count, errors, and retention/recipient note.

## Decision contract

Return READY, PARTIAL, or BLOCKED with output path and manifest; never imply a partial export is complete.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. Missing fields remain blank with a reason. 403 stops unsupported data; 429 resumes after Retry-After.

## Operational follow-through

Deliver through an approved internal channel and delete temporary API data under the organization retention policy.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
