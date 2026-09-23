# Vetting report format

Use the current route map in the repository `API-DISCOVERY.md`.

Produce a comprehensive, structured vetting report:

```
========================================
CARRIER VETTING REPORT
========================================
DOT Number: {dot_number}
Carrier: {legal_name}
DBA: {dba_name}
MC Number: {mc_number}
Report Date: {today}
Rule Set: {default / custom file path / inline}

CARRIER SNAPSHOT
  Status: {status_code} ({status_description})
  Operation: {carrier_operation}
  Fleet: {power_units} power units, {total_drivers} drivers
  Safety Rating: {safety_rating} ({safety_rating_date})
  Hazmat: {hm_ind}
  Officers: {company_officers}

========================================
RULE RESULTS
========================================

  [1] ACTIVE STATUS                    {PASS/FAIL/REVIEW}
      Expected: status_code = 'A'
      Actual:   status_code = '{value}'

  [2] OPERATING AUTHORITY              {PASS/FAIL/REVIEW}
      Expected: common_authority_status = 'authorized'
      Actual:   common_authority_status = '{value}'

  [3] INSURANCE ACTIVE                 {PASS/FAIL/REVIEW}
      Expected: At least one active BIPD policy
      Actual:   {count} active BIPD policies found

  [4] INSURANCE MINIMUM                {PASS/FAIL/REVIEW}
      Expected: BIPD >= ${minimum}
      Actual:   BIPD = ${actual}

  [5] MCS-150 CURRENT                  {PASS/FAIL/REVIEW}
      Expected: Filed within 24 months
      Actual:   Filed {X} months ago

  [6] SAFETY RATING                    {PASS/FAIL/REVIEW}
      Expected: Satisfactory or Conditional
      Actual:   {rating}

  [7] AUTHORITY AGE                    {PASS/FAIL/REVIEW}
      Expected: >= 18 months
      Actual:   {X} months

  [8] NO PRIOR REVOCATION              {PASS/FAIL/REVIEW}
      Expected: prior_revoke_flag = 'N'
      Actual:   prior_revoke_flag = '{value}'

  [9] FLEET SIZE                       {PASS/FAIL/REVIEW}
      Expected: >= {minimum} power units
      Actual:   {count} power units

  [10] OOS RATE                        {PASS/FAIL/REVIEW}
       Expected: Vehicle OOS <= 30%, Driver OOS <= 30%
       Actual:   Vehicle OOS = {X}%, Driver OOS = {Y}%

  [11] HAZMAT COMPLIANCE               {PASS/FAIL/REVIEW}
       Expected: No hazmat violations
       Actual:   {count} violations found

========================================
VERDICT
========================================
  Rules Passed:  {count}/{total}
  Rules Failed:  {count}/{total}
  Rules Review:  {count}/{total}

  OVERALL: {PASS / FAIL / REVIEW WITH EXCEPTIONS}
  Reason: {explanation}

========================================
NOTES
========================================
  [Any additional context, warnings, or recommendations]
```
