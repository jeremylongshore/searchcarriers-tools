# Carrier Intel MCP Operator

**Use the Carrier Intel MCP tools for identifier resolution, filtered sourcing, profiles, relationship evidence, and fleet summaries.**

`searchcarriers-carrier-intel` | SearchCarriers tier: **free** | Version **0.3.0**

## The customer pain

Operators need the right tool and route without manually translating API versions or treating search candidates as approved carriers.

## What this skill changes

Use the Carrier Intel MCP tools for identifier resolution, filtered sourcing, profiles, relationship evidence, and fleet summaries. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Operations teams that need one MCP surface for carrier research.
- **When:** “Use Carrier Intel to source van carriers on an Alabama-to-Texas lane.”
- **Evidence:** MCP tools: carrier_lookup, carrier_profile, entity_map, fleet_summary.
- **Customer receives:** Tool name/input, API version, identity, selected evidence, missing fields, pagination, and next required check.

## Decision contract

Return identity/candidate/fleet evidence only; qualification belongs to the named policy workflow.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. A tool error is evidence of unavailable data, not a negative carrier fact.

## Operational follow-through

Route selected carriers to authority, insurance, safety, or qualification review.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
