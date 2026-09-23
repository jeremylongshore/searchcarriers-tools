# searchcarriers-contact-verifier examples

These examples use synthetic identifiers. Apply the current route map in the repository `API-DISCOVERY.md`.

### Example 1: Single Carrier Verification

**User**: "Verify contact info for DOT 12345"

```bash
curl -s "https://searchcarriers.com/api/v3/search?dotNumber=12345" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Run all verification checks (phone, address, email, MCS-150), calculate the quality score, and present the full verification report.

### Example 2: Phone Number Check

**User**: "Check if this carrier's phone number is valid — DOT 67890"

```bash
curl -s "https://searchcarriers.com/api/v3/search?dotNumber=67890" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Focus on phone validation. Report all three phone fields (phone, fax, cell), their format validity, and whether they are duplicates of each other.

### Example 3: Multi-Carrier Cross-Reference

**User**: "Compare contact info across DOTs 12345, 67890, and 11111"

```bash
curl -s "https://searchcarriers.com/api/v1/export?dot_numbers[]=12345&dot_numbers[]=67890&dot_numbers[]=11111&file_format=json" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Run individual verification on each carrier, then run the cross-carrier sharing detection. Flag any shared phones, addresses, or emails between the three carriers. This pattern is critical for identifying related entities or chameleon carriers.

### Example 4: Address Investigation

**User**: "Is this carrier's address legitimate? DOT 12345"

```bash
curl -s "https://searchcarriers.com/api/v3/search?dotNumber=12345" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Focus on address checks: completeness, PO Box detection, physical/mailing mismatch. Then search for other carriers at the same address:

```bash
curl -s "https://searchcarriers.com/api/v3/search?superSearchTerm=123+Main+St&addressState=TX&addressCity=Dallas&perPage=50" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

If multiple carriers share the address, report them and assess whether it is a shared office, process agent, or virtual address.

### Example 5: Bulk Contact Quality Audit

**User**: "Run contact quality checks on all carriers in /tmp/my_carriers.csv"

1. Parse the CSV for DOT numbers (use the bulk-processor pattern).
2. Fetch all carriers via `/export`.
3. Run verification checks on each carrier.
4. Cross-reference contacts across the batch.
5. Present a summary table sorted by quality score, worst first.
6. Export the full results to CSV with a quality_score column.

## Output

Return the requested result with the API route version, relevant carrier identifiers, evidence, missing-data limits, and the next operational action. Never include an API token or an unredacted bulk API response.
