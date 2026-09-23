---
name: sc-api
description: Check SearchCarriers API health, response times, and rate limits
allowed-tools: "Bash(python:*),Read"
---

# /sc-api -- API Health Monitor

When the user runs `/sc-api [target]`, check the health of SearchCarriers API endpoints and display a status dashboard.

## Parse the Input

The optional argument specifies what to check:

| Argument | Description |
|----------|-------------|
| (none) | Check all endpoints and show full dashboard |
| `search` | Check search endpoints only (`/search`, `/search/scac`) |
| `company` | Check company detail endpoints (`/company/{dot}/*`) |
| `export` | Check the export endpoint (`/export`) |
| `auth` | Check authentication status and key validity |

If the argument does not match a known target, treat it as a DOT number and use it as the test carrier for endpoint probes.

## Execute the Health Check

### Authentication Probe

Before checking any data endpoints, verify the API key:

1. Make a lightweight request to `GET /api/v3/search?dotNumber=1&perPage=1`
2. If 401: report authentication failure and stop -- no point checking further
3. If 200: extract response time and continue

### Endpoint Probes

For each endpoint category, make a minimal request and record the response:

| Endpoint | Test Request | Success |
|----------|-------------|---------|
| Search | `GET /search?dotNumber=2247837&perPage=1` | 200 with data |
| SCAC | `GET /search/scac?scac=HJBT` | 200 with code |
| Inspections | `GET /company/2247837/inspections?perPage=1` | 200 |
| Insurances | `GET /company/2247837/insurances?perPage=1` | 200 |
| Authorities | `GET /company/2247837/authorities` | 200 |
| OOS Orders | `GET /company/2247837/out-of-service-orders?perPage=1` | 200 |
| Equipment | `GET /company/2247837/equipment?perPage=1` | 200 |
| Vehicles | `GET /company/2247837/vehicles?perPage=1` | 200 |
| Auth History | `GET /authority/2247837/history?perPage=1` | 200 |
| Export | `GET /export?dot_numbers[]=2247837&file_format=json` | 200 |
| Watch | `GET /company/2247837/watch` | 200 |

Record for each probe: HTTP status code, response time (ms), and response size (bytes).

## Display the Dashboard

### Full Dashboard (no argument)

```
SEARCHCARRIERS API STATUS
Checked: {timestamp}
Base URL: https://searchcarriers.com/api/v1
Auth: {key_status} (key ...{last_4})

| Endpoint         | Status | Response | Size    | Notes             |
|------------------|--------|----------|---------|-------------------|
| Search           | UP     | 142ms    | 3.2 KB  |                   |
| SCAC Lookup      | UP     | 89ms     | 0.4 KB  |                   |
| Inspections      | UP     | 215ms    | 8.1 KB  |                   |
| Insurances       | UP     | 103ms    | 0.2 KB  | Empty response    |
| Authorities      | UP     | 97ms     | 1.1 KB  |                   |
| OOS Orders       | UP     | 110ms    | 0.3 KB  |                   |
| Equipment        | UP     | 178ms    | 4.5 KB  |                   |
| Vehicles         | UP     | 134ms    | 2.8 KB  |                   |
| Auth History     | UP     | 91ms     | 1.4 KB  |                   |
| Export           | UP     | 320ms    | 5.6 KB  |                   |
| Watch            | UP     | 85ms     | 0.1 KB  |                   |

Summary: {up_count}/11 endpoints healthy
Avg response: {avg_ms}ms | Slowest: {slowest_name} ({slowest_ms}ms)
```

### Rate Limit Status

If response headers include rate limit information (`X-RateLimit-*` or `Retry-After`), display:

```
RATE LIMITS
Remaining: {remaining}/{limit} requests
Resets: {reset_time}
Recommended: Max 3 req/sec, cache with 5-min TTL
```

If no rate limit headers are present, display:
"Rate limit headers not returned. Recommended: max 3 requests/second with 5-minute cache TTL."

### Single Endpoint Check

When a specific target is requested, show only the relevant rows from the dashboard plus the rate limit section.

## Error Handling

- **401 Unauthorized**: "API key invalid or missing. Set SEARCHCARRIERS_API_KEY with a valid Bearer token."
- **429 Too Many Requests**: "Rate limited. Retry after {retry_after}s. Reduce request frequency."
- **Timeout (>10s)**: Mark endpoint as SLOW and flag for investigation.
- **Connection error**: Mark endpoint as DOWN. Suggest checking network or API status page.
- **Partial failures**: Show the dashboard with failing endpoints marked as DOWN. Do not abort the entire check.
