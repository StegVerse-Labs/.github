# Canonical Work Coordination Runtime Mirror Handoff

Updated: 2026-09-13
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Status: `REGISTERED_TASK_INGRESS_RUNTIME_PROFILE_MAP_STAGED_LIVE_REGISTRY_PRESERVATION_SOURCE_COMPLETE_STATE_TRANSITION_PENDING`

## Parent authority

Parent coordination handoff: `docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md`.
Canonical resident runtime/carrier authority: `control/canonical-resident-carrier-contract.json`.
This runtime lane MUST NOT create a second heartbeat, oscillator, scheduler, WorkerCoordinator, credential path, task registry, or execution authority.

## HB / oscillator binding

Canonical runtime reference is HB32 with `INDEPENDENT_PHASE_OSCILLATOR`, 100 Hz / 10 ms, `progression_dependency=OSCILLATOR_ONLY`. HB and HB-derived InTr carriage are reference/transport observability only and grant no admission, execution, claim/fence, routing, transition, receiving, or credential authority.

## Installed runtime-source surfaces

- `control/canonical-work-runtime-profile.json`
- `scripts/build_canonical_work_intr_request.py`
- `scripts/project_canonical_work_runtime.py`
- `scripts/validate_canonical_work_runtime_profile.py`
- `scripts/consume_canonical_work_intr_materialization_request.py`
- `workers/canonical_work_intr_ingress.py`
- `scripts/install_canonical_work_universal_intr_route.py`
- `scripts/project_master_records_work_events.py`
- `scripts/reevaluate_canonical_task_dependencies.py`
- `scripts/normalize_github_failure_email_events.py`
- `scripts/reconcile_admitted_canonical_work.py`
- `scripts/consume_admitted_dependency_resolution.py`
- `scripts/apply_admitted_canonical_work_projection.py`
- `scripts/project_worker_claim_into_canonical_task.py`
- `scripts/run_canonical_work_event_bootstrap.py`
- `scripts/install_and_run_canonical_work_event_bootstrap.py`
- `control/resident-execution-request.d/canonical-work-coordination-bootstrap-001.json`
- `control/resident-execution-request.d/canonical-work-quantum-resilience-001.json`
- `control/resident-execution-request.d/canonical-work-object-provenance-continuity-190.json`
- `control/resident-execution-request.d/canonical-work-runtime-profile-map-001.json`
- `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py`
- `scripts/dispatch_resident_execution_requests.py`
- `tests/test_canonical_work_registered_task_ingress.py`
- `tests/test_object_provenance_canonical_work_resident_request.py`
- `tests/test_runtime_profile_map_canonical_work_resident_request.py`
- `tests/test_canonical_work_resident_registry_preservation.py`
- `data/canonical-task-registry.json`

Master Records corresponding bounded feed contract remains in `master-records/orchestration/CANONICAL_WORK_COORDINATION_CUSTODY_MIRROR_HANDOFF.md` with the existing canonical work-event projector/schema/tests.

## Registered-task ingress behavior

`build_canonical_work_intr_request.py` emits the existing `stegverse.universal-intr-materialization-request/v1` shape and may bind to the canonical HB-derived carrier profile. The result remains source material until authentic Interlock/InTr ingress admits it.

`workers/canonical_work_intr_ingress.py` is a reusable adapter for the existing Universal InTr listener. It starts no server, validates CanonicalWork destination/binding, writes a write-once `INGRESS_ADMITTED` receipt, preserves the non-authorizing HB carrier boundary, and dispatches only the canonical-work coordination consumer.

`scripts/install_canonical_work_universal_intr_route.py` is an idempotent fail-closed transformer for the existing `workers/universal_intr_profiled_ingress.py`. Source installation cannot itself prove governed ingress.

`scripts/run_canonical_work_event_bootstrap.py` accepts an explicit **registered canonical task** only when it resolves exactly once in the Task Registry, remains `PROPOSED`, allows `INGRESS_ADMITTED`, has no projected WorkerCoordinator claim/fence, and preserves the canonical authority model. It refuses unregistered, duplicate, non-PROPOSED, already-claimed, or transition-ineligible task identities. It reuses the existing shared Universal InTr server and does not create another listener, scheduler, WorkerCoordinator, or authority path.

