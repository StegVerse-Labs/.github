# Task Registry Anti-Collision Aggregation Mirror Handoff

Goal Task ID: `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001`
Canonical issue: `StegVerse-Labs/.github#1343`
Historical implementation PR: `StegVerse-Labs/.github#1344`
Substrate-registration enforcement PR: `StegVerse-Labs/.github#1539`
Merged substrate-registration enforcement: `bbe00e1a1382ea8c98ae6441ff3b33f01dacc6d6`
Status: `ACTIVE / CHECKED_OUT / REGISTRY PREFLIGHT + PORTABLE PRECLAIM ENFORCED / NEW-TASK EXECUTION-SUBSTRATE SORTING MERGED_VALIDATED / SUBSTRATE-AWARE CHECKIN CONVERGENCE MERGED_VALIDATED / USER-ACTION-SURFACE COLLISION ENFORCEMENT REMAINS`

## Objective

Every task/session reaching the canonical Task Registry must receive a deterministic pre-mutation disposition from current canonical coordination state. New runtime-capable task registrations must also resolve execution-substrate dependencies before a reachability/evidence gap can be promoted into an external-device requirement.

Task Registry sorting is coordination only. WorkerCoordinator remains claim/fence authority; Interlock/InTr remains transition/admission authority; TV/TVC remains credential authority; Master Records remains observed-reality/reconstruction authority; HB remains observability only; GitHub runtime authority remains NONE.

## Canonical dispositions

- `CONTINUE`
- `COORDINATE_CONVERGENCE`
- `STOP_COLLISION`
- `STOP_SUPERSEDED`
- `STOP_INACTIVE`
- `STOP_NOT_REGISTERED`
- `STOP_SUBSTRATE_REVIEW_REQUIRED`

## Execution-substrate registration invariant

Every newly registered runtime-capable canonical task must review these substrates in this order:

1. `STEG-BROWSER-RETAINED-RESIDENT-NODE`
2. `STEGOS-CURRENT-DEVICE-NODE`
3. `STEG-BROWSER-EPHEMERAL-LEASE`
4. `SAME-DEVICE-SITE-SAFARI-SERVICE-WORKER`
5. `ADMITTED-EPHEMERAL-STEGOS-NODE`
6. `REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT`

The task record uses `execution_substrate_resolution` / `stegverse.execution-substrate-resolution/v1` and must preserve:

```text
second_user_operated_device_allowed=false
authority_effect=NONE
```

A review with `limitation_class=EVIDENCE_REACHABILITY` may be `PENDING_EVIDENCE`; it may not be `UNSUITABLE`. Therefore an empty Remote Computer inventory, unavailable connector, missing receipt, temporarily unreachable listener, or equivalent observation cannot itself become a hardware requirement.

`external_device_required=true` is valid only after every preceding single-device substrate is evidenced `UNSUITABLE` or `NOT_APPLICABLE`, and the external substrate is explicitly selected. Any `UNSUITABLE` determination requires evidence references.

## Merged implementation — PR #1539

Validated PR head:

`7e68c906381d97e7f4ebf9e86593c447caede414`

Squash merge:

`bbe00e1a1382ea8c98ae6441ff3b33f01dacc6d6`

Merged surfaces:

- `scripts/validate_task_registration_substrate_resolution.py`
- `scripts/validate_org_control_plane.py`
- `schemas/canonical-task-record.schema.json`
- `tests/test_task_registration_substrate_resolution.py`
- `scripts/evaluate_task_registry_collision_checkin.py`
- `tests/test_task_registry_collision_checkin.py`
- `.github/workflows/org-control-plane-validate.yml`

The organization-control workflow now triggers directly on `data/canonical-task-records/**`, so a task-record-only registration cannot bypass the substrate gate.

The registration validator inspects newly added canonical task records relative to the PR base. Legacy records remain readable; new runtime-capable registrations cannot omit substrate resolution.

The collision evaluator now:

- validates present `execution_substrate_resolution` before continuing;
- emits `STOP_SUBSTRATE_REVIEW_REQUIRED` on invalid substrate review;
- projects `selected_execution_substrate` into the check-in disposition;
- treats a shared selected substrate as a `COORDINATE_CONVERGENCE` signal;
- does not treat substrate sharing alone as a hard collision.

This lets multiple tasks converge on one eligible retained StegBrowser/StegOS resident rather than independently inventing listeners, activation pages, connector requirements, or second-device assumptions.

## Exact-head validation

All required exact-head lanes passed at `7e68c906381d97e7f4ebf9e86593c447caede414`:

- organization control: run `34667518970` — PASS;
- deterministic repository suite: run `34667519006` — PASS;
- Heartbeat validation: run `34667518973` — PASS.

Within organization control, step `Test task registration substrate sorting invariant` passed explicitly.

Regression coverage includes:

- retained StegBrowser resident selected first;
- runtime-capable registration without substrate review rejected;
- `EVIDENCE_REACHABILITY -> UNSUITABLE` rejected;
- premature external-device selection rejected;
- external-device selection accepted only after evidenced same-device exhaustion;
- legacy/non-runtime compatibility;
- substrate-aware check-in convergence without converting shared substrate into a hard collision.

## Existing collision enforcement

The pre-existing anti-collision implementation still provides:

- canonical task identity/supersession resolution;
- repository/component/lineage/adjacency overlap detection;
- recent check-in/check-out event-history participation;
- canonical Work preflight before mutation;
- portable WorkerCoordinator preclaim gating;
- hash-bound check-in context/disposition evidence;
- fail-closed non-`CONTINUE` portable checkout behavior.

## Remaining defect: user-action/runtime surface collisions

Issue #1343 records a remaining distinct gap: mutable human/browser action surfaces are not yet first-class collision resources. Multiple tasks were able to independently request the same current-iPhone URL/runtime surface because URL/browser/service-worker/action identity was not part of registry overlap sorting.

GADI/HIL exposed this defect. This remains owned by the same anti-collision goal; do not create a second collision engine.

Next implementation must add structured user-action surface identity to registration/check-in so the registry can detect overlap across at least:

- exact URL/route;
- current-device/browser context class;
- service-worker/runtime surface;
- action type;
- owning task/request identity;
- shareable vs exclusive semantics.

The registry must return `COORDINATE_CONVERGENCE` or `STOP_COLLISION` before user instruction when two tasks target an incompatible shared action surface.

## Canonical files

- `data/canonical-task-records/TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001.json`
- `scripts/evaluate_task_registry_collision_checkin.py`
- `scripts/validate_task_registration_substrate_resolution.py`
- `scripts/task_registry_checkin_event_history.py`
- `scripts/install_and_run_canonical_work_event_bootstrap.py`
- `workercoordinator/portable_checkout.js`
- `schemas/canonical-task-record.schema.json`
- `tests/test_task_registry_collision_checkin.py`
- `tests/test_task_registration_substrate_resolution.py`
- `tests/test_portable_workercoordinator_registry_gate.py`

## Manual work

None.
