# Task Registry Anti-Collision Aggregation Mirror Handoff

Goal Task ID: `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001`
Canonical issue: `StegVerse-Labs/.github#1343`
Historical implementation PR: `StegVerse-Labs/.github#1344`
Current continuation PR: `StegVerse-Labs/.github#1539`
Status: `ACTIVE / CHECKED_OUT / REGISTRY PREFLIGHT + PORTABLE PRECLAIM ENFORCED / USER-ACTION-SURFACE COLLISION DEFECT RECORDED / NEW-TASK EXECUTION-SUBSTRATE SORTING IMPLEMENTED / EXACT-HEAD VALIDATION PENDING`

## Objective

Every task/session reaching the canonical Task Registry must receive a deterministic pre-mutation disposition derived from current canonical task records, and no portable WorkerCoordinator claim may be minted unless that exact task has a current `CONTINUE` disposition.

Task registration must also resolve execution-substrate dependencies before downstream work can turn a reachability or evidence gap into a second-device requirement. The canonical preference is single-device sovereign capacity first.

## Required dispositions

- `CONTINUE` — no current collision candidate discovered.
- `COORDINATE_CONVERGENCE` — overlapping active work exists; coordinate before mutation.
- `STOP_COLLISION` — a currently checked-out task overlaps the same component or lineage strongly enough that this session should end and continue only through the returned collision owner/convergence path.
- `STOP_SUPERSEDED` — canonical task state is superseded/retired with a continuation task.
- `STOP_INACTIVE` — canonical task is inactive/retired without a continuation.
- `STOP_NOT_REGISTERED` — task is absent from canonical task records and must not mutate source until registered/reconciled.
- `STOP_SUBSTRATE_REVIEW_REQUIRED` — intended registration/check-in semantics for a runtime-capable task whose execution-substrate dependency review is absent or invalid. The current PR implements registration rejection before such a task may enter canonical state; check-in disposition projection remains a follow-on convergence step.

## Implemented protocol

1. `scripts/evaluate_task_registry_collision_checkin.py` resolves canonical task identity and all active/recently active collision candidates.
2. The evaluator accepts optional `checkin_context` containing `session_id`, `checked_in_at`, repository, branch, pull request, source head, first unresolved predicate, repositories-under-mutation, and components-under-mutation.
3. Intended mutation targets from that context participate in overlap calculation instead of relying only on static task-record scope.
4. The normalized check-in context and complete disposition are independently SHA-256 bound as `checkin_context_sha256` and `checkin_disposition_sha256`.
5. Canonical Work event bootstrap executes this preflight before route installation or bounded work mutation. Only `CONTINUE` proceeds.
6. Portable current-iPhone WorkerCoordinator checkout requires that same disposition as an explicit third input before it reads or mutates WorkerCoordinator state.
7. Portable checkout validates exact task identity, disposition schema, `authority_effect=NONE`, and `disposition=CONTINUE`; all other states fail closed before claim/fence mutation.
8. WorkerCoordinator claim receipts retain the exact registry disposition hash, preserving the ordering `Task Registry decision -> WorkerCoordinator claim/fence -> Interlock/InTr -> execution` for later reconstruction.
9. PR #1539 adds `execution_substrate_resolution` to canonical task-record semantics and runs a new-task registration gate from organization-control validation.
10. The registration gate validates only newly added canonical task records, preserving legacy readability while making the rule mandatory for new runtime-capable task registrations.

## Execution-substrate registration order

Every newly registered runtime-capable task must review, in order:

1. `STEG-BROWSER-RETAINED-RESIDENT-NODE`
2. `STEGOS-CURRENT-DEVICE-NODE`
3. `STEG-BROWSER-EPHEMERAL-LEASE`
4. `SAME-DEVICE-SITE-SAFARI-SERVICE-WORKER`
5. `ADMITTED-EPHEMERAL-STEGOS-NODE`
6. `REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT`

The record must preserve `second_user_operated_device_allowed=false` and `authority_effect=NONE`.

A substrate with `limitation_class=EVIDENCE_REACHABILITY` may be `PENDING_EVIDENCE`; it may not be classified `UNSUITABLE`. Therefore an empty Remote Computer inventory, missing receipt, temporarily unreachable listener, or similar observation cannot itself become a hardware requirement.

`external_device_required=true` is valid only after every prior single-device substrate is evidenced `UNSUITABLE` or `NOT_APPLICABLE`, and the external substrate is explicitly selected. Any `UNSUITABLE` determination requires evidence references.

