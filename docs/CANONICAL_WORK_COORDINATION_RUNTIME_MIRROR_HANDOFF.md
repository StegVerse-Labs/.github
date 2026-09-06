# Canonical Work Coordination Runtime Mirror Handoff

Updated: 2026-09-05
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Status: `REGISTERED_TASK_INGRESS_SOURCE_GENERALIZED_AUTHENTIC_LIFECYCLE_PENDING`

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
- `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py`
- `scripts/dispatch_resident_execution_requests.py`
- `tests/test_canonical_work_registered_task_ingress.py`
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

The original coordination request remains staged at `control/resident-execution-request.d/canonical-work-coordination-bootstrap-001.json`. `QUANTUM-RESILIENCE-001` is additionally staged at `control/resident-execution-request.d/canonical-work-quantum-resilience-001.json`. Both use the same existing resident dispatcher selector `canonical_work_coordination` and the same `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py`; no second dispatch plane or ingress implementation is introduced.

That consumer deliberately resides inside `control/resident-execution-request.d`, which the existing sovereign source refresh already materializes wholesale. It copies only an explicit Canonical Work file manifest from the already-local canonical source root to the runtime checkout, verifies exact SHA-256 byte equality for every copy, and invokes the install-and-run wrapper with the exact task ID from its fixed request specification. Multiple explicit Canonical Work request specifications are visited independently so one task-local failure does not prevent a later request from being attempted. No network source fetch or credential use is allowed.

`scripts/consume_canonical_work_intr_materialization_request.py` requires the authentic ingress receipt, verifies payload hash and stable task/correlation identity, reads existing WorkerCoordinator state as projection only, and emits a non-authorizing coordination receipt.

`scripts/apply_admitted_canonical_work_projection.py` provides the guarded registry transition projection after authentic ingress. It refuses to advance a task unless the write-once CanonicalWork ingress receipt is `INGRESS_ADMITTED`, has the expected authority boundary, and is exactly bound to the canonical-work consumption receipt.

`scripts/project_worker_claim_into_canonical_task.py` provides guarded WorkerCoordinator ownership projection after admission. It resolves at most one existing WorkerCoordinator task identity and never creates or modifies WorkerCoordinator ownership.

`scripts/reconcile_admitted_canonical_work.py` binds authentic task ingress to explicit Master Records projection and existing WorkerCoordinator projection, returning only a non-authorizing disposition: reconciliation conflict, dependency blocked, existing-claim reuse/wait, or eligible for WorkerCoordinator admission review.

The Master Records authority-side projector scans configured retained custody roots and emits only explicit task/correlation identities and explicit predicates. Custody acceptance or reconstruction PASS is never silently converted into task completion.

`reevaluate_canonical_task_dependencies.py` implements deterministic dependency fanout proposals. `consume_admitted_dependency_resolution.py` requires an already admitted Interlock/InTr dependency-resolution event before invoking that fanout. Neither mutates WorkerCoordinator or HB/oscillator authority.

`normalize_github_failure_email_events.py` clusters explicit email observations into incident proposals; email count is not failure count and email state is not runtime proof.

## Registry state

`STEGVERSE-CANONICAL-WORK-COORDINATION-001` and `QUANTUM-RESILIENCE-001` remain `PROPOSED` unless and until authentic task-specific Interlock/InTr ingress receipts are observed and the resulting projections are governed into canonical task state. Source staging does not promote either task. Their next admissible governed transition remains `INGRESS_ADMITTED`.

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

The previous source-level restriction that allowed only `STEGVERSE-CANONICAL-WORK-COORDINATION-001` to use the bounded Canonical Work bootstrap has been removed. The reusable path now accepts only an explicitly registered, transition-eligible canonical task and still fails closed on identity, state, claim/fence, or authority drift.

`QUANTUM-RESILIENCE-001` now has a non-authorizing resident request staged through that path. This is source/request readiness only. No authentic quantum task ingress is claimed until `receipts/sovereign-host/canonical-work-quantum-resilience-request-consumption.latest.json` and its nested Canonical Work ingress/consumption/bootstrap receipts are observed from the resident runtime.

## Remaining machine work

1. Existing resident dispatcher visits selector `canonical_work_coordination` and the resident consumer visits both explicit Canonical Work request specs independently.
2. Observe authentic task-specific request-consumption plus Canonical Work ingress/consumption/bootstrap receipts; do not infer them from source or merge.
3. Apply each resulting authentic ingress projection to canonical task state through governed registry persistence.
4. Run Master Records pre-execution projection/reconciliation and WorkerCoordinator admission review; project any authentic claim/fence.
5. Run governed work only under the existing WorkerCoordinator/HB32 architecture.
6. Run post-execution Master Records reconciliation and governed egress/closure.
7. Invoke dependency fanout from authentic admitted dependency-resolution events.
8. Prove at least one complete authentic lifecycle through ingress, claim/fence, evidence, reconciliation, egress/closure, and dependent reevaluation.

## Human action

None currently required. All presently identified next steps are machine-owned resident/runtime work.

## Archive readiness

This runtime workstream is not complete until an authentic end-to-end lifecycle is proven. All unique continuation state is preserved here; the chat session may be archived without losing continuation context.
