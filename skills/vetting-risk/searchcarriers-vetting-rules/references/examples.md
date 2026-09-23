# searchcarriers-vetting-rules examples

These examples use synthetic identifiers. Apply the current route map in the repository `API-DISCOVERY.md`.

### Standard vetting run

**User prompt**: "Vet DOT 12345"

Load default rules, fetch all data from the 6 API endpoints, execute all 11 rules, produce the full vetting report with PASS/FAIL/REVIEW verdict.

### Vetting with custom requirements

**User prompt**: "Vet this carrier with 50 unit minimum and no conditional ratings"

Acknowledge the custom requirements: "Running vetting with modified rules: fleet_size.minimum_power_units = 50, safety_rating moved Conditional to fail_ratings." Then execute the full vetting with the modified rule set.

### Vetting by company name

**User prompt**: "Run full vetting on Pacific Transport"

First search by name: `/api/v3/search?superSearchTerm=PACIFIC%20TRANSPORT`. If multiple results, present them and ask the user to confirm the correct carrier. Then run the full vetting on the confirmed DOT number.

### Batch vetting

**User prompt**: "Vet these 3 carriers: DOT 12345, DOT 67890, DOT 11111"

Run the full vetting for each carrier sequentially. Produce individual reports for each, then a summary table:

```
BATCH VETTING SUMMARY
| DOT    | Carrier Name      | Verdict              | Failed Rules |
|--------|-------------------|----------------------|--------------|
| 12345  | ABC Trucking      | PASS                 | —            |
| 67890  | XYZ Logistics     | FAIL                 | insurance    |
| 11111  | Quick Freight     | REVIEW W/ EXCEPTIONS | authority_age|
```

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.

### Custom Rules Examples

Users can override default rules inline. Parse their request and modify the rule set:

| User Says | Rule Modification |
|-----------|-------------------|
| "require 50 power units minimum" | Set `fleet_size.minimum_power_units` = 50 |
| "Satisfactory only, no Conditional" | Remove "Conditional" from `safety_rating.pass_ratings`, add to `fail_ratings` |
| "ignore fleet size" | Set `fleet_size.enabled` = false |
| "max 20% OOS rate" | Set `oos_rate.max_vehicle_oos_pct` = 20, `oos_rate.max_driver_oos_pct` = 20 |
| "must have cargo insurance" | Add a new rule checking for active cargo insurance |
| "authority must be 3+ years" | Set `authority_age.minimum_months` = 36 |
| "$5M insurance minimum" | Set `insurance_minimum.minimum_bipd` = 5000000 |

Always echo back the interpreted rule changes to the user before running the vetting so they can confirm.
