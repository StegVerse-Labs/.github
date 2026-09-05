# Canonical Runtime Profile Map Mirror Handoff

Updated: 2026-09-04
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`
Status: `SOURCE_IMPLEMENTED_POST_RECONCILIATION_TRANSITION_READINESS_BOUND_AUTHENTIC_RESIDENT_EVIDENCE_PENDING`

## Authority boundary

This workstream is subordinate to `control/canonical-resident-carrier-contract.json`, Canonical Work Coordination, WorkerCoordinator, Universal InTr, runtime observability, and Master Records.

It MUST NOT create a second heartbeat, oscillator, scheduler, WorkerCoordinator, ingress server, credential authority, task registry, or runtime authority. HB32 + the independent 100 Hz / 10 ms oscillator remains reference/carrier substrate only and grants no admission, execution, routing, receiving, claim/fence, credential, or transition authority.

## Purpose

Provide one canonical machine-readable discovery/reconciliation projection answering which runtime substrates exist, what declared capabilities and transition surfaces they expose, what explicit runtime observations/freshness are available, which canonical tasks can consider them compatible candidates, and what governance review class is appropriate after Master Records reconciliation.

A profile declaration, runtime observation, capability match, routing-readiness result, custody record, reconciliation result, transition-readiness result, source presence, service presence, heartbeat progression, or prior receipt never grants execution authority.

## Best-practice invariants

1. One map projects many source authorities without replacing them.
2. Declared capability and observed runtime state remain separate.
3. Observation freshness is explicit: `CURRENT`, `STALE`, `UNKNOWN`, or `CONFLICT`; unknown is not false and stale is not unavailable.
4. Source/merge/CI/deployment/HB progression never becomes inferred runtime completion.
5. Matching is deterministic from task-declared capabilities, environment, direction, mutation/deployment requirements, and optional current-observation requirements.
6. Negative requirements fail closed.
7. Runtime selection remains downstream of Task Registry/Master Records/dependency reconciliation and upstream of WorkerCoordinator admission.
8. Provenance is retained and secret material is forbidden.
9. Projection generations are monotonic.
10. Runtime requirements live on canonical tasks; runtime resolution is projection-only.
11. Generic `runtime missing` is inadmissible until the current task has been resolved against the current map and the exact failed predicate is identified.
12. Candidate projections are persisted atomically as a complete set.
13. Routing readiness is distinct from compatibility and distinct from WorkerCoordinator authority.
14. Exact map/routing evidence is packaged for Master Records custody without custody itself granting authority.
15. Master Records custody is followed by explicit task reconciliation; custody acceptance does not itself satisfy task completion predicates.
16. Reconciliation emits evidence/disposition only and cannot silently advance task coordination state, close work, or mint claim/fence authority.
17. Post-reconciliation transition readiness is a separate non-authorizing projection; it identifies the next governance review class but does not perform that transition.
18. Existing WorkerCoordinator ownership is reused/waited/transferred under WorkerCoordinator authority rather than duplicated.

## Canonical source surfaces

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
- `scripts/evaluate_runtime_profile_map_transition_readiness.py`
- `scripts/build_runtime_profile_map_custody_package.py`
- `scripts/finalize_runtime_profile_map_cycle.py`
- `scripts/reconcile_task_registry_master_records.py`
- `scripts/emit_runtime_profile_map_receipt.py`
- `tests/test_runtime_profile_map.py`
- `tests/test_task_runtime_resolution.py`
- `tests/test_runtime_profile_map_reconciliation.py`
- `tests/test_runtime_profile_map_transition_readiness.py`

Resident continuation surfaces:

- `control/resident-execution-request.d/runtime-profile-map-build-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-build.py`
- dispatcher selector `runtime_profile_map`
- `control/resident-execution-request.d/runtime-profile-map-custody-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-custody.py`
- dispatcher selector `runtime_profile_map_custody`
- `control/resident-execution-request.d/runtime-profile-map-reconciliation-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-reconciliation.py`
- dispatcher selector `runtime_profile_map_reconciliation`
- `control/resident-execution-request.d/runtime-profile-map-transition-readiness-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-transition-readiness.py`
- dispatcher selector `runtime_profile_map_transition_readiness`

## Important correction made in this continuation

The reconciliation consumer existed in source but was not actually registered in `scripts/dispatch_resident_execution_requests.py`. That omission is now corrected. The dispatcher also recognizes reconciliation and transition-readiness wait states as non-failure states. No runtime receipt is claimed merely because the selector now exists.

## Resident build + custody + reconciliation + transition-readiness sequence

```text
build current runtime-profile map
-> validate map
-> emit exact-byte map integrity receipt
-> resolve every canonical task with runtime_requirements
-> atomically persist runtime_resolution projections
-> emit per-task routing-readiness receipts
-> build exact-hash custody package
-> Master Records exact-hash custody ingestion
-> project retained Master Records work events
-> reconcile every canonical task carrying runtime_requirements
-> emit per-task reconciliation receipts
-> combine task state + routing readiness + reconciliation + current WorkerCoordinator projection
-> emit post-reconciliation transition-readiness receipt
-> current authority performs or rejects any subsequent transition independently
```

`scripts/evaluate_runtime_profile_map_transition_readiness.py` produces explicit dispositions including:

- `BLOCK_FOR_RECONCILIATION_CONFLICT`
- `WAIT_FOR_REQUIRED_EVIDENCE`
- `RECONCILE_TASK_STATE_WITH_OBSERVED_REALITY`
- `WAIT_OR_REQUEST_EVIDENCE_RECONCILIATION`
- `DEPENDENCY_OR_BLOCKER_PREVENTS_TRANSITION`
- `EXISTING_WORKERCOORDINATOR_OWNERSHIP_REUSE_WAIT_OR_TRANSFER`
- `ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW`
- `NO_CURRENT_TRANSITION_CANDIDATE`

Even `ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW` grants no execution authority. WorkerCoordinator admission/current claim-fence and current Interlock/InTr transition governance remain mandatory.

## Completion predicates

1. Map schema/catalog/builder/validator/query/matcher/receipt emitter exist. **SOURCE COMPLETE**
2. HB32/oscillator authority boundary is correct. **SOURCE COMPLETE**
3. Worker capability/environment normalization avoids false runtime-missing conclusions. **SOURCE COMPLETE**
4. Runtime observations preserve freshness/unknown semantics. **SOURCE COMPLETE**
5. Deterministic matching rejects incompatible profiles. **SOURCE COMPLETE**
6. Canonical task records carry explicit runtime requirements. **SOURCE COMPLETE**
7. Candidate results project atomically without changing task/claim authority. **SOURCE COMPLETE**
8. Routing readiness produces exact non-authorizing dispositions. **SOURCE COMPLETE**
9. Resident build path builds, validates, receipts, resolves, persists, and packages custody input. **SOURCE COMPLETE**
10. Master Records exact-hash custody and canonical work-event projection support the package. **SOURCE COMPLETE**
11. Custody completion chains to deterministic per-task Master Records reconciliation without changing task state or authority. **SOURCE COMPLETE**
12. Reconciliation resident selector is actually registered in the resident dispatcher. **SOURCE COMPLETE**
13. Post-reconciliation transition-readiness evaluator/request/consumer/dispatcher path exists and remains non-authorizing. **SOURCE COMPLETE**
14. One authentic resident execution emits map-build, integrity, task-resolution, routing-readiness, registry-projection, custody-package, custody-consumption, reconciliation, and transition-readiness evidence. **RUNTIME PENDING**
15. Authentic transition-readiness is evaluated by WorkerCoordinator/Interlock-InTr under current governance before any transition. **RUNTIME PENDING**
16. Any execution/closure is evidenced in Master Records and reconciled back to the task registry. **RUNTIME PENDING**

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
- generated `control/runtime-profile-map.json` with non-null `generated_at`
- resident `data/canonical-task-registry.json` with current-map runtime-resolution projections
- `master-records/orchestration/custody/runtime-profile-map/RUNTIME-PROFILE-MAP-G<generation>-<hash-prefix>.json`

## Current boundary

No runtime-complete claim is made. Source implementation now covers discovery, deterministic matching, routing readiness, exact-hash custody packaging, Master Records custody validation, retained-event projection, Task Registry ↔ Master Records reconciliation, and post-reconciliation transition-readiness classification. The unresolved boundary is authentic resident consumption through the existing HB32/oscillator + WorkerCoordinator architecture and current-governance transitions.

## Human action

None currently required. Remaining work is machine-owned authentic resident execution and current-governance handling of resulting transition-readiness evidence.

## Archive readiness

All unique continuation state is preserved here and in the canonical task registry. This workstream remains runtime-open until completion predicates 14-16 are evidenced.
