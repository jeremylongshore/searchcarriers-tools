# API Bridge - User Journey

## Persona

**Name:** David Kim
**Role:** IT Director at Pacific Freight Partners, a large freight brokerage (120 employees, 800 loads/day, 500+ carrier panel)
**Goal:** Automate carrier data management -- bulk re-qualification, TMS sync, API monitoring -- so his three-person IT team stops spending half their week on manual carrier data work
**Tier:** Enterprise ($499/month -- the brokerage also has Carrier Intel and Risk Engine subscriptions for their compliance team)
**Current workflow:** His team maintains a carrier panel of 530 approved carriers in McLeod LoadMaster TMS. Every quarter, a compliance analyst exports the DOT list from McLeod, opens FMCSA SAFER, manually checks each carrier (530 lookups over 3 days), updates a master spreadsheet, reformats the spreadsheet into McLeod's import template, and uploads it. The process takes 4 full working days per quarter. Between re-qualification cycles, nobody checks for carrier status changes unless dispatch reports a problem.
**Pain:** Last quarter, they tendered a load to a carrier whose operating authority had been revoked 6 weeks earlier. The carrier moved the load anyway, without legal authority. The shipper discovered the violation during an audit and threatened to pull their $4M annual contract. David's CTO told him to "fix the carrier data problem or we will find someone who can."

## Prerequisites

