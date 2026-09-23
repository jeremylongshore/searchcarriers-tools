# Carrier Intel - User Journey

## Persona

**Name:** Sarah Chen
**Role:** Senior Freight Broker at a mid-size 3PL (75 employees, 300 loads/day)
**Goal:** Vet carriers fast enough to keep up with load volume without cutting corners on safety
**Tier:** Free (evaluating for team-wide Pro upgrade)
**Current workflow:** Opens FMCSA SAFER in a browser, manually searches DOT, copies fields into a Google Sheet, then checks authority and insurance on separate pages. Takes 15-25 minutes per carrier. She does this 30 times a day.
**Pain:** By 2 PM she is behind on vetting and starts rubber-stamping carriers she should be checking more carefully. Last quarter, her company had a $180,000 cargo claim from a carrier whose authority had lapsed two weeks before the load.

## Prerequisites

- [ ] SearchCarriers account (Free tier or above) -- sign up at [searchcarriers.com](https://searchcarriers.com)
- [ ] API key generated at [searchcarriers.com/settings/api-tokens](https://searchcarriers.com/settings/api-tokens)
- [ ] API key set in environment: `export SEARCHCARRIERS_API_KEY="your_id|your_token"`
- [ ] Grok Build, Claude Code, or another MCP-capable client installed
- [ ] Plugin installed: copy `searchcarriers-carrier-intel/` to `.claude/plugins/` or configure in `.mcp.json`

## Step-by-Step Walkthrough

### Step 1: Look Up a Carrier by Name

Sarah has a new carrier requesting to haul a load. She knows the name: Werner Enterprises.

```
/sc-lookup Werner Enterprises
```

**What happens behind the scenes:**
1. the MCP client invokes `carrier_lookup` with `search_term="Werner Enterprises"`
2. The MCP server detects this is a name (not DOT/MC/VIN), uses `superSearchTerm`
3. API call: `GET /api/v3/search?superSearchTerm=Werner+Enterprises`
4. Results returned, formatted by the MCP client

**Expected output:**

```
Found 3 carriers matching "Werner Enterprises":

1. WERNER ENTERPRISES INC
   DOT: 69494 | MC: MC-14983
   Status: Active | Rating: Satisfactory
   Location: Omaha, NE
   Power Units: 7,880 | Drivers: 12,525
   Operation: Authorized For Hire, Interstate

2. WERNER ENTERPRISES INC (DBA Werner Global Logistics)
   DOT: 2853291 | MC: MC-954017
   Status: Active | Rating: None
   Location: Omaha, NE
   Power Units: 0 | Drivers: 0
   Operation: Broker

3. WERNER ENTERPRISES LTD
   DOT: 3245108 | MC: N/A
   Status: Active | Rating: None
   Location: Steinbach, MB (Canada)
   Power Units: 12 | Drivers: 15
   Operation: Authorized For Hire
```

Sarah immediately sees the main Werner entity (DOT 69494) with 7,880 power units and a Satisfactory safety rating. She notes the DOT number for the next step.

### Step 2: Get the Full Carrier Profile

Sarah needs the complete picture -- authorities and insurance -- before she can tender this load.

```
/sc-profile 69494
```

**What happens behind the scenes:**
1. the MCP client invokes `carrier_profile` with `dot_number="69494"`
2. MCP server makes one field-selected API call:
   - `GET /api/v3/company/69494?fields=contact,safety,authorities,insurance,...`
3. Selected nested sections are returned as one profile

**Expected output:**

```
CARRIER PROFILE: WERNER ENTERPRISES INC (DOT 69494)
====================================================

IDENTITY
  Legal Name:    WERNER ENTERPRISES INC
  DBA:           --
  DOT:           69494
  MC:            MC-14983
  Status:        Active (since 1981-01-27)
  Entity Type:   Carrier, Broker
  DUNS:          00-601-3120

CONTACT
  Phone:         (402) 895-6640
  Address:       14507 FRONTIER RD, OMAHA, NE 68138

FLEET
  Power Units:   7,880
  Total Drivers: 12,525
  CDL Drivers:   12,525
  Fleet Size:    Category F (1,000+)

OPERATIONS
  Interstate:    Yes
  Hazmat:        Yes
  Cargo Types:   General Freight, Household Goods, Metal/Sheets/Coils,
                 Motor Vehicles, Refrigerated Food, Beverages, Chemicals

SAFETY
  Rating:        Satisfactory
  Rating Date:   2019-03-15

AUTHORITIES
  Common Authority:   Active (since 1981-01-27)
  Contract Authority: Active (since 1981-01-27)
  Broker Authority:   Active (since 2006-04-14)
  Property:           Yes
  Household Goods:    Yes

INSURANCE
  Bodily Injury & Property Damage:  $5,000,000 (Active)
  Cargo:                            $250,000 (Active)
  Surety Bond (Broker):             $75,000 (Active)
```

Sarah can see in a single response what would normally require navigating three separate browser tabs. Active authorities, active insurance with adequate limits, Satisfactory safety rating. She is ready to tender this load.

### Step 3: Entity Mapping (Pro Tier)

Sarah's compliance team flagged a small carrier (DOT 3891456) that recently got a new operating authority. They want to check if it is connected to any previously revoked carriers -- a common pattern with chameleon carriers.

```
Look up related companies for DOT 3891456 using shared equipment
```

**What happens behind the scenes:**
1. the MCP client invokes `entity_map` with `dot_number="3891456"`
2. MCP server checks tier: user must be Pro or above
3. API calls: `GET /company/3891456/equipment` to get VINs, then `GET /search/by-vin/` per VIN
4. Results mapped into a relationship network

**Expected output (Pro tier):**

```
ENTITY MAP: DOT 3891456 (QUICK HAUL TRANSPORT LLC)
====================================================

Equipment scanned: 8 VINs

RELATED CARRIERS FOUND:

  VIN 1FUJGHDV0CLBP8834 (2012 Freightliner Cascadia)
    Also registered to:
    - FAST FREIGHT SOLUTIONS INC (DOT 2987123) -- Status: REVOKED
      Authority revoked: 2025-09-14
      Same physical address as Quick Haul Transport

  VIN 3AKJHHDR5KSKL9021 (2019 Freightliner Cascadia)
    Also registered to:
    - FAST FREIGHT SOLUTIONS INC (DOT 2987123) -- Status: REVOKED

SUMMARY:
  5 of 8 VINs are unique to DOT 3891456
  3 VINs shared with 1 other carrier
  *** RED FLAG: Related carrier DOT 2987123 has REVOKED authority ***
  *** RED FLAG: Shared physical address detected ***
```

This is the entity mapping that justifies the Pro upgrade. Sarah's compliance team just found a probable chameleon carrier through a single command that would otherwise require manually cross-referencing VINs across multiple FMCSA records.

**Expected output (Free tier):**

```
Entity mapping requires a Pro subscription.
Your current tier: Free

Upgrade at https://searchcarriers.com/pricing to access:
  - Entity mapping (discover related companies via shared equipment)
  - VIN-based relationship analysis
  - Chameleon carrier detection

carrier_lookup and carrier_profile are available on your current Free tier.
```

### Step 4: Fleet Summary

Sarah wants to verify that a carrier actually has the reefer trailers they claim to have before booking a temperature-controlled load.

```
/sc-lookup KLLM Transport
```

Then, using the DOT from the results:

```
Show me the fleet summary for DOT 27021
```

**What happens behind the scenes:**
1. the MCP client invokes `fleet_summary` with `dot_number="27021"`
2. MCP server makes two API calls:
   - `GET /company/27021/equipment` (detailed equipment with VIN, make, model)
   - `GET /company/27021/vehicles` (simplified vehicle list)
3. Results combined into fleet overview

**Expected output:**

```
FLEET SUMMARY: KLLM TRANSPORT SERVICES INC (DOT 27021)
========================================================

OVERVIEW
  Power Units:      2,156
  Total Drivers:    2,489
  Driver/Unit Ratio: 1.15

EQUIPMENT BREAKDOWN
  Type             Count    % of Fleet
  ----             -----    ----------
  Tractors           987       45.8%
  Reefer Trailers    842       39.1%
  Dry Vans           198        9.2%
  Flatbeds            67        3.1%
  Other               62        2.8%

TOP MAKES
  Freightliner:    612 units
  Kenworth:        298 units
  Peterbilt:       187 units
  Volvo:           109 units
  International:    78 units

YEAR DISTRIBUTION
  2020-2025:     1,245 units (57.7%)
  2015-2019:       634 units (29.4%)
  2010-2014:       198 units  (9.2%)
  Pre-2010:         79 units  (3.7%)
```

Sarah confirms KLLM has 842 reefer trailers -- they are a legitimate reefer carrier. The fleet is mostly newer equipment (57% from 2020 onward), which suggests well-maintained trucks and lower breakdown risk.

## Error Scenarios

### Scenario: API Key Not Set

**Trigger:** Running any command without `SEARCHCARRIERS_API_KEY` in environment.

```
/sc-lookup Werner
```

**Response:**

```
SearchCarriers API key is not configured.

To set up your API key:
1. Sign up or log in at https://searchcarriers.com
2. Go to Settings > API (https://searchcarriers.com/settings/api-tokens)
3. Generate a new API token
4. Set the environment variable:

   export SEARCHCARRIERS_API_KEY="your_id|your_token"

   Or add it to your .env file for persistence.
```

### Scenario: Insufficient Tier

**Trigger:** Free user attempts to use `entity_map`.

```
Map entities for DOT 3891456
```

**Response:**

```
Entity mapping requires a Pro subscription.
Your current tier: Free

This tool uses VIN-based searches to discover related companies, shell
entities, and chameleon carriers. It requires multiple API calls per carrier.

Upgrade at https://searchcarriers.com/pricing

Tools available on your Free tier:
  - carrier_lookup: Search carriers by DOT, MC, name, or VIN
  - carrier_profile: Full profile with authorities and insurance
  - fleet_summary: Equipment roster and fleet breakdown
```

### Scenario: Carrier Not Found

**Trigger:** Searching for a DOT that does not exist in the database.

```
/sc-profile 99999999
```

**Response:**

```
No carrier found for DOT 99999999.

This could mean:
  - The DOT number is incorrect (check for typos)
  - The carrier is not yet in the SearchCarriers database
  - The carrier has been permanently removed from FMCSA records

Try searching by name instead:
  /sc-lookup "company name"

Or search by MC number:
  /sc-lookup MC 123456
```

### Scenario: Rate Limit Hit

**Trigger:** Running entity_map on a carrier with a large fleet during a busy period.

**Response:**

```
Rate limit reached on SearchCarriers API. Waiting 2 seconds before retrying...

Progress: 34 of 87 VINs scanned (39%)
Related carriers found so far: 2

[Retrying...]

Progress: 87 of 87 VINs scanned (100%)

ENTITY MAP: [results follow]
```

### Scenario: API Timeout

**Trigger:** SearchCarriers API is slow or temporarily unavailable.

**Response:**

```
SearchCarriers API timed out after 10 seconds. Retrying (attempt 2 of 3)...

If this persists, check API status at https://searchcarriers.com/status
```

## FAQ

**Q: How fresh is the data?**
A: SearchCarriers syncs from FMCSA nightly. Most carrier records are less than 24 hours behind the federal source. Authority and insurance updates may take 24 to 48 hours to propagate. Inspection records are typically available within 48 hours of the roadside event.

**Q: What about inactive or revoked carriers?**
A: Inactive and revoked carriers remain in the database. You can search for them by DOT, MC, or name. Their status will show as "Inactive," "Revoked," or "Not Authorized." This is intentional -- compliance teams need to look up revoked carriers to check for chameleon patterns (new authority, same trucks).

**Q: Can I search by MC number?**
A: Yes. Use the format `MC 123456` or just the number. The auto-detection in `carrier_lookup` recognizes MC format and routes to the correct search parameter. Example: `/sc-lookup MC 14983` finds Werner Enterprises.

**Q: What if a carrier has no insurance records?**
A: The `carrier_profile` tool returns an empty insurance array. This does not necessarily mean the carrier is uninsured -- it may mean their insurance filings have not been recorded in the FMCSA system yet, or the carrier is a broker-only entity that carries surety bonds instead of cargo insurance.

**Q: How is this different from the SearchCarriers website?**
A: The website gives you a visual dashboard with saved searches, charts, and export options. The Carrier Intel plugin gives you the same data through natural language in your terminal. Use the website for exploration and visual analysis. Use the plugin for quick lookups during active load planning, for automated pipelines (search -> vet -> report), and for integration into developer workflows.

**Q: Can I look up Canadian or Mexican carriers?**
A: The SearchCarriers database includes carriers registered with FMCSA, which includes US carriers, Canadian carriers with US operating authority, and Mexican carriers with US operating authority. Purely domestic Canadian or Mexican carriers that do not operate in the US are not in the database.

**Q: What counts as a "power unit"?**
A: Power units are self-propelled vehicles (trucks, tractors, buses) used in revenue-generating service. Trailers are not power units. The FMCSA uses power unit count as a primary measure of carrier size. A carrier with 10 power units is small; 100 is mid-size; 1,000+ is large.

**Q: Does entity_map find ALL related companies?**
A: Entity mapping finds companies that share equipment (VINs) with the target carrier. This catches the most common relationship patterns: chameleon carriers reusing trucks, sister companies sharing fleets, and owner-operators leased to multiple carriers. It does not find relationships based on shared addresses, shared officers, or shared phone numbers -- those require different analysis that may be added in future versions.
