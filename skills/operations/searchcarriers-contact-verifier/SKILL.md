---
name: searchcarriers-contact-verifier
description: Validates carrier contact info including phones, addresses, and emails. Use when verifying contact quality or detecting shared contacts.
allowed-tools: Read,Grep,Bash(curl:*),Bash(python:*)
metadata:
  tier: pro
version: 0.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Claude Code or another MCP-capable client; Python 3.10+; network access to searchcarriers.com; an appropriate SearchCarriers API subscription.
tags:
- searchcarriers
- motor-carrier
- operations
---

# Contact Verifier

## Overview

> **API contract:** Use the repository `API-DISCOVERY.md` for the current v3/v2/v1 route map and verified parameter names. Do not infer newer-version routes.

Bad contact information is the silent killer of freight operations. A dispatcher calls a carrier's listed phone number and gets a disconnected line. A compliance team mails insurance requests to an address that turns out to be a UPS Store mailbox. An onboarding email goes to a generic Gmail account that nobody monitors. These failures waste hours and create liability gaps. This skill retrieves carrier contact data from the SearchCarriers API and runs a structured verification analysis: phone format validation, address completeness and consistency checks, email domain assessment, MCS-150 freshness dating, and cross-carrier contact sharing detection. The output is a contact quality score with specific, actionable flags.

## Prerequisites

- **Minimum tier**: Pro
- **Environment variable**: `SEARCHCARRIERS_API_KEY` must be set in the shell environment
- **Network access**: HTTPS to `searchcarriers.com`
- **Context**: For cross-carrier comparisons, multiple DOT numbers are needed

## Instructions

### 1. Fetch Contact Data

Retrieve the carrier record focusing on contact-related fields:

```bash
curl -s "https://searchcarriers.com/api/v3/search?dotNumber=12345" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

Extract these contact fields from the response:

| Field | API Key | Description |
|---|---|---|
| Phone | `phone` | Primary business phone |
| Fax | `fax` | Fax number |
| Cell Phone | `cell_phone` | Mobile number |
| Email | `email_address` | Primary email |
| Physical Street | `phy_street` | Physical location street |
| Physical City | `phy_city` | Physical location city |
| Physical State | `phy_state` | Physical location state |
| Physical ZIP | `phy_zip` | Physical location ZIP |
| Mailing Street | `carrier_mailing_street` | Mailing address street |
| Mailing City | `carrier_mailing_city` | Mailing address city |
| Mailing State | `carrier_mailing_state` | Mailing address state |
| Mailing ZIP | `carrier_mailing_zip` | Mailing address ZIP |
| MCS-150 Date | `mcs150_date` | Last MCS-150 filing date |
| MCS-150 Year | `mcs150_year` | MCS-150 mileage year |

### 2. Phone Number Validation

Run these checks on `phone`, `fax`, and `cell_phone`:

```bash
python3 -c "
import re, sys, json

carrier = json.loads(sys.argv[1])
phone_fields = {
    'Phone': carrier.get('phone', ''),
    'Fax': carrier.get('fax', ''),
    'Cell': carrier.get('cell_phone', ''),
}

flags = []
valid_numbers = {}

for label, number in phone_fields.items():
    if not number or number.strip() == '':
        flags.append(f'{label}: MISSING')
        continue

    # Strip to digits only
    digits = re.sub(r'\D', '', str(number))

    # Check length
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]  # strip country code
    if len(digits) != 10:
        flags.append(f'{label}: INVALID FORMAT ({number}) - not 10 digits')
        continue

    area_code = digits[:3]

    # Check for known invalid area codes
    invalid_area = ['000', '555', '911', '411', '611']
    if area_code in invalid_area:
        flags.append(f'{label}: SUSPICIOUS AREA CODE ({area_code})')

    # Check for obvious fake patterns
    if digits == '0000000000' or digits == '1111111111' or len(set(digits)) == 1:
        flags.append(f'{label}: LIKELY FAKE ({number})')
        continue

    valid_numbers[label] = digits

# Check if all numbers are identical
unique_numbers = set(valid_numbers.values())
if len(valid_numbers) >= 2 and len(unique_numbers) == 1:
    flags.append('ALL NUMBERS IDENTICAL: phone = fax = cell (suspicious for a trucking company with drivers)')

# Check if phone == fax (common but notable)
if valid_numbers.get('Phone') and valid_numbers.get('Fax') and valid_numbers['Phone'] == valid_numbers['Fax']:
    flags.append('PHONE = FAX: same number for voice and fax (may indicate single-line operation)')