`scripts/install_and_run_canonical_work_event_bootstrap.py` joins route install/check and bounded bootstrap in one resident-machine sequence and forwards the explicit registered task identity.

The staged requests include the coordination task, `QUANTUM-RESILIENCE-001`, `STEGVERSE-OBJECT-PROVENANCE-CONTINUITY-190`, and `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`. The Runtime Profile Map request is `control/resident-execution-request.d/canonical-work-runtime-profile-map-001.json`; its expected governed request-consumption transition result is `receipts/sovereign-host/canonical-work-runtime-profile-map-request-consumption.latest.json`. All four reuse the one existing dispatcher selector `canonical_work_coordination` and the same resident consumer.

## Live canonical registry preservation

A source review after staging the Runtime Profile Map request identified a resident-state rollback hazard: the Canonical Work consumer's local source materialization list previously included `data/canonical-task-registry.json` as an unconditional exact-copy artifact. On a resident runtime that had already accumulated governed ingress/runtime-resolution/task-state projections, a later request visit could therefore replace newer mutable coordination state with the static source registry.

That behavior is corrected. `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py` now treats `data/canonical-task-registry.json` as `PRESERVE_IF_PRESENT` mutable resident coordination state. A fresh resident runtime may seed the registry from canonical source when the file is absent; an existing resident registry is retained byte-for-byte and its resident SHA-256 plus source SHA-256 are recorded in source-materialization evidence. The request-consumption receipt records whether the existing registry was preserved.

This preservation does not validate or authorize the retained registry. The subsequent registered-task identity/state checks, Interlock/InTr admission, WorkerCoordinator ownership rules, Master Records reconciliation, and all current-governance transitions remain independently mandatory. It only prevents local source refresh from rolling resident coordination state backward.

`tests/test_canonical_work_resident_registry_preservation.py` covers both cases: an existing resident registry remains unchanged, while an absent resident registry is seeded from canonical source.

## README completeness

Two README-impact determinations apply to this continuation:

1. Adding `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001` to the already-generalized request set was `material_function_change=false`; existing **Canonical Work task ingress** documentation already covered multiple explicit registered-task specifications and the same authority/failure model.
2. Changing canonical registry materialization from unconditional replacement to preserve-if-present **is** a material runtime/failure-semantics change. `README.md` was updated in the same logical change set to document that the resident registry is mutable state, is seeded only when absent, and must not be overwritten by static source materialization.

README completeness remains evidence-only and grants no execution or task authority.

## Registry state

The checked-in canonical registry is generation 130. `STEGVERSE-CANONICAL-WORK-COORDINATION-001` and `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001` remain `PROPOSED` in source state unless a governed state transition changes that canonical state. Source/request staging, preservation logic, tests, merge, CI, deployment, and heartbeat progression do not promote task state.

For Runtime Profile Map, its existing map-build/custody/reconciliation/readiness resident source remains non-authorizing. The Canonical Work request supplies explicit governed task-ingress staging for the lifecycle; it does not replace or duplicate Runtime Profile Map build consumers.

## Required governed state-transition sequence

```text
resident HB32/oscillator runtime dispatch cycle
-> dispatcher visits canonical_work_coordination
-> consumer preserves existing resident canonical task registry (or seeds it only if absent)
-> consumer validates each exact REQUESTED object independently
-> install_and_run_canonical_work_event_bootstrap.py --task-id <registered task>
-> existing shared CanonicalWork/InTr route handles exact request
-> retained governed INGRESS_ADMITTED transition
-> exact Canonical Work consumption/bootstrap evidence
-> governed post-ingress registry persistence
-> Master Records projection/reconciliation
-> WorkerCoordinator duplicate/adjacency/blocker review
-> WorkerCoordinator claim/fence if independently admitted
-> governed work
-> Master Records custody/reconstruction
-> post-execution reconciliation
-> Interlock/InTr egress / transfer / closure
-> admitted dependency-resolution event
-> dependent-task reevaluation
```

No step may infer authority from a preceding receipt. Every state change requires current applicable governance.

## Current boundary

