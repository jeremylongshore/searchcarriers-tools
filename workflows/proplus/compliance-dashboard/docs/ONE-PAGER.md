# Carrier Panel Compliance Dashboard

**Build an as-of panel dashboard that exposes stale, missing, and high-priority evidence.**

`searchcarriers-compliance-dashboard` | SearchCarriers tier: **proplus** | Version **0.3.0**

## The customer pain

A green dashboard can hide old snapshots, low-exposure carriers, and failed API calls.

## What this skill changes

Build an as-of panel dashboard that exposes stale, missing, and high-priority evidence. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Compliance leaders responsible for a live carrier panel.
- **When:** “Build a weekly compliance dashboard for our approved panel.”
- **Evidence:** GET /api/v3/company/{dot}; GET /api/v2/company/{dot}/qualification-reports; company watch routes.
- **Customer receives:** Panel input hash, run/as-of, per-carrier evidence status, qualification, watch state, errors, and aging.

## Decision contract

Return CURRENT, PARTIAL, or STALE; collection failure is never green.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. Missing or old snapshots appear in a dedicated queue and do not count as compliant.

## Operational follow-through

Refresh failed/stale rows and assign policy reviews before relying on the dashboard.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
