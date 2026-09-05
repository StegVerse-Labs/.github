# Canonical Runtime Profile Map Mirror Handoff

Updated: 2026-09-04
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`
Status: `SOURCE_IMPLEMENTED_TASK_RUNTIME_RESOLUTION_BOUND_RESIDENT_EVIDENCE_PENDING`

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
4. HB32 + the independent 100 Hz / 10 ms oscillator remains reference/carrier substrate only.
5. Observation freshness is explicit: `CURRENT`, `STALE`, `UNKNOWN`, or `CONFLICT`; unknown is not false and stale is not unavailable.
6. Source/merge/CI/deployment/HB progression never becomes inferred runtime completion.
7. Matching is deterministic from explicit capabilities, environment, direction, mutation/deployment requirements, and optional current-observation requirements.
8. Negative requirements fail closed.
9. Runtime selection remains downstream of task/Master Records/dependency reconciliation and upstream of WorkerCoordinator admission.
10. Projection provenance is retained.
11. Secret material is forbidden from the map.
12. Generated projections are machine-built from the source catalog.
13. Projection generations are monotonic.
14. Validated generated maps emit an exact-byte integrity receipt.
15. Runtime requirements live on the canonical task; runtime candidate resolution is a projection on that task and never becomes execution ownership.

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
- `scripts/emit_runtime_profile_map_receipt.py`
- `tests/test_runtime_profile_map.py`
- `tests/test_task_runtime_resolution.py`

Resident continuation surfaces:

- `control/resident-execution-request.d/runtime-profile-map-build-001.json`
- `control/resident-execution-request.d/consume-runtime-profile-map-build.py`
- resident dispatcher selector `runtime_profile_map`

## Canonical task binding

`schemas/canonical-task-record.schema.json` now supports `runtime_requirements` and a projection-only `runtime_resolution`.

`runtime_requirements` carries explicit capabilities, environment, direction, mutation/deployment requirements, and whether a current observation is required. `runtime_resolution` may record only map ref/generation, candidate profile IDs, resolution time, `projection_only=true`, and `selection_grants_authority=false`.

Current canonical tasks now declare explicit runtime requirements. This means a task cannot merely say "runtime missing" without first being comparable against the canonical map.

`scripts/resolve_task_runtime_candidates.py` deterministically evaluates one canonical task against the current map and emits `stegverse.canonical-task-runtime-resolution/v1`. `scripts/apply_task_runtime_resolution_projection.py` can project that result back into the task registry only when task identity, correlation identity, requirements, map generation, and candidate identities all match. It does not change coordination state or WorkerCoordinator ownership.

## Source catalog and generated projection

`control/runtime-profile-sources.json` is the canonical source catalog. The builder consumes the canonical resident carrier contract, WorkerCoordinator capability profiles, WorkerCoordinator runtime registry as a required dependency, shared Universal InTr ingress source, Canonical Work runtime profile, and all JSON runtime-observability consumers.

Missing required sources fail closed. Source presence never becomes process-liveness proof.

The checked-in `control/runtime-profile-map.json` remains a bootstrap source projection with `generated_at=null`. The resident builder produces the complete current projection from already-local source and observations.

## Resident build path

The existing resident dispatcher registers selector `runtime_profile_map`. Its bounded consumer validates the exact request, preserves mutable WorkerCoordinator/shared-router state, materializes only required immutable source surfaces, builds and validates the map, emits its integrity receipt, then resolves every canonical task that declares `runtime_requirements` into separate projection receipts under:

`receipts/runtime-profile-map/task-resolutions/`

The resident build is successful only when map build, map validation, integrity receipting, and task runtime-resolution generation all succeed. These candidate resolutions still grant no execution or admission authority.

No GitHub/network source fetch, credentials, second machine, HB progression, oscillator progression, task admission, or claim/fence minting occurs in this consumer.

## Coordination relationship

```text
canonical task registry
-> Master Records reconciliation
-> dependency / incident reconciliation
-> task runtime requirements
-> canonical runtime-profile map
-> deterministic candidate resolution
-> WorkerCoordinator admission / current claim-fence
-> current Interlock/InTr transition governance
-> governed execution
-> Master Records evidence
-> task-state reconciliation
```

## Completion predicates

1. Map schema, catalog, builder, validator, query, matcher, receipt emitter and tests exist. **SOURCE COMPLETE**
2. HB32/oscillator authority boundary is correct. **SOURCE COMPLETE**
3. Worker capabilities are normalized without authority inference. **SOURCE COMPLETE**
4. Universal InTr and Canonical Work relationships are represented. **SOURCE COMPLETE**
5. Runtime observations preserve freshness/unknown semantics. **SOURCE COMPLETE**
6. Candidate matching rejects incompatible requirements deterministically. **SOURCE COMPLETE**
7. Canonical task coordination references the map as discovery only. **SOURCE COMPLETE**
8. Canonical task records carry explicit runtime requirements. **SOURCE COMPLETE**
9. Runtime candidate results can be projected back without changing task/claim authority. **SOURCE COMPLETE**
10. Resident build/dispatcher path builds, validates, receipts, and resolves task candidates. **SOURCE COMPLETE**
11. One admitted resident execution emits authentic map-build, map-integrity, and task-resolution receipts. **RUNTIME PENDING**
12. Authentic projection/receipt is reconciled/custodied as appropriate without creating runtime authority. **RUNTIME/CUSTODY PENDING**

## Expected resident evidence

- `receipts/sovereign-host/runtime-profile-map-build-request-consumption.latest.json`
- `receipts/runtime-profile-map/runtime-profile-map.latest.json`
- `receipts/runtime-profile-map/task-resolutions/STEGVERSE-CANONICAL-WORK-COORDINATION-001.json`
- `receipts/runtime-profile-map/task-resolutions/STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001.json`
- generated `control/runtime-profile-map.json` with non-null `generated_at`

## Human action

None currently required. Remaining work is machine-owned resident execution, projection persistence, and evidence reconciliation.

## Archive readiness

All source design and continuation state is captured here and in the canonical task registry. The workstream is not runtime-complete until completion predicates 11-12 are evidenced.
