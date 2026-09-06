# Canonical Work Coordination Runtime Mirror Handoff

Updated: 2026-09-05
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Status: `TASK_TARGETED_BOOTSTRAP_SOURCE_IMPLEMENTED_VALIDATION_PENDING`

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
- `tests/test_task_targeted_canonical_work_bootstrap.py`
- `control/resident-execution-request.d/canonical-work-coordination-bootstrap-001.json`
- `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py`
- `scripts/dispatch_resident_execution_requests.py`
- generation 15 of `data/canonical-task-registry.json`

Master Records corresponding bounded feed contract:

- `master-records/orchestration/CANONICAL_WORK_COORDINATION_CUSTODY_MIRROR_HANDOFF.md`
- `master-records/orchestration/schemas/canonical_work_event_projection.schema.json`
- `master-records/orchestration/scripts/project_canonical_work_events.py`
- `master-records/orchestration/tests/test_canonical_work_event_projection.py`

## Runtime-source behavior

`build_canonical_work_intr_request.py` emits the existing `stegverse.universal-intr-materialization-request/v1` shape and may bind the packet to the canonical HB-derived carrier profile. The result remains source material until authentic Interlock/InTr ingress admits it.

`workers/canonical_work_intr_ingress.py` is a reusable adapter for the existing Universal InTr listener. It starts no server, validates CanonicalWork destination/binding, writes a write-once `INGRESS_ADMITTED` receipt, preserves the non-authorizing HB carrier boundary, and dispatches only the canonical-work coordination consumer.

`scripts/install_canonical_work_universal_intr_route.py` is an idempotent fail-closed transformer for the existing `workers/universal_intr_profiled_ingress.py`. It adds the CanonicalWork adapter import, profile advertisement, and route only when expected router anchors match. Source installation cannot itself prove authentic ingress.

`scripts/run_canonical_work_event_bootstrap.py` provides a bounded executable ingress cycle using the existing shared `workers.universal_intr_profiled_ingress.Server` implementation. It refuses to run unless `CanonicalWork:Coordination` is actually installed in that shared router, builds the request through the canonical builder, uses a loopback event-triggered one-request listener instance, posts exact bytes with InTr headers, waits for the write-once CanonicalWork consumption receipt, and generates a proposed post-ingress registry projection. It does not create another listener implementation and explicitly records that it does not advance the HB oscillator or prove WorkerCoordinator claim/fence, Master Records reconciliation, governed work, egress, or closure.

The bootstrap now accepts an exact `--task-id` and resolves that task exactly once in the supplied canonical registry. It fails closed unless the selected task is `PROPOSED`, explicitly allows `INGRESS_ADMITTED`, preserves Task Registry / WorkerCoordinator / Master Records / Interlock-InTr authority separation, and has no pre-existing projected claim/fence that would require reconciliation first. Projection validation is bound to the selected task rather than the coordination-parent constant. The default remains `STEGVERSE-CANONICAL-WORK-COORDINATION-001`, and the historical parent receipt path is preserved for compatibility.

`scripts/install_and_run_canonical_work_event_bootstrap.py` forwards `--task-id` to the bounded bootstrap after applying/checking the existing shared route. This changes source capability from parent-task-only bootstrap to task-targeted CanonicalWork ingress without creating another listener, task registry, WorkerCoordinator, or transition authority.

`tests/test_task_targeted_canonical_work_bootstrap.py` verifies exact task resolution and fail-closed rejection for unknown/duplicate identity, non-PROPOSED state, disallowed ingress, pre-existing claim/fence, authority-model drift, wrapper task forwarding, and task-specific projection/receipt naming.

The canonical work parent request remains staged at `control/resident-execution-request.d/canonical-work-coordination-bootstrap-001.json`. The existing resident dispatcher registers selector `canonical_work_coordination` and points it to `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py`.

That existing parent consumer remains deliberately bounded to the coordination parent request. The new task-targeted bootstrap source does **not** by itself prove that a resident request for any newly registered task has been staged or consumed. A resident-targeting layer must reuse this generalized bootstrap rather than introducing another transport/listener/WorkerCoordinator.

`scripts/consume_canonical_work_intr_materialization_request.py` requires the authentic ingress receipt, verifies payload hash and stable task/correlation identity, reads existing WorkerCoordinator state as projection only, and emits a non-authorizing coordination receipt.

`scripts/apply_admitted_canonical_work_projection.py` provides the guarded registry transition projection after authentic ingress. It refuses to advance a task unless the write-once CanonicalWork ingress receipt is `INGRESS_ADMITTED`, has the expected authority boundary, and is exactly bound to the canonical-work consumption receipt.

`scripts/project_worker_claim_into_canonical_task.py` provides guarded WorkerCoordinator ownership projection after admission. It resolves at most one existing WorkerCoordinator task identity and never creates or modifies WorkerCoordinator ownership.

