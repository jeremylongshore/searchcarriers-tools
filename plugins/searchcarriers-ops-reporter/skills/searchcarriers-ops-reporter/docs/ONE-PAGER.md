# Carrier Decision Report Builder

**Turn carrier evidence into an auditable report or export without changing the underlying verdict.**

`searchcarriers-ops-reporter` | SearchCarriers tier: **pro** | Version **0.3.0**

## The customer pain

Pretty reports can conceal missing evidence, stale data, and the difference between API facts and analyst judgment.

## What this skill changes

Turn carrier evidence into an auditable report or export without changing the underlying verdict. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Analysts and managers who review or distribute carrier decisions.
- **When:** “Build an audit-ready vetting report from these tool outputs.”
- **Evidence:** MCP tools: generate_report, generate_fleet, generate_compare, export_data.
- **Customer receives:** Subject identity, purpose, evidence sections, policy/model disclosure, missing evidence, human decision, source/as-of, and export manifest.

## Decision contract

Return READY or INCOMPLETE; formatting may not upgrade REVIEW to PASS.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. If an upstream section failed, mark the report incomplete and include the exact recovery action.

## Operational follow-through

Have the decision owner sign off, then retain the report according to internal policy.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
