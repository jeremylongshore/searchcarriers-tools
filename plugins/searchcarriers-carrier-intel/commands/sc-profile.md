# /sc-profile — Full Carrier Profile

When the user runs `/sc-profile [DOT]`, fetch and display a comprehensive carrier profile.

The argument must be a DOT number (7-digit numeric). If the user passes an MC number or
name instead, tell them to run `/sc-lookup` first to find the DOT number.

Call the `carrier_profile` MCP tool with the DOT number. This returns the combined carrier
record: search data, authorities, and insurance in a single response.

Present these sections. Omit a section only if every field in it is null.

### Identity

```
CARRIER PROFILE — DOT {dot_number}
Legal Name:       {legal_name}
DBA:              {dba_name}
DOT Number:       {dot_number}
MC/MX Number:     {mc_number}
SCAC:             {scac} (if available)
Entity Type:      {entity_type}
Status:           {status}
Registration:     MCS-150 filed {mcs150_date}, form type {mcs150_form_type}
```

### Contact

```
Phone:            {phone}
Email:            {email}
Physical:         {phy_street}, {phy_city}, {phy_state} {phy_zip}
Mailing:          {mail_street}, {mail_city}, {mail_state} {mail_zip}
```

### Fleet & Operations

```
Power Units:      {power_units}
Drivers:          {drivers}
CDL Holders:      {cdl_holders} (if available)
Operation Type:   {carrier_operation} — {description}
Fleet Size Code:  {fleet_size_code}
```

### Authority

```
| Authority Type | Status   | Docket | Effective  |
|---------------|----------|--------|------------|
| Common        | {status} | {num}  | {date}     |
| Contract      | {status} | {num}  | {date}     |
| Broker        | {status} | {num}  | {date}     |
```

### Insurance

```
| Type | Provider          | Policy #    | Amount     | Status | Effective  |
|------|-------------------|-------------|------------|--------|------------|
| BIPD | {company}         | {policy}    | ${amount}  | Active | {date}     |
| Cargo| {company}         | {policy}    | ${amount}  | Active | {date}     |
```

### Safety

```
Safety Rating:    {safety_rating} ({rating_date})
Review Type:      {review_type}
Crashes:          {fatal} fatal, {injury} injury, {towaway} towaway
Vehicle OOS:     {veh_oos_pct}%  (national avg ~20%)
Driver OOS:      {driver_oos_pct}%  (national avg ~5%)
```

### Cargo Types

List only cargo boolean fields that are true/yes as a comma-separated line.

## Red Flag Detection

After the profile, highlight these concerns in a warning block:

- **INACTIVE/REVOKED** status — carrier cannot legally operate
- **No active BIPD insurance** — illegal to operate for-hire
- **Unsatisfactory safety rating** — FMCSA may issue OOS order
- **Conditional safety rating** — deficiencies identified, review needed
- **MCS-150 overdue** — if last filing > 2 years ago, data may be stale
- **Zero power units or drivers** — possible shell or dormant entity
- **Very new carrier** — MCS-150 date within last 6 months, limited history

## Next Steps

Suggest: `/sc-risk {DOT}` for risk scoring, entity mapping via `entity_map`, or fleet
details via `fleet_summary`.

## Error Handling

- 404: "No carrier found with DOT {dot_number}. Verify the number or use `/sc-lookup`."
- 401: "API authentication failed. Check that SEARCHCARRIERS_API_KEY is set."
- Non-numeric input: "Please provide a DOT number. Use `/sc-lookup` to find it by name."
