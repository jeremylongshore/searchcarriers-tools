# SearchCarriers workflow and skill research

Reviewed: 2026-09-23

This research defines the user problems the skills must solve. It separates
market evidence from product capability and from the decision limits imposed by
SearchCarriers' terms. The skill pack should be revised when any source contract
or operating assumption changes.

## Findings that shape the product

| Pain point | Evidence | Skill response |
|---|---|---|
| Trusted carrier discovery is a high-volume job | A 2025 Truckstop broker survey reported that finding a trusted carrier was respondents' biggest challenge. The average brokerage worked with about 175 carriers monthly; firms with fewer than five people worked with about 35. | Search must narrow a lane and equipment need with documented API filters, preserve pagination, and then route candidates through identity, authority, insurance, and qualification. A search hit is never an approval. |
| Fraud is identity and authorization failure, not just a bad safety record | FMCSA warns about unauthorized use of USDOT numbers, unregistered brokering, fake search results, and fraudulent insurance certificates. Its guidance calls for checking multiple sources and directly calling relevant companies. | Fraud and contact skills return a hold/review state, record exact mismatches, and prescribe callback through a previously trusted channel. They never declare fraud from an API signal. |
| Legitimate history does not remove current identity risk | Highway's Q4 2025 index described direct theft involving carriers with real equipment and operating histories, plus compromised inboxes and manipulated identities. It recommends verifying reroutes through original trusted contacts. | Contact consistency and event workflows treat changed email, phone, pickup, or destination instructions as a new verification event even when the carrier has a clean historical record. |
| Registration identity controls changed materially | FMCSA launched Motus in 2026 with identity verification and third-party business validation after describing low barriers and fragmented legacy systems. | Entity and authority skills must preserve exact DOT/docket identity, distinguish current status from history, and avoid assumptions based on sequential identifiers or names. |
| Insurance cannot use one blanket threshold | FMCSA says requirements vary by entity type, authority, cargo, and vehicle type. Active for-hire authority also depends on proof of financial responsibility. | Insurance validation starts with the intended operation and a cited requirement or supplied company policy, then reconciles filings, coverage, dates, insurer, and cancellations. Missing type/amount is Review, not Pass. |
| Carrier policy varies by customer and commodity | SearchCarriers 1.31 added named qualifications with Pass/Review/Fail evidence and team controls, plus a v2 qualification-report endpoint. | Vetting skills prefer named upstream qualifications, preserve the criteria snapshot, and apply only caller-approved supplemental rules. They no longer invent “standard” thresholds. |
| Operations need partial-failure and restart semantics | Broker carrier-panel volume, API quotas, rate limits, and per-record data errors make all-or-nothing batches unreliable. | Bulk and TMS workflows use input hashes, run IDs, checkpoints, idempotency keys, error manifests, bounded retries, dry runs, rereads, and rollback receipts. |
| API data has contractual decision and storage limits | SearchCarriers permits internal research and decisions within plan limits, says its analytics are not endorsements or official safety ratings, bars FCRA-regulated eligibility uses, and requires data minimization and refresh. | Every skill separates facts from policy/model judgment, includes source/as-of and missing evidence, avoids official-safety or guarantee language, minimizes exports, and keeps live API data out of the repository. |
| Current API capability is much richer than identifier lookup | The public API exposes fleet-size, insurance, registration-date, authority-age, equipment/cargo, and independent lane origin/destination radius filters. Release 1.31 also adds qualification reports and MCP search filters. | `carrier_lookup` now maps the verified advanced filters through the shared API contract, with route-contract tests that assert exact outgoing names. |

## Skill design contract

Each skill must answer five questions:

1. What single operational job is the user trying to complete?
2. Which documented API route or MCP tool supplies the decisive evidence?
3. What facts are observed, what rules come from policy, and what statements are inference?
4. What bounded status can the available evidence support, including missing data?
5. Who owns the next action, and what exactly must they do?

The standard output is an auditable decision record with subject, purpose,
bounded status, sourced evidence, as-of date, missing evidence, named policy or
method, next action, and limitations. Batch workflows add input hash, run ID,
per-record status, checkpoint, and error manifest.

## Sources

- [SearchCarriers API documentation](https://searchcarriers.com/docs/api)
- [SearchCarriers 1.31.0 release notes](https://searchcarriers.com/changelog/1.31.0)
- [SearchCarriers terms of service](https://searchcarriers.com/terms-of-service)
- [FMCSA: Broker and Carrier Fraud and Identity Theft](https://www.fmcsa.dot.gov/mission/help/broker-and-carrier-fraud-and-identity-theft)
- [FMCSA: Insurance Filing Requirements](https://www.fmcsa.dot.gov/registration/insurance-filing-requirements)
- [FMCSA: insurance requirements vary by operation](https://www.fmcsa.dot.gov/faq/how-do-i-request-change-minimum-insurance-requirements-my-companys-operating-authority)
- [FMCSA: Motus anti-fraud registration launch](https://www.fmcsa.dot.gov/newsroom/trumps-transportation-secretary-sean-p-duffy-launches-new-anti-fraud-registration-system)
- [TIA: State of Fraud in the Industry, April 2025](https://news.tianet.org/tia-releases-state-of-fraud-in-the-industry-april-2025-report/)
- [Truckstop broker survey coverage](https://www.foodlogistics.com/transportation/trucking/news/22938198/truckstopcom-truckstop-survey-reveals-trust-is-top-priority-for-brokers-in-2025)
- [Highway Q4 2025 Freight Fraud Index](https://highway.com/press-releases/highway-releases-q4-2025-freight-fraud-index-revealing-the-rise-of-carrier-involved-theft)
