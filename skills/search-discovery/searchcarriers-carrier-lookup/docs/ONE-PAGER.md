# Carrier Candidate Finder

**Find a defensible carrier shortlist for a named company, identifier, geography, fleet need, insurance requirement, or lane.**

`searchcarriers-carrier-lookup` | SearchCarriers tier: **free** | Version **0.3.0**

## The customer pain

A name-only search returns false matches, while a broad search returns candidates that cannot serve the load.

## What this skill changes

Find a defensible carrier shortlist for a named company, identifier, geography, fleet need, insurance requirement, or lane. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Carrier sourcing, brokerage operations, and identity-review teams.
- **When:** “Find dry-van carriers with at least 10 power units on an Alabama-to-Texas lane.”
- **Evidence:** GET /api/v3/search; GET /api/v1/search/scac; GET /api/v1/search/by-vin/{vin}.
- **Customer receives:** DOT/docket identity, legal name, location, fleet facts, selected filters, pagination metadata, and an as-of timestamp.

## Decision contract

Return MATCH, POSSIBLE MATCH, or NO MATCH for identity; for sourcing return a ranked candidate list without calling it approved.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. An empty page means no candidates under those filters. A missing field is unknown, never false or zero.

## Operational follow-through

Resolve ambiguous identities, open the selected carrier profile, then run authority, insurance, and policy qualification checks.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
