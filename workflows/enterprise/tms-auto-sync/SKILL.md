---
name: searchcarriers-tms-auto-sync
description: Reconcile current carrier data into a TMS from a scheduled job or validated change event. Use when operating an audited carrier-data synchronization.
allowed-tools: Read,Grep,Bash(python:*)
metadata:
  tier: enterprise
version: 0.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Claude Code or another MCP-capable client; Python 3.10+; network access to searchcarriers.com; an appropriate SearchCarriers API subscription.
tags:
- searchcarriers
- motor-carrier
- workflow
---

# TMS carrier reconciliation

## Overview

> **API contract:** Use `API-DISCOVERY.md`. The public SearchCarriers API does
> not expose the alert-feed route assumed by earlier versions of this workflow.

This workflow reconciles current SearchCarriers data into a transportation
management system. Trigger it from an application-owned schedule or a validated
external notification. It never treats `get_alerts` as a source of change
events.

## Prerequisites

- Enterprise SearchCarriers subscription and valid API token
- API Bridge MCP server
- TMS credentials stored outside prompts, logs, and repository files
- Approved field mapping, write allowlist, rollback method, and audit sink
- Stable external event ID or scheduled-run ID for deduplication

## Instructions

1. **Establish scope.** Accept a bounded list of DOT numbers from the scheduler
   or validated event. Reject unbounded “sync everything” requests.
2. **Read current data.** Call `bulk_lookup` with only the sections required by
   the approved mapping. Preserve missing fields as missing.
3. **Build a dry-run diff.** Call `tms_sync` in dry-run/export mode. Classify
   changes into safe automatic updates and review-required changes.
4. **Gate writes.** Require explicit application policy for status, authority,
   insurance, safety, contact, and equipment fields. Never overwrite a curated
   TMS value merely because upstream data is blank.
5. **Apply idempotently.** Use the source event or run ID as the idempotency key.
   Write in bounded batches and stop on authentication or schema failures.
6. **Verify.** Read the affected TMS records back, compare allowed fields, and
   record counts and identifiers without copying full carrier records into logs.
7. **Report.** Separate `evaluated`, `changed`, `unchanged`, `review_required`,
   and `failed` counts.

## Examples

```json
{
  "run_id": "tms-reconcile-2026-09-22T1800Z",
  "dot_numbers": ["1234567", "7654321"],
  "include": ["basics", "authorities", "insurances"],
  "mode": "dry_run"
}
```

Review the diff before changing `mode` to the repository's supported write
operation. A notification saying “carrier changed” is a trigger to re-read the
current company record; it is not itself authoritative carrier data.

## Error handling

- `get_alerts` / `endpoint_unavailable`: use the scheduler or external event
  source; do not infer that no changes occurred.
- `401` or `403`: stop the batch and correct authorization.
- `429`: honor `Retry-After`; retain the run ID and resume idempotently.
- TMS write failure: stop subsequent writes when consistency is uncertain,
  preserve the dry-run diff, and execute the approved rollback.
- Missing source section: mark the affected field `review_required`; do not
  clear the TMS value.

## Resources

- Current API contract: `API-DISCOVERY.md`
- API Bridge skill: `searchcarriers-api-bridge`
- TMS connector skill: `searchcarriers-tms-connector`

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.