for f in flags:
    print(f'  [{\"WARNING\" if \"SUSPICIOUS\" in f or \"IDENTICAL\" in f else \"FLAG\" if \"MISSING\" not in f else \"INFO\"}] {f}')
if not flags:
    print('  All phone numbers valid')
" '$CARRIER_JSON'
```

**Phone validation rules:**
1. Must be exactly 10 digits (after stripping formatting and country code).
2. Area code must not be 000, 555, 911, or other reserved codes.
3. Must not be all-same-digit (e.g., 0000000000).
4. If phone = fax = cell, flag as suspicious -- a trucking company with drivers should have separate lines.
5. If phone = fax only, note it (common for small operations, not necessarily suspicious).

### 3. Address Completeness and Consistency

Verify both physical and mailing addresses:

```bash
python3 -c "
import json, sys

carrier = json.loads(sys.argv[1])
flags = []

# Physical address completeness
phy = {
    'street': carrier.get('phy_street', ''),
    'city': carrier.get('phy_city', ''),
    'state': carrier.get('phy_state', ''),
    'zip': carrier.get('phy_zip', ''),
}

missing_phy = [k for k, v in phy.items() if not v or v.strip() == '']
if missing_phy:
    flags.append(f'PHYSICAL ADDRESS INCOMPLETE: missing {missing_phy}')

# Mailing address completeness
mail = {
    'street': carrier.get('carrier_mailing_street', ''),
    'city': carrier.get('carrier_mailing_city', ''),
    'state': carrier.get('carrier_mailing_state', ''),
    'zip': carrier.get('carrier_mailing_zip', ''),
}

missing_mail = [k for k, v in mail.items() if not v or v.strip() == '']
has_any_mail = any(v.strip() for v in mail.values() if v)
if has_any_mail and missing_mail:
    flags.append(f'MAILING ADDRESS INCOMPLETE: missing {missing_mail}')

# Physical vs mailing comparison
if not missing_phy and has_any_mail and not missing_mail:
    phy_norm = ' '.join(v.strip().upper() for v in phy.values())
    mail_norm = ' '.join(v.strip().upper() for v in mail.values())
    if phy_norm != mail_norm:
        flags.append('ADDRESS MISMATCH: physical and mailing addresses differ (may indicate mail forwarding service, agent, or remote operations)')

# PO Box check on physical address
phy_street = phy.get('street', '').upper()
if 'PO BOX' in phy_street or 'P.O. BOX' in phy_street or 'P O BOX' in phy_street:
    flags.append('PO BOX AS PHYSICAL ADDRESS: FMCSA requires a physical location, not a PO Box')

# ZIP code format
import re
for label, addr in [('Physical', phy), ('Mailing', mail)]:
    z = addr.get('zip', '')
    if z and not re.match(r'^\d{5}(-\d{4})?$', z.strip()):
        flags.append(f'{label.upper()} ZIP INVALID: \"{z}\" is not a valid US ZIP format')

# State validation
valid_states = {'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
    'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY',
    'NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI',
    'WY','DC','PR','VI','GU','AS','MP'}
for label, addr in [('Physical', phy), ('Mailing', mail)]:
    st = addr.get('state', '').strip().upper()
    if st and st not in valid_states:
        flags.append(f'{label.upper()} STATE INVALID: \"{st}\" is not a recognized US state/territory')

for f in flags:
    print(f'  [FLAG] {f}')
if not flags:
    print('  Addresses complete and consistent')
" '$CARRIER_JSON'
```

**Address validation rules:**
1. Physical address must have all four components: street, city, state, ZIP.
2. Mailing address, if present, must also be complete.
3. Physical address must not be a PO Box (FMCSA requirement).
4. If physical and mailing differ, flag as potential mail forwarding (not necessarily bad, but notable).
5. ZIP must match 5-digit or 5+4 format.
6. State must be a valid US state or territory abbreviation.

### 4. Email Domain Assessment

```bash
python3 -c "
import json, sys

carrier = json.loads(sys.argv[1])
email = carrier.get('email_address', '')
fleet_size = int(carrier.get('total_power_units', 0) or 0)
legal_name = carrier.get('legal_name', '')
flags = []

if not email or email.strip() == '':
    flags.append('EMAIL MISSING: no email on file')
