# Fleet Identity Reconciler

**Reconcile a VIN, the carrier claiming it, and the companies observed operating it.**

`searchcarriers-vin-decoder` | SearchCarriers tier: **pro** | Version **0.3.0**

## The customer pain

A truck at pickup may not match the approved carrier, while leased or transferred equipment can create legitimate multi-carrier history.

## What this skill changes

Reconcile a VIN, the carrier claiming it, and the companies observed operating it. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Carrier sourcing, brokerage operations, and identity-review teams.
- **When:** “Does VIN 1M8GDM9AXKP042788 match the carrier we approved?”
- **Evidence:** GET /api/v1/search/by-vin/{vin}; GET /api/v3/company/{dot}/equipment.
- **Customer receives:** VIN, claimed DOT, observed DOT records, equipment details, inspection dates where returned, and exact match/mismatch status.

## Decision contract

Return MATCH, MISMATCH, MULTIPLE OBSERVED CARRIERS, or INSUFFICIENT EVIDENCE.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. A VIN with no result is unresolved; malformed VINs stop before the API call.

## Operational follow-through

For a mismatch, stop tendering and verify truck, trailer, plate, driver, and dispatch through the original trusted contact.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
