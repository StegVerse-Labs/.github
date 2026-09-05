# Canonical Runtime Profile Map Mirror Handoff

Updated: 2026-09-04
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`
Status: `SOURCE_IMPLEMENTED_ROUTING_READINESS_BOUND_RESIDENT_EVIDENCE_PENDING`

## Parent authority and adjacent systems

This bounded workstream is subordinate to:

- `control/canonical-resident-carrier-contract.json`
- `docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md`
- `docs/CANONICAL_WORK_COORDINATION_RUNTIME_MIRROR_HANDOFF.md`
- `control/worker-capability-profiles.json`
- `control/worker-registry.json`
- `control/runtime-observability-consumers/`
- `workers/universal_intr_profiled_ingress.py`

It MUST NOT create a second heartbeat, oscillator, scheduler, WorkerCoordinator, ingress server, credential authority, task registry, or runtime authority.

## Purpose

Create one canonical machine-readable projection answering what execution/runtime substrates exist, what declared capabilities and transition surfaces they expose, what runtime predicates/evidence describe their observed condition, and which canonical tasks can consider them as compatible candidates.

The map is discovery/reconciliation only. Availability, capability matching, source presence, service presence, heartbeat progression, or prior receipts do not grant authorization.

## Best-practice rules

1. One map, many source authorities; the map never replaces its sources.
2. Declared capability and observed runtime state remain separate.
3. Capability matching never grants task admission, claim/fence, InTr admission, credentials, deployment, or consequence authority.
4. HB32 + independent 100 Hz / 10 ms oscillator remains reference/carrier substrate only.
5. Observation freshness is explicit: `CURRENT`, `STALE`, `UNKNOWN`, or `CONFLICT`; unknown is not false and stale is not unavailable.
6. Source/merge/CI/deployment/HB progression never becomes inferred runtime completion.
7. Matching is deterministic from explicit capabilities, environment, direction, mutation/deployment requirements, and optional current-observation requirements.
8. Negative requirements fail closed.
9. Runtime selection remains downstream of task/Master Records/dependency reconciliation and upstream of WorkerCoordinator admission.
10. Projection provenance is retained.
11. Secret material is forbidden from the map.
12. Generated projections are machine-built from the source catalog.
13. Projection generations are monotonic.
14. Validated generated maps emit exact-byte integrity receipts.
15. Runtime requirements live on canonical tasks; candidate resolution is projection-only.
16. A generic `runtime missing` conclusion is not admissible until the task has been resolved against the current canonical runtime-profile map and the exact failed predicate is identified.
17. Candidate projections are persisted atomically as a complete set; partial runtime-resolution persistence fails closed.
18. Routing readiness is evaluated separately from compatibility and separately from WorkerCoordinator authority.

## Canonical surfaces

- `schemas/runtime-profile-map.schema.json`
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
- `scripts/finalize_runtime_profile_map_cycle.py`
- `scripts/emit_runtime_profile_map_receipt.py`
- `tests/test_runtime_profile_map.py`
- `tests/test_task_runtime_resolution.py`

Resident continuation surfaces:

- `control/resident-execution-request.d/runtime-profile-map-build-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-build.py`
- resident dispatcher selector `runtime_profile_map`

## Canonical task binding

`schemas/canonical-task-record.schema.json` supports `runtime_requirements` and projection-only `runtime_resolution`.

`runtime_requirements` carries explicit capabilities, environment, direction, mutation/deployment requirements, and whether a current observation is required. `runtime_resolution` records only map ref/generation, compatible profile IDs, resolution time, `projection_only=true`, and `selection_grants_authority=false`.

Current canonical tasks declare explicit runtime requirements, so a task cannot simply report `runtime missing` without being comparable against the canonical map.

`scripts/resolve_task_runtime_candidates.py` deterministically evaluates one canonical task against the current map. `scripts/apply_all_task_runtime_resolutions.py` requires the resolution set to exactly match every task that declares runtime requirements, validates every result against the same map generation, and atomically persists all projections. It does not change coordination state or WorkerCoordinator ownership.

## Routing readiness

`scripts/evaluate_task_runtime_routing_readiness.py` distinguishes runtime compatibility from actual routing readiness. It reports explicit predicates for:

- runtime requirements declared;
- current map-generation resolution present;
- at least one compatible runtime candidate;
- dependencies resolved;
- no active task blocker;
- no competing projected WorkerCoordinator ownership.

Its possible dispositions include:

- `RUNTIME_PROFILE_RESOLUTION_REQUIRED`
- `NO_COMPATIBLE_RUNTIME_PROFILE_CANDIDATE`
- `TASK_DEPENDENCY_OR_BLOCKER_PREVENTS_ROUTING`
- `EXISTING_WORKERCOORDINATOR_OWNERSHIP_REUSE_WAIT_OR_TRANSFER`
- `ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW`

Even the last state grants no authority. WorkerCoordinator admission/current claim-fence and current Interlock/InTr governance remain mandatory.

`data/task-coordination-policy.json` now explicitly requires runtime-map resolution and routing-readiness evaluation before WorkerCoordinator admission review, and forbids a generic runtime-missing escalation before that comparison.

## Source catalog and generated projection

`control/runtime-profile-sources.json` remains the canonical source catalog. The builder consumes the canonical resident carrier contract, WorkerCoordinator capability profiles, WorkerCoordinator runtime registry as a required dependency, shared Universal InTr ingress source, Canonical Work runtime profile, and all JSON runtime-observability consumers.

Missing required sources fail closed. Source presence never becomes process-liveness proof.

The checked-in `control/runtime-profile-map.json` remains a bootstrap source projection with `generated_at=null`. The resident builder produces the current projection from already-local source and observations.

## Resident build path

The existing resident dispatcher registers selector `runtime_profile_map`. Its bounded consumer validates the exact request, preserves mutable WorkerCoordinator/shared-router/task-registry state, and uses only already-local canonical source.

One admitted resident cycle now performs:

```text
build runtime-profile map
-> validate map
-> emit map integrity receipt
-> resolve every canonical task with runtime_requirements
-> require complete resolution set
-> atomically persist all runtime_resolution projections
-> validate canonical work coordination consistency
-> emit per-task routing-readiness receipts
-> emit resident build-consumption receipt
```

The consumer materializes the exact coordination/schema/scripts required for this sequence while preserving current `control/worker-registry.json`, current shared Universal InTr router, and an already-existing resident canonical task registry.

No GitHub/network source fetch, credentials, second machine, HB progression, oscillator progression, task admission, coordination-state transition, or claim/fence minting occurs in this consumer.

## Coordination relationship

```text
canonical task registry
-> Master Records reconciliation
-> dependency / incident reconciliation
-> task runtime requirements
-> canonical runtime-profile map
-> deterministic candidate resolution
-> atomic runtime_resolution projection
-> routing-readiness evaluation
-> WorkerCoordinator admission / current claim-fence
-> current Interlock/InTr transition governance
-> governed execution
-> Master Records evidence
-> task-state reconciliation
```

## Completion predicates

1. Map schema/catalog/builder/validator/query/matcher/receipt emitter exist. **SOURCE COMPLETE**
2. HB32/oscillator authority boundary is correct. **SOURCE COMPLETE**
3. Worker capabilities normalize without authority inference. **SOURCE COMPLETE**
4. Universal InTr and Canonical Work relationships are represented. **SOURCE COMPLETE**
5. Runtime observations preserve freshness/unknown semantics. **SOURCE COMPLETE**
6. Candidate matching deterministically rejects incompatible profiles. **SOURCE COMPLETE**
7. Canonical coordination references the map as discovery only. **SOURCE COMPLETE**
8. Canonical task records carry explicit runtime requirements. **SOURCE COMPLETE**
9. Candidate results project back without changing task/claim authority. **SOURCE COMPLETE**
10. Batch projection is complete-set, fail-closed, and atomic. **SOURCE COMPLETE**
11. Routing-readiness evaluator prevents ambiguous runtime-missing conclusions and produces exact dispositions. **SOURCE COMPLETE**
12. Resident build/dispatcher path builds, validates, receipts, resolves, persists, validates coordination, and emits routing-readiness evidence. **SOURCE COMPLETE**
13. One admitted resident execution emits authentic map-build, map-integrity, task-resolution, registry-projection, and routing-readiness receipts. **RUNTIME PENDING**
14. Authentic projection/evidence is reconciled/custodied as appropriate without creating runtime authority. **RUNTIME/CUSTODY PENDING**

## Expected resident evidence

- `receipts/sovereign-host/runtime-profile-map-build-request-consumption.latest.json`
- `receipts/runtime-profile-map/runtime-profile-map.latest.json`
- `receipts/runtime-profile-map/task-resolutions/STEGVERSE-CANONICAL-WORK-COORDINATION-001.json`
- `receipts/runtime-profile-map/task-resolutions/STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001.json`
- `receipts/runtime-profile-map/routing-readiness/STEGVERSE-CANONICAL-WORK-COORDINATION-001.json`
- `receipts/runtime-profile-map/routing-readiness/STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001.json`
- generated `control/runtime-profile-map.json` with non-null `generated_at`
- resident `data/canonical-task-registry.json` with current-map `runtime_resolution` projections

## Human action

None currently required. Remaining work is machine-owned resident execution and evidence reconciliation.

## Archive readiness

All source design and continuation state is captured here and in the canonical task registry. The workstream is not runtime-complete until completion predicates 13-14 are evidenced.