## Current continuation implementation — PR #1539

Branch: `task-registry/substrate-resolution-ingress-001`

Current exact head: `68e0914ffe3efc1fa3fddad7b98c4da20a52390f`

Changed surfaces:

- `scripts/validate_task_registration_substrate_resolution.py`
- `scripts/validate_org_control_plane.py`
- `schemas/canonical-task-record.schema.json`
- `tests/test_task_registration_substrate_resolution.py`
- `.github/workflows/org-control-plane-validate.yml`

The workflow now triggers directly on `data/canonical-task-records/**`, so a task-record-only registration cannot bypass organization-control validation. The dedicated unittest covers:

- retained StegBrowser resident selection;
- missing resolution rejection;
- rejection of `EVIDENCE_REACHABILITY -> UNSUITABLE` promotion;
- rejection of premature external-device selection;
- acceptance of external-device selection only after evidenced same-device exhaustion;
- legacy/non-runtime compatibility.

As of this handoff update, PR #1539 is open and GitHub reports it mergeable, but exact-head workflow/status checks have not yet appeared. No validation or merge claim is made.

## Canonical files

- `data/canonical-task-records/TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001.json`
- `data/canonical-task-records/STEGOS-NODE-MANIFOLD-001.json`
- `scripts/evaluate_task_registry_collision_checkin.py`
- `scripts/validate_task_registration_substrate_resolution.py`
- `scripts/install_and_run_canonical_work_event_bootstrap.py`
- `workercoordinator/portable_checkout.js`
- `schemas/canonical-task-record.schema.json`
- `tests/test_task_registry_collision_checkin.py`
- `tests/test_task_registration_substrate_resolution.py`
- `tests/test_portable_workercoordinator_registry_gate.py`

## Prior validation evidence

Initial evaluator head `7b12ca062b463270c7b4564aad502e9a397ea3e8` passed repository suite `34544805866`, organization control `34544805762`, and Heartbeat validation `34544805873`.

Canonical Work ingress head `d7b36d6a6e850e2a423dac62ebf721ca871117fe` passed repository suite `34549352435`, organization control `34549352440`, and Heartbeat validation `34549352456`.

Portable preclaim head `888314d7fd4ed5e301fff360e32581dfb19b8f0f` passed repository suite `34553056822`, organization control `34553056856`, and Heartbeat validation `34553056820`.

Post-Node-Manifold-registration head `479b3e4f14ae85400b21ce35279a22001345aff7` passed repository suite `34553340082`, organization control `34553340116`, and Heartbeat validation `34553340079`.

These historical passes do not validate PR #1539.

## Node Manifold visibility repair

`STEGOS-NODE-MANIFOLD-001` is centrally represented in `.github` canonical task records. Its record points to StegOS issue #23 and the Node Manifold/service-KV handoffs, identifies shared StegOS/.github/Site/KV surfaces, and declares adjacency to global runtime, KV revalidation, Device/KV/SKAP roundtrip, KV-bound browser projection, and Ecosystem Chat work. The task therefore participates in collision aggregation instead of remaining invisible.

## User-action surface collision defect

Issue #1343 now also records that repository/component/lineage collision detection did not model mutable human/browser action surfaces. That allowed multiple tasks to independently request the same current-iPhone URL/runtime surface. GADI exposed the defect because its canonical record carried no actionable browser-surface reservation while HIL had task-specific browser/runtime state outside the same canonical comparison boundary.

This remains part of the same anti-collision owner. Do not create a second collision engine.

## Remaining integration

1. obtain exact-head validation for PR #1539;
2. repair only authentic failures found at that head;
3. merge #1539 only after required checks are green;
4. project the same substrate-resolution facts into check-in collision output so sessions receive an explicit `STOP_SUBSTRATE_REVIEW_REQUIRED` rather than discovering the registration defect later;
5. extend collision aggregation to structured user-action/browser surfaces so URL/runtime-surface contention is detected before user instruction;
6. keep execution-substrate identity available to convergence sorting so multiple tasks reuse one eligible retained StegBrowser/StegOS substrate instead of inventing duplicate listeners/pages/device requirements.

## Authority invariants

Task Registry sorting and registration evidence are coordination only. They grant no claim/fence, execution, credential, transition, custody, publication, release, or completion authority. WorkerCoordinator remains claim/fence authority; Interlock/InTr remains transition/admission authority; TV/TVC remains credential authority; Master Records remains observed-reality/reconstruction authority; HB remains observability only; GitHub runtime authority remains NONE.

## Manual work

None.
