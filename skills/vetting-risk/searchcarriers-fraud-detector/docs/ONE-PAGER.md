# Carrier Identity Risk Triage

**Triage carrier identity anomalies and prescribe independent verification without accusing a carrier of fraud.**

`searchcarriers-fraud-detector` | SearchCarriers tier: **pro** | Version **0.3.0**

## The customer pain

Identity theft, spoofed contacts, unauthorized USDOT use, and carrier-involved theft defeat single-source checks.

## What this skill changes

Triage carrier identity anomalies and prescribe independent verification without accusing a carrier of fraud. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Carrier onboarding, risk, compliance, and brokerage operations teams.
- **When:** “A dispatcher changed the pickup address; triage DOT 1234567 before tender.”
- **Evidence:** GET /api/v3/company/{dot}?fields=contact,authorities,insurance,equipment,risk_factors; GET /api/v3/company/{dot}/equipment; GET /api/v1/search/by-vin/{vin}.
- **Customer receives:** Claimed identity, authoritative API identity, exact mismatches, timing anomalies, shared identifiers, verification performed, missing evidence, and source/as-of.

## Decision contract

Return NO MATERIAL ANOMALY OBSERVED, HOLD FOR VERIFICATION, or STOP AND ESCALATE. Never label an entity fraudulent from API data alone.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. Missing contact or equipment evidence increases uncertainty; it does not prove fraud.

## Operational follow-through

Verify through independent contact channels, preserve evidence, and follow FMCSA reporting guidance when misuse is suspected.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
