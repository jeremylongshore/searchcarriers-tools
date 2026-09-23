---
name: searchcarriers-api-bridge
description: Manage API health, run bulk carrier lookups, sync TMS data, and configure webhooks. Use when scaling carrier operations.
allowed-tools: Read,Grep,Bash(python:*)
metadata:
  tier: smb
version: 0.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Claude Code or another MCP-capable client; Python 3.10+; network access to searchcarriers.com; an appropriate SearchCarriers API subscription.
tags:
- searchcarriers
- motor-carrier
- plugin
---

# API Bridge -- Embedded Skill

## Overview

This skill provides the integration and operations layer for the searchcarriers-api-bridge plugin. It teaches you how to manage API connectivity, execute bulk carrier operations, map data for TMS export, and configure webhook-driven workflows. Where the carrier-intel plugin handles individual lookups and the risk-engine handles analysis, this plugin handles scale -- moving data efficiently between SearchCarriers and external systems.

The api-bridge plugin operates at the INTEGRATION stage. It consumes data from the SearchCarriers REST API (`https://searchcarriers.com/api/v1`) and produces structured output suitable for TMS import, webhook delivery, or pipeline handoff to other plugins.

## Prerequisites

- **Minimum tier**: SMB (bulk operations and TMS sync require paid plan)
- `SEARCHCARRIERS_API_KEY` environment variable set with a valid Bearer token
- API base URL: `https://searchcarriers.com/api/v1`
- Authentication format: `Authorization: Bearer {id}|{token}` (Laravel Sanctum)
- For TMS sync: target TMS credentials and field mapping configuration
- For webhooks: a publicly accessible callback URL

## Instructions

### Bulk Processing Operations

Bulk operations allow batch carrier lookups against the SearchCarriers API. All bulk operations must respect rate limits and implement proper error handling.

**Rate Limit Rules**

| Rule | Value | Notes |
|------|-------|-------|
| Max request rate | 3 requests/second | Enforced client-side |
| Cache TTL | 5 minutes | Avoid redundant API calls |
| Retry on 429 | Wait for `Retry-After` header | Default 30s if header absent |
| Retry on 5xx | Once after 5 seconds | Then log as error and continue |
| Batch size advisory | 100 carriers per batch | Larger batches should be chunked |

**Bulk Lookup Pipeline**

1. **Input validation**: Parse DOT numbers from list, file, or previous results. Deduplicate. Reject non-numeric entries.
2. **Rate-limited execution**: Call `GET /api/v3/search?dotNumber={dot}&perPage=1` for each DOT at max 3/sec.
3. **Result aggregation**: Collect results into a structured array. Track success, not-found, and error counts.
4. **Red flag scan**: For each found carrier, check status (ACTIVE/INACTIVE), power units (>0), and safety rating.
5. **Summary generation**: Produce a results table with DOT, name, status, location, fleet size, and flag indicators.

**Enrichment Pipeline (Optional)**

For carriers that pass the initial lookup, optionally enrich with additional data:

| Endpoint | Data Added | When to Call |
|----------|-----------|--------------|
| `/company/{dot}/authorities` | Authority status, docket numbers | Always for vetting workflows |
| `/company/{dot}/insurances` | Coverage type, amounts, providers | Always for vetting workflows |
| `/company/{dot}/inspections?perPage=5` | Recent inspection history | When safety assessment needed |
| `/company/{dot}/equipment?perPage=10` | Fleet composition | When fleet verification needed |
| `/company/{dot}/out-of-service-orders?perPage=5` | OOS history | When compliance check needed |

Enrichment multiplies API calls by the number of endpoints requested. For a 100-carrier batch with full enrichment (5 extra endpoints each), expect 600 total calls at ~3.5 minutes.

**Export Formats**

| Format | Use Case | Structure |
|--------|----------|-----------|
| JSON | Pipeline handoff, programmatic use | Array of carrier objects with all retrieved fields |
| CSV | Spreadsheet import, TMS upload | Flat rows: DOT, Name, DBA, Status, City, State, Phone, Units, Drivers, Rating |
| Markdown | Reports, documentation | Formatted table with flag indicators |

### API Health Monitoring

Monitor the SearchCarriers API to detect outages, latency spikes, and rate limit pressure before they disrupt operations.

**Endpoint Categories**

