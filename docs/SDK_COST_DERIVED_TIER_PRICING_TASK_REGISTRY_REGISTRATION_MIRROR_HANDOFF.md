# SDK Cost-Derived Tier Pricing Task Registry Registration Mirror Handoff

Updated: 2026-10-17
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SDK-COST-DERIVED-TIER-PRICING-001`
Issue: `StegVerse-org/StegVerse-SDK#484`
Allocation request: `control/goal-task-allocation-requests/sdk-484-cost-derived-tier-pricing-2026-10-17.json` (owner directive in SDK#484 comment [6235730818](https://github.com/StegVerse-org/StegVerse-SDK/issues/484#issuecomment-6235730818))
Status: `ACTIVE / UNCLAIMED / REGISTERED`

## Purpose

The owner directed, in SDK#484 comment 6235730818 (2026-10-17, "ChatGPT Coordination — owner pricing-cost directives"): "Distinguish this pricing workstream from structural-validator task ownership; register/reconcile a separate canonical task if required." Registration is required: SDK #527 (`stegverse/tier_pricing.py`) and SDK #538 were carried under `SDK-STRUCTURAL-VALIDATOR-CONSOLIDATION-001`, and no canonical record owned commercial pricing. `ls data/canonical-task-records | grep -iE "PRIC|TIER|COST|COMMERC"` returns only `GP10-COMMERCIAL-RESPONSE-VALIDATION-001` (commercial response validation) and `WORKER-TASK-RESOURCE-COST-LINKAGE-001` (task-native cost linkage, not commercial pricing). Before registration, a collision check-in for this task ID returned `STOP_NOT_REGISTERED / END_OR_REGISTER_BEFORE_MUTATION`.

## Goal

A cost-derived tiered pricing basis for the StegVerse governance product:

- a versioned, extensible cost-component registry;
- the owner pricing invariant `C_pricing = max(C_estimated, C_authentically_observed)`; UNKNOWN is never zero, and an incomplete evidence set yields only a provisional scenario;
- the five-lane cost analysis (`SV-COST-FIVE-LANE-RESULTS-001`) as foundation and the eleven-lane analysis (`SV-COST-ELEVEN-LANE-RESULTS-001`, GCAT-BCAT-Engine/workflows) as expansion;
- internal-first execution preference.

Pricing issues no TV/TVC entitlement and no InTr ALLOW.

## Registration contract

- `data/canonical-task-records/SDK-COST-DERIVED-TIER-PRICING-001.json`: canonical shard; root goal (no parent); `coordination_state=ACTIVE`; `checkout_state=UNCLAIMED` because no WorkerCoordinator claim exists.
- `data/canonical-task-registry.json`: aggregate row for the same record; generation 317 -> 318.
- `control/task-vectors/SDK-COST-DERIVED-TIER-PRICING-001.json`: task.v1 COSV `10300000011002`, computed by `scripts/cosv.py encode_task` from evidence-bound exact metrics (lifecycle UNCLAIMED, 3 unassigned work items, 0 chat-owned work, owner not installed, thread required, 1 blocker, evidence incomplete, not activated, propagation unknown).
- `control/task-vector-index.json`: EMITTED index entry; coverage 127 -> 128.
- Allocation request: `state=REGISTERED`, vector bound, `owner_authorization.authority_limit=OWNER_INTENT_ONLY`, `registration` block with `authority_effect=NONE_REGISTRATION_ONLY`.
- `worker_claim` follows `TASK_REGISTRY_CANONICAL_INVARIANTS.md`: `authority=WORKERCOORDINATOR`, `claim_ref=null`, `fence_ref=null`, `projection_only=true`.

COSV inputs: the 3 unassigned work items are the cost-component registry module, enforcement of the max/UNKNOWN invariant in `tier_pricing.py`, and binding the five- and eleven-lane evidence by reference. The 1 blocker is the absence of authentically observed receipt cost, which only `ORGANIZATION-BATCH-CUSTODY-REPLAY-001` can supply; until then every price is a provisional scenario.

## Source state

SDK main `ba5bbf42eabec6a6ae3b0efdff7c683967a79083`: `stegverse/tier_pricing.py` present (merged via #527). There is no cost-component registry module on SDK main.

2026-10-17, `REPORTED_BY_SDK_LANE` (reported by the SDK#484 parent session; this registration did not read the SDK repository): StegVerse-org/StegVerse-SDK PR #538 is open at head `00fc13aa2524051292616fe3432c0c9ce05a1765`, with 21 checks success and `deploy` and `live` skipped. It adds `stegverse/cost_registry.py` and the `C_pricing = max(C_estimated, C_authentically_observed)` rule in `stegverse/tier_pricing.py`.

Predicate status:

- Predicates 1–3 are source-implemented on that PR head. They are not merged and not satisfied.
- Predicate 4 remains open.

Source merge does not prove runtime.

## Adjacent tasks

- `SDK-STRUCTURAL-VALIDATOR-CONSOLIDATION-001`: parent lane this workstream is split from. Its structural-validator scope and ownership are unchanged; pricing ownership moves here.
- `WORKER-TASK-RESOURCE-COST-LINKAGE-001`: task-native cost linkage; consumed as cost-basis input, not owned here.
- `ORGANIZATION-BATCH-CUSTODY-REPLAY-001`: owns actual receipt-cost measurement and is the only source of `C_authentically_observed`.

## Collision check-in

`scripts/evaluate_task_registry_collision_checkin.py` (caller surface `AI_SESSION_GATE`, observed generation 318) returns `COORDINATE_CONVERGENCE / COORDINATE_BEFORE_MUTATION` with no hard collision and `reconciliation_required_before_mutation=false`. The only candidates are the three declared adjacent tasks (no shared components, no lineage; only `SDK-STRUCTURAL-VALIDATOR-CONSOLIDATION-001` shares the SDK repository). Other SDK tasks appear only as non-blocking `DISTINGUISHED_COMPONENT_SCOPE` repository overlaps. SDK pricing source mutation must first converge with the structural-validator lane on `stegverse/tier_pricing.py`.

## Remaining predicates

1. `VERSIONED_COST_COMPONENT_REGISTRY_SOURCE_MERGED`
2. `TIER_PRICING_ENFORCES_MAX_ESTIMATED_OBSERVED_UNKNOWN_NOT_ZERO`
3. `FIVE_AND_ELEVEN_LANE_COST_EVIDENCE_BOUND_BY_REF`
4. `AUTHENTICALLY_OBSERVED_RECEIPT_COST_FROM_ORGANIZATION_BATCH_CUSTODY_REPLAY`

This registration does not invent a WorkerCoordinator claim, a TV/TVC credential or entitlement, an InTr admission, or a runtime ALLOW.

## Authority separation

The Task Registry mints no execution authority. Worker claims belong to WorkerCoordinator, credentials and entitlements to TV/TVC, governed ingress and egress to Interlock/InTr. GitHub runtime authority is NONE; there is no hosted fallback and no second user-operated device requirement. The record declares no `runtime_requirements`, so no substrate resolution applies.

## Validation

`tests/test_sdk_cost_derived_tier_pricing_registration.py` checks identity, states, the pricing invariant, the adjacent tasks, that the vector equals `encode_task(exact_metrics)` and agrees across record, registry, vector file, index and allocation request, the canonical `worker_claim` projection, the authority separation, and that no completion is claimed.

## Next sequence

1. owner merges this registration;
2. converge with `SDK-STRUCTURAL-VALIDATOR-CONSOLIDATION-001` on ownership of `stegverse/tier_pricing.py`;
3. run the collision check-in for the intended SDK mutation context against the current registry generation and obey its disposition;
4. obtain a WorkerCoordinator claim before claiming the task;
5. satisfy the predicates; observed cost only from `ORGANIZATION-BATCH-CUSTODY-REPLAY-001` receipts, never from source or CI.

## Human action

Owner merge approval only.

## Authenticated post-merge source reconciliation — 2026-10-17

This section supersedes the earlier historical source-state snapshot; that snapshot is retained above as dated evidence, not current authority.

- Registry registration #3214 merged at `60d90c48209fb250c12839bb29dfcd7e6d21aaad`; generation correction #3219 merged at `5a354844b7266dd9db09852b893c30bc4ca02ca3` (generation 319); generation-fence #3220 merged at `f16b9153b4d33630a0542f69d0ba8e8af9da40ae`.
- SDK #538 merged at `07a6a90ad39c739f7b8a6d426f334a6b9649c09d`, with actual module `stegverse/cost_registry.py`; SDK #540 merged at `ae4a2a12fb3261e5d9fbee1dae1b4195bcf69fc9`, correcting `owning_existing_goal` in `stegverse/tier_pricing.py` to `SDK-COST-DERIVED-TIER-PRICING-001`. Both SDK files independently read on main.
- This branch corrects the pricing canonical shard's source metadata and module path; it does not change task identity, COSV `10300000011002`, coordination state `ACTIVE / UNCLAIMED`, worker claim, or runtime authority.
- Aggregate registry readback remains unverified: the GitHub connector returned a blob SHA but empty content. Any required aggregate regeneration must occur through the canonical authorized Registry mechanism and be validated against main before merge. Do not claim full aggregate/shard convergence from this branch alone.
- KV INDEX reconciliation is pending authenticated KV read/write and deduplicated readback; no KV update is asserted here.
- Authentic receipt-backed `C_authentically_observed` is still UNKNOWN pending `ORGANIZATION-BATCH-CUSTODY-REPLAY-001` sovereign Organization ledger evidence. `UNKNOWN != 0`; pricing is `PROVISIONAL_SCENARIO_ONLY`. Source merge and CI do not mint runtime ALLOW, entitlement, or final pricing authorization.

**Disposition:** `FAIL_CLOSED / AGGREGATE_AND_KV_READBACK_UNVERIFIED_AND_AUTHENTIC_COST_UNOBSERVED`.
