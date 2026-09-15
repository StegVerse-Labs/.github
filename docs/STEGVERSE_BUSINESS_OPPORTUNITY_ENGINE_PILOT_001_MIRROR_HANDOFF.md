# StegVerse Business Opportunity Engine Pilot Mirror Handoff

Updated: 2026-09-15
Repository: `StegVerse-Labs/.github`
Goal Task ID: `STEGVERSE-BUSINESS-OPPORTUNITY-ENGINE-PILOT-001`
COSV profile: `task.v1`
COSV vector: `10100000110000`
Status: `ACTIVE / UNCLAIMED / REGISTRATION REPAIR IN PROGRESS`

## Goal

Formalize and implement a falsifiable, provenance-preserving, analysis-only StegVerse Business Opportunity Engine pilot that surveys one frozen market, estimates defensible addressable gross-revenue-leakage ranges, deterministically ranks candidates, and generates review-only draft proposals without contacting any business.

No outreach, call, email, publication, provider execution, survey contact, or business contact is authorized by this Goal Task.

## Authority boundary

Canonical task registration is coordination only. It does not mint execution authority. WorkerCoordinator remains claim/fence authority, Interlock/InTr remains governed transition authority, TV/TVC remains provider credential authority, and Master Records remains observed-reality/reconstruction authority. GitHub source and CI prove source/validation state only.

The pilot terminates at `PILOT_REVIEW_READY`. There is intentionally no `OUTREACH_SENT` transition in this Goal Task.

## Execution-substrate registration repair

This task carries `runtime_requirements`, therefore the canonical registration validator requires `execution_substrate_resolution` using `stegverse.execution-substrate-resolution/v1`.

The canonical review order is preserved exactly:

1. `STEG-BROWSER-RETAINED-RESIDENT-NODE`
2. `STEGOS-CURRENT-DEVICE-NODE`
3. `STEG-BROWSER-EPHEMERAL-LEASE`
4. `SAME-DEVICE-SITE-SAFARI-SERVICE-WORKER`
5. `ADMITTED-EPHEMERAL-STEGOS-NODE`
6. `REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT`

Registration does not select a runtime. `selected_substrate_id` remains `null`, `external_device_required=false`, `second_user_operated_device_allowed=false`, and `authority_effect=NONE`.

The retained resident node is `PENDING_EVIDENCE / EVIDENCE_REACHABILITY`; current-device, browser-ephemeral, same-device service-worker, and admitted-ephemeral StegOS paths are reviewable/suitable but not selected; the remote/external-device lane is `NOT_APPLICABLE` for this registration. A later authentic execution request must still resolve the exact substrate under the ordinary WorkerCoordinator and Interlock/InTr path.

## Pilot boundary

The first pilot is an analysis-only market survey. It may collect admissible public business evidence, derive transparent economic ranges, rank candidates, and generate draft proposals. It must not send them.

The geographic boundary is data, not code. A frozen manifest must record `market.center`, `market.radius_miles`, `market.jurisdictions`, `market.business_classes`, `market.observed_at`, and `market.source_policy` before evidence collection begins.

## Public evidence contract

Every observation is separate from inference and carries at minimum:

- `evidence_id`
- `business_id`
- `source_class`
- `source_uri_or_public_locator`
- `observed_at`
- `retrieved_at`
- `field`
- `raw_or_normalized_value`
- `unit` when relevant
- `freshness_days`
- `source_reliability_weight`
- `direct_observation`
- `derivation_parent_refs`
- `license_or_use_constraint` when known
- `provenance_hash`
- `admissibility_disposition`

Admissible initial source classes include official business surfaces, public directories/listings, published hours/services/prices, reproducible booking/contact friction, public aggregate review signals, public maps/business-density observations, public government demographic/economic datasets, public staffing indicators, and public competitor observations.

The pilot excludes private personal information, purchased consumer dossiers, protected/sensitive-trait targeting or inference, covert/deceptive contact, inaccessible private analytics, and unverifiable revenue assertions treated as facts.

## Leakage model

The engine estimates addressable gross-revenue leakage, not lost profit and not guaranteed recoverable revenue.

For leakage channel `k`:

`LEAK_k = OPPORTUNITY_VOLUME_k × CONVERSION_PROBABILITY_k × EXPECTED_GROSS_VALUE_k × ADDRESSABLE_SHARE_k`

Business-level outputs are ranges:

`LEAK_total_low = Σ LEAK_k_low`

`LEAK_total_mid = Σ LEAK_k_mid`

`LEAK_total_high = Σ LEAK_k_high`

Permitted initial channels include after-hours inbound demand, unanswered/abandoned inbound contact, booking friction, delayed follow-up, discoverability/contact-path friction, independently observable capacity mismatch, and service accessibility friction where the proposed intervention directly addresses it without targeting protected persons.

Every factor must be directly observed, externally benchmarked with provenance, or an explicit assumption. Unsupported factors remain unknown. Proposal language must characterize output as an `estimated addressable gross-revenue leakage under stated assumptions`, never as audited or known historical lost revenue.

## Confidence and sensitivity

For each channel:

`CONF_k = geometric_mean(C_e, C_s, C_m, C_a)`

where evidence coverage, source reliability, model sensitivity/stability, and assumption burden are normalized to `[0,1]`. Business confidence is value-weighted across material channels and capped by the weakest material channel contributing at least 20% of midpoint leakage.

Every uncertain material input is varied across its declared low/high interval. Resulting ranking movement is recorded. Candidates whose top-50 membership is unstable under reasonable assumptions receive a ranking-stability penalty.

