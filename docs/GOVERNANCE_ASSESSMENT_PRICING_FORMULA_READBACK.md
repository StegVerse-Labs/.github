# Governance Assessment — Canonical Pricing Formula Readback (2026-10-28)

**Evidence class:** SOURCE_READBACK + LOCAL_REPRODUCTION. Coordination/design artifact only.
No price is approved, quoted or invoiced by this document. `authority_effect: NONE`.
Prepared under #3370 owner ruling: "price = exactly the formula established plus acceptable
margin if not already included" and the adaptive-pricing clarification (formula output is a
baseline; governed bands permitted once authentic cost/market evidence exists).

## 1. The established formula (recovered, not invented)

Owner pricing invariant, canonical source
`StegVerse-org/StegVerse-SDK@56b1d0fef35a8b29cb21ebcb4acafb35ebbf05d9:stegverse/cost_registry.py`:

    C_pricing = max(C_estimated, C_authentically_observed)

- UNKNOWN is never zero; one missing operand yields `PROVISIONAL_SCENARIO`, never a final rate.
- Task record `SDK-COST-DERIVED-TIER-PRICING-001` (shard blob `5ad7ec567004ee55fe09b83ab4e88a3e89f962b5`)
  owns this basis; `ORGANIZATION-BATCH-CUSTODY-REPLAY-001` is the sole source of
  `C_authentically_observed`. No observed operand exists today → any number is PROVISIONAL.
- Margin is ALREADY inside the formula machinery as `target_gross_margin` (tier price floor
  `unit_cost / (1 - margin)`; market median above floor wins). Per the owner ruling, no second
  margin may be applied on top — the margin question is the pending owner decision on the
  candidate policy value (0.75), not an add-on.
- Every USD figure requires an https citation and `observed_at`; uncited rates fail closed
  (`UNKNOWN_RATE_NOT_SOURCED`).

## 2. Local reproduction of the committed candidate report

Executed the unmodified pricing engine (`stegverse/tier_pricing.py` + `pricing_basis` from
`stegverse/cost_registry.py`) locally against the real candidate inputs:

- Cost basis: `StegVerse-Labs/.github:cost-basis/worker-runtime/` (5 task classes referenced
  by the candidate policy, blobs read at main `1f72f204`).
- Rate card: `pricing/rate-card.candidate.json` (blob `8e0dbeee`; compute_unit $0.006,
  storage_gb $0.25, both cited 2026-10-14; status CANDIDATE_PENDING_OWNER_DEFINITION).
- Policy: `pricing/policy.candidate.json` (blob `ad44f41e`; margin 0.75,
  CANDIDATE_PENDING_OWNER_DECISION).

Result matches committed `pricing/candidate-report.json` (blob `29648447`):

| Tier | Status | USD/action | USD/period |
|---|---|---|---|
| Team (1,000 actions) | PROVISIONAL_SCENARIO | 0.072262144 | 72.27 |
| Organization (10,000 actions) | UNKNOWN_RATE_NOT_SOURCED | — | — |

Overall `INCOMPLETE`: `steggate_stable_rendezvous` declares `network_bytes: 1048576` but the
candidate rate card has no cited `network_gb` rate. Reproduction is conversation-local; the
committed report remains the canonical artifact.

## 3. Exact missing inputs before ANY numeric assessment quote

1. **Assessment cost-basis record.** None of the 62 records in `cost-basis/worker-runtime/`
   prices an assessment engagement; all are machine task classes. The assessment deliverable
   (one workflow map, authority/evidence inventory, risk matrix, 30-day plan, review meeting)
   needs its own `stegverse.worker-runtime-cost-basis/v0.1` record with estimator-declared
   quantities (compute units for LLM-assisted analysis, external provider token cost if any,
   storage). Quantities must come from the assessment owner — they are not derivable here.
2. **Owner decisions pending on candidates:** compute-unit definition (SDK#484), margin 0.75,
   plan composition — all flagged CANDIDATE_PENDING_OWNER_*.
3. **Cited `network_gb` rate** if the assessment task class consumes network bytes.
4. **Observed operand:** a receipt-backed observed cost from
   `ORGANIZATION-BATCH-CUSTODY-REPLAY-001` in the same `cost_basis_version`; absent it, the
   quote stays PROVISIONAL_SCENARIO (permitted as baseline under the adaptive-pricing
   clarification, with documented provisional status).
5. **Engagement↔action mapping:** the engine prices per action; the assessment is a fixed-fee
   engagement. The owner must declare the mapping (e.g., one engagement = N priced actions of
   the assessment task class) before `usd_per_period` is meaningful for the offer.

## 4. Boundaries

- No numeric price, discount, margin percentage, market benchmark or customer quote is
  asserted here. Stripe account "StegVerse.org" (per #3370 comment) is a provider surface,
  not invoice authority; invoice-issuance owner remains unestablished (TVC#558 is read-only).
- Outreach, contract, invoice and settlement remain blocked on commercial-owner rulings
  recorded in #3370.
