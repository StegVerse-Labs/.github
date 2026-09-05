# Canonical Work Coordination Runtime Mirror Handoff

Updated: 2026-09-04
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Status: `RUNTIME_BOOTSTRAP_SOURCE_INSTALLED_AUTHENTIC_LIFECYCLE_PENDING`

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
- generation 6 of `data/canonical-task-registry.json`

Master Records corresponding bounded feed contract:

- `master-records/orchestration/CANONICAL_WORK_COORDINATION_CUSTODY_MIRROR_HANDOFF.md`
- `master-records/orchestration/schemas/canonical_work_event_projection.schema.json`
- `master-records/orchestration/scripts/project_canonical_work_events.py`
- `master-records/orchestration/tests/test_canonical_work_event_projection.py`

## Runtime-source behavior

`build_canonical_work_intr_request.py` emits the existing `stegverse.universal-intr-materialization-request/v1` shape and may bind the packet to the canonical HB-derived carrier profile. The result remains source material until authentic Interlock/InTr ingress admits it.

`workers/canonical_work_intr_ingress.py` is a reusable adapter for the existing Universal InTr listener. It starts no server, validates CanonicalWork destination/binding, writes a write-once `INGRESS_ADMITTED` receipt, preserves the non-authorizing HB carrier boundary, and dispatches only the canonical-work coordination consumer.

`scripts/install_canonical_work_universal_intr_route.py` is an idempotent fail-closed transformer for the existing `workers/universal_intr_profiled_ingress.py`. It adds the CanonicalWork adapter import, profile advertisement, and route only when expected router anchors match. Source installation cannot itself prove authentic ingress.

`scripts/run_canonical_work_event_bootstrap.py` now provides a bounded executable ingress cycle using the existing shared `workers.universal_intr_profiled_ingress.Server` implementation. It refuses to run unless `CanonicalWork:Coordination` is actually installed in that shared router, builds the request through the canonical builder, uses a loopback event-triggered one-request listener instance, posts exact bytes with InTr headers, waits for the write-once CanonicalWork consumption receipt, and generates a proposed post-ingress registry projection. It does not create another listener implementation and explicitly records that it does not advance the HB oscillator or prove WorkerCoordinator claim/fence, Master Records reconciliation, governed work, egress, or closure.

`scripts/install_and_run_canonical_work_event_bootstrap.py` now joins the previously separate machine steps for an admitted resident checkout: apply the fail-closed shared-router source transformation, verify it, then launch the bounded bootstrap in a fresh Python process so the transformed router is imported. This removes the need for a human to manually edit or sequence the route installation and first ingress test. Its output is still only authentic evidence when the resident process actually executes and emits the bounded receipts.

`scripts/consume_canonical_work_intr_materialization_request.py` requires the authentic ingress receipt, verifies payload hash and stable task/correlation identity, reads existing WorkerCoordinator state as projection only, and emits a non-authorizing coordination receipt.

`scripts/apply_admitted_canonical_work_projection.py` provides the guarded registry transition projection after authentic ingress. It refuses to advance a task unless the write-once CanonicalWork ingress receipt is `INGRESS_ADMITTED`, has the expected authority boundary, and is exactly bound to the canonical-work consumption receipt. It can then project `INGRESS_ADMITTED` plus receipt references into the registry without minting execution or claim/fence authority.

`scripts/project_worker_claim_into_canonical_task.py` provides guarded WorkerCoordinator ownership projection after admission. It resolves at most one existing WorkerCoordinator task identity, copies existing claim/fence/worker references into the canonical task, and never creates or modifies WorkerCoordinator ownership.

`scripts/reconcile_admitted_canonical_work.py` binds authentic task ingress to explicit Master Records projection and existing WorkerCoordinator projection, returning only a non-authorizing disposition: reconciliation conflict, dependency blocked, existing-claim reuse/wait, or eligible for WorkerCoordinator admission review.

The Master Records authority-side projector scans configured retained custody roots and emits only explicit task/correlation identities and explicit predicates. Custody acceptance or reconstruction PASS is never silently converted into task completion.

`reevaluate_canonical_task_dependencies.py` implements deterministic dependency fanout proposals. `consume_admitted_dependency_resolution.py` requires an already admitted Interlock/InTr dependency-resolution event before invoking that fanout. Neither mutates WorkerCoordinator or HB/oscillator authority.

`normalize_github_failure_email_events.py` clusters explicit email observations into incident proposals; email count is not failure count and email state is not runtime proof.

## Registry state

`STEGVERSE-CANONICAL-WORK-COORDINATION-001` remains `PROPOSED` because no authentic Interlock/InTr task ingress receipt has yet been observed. Generation 6 records installed source/runtime-bootstrap machinery only. The next admissible governed transition remains `INGRESS_ADMITTED`.

## Required authentic runtime sequence

```text
canonical task proposal
-> admitted resident checkout invokes install_and_run_canonical_work_event_bootstrap.py
-> fail-closed route transformer applies/checks CanonicalWork binding in existing shared router
-> canonical builder creates exact Universal InTr request
-> HB32-derived carrier binding (reference only)
-> existing shared Universal Interlock/InTr Server handles one event-triggered request
-> canonical_work_intr_ingress.admit(...)
-> authentic INGRESS_ADMITTED receipt
-> canonical-work consumer exact identity/payload verification
-> bounded bootstrap observes consumption receipt
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

The connected GitHub surface permits repository source writes but does not execute repository-local Python. The current committed shared router source was re-read before this update and still lacked the CanonicalWork route/profile binding. That no longer requires a human edit: the new install-and-run wrapper performs the fail-closed source transformation and immediately runs the bounded ingress bootstrap in a fresh process when executed by the admitted resident runtime.

Therefore the highest-priority unresolved boundary is now actual resident execution of that wrapper in the canonical HB32/oscillator environment. Until its authentic ingress and consumption receipts exist, the registry MUST remain `PROPOSED` and no WorkerCoordinator claim/fence or runtime completion may be inferred.

## Remaining machine work

1. Execute `scripts/install_and_run_canonical_work_event_bootstrap.py` in the admitted resident checkout under the existing HB32/oscillator runtime and retain its authentic ingress/consumption/bootstrap receipts.
2. Apply the resulting authentic ingress projection to the canonical task state through governed registry persistence.
3. Run Master Records pre-execution projection/reconciliation and WorkerCoordinator admission review; project any authentic claim/fence through `project_worker_claim_into_canonical_task.py`.
4. Run governed work only under the existing WorkerCoordinator/HB32 architecture.
5. Run post-execution Master Records reconciliation and governed egress/closure.
6. Invoke dependency fanout from authentic admitted dependency-resolution events.
7. Feed explicit email-monitor observations into failure clustering and admit resulting incident proposals through canonical task ingress.
8. Prove one complete authentic lifecycle through ingress, claim/fence, evidence, reconciliation, egress/closure, and dependent reevaluation.

## Human action

None currently required. All presently identified next steps are machine-owned resident/runtime integration work.

## Archive readiness

This runtime workstream is not complete until an authentic end-to-end lifecycle is proven. All unique continuation state is preserved here; the chat session may be archived without losing continuation context.