else:
    email = email.strip().lower()

    # Basic format check
    if '@' not in email or '.' not in email.split('@')[-1]:
        flags.append(f'EMAIL INVALID FORMAT: \"{email}\"')
    else:
        domain = email.split('@')[1]

        # Generic consumer domains
        consumer_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com',
            'icloud.com', 'mail.com', 'yandex.com', 'protonmail.com', 'live.com',
            'msn.com', 'comcast.net', 'att.net', 'verizon.net', 'sbcglobal.net',
            'bellsouth.net', 'charter.net', 'cox.net', 'earthlink.net'
        ]

        if domain in consumer_domains:
            if fleet_size > 10:
                flags.append(f'GENERIC EMAIL FOR LARGE FLEET: {email} (fleet size: {fleet_size}) - large carriers typically use business domains')
            else:
                flags.append(f'GENERIC EMAIL: {email} (common for small operators, but less professional)')

        # Check if domain matches company name loosely
        company_words = set(legal_name.lower().replace('llc','').replace('inc','').replace('corp','').replace(',','').split())
        domain_base = domain.split('.')[0]
        if domain not in consumer_domains and not any(w in domain_base for w in company_words if len(w) > 3):
            flags.append(f'EMAIL DOMAIN MISMATCH: domain \"{domain}\" does not match company name \"{legal_name}\"')

for f in flags:
    print(f'  [FLAG] {f}')
if not flags:
    print(f'  Email appears valid: {email}')
" '$CARRIER_JSON'
```

**Email validation rules:**
1. Must be present (missing email = reduced reachability).
2. Must have valid format (contains @, domain has a dot).
3. Generic consumer domain (gmail, yahoo, hotmail) for a fleet > 10 units is unusual.
4. Domain should loosely match the company name (mismatch may indicate agent or third-party service).
5. For small owner-operators (1-5 units), generic email is normal and should be noted but not heavily flagged.

### 5. MCS-150 Freshness Check

The MCS-150 form is the biennial update carriers file with FMCSA. Contact information is only as fresh as the last filing:

```bash
python3 -c "
import json, sys
from datetime import datetime, timedelta

carrier = json.loads(sys.argv[1])
mcs_date_str = carrier.get('mcs150_date', '')
flags = []

if not mcs_date_str:
    flags.append('MCS-150 DATE MISSING: cannot determine contact info freshness')
else:
    try:
        # Handle various date formats
        for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d/%m/%Y']:
            try:
                mcs_date = datetime.strptime(mcs_date_str, fmt)
                break
            except ValueError:
                continue
        else:
            flags.append(f'MCS-150 DATE UNPARSEABLE: \"{mcs_date_str}\"')
            mcs_date = None

        if mcs_date:
            age = datetime.now() - mcs_date
            age_months = age.days / 30

            if age_months > 36:
                flags.append(f'MCS-150 SEVERELY STALE: filed {mcs_date_str} ({int(age_months)} months ago) - contact info likely outdated')
            elif age_months > 24:
                flags.append(f'MCS-150 OVERDUE: filed {mcs_date_str} ({int(age_months)} months ago) - biennial update was due')
            elif age_months > 18:
                flags.append(f'MCS-150 AGING: filed {mcs_date_str} ({int(age_months)} months ago) - approaching update deadline')
            else:
                print(f'  MCS-150 current: filed {mcs_date_str} ({int(age_months)} months ago)')
    except Exception as e:
        flags.append(f'MCS-150 DATE ERROR: {e}')

for f in flags:
    print(f'  [FLAG] {f}')
" '$CARRIER_JSON'
```

**MCS-150 freshness rules:**
- Filed within 18 months: current (contact info likely accurate).
- Filed 18-24 months ago: aging (approaching biennial deadline).
- Filed 24-36 months ago: overdue (contact info may be stale).
- Filed 36+ months ago: severely stale (contact info should not be trusted without independent verification).

### 6. Cross-Carrier Contact Sharing Detection

When verifying multiple carriers, check if they share contact information. Shared contacts may indicate:
- A process agent or compliance service company
- Related corporate entities operating under different DOTs
- A chameleon carrier (rebranding to escape safety history)

```bash
python3 -c "
import json, sys

carriers = json.loads(sys.argv[1])  # list of carrier objects
shared = {'phone': {}, 'address': {}, 'email': {}}

for c in carriers:
    dot = str(c.get('dot_number', ''))
    name = c.get('legal_name', '')

    phone = c.get('phone', '').strip()
    if phone:
        shared['phone'].setdefault(phone, []).append(f'{dot} ({name})')

    addr = f\"{c.get('phy_street','').strip().upper()} {c.get('phy_city','').strip().upper()} {c.get('phy_state','').strip().upper()}\"
    if addr.strip():
        shared['address'].setdefault(addr, []).append(f'{dot} ({name})')

    email = c.get('email_address', '').strip().lower()
    if email:
        shared['email'].setdefault(email, []).append(f'{dot} ({name})')

