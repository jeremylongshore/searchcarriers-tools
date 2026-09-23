# Carrier Relationship Mapper

**Map evidence of shared equipment and related company records without declaring common control.**

`searchcarriers-entity-mapper` | SearchCarriers tier: **pro** | Version **0.3.0**

## The customer pain

Fraud investigations often overstate weak shared attributes, and common addresses or service providers create noisy links.

## What this skill changes

Map evidence of shared equipment and related company records without declaring common control. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Carrier sourcing, brokerage operations, and identity-review teams.
- **When:** “Map companies connected to DOT 1234567 through shared VINs.”
- **Evidence:** GET /api/v3/company/{dot}; GET /api/v3/company/{dot}/equipment; GET /api/v1/search/by-vin/{vin}.
- **Customer receives:** Seed identity, related DOT, shared VIN or API-provided association, dates where present, source route, and confidence rationale.

## Decision contract

Return CONFIRMED LINK only for an exact shared identifier, POSSIBLE LINK for weaker API evidence, and UNRESOLVED when evidence is incomplete.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. No related results is not proof of independence; state the coverage limits and unsearched identifiers.

## Operational follow-through

Manually verify high-impact links through official records and trusted contacts before changing carrier status.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
