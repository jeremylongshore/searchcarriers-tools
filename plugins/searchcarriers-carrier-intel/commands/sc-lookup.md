# /sc-lookup — Carrier Search

When the user runs `/sc-lookup [query]`, perform a carrier search and return formatted results.

## Parse the Query

Classify the query into one search type and call `carrier_lookup` with the right parameter:

| Pattern | Type | Parameter |
|---------|------|-----------|
| 7-digit number or "DOT" prefix | DOT | `dot_number` |
| "MC" followed by digits | MC | `mc_number` |
| 17-char alphanumeric | VIN | `vin` |
| 2-4 uppercase letters only | SCAC | `scac` |
| Anything else (company name, phrase) | Name | `search_term` |

If the query is ambiguous, use `search_term` — it searches across multiple fields.

## Execute the Search

Call the `carrier_lookup` MCP tool with the detected parameter. Pass any additional
filters the user mentioned (state, status, carrier operation type).

## Format Results

### Single Result

Display a full summary table:

```
CARRIER SUMMARY — DOT {dot_number}
Legal Name:     {legal_name}
DBA:            {dba_name}
DOT:            {dot_number}    MC: {mc_number}
Status:         {status}
Phone:          {phone}
Location:       {city}, {state} {zip}

Fleet:          {power_units} power units, {drivers} drivers
Operation:      {carrier_operation_desc}
Hazmat:         {hm_ind}

Safety Rating:  {safety_rating} ({rating_date})
```

After the summary, scan for red flags (see below) and display any that apply.

### Multiple Results

Show a compact list:

```
Found {total} carriers matching "{query}":

| # | DOT     | Legal Name            | City, State    | Status | Fleet |
|---|---------|----------------------|----------------|--------|-------|
| 1 | 1234567 | ACME TRUCKING LLC    | Dallas, TX     | ACTIVE | 42    |
| 2 | 2345678 | ACME TRANSPORT INC   | Houston, TX    | ACTIVE | 18    |
...
```

Then say: *"Run `/sc-profile {DOT}` to see the full profile for any carrier above."*

## Red Flags

Flag any of these conditions in a clearly separated block:

- **INACTIVE** or **REVOKED** operating status
- **No insurance on file** or lapsed coverage
- **Conditional** or **Unsatisfactory** safety rating
- **Out-of-service** orders (company, driver, or vehicle)
- **Zero power units** or **zero drivers** with active authority
- **High OOS rates** (vehicle > 25%, driver > 10%)

## Error Handling

- No results: "No carriers found matching '{query}'. Try a DOT number, MC number, or broader name search."
- API errors: Report the status code and suggest checking the API key if 401.
- Ambiguous query: Run as `search_term` and let the user refine from results.
