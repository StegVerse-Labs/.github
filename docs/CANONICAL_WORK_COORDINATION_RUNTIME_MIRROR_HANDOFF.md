# Canonical Work Coordination Runtime Mirror Handoff

Updated: 2026-09-05
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Status: `REGISTERED_TASK_INGRESS_SOURCE_GENERALIZED_RUNTIME_PROFILE_MAP_REQUEST_STAGED_AUTHENTIC_LIFECYCLE_PENDING`

## Parent authority

Parent coordination handoff: `docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md`.
Canonical resident runtime/carrier authority: `control/canonical-resident-carrier-contract.json`.
This runtime lane MUST NOT create a second heartbeat, oscillator, scheduler, WorkerCoordinator, credential path, or execution authority.

## HB / oscillator binding

Canonical runtime reference is HB32 with `INDEPENDENT_PHASE_OSCILLATOR`, 100 Hz / 10 ms, `progression_dependency=OSCILLATOR_ONLY`.
HB and HB-derived InTr carriage are reference/transport observability only. They grant no admission, execution, claim/fence, routing, transition, receiving, or credential authority.
The task coordination runtime consumes that substrate; it does not own or advance it.

## Installed runtime-source surfaces

- `control/canonical-work-runtime-profile.json`
- `scripts/build_canonical_work_intr_request.py`
- `scripts/project_canonical_work_runtime.py`
- `scripts/validate_canonical_work_runtime_profile.py`
- `scripts/consume_canonical_work_intr_materialization_request.py`
- `workers/canonical_work_intr_ingress.py`
- `scripts/install_canonical_work_universal_intr_route.py`
- `tests/test_install_canonical_work_universal_intr_route.py`
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
- `data/canonical-task-registry.json`

Master Records corresponding bounded feed contract:

- `master-records/orchestration/CANONICAL_WORK_COORDINATION_CUSTODY_MIRROR_HANDOFF.md`
- `master-records/orchestration/schemas/canonical_work_event_projection.schema.json`
- `master-records/orchestration/scripts/project_canonical_work_events.py`
- `master-records/orchestration/tests/test_canonical_work_event_projection.py`

## Runtime-source behavior

`build_canonical_work_intr_request.py` emits the existing `stegverse.universal-intr-materialization-request/v1` shape and may bind the packet to the canonical HB-derived carrier profile. The result remains source material until authentic Interlock/InTr ingress admits it.

`workers/canonical_work_intr_ingress.py` is a reusable adapter for the existing Universal InTr listener. It starts no server, validates CanonicalWork destination/binding, writes a write-once `INGRESS_ADMITTED` receipt, preserves the non-authorizing HB carrier boundary, and dispatches only the canonical-work coordination consumer.

`scripts/install_canonical_work_universal_intr_route.py` is an idempotent fail-closed transformer for the existing `workers/universal_intr_profiled_ingress.py`. It adds the CanonicalWork adapter import, profile advertisement, and route only when expected router anchors match. Source installation cannot itself prove authentic ingress.

`scripts/run_canonical_work_event_bootstrap.py` provides a bounded executable ingress cycle using the existing shared `workers.universal_intr_profiled_ingress.Server` implementation. The selected **registered canonical task** must resolve exactly once in the canonical Task Registry, remain `PROPOSED`, explicitly allow `INGRESS_ADMITTED`, have no projected WorkerCoordinator claim/fence, and preserve the canonical authority model. The bootstrap refuses unregistered, duplicate, non-PROPOSED, already-claimed, or transition-ineligible task identities. It builds the request through the canonical builder, uses a loopback event-triggered one-request listener instance, posts exact bytes with InTr headers, waits for the write-once CanonicalWork consumption receipt, and generates a proposed post-ingress registry projection for that exact task. It does not create another listener implementation and explicitly records that it does not advance the HB oscillator or prove WorkerCoordinator claim/fence, Master Records reconciliation, governed work, egress, or closure.

