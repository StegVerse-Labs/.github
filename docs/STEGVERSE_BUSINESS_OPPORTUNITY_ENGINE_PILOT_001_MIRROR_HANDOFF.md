# StegVerse Business Opportunity Engine Pilot Mirror Handoff

Updated: 2026-09-15
Repository: `StegVerse-Labs/.github`
Goal Task ID: `STEGVERSE-BUSINESS-OPPORTUNITY-ENGINE-PILOT-001`
COSV profile: `task.v1`
COSV vector: `10100000110000`
Status: `ACTIVE / UNCLAIMED / DESIGN CONTRACT MATERIALIZED`

## Goal

Formalize a falsifiable, provenance-preserving StegVerse Business Opportunity Engine pilot that surveys one bounded geographic market, ranks businesses by defensible gross-revenue-leakage opportunity, prepares the top 50 business-specific proposals, and stops before any outbound contact.

No outreach, call, email, publication, provider execution, or business contact is authorized by this task.

## Pilot boundary

The first pilot is an analysis-only market survey. It may collect admissible public business evidence, derive transparent economic ranges, rank candidates, and generate draft proposals. It must not send them.

The geographic boundary is expressed as a manifest field rather than hard-coded geography:

- `market.center`: named locality or coordinate reference;
- `market.radius_miles`: explicit bounded radius;
- `market.jurisdictions`: city/county/state identifiers where applicable;
- `market.business_classes`: allowed NAICS/SIC/local category classes;
- `market.observed_at`: survey time;
- `market.source_policy`: admissible source classes.

The initial execution should use one contiguous local market and freeze the boundary before evidence collection so rankings cannot be improved by changing the denominator after results are seen.

## Admissible public evidence schema

Every observation must be represented independently from inference and carry:

- `evidence_id`;
- `business_id`;
- `source_class`;
- `source_uri_or_public_locator`;
- `observed_at`;
- `retrieved_at`;
- `field`;
- `raw_or_normalized_value`;
- `unit` where relevant;
- `freshness_days`;
- `source_reliability_weight`;
- `direct_observation` boolean;
- `derivation_parent_refs` when derived;
- `license_or_use_constraint` when known;
- `provenance_hash`;
- `admissibility_disposition`.

Initial admissible source classes:

1. official business website and published booking/contact surfaces;
2. public business-directory/listing information;
3. public operating hours and service menus;
4. public review counts/ratings and review text limited to defensible aggregate or directly cited operational observations;
5. public maps/business-density observations;
6. public government demographic/economic datasets where license and geographic granularity permit;
7. public pricing/service-price observations;
8. public job postings or staffing indicators where relevant and not used to infer protected personal characteristics;
9. public competitor count/category/distance observations;
10. directly observed online booking friction, unanswered-contact indicators, or after-hours availability gaps that can be reproduced without deception.

Excluded from the pilot:

- private personal information;
- purchased consumer dossiers;
- sensitive/protected-trait targeting;
- inferred health, race, religion, political affiliation, or other protected/sensitive individual characteristics;
- covert calling or pretending to be a customer merely to manufacture missed-call evidence;
- inaccessible/private analytics;
- unverifiable revenue assertions treated as facts.

## Leakage model

The engine estimates *addressable gross-revenue leakage*, not lost profit and not guaranteed recoverable revenue.

For each leakage channel `k`:

`LEAK_k = OPPORTUNITY_VOLUME_k × CONVERSION_PROBABILITY_k × EXPECTED_GROSS_VALUE_k × ADDRESSABLE_SHARE_k`

The business estimate is a range, not a point claim:

`LEAK_total_low = Σ LEAK_k_low`

`LEAK_total_mid = Σ LEAK_k_mid`

`LEAK_total_high = Σ LEAK_k_high`

Permitted initial channels include:

- after-hours inbound demand;
- unanswered or abandoned inbound contact;
- booking friction;
- delayed follow-up;
- discoverability/contact-path friction;
- capacity mismatch where independently observable;
- language/accessibility friction where the service capability directly addresses it and no protected-person targeting is performed.

Every factor must be one of: directly observed, externally benchmarked with provenance, or explicit assumption. Unsupported factors default to unknown and may not be silently replaced by optimistic values.

No proposal may state the range as actual historical lost revenue. Required language is equivalent to `estimated addressable gross-revenue leakage under stated assumptions`.

## Confidence method

Channel confidence is computed from four independently recorded dimensions:

- evidence coverage `C_e`;
- source reliability `C_s`;
- model sensitivity/stability `C_m`;
- assumption burden `C_a` where higher means fewer unsupported assumptions.

Pilot confidence:

`CONF_k = geometric_mean(C_e, C_s, C_m, C_a)`

Each factor is normalized to `[0,1]`. Geometric mean is used so one weak dimension cannot be hidden by averaging several strong dimensions.

Business confidence is value-weighted across leakage channels and capped by the weakest material channel contributing at least 20% of the midpoint estimate.

Required sensitivity test: vary each uncertain material input across its declared low/high interval and record the resulting ranking movement. Candidates whose top-50 status is unstable under reasonable assumptions receive a ranking penalty.

## Top-50 ranking

Ranking is performed only after the survey boundary and model version are frozen.

For business `b`:

`S_b = N(log1p(LEAK_mid)) × CONF × ADDRESSABILITY × EVIDENCE_COMPLETENESS × RANK_STABILITY × (1 - COMPLIANCE_RISK)`

Where each non-revenue factor is `[0,1]` and `N()` is normalization within the frozen survey population.

Tie-break order:

1. higher confidence;
2. higher evidence completeness;
3. narrower relative leakage interval;
4. higher addressability;
5. stable deterministic business ID.