- [ ] SearchCarriers account with Enterprise tier -- upgrade at [searchcarriers.com/pricing](https://searchcarriers.com/pricing)
- [ ] API key generated at [searchcarriers.com/settings/api-tokens](https://searchcarriers.com/settings/api-tokens)
- [ ] API key set in environment: `export SEARCHCARRIERS_API_KEY="your_id|your_token"`
- [ ] Grok Build, Claude Code, or another MCP-capable client installed
- [ ] API Bridge plugin installed: configure in `.mcp.json` or copy to plugins directory
- [ ] (Recommended) Carrier Intel plugin installed for individual follow-up lookups

## Step-by-Step Walkthrough

### Step 1: API Health Check

David's team starts their Monday morning by verifying the SearchCarriers API is healthy before kicking off any batch jobs. Last month, they ran a bulk re-qualification while the API was experiencing intermittent timeouts. Half the batch failed and they had to re-run it.

```
Check the SearchCarriers API health
```

**What happens behind the scenes:**
1. the MCP client invokes `api_health`
2. MCP server checks tier: user must be SMB or above (Enterprise qualifies)
3. Health checker probes 5 API endpoints using DOT 69494 (Werner, known-good carrier)
4. Response times measured, rate limit headers parsed, status computed

**Expected output:**

```
SEARCHCARRIERS API HEALTH CHECK
================================
Timestamp: 2026-02-26 08:15:03 UTC

ENDPOINTS
  Endpoint                        Status    Response Time    HTTP
  --------                        ------    -------------    ----
  /search                          OK            312ms       200
  /company/{dot}/authorities       OK            287ms       200
  /company/{dot}/insurances        OK            345ms       200
  /company/{dot}/equipment         OK            298ms       200
  /company/{dot}/vehicles          OK            256ms       200

RATE LIMITS
  Limit:      180 requests / minute
  Remaining:  175 requests
  Reset:      42 seconds

OVERALL STATUS: HEALTHY
  All 5 endpoints responding normally.
  Average response time: 300ms
  Rate limit headroom: 97% remaining
```

David sees all green. The API is healthy with plenty of rate limit headroom. He gives his compliance analyst the go-ahead to run the quarterly re-qualification.

### Step 2: Bulk Lookup of 50 Carriers

David's analyst has the first batch of 50 DOT numbers from their McLeod export. Rather than looking up each one manually, she runs a bulk lookup with standard sections (carrier data plus authority status).

```
Run a bulk lookup on these 50 DOT numbers with standard sections:
69494, 27021, 3456789, 2853291, 1234567, 2345678, 3456780, 4567891,
5678901, 6789012, 7890123, 8901234, 9012345, 1023456, 1134567,
1245678, 1356789, 1467890, 1578901, 1689012, 1790123, 1801234,
1912345, 2023456, 2134567, 2245678, 2356789, 2467890, 2578901,
2689012, 2790123, 2801234, 2912345, 3023456, 3134567, 3245678,
3356789, 3467890, 3578901, 3689012, 3790123, 3801234, 3912345,
4023456, 4134567, 4245678, 4356789, 4467890, 4578901, 4689012
```

**What happens behind the scenes:**
1. the MCP client invokes `bulk_lookup` with 50 DOT numbers and `sections="standard"`
2. MCP server checks tier: SMB or above (Enterprise qualifies)
3. Batch processor initializes: 50 DOTs x 2 API calls each = 100 total API calls
4. Rate limiter: 3 req/s means ~34 seconds estimated runtime
5. Processing loop runs, reporting progress every 10 DOTs
6. 2 DOTs fail (invalid/not found), 48 succeed

**Expected output:**

```
BULK CARRIER LOOKUP
====================
Sections: standard (search + authorities)
Total DOTs: 50

Progress: 10/50 complete...
Progress: 20/50 complete...
Progress: 30/50 complete...
Progress: 40/50 complete...
Progress: 50/50 complete

SUMMARY
  Succeeded:  48 carriers
  Failed:     2 carriers
  Duration:   36.4 seconds
  API calls:  100 (96 succeeded, 4 failed)

FAILED DOTs
  DOT 9012345  -- 404 Not Found (no carrier in database)
  DOT 1023456  -- 404 Not Found (no carrier in database)

RESULTS (first 5 of 48)
  1. WERNER ENTERPRISES INC (DOT 69494)
     Status: Active | Rating: Satisfactory | Power Units: 7,880
     Authorities: Common (Active), Contract (Active), Broker (Active)

  2. KLLM TRANSPORT SERVICES INC (DOT 27021)
     Status: Active | Rating: Satisfactory | Power Units: 2,156
     Authorities: Common (Active)

  3. COLD STAR LOGISTICS LLC (DOT 3456789)
     Status: Active | Rating: None | Power Units: 12
     Authorities: Common (Active, granted 2024-12-15)

  [...43 more carriers...]

Full structured data available for export. Run tms_sync to format for your TMS.
```

The analyst has 48 carrier profiles with authority data in 36 seconds. The two failed DOTs are carriers that no longer exist in FMCSA -- she will flag these for removal from the McLeod panel.

### Step 3: TMS Export to CSV

David wants the bulk lookup results formatted as CSV for import into McLeod LoadMaster. In v0.1, `tms_sync` exports generic CSV that works with most TMS platforms. McLeod-specific and TMW-specific field mappings are planned for v0.2.

```
Export the bulk lookup results to CSV format
```

**What happens behind the scenes:**
1. the MCP client passes the bulk_lookup results to `tms_sync` with `action="export"` and `format="csv"`
2. MCP server checks tier: Enterprise required for tms_sync (yes)
3. TMS Mapper generates CSV with standard column headers
4. Column headers may need manual mapping in McLeod's import configuration

**Expected output:**

```
TMS EXPORT: Generic CSV Format
=====================================
Carriers exported: 48
Format: Generic CSV
Timestamp: 2026-02-26 08:22:41 UTC

CSV CONTENT:
carrier_name,dot_number,mc_number,address,city,state,zip,phone,status,safety_rating,power_units,total_drivers,common_authority,contract_authority,broker_authority
"WERNER ENTERPRISES INC",69494,"MC-14983","14507 FRONTIER RD","OMAHA","NE","68138","(402) 895-6640","Active","Satisfactory",7880,12525,"Active","Active","Active"
"KLLM TRANSPORT SERVICES INC",27021,"MC-135567","1080 RIVER OAKS DR","JACKSON","MS","39232","(601) 936-2696","Active","Satisfactory",2156,2489,"Active","N/A","N/A"
"COLD STAR LOGISTICS LLC",3456789,"MC-1456789","4521 INDUSTRIAL BLVD","DALLAS","TX","75247","(214) 555-0198","Active","None",12,15,"Active","N/A","N/A"
[...45 more rows...]

Source: SearchCarriers API v1 | Generated by API Bridge v0.2.0

Copy the CSV content above and save it as a .csv file for TMS import.
Column headers use generic names -- map them to your TMS fields during import.
```

David's analyst copies the CSV, saves it as `carrier_requalification_2026_Q1.csv`, maps the columns in McLeod's import wizard, and imports it.

### Step 4: Webhook Setup for Carrier Watch

Now that the panel is re-qualified, David wants to set up automated monitoring so they do not miss carrier status changes between quarterly cycles. He configures a webhook to send carrier change events to their internal Slack integration endpoint.

```
Create a Carrier Watch webhook for authority changes and insurance changes,
pointing to https://hooks.pacificfreight.com/carrier-alerts
```

**What happens behind the scenes:**
1. the MCP client invokes `webhook_manage` with `action="create"`, URL, and event types
2. MCP server checks tier: SMB or above (Enterprise qualifies)
3. URL validated: HTTPS, valid format
4. Event types validated: `authority_change` and `insurance_change` are known types
5. API call to Carrier Watch webhook endpoint

**Expected output:**

```
WEBHOOK CREATED
================
Webhook ID:   wh_8f3a2b1c
URL:          https://hooks.pacificfreight.com/carrier-alerts
Events:       authority_change, insurance_change
Status:       Active
Created:      2026-02-26 08:25:12 UTC

This webhook will receive POST requests when any carrier on your
Carrier Watch list has an authority or insurance status change.

Payload format:
  {
    "event": "authority_change",
    "carrier": { "dot_number": "...", "legal_name": "..." },
    "change": { "field": "...", "old_value": "...", "new_value": "..." },
    "timestamp": "..."
  }

To manage this webhook later:
  - List all webhooks: "List my Carrier Watch webhooks"
  - Update this webhook: "Update webhook wh_8f3a2b1c"
  - Delete this webhook: "Delete webhook wh_8f3a2b1c"
```

David now has automated webhook notifications for the two most critical change types -- authority revocations and insurance lapses. His Slack channel will get pinged when any carrier on their panel has a detected status change (based on nightly FMCSA data syncs), instead of waiting until the next quarterly re-qualification.

### Step 5: Verify Webhook Configuration

A week later, David wants to review all configured webhooks to make sure everything is still active.

```
List my Carrier Watch webhooks
```

**Expected output:**

```
CARRIER WATCH WEBHOOKS
=======================
Total: 2 webhooks configured

  ID             URL                                           Events                           Status
  --             ---                                           ------                           ------
  wh_8f3a2b1c    https://hooks.pacificfreight.com/carrier-alerts   authority_change, insurance_change   Active
  wh_6d4e9f0a    https://hooks.pacificfreight.com/safety-alerts    safety_rating_change                 Active

Both webhooks are active and receiving events.
```

## Error Scenarios

### Scenario: Bulk Lookup with Rate Limit Hit

**Trigger:** Running a 100-DOT bulk lookup when rate limit headroom is low.

```
Run a bulk lookup on 100 DOT numbers with full sections
```

**Response:**

```
BULK CARRIER LOOKUP
====================
Sections: full (search + authorities + insurance)
Total DOTs: 100
Estimated API calls: 300

Progress: 15/100 complete...
Rate limit reached. Pausing for 12 seconds (Retry-After header)...
Progress: 30/100 complete...
Progress: 45/100 complete...
Rate limit reached. Pausing for 8 seconds...
Progress: 60/100 complete...
Progress: 75/100 complete...
Progress: 90/100 complete...
Progress: 100/100 complete

SUMMARY
  Succeeded:  97 carriers
  Failed:     3 carriers
  Duration:   142.8 seconds (includes 20 seconds of rate limit pauses)
  API calls:  300 (291 succeeded, 9 failed)

Rate limit pauses are normal during large batch operations.
The API Bridge automatically waits and resumes when rate limit resets.
```

### Scenario: TMS Sync with Insufficient Tier

**Trigger:** SMB user attempts TMS export.

```
Export carrier data to CSV for TMS import
```

**Response:**

```
TMS synchronization requires an Enterprise subscription.
Your current tier: SMB

The tms_sync tool exports carrier data as generic CSV or JSON
for TMS import. It requires Enterprise tier. TMS-specific
field mappings (McLeod, TMW) are planned for v0.2.

Upgrade at https://searchcarriers.com/pricing

Tools available on your SMB tier:
  - api_health: API endpoint monitoring and rate limit status
  - bulk_lookup: Batch carrier lookups (up to 100 DOTs)
  - webhook_manage: Carrier Watch webhook configuration
```

### Scenario: Webhook with Invalid URL

**Trigger:** Creating a webhook with a non-HTTPS URL.

```
Create a webhook at http://hooks.example.com/carriers
```

**Response:**

```
Webhook URL must use HTTPS.
  Provided: http://hooks.example.com/carriers
  Required: https://hooks.example.com/carriers

SearchCarriers requires HTTPS for all webhook endpoints to ensure
payload delivery is encrypted in transit. Update the URL to use
HTTPS and try again.
```

### Scenario: API Health Check Shows Degraded Status

**Trigger:** API is experiencing slowdowns on some endpoints.

```
Check API health
```

**Response:**

```
SEARCHCARRIERS API HEALTH CHECK
================================
Timestamp: 2026-02-26 14:30:22 UTC

ENDPOINTS
  Endpoint                        Status    Response Time    HTTP
  --------                        ------    -------------    ----
  /search                          OK            445ms       200
  /company/{dot}/authorities       SLOW         3,241ms      200
  /company/{dot}/insurances        SLOW         2,876ms      200
  /company/{dot}/equipment         OK            512ms       200
  /company/{dot}/vehicles          OK            389ms       200

RATE LIMITS
  Limit:      180 requests / minute
  Remaining:  112 requests
  Reset:      28 seconds

OVERALL STATUS: DEGRADED
  2 of 5 endpoints responding slowly (>2000ms).
  Affected: authorities, insurances
  Search and equipment endpoints are normal.

  Recommendation: Bulk lookups with "standard" or "full" sections will be
  slower than normal. Consider using "basic" sections until performance
  recovers, or reduce batch size. Monitor at https://searchcarriers.com/status
```

### Scenario: Batch Exceeds Maximum Size

**Trigger:** Submitting more than 100 DOT numbers.

```
Bulk lookup for 150 DOT numbers: [...]
```

**Response:**

```
Maximum batch size is 100 DOT numbers per bulk_lookup call.
You submitted: 150 DOTs

Split your list into multiple batches:
  Batch 1: DOTs 1-100
  Batch 2: DOTs 101-150

Run each batch separately. Results can be combined for TMS export.
```

## FAQ

**Q: How many carriers can I look up in one bulk_lookup call?**
A: Up to 100 DOT numbers per call. For larger panels, split into multiple batches. A 500-carrier panel takes 5 batches. Each batch runs independently and results can be combined for TMS export.

**Q: How long does a bulk lookup take?**
A: Depends on batch size and section depth. At the API's 3 req/s rate limit: 100 DOTs with basic sections takes ~34 seconds, standard sections ~67 seconds, full sections ~100 seconds. Rate limit pauses may add 10-30 seconds during high-traffic periods.

**Q: What TMS formats are supported?**
A: v0.1 ships with generic CSV and JSON export. McLeod LoadMaster and TMW Suite specific formats are planned for v0.2. The generic CSV format works with most TMS platforms that support CSV import -- column headers may need manual mapping in the TMS configuration.

**Q: Does API Bridge write files to disk?**
A: No. All output is returned as text content in the model client's context. CSV and JSON exports are returned as strings. You copy the content and save it to a file yourself, or ask the model client to save it. The MCP server does not create files on the filesystem.

**Q: Can I use bulk_lookup results with other plugins?**
A: Yes. Bulk lookup results are structured JSON that Carrier Intel, Risk Engine, and Ops Reporter can consume. For example, you can run a bulk lookup, then pass individual carrier results to Risk Engine for scoring, then to Ops Reporter for formatted reports. The pipeline plugins work on single carriers, so you would process the bulk results one at a time through the pipeline.

**Q: What happens if my API key does not have the right tier?**
A: Each tool checks your tier before making API calls. If your tier is insufficient, you get a clear error message with the required tier and a link to the pricing page. No API calls are wasted on tier-gated operations.

**Q: How does webhook_manage relate to the Watchdog plugin?**
A: API Bridge's `webhook_manage` configures the webhook endpoints (create, update, delete). Watchdog's tools consume the data those webhooks deliver (alerts, compliance drift). Think of API Bridge as managing the plumbing and Watchdog as reading the water. You can use `webhook_manage` without Watchdog if you have your own systems consuming webhook payloads.

**Q: Does the api_health check count against my rate limit?**
A: Yes. The health check makes 5 API requests (one per endpoint). This uses 5 of your rate limit budget. At 180 requests per minute, this is minimal. The health check reports remaining rate limit budget so you can see the impact.
