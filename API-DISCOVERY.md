# SearchCarriers API contract

This repository uses a versioned, hybrid API contract. Do not assume that the
highest version contains every resource, and do not copy parameter names from
an older search route into v3. SearchCarriers may return HTTP 200 while ignoring
an unknown filter, so route tests must assert the request parameters and the
response structure.

Contract reviewed: 2026-09-23 against the public OpenAPI document, the
SearchCarriers 1.31.0 release notes, and authenticated structural probes. Live
probe output recorded only status codes and object shapes; API response data is
not committed to this repository.

## Authentication

Send the token as a bearer value:

```http
Authorization: Bearer {token-id}|{token-secret}
Accept: application/json
```

Create tokens in [SearchCarriers API settings](https://searchcarriers.com/settings/api-tokens).
Keep tokens in a secret manager or process environment. Never commit tokens or
API response datasets.

## Version routing

| Capability | Version and route |
|---|---|
| Carrier search | `GET /api/v3/search` |
| Company profile with selected sections | `GET /api/v3/company/{dotNumber}` |
| Equipment | `GET /api/v3/company/{dotNumber}/equipment` |
| Crashes | `GET /api/v3/company/{dotNumber}/crashes` |
| Qualification reports | `GET /api/v2/company/{dotNumber}/qualification-reports` |
| VIN lookup | `GET /api/v1/search/by-vin/{vin}` |
| SCAC lookup | `GET /api/v1/search/scac?scac={code}` |
| Inspections | `GET /api/v1/company/{dotNumber}/inspections` |
| Out-of-service orders | `GET /api/v1/company/{dotNumber}/out-of-service-orders` |
| Authority history | `GET /api/v1/authority/{docketNumber}/history` |
| Bulk export | `GET /api/v1/export` |
| List watches | `GET /api/v1/company/watch` |
| Read or update one watch | `GET/POST /api/v1/company/{dotNumber}/watch` |

The published API does not expose `/api/v1/carrier-watch`,
`/api/v1/carrier-watch/alerts`, or `/api/v1/webhooks`. The API Bridge webhook
tool manages a local configuration file for downstream software; it does not
create SearchCarriers webhooks. The Watchdog compatibility `get_alerts` tool
returns a structured unavailable response rather than calling an invented route.

## v3 search parameters

| Intent | Parameter |
|---|---|
| USDOT number | `dotNumber` |
| MC, MX, or FF docket number | `docketNumber` |
| Name or broad text | `superSearchTerm` |
| State | `addressState` |
| City | `addressCity` |
| Page size | `perPage` |
| Page | `page` |

The public OpenAPI document also exposes these advanced v3 filters. The MCP
`carrier_lookup` tool accepts the corresponding snake-case names and the shared
contract translates them to the exact wire names below.

| Job | Public API parameters |
|---|---|
| Company class | `companyTypes[]` |
| Radius from ZIP | `radiusZipcode`, `radiusMiles` |
| Fleet capacity | `minPowerUnits`, `maxPowerUnits`, `minTrailers`, `maxTrailers` |
| Safety-data presence | `safetyScorePresent` |
| Filed insurance | `minBipdCoverage`, `maxBipdCoverage`, `cargoInsurancePresent` |
| Registration window | `dotRegisteredSince`, `dotRegisteredBefore` |
| Authority timing | `latestAuthorityGrantedSince`, `latestAuthorityGrantedBefore`, `minAuthorityAge`, `maxAuthorityAge` |
| Authority and operation class | `includeAuthorities[]`, `excludeAuthorities[]`, `includeOperationTypes[]`, `excludeOperationTypes[]` |
| Equipment and cargo | `includeEquipmentTypes[]`, `includeCargoCarried[]` |
| Lane origin | `laneOriginState`, `laneOriginCountyGeoid`, `laneOriginLatitude`, `laneOriginLongitude`, `laneOriginRadiusMiles` |
| Lane destination | `laneDestinationState`, `laneDestinationCountyGeoid`, `laneDestinationLatitude`, `laneDestinationLongitude`, `laneDestinationRadiusMiles` |

These filters narrow discovery candidates; they do not prove that a carrier is
available, willing to accept a load, or qualified under the caller's policy.

Use `docketNumber`, not `mcNumber`; `perPage`, not `per_page`; and
`addressState`/`addressCity`, not `state`/`city`. Use the dedicated v1 VIN path;
the `vin` query parameter is not a v3 search filter.

Example:

```bash
curl --fail-with-body --get 'https://searchcarriers.com/api/v3/search' \
  --header "Authorization: Bearer ${SEARCHCARRIERS_API_KEY}" \
  --header 'Accept: application/json' \
  --data-urlencode 'superSearchTerm=Example Freight' \
  --data-urlencode 'addressState=TX' \
  --data-urlencode 'perPage=25'
```

## v3 company sections

Pass a comma-separated `fields` parameter when requesting a company. The
verified selectable sections are:

- `contact`
- `inspections`
- `safety`
- `oos_orders`
- `oos_percents`
- `authorities`
- `insurance`
- `equipment`
- `operation`
- `service_areas`
- `risk_factors`
- `basic_scores`
- `vetting_report`

Example:

```bash
curl --fail-with-body --get \
  'https://searchcarriers.com/api/v3/company/1234567' \
  --header "Authorization: Bearer ${SEARCHCARRIERS_API_KEY}" \
  --header 'Accept: application/json' \
  --data-urlencode 'fields=contact,safety,authorities,insurance,risk_factors'
```

Use the response's nested sections directly. The MCP compatibility normalizer
adds selected legacy camel-case aliases only when older report code needs them;
it does not fabricate missing values.

## Watches

Synchronize the watch types for a company with a POST body:

```json
{"watch_types":["all","details","inspections"]}
```

To stop watching, POST an empty array. No DELETE route is documented.

## Pagination and errors

Treat `data`, `links`, and `meta` as the v3 paginated envelope. Follow returned
pagination metadata instead of assuming a fixed result limit. Handle at least:

- `401`: missing or invalid token
- `403`: subscription tier does not permit the operation
- `404`: resource or company not found
- `422`: invalid parameter or request body
- `429`: rate limit; honor `Retry-After`
- `5xx`: transient service error; use bounded backoff

Do not treat a 200 response alone as proof that a filter worked. Contract tests
must verify the outgoing parameter name and should use a query with a known
small result set when running an authorized live smoke test.

## Data handling

SearchCarriers API results are licensed service data. Do not commit live
responses, export them as public fixtures, or redistribute result datasets.
Tests in this repository use invented companies, reserved example domains, and
synthetic identifiers. Users remain responsible for their SearchCarriers
subscription and the service terms.

## Sources

- [SearchCarriers public API documentation](https://searchcarriers.com/docs/api)
- [SearchCarriers 1.31.0 release notes](https://searchcarriers.com/changelog/1.31.0)
- [SearchCarriers terms of service](https://searchcarriers.com/terms-of-service)
- [SearchCarriers product overview](https://searchcarriers.com/lander)