Top 50 is a hard pilot output limit, not permission to contact 50 businesses.

## Proposal-generation contract

A generated proposal must be reproducible from one business evidence packet plus the frozen model version. It must contain:

- business name and public business context;
- date of analysis;
- observed opportunity summary;
- maximum three strongest leakage channels;
- low/mid/high addressable gross-revenue leakage range;
- confidence and principal uncertainty drivers;
- evidence citations or public-source references;
- exact assumptions;
- recommended StegVerse-supported intervention class;
- estimated intervention cost range only when supported;
- expected measurement plan;
- disclaimer that the estimate is analytical, not an audited revenue statement;
- no fabricated testimonials, urgency, exclusivity, or guaranteed return claim.

A proposal may not include a claim not traceable to its evidence packet or model assumptions.

## Outreach compliance gate

Pilot gate state is `OUTREACH_DISABLED`.

Before any later send transition, a separate governed authorization must establish at minimum:

- sender legal identity and required postal/contact disclosures;
- truthful sender/header/subject contract;
- commercial-message disclosure as applicable;
- opt-out mechanism and suppression-list enforcement;
- jurisdiction/channel classification;
- B2B/B2C classification where material;
- channel-specific CAN-SPAM/TCPA/TSR/state-law review;
- no automated voice/call route unless independently admitted under the applicable legal/provider rules;
- deterministic do-not-contact/suppression check;
- rate and repetition limits;
- proposal evidence still fresh enough for the claims being made;
- Interlock/InTr transition admission for the exact outreach event;
- TV/TVC credential authority for any provider credentials;
- execution receipt and outcome receipt requirements.

No current task artifact grants this later transition.

## Outcome measurement schema

The pilot creates the schema even though outreach is disabled. Later observed outcomes may include:

- delivery state;
- open/view state when lawfully and reliably observable;
- reply;
- request for evidence;
- meeting;
- objection class;
- qualified opportunity;
- conversion;
- intervention deployed;
- baseline operating metric;
- post-intervention operating metric;
- attributable recovered gross revenue range;
- forecast error against original leakage interval;
- model-calibration update.

The preferred success measure is not merely response rate. It is whether subsequent authentic business data supports or falsifies the original economic estimate.

## RTG / GTG / InTr path

This pilot uses the existing StegVerse authority separation. The intended path is:

`human goal -> canonical Goal Task/COSV -> manifest -> RTG candidate transition graph -> GTG governed transition graph -> WorkerCoordinator claim/fence when execution is requested -> Interlock -> InTr -> bounded analysis execution -> evidence/proposal artifacts -> Master Records reconstruction`

Phase transitions:

1. `PILOT_DEFINED` -> `SURVEY_ADMITTED`;
2. `SURVEY_ADMITTED` -> `EVIDENCE_COLLECTED`;
3. `EVIDENCE_COLLECTED` -> `MODEL_EVALUATED`;
4. `MODEL_EVALUATED` -> `TOP50_FROZEN`;
5. `TOP50_FROZEN` -> `PROPOSALS_GENERATED`;
6. `PROPOSALS_GENERATED` -> `PILOT_REVIEW_READY`.

There is intentionally no `OUTREACH_SENT` transition in this Goal Task.

RTG may describe possible transitions and failure/retry/reconciliation paths. GTG may retain only transitions admitted by governance. Interlock/InTr remains transition authority; WorkerCoordinator remains execution claim/fence authority; TV/TVC remains provider credential authority; Master Records remains observed-reality/reconstruction authority; GitHub source/CI does not prove runtime execution.

## Falsification gates

The pilot is not successful merely because it produces 50 polished proposals. It must fail or downgrade candidates when:

- source provenance cannot be reconstructed;
- leakage estimate is dominated by unsupported assumptions;
- reasonable sensitivity ranges move the candidate materially out of the top 50;
- economic estimate cannot be expressed as a defensible range;
- intervention cannot plausibly address the identified channel;
- proposal claims exceed evidence;
- compliance classification is unresolved for any future outreach route.

## Completion predicates

This task may be considered design-complete only when:

- canonical task registration is merged;
- this handoff is merged;
- schemas/equations/ranking/proposal/compliance/outcome contracts are materialized in the implementation owner repository;
- deterministic validation covers provenance requirements, range math, ranking determinism, unsupported-claim rejection, and `OUTREACH_DISABLED` enforcement;
- README is updated in the implementation owner repository;
- no outreach has occurred under this pilot;
- exact implementation and validation evidence is reconciled back into this handoff.

Authentic survey execution, top-50 production, proposal generation, outreach, and economic validation are separate evidence predicates and are not claimed here.

## Implementation owner recommendation

Use `StegVerse-Labs/StegBusiness-Ops` for the operational pilot package while consuming canonical business/evidence identities from `StegVerse-Labs/StegBusiness`. Do not redefine legal entity identity or business lifecycle authority inside the opportunity engine.

## Current truth

- Concept formalization: COMPLETE in this handoff branch.
- Canonical Task Registry registration: PROPOSED in the same branch, not yet merged.
- Implementation in StegBusiness-Ops: NOT STARTED under this task.
- Survey execution: NOT STARTED.
- Top 50: NOT PRODUCED.
- Proposals: NOT GENERATED.
- Outreach: DISABLED / NONE SENT.
- Runtime execution: NOT CLAIMED.

## Next admissible work

After this registration merges, rerun the canonical collision/check-in for `StegVerse-Labs/StegBusiness-Ops` and implement the analysis-only pilot package there: evidence schema, model/ranking engine, proposal generator, validators, README/handoff update, and test fixtures. Keep outbound adapters absent or hard-disabled.