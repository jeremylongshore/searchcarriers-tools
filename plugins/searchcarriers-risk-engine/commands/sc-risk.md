# /sc-risk -- Carrier Risk Score

When the user runs `/sc-risk [DOT]`, calculate and display a composite risk score for the carrier.

## Parse the Input

The argument must be a DOT number (7-digit numeric). If the user passes an MC number or
name instead, tell them to run `/sc-lookup` first to resolve the DOT number.

## Execute the Scoring

Call the `risk_score` MCP tool with the DOT number. This returns a composite risk score
(0-100), individual risk factor scores, and a carrier snapshot summary.

## Display Results

### Risk Score Header

Display the composite score with a color-coded severity level:

```
CARRIER RISK SCORE -- DOT {dot_number}
Carrier:    {legal_name}
Status:     {status}
Location:   {city}, {state}

 RISK SCORE:  {score}/100  [{level}]

   0----25----50----75----100
   |  LOW  | MED |ELEVD| HIGH|
              ^
```

Level mapping:

| Score Range | Level    | Indicator |
|-------------|----------|-----------|
| 0-25        | LOW      | Green     |
| 26-50       | MEDIUM   | Yellow    |
| 51-75       | ELEVATED | Orange    |
| 76-100      | HIGH     | Red       |

### Risk Factors Breakdown

Show each contributing factor and its weighted score:

```
RISK FACTORS

| Factor              | Score | Weight | Weighted | Notes                        |
|---------------------|-------|--------|----------|------------------------------|
| Safety Rating       | 15    | 25%    | 3.75     | Satisfactory rating          |
| Insurance Coverage  | 30    | 20%    | 6.00     | BIPD active, no cargo        |
| Authority Status    | 0     | 15%    | 0.00     | All authorities active       |
| OOS Rates           | 45    | 15%    | 6.75     | Vehicle OOS above average    |
| Operating History   | 20    | 10%    | 2.00     | 3 years operating            |
| Crash History       | 10    | 10%    | 1.00     | 1 towaway, no fatals         |
| Compliance Currency | 25    | 5%     | 1.25     | MCS-150 filed 14 months ago  |
|---------------------|-------|--------|----------|------------------------------|
| COMPOSITE           |       |        | 20.75    |                              |
```

### Carrier Snapshot

Display key carrier data that informed the score:

```
CARRIER SNAPSHOT

Power Units:    42          Drivers:        55
Safety Rating:  SATISFACTORY   Rating Date:  2024-03-15
BIPD Coverage:  $1,000,000     Cargo:        None on file
Vehicle OOS:    22.5%          Driver OOS:   4.1%
Crashes (2yr):  0 fatal, 1 injury, 2 towaway
MCS-150 Filed:  2024-12-10     Authority:    ACTIVE (Common)
```

## Follow-Up Actions

After displaying the risk score, offer these next steps:

- **Deep dive**: `/sc-vet {DOT}` for rule-by-rule vetting with pass/fail verdict
- **Insurance detail**: "Run `insurance_check` for full coverage gap analysis"
- **Full pipeline**: "Run `/sc-analyze {DOT}` for the complete risk analyst report"
- **Monitoring**: "Set up Carrier Watch for ongoing risk alerts"

## Error Handling

- **Carrier not found (404)**: "No carrier found with DOT {dot_number}. Verify the number or use `/sc-lookup` to search."
- **Tier insufficient (403)**: "Risk scoring requires a Pro subscription. Upgrade at searchcarriers.com/pricing to access the Risk Engine."
- **API timeout**: Retry the call once. If it fails again: "Risk scoring timed out for DOT {dot_number}. The carrier may have an unusually large record. Try again in a moment."
- **API authentication (401)**: "API authentication failed. Check that SEARCHCARRIERS_API_KEY is set and valid."
- **Partial data**: If the score is returned but some factors are null, display available factors and note which could not be calculated.