for contact_type, groups in shared.items():
    for value, dots in groups.items():
        if len(dots) > 1:
            print(f'  [SHARED {contact_type.upper()}] \"{value}\" used by: {dots}')
"
```

For single-carrier verification, offer to search for other carriers at the same address or phone:

```bash
# Search for other carriers at the same physical address
curl -s "https://searchcarriers.com/api/v3/search?superSearchTerm=123+Main+St&addressState=TX&addressCity=Dallas&perPage=25" \
  -H "Authorization: Bearer $SEARCHCARRIERS_API_KEY" \
  -H "Accept: application/json"
```

### 7. Build the Contact Quality Score

Aggregate all checks into a 0-100 score:

| Check | Points Deducted | Weight |
|---|---|---|
| Phone missing | -15 | High |
| Phone invalid format | -10 | Medium |
| All phone numbers identical | -10 | Medium |
| Physical address incomplete | -20 | Critical |
| PO Box as physical address | -15 | High |
| Physical/mailing mismatch | -5 | Low (informational) |
| Email missing | -10 | Medium |
| Email invalid format | -15 | High |
| Generic email for large fleet | -5 | Low |
| MCS-150 overdue (24-36 months) | -10 | Medium |
| MCS-150 severely stale (36+) | -20 | Critical |
| Shared contact with other carrier | -5 per shared item | Variable |

**Score interpretation:**
- **90-100**: Excellent -- contact info is complete, current, and consistent.
- **70-89**: Good -- minor gaps or age concerns; usable for operations.
- **50-69**: Fair -- multiple issues; verify independently before relying on this data.
- **Below 50**: Poor -- contact info is unreliable; independent verification required before doing business.

### 8. Present the Verification Report

Structure the output as:

```
## Contact Verification: Acme Trucking LLC (DOT 123456)

### Contact Quality Score: 78/100 (Good)

### Contact Information on File
| Type | Value | Status |
|---|---|---|
| Phone | (555) 123-4567 | Valid |
| Fax | (555) 123-4567 | Valid (same as phone) |
| Cell | — | Missing |
| Email | dispatch@example.invalid | Valid (synthetic example) |
| Physical | 123 Main St, Dallas, TX 75201 | Complete |
| Mailing | PO Box 456, Dallas, TX 75201 | Complete (differs from physical) |

### Flags
- [WARNING] Phone and fax are the same number
- [INFO] Cell phone missing
- [INFO] Physical and mailing addresses differ
- [FLAG] MCS-150 filed 26 months ago — biennial update overdue

### Recommendation
Contact data is mostly complete but MCS-150 is overdue. Recommend verifying
phone number is still active before relying on it for dispatch communications.
```

## Examples

Read `{baseDir}/references/examples.md` for the detailed single-carrier, batch, and exception scenarios. The examples use synthetic identifiers.

## Output

Return a contact-verification report with the normalized contact fields, quality
score, evidence-backed flags, freshness assessment, and a clear follow-up
recommendation. Never include API credentials or persist raw API responses.

## Error Handling

| HTTP Status | Meaning | Action |
|---|---|---|
| 401 | Invalid or missing API key | Stop; inform the user to check `SEARCHCARRIERS_API_KEY` |
| 403 | Feature requires Pro tier | Inform the user that contact verification requires a Pro subscription |
| 404 | Carrier not found | Report the DOT as not found; cannot verify contacts for a nonexistent carrier |
| 422 | Invalid parameter | Check DOT format (numeric, 1-8 digits) |
| 429 | Rate limit exceeded | Wait 5 seconds and retry; particularly relevant for multi-carrier cross-references |
| 500+ | Server error | Retry once; report failure |

**Verification-specific errors:**
- If contact fields are all null/empty, report a quality score of 0 and note that the carrier has no contact information on file.
- If MCS-150 date is in an unrecognizable format, skip the freshness check rather than failing.
- If the cross-reference search returns too many results (100+), narrow by adding city/state filters.

## Resources

- SearchCarriers API documentation: `https://searchcarriers.com/docs`
- FMCSA MCS-150 biennial update requirement: carriers must update every 2 years in their assigned month
- FMCSA physical address requirement: must be an actual physical location, not a PO Box or virtual office
- Process agent: a designated representative who accepts legal service on behalf of a carrier; commonly shares an address with many carriers
- Chameleon carrier: a carrier that reincorporates under a new name/DOT to escape an adverse safety record; shared contacts across new and old entities are a key indicator
- Carrier object field reference: `{baseDir}/docs/carrier-fields.md`
- Related skill: `searchcarriers-carrier-lookup` for full carrier data retrieval
- Related skill: `searchcarriers-bulk-processor` for batch contact verification workflows
