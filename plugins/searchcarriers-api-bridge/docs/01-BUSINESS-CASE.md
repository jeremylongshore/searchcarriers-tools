# API Bridge - Business Case

## Problem Statement

Single carrier lookups solve the individual broker's problem. But operations teams at mid-size and large freight companies do not vet carriers one at a time. They onboard 50 carriers in a batch after a sales blitz. They re-qualify their entire approved panel -- 200 to 500 carriers -- every quarter. They need carrier data flowing into their TMS without manual re-keying. They need to know when the API they depend on is degraded before their dispatch team discovers it at 6 AM on a Monday.

The current process at a 500-carrier brokerage looks like this. The compliance team exports a list of DOT numbers from their TMS. An analyst opens FMCSA SAFER, types each DOT into the search box, copies the results into a spreadsheet, and repeats 500 times. This takes two to three full working days. Then someone reformats the spreadsheet into the TMS import template -- different column names, different date formats, different status codes. Another half day. If any carrier's data changed since the last re-qualification, nobody knows until the next cycle.

For organizations that have adopted SearchCarriers and the Carrier Intel plugin, individual lookups are fast. But running 500 individual `carrier_lookup` commands is still manual, still sequential, and still disconnected from their TMS. The data lives in Claude's context but not in the system of record where dispatch and operations need it.

The API Bridge plugin closes this gap. Bulk operations, TMS-ready exports, API health monitoring, and webhook management -- the integration layer that connects SearchCarriers to enterprise freight operations.

## Target Customer

| Segment | Role | Pain Level | Frequency |
|---------|------|-----------|-----------|
| Mid-size brokerages (50-500 carriers) | IT managers, compliance leads | High | Weekly batch re-quals, daily API monitoring |
| Large 3PLs (500+ carriers) | IT directors, systems integrators | Critical | Daily bulk operations, TMS sync cycles |
| Enterprise shippers | Transportation procurement, vendor management | High | Monthly panel re-qualification |
| Freight tech teams | Developers, DevOps engineers | Medium | Ongoing API monitoring, webhook integration |

The primary buyer is the IT director or systems integrator at a freight brokerage or 3PL with 200+ carriers on their approved panel. They have a TMS (McLeod, TMW, MercuryGate, Aljex, Tai, or a custom build), they need carrier data inside it, and they need the pipeline to be automated and monitored. Today they build custom integrations from scratch or pay for expensive middleware. API Bridge gives them bulk operations, TMS formatting, and monitoring in a single plugin.

## Market Size

- **TAM**: Same ~50,000 organizations that vet motor carriers (freight brokerages, 3PLs, shippers). Every organization that vets carriers at volume eventually needs batch operations and TMS integration.
- **SAM**: ~3,000-5,000 organizations with 200+ carrier panels that currently use or are evaluating API-based carrier data tools. These are the companies where manual carrier data management is a measurable labor cost.
- **SOM**: SearchCarriers users who outgrow individual lookups and need batch/integration capabilities. Year 1 target: 50-100 SMB subscribers, 10-25 Enterprise subscribers. SMB adoption is driven by bulk_lookup utility; Enterprise by TMS sync value.

The API Bridge market is smaller than Carrier Intel (fewer companies need batch operations than need individual lookups) but higher revenue per customer. A single Enterprise subscriber at $499/month generates more annual revenue than 60 Free-tier Carrier Intel users.

## Efficiency Gains

| Metric | Without API Bridge | With API Bridge | Impact |
|--------|-------------------|-----------------|--------|
| Quarterly panel re-qualification (500 carriers) | Days of manual work | Estimated minutes (bulk_lookup) | Eliminates manual per-carrier lookups |
| TMS data import per carrier | 10-15 min (manual re-keying) | Automated (tms_sync export) | Eliminates re-keying entirely |
| API outage detection | When dispatch complains | On-demand (api_health) | Proactive vs. reactive |
| Carrier Watch webhook setup | Web UI, manual per-endpoint | CLI bulk management | Faster configuration |
| Monthly labor on carrier data management | Significant (mid-size brokerage) | Substantially reduced | Frees analyst time for higher-value work |

The primary value is turning batch carrier operations from a multi-day manual process into an automated workflow. Enterprise customers who add TMS sync eliminate the manual re-keying step entirely -- removing a common source of transcription errors.

## Competitive Positioning

| Capability | API Bridge | Manual Process | Carrier411 | Highway | RMIS |
|-----------|-----------|----------------|-----------|---------|------|
| Bulk carrier lookup (100 DOTs) | Yes (one command) | No (one at a time) | CSV upload | API batch | API batch |
| TMS-formatted export | Yes (McLeod, TMW, CSV) | Manual reformatting | CSV only | API/JSON | CSV/PDF |
| API health monitoring | Yes (endpoint-level) | No | No | Status page only | No |
| Webhook management via CLI | Yes (CRUD) | Web UI only | N/A | N/A | N/A |
| Rate limit visibility | Yes (on-demand) | No | No | No | No |
| Works in terminal/IDE | Yes (Claude Code native) | No | No | No | No |

**Key differentiator**: API Bridge is the only carrier data integration tool that operates from a developer's terminal. IT teams building carrier data pipelines get bulk operations, TMS formatting, health monitoring, and webhook management without writing custom integration code or navigating web dashboards.

**Secondary differentiator**: TMS field mapping. Other tools export raw data. API Bridge maps SearchCarriers carrier fields to TMS-specific column names and formats, producing import-ready files for the major freight TMS platforms. No intermediate spreadsheet manipulation required.

## Revenue Model

API Bridge drives SMB and Enterprise tier subscription revenue:

| Plugin Tool | Min Tier | Revenue Driver |
|------------|----------|----------------|
| `api_health` | SMB ($199/mo) | Operations teams need uptime visibility before they trust API-dependent workflows |
| `bulk_lookup` | SMB ($199/mo) | Batch processing is the gateway to enterprise adoption -- once teams run bulk re-quals, they are locked in |
| `webhook_manage` | SMB ($199/mo) | Webhook configuration drives Carrier Watch adoption (recurring monitoring revenue) |
| `tms_sync` | Enterprise ($499/mo) | TMS integration is the highest-value feature -- it replaces custom middleware |

**Conversion funnel**: Organizations start with Carrier Intel (Free) for individual lookups. When they need to scale to batch operations, they hit the SMB tier gate. When they need TMS integration, they upgrade to Enterprise. Each tier increase reflects a deeper operational dependency on SearchCarriers.

**Retention driver**: TMS integrations are sticky. Once a brokerage configures their McLeod import to consume API Bridge output, switching costs are high. The webhook configurations and bulk processing workflows become part of their operational infrastructure.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Rate limit exhaustion on bulk operations | High | Medium -- 100-carrier batch at 3 req/s takes 33+ seconds | Client-side rate limiter with progress reporting, configurable concurrency |
| TMS format drift | Medium | Medium -- TMS vendors change import formats | Version TMS mappings, document field maps, let users override mappings |
| Webhook endpoint reliability | Medium | Low -- webhook delivery is SearchCarriers server-side | API Bridge only manages configuration, not delivery; document this boundary |
| API key permission scope | Low | High -- bulk operations amplify the impact of a compromised key | Document minimum required scopes, recommend key rotation schedule |
| Large batch timeouts | Medium | Medium -- 100 DOTs with full profiles could exceed MCP tool timeout | Chunked processing with progress callbacks, configurable batch size |
| Enterprise pricing resistance | Medium | Medium -- $499/month is a premium tier | Document concrete efficiency gains; TMS sync value is quantifiable per-organization |
