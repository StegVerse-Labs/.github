# ERL AI Economic Transparency Standard v1

## Purpose

Define a reproducible method for evaluating literal inference-cost transparency and the economic importance of cost uncertainty under elevated usage.

## Axis A — ACTUAL_COST_DISCLOSURE_BURDEN

Lower is more transparent.

| Score | State | Required evidence |
|---:|---|---|
| 0 | DIRECT | Literal request-attributable cost exposed at the request/receipt surface. |
| 1 | ONE_STEP_DERIVABLE | Exact request usage plus one public version-bound pricing artifact reconstructs cost. |
| 2 | MULTI_SOURCE_DERIVABLE | Exact cost is reconstructable only by combining multiple provider-controlled surfaces/rules. |
| 3 | ACCOUNT_GATED | Reconstruction requires authenticated billing/admin/account surfaces beyond the ordinary request surface. |
| 4 | SUPPORT_OR_EXTERNAL_RESEARCH_REQUIRED | Reconstruction requires support or substantial research beyond ordinary provider self-service surfaces. |
| 5 | NON_RECONSTRUCTABLE | Governed discovery protocol completed and literal request-attributable cost remains non-reconstructable. |

A score of 5 requires protocol completion. Initial opacity alone is not sufficient.

## Axis B — COST_SCALE_SENSITIVITY

This axis records how known or unresolved cost components behave across elevated usage.

Required scenarios, where the workload definition supports them:
- 1,000 equivalent requests;
- 100,000 equivalent requests;
- 1,000,000 equivalent requests.

If request shape varies, use a documented normalized workload basis such as input/output tokens, compute seconds, or another reproducible denominator.

For exact per-request cost `c` and workload count `n`:

`known_total_cost = c * n`

For bounded unresolved per-request exposure `[l,u]`:

`scale_exposure = [l*n, u*n]`

If no defensible bound exists, preserve `UNBOUNDED_UNKNOWN`; do not invent one.

## Discovery protocol

1. Capture immediate request/result cost and usage surfaces.
2. Capture provider-controlled pricing documentation.
3. Capture provider-controlled usage/billing/account surfaces available to evaluator.
4. Record every material pricing rule affecting literal cost.
5. Record navigation/research steps and elapsed minutes.
6. Record access barriers.
7. Attempt exact reconstruction.
8. Record unresolved components.
9. Assign disclosure burden only after protocol completion.
10. Calculate elevated-usage consequences only from exact or bounded evidence.

## Material cost components

Examples include input/output token rates, cache rates, reasoning-token treatment, batch discounts, peak/off-peak rules, model routing, minimum charges, subscription quota allocation, tool/search charges, storage/network charges, and other provider-documented components that affect the literal economic consequence.

This list is non-exclusive. Evidence determines applicability.

## Independence rule

SV-COST artifacts may be cited as source observations. ERL must separately validate the evidence path and compute its own ratings.

## Findings discipline

- `rate_card_present` does not equal `actual_cost_reconstructable`.
- `cost_unknown` does not equal `cost_high`.
- `cost_unknown` does not equal `cost_zero`.
- `opaque_surface` does not prove intent.
- a misleading/deceptive-effect finding requires evidence of a materially inaccurate pricing impression, not merely missing metadata.
- intent-based findings require separate direct or reconstructable evidence.

## Release gate

Provider rankings and paper conclusions require:
- validator-clean observations;
- completed protocols for compared providers;
- reproducible scale calculations;
- contradiction review;
- independent review.
