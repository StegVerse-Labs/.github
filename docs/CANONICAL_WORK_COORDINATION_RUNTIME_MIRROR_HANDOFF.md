# Canonical Work Coordination Runtime Mirror Handoff

Updated: 2026-09-04
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Status: `RUNTIME_SOURCE_COORDINATION_ADAPTERS_INSTALLED_ROUTER_AND_AUTHENTIC_LIFECYCLE_PENDING`

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
- generation 3 of `data/canonical-task-registry.json`

Master Records now has a corresponding bounded feed contract:

- `master-records/orchestration/CANONICAL_WORK_COORDINATION_CUSTODY_MIRROR_HANDOFF.md`
- `master-records/orchestration/schemas/canonical_work_event_projection.schema.json`
- `master-records/orchestration/scripts/project_canonical_work_events.py`
- `master-records/orchestration/tests/test_canonical_work_event_projection.py`

`build_canonical_work_intr_request.py` emits the existing `stegverse.universal-intr-materialization-request/v1` shape rather than creating a parallel transport protocol. It writes the exact canonical task-transition payload separately, hashes it, and may bind the packet to the canonical HB-derived carrier profile. The result remains source material until authentic Interlock/InTr ingress admits it.

`workers/canonical_work_intr_ingress.py` is a reusable admission adapter for the existing Universal InTr listener. It intentionally starts no server. It validates the CanonicalWork destination, writes a write-once `INGRESS_ADMITTED` receipt, preserves the non-authorizing HB carrier boundary, and dispatches only the canonical-work coordination consumer.

`scripts/install_canonical_work_universal_intr_route.py` is an idempotent fail-closed source transformer for the existing `workers/universal_intr_profiled_ingress.py`. It adds the CanonicalWork adapter import, profile advertisement, and route only if the expected current router anchors match. It does not start or define another listener and cannot prove runtime ingress merely by modifying source.

`scripts/consume_canonical_work_intr_materialization_request.py` requires the authentic ingress receipt before it will consume the request. It verifies the payload hash and stable task/correlation identity, reads existing WorkerCoordinator state as projection only, and emits a non-authorizing coordination receipt. It does not execute the task, create a claim/fence, or start another scheduler/runtime.

`project_canonical_work_runtime.py` projects canonical task state against the existing `control/worker-registry.json` and a current HB32 oscillator reference. It never mints WorkerCoordinator claim/fence state and never treats the heartbeat reference as authority.

The Master Records bounded feed contract now provides the authority-side projection source. `master-records/orchestration/scripts/project_canonical_work_events.py` scans configured retained custody roots including state-alignment, worker-lifecycle, lineage, and heartbeat-worker coordination. It emits only explicit task/correlation identities and explicit predicates. Existing `task_effects[]` custody such as `ALIGN-UNIFIED-CONVERSATION-TASK-PROJECTION-001.custody.json` is supported without converting custody acceptance or reconstruction PASS into inferred task completion.

`project_master_records_work_events.py` remains the .github-side adapter for explicitly supplied Master Records projection inputs. The Master Records authority-side projector output uses an `events[]` form directly consumable by `scripts/reconcile_task_registry_master_records.py`.

`reevaluate_canonical_task_dependencies.py` implements deterministic dependency fanout at source level. A dependency state change identifies every dependent task, removes/adds corresponding blocker projections, and exposes next transition candidates only when prerequisites are resolved. Its output is a proposal and never admits a task transition or WorkerCoordinator claim/fence.

`normalize_github_failure_email_events.py` implements deterministic failure-email clustering by normalized repository/workflow/error signature. Email observations become incident proposals only; message count is not failure count, email state is not runtime proof, and every proposed incident still requires canonical task ingress before work.

`validate_canonical_work_runtime_profile.py` statically checks the runtime profile against `control/canonical-resident-carrier-contract.json`, the task coordination policy, canonical registry, and existing WorkerCoordinator registry.

## Registry state

`STEGVERSE-CANONICAL-WORK-COORDINATION-001` remains `PROPOSED` because no authentic Interlock/InTr task ingress receipt has yet been observed. Generation 3 records the installed source adapters without promoting runtime state.

The next admissible governed transition remains `INGRESS_ADMITTED`.

## Required authentic runtime sequence

```text
canonical task proposal
-> build exact Universal InTr transition payload/request
-> HB32-derived carrier binding (reference only; optional while migration profile allows)
-> existing canonical Universal Interlock/InTr listener
-> canonical_work_intr_ingress.admit(...)
-> ingress receipt / materialization
-> canonical task state transition to INGRESS_ADMITTED
-> canonical-work consumer verifies exact payload + identity
-> Master Records authority-side work-event projection + pre-execution reconciliation
-> WorkerCoordinator duplicate/adjacency/blocker review
-> WorkerCoordinator claim/fence if execution is admitted
-> governed work
-> Master Records evidence custody
-> authority-side projection + post-execution reconciliation
-> Interlock/InTr egress / transfer / closure
-> dependency fanout reevaluates all affected tasks
```

No step may infer authority from the preceding receipt. Every state change requires current applicable governance.

## Execution attempt note

A prior local source-validation attempt from the ChatGPT execution environment could not clone GitHub because that container had no external DNS/network access. That failure is not a StegVerse runtime failure and is not evidence about resident execution. Repository source writes were completed through the connected GitHub authority surface. Static validator execution remains pending in an admitted execution environment.

## Remaining machine work

1. Apply the installed fail-closed route transformer to `workers/universal_intr_profiled_ingress.py`, validate the resulting shared-router source, and keep the existing single ingress listener.
2. Persist authentic ingress receipt/materialization references into the canonical task projection after the shared router admits a real request.
3. Project live WorkerCoordinator claim/fence state after admission and after every ownership transition.
4. Execute the installed Master Records authority-side projector against retained custody and consume its current output in pre/post-execution reconciliation.
5. Connect dependency fanout to admitted dependency-resolution events so affected tasks are reevaluated automatically rather than by manual invocation.
6. Feed explicit email-monitor observations to the installed GitHub failure-email normalizer and admit normalized incident proposals through canonical task ingress rather than treating emails as execution evidence.
7. Prove one authentic end-to-end lifecycle through ingress, claim/fence, evidence, reconciliation, egress, closure, and dependent-task reevaluation.

## Human action

None currently required. All presently identified next steps are machine-owned integration/runtime work.

## Archive readiness

This runtime workstream is not complete until an authentic end-to-end lifecycle is proven. All unique runtime-source continuation state from this session is preserved here, so the chat session itself may be archived without losing continuation context.
