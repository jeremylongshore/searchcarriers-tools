---
name: sc-bulk
description: Batch carrier lookups and bulk operations
allowed-tools: "Bash(python:*),Read"
---

# /sc-bulk -- Bulk Carrier Operations

When the user runs `/sc-bulk <action> [arguments]`, execute batch carrier lookups and bulk data operations.

## Parse the Input

The first argument is the action. Supported actions:

| Action | Arguments | Description |
|--------|-----------|-------------|
| `lookup` | `<DOT list>` | Batch lookup a list of DOT numbers |
| `file` | `<path>` | Load DOT numbers from a file (one per line, CSV, or JSON) |
| `export` | `<format>` | Export last bulk results (json, csv, markdown) |
| `status` | (none) | Show status of the last or running bulk operation |

If the user omits the action, default to `status`.

## Execute the Action

### Bulk Lookup (`lookup`)

The DOT list can be provided as:

- Space-separated: `/sc-bulk lookup 1234567 2345678 3456789`
- Comma-separated: `/sc-bulk lookup 1234567,2345678,3456789`
- Range is NOT supported -- DOT numbers are not sequential

**Processing Steps:**

1. Parse and deduplicate the DOT list
2. Validate each entry is a 7-digit number; reject non-numeric entries with a warning
3. Display the batch plan before starting:

```
BULK LOOKUP PLAN
Carriers: {count}
DOTs: {dot1}, {dot2}, ... ({count} total)
Estimated time: ~{seconds}s ({count} x ~{avg_ms}ms per lookup)
Rate limit: 3 requests/second with 5-min cache
```

4. Process carriers sequentially at max 3 requests/second
5. For each carrier, call the SearchCarriers API `GET /api/v3/search?dotNumber={dot}&perPage=1`
6. Track progress and display updates every 10 carriers or every 10 seconds

### File Import (`file`)

Load DOT numbers from a file. Supported formats:

| Format | Detection | Parsing |
|--------|-----------|---------|
| Plain text | `.txt` extension or one number per line | Strip whitespace, one DOT per line |
| CSV | `.csv` extension | First column or column named `dot`, `dot_number`, or `DOT` |
| JSON | `.json` extension | Array of strings/numbers, or objects with `dot_number` key |

After parsing, execute the same bulk lookup pipeline as the `lookup` action.

### Progress Tracking

Display progress during batch operations:

```
BULK LOOKUP PROGRESS
[=========>          ] 45/100 (45%)
Current: DOT 3456789 -- FAST FREIGHT INC
Elapsed: 32s | Remaining: ~39s
Success: 43 | Not Found: 1 | Errors: 1
Rate: 1.4 lookups/sec
```

Update this display in-place when possible. If the terminal does not support rewriting, print a progress line every 10 carriers.

### Results Summary

After all lookups complete, display a summary:

```
BULK LOOKUP COMPLETE
Total: {total} carriers
Found: {found} | Not Found: {not_found} | Errors: {errors}
Duration: {elapsed}s ({rate} lookups/sec)

RESULTS OVERVIEW
| # | DOT     | Legal Name              | Status   | City, State    | Fleet | Flags |
|---|---------|------------------------|----------|----------------|-------|-------|
| 1 | 1234567 | ACME TRUCKING LLC      | ACTIVE   | Dallas, TX     | 42    |       |
| 2 | 2345678 | FAST FREIGHT INC       | ACTIVE   | Houston, TX    | 18    |       |
| 3 | 3456789 | ROAD RUNNER TRANSPORT  | INACTIVE | Phoenix, AZ    | 0     | INACTIVE, No fleet |
```

The **Flags** column shows abbreviated red flags:
- `INACTIVE` -- carrier is not active
- `No fleet` -- zero power units reported
- `No insurance` -- no active BIPD on file (requires profile call)
- `OOS` -- out-of-service order active
- `Unsatisfactory` -- safety rating is unsatisfactory

### Export Results (`export`)

Export the results from the most recent bulk lookup. Supported formats:

| Format | Output |
|--------|--------|
| `json` | JSON array of carrier objects with all retrieved fields |
| `csv` | CSV with columns: DOT, Legal Name, DBA, Status, City, State, Phone, Power Units, Drivers, Safety Rating |
| `markdown` | Formatted markdown table (same as results overview) |

```
BULK EXPORT
Format: {format}
Carriers: {count}
Output: {filename or "displayed below"}
```

If the user provides a file path, write to that path. Otherwise, display the output inline.

### Status Check (`status`)

Show the status of the last bulk operation:

```
LAST BULK OPERATION
Started: {timestamp}
Status: {completed|in_progress|failed}
Total: {total} | Processed: {processed}
Found: {found} | Not Found: {not_found} | Errors: {errors}
Duration: {elapsed}s
```

If no bulk operation has been run in this session, display:
"No bulk operations in this session. Run `/sc-bulk lookup <DOTs>` to start."

## Rate Limit Handling

- Enforce max 3 requests/second between API calls
- If a 429 response is received, pause for the `Retry-After` duration (or 30s default)
- Log rate limit events in the progress display
- Cache successful responses with a 5-minute TTL to avoid redundant calls

## Error Handling

- **Invalid DOT format**: Skip the entry, warn the user, continue with valid entries
- **Carrier not found (404/empty)**: Log as "Not Found" in results, continue processing
- **API error (5xx)**: Retry once after 5 seconds. If still failing, log as "Error" and continue
- **Auth failure (401)**: Stop the batch. "API key invalid. Set SEARCHCARRIERS_API_KEY."
- **Rate limited (429)**: Pause and retry. Do not count as an error
- **File not found**: "File not found: {path}. Check the path and try again."
- **Unparseable file**: "Could not parse {path}. Supported formats: .txt, .csv, .json"
- **Empty input**: "No DOT numbers provided. Usage: `/sc-bulk lookup 1234567 2345678`"
