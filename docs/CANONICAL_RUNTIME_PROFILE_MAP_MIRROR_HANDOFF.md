# Canonical Runtime Profile Map Mirror Handoff

Updated: 2026-09-04
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`
Status: `SOURCE_IMPLEMENTED_CUSTODY_TO_RECONCILIATION_CHAIN_BOUND_AUTHENTIC_RESIDENT_EVIDENCE_PENDING`

## Authority boundary

This workstream is subordinate to `control/canonical-resident-carrier-contract.json`, Canonical Work Coordination, WorkerCoordinator, Universal InTr, runtime observability, and Master Records.

It MUST NOT create a second heartbeat, oscillator, scheduler, WorkerCoordinator, ingress server, credential authority, task registry, or runtime authority. HB32 + the independent 100 Hz / 10 ms oscillator remains reference/carrier substrate only and grants no admission, execution, routing, receiving, claim/fence, credential, or transition authority.

## Purpose

Provide one canonical machine-readable discovery/reconciliation projection answering which runtime substrates exist, what declared capabilities and transition surfaces they expose, what explicit runtime observations/freshness are available, and which canonical tasks can consider them compatible candidates.

A profile declaration, runtime observation, capability match, routing-readiness result, source presence, service presence, heartbeat progression, custody record, or prior receipt never grants execution authority.

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
- `scripts/build_runtime_profile_map_custody_package.py`
- `scripts/finalize_runtime_profile_map_cycle.py`
- `scripts/reconcile_task_registry_master_records.py`
- `scripts/emit_runtime_profile_map_receipt.py`
- `tests/test_runtime_profile_map.py`
- `tests/test_task_runtime_resolution.py`
- `tests/test_runtime_profile_map_reconciliation.py`

Resident continuation surfaces:

- `control/resident-execution-request.d/runtime-profile-map-build-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-build.py`
- dispatcher selector `runtime_profile_map`
- `control/resident-execution-request.d/runtime-profile-map-custody-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-custody.py`
- `control/resident-execution-request.d/runtime-profile-map-reconciliation-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-reconciliation.py`

Master Records counterparts:

- `master-records/orchestration/RUNTIME_PROFILE_MAP_CUSTODY_MIRROR_HANDOFF.md`
- `master-records/orchestration/CANONICAL_WORK_COORDINATION_CUSTODY_MIRROR_HANDOFF.md`
- `master-records/orchestration/schemas/runtime_profile_map_custody.schema.json`
- `master-records/orchestration/scripts/ingest_runtime_profile_map_custody.py`
- `master-records/orchestration/scripts/project_canonical_work_events.py`

## Canonical task binding

Canonical task records carry explicit `runtime_requirements` and projection-only `runtime_resolution`. Candidate resolution may be projected back only when task identity, correlation identity, requirements, map generation, and candidate identities match. That projection never changes coordination state or WorkerCoordinator ownership.

Routing readiness separately evaluates current-map resolution, compatible candidates, dependencies, blockers, and projected WorkerCoordinator ownership. Its dispositions distinguish unresolved runtime-profile resolution, no compatible candidate, dependency/blocker prevention, existing ownership requiring reuse/wait/transfer, and eligibility for WorkerCoordinator admission review. Even admission-review eligibility grants no execution authority.

## Resident build + custody + reconciliation sequence

One admitted resident sequence now has source plumbing for:

```text
build current runtime-profile map
-> validate map
-> emit exact-byte map integrity receipt
-> resolve every canonical task with runtime_requirements
-> require complete resolution set
-> atomically persist runtime_resolution projections
-> validate Canonical Work coordination consistency
-> emit per-task routing-readiness receipts
-> build exact-hash custody package
-> Master Records exact-hash custody ingestion
-> project current retained Master Records work events
-> reconcile every canonical task carrying runtime_requirements
-> emit per-task reconciliation receipts
```

The custody consumer now chains to the reconciliation consumer after authentic custody success when the canonical source root and local Master Records root are available. If reconciliation is unavailable, custody remains valid and the reconciliation request remains independently staged/retryable; no authority or task state is inferred.

The reconciliation consumer waits for `runtime-profile-map-custody-request-consumption.latest.json:COMPLETED`, requires the already-local `master-records/orchestration` projector, materializes only the exact local reconciliation script/schema it needs, projects retained Master Records events, and emits one deterministic reconciliation for each canonical task with runtime requirements.

It explicitly performs no network source fetch, HB/oscillator progression, runtime selection, task-state mutation, closure, claim/fence creation, or credential use.

## Master Records integration

`master-records/orchestration` validates exact hashes and writes append-only Runtime Profile Map custody under `custody/runtime-profile-map/`. Its canonical work-event projector includes that custody root by default. The resident reconciliation consumer then compares those retained events with the canonical Task Registry using `scripts/reconcile_task_registry_master_records.py`.

Possible reconciliation states remain `CONSISTENT`, `TASK_AHEAD_OF_EVIDENCE`, `REALITY_AHEAD_OF_TASK`, `CONFLICT`, `UNKNOWN`, and `ORPHANED_EVENT` at the system contract level. The task-specific reconciler never treats absence of evidence as proof that work did not occur.

## Completion predicates

1. Map schema/catalog/builder/validator/query/matcher/receipt emitter exist. **SOURCE COMPLETE**
2. HB32/oscillator authority boundary is correct. **SOURCE COMPLETE**
3. Worker capability/environment normalization avoids false runtime-missing conclusions. **SOURCE COMPLETE**
4. Universal InTr and Canonical Work relationships are represented. **SOURCE COMPLETE**
5. Runtime observations preserve freshness/unknown semantics. **SOURCE COMPLETE**
6. Deterministic matching rejects incompatible profiles. **SOURCE COMPLETE**
7. Canonical task records carry explicit runtime requirements. **SOURCE COMPLETE**
8. Candidate results project atomically without changing task/claim authority. **SOURCE COMPLETE**
9. Routing readiness produces exact non-authorizing dispositions. **SOURCE COMPLETE**
10. Resident build path builds, validates, receipts, resolves, persists, validates, and packages custody input. **SOURCE COMPLETE**
11. Master Records exact-hash custody and canonical work-event projection support the package. **SOURCE COMPLETE**
12. Custody completion chains to deterministic per-task Master Records reconciliation without changing task state or authority. **SOURCE COMPLETE**
13. One authentic resident execution emits map-build, integrity, task-resolution, routing-readiness, registry-projection, custody-package, custody-consumption, and reconciliation evidence. **RUNTIME PENDING**
14. Authentic reconciliation results are evaluated under current governance for any subsequent task transition. **RUNTIME PENDING**
15. WorkerCoordinator/Interlock-InTr execute only work independently admitted under current governance. **RUNTIME PENDING**

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
- generated `control/runtime-profile-map.json` with non-null `generated_at`
- resident `data/canonical-task-registry.json` with current-map runtime-resolution projections
- `master-records/orchestration/custody/runtime-profile-map/RUNTIME-PROFILE-MAP-G<generation>-<hash-prefix>.json`

## Current boundary

No runtime-complete claim is made. Source implementation now covers discovery, matching, routing readiness, exact-hash custody packaging, Master Records custody validation, retained-event projection, and deterministic Task Registry ↔ Master Records reconciliation. The unresolved boundary is authentic resident consumption through the existing HB32/oscillator + WorkerCoordinator architecture and subsequent current-governance transitions.

## Human action

None currently required. Remaining work is machine-owned authentic resident execution and evaluation of resulting reconciliation evidence under current governance.

## Archive readiness

All unique continuation state is preserved here and in the canonical task system. This workstream remains runtime-open until completion predicates 13-15 are evidenced.
