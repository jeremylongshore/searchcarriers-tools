# Insurance Change Review

**Evaluate a supplied insurance change or current filing and create a bounded response.**

`searchcarriers-insurance-lapse-alert` | SearchCarriers tier: **proplus** | Version **0.3.0**

## The customer pain

A cancellation notice may be future-dated, replaced, stale, or unrelated to the required coverage, while false alarms disrupt loads.

## What this skill changes

Evaluate a supplied insurance change or current filing and create a bounded response. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Risk and operations teams responding to insurance changes.
- **When:** “Review this cancellation event for DOT 1234567 and check replacement coverage.”
- **Evidence:** GET /api/v3/company/{dot}?fields=insurance,authorities,operation; GET /api/v1/company/{dot}/insurances.
- **Customer receives:** Event source/time, current filing, replacement evidence, requirement source, affected loads, classification, owner, and deadline.

## Decision contract

Return NO CURRENT GAP, UPCOMING REVIEW, CURRENT GAP, or UNRESOLVED.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. An unavailable refetch or unknown requirement is UNRESOLVED, not clear.

## Operational follow-through

Hold affected tendering when required coverage cannot be confirmed and verify with the insurer through an independent contact.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