`scripts/reconcile_admitted_canonical_work.py` binds authentic task ingress to explicit Master Records projection and existing WorkerCoordinator projection, returning only a non-authorizing disposition: reconciliation conflict, dependency blocked, existing-claim reuse/wait, or eligible for WorkerCoordinator admission review.

The Master Records authority-side projector scans configured retained custody roots and emits only explicit task/correlation identities and explicit predicates. Custody acceptance or reconstruction PASS is never silently converted into task completion.

`reevaluate_canonical_task_dependencies.py` implements deterministic dependency fanout proposals. `consume_admitted_dependency_resolution.py` requires an already admitted Interlock/InTr dependency-resolution event before invoking that fanout. Neither mutates WorkerCoordinator or HB/oscillator authority.

`normalize_github_failure_email_events.py` clusters explicit email observations into incident proposals; email count is not failure count and email state is not runtime proof.

## README completeness preflight for task-targeted bootstrap

The change from a bootstrap hard-coded to the coordination parent task to a bootstrap that can target any exactly resolved eligible canonical task materially changes `.github` runtime/capability semantics. README impact is therefore **material**.

This change set updates `README.md` in the same branch with the task-targeted CanonicalWork ingress contract and authority boundaries. Evidence references are this handoff, the changed bootstrap/wrapper source, and the focused deterministic tests. README completeness is a preflight predicate only and grants no admission or execution authority.

## Registry state

`STEGVERSE-CANONICAL-WORK-COORDINATION-001` remains `PROPOSED` because no authentic Interlock/InTr task ingress receipt has yet been observed for it.

`STEGVERSE-OBJECT-PROVENANCE-CONTINUITY-190` is registered at generation 15 as `PROPOSED`. Its source dependencies for the canonical provenance primitive, displayed-surface ingress adapter, and Master Records custody support are resolved. No authentic CanonicalWork task ingress, WorkerCoordinator claim/fence, object-provenance runtime lineage, Master Records runtime custody/reconstruction, or Workspace projection is claimed.

The next admissible governed transition for either eligible PROPOSED task remains `INGRESS_ADMITTED` through the existing shared Interlock/InTr route.

## Required authentic runtime sequence

```text
resident HB32/oscillator runtime dispatch cycle
-> task-targeted CanonicalWork request is present under an existing resident consumer path
-> resident consumer validates exact target task/request
-> generalized install_and_run_canonical_work_event_bootstrap.py --task-id <exact task>
-> fail-closed route transformer applies/checks CanonicalWork binding in existing shared router
-> task-targeted canonical builder creates exact Universal InTr request
-> HB32-derived carrier binding (reference only)
-> existing shared Universal Interlock/InTr Server handles one event-triggered request
-> canonical_work_intr_ingress.admit(...)
-> authentic INGRESS_ADMITTED receipt
-> canonical-work consumer exact identity/payload verification
-> bounded bootstrap observes consumption receipt
-> apply_admitted_canonical_work_projection.py produces selected-task post-ingress projection
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

The source bootstrap itself is no longer structurally limited to one canonical task identity. It can target an exactly resolved eligible canonical task while preserving the shared router and authority boundaries.

The next source/runtime boundary is resident request targeting: the currently staged resident CanonicalWork request/consumer is still parent-task-specific. For `STEGVERSE-OBJECT-PROVENANCE-CONTINUITY-190`, a bounded resident request must invoke the generalized bootstrap with that exact task ID through the existing dispatcher/materialization architecture. That addition must not create another listener, scheduler, WorkerCoordinator, task registry, or provenance authority.

Even after that request source exists, runtime completion remains strictly dependent on authentic resident consumption and write-once CanonicalWork ingress/consumption receipts. Source or CI validation must not change the registry from `PROPOSED`.

## Remaining machine work

1. Validate and merge the task-targeted bootstrap/wrapper/README/tests in this change set.
2. Reuse the existing resident request/materialization architecture to stage `STEGVERSE-OBJECT-PROVENANCE-CONTINUITY-190` as an exact target for the generalized bootstrap, without duplicating transport or worker authority.
3. Existing resident dispatcher consumes that exact request and emits request-consumption plus CanonicalWork ingress/consumption/bootstrap receipts.
4. Apply the resulting authentic ingress projection to canonical task state through governed registry persistence.
5. Run Master Records pre-execution projection/reconciliation and WorkerCoordinator admission review; project any authentic claim/fence.
6. Run governed object-provenance work only under the existing WorkerCoordinator/HB32 architecture.
7. Run post-execution Master Records reconciliation and governed egress/closure.
8. Invoke dependency fanout from authentic admitted dependency-resolution events.
9. Prove one complete authentic lifecycle through ingress, claim/fence, evidence, reconciliation, egress/closure, and dependent reevaluation.

## Human action

None currently required for this source lane. Authentic user-device object capture is a later runtime evidence event under the StegOS #190 handoff; it is not evidence that may be fabricated from source or CI.

## Archive readiness

This runtime workstream is not complete until an authentic end-to-end lifecycle is proven. The task-targeted bootstrap source does not make the thread archive-ready by itself.