The Runtime Profile Map task now has a non-authorizing Canonical Work resident request staged through the generalized path, and the consumer no longer risks overwriting a newer resident canonical registry while materializing source. No authentic task ingress is claimed until `receipts/sovereign-host/canonical-work-runtime-profile-map-request-consumption.latest.json` and nested task-specific ingress/consumption/bootstrap receipts are observed from the resident runtime.

No such governed request-consumption transition result is present in repository-observable source state at this handoff update.

## Remaining machine work

1. Existing resident dispatcher visits `canonical_work_coordination`; consumer visits all explicit Canonical Work request specs independently while preserving live resident task state.
2. Observe authentic task-specific request-consumption plus Canonical Work ingress/consumption/bootstrap receipts without inferring them from source/merge/CI/deployment/HB progression.
3. Govern resulting governed ingress projections into canonical task state.
4. Run Master Records pre-execution reconciliation and WorkerCoordinator admission review; project only retained WorkerCoordinator claim/fence transition closure.
5. Continue already-owned governed work paths without duplicate execution substrates.
6. Run post-execution Master Records reconciliation and governed egress/closure, then dependency fanout from retained admitted dependency transition events.
7. Prove a complete terminal canonical state-transition lineage.

## Human action

None currently required for this source/request work. Any later human/device evidence requirement remains task-specific and cannot be substituted by source or CI.

## Archive readiness

All unique continuation state is preserved here. This runtime workstream remains open until the canonical Goal reaches terminal state through retained governed transition closures.


## 2026-09-19 ACTIVE/CHECKED_OUT carriage repair

`STEGHEALTH-KV-INTERLOCK-PRODUCTION-ENDPOINT-001` is already `ACTIVE / CHECKED_OUT`, so PROPOSED-only registry selection could not carry it to Canonical Work and the shared bootstrap also rejected it. The repair stays inside the existing `canonical_work_coordination` selector and consumer: an exact non-authorizing request reaches the shared Canonical Work bootstrap; ACTIVE/CHECKED_OUT is accepted only when `INGRESS_ADMITTED` is explicitly allowed, no WorkerCoordinator claim/fence is projected, and the authority model remains intact. Runtime ingress is recorded as `runtime_refs.ingress_state=INGRESS_ADMITTED` without demoting canonical coordination state. Focused regression coverage is `tests/test_steghealth_kv_interlock_canonical_work_ingress.py`. No separate runtime-proof class is required. The next state changes only when the governed transition itself is retained by Master Records with the required closure predicates.


## 2026-09-21 StegHealth task-specific consumption-retention repair

Tracing the standing Healer `RT-CANONICAL-WORK-PORTABLE-DISPATCH-001` lineage exposed the first deterministic producer-path defect after source-materialization closure. `scripts/refresh_and_dispatch_resident_requests.py` previously accepted exact-selector `DISPATCH_COMPLETE` for `canonical_work_coordination` without requiring the current Goal's task-specific consumption receipt. Because `scripts/trigger_reusable_task.py` classifies a successful runner with no standardized result as `AUTOMATABLE_STEPS_EXHAUSTED`, and the neutral scheduler treats that state as a satisfied slot, the StegHealth schedule could stop retrying even when `canonical-work-steghealth-kv-interlock-production-endpoint-request-consumption.latest.json` was still absent.

The bounded repair keeps the existing path and authority model unchanged. For current Goal `STEGHEALTH-KV-INTERLOCK-PRODUCTION-ENDPOINT-001` only, portable dispatch now requires the retained receipt to:
- use schema `stegverse.canonical-work-bootstrap-request-consumption/v1`;
- identify the exact StegHealth Goal task;
- be `state=COMPLETED`;
- show no credential material and no network source fetch;
- match the same dispatch's `canonical_work_request_set.outcomes[]` entry by task ID, request SHA-256, and bootstrap receipt reference.

Until those predicates hold, the bridge returns `REFRESH_COMPLETE_DISPATCH_INCOMPLETE`, causing the existing reusable-task lifecycle to remain retryable rather than falsely satisfying the slot. This repair does not itself prove resident execution or create a WorkerCoordinator claim/fence, Interlock/InTr decision, or Master Records closure.
