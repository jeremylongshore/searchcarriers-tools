# Carrier Watch Operations

**Manage company watch types and turn supplied change events into review work.**

`searchcarriers-watchdog` | SearchCarriers tier: **proplus** | Version **0.3.0**

## The customer pain

Teams assume a configured watch guarantees alerts even though the public API exposes watch state but no alert-feed endpoint.

## What this skill changes

Manage company watch types and turn supplied change events into review work. The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** Compliance and operations teams responsible for change follow-up.
- **When:** “Watch DOT 1234567 for details and inspections, then verify read-back.”
- **Evidence:** MCP tools: manage_watchlist, get_alerts, route_alert, monitor_compliance; GET/POST /api/v1/company/{dot}/watch.
- **Customer receives:** DOT, requested/current watch types, API result, event provenance, current compliance snapshot, delivery attempt, and as-of.

## Decision contract

Return WATCH CONFIGURED, WATCH REMOVED, REVIEW EVENT, or DELIVERY FAILED. Never report no alerts from an unavailable feed.

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. get_alerts endpoint_unavailable means unavailable, not zero events. Delivery failure does not undo watch state.

## Operational follow-through

Fix the external event source or delivery channel and retain a retry receipt.

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
