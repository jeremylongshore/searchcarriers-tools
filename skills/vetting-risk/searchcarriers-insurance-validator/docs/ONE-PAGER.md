# Insurance Filing Reconciler

**Reconcile filed insurance evidence with the requirements for the exact entity, authority, cargo, and vehicle.**

`searchcarriers-insurance-validator` | SearchCarriers tier: **pro** | Version **0.3.0**

## The customer pain

Insurance minimums vary by operation, and certificates can be altered or inconsistent with filed coverage.

## What this skill changes

Reconcile filed insurance evidence with the requirements for the exact entity, authority, cargo, and vehicle. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Carrier onboarding, risk, compliance, and brokerage operations teams.
- **When:** “Validate insurance for a household-goods movement by DOT 1234567.”
- **Evidence:** GET /api/v3/company/{dot}?fields=insurance,authorities,operation; GET /api/v1/company/{dot}/insurances.
- **Customer receives:** Requirement source, operation facts, active filing evidence, coverage amount/type, effective/cancellation dates, gaps, conflicts, and as-of.

## Decision contract

Return MEETS STATED REQUIREMENT, DOES NOT MEET, or REVIEW REQUIRED. Do not apply one blanket minimum to every carrier.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. An active policy with missing amount or type is REVIEW. No returned record is not proof of no insurance until route/access errors are excluded.

## Operational follow-through

Call the insurer using independently sourced contact information when documents or filings conflict; stop tendering if required coverage cannot be confirmed.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