`scripts/install_and_run_canonical_work_event_bootstrap.py` joins the route install/check and bounded bootstrap in one resident-machine sequence and forwards the explicit registered task identity to the bootstrap. It runs the bootstrap in a fresh Python process so the transformed shared router is imported after the route edit.

The staged requests now include the original coordination request, `QUANTUM-RESILIENCE-001`, `STEGVERSE-OBJECT-PROVENANCE-CONTINUITY-190`, and `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`. The Runtime Profile Map task is staged at `control/resident-execution-request.d/canonical-work-runtime-profile-map-001.json`, with expected consumption at `receipts/sovereign-host/canonical-work-runtime-profile-map-request-consumption.latest.json`. All four use the same existing resident dispatcher selector `canonical_work_coordination` and the same `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py`; no second dispatch plane or ingress implementation is introduced.

That consumer deliberately resides inside `control/resident-execution-request.d`, which the existing sovereign source refresh already materializes wholesale. It copies only an explicit Canonical Work file manifest from the already-local canonical source root to the runtime checkout, verifies exact SHA-256 byte equality for every copy, and invokes the install-and-run wrapper with the exact task ID from its fixed request specification. Multiple explicit Canonical Work request specifications are visited independently so one task-local failure does not prevent a later request from being attempted. No network source fetch or credential use is allowed.

The Runtime Profile Map request is a configuration-only extension of this already-generalized registered-task path. It does not alter the request schema, consumer behavior class, dispatcher selector, shared InTr listener, Task Registry authority, WorkerCoordinator authority, Master Records boundary, TV/TVC credential authority, GitHub-token boundary, or failure semantics. README impact is therefore `material_function_change=false`. The current `README.md` section **Canonical Work task ingress** already documents registered-task reuse, multiple explicit task request specifications, and the non-authorizing semantics. Evidence for the no-update determination is current `README.md`, this handoff, `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py`, and `tests/test_runtime_profile_map_canonical_work_resident_request.py`. If those generic semantics change later, README must change in the same change set.

The object-provenance request remains another non-authorizing configuration of the same generalized path; its earlier README no-update determination remains valid.

`scripts/consume_canonical_work_intr_materialization_request.py` requires the authentic ingress receipt, verifies payload hash and stable task/correlation identity, reads existing WorkerCoordinator state as projection only, and emits a non-authorizing coordination receipt.

`scripts/apply_admitted_canonical_work_projection.py` provides the guarded registry transition projection after authentic ingress. It refuses to advance a task unless the write-once CanonicalWork ingress receipt is `INGRESS_ADMITTED`, has the expected authority boundary, and is exactly bound to the canonical-work consumption receipt.

`scripts/project_worker_claim_into_canonical_task.py` provides guarded WorkerCoordinator ownership projection after admission. It resolves at most one existing WorkerCoordinator task identity and never creates or modifies WorkerCoordinator ownership.

`scripts/reconcile_admitted_canonical_work.py` binds authentic task ingress to explicit Master Records projection and existing WorkerCoordinator projection, returning only a non-authorizing disposition: reconciliation conflict, dependency blocked, existing-claim reuse/wait, or eligible for WorkerCoordinator admission review.

The Master Records authority-side projector scans configured retained custody roots and emits only explicit task/correlation identities and explicit predicates. Custody acceptance or reconstruction PASS is never silently converted into task completion.

`reevaluate_canonical_task_dependencies.py` implements deterministic dependency fanout proposals. `consume_admitted_dependency_resolution.py` requires an already admitted Interlock/InTr dependency-resolution event before invoking that fanout. Neither mutates WorkerCoordinator or HB/oscillator authority.

`normalize_github_failure_email_events.py` clusters explicit email observations into incident proposals; email count is not failure count and email state is not runtime proof.

## Registry state

`STEGVERSE-CANONICAL-WORK-COORDINATION-001`, `QUANTUM-RESILIENCE-001`, `STEGVERSE-OBJECT-PROVENANCE-CONTINUITY-190`, and `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001` remain `PROPOSED` unless and until authentic task-specific Interlock/InTr ingress receipts are observed and the resulting projections are governed into canonical task state. Source/request staging does not promote any task. Their next admissible governed transition remains `INGRESS_ADMITTED` where declared in the current registry.