## Deterministic ranking

Ranking occurs only after the market boundary and model version are frozen.

`S_b = N(log1p(LEAK_mid)) × CONF × ADDRESSABILITY × EVIDENCE_COMPLETENESS × RANK_STABILITY × (1 - COMPLIANCE_RISK)`

Tie-break order is:

1. higher confidence
2. higher evidence completeness
3. narrower relative leakage interval
4. higher addressability
5. stable deterministic business ID

Top 50 is an analysis output limit, never permission to contact 50 businesses.

## Draft-only proposal contract

A proposal must be reproducible from one business evidence packet plus the frozen model version and must contain business/public context, analysis date, strongest observed opportunity channels, low/mid/high leakage range, confidence and uncertainty drivers, evidence references, exact assumptions, intervention class, cost range only when supported, measurement plan, and a clear analytical-not-audited disclaimer.

A proposal may not contain a claim not traceable to evidence or explicit assumptions. Fabricated testimonials, urgency, exclusivity, or guaranteed-return language are rejected.

The generator output state is `DRAFT_ONLY`. No adapter or function in the pilot may send, publish, call, message, schedule outreach, resolve provider credentials, or transition a generated draft into an outbound event.

## Outreach hard-disable

Pilot gate state is `OUTREACH_DISABLED`.

Any later outbound work requires a separate canonical Goal Task and contemporaneous governed authorization, including sender identity/disclosure rules, opt-out/suppression enforcement, jurisdiction/channel classification, applicable commercial-message/call review, rate/repetition limits, evidence freshness, exact Interlock/InTr admission, TV/TVC credential authority, and execution/outcome receipts.

No artifact in this task grants that future transition.

## Outcome schema

The pilot may define later-observable outcome fields without producing any outreach event: delivery state, lawful view/open state, reply, evidence request, meeting, objection class, qualified opportunity, conversion, intervention deployment, baseline/post-intervention metrics, attributable recovered-gross-revenue range, forecast error, and calibration update.

The preferred success criterion is whether later authentic business data supports or falsifies the original estimate, not raw response rate.

## RTG / GTG / InTr path

The intended governed path is:

`human goal -> canonical Goal Task/COSV -> manifest -> RTG candidate transition graph -> GTG governed transition graph -> WorkerCoordinator claim/fence when execution is requested -> Interlock -> InTr -> bounded analysis execution -> evidence/ranking/draft artifacts -> Master Records reconstruction`

Allowed pilot phases are:

1. `PILOT_DEFINED -> SURVEY_ADMITTED`
2. `SURVEY_ADMITTED -> EVIDENCE_COLLECTED`
3. `EVIDENCE_COLLECTED -> MODEL_EVALUATED`
4. `MODEL_EVALUATED -> TOP50_FROZEN`
5. `TOP50_FROZEN -> PROPOSALS_GENERATED`
6. `PROPOSALS_GENERATED -> PILOT_REVIEW_READY`

There is no outreach transition in this Goal Task.

## Falsification gates

A candidate fails or is downgraded when provenance cannot be reconstructed, unsupported assumptions dominate the estimate, sensitivity materially destabilizes ranking, a defensible range cannot be produced, the proposed intervention cannot address the observed channel, proposal claims exceed evidence, or compliance classification remains unresolved for any hypothetical future outreach route.

## Implementation-owner collision check

After canonical registration is merged and verified on `main`, `StegVerse-Labs/StegBusiness-Ops` is the proposed implementation owner. Before mutation, inspect its canonical mirror handoff, task-state/registry surfaces, open PRs/branches, and adjacent active tasks for semantic overlap.

Proceed only on an evidence-backed `CONTINUE` or a resolved convergence disposition. Do not create duplicate schemas/model lanes or redefine canonical business identity owned by `StegVerse-Labs/StegBusiness`.

## Completion predicates

Source/design completion requires:

- canonical task registration merged and visible on `main`
- this handoff merged and reconciled
- implementation-owner collision disposition recorded
- evidence/range/confidence/ranking/proposal/outcome schemas materialized
- deterministic validators cover provenance, range math, ranking determinism, unsupported-claim rejection, and outreach hard-disable
- implementation README and canonical handoff updated
- exact-head validation green before merge
- merged-main revalidation green
- no outreach has occurred under this pilot

Authentic market survey execution, real top-50 production, real business proposal generation, provider execution, and economic validation are separate evidence predicates and are not claimed by source materialization alone.

## Current truth

- Goal Task: `ACTIVE / UNCLAIMED`.
- COSV: `10100000110000`.
- PR #1928: registration repair branch; merge is prohibited until required exact-head checks are green.
- Missing-substrate-registration defect: repaired in source by adding non-authorizing `execution_substrate_resolution`.
- Selected execution substrate: NONE.
- External/second user-operated device required: NO.
- StegBusiness-Ops implementation: NOT STARTED under this Goal Task until canonical registration merges and collision check returns CONTINUE or resolved convergence.
- Survey execution: NOT STARTED.
- Top 50: NOT PRODUCED.
- Real proposals: NOT GENERATED.
- Outreach: HARD-DISABLED / NONE SENT.
- Runtime execution: NOT CLAIMED.

## Next admissible work

Obtain preserved green exact-head validation for PR #1928, merge only with expected-head protection, verify the canonical record/handoff on `main`, then run the StegBusiness-Ops collision check. On `CONTINUE`, implement the deterministic analysis-only package with outreach structurally disabled and reconcile exact implementation/validation evidence back into this handoff.
