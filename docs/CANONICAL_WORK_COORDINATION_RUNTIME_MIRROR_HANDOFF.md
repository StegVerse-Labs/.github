# Canonical Work Coordination Runtime Mirror Handoff

Updated: 2026-09-04
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Status: `RUNTIME_SOURCE_COORDINATION_ADAPTERS_INSTALLED_AUTHENTIC_LIFECYCLE_PENDING`

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
- generation 5 of `data/canonical-task-registry.json`

Master Records corresponding bounded feed contract:

- `master-records/orchestration/CANONICAL_WORK_COORDINATION_CUSTODY_MIRROR_HANDOFF.md`
- `master-records/orchestration/schemas/canonical_work_event_projection.schema.json`
- `master-records/orchestration/scripts/project_canonical_work_events.py`
- `master-records/orchestration/tests/test_canonical_work_event_projection.py`

## Runtime-source behavior

`build_canonical_work_intr_request.py` emits the existing `stegverse.universal-intr-materialization-request/v1` shape and may bind the packet to the canonical HB-derived carrier profile. The result remains source material until authentic Interlock/InTr ingress admits it.

`workers/canonical_work_intr_ingress.py` is a reusable adapter for the existing Universal InTr listener. It starts no server, validates CanonicalWork destination/binding, writes a write-once `INGRESS_ADMITTED` receipt, preserves the non-authorizing HB carrier boundary, and dispatches only the canonical-work coordination consumer.

`scripts/install_canonical_work_universal_intr_route.py` is an idempotent fail-closed transformer for the existing `workers/universal_intr_profiled_ingress.py`. It adds the CanonicalWork adapter import, profile advertisement, and route only when expected router anchors match. Source installation cannot itself prove authentic ingress.

`scripts/consume_canonical_work_intr_materialization_request.py` requires the authentic ingress receipt, verifies payload hash and stable task/correlation identity, reads existing WorkerCoordinator state as projection only, and emits a non-authorizing coordination receipt.

`scripts/apply_admitted_canonical_work_projection.py` now provides the guarded registry transition projection after authentic ingress. It refuses to advance a task unless the write-once CanonicalWork ingress receipt is `INGRESS_ADMITTED`, has the expected authority boundary, and is exactly bound to the canonical-work consumption receipt. It can then project `INGRESS_ADMITTED` plus receipt references into the registry without minting execution or claim/fence authority.

`scripts/project_worker_claim_into_canonical_task.py` now provides guarded WorkerCoordinator ownership projection after admission. It resolves at most one existing WorkerCoordinator task identity, copies existing claim/fence/worker references into the canonical task, and never creates or modifies WorkerCoordinator ownership.

`scripts/reconcile_admitted_canonical_work.py` binds authentic task ingress to explicit Master Records projection and existing WorkerCoordinator projection, returning only a non-authorizing disposition: reconciliation conflict, dependency blocked, existing-claim reuse/wait, or eligible for WorkerCoordinator admission review.

The Master Records authority-side projector scans configured retained custody roots and emits only explicit task/correlation identities and explicit predicates. Custody acceptance or reconstruction PASS is never silently converted into task completion.

`reevaluate_canonical_task_dependencies.py` implements deterministic dependency fanout proposals. `consume_admitted_dependency_resolution.py` requires an already admitted Interlock/InTr dependency-resolution event before invoking that fanout. Neither mutates WorkerCoordinator or HB/oscillator authority.

`normalize_github_failure_email_events.py` clusters explicit email observations into incident proposals; email count is not failure count and email state is not runtime proof.

## Registry state

`STEGVERSE-CANONICAL-WORK-COORDINATION-001` remains `PROPOSED` because no authentic Interlock/InTr task ingress receipt has yet been observed. Generation 5 records installed source adapters only. The next admissible governed transition remains `INGRESS_ADMITTED`.

## Required authentic runtime sequence

```text
canonical task proposal
-> build exact Universal InTr transition payload/request
-> HB32-derived carrier binding (reference only)
-> existing shared Universal Interlock/InTr listener
-> canonical_work_intr_ingress.admit(...)
-> authentic INGRESS_ADMITTED receipt
-> canonical-work consumer exact identity/payload verification
-> apply_admitted_canonical_work_projection.py
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

The highest-priority remaining source integration is still the shared-router edit: apply the installed fail-closed CanonicalWork route transformer to `workers/universal_intr_profiled_ingress.py` while preserving the existing single listener. The current router source has been re-read and still lacks the CanonicalWork route/profile binding. Authentic runtime admission cannot occur through that shared listener until this binding is present.

The connected GitHub interface permits direct repository writes but does not execute repository-local Python. Therefore no claim is made that the route transformer, validators, Master Records projector, or resident runtime have executed merely because their source is present.

## Remaining machine work

1. Apply and validate the CanonicalWork route binding in the existing shared Universal InTr router.
2. Admit one authentic CanonicalWork request and persist its ingress/consumption references through `apply_admitted_canonical_work_projection.py`.
3. Run pre-execution Master Records reconciliation and WorkerCoordinator admission review; then project any authentic claim/fence through `project_worker_claim_into_canonical_task.py`.
4. Run governed work only under the existing WorkerCoordinator/HB32 architecture.
5. Run post-execution Master Records reconciliation and governed egress/closure.
6. Invoke dependency fanout from authentic admitted dependency-resolution events.
7. Feed explicit email-monitor observations into failure clustering and admit resulting incident proposals through canonical task ingress.
8. Prove one complete authentic lifecycle through ingress, claim/fence, evidence, reconciliation, egress/closure, and dependent reevaluation.

## Human action

None currently required. All presently identified next steps are machine-owned integration/runtime work.

## Archive readiness

This runtime workstream is not complete until an authentic end-to-end lifecycle is proven. All unique continuation state is preserved here; the chat session may be archived without losing continuation context.