For object provenance specifically, the already-merged StegOS source primitive, displayed-surface ingress adapter, and Master Records custody source are prerequisites/evidence only. They do not satisfy authentic object-provenance ingress, custody/reconstruction, reverse-source resolution, Workspace projection, or task closure.

For Runtime Profile Map specifically, its existing map-build/custody/reconciliation/readiness resident source remains non-authorizing. The new Canonical Work request supplies the previously missing explicit governed task-ingress staging for the task lifecycle; it does not replace or duplicate the Runtime Profile Map build consumers.

## Required authentic runtime sequence

```text
resident HB32/oscillator runtime dispatch cycle
-> dispatch_resident_execution_requests.py visits canonical_work_coordination
-> materialized control-directory consumer validates each exact REQUESTED object
-> consumer copies/verifies explicit Canonical Work source manifest from already-local source root
-> install_and_run_canonical_work_event_bootstrap.py --task-id <registered task>
-> fail-closed route transformer applies/checks CanonicalWork binding in existing shared router
-> canonical builder creates exact Universal InTr request
-> HB32-derived carrier binding (reference only)
-> existing shared Universal Interlock/InTr Server handles one event-triggered request
-> canonical_work_intr_ingress.admit(...)
-> authentic task-specific INGRESS_ADMITTED receipt
-> canonical-work consumer exact identity/payload verification
-> bounded bootstrap observes task-specific consumption receipt
-> apply_admitted_canonical_work_projection.py produces post-ingress task projection
-> Master Records authority-side work-event projection
-> reconcile_admitted_canonical_work.py pre-execution reconciliation
-> WorkerCoordinator duplicate/adjacency/blocker review
-> WorkerCoordinator claim/fence if admitted
-> project_worker_claim_into_canonical_task.py
-> governed work
-> Master Records evidence custody
-> authority-side post-execution projection + reconciliation
-> Interlock/InTr egress / transfer / closure
-> admitted dependency-resolution event
-> consume_admitted_dependency_resolution.py
-> dependent-task reevaluation
```

No step may infer authority from a preceding receipt. Every state change requires current applicable governance.

## Current boundary

The reusable path accepts only an explicitly registered, transition-eligible canonical task and fails closed on identity, state, claim/fence, or authority drift.

The Runtime Profile Map task now has a non-authorizing resident Canonical Work request staged through that same path. This closes a source/request gap only. No authentic task ingress is claimed until `receipts/sovereign-host/canonical-work-runtime-profile-map-request-consumption.latest.json` and its nested Canonical Work ingress/consumption/bootstrap receipts are observed from the resident runtime.

The quantum-resilience and object-provenance request stages remain source/request readiness only as well.

## Remaining machine work

1. Existing resident dispatcher visits selector `canonical_work_coordination` and the resident consumer visits all four explicit Canonical Work request specs independently.
2. Observe authentic task-specific request-consumption plus Canonical Work ingress/consumption/bootstrap receipts; do not infer them from source, merge, CI, deployment, or heartbeat progression.
3. Apply each resulting authentic ingress projection to canonical task state through governed registry persistence.
4. Run Master Records pre-execution projection/reconciliation and WorkerCoordinator admission review for admitted work; project any authentic existing/new claim/fence only from WorkerCoordinator evidence.
5. Continue each task's already-owned governed work path without creating duplicate execution substrates.
6. Run post-execution Master Records reconciliation and governed egress/closure.
7. Invoke dependency fanout from authentic admitted dependency-resolution events.
8. Prove at least one complete authentic lifecycle through ingress, claim/fence, evidence, reconciliation, egress/closure, and dependent reevaluation.

## Human action

None currently required for Canonical Work source/request staging. Any later user-device evidence requirement remains owned by the applicable task-specific handoff and cannot be replaced by source or CI.

## Archive readiness

All unique continuation state is preserved here. This runtime workstream remains open until authentic end-to-end lifecycle evidence is observed.