| Category | Endpoints | Test Method |
|----------|-----------|-------------|
| Search | `/search`, `/search/scac` | Lookup known DOT/SCAC |
| Company Details | `/company/{dot}/inspections`, `insurances`, `authorities`, `out-of-service-orders`, `equipment`, `vehicles` | Request with `perPage=1` |
| Authority | `/authority/{docketNumber}/history` | Request with `perPage=1` |
| Export | `/export` | Export single known DOT |
| Watch | `/company/{dot}/watch` | GET watch status |

**Health Check Protocol**

1. Verify authentication with a lightweight search request
2. Probe each endpoint with a minimal request (perPage=1 or single DOT)
3. Record HTTP status, response time (ms), and response size (bytes)
4. Classify each endpoint: UP (2xx under 5s), SLOW (2xx over 5s), DOWN (4xx/5xx/timeout)
5. Report rate limit headers if present (`X-RateLimit-Remaining`, `Retry-After`)

**Latency Thresholds**

| Classification | Response Time | Action |
|----------------|--------------|--------|
| Fast | < 200ms | Normal operation |
| Normal | 200ms - 1000ms | Acceptable, no action needed |
| Slow | 1000ms - 5000ms | Flag in dashboard, consider reducing request rate |
| Timeout | > 5000ms | Mark as DOWN, retry once, escalate if persistent |

### TMS Field Mapping

Map SearchCarriers carrier data to common TMS (Transportation Management System) field schemas for import/export.

**Standard Field Map**

| SearchCarriers Field | TMS Common Field | Transform | Notes |
|---------------------|-----------------|-----------|-------|
| `dot_number` | `carrier_id` | Direct | Primary identifier |
| `legal_name` | `carrier_name` | Direct | |
| `dba_name` | `doing_business_as` | Direct | May be null |
| `phy_street` | `address_line_1` | Direct | |
| `phy_city` | `city` | Direct | |
| `phy_state` | `state` | Direct | 2-letter code |
| `phy_zip` | `postal_code` | Direct | |
| `phone` | `phone_primary` | Strip non-digits | Format: 10-digit |
| `email_address` | `email` | Direct | May be null |
| `power_units` | `fleet_size` | Integer | |
| `total_drivers` | `driver_count` | Integer | |
| `carrier_operation` | `operation_type` | Map code | A=Auth, B=Exempt, C=Private |
| `status_code` | `carrier_status` | Map code | A=Active, I=Inactive |
| `safety_rating` | `safety_rating` | Direct | SATISFACTORY/CONDITIONAL/UNSATISFACTORY |
| `hm_ind` | `hazmat_certified` | Y/N to bool | |
| `mc_number` (from docket_numbers) | `mc_number` | Extract MC prefix | |
| `scac` | `scac_code` | Direct | May be null |

**Operation Type Code Mapping**

| SC Code | TMS Value | Description |
|---------|-----------|-------------|
| A | `AUTHORIZED_FOR_HIRE` | Common or contract carrier |
| B | `EXEMPT_FOR_HIRE` | Exempt from economic regulation |
| C | `PRIVATE_PROPERTY` | Hauls own goods |
| D | `PRIVATE_PASSENGER` | Private passenger carrier |
| E | `PRIVATE_ENTERPRISE` | Enterprise carrier |
| X | `MULTIPLE` | Combination of types |

**Insurance Mapping**

| SC Insurance Type | TMS Field | Notes |
|------------------|-----------|-------|
| BIPD | `liability_coverage` | Amount in dollars, provider name |
| Cargo | `cargo_coverage` | Amount in dollars, provider name |
| Bond (BMC-84/85) | `broker_bond` | Required only for broker authority |

When exporting to TMS, always validate:
1. Required fields are populated (carrier_id, carrier_name, carrier_status at minimum)
2. Phone numbers are formatted consistently (strip to 10 digits)
3. Status codes are translated from SC codes to TMS-expected values
4. Dollar amounts are numeric, not formatted strings
5. Dates are in the TMS-expected format (typically YYYY-MM-DD)

### Webhook Configuration

Configure webhook endpoints to receive real-time notifications from SearchCarriers for watched carriers.

**Supported Webhook Events**

| Event | Trigger | Payload Contains |
|-------|---------|-----------------|
| `carrier.status_change` | Carrier status changes (Active/Inactive/OOS) | DOT, old status, new status, timestamp |
| `carrier.insurance_change` | Insurance added, cancelled, or modified | DOT, insurance type, old/new values |
| `carrier.authority_change` | Authority granted, revoked, or pending | DOT, authority type, old/new status |
| `carrier.safety_rating` | Safety rating issued or changed | DOT, old/new rating, review date |
| `carrier.oos_order` | Out-of-service order issued or lifted | DOT, order type, effective date |

