# Carrier Intel - Business Case

## Problem Statement

Every freight broker, 3PL, and shipper in the United States faces the same bottleneck: vetting a motor carrier takes too long.

The current process looks like this. A broker gets a load request. They need to verify the carrier before tendering. They open FMCSA SAFER (often slow, sometimes down), manually enter the DOT or MC number, scroll through the results page, copy relevant fields into a spreadsheet or their TMS, then open a second tab to check insurance status, a third tab to verify operating authority, and maybe a fourth to check equipment. This takes 15 to 30 minutes per carrier on a good day. On a bad day -- when SAFER is overloaded or the carrier has a complex corporate structure with related entities -- it takes longer.

This process happens hundreds of times per week at a mid-size brokerage. A 50-person brokerage running 200 loads per day might vet 40 to 60 new carriers daily. At 20 minutes each, that is 13 to 20 hours of pure manual data gathering every single day.

The data is public. The endpoints exist. The problem is not access -- it is workflow. Brokers are switching between browser tabs, copy-pasting DOT numbers, reformatting data, and making transcription errors. They are doing the work of a database query by hand.

## Target Customer

| Segment | Role | Pain Level | Frequency |
|---------|------|-----------|-----------|
| Freight brokers | Carrier sales reps, load planners | High | 20-60 lookups/day |
| Third-party logistics (3PL) | Operations managers, carrier compliance | High | 10-40 lookups/day |
| Shippers | Transportation procurement, carrier management | Medium | 5-20 lookups/week |
| Safety departments | Safety directors, compliance analysts | High | 10-30 lookups/day |
| Insurance underwriters | Motor carrier underwriting teams | Medium | 5-15 lookups/day |

The primary buyer is the freight brokerage with 10 to 500 employees. They have the highest lookup volume, the most to lose from onboarding a bad carrier, and the most to gain from automation. A single cargo claim from a poorly vetted carrier can cost $50,000 to $250,000. Faster, more accurate vetting directly reduces that exposure.

## Market Size

- **TAM**: ~35,000 freight brokerages and 3PLs in the US (FMCSA active broker authorities), plus ~15,000 active shippers with dedicated transportation departments. Approximately 50,000 organizations that regularly vet motor carriers.
- **SAM**: Organizations already using or willing to adopt API-based carrier data tools. Estimated 8,000 to 12,000 companies currently using Carrier411, Highway, DAT carrier monitoring, or similar paid vetting tools.
- **SOM**: SearchCarriers existing user base plus new users attracted by the model-client integration. Year 1 target: 200 to 500 active API subscribers driven by plugin adoption.

## Efficiency Gains

| Metric | Without Plugin | With Plugin | Impact |
|--------|---------------|-------------|--------|
| Time per carrier lookup | 15-30 min (manual SAFER/FMCSA) | 10-15 sec (natural language) | Significantly faster |
| Lookups per day (50-person brokerage) | 40-60 | 40-60 (same volume) | Same throughput, freed labor |
| Daily hours on carrier research | 13-20 hours | Estimated minutes | Hours of manual work eliminated |
| Data accuracy (manual copy errors) | Error-prone (manual transcription) | API-direct (no transcription) | Eliminates transcription errors |
| Carrier profile completeness | Partial (brokers skip fields under time pressure) | Full (automated aggregation) | Better vetting decisions |
| Time to full profile (with authorities + insurance) | 25-45 min | Seconds (API-speed) | On-demand full profiles |

The primary efficiency gain is eliminating manual data gathering. Brokers spend their time evaluating carriers instead of copy-pasting data between browser tabs.

## Competitive Positioning

| Capability | SearchCarriers + Carrier Intel | Manual FMCSA/SAFER | Carrier411 | Highway | DAT Carrier Watch |
|-----------|-------------------------------|--------------------|-----------|---------|--------------------|
| Natural language lookup | Yes ("look up JB Hunt") | No (form fields only) | No | No | No |
| CLI/developer workflow | Yes (MCP-native) | No (browser only) | No | API available | API available |
| Full profile aggregation | Yes (search + authority + insurance in one call) | No (3+ separate pages) | Partial | Yes | Partial |
| Entity mapping (VIN-based) | Yes (find related companies) | No | No | Limited | No |
| Pipeline chaining | Yes (auto-feeds Risk Engine and Ops Reporter) | No | No | No | No |
| 4M+ carrier database | Yes | Yes (same FMCSA source) | Yes | Yes | Yes |
| On-demand API access | Yes (REST API) | No (web scraping fragile) | Yes | Yes | Yes |
| Price (entry tier) | Free (basic lookup) | Free (slow, unreliable) | $35/mo+ | $99/mo+ | Included with DAT |
| Works in terminal/IDE | Yes | No | No | No | No |

**Key differentiator**: No other carrier data tool integrates with a developer's existing workflow. Brokers who use an MCP-capable client (or whose tech teams build on one) get carrier data without leaving their terminal. The plugin turns carrier research from a context switch into a conversation.

**Secondary differentiator**: Pipeline architecture. Carrier Intel is not a standalone tool -- it is the INPUT stage of a three-stage pipeline. Data flows automatically from lookup (Carrier Intel) to risk assessment (Risk Engine) to formatted report (Ops Reporter). No other carrier data platform offers this kind of automated chaining.

## Revenue Model

Carrier Intel drives SearchCarriers API subscription revenue through a tiered access model:

| Plugin Tool | Min Tier | API Calls Per Use | Revenue Driver |
|------------|----------|-------------------|----------------|
| `carrier_lookup` | Free | 1 (search) | Gets users in the door |
| `carrier_profile` | Free | 3 (search + authorities + insurance) | Demonstrates full value |
| `entity_map` | Pro | 2+ (equipment + VIN searches) | Upsell trigger |
| `fleet_summary` | Free | 2 (equipment + vehicles) | Demonstrates data depth |

**Conversion funnel**: Free users get `carrier_lookup` and `carrier_profile` to experience the speed and accuracy. When they need entity mapping to trace corporate structures (a common compliance requirement), they hit the Pro tier gate and see a clear upgrade path with pricing URL.

**Downstream revenue**: Carrier Intel is the entry point. Users who adopt it naturally want risk scoring (Risk Engine, Pro) and formatted reports (Ops Reporter, Pro). The stackable pipeline creates a natural upsell path from Free to Pro to Pro+ as users discover each stage.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| API uptime dependency | Medium | High -- plugin is useless if API is down | Implement retry logic with exponential backoff, cache recent results (5 min TTL), surface clear error messages with status page URL |
| Data freshness lag | Low | Medium -- FMCSA data can be 24-48 hours behind | Document sync frequency in user-facing output, add "last updated" timestamps to carrier profiles |
| API rate limiting | Medium | Medium -- heavy users hit 3 req/s ceiling | Client-side request queuing, batch operations for bulk use cases, cache layer reduces redundant calls |
| FMCSA source changes | Low | High -- upstream schema changes break field mappings | SearchCarriers abstracts FMCSA, so this risk is on their side. Monitor for carrier object field changes |
| Competitor replication | Medium | Low -- anyone can wrap FMCSA data | Our moat is the pipeline architecture + the model-client integration, not the raw data access |
| MCP client or protocol changes | Low | High -- MCP protocol changes could break plugin | Pin MCP protocol version, maintain backward compatibility, follow the MCP specification and supported client changelogs |
| Low adoption / market fit | Medium | Medium -- developers may not be the buyers | Target tech-forward brokerages first, provide clear efficiency documentation for procurement justification |
