# Canonical Runtime Profile Map Mirror Handoff

Updated: 2026-09-04
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`
Status: `SOURCE_IMPLEMENTED_AUTHORITY_REVIEW_ROUTING_BOUND_AUTHENTIC_RESIDENT_EVIDENCE_PENDING`

## Authority boundary

This workstream is subordinate to `control/canonical-resident-carrier-contract.json`, Canonical Work Coordination, WorkerCoordinator, Universal InTr, runtime observability, and Master Records.

It MUST NOT create a second heartbeat, oscillator, scheduler, WorkerCoordinator, ingress server, credential authority, task registry, or runtime authority. HB32 + the independent 100 Hz / 10 ms oscillator remains reference/carrier substrate only and grants no admission, execution, routing, receiving, claim/fence, credential, or transition authority.

## Purpose

Provide one canonical machine-readable discovery/reconciliation projection answering which runtime substrates exist, what declared capabilities and transition surfaces they expose, what explicit observations/freshness exist, which canonical tasks can consider them compatible candidates, what routing and transition-readiness state exists, and which current authority class must review the next transition.

No map/profile/observation/match/readiness/custody/reconciliation/review/routing artifact grants authority.

## Canonical invariants

1. Declared capability and observed runtime state remain separate.
2. `CURRENT`, `STALE`, `UNKNOWN`, and `CONFLICT` are distinct observation states; unknown is not false and stale is not unavailable.
3. Source/merge/CI/deployment/HB progression never becomes inferred runtime completion.
4. Runtime selection is deterministic from explicit task requirements and remains downstream of task/Master Records/dependency reconciliation.
5. Generic `runtime missing` is inadmissible until current-map resolution identifies the exact failed predicate.
6. Runtime candidate selection, routing readiness, reconciliation, transition readiness, governance-review packaging, and authority-review routing are all non-authorizing projections.
7. WorkerCoordinator remains claim/fence authority. Interlock/InTr remains governed transition authority. TV/TVC remains credential authority. Master Records remains observed-reality/custody authority.
8. Existing WorkerCoordinator ownership is reused/waited/transferred under WorkerCoordinator authority rather than duplicated.
9. Every transition still requires current governance; no prior receipt authorizes a later transition.
10. Exact evidence references and SHA-256 values are carried forward into custody, governance-review, and authority-review routing artifacts.
11. Routing a review package to an authority inbox does not invoke that authority and does not imply acceptance, rejection, admission, execution, or transition.

## Source surfaces

- `schemas/runtime-profile-map.schema.json`
- `schemas/runtime-profile-map-custody-package.schema.json`
- `schemas/canonical-task-record.schema.json`
- `schemas/task-master-records-reconciliation.schema.json`
- `control/runtime-profile-sources.json`
- `control/runtime-profile-map.json`
- `scripts/build_runtime_profile_map.py`
- `scripts/validate_runtime_profile_map.py`
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
- `tests/test_runtime_profile_map_authority_routing.py`

Resident continuation surfaces:

- `control/resident-execution-request.d/runtime-profile-map-build-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-build.py`
- selector `runtime_profile_map`
- `control/resident-execution-request.d/runtime-profile-map-custody-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-custody.py`
- selector `runtime_profile_map_custody`
- `control/resident-execution-request.d/runtime-profile-map-reconciliation-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-reconciliation.py`
- selector `runtime_profile_map_reconciliation`
- `control/resident-execution-request.d/runtime-profile-map-transition-readiness-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-transition-readiness.py`
- selector `runtime_profile_map_transition_readiness`
- `control/resident-execution-request.d/runtime-profile-map-governance-review-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-governance-review.py`
- selector `runtime_profile_map_governance_review`

## Current resident sequence

```text
build current runtime-profile map
-> validate + exact-byte map receipt
-> resolve all canonical tasks with runtime_requirements
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

## Governance-review and authority-routing path

`scripts/build_runtime_profile_map_governance_review.py` binds the current canonical task, WorkerCoordinator projection, routing-readiness receipt, Master Records reconciliation, and transition-readiness receipt using exact file hashes. It maps `next_governance_review` to `WORKERCOORDINATOR`, `INTERLOCK_INTR`, `MASTER_RECORDS_RECONCILIATION`, or `CANONICAL_COORDINATION`.

`scripts/route_runtime_profile_map_governance_review.py` validates that the review artifact grants no authority, verifies the authority class against a closed allowlist, retains the exact review-package hash, and emits `stegverse.runtime-profile-map-authority-review-envelope/v1` under the matching local authority-review inbox:

- `receipts/runtime-profile-map/authority-review/workercoordinator/`
- `receipts/runtime-profile-map/authority-review/interlock-intr/`
- `receipts/runtime-profile-map/authority-review/master-records-reconciliation/`
- `receipts/runtime-profile-map/authority-review/canonical-coordination/`

The routing envelope explicitly records `authority_invoked=false`, `task_state_changed=false`, `claim_or_fence_minted=false`, `execution_authority_granted=false`, `interlock_intr_admission_granted=false`, and `authority_effect=NONE_AUTHORITY_REVIEW_ROUTING_ONLY`.

`consume-runtime-profile-map-governance-review.py` now materializes both the governance-review builder and authority router from already-local canonical source, builds each review package, routes it to the matching inbox, and requires both exact review output and routing-envelope output before the aggregate consumption is `COMPLETED`.

This removes a machine handoff gap without automating authority itself.

## Completion predicates

1. Runtime map schema/catalog/builder/validator/query/matcher/receipt surfaces. **SOURCE COMPLETE**
2. HB32/oscillator authority separation. **SOURCE COMPLETE**
3. Explicit runtime requirements and deterministic candidate resolution. **SOURCE COMPLETE**
4. Atomic runtime-resolution persistence and routing readiness. **SOURCE COMPLETE**
5. Exact-hash Master Records custody package and custody consumer. **SOURCE COMPLETE**
6. Retained-event projection and Task Registry ↔ Master Records reconciliation. **SOURCE COMPLETE**
7. Post-reconciliation transition-readiness classification. **SOURCE COMPLETE**
8. Resident dispatcher registration for reconciliation and transition readiness. **SOURCE COMPLETE**
9. Exact-evidence governance-review builder/request/consumer/dispatcher selector. **SOURCE COMPLETE**
10. Closed-allowlist non-authorizing routing of governance-review packages to authority-specific local inboxes. **SOURCE COMPLETE**
11. One authentic resident cycle emits all build through authority-review routing evidence. **RUNTIME PENDING**
12. Current WorkerCoordinator/Interlock-InTr/Master Records/coordination authority consumes the applicable review envelope and performs or rejects the next transition under current governance. **RUNTIME PENDING**
13. Any resulting execution/closure is retained in Master Records and reconciled back into canonical task state. **RUNTIME PENDING**

## Expected authentic evidence

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

No runtime-complete claim is made. Source implementation now reaches an exact-evidence, authority-specific local review envelope without invoking the authority. The unresolved boundary is authentic resident consumption through the existing HB32/oscillator + WorkerCoordinator architecture and the resulting current-authority transition decisions.

The checked-in canonical task registry remains generation 12 and correctly remains `PROPOSED`; this continuation did not promote source routing artifacts into runtime evidence or change coordination state.

## Human action

None currently required. Remaining work is machine-owned authentic resident execution and current-authority handling of generated review envelopes.

## Archive readiness

All unique continuation state is preserved here. The workstream remains runtime-open until authentic evidence and subsequent current-governance transitions are observed.
