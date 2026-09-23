# searchcarriers-tms-connector examples

These examples use synthetic identifiers. Apply the current route map in the repository `API-DISCOVERY.md`.

### Example 1: Format for McLeod

**User**: "Format DOT 12345 for McLeod import"

```bash
curl -s "https://searchcarriers.com/api/v3/search?dotNumber=12345" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Map fields to McLeod format, generate CSV, report the output path. Include a note about where in McLeod to import the file (Carrier Maintenance > Import Carrier Records).

### Example 2: Generic TMS Import

**User**: "Build a carrier import CSV for our TMS"

Ask which carriers (DOT numbers) and which TMS platform. If platform is unknown, use the generic format. Fetch carrier data, generate the CSV, and list the included fields so the user can verify column mapping.

### Example 3: TMS Platform Field Guidance

**User**: "What fields does TMW need for carrier onboarding?"

Present the TMW field mapping table from section 3. Explain which fields are required vs. optional. Note any fields that SearchCarriers provides that TMW does not natively support (these can be added as custom fields in TMW).

### Example 4: Batch Carrier Onboarding

**User**: "Onboard these carriers into our TMS: DOTs 12345, 67890, 11111, 22222"

```bash
curl -s "https://searchcarriers.com/api/v1/export?dot_numbers[]=12345&dot_numbers[]=67890&dot_numbers[]=11111&dot_numbers[]=22222&file_format=json" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Run vetting on each carrier, classify results, generate import file for approved carriers, and present the batch summary.

### Example 5: Carrier Update Sync

**User**: "Check if DOT 12345 has changed since we last synced"

```bash
# Fetch current data
curl -s "https://searchcarriers.com/api/v3/search?dotNumber=12345" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"

# Check watch status
curl -s "https://searchcarriers.com/api/v1/company/12345/watch" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Present current data and ask the user what their TMS currently shows. Diff the two and generate an update file if needed. Recommend adding to watchlist if not already watched.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.