**Webhook Setup Steps**

1. Register the callback URL via `POST /api/v1/company/{dot}/watch`
2. Verify the carrier is on the watch list via `GET /api/v1/company/{dot}/watch`
3. Configure event filters (which events to receive) -- if supported by API tier
4. Test the webhook with a synthetic event -- verify your endpoint responds with 200

**Webhook Payload Processing**

When a webhook fires, the receiving system should:

1. Validate the payload authenticity (check source IP or signature if provided)
2. Parse the event type and carrier DOT number
3. Look up the carrier in local cache or fetch fresh data from the API
4. Apply business rules (e.g., auto-quarantine if status changes to INACTIVE)
5. Log the event for audit trail
6. Acknowledge receipt with HTTP 200

**Retry Behavior**

SearchCarriers retries failed webhook deliveries. Your endpoint must be idempotent -- receiving the same event twice should not cause duplicate actions. Use the event ID or timestamp for deduplication.

## Examples

### Example 1: Bulk Lookup with TMS Export

User needs to vet 50 carriers from a DOT list for TMS import.

1. Parse the DOT list (from file or inline)
2. Execute bulk lookup at 3 req/sec (~17 seconds)
3. Flag carriers with INACTIVE status, zero fleet, or unsatisfactory rating
4. Map results to TMS field schema
5. Export as CSV for TMS import
6. Report: "50 carriers processed. 47 active, 2 inactive, 1 not found. CSV exported."

### Example 2: API Health Check Before Batch

User wants to verify API health before running a large batch.

1. Probe all 11 endpoints with minimal requests
2. Report dashboard: 11/11 UP, avg 145ms, no rate limit pressure
3. Confirm: "API healthy. Safe to proceed with batch operations."
4. If any endpoint is DOWN: "2 endpoints degraded. Inspections and Equipment returning 5xx. Recommend delaying batch or excluding enrichment."

### Example 3: Webhook Setup for Carrier Monitoring

User wants real-time alerts when a watched carrier's insurance lapses.

1. Add carrier to watch list via `POST /api/v1/company/{dot}/watch`
2. Confirm watch is active via `GET /api/v1/company/{dot}/watch`
3. Document the expected webhook events: `carrier.insurance_change`
4. Advise on callback endpoint requirements (HTTPS, 200 response, idempotent)
5. Suggest: "Monitor `/sc-api` periodically to verify webhook delivery health."

### Example 4: TMS Field Mapping Validation

User asks to verify their TMS mapping before importing carrier data.

1. Fetch a sample carrier via `/api/v3/search?dotNumber={dot}`
2. Apply the standard field map from the table above
3. Display side-by-side: SC field name, SC value, TMS field name, mapped value
4. Flag any null or missing required fields
5. Report: "Mapping valid. 2 optional fields null (DBA, email). All required fields populated."

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| 401 from API | Invalid or expired API key | Verify `SEARCHCARRIERS_API_KEY` is set with valid `{id}\|{token}` format |
| 429 rate limited | Exceeded request rate | Pause for `Retry-After` duration; reduce batch concurrency |
| 5xx server error | API infrastructure issue | Retry once after 5s; if persistent, check `/sc-api` dashboard |
| Timeout (>10s) | Network or API latency | Retry once; if persistent, flag endpoint as degraded |
| Empty insurance data | Carrier has no insurance on file | Not an error -- flag as "No insurance" in results |
| Watch endpoint 403 | Tier does not support watches | "Watch/webhook features require Pro Plus. Upgrade at searchcarriers.com/pricing." |
| File parse failure | Unsupported format or malformed data | Report the specific parse error and supported formats |
| TMS mapping null | Required SC field is null | Skip the carrier or flag for manual review |

## Resources

- API endpoint reference: `{baseDir}/API-DISCOVERY.md`
- Plugin configuration: `{baseDir}/.claude-plugin/plugin.json`
- MCP server source: `{baseDir}/scripts/api_bridge_mcp.py`
- Rate limit guidance: max 3 req/sec, 5-min cache TTL
- SearchCarriers API base: `https://searchcarriers.com/api/v1`
- Auth format: `Authorization: Bearer {id}|{token}` (Laravel Sanctum)
- Carrier object schema: selectable v3 sections (see API-DISCOVERY.md)
