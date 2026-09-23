# Trusted Contact Consistency Check

**Compare supplied contact details with carrier records and define an independent callback step.**

`searchcarriers-contact-verifier` | SearchCarriers tier: **pro** | Version **0.3.0**

## The customer pain

Spoofed email, caller ID, and recently changed FMCSA contacts make a matching string insufficient proof of identity.

## What this skill changes

Compare supplied contact details with carrier records and define an independent callback step. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Carrier operations, data, integration, and TMS teams.
- **When:** “The rate confirmation came from a new email; compare it with DOT 1234567.”
- **Evidence:** GET /api/v3/company/{dot}?fields=contact,risk_factors; GET /api/v1/company/{dot}/contact-details.
- **Customer receives:** Supplied contact, returned contact, comparison result, freshness/change evidence, verification channel, missing fields, and as-of.

## Decision contract

Return CONSISTENT, MISMATCH, or UNVERIFIED. Never claim that the API alone verified the person communicating.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. Missing contacts are UNVERIFIED. Generic or VoIP metadata may raise review but is not proof of fraud.

## Operational follow-through

Call a known number, confirm dispatch and equipment details, and hold the load until a material mismatch is resolved.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
