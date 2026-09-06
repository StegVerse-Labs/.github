# Canonical Runtime Profile Map Mirror Handoff

Updated: 2026-09-05
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`
Status: `SOURCE_IMPLEMENTED_CANONICAL_TASK_INGRESS_REGISTRY_PRESERVATION_AND_RUNTIME_CHAIN_PREFLIGHT_BOUND_AUTHENTIC_RESIDENT_EVIDENCE_PENDING`

## Authority boundary

This workstream is subordinate to `control/canonical-resident-carrier-contract.json`, Canonical Work Coordination, WorkerCoordinator, Universal InTr, runtime observability, and Master Records.

It MUST NOT create a second heartbeat, oscillator, scheduler, WorkerCoordinator, ingress server, credential authority, task registry, or runtime authority. HB32 + the independent 100 Hz / 10 ms oscillator remains reference/carrier substrate only and grants no admission, execution, routing, receiving, claim/fence, credential, or transition authority.

## Purpose

Provide one canonical machine-readable discovery/reconciliation projection answering which runtime substrates exist, what declared capabilities and transition surfaces they expose, what explicit observations/freshness exist, which canonical tasks can consider them compatible candidates, what routing and transition-readiness state exists, and which current authority class must review the next transition.

No task request, map/profile/observation/match/readiness/custody/reconciliation/review/routing/source-validation artifact grants authority.

## Canonical invariants

1. Declared capability and observed runtime state remain separate.
2. `CURRENT`, `STALE`, `UNKNOWN`, and `CONFLICT` remain distinct observation states.
3. Source/merge/CI/deployment/HB progression never becomes inferred runtime completion.
4. Runtime matching is deterministic from explicit task requirements.
5. Generic `runtime missing` is inadmissible until current-map resolution identifies the failed predicate.
6. Candidate selection, routing readiness, reconciliation, transition readiness, governance-review packaging, authority-review routing, and chain validation are non-authorizing projections.
7. WorkerCoordinator remains claim/fence authority; Interlock/InTr remains transition authority; TV/TVC remains credential authority; Master Records remains observed-reality/custody authority.
8. Existing WorkerCoordinator ownership must be reused/waited/transferred rather than duplicated.
9. Every transition requires current governance; prior receipts do not authorize later transitions.
10. Exact SHA-256 evidence bindings are preserved across custody, review, and routing.
11. Routing to an authority inbox does not invoke that authority.
12. Every staged resident request must have the exact request/consumer/dispatcher-selector binding before the build may proceed.
13. The exact chain validation must run against the **materialized resident runtime**, not only the canonical source checkout, before runtime-profile-map generation proceeds.
14. The Runtime Profile Map task lifecycle itself must enter through the reusable Canonical Work registered-task ingress before any governed task-state promotion; the map-build resident lane is not a substitute for task ingress.
15. An existing resident `data/canonical-task-registry.json` is mutable coordination state and MUST NOT be replaced by static source materialization; source may seed it only when absent.

## Canonical source surfaces

- `schemas/runtime-profile-map.schema.json`
- `schemas/runtime-profile-map-custody-package.schema.json`
- `schemas/canonical-task-record.schema.json`
- `schemas/task-master-records-reconciliation.schema.json`
- `control/runtime-profile-sources.json`
- `control/runtime-profile-map.json`
- `scripts/build_runtime_profile_map.py`
- `scripts/validate_runtime_profile_map.py`
- `scripts/validate_runtime_profile_map_resident_chain.py`
- `scripts/query_runtime_profile_map.py`
- `scripts/match_runtime_profile.py`
- `scripts/resolve_task_runtime_candidates.py`
- `scripts/apply_task_runtime_resolution_projection.py`
- `scripts/apply_all_task_runtime_resolutions.py`
- `scripts/evaluate_task_runtime_routing_readiness.py`
- `scripts/reconcile_task_registry_master_records.py`
- `scripts/evaluate_runtime_profile_map_transition_readiness.py`
- `scripts/build_runtime_profile_map_governance_review.py`
- `scripts/route_runtime_profile_map_governance_review.py`
- `scripts/build_runtime_profile_map_custody_package.py`
- `scripts/finalize_runtime_profile_map_cycle.py`
- `scripts/emit_runtime_profile_map_receipt.py`
- `control/resident-execution-request.d/canonical-work-runtime-profile-map-001.json`
- `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py`
- `tests/test_runtime_profile_map_canonical_work_resident_request.py`
- `tests/test_canonical_work_resident_registry_preservation.py`
- `tests/test_runtime_profile_map_authority_routing.py`
- `tests/test_runtime_profile_map_resident_chain.py`

## Governed task ingress staging

`STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001` already exists exactly once in the canonical Task Registry, remains `PROPOSED`, allows `INGRESS_ADMITTED`, and has no projected WorkerCoordinator claim/fence in checked-in state. Its non-authorizing Canonical Work resident request is staged at `control/resident-execution-request.d/canonical-work-runtime-profile-map-001.json`.

It reuses the generalized Canonical Work ingress consumer and the single existing dispatcher selector `canonical_work_coordination`. The consumer carries `RUNTIME_PROFILE_MAP_SPEC` alongside the coordination, quantum-resilience, and object-provenance request specs. No new dispatcher selector, listener, scheduler, WorkerCoordinator, task identity, or authority path is introduced.

Expected authentic request-consumption evidence is `receipts/sovereign-host/canonical-work-runtime-profile-map-request-consumption.latest.json`. That receipt plus nested Canonical Work ingress/consumption/bootstrap evidence is required before any claim that the task reached authentic `INGRESS_ADMITTED` state.

## Canonical registry preservation

The Canonical Work ingress consumer previously treated `data/canonical-task-registry.json` like an immutable source artifact and could exact-copy the checked-in registry over an existing resident copy. That was unsafe for this workstream because Runtime Profile Map and other governed flows may have already projected newer authentic ingress/runtime-resolution/task state into the resident registry.

The consumer now uses `PRESERVE_IF_PRESENT` semantics for the canonical registry. When a resident registry exists, it is preserved byte-for-byte and both its resident SHA-256 and the canonical source SHA-256 are recorded in materialization evidence. When absent, it is seeded from canonical source. The request-consumption receipt reports whether an existing resident registry was preserved.

This is preservation only. It does not validate the resident registry or make it authoritative beyond its existing Task Registry role; all registered-task identity/state checks, current Interlock/InTr admission, WorkerCoordinator claim/fence rules, and Master Records reconciliation remain mandatory.

`tests/test_canonical_work_resident_registry_preservation.py` verifies both preservation of existing state and source seeding when absent.

README impact for this preservation change is `material_function_change=true` because resident runtime/failure semantics changed. `README.md` was updated in the same logical change set under **Canonical Work task ingress** to document preserve-if-present behavior. The earlier addition of the Runtime Profile Map request itself remained a configuration-only non-material addition already covered by the generic README semantics.

## Resident Runtime Profile Map stages

- `runtime_profile_map` -> `control/resident-execution-request.d/consume-runtime-profile-map-build.py`
- `runtime_profile_map_custody` -> `control/resident-execution-request.d/consume-runtime-profile-map-custody.py`
- `runtime_profile_map_reconciliation` -> `control/resident-execution-request.d/consume-runtime-profile-map-reconciliation.py`
- `runtime_profile_map_transition_readiness` -> `control/resident-execution-request.d/consume-runtime-profile-map-transition-readiness.py`
- `runtime_profile_map_governance_review` -> `control/resident-execution-request.d/consume-runtime-profile-map-governance-review.py`

All five selectors are registered in the existing `scripts/dispatch_resident_execution_requests.py`. No second dispatcher/scheduler/runtime is introduced.

## Current resident sequence

```text
canonical_work_coordination visits Runtime Profile Map registered-task request
-> preserve existing resident canonical task registry (seed only if absent)
-> exact task identity/state/authority checks
-> existing shared Universal Interlock/InTr task ingress
-> authentic task-specific INGRESS_ADMITTED evidence
-> governed canonical task-state projection
-> materialize current canonical Runtime Profile Map source into existing resident runtime
-> preserve resident WorkerCoordinator registry/shared InTr router/current task registry/current dispatcher
-> run exact request/consumer/selector chain preflight against materialized resident runtime
-> require SOURCE_CHAIN_VALID
-> build current runtime-profile map
-> validate + exact-byte map receipt
-> resolve all canonical tasks carrying runtime_requirements
-> atomically persist runtime_resolution projections
-> emit routing-readiness receipts
-> build exact-hash custody package
-> Master Records exact-hash custody
-> project retained Master Records work events
-> reconcile every runtime-bound canonical task
-> emit transition-readiness receipts
-> build exact-evidence governance-review packages
-> route each package to the matching local authority-review inbox
-> current named authority independently accepts/rejects/performs the next governed transition
```

Task ingress and Runtime Profile Map build may occur during adjacent resident dispatch activity, but neither is allowed to infer the other's authority or evidence. Exact receipts govern ordering/promotion.

## Resident materialization preflight

`control/resident-execution-request.d/consume-runtime-profile-map-build.py` materializes `scripts/validate_runtime_profile_map_resident_chain.py` into the already-existing resident runtime and preserves the existing resident dispatcher as required runtime state.

Before map generation, the consumer executes the chain validator against the **runtime root**, writing `receipts/runtime-profile-map/source-chain-validation.latest.json`.

The build proceeds only when the validator returns `SOURCE_CHAIN_VALID` with a retained SHA-256. If the resident runtime is missing any staged request, consumer, dispatcher selector, or non-authorizing request invariant, map generation is not attempted. The preflight still records `runtime_execution_observed=false`; validating resident materialization integrity is not evidence that the map lifecycle completed.

## Authority-review routing

`scripts/build_runtime_profile_map_governance_review.py` binds current task state, WorkerCoordinator projection, routing-readiness, Master Records reconciliation, and transition-readiness evidence by SHA-256.

`scripts/route_runtime_profile_map_governance_review.py` accepts only `WORKERCOORDINATOR`, `INTERLOCK_INTR`, `MASTER_RECORDS_RECONCILIATION`, or `CANONICAL_COORDINATION`, and emits an exact review envelope under the matching local authority inbox. Every envelope records `authority_invoked=false` and grants no task transition, claim/fence, execution, InTr admission, HB/oscillator progression, or credential authority.

## Master Records boundary

The corresponding Master Records handoff is `master-records/orchestration/RUNTIME_PROFILE_MAP_CUSTODY_MIRROR_HANDOFF.md`. Master Records validates exact-hash custody input and remains reality/custody authority only. Custody acceptance or reconstruction does not grant runtime selection, WorkerCoordinator ownership, InTr admission, execution, or task completion.

## Completion predicates

1. Runtime map schema/catalog/builder/validator/query/matcher/receipt surfaces. **SOURCE COMPLETE**
2. HB32/oscillator authority separation. **SOURCE COMPLETE**
3. Explicit runtime requirements and deterministic candidate resolution. **SOURCE COMPLETE**
4. Atomic runtime-resolution persistence and routing readiness. **SOURCE COMPLETE**
5. Exact-hash Master Records custody package and custody consumer. **SOURCE COMPLETE**
6. Retained-event projection and Task Registry ↔ Master Records reconciliation. **SOURCE COMPLETE**
7. Post-reconciliation transition-readiness classification. **SOURCE COMPLETE**
8. Exact-evidence governance-review packaging and closed-allowlist authority routing. **SOURCE COMPLETE**
9. Static fail-closed source-chain validation for all five request/consumer/selector bindings. **SOURCE COMPLETE**
10. Resident build requires the same fail-closed chain validation against the materialized runtime before map generation. **SOURCE COMPLETE**
11. Canonical Work registered-task ingress request for `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001` is staged through the existing generalized path. **SOURCE COMPLETE**
12. Canonical Work source materialization preserves an existing resident Task Registry instead of rolling it back. **SOURCE COMPLETE**
13. Authentic Runtime Profile Map task ingress is observed and governed into canonical task state. **RUNTIME PENDING**
14. One authentic resident cycle emits chain-preflight through authority-review-routing evidence. **RUNTIME PENDING**
15. Current WorkerCoordinator/Interlock-InTr/Master Records/Canonical Coordination authority consumes the applicable review envelope and independently performs/rejects/waits/transfers under current governance. **RUNTIME PENDING**
16. Any resulting execution/closure is retained in Master Records and reconciled back into canonical task state. **RUNTIME PENDING**

## Expected authentic evidence

- `receipts/sovereign-host/canonical-work-runtime-profile-map-request-consumption.latest.json`
- nested Canonical Work Runtime Profile Map ingress/consumption/bootstrap receipts under `runtime/canonical-work-runtime-profile-map/`
- `receipts/runtime-profile-map/source-chain-validation.latest.json`
- `receipts/sovereign-host/runtime-profile-map-build-request-consumption.latest.json`
- `receipts/runtime-profile-map/runtime-profile-map.latest.json`
- `receipts/runtime-profile-map/task-resolutions/*.json`
- `receipts/runtime-profile-map/routing-readiness/*.json`
- `receipts/runtime-profile-map/custody/runtime-profile-map-custody-package.latest.json`
- `receipts/sovereign-host/runtime-profile-map-custody-request-consumption.latest.json`
- `receipts/runtime-profile-map/reconciliation/master-records-work-events.latest.json`
- `receipts/runtime-profile-map/reconciliation/tasks/*.json`
- `receipts/sovereign-host/runtime-profile-map-reconciliation-request-consumption.latest.json`
- `receipts/runtime-profile-map/transition-readiness/*.json`
- `receipts/sovereign-host/runtime-profile-map-transition-readiness-request-consumption.latest.json`
- `receipts/runtime-profile-map/governance-review/*.json`
- `receipts/runtime-profile-map/authority-review/*/*.json`
- `receipts/sovereign-host/runtime-profile-map-governance-review-request-consumption.latest.json`
- generated `control/runtime-profile-map.json` with non-null `generated_at`
- resident `data/canonical-task-registry.json` with current-map runtime-resolution projections
- Master Records runtime-profile-map custody record

## Current boundary

No runtime-complete or ingress-complete claim is made. The task lifecycle now has explicit source staging through Canonical Work, the Canonical Work materializer preserves later resident Task Registry state, and the map build retains its fail-closed resident-chain preflight. The unresolved boundary is authentic resident task ingress plus authentic Runtime Profile Map lifecycle consumption through the existing HB32/oscillator + WorkerCoordinator architecture and resulting current-authority decisions.

The checked-in canonical task registry is currently generation 15; `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001` remains `PROPOSED`. These source changes do not qualify as authentic task ingress, runtime completion, WorkerCoordinator claim/fence, Master Records reconciliation completion, or governed closure.

## Human action

None currently required. Remaining work is machine-owned authentic resident execution and current-authority handling of resulting evidence.

## Archive readiness

All unique continuation state is preserved here. This workstream remains runtime-open until authentic resident evidence and subsequent current-governance transitions are observed.
