# Risk Engine MCP Operator

**Use risk tools as transparent evidence and policy checks without presenting modeled scores as official ratings.**

`searchcarriers-risk-engine` | SearchCarriers tier: **pro** | Version **0.3.0**

## The customer pain

Composite scores and default thresholds can hide assumptions or be mistaken for FMCSA determinations.

## What this skill changes

Use risk tools as transparent evidence and policy checks without presenting modeled scores as official ratings. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Risk and onboarding teams applying explicit qualification policy.
- **When:** “Run the Risk Engine with our supplied carrier policy and show every rule.”
- **Evidence:** MCP tools: risk_score, vetting_check, insurance_check, compliance_audit; API v2 qualification reports when available.
- **Customer receives:** Tool/version, policy or model name, factors/rules, observed values, missing evidence, source/as-of, verdict, and next action.

## Decision contract

Return EVIDENCE, REVIEW, or the named policy verdict; never call a modeled risk score an official safety rating.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. Partial endpoint failure forces REVIEW for affected dimensions.

## Operational follow-through

Resolve failed evidence, obtain the named policy, or escalate reviews before onboarding.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
