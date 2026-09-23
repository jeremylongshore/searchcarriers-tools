# Safety Evidence Interpreter

**Explain a carrier safety record without inventing a universal safety score.**

`searchcarriers-safety-scorer` | SearchCarriers tier: **free** | Version **0.3.0**

## The customer pain

Teams confuse FMCSA safety ratings, BASIC information, crashes, and missing data, leading to false passes and false rejections.

## What this skill changes

Explain a carrier safety record without inventing a universal safety score. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Safety, compliance, and carrier-management teams.
- **When:** “Explain the safety record for DOT 1234567 and show what is unknown.”
- **Evidence:** GET /api/v3/company/{dot}?fields=safety,basic_scores,risk_factors; GET /api/v3/company/{dot}/crashes.
- **Customer receives:** Rating with date, safety measures with observation windows, crash facts, inspection exposure, missing fields, and source/as-of.

## Decision contract

Return CLEAR EVIDENCE, CONCERN, or REVIEW REQUIRED under the caller policy; do not create an official score.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. Not rated is not satisfactory or unsafe. Zero inspections is low exposure, not proof of safety.

## Operational follow-through

Escalate concerns to the caller policy or SearchCarriers qualification; verify official status when the decision is consequential.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
