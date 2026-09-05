# Canonical Runtime Profile Map Mirror Handoff

Updated: 2026-09-04
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`
Status: `SOURCE_IMPLEMENTED_ROUTING_AND_CUSTODY_INPUT_BOUND_AUTHENTIC_RESIDENT_EVIDENCE_PENDING`

## Parent authority and adjacent systems

This bounded workstream is subordinate to `control/canonical-resident-carrier-contract.json`, Canonical Work Coordination, WorkerCoordinator, runtime observability, Universal InTr, and Master Records. It MUST NOT create a second heartbeat, oscillator, scheduler, WorkerCoordinator, ingress server, credential authority, task registry, or runtime authority.

HB32 + the independent 100 Hz / 10 ms oscillator remains reference/carrier substrate only. It grants no admission, execution, claim/fence, credential, routing, receiving, or transition authority.

## Purpose

Provide one canonical machine-readable discovery/reconciliation projection answering what runtime substrates exist, which declared capabilities and transition surfaces they expose, what explicit runtime observations/freshness are available, and which canonical tasks can consider them compatible candidates.

A profile declaration, profile match, runtime observation, routing-readiness result, source presence, service presence, HB progression, or prior receipt never grants authority.

## Best-practice invariants

1. One map projects many source authorities without replacing them.
2. Declared capability and observed runtime state remain separate.
3. Observation freshness is explicit: `CURRENT`, `STALE`, `UNKNOWN`, or `CONFLICT`; unknown is not false and stale is not unavailable.
4. Source/merge/CI/deployment/HB progression never becomes inferred runtime completion.
5. Matching is deterministic from task-declared capabilities, environment, direction, mutation/deployment requirements, and optional current-observation requirements.
6. Negative requirements fail closed.
7. Runtime selection remains downstream of task/Master Records/dependency reconciliation and upstream of WorkerCoordinator admission.
8. Provenance is retained and secret material is forbidden.
9. Projection generations are monotonic.
10. Runtime requirements live on canonical tasks; candidate resolution is projection-only.
11. Generic `runtime missing` is not admissible until the current task has been resolved against the current map and the exact failed predicate is identified.
12. Candidate projections are persisted atomically as a complete set.
13. Routing readiness is distinct from compatibility and distinct from WorkerCoordinator authority.
14. Exact map/routing evidence is packaged for Master Records custody without performing custody or creating authority.

## Canonical source surfaces

- `schemas/runtime-profile-map.schema.json`
- `schemas/runtime-profile-map-custody-package.schema.json`
- `schemas/canonical-task-record.schema.json`
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
- `scripts/emit_runtime_profile_map_receipt.py`
- `tests/test_runtime_profile_map.py`
- `tests/test_task_runtime_resolution.py`

Resident continuation surfaces:

- `control/resident-execution-request.d/runtime-profile-map-build-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-build.py`
- dispatcher selector `runtime_profile_map`
- `control/resident-execution-request.d/runtime-profile-map-custody-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-custody.py`

Master Records custody counterpart:

- `master-records/orchestration/RUNTIME_PROFILE_MAP_CUSTODY_MIRROR_HANDOFF.md`
- `master-records/orchestration/schemas/runtime_profile_map_custody.schema.json`
- `master-records/orchestration/scripts/ingest_runtime_profile_map_custody.py`
- `master-records/orchestration/tests/test_runtime_profile_map_custody.py`

## Canonical task binding

Canonical task records support explicit `runtime_requirements` and projection-only `runtime_resolution`. Candidate resolution can be projected back only when task identity, correlation identity, requirements, map generation, and candidate identities all match. It never changes coordination state or WorkerCoordinator ownership.

Routing readiness separately evaluates current-map resolution, compatible candidates, dependencies, blockers, and projected WorkerCoordinator ownership. Possible dispositions include resolution required, no compatible candidate, dependency/blocker prevention, existing ownership reuse/wait/transfer, and eligibility for WorkerCoordinator admission review. Even the last disposition grants no authority.

## Resident build cycle

One admitted resident `runtime_profile_map` cycle uses only already-local canonical source and preserves current WorkerCoordinator state, shared Universal InTr router, and existing resident task registry. It performs:

```text
build current runtime-profile map
-> validate map
-> emit exact-byte map integrity receipt
-> resolve every canonical task with runtime_requirements
-> require complete resolution set
-> atomically persist runtime_resolution projections
-> validate Canonical Work coordination consistency
-> emit per-task routing-readiness receipts
-> build exact-hash runtime-profile-map custody package
-> emit resident build-consumption receipt
```

The custody package retains exact hashes/refs for the generated map, map-integrity receipt, post-projection canonical task registry, every task-resolution receipt, and every routing-readiness receipt. Package generation is not Master Records custody.

A separate bounded custody request/consumer is staged to invoke the already-local Master Records custody consumer when the package and `STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT` are available. It performs no network source fetch and does not mint execution authority.

## Master Records integration

`master-records/orchestration` now has a dedicated runtime-profile-map custody contract. Its consumer verifies every package artifact against its declared SHA-256 and writes append-only custody under `custody/runtime-profile-map/`. The canonical Master Records work-event projector includes that custody root by default so retained runtime-profile-map evidence becomes comparable to canonical task state without turning custody acceptance into task completion or execution authority.

## Coordination sequence

```text
Canonical Task Registry
-> Master Records reconciliation
-> dependency / incident reconciliation
-> explicit task runtime requirements
-> Canonical Runtime Profile Map
-> deterministic candidate resolution
-> atomic runtime_resolution projection
-> routing-readiness evaluation
-> WorkerCoordinator admission / current claim-fence
-> current Interlock/InTr governance
-> governed execution
-> exact runtime evidence
-> Master Records custody/reconstruction
-> task-state reconciliation
```

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
11. Master Records exact-hash custody consumer and canonical work-event projection support the generated package. **SOURCE COMPLETE**
12. One authentic resident execution emits map-build, map-integrity, task-resolution, routing-readiness, registry-projection, and custody-package evidence. **RUNTIME PENDING**
13. The authentic package is retained by Master Records and projected into reconciliation. **RUNTIME/CUSTODY PENDING**
14. WorkerCoordinator/Interlock-InTr subsequently execute only work independently admitted under current governance. **RUNTIME PENDING**

## Expected authentic evidence

- `receipts/sovereign-host/runtime-profile-map-build-request-consumption.latest.json`
- `receipts/runtime-profile-map/runtime-profile-map.latest.json`
- `receipts/runtime-profile-map/task-resolutions/*.json`
- `receipts/runtime-profile-map/routing-readiness/*.json`
- `receipts/runtime-profile-map/custody/runtime-profile-map-custody-package.latest.json`
- generated `control/runtime-profile-map.json` with non-null `generated_at`
- resident `data/canonical-task-registry.json` with current-map runtime-resolution projections
- `master-records/orchestration/custody/runtime-profile-map/RUNTIME-PROFILE-MAP-G<generation>-<hash-prefix>.json`

## Current boundary

No runtime-complete claim is made. Source implementation now covers discovery, deterministic matching, routing readiness, exact-hash custody packaging, Master Records custody validation, and reconciliation projection. The unresolved boundary is authentic resident consumption through the existing HB32/oscillator + WorkerCoordinator architecture and subsequent current-governance transitions.

## Human action

None currently required. Remaining work is machine-owned authentic resident execution, custody consumption, and evidence reconciliation.

## Archive readiness

All unique continuation state is preserved here and in the canonical task system. This workstream remains runtime-open until completion predicates 12-14 are evidenced.
