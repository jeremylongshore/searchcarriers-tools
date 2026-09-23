# Risk Engine - Business Case

## Problem Statement

Carrier vetting in the freight industry is manual, inconsistent, and dangerously subjective. A broker receives a load request, checks if the carrier has active authority, maybe glances at their insurance, and tenders the load. The entire decision rests on gut feel and a cursory SAFER check.

The consequences are measurable. The FBI estimates $500 million in annual cargo theft losses. The FMCSA reports over 500,000 crashes involving large trucks every year. Insurance claims from poorly vetted carriers cost brokerages $50,000 to $250,000 per incident. Yet the typical carrier qualification process at a mid-size brokerage is a 10-question checklist on a spreadsheet that someone fills out inconsistently between lunch and their next phone call.

The data to make better decisions already exists. Safety scores, inspection results, crash history, insurance filings, authority status, MCS-150 filing recency, out-of-service rates -- it is all public record. The problem is that no one has time to pull it all together, weight the factors, and produce a consistent risk assessment for every carrier, every time. A broker vetting 30 carriers a day cannot spend 20 minutes computing a risk score by hand. So they skip it.

## Target Customer

| Segment | Role | Pain Level | Frequency |
|---------|------|-----------|-----------|
| Freight brokers | Carrier sales, load planners | Critical | 20-60 vets/day |
| Third-party logistics (3PL) | Carrier compliance, ops managers | Critical | 10-40 vets/day |
| Shippers | Transportation procurement | High | 5-20 vets/week |
| Compliance managers | Safety, regulatory compliance | Critical | 10-30 audits/day |
| Insurance underwriters | Motor carrier underwriting | High | 5-15 risk assessments/day |

The primary buyer is the freight brokerage compliance department or the broker-principal who carries personal liability for carrier selection. A single bad carrier decision -- revoked authority, lapsed insurance, chameleon entity -- can trigger cargo claims, FMCSA fines, and loss of contingent cargo coverage. Automated risk scoring reduces the chance of onboarding a carrier with known red flags in public FMCSA data.

## Market Size

- **TAM**: Same 50,000 organizations that vet carriers (freight brokerages, 3PLs, shippers). All of them need risk assessment; none of them do it systematically.
- **SAM**: ~8,000-12,000 companies currently paying for carrier vetting tools (Carrier411, Highway, RMIS, SaferWatch). These organizations already spend money on carrier qualification.
- **SOM**: SearchCarriers existing user base converting from Free (Carrier Intel) to Pro/Pro+ for risk scoring and vetting. Year 1 target: 100-300 Pro/Pro+ subscribers driven by Risk Engine adoption.

## Efficiency Gains

| Metric | Without Risk Engine | With Risk Engine | Impact |
|--------|-------------------|-----------------|--------|
| Time per carrier risk assessment | 15-30 min (manual) | Seconds (automated) | Significantly faster |
| Assessment consistency | Varies by person, mood, workload | Same algorithm every time | Eliminates human inconsistency |
| Compliance audit readiness | Manual documentation | Structured audit trail | Faster audit preparation |
| Insurance documentation | Ad hoc checks | Systematic gap detection | More thorough vetting records |

The primary value is consistency and speed. Manual risk assessment is slow and subjective -- it depends on who does it, how busy they are, and what they remember to check. Automated scoring applies the same weighted criteria to every carrier, every time. This does not guarantee better outcomes, but it eliminates the variability in the vetting process and creates a documented audit trail.

## Competitive Positioning

| Capability | Risk Engine | Carrier411 | Highway | RMIS | SaferWatch |
|-----------|------------|-----------|---------|------|------------|
| Composite risk score (0-100) | Yes | No (pass/fail only) | Yes (A-F grade) | No | No |
| Configurable vetting rules | Yes (Pro+) | Limited | Yes | Yes | Limited |
| Insurance gap detection | Yes | Manual check | Yes | Yes | Basic |
| MCS-150 compliance audit | Yes | No | Limited | No | No |
| Current FMCSA data (nightly sync) | Yes (via SearchCarriers API) | Nightly batch | On-demand | Daily batch | Nightly batch |
| Pipeline integration | Yes (Carrier Intel -> Risk Engine -> Ops Reporter) | Standalone | Standalone | Standalone | Standalone |
| CLI / developer workflow | Yes (Claude Code native) | No | No | No | No |
| Price (risk scoring) | $49/mo (Pro) | $35/mo+ | $99/mo+ | $200/mo+ | $15/mo+ |

**Key differentiator**: Transparent, weighted composite scoring. Most competitors give a pass/fail or letter grade with no visibility into how the score was computed. Risk Engine returns the composite score AND the breakdown -- safety weight, insurance weight, authority weight, operational weight -- so the broker can see exactly why a carrier scored 62 instead of 85.

**Secondary differentiator**: Pipeline architecture. Risk Engine consumes structured data from Carrier Intel and feeds structured assessments to Ops Reporter. The vetting workflow is automated end-to-end. No other carrier risk tool chains data retrieval, risk analysis, and report generation into a single conversational flow.

## Revenue Model

Risk Engine is the primary upsell from Free-tier Carrier Intel to paid subscriptions:

| Plugin Tool | Min Tier | Monthly Price | Revenue Driver |
|------------|----------|--------------|----------------|
| `risk_score` | Pro | $49/mo | Core value prop -- automated risk scoring |
| `insurance_check` | Pro | $49/mo | Insurance validation and gap detection |
| `compliance_audit` | Pro | $49/mo | Regulatory compliance posture |
| `vetting_check` | Pro+ | $99/mo | Custom rules engine -- enterprise upsell |

**Conversion funnel**: Users discover SearchCarriers through Carrier Intel (Free). They look up a carrier, see the data, and immediately want to know "is this carrier safe?" That question is the Risk Engine's entry point. The Free tier shows the raw data; Pro tier interprets it into structured risk scores. Pro+ adds custom vetting rules for organizations that need configurable qualification criteria.

**Downstream revenue**: Users who adopt risk scoring naturally want formatted vetting reports (Ops Reporter, Pro). The three-plugin pipeline creates a natural progression: look up (Free) -> assess risk (Pro) -> generate report (Pro) -> custom rules (Pro+).

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Scoring algorithm inaccuracy | Medium | High -- bad scores erode trust | Weight calibration against known carrier outcomes; user feedback loop; transparent scoring breakdown; disclaimer that scores are advisory |
| Liability from vetting recommendations | Medium | High -- "your tool said PASS" | Clear disclaimers: not legal advice, not a compliance guarantee, not a replacement for broker judgment. Vetting_check returns PASS/REVIEW/FAIL, not "hire this carrier" |
| Missing data fields | High | Medium -- carriers with sparse FMCSA data get unreliable scores | Handle missing data gracefully with confidence indicators; flag scores computed with incomplete data |
| Algorithm gaming | Low | Medium -- carriers could optimize for score factors | Use multiple weighted factors; do not publish exact weights; rotate weight emphasis periodically |
| Regulatory scrutiny | Low | High -- FMCSA could object to automated vetting scores | Position as decision-support, not decision-making; maintain "broker judgment required" language throughout |
| Competitor replication | Medium | Low -- scoring algorithms are defensible through calibration data | Moat is pipeline integration + calibration data, not the algorithm concept |
