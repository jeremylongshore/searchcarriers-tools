# Operating Authority Verifier

**Verify that the identified entity has the authority required for the intended job.**

`searchcarriers-authority-checker` | SearchCarriers tier: **free** | Version **0.3.0**

## The customer pain

A valid DOT is not the same as active for-hire authority, and similar names or old dockets cause misidentification.

## What this skill changes

Verify that the identified entity has the authority required for the intended job. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Carrier onboarding, risk, compliance, and brokerage operations teams.
- **When:** “Can DOT 1234567 legally haul this for-hire property load?”
- **Evidence:** GET /api/v3/company/{dot}?fields=authorities,operation,insurance; GET /api/v1/authority/{docketNumber}/history.
- **Customer receives:** Legal identity, DOT/docket, required role, current authority type/status, history events, insurance linkage, and as-of timestamp.

## Decision contract

Return AUTHORIZED FOR STATED USE, NOT AUTHORIZED, or REVIEW REQUIRED.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. No authority record never becomes a pass. Mixed or unclear statuses require review.

## Operational follow-through

Stop the transaction when required authority is absent; otherwise continue to insurance and policy qualification.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
