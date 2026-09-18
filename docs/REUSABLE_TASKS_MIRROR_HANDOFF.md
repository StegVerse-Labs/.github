# Reusable Tasks Mirror Handoff

Status: ACTIVE_SOURCE_DEFINED
Repository: `StegVerse-Labs/.github`
Canonical reusable-task registry: `data/reusable-task-registry.json`
Canonical task registry: `data/canonical-task-registry.json`

## Purpose

`Reusable Tasks` are stable, reusable work definitions that may be referenced by many sessions or canonical work items without recreating the task specification each time.

They are coordination/discovery primitives only. A reusable task definition does **not** mint execution authority, a WorkerCoordinator claim/fence, Master Records truth, InTr admission, TV/TVC credential authority, or runtime activation.

## Canonical reusable tasks

- `RT-README-VALIDATION-001` — evaluate README impact for materially changed repositories; update in the same change set when required or record an evidence-supported `NO_README_CHANGE_REQUIRED` determination.
- `RT-MIRROR-HANDOFF-VALIDATION-001` — resolve and reconcile applicable `*_MIRROR_HANDOFF.md` files against current task/evidence state.
- `RT-STEGINDEX-VALIDATION-001` — verify materially affected StegIndex/index projections are accurate and not overclaimed.
- `RT-NATIVE-EMAIL-ACTION-MONITOR-001` — invoke the existing `STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001` / `RESIDENT-EXEC-NATIVE-EMAIL-ACTION-MONITOR-001` path without creating another monitor, scheduler, polling loop, heartbeat, worker, or credential route.
- `RT-CANONICAL-STATE-RECONCILIATION-001` — reconcile Task Registry, WorkerCoordinator claim/fence projection, Master Records, receipts, handoffs, README completeness determination, and StegIndex/index state without collapsing authority boundaries.
- `RT-SESSION-CLOSEOUT-001` — bounded composition of the five reusable tasks above before successor session handoff.
- `RT-INTR-PROTOCOL-ESTABLISH-001` — resolve or establish one normalized Interlock/InTr protocol without cloning provider-specific governance.
- `RT-INTR-BOUNDARY-ADMISSION-001` — validate one normalized ingress boundary, payload/envelope integrity, destination profile, and applicable standing before downstream transition.
- `RT-INTR-GOVERNED-TRANSITION-001` — evaluate one admitted transition through applicable Transition Elements while resolving authority effect separately from execution success.
- `RT-INTR-ROUNDTRIP-CORRELATION-001` — preserve exact request/response correlation, destination binding, replay/loop prevention, and transport-versus-application outcome separation.
- `RT-INTR-EVIDENCE-CUSTODY-001` — bind hash-linked Interlock/InTr evidence into canonical custody/reconstruction without promoting recording into transition authority.
- `RT-CANONICAL-WORK-PORTABLE-DISPATCH-001` — invoke the existing already-local source refresh + exact `canonical_work_coordination` portable bridge for one manifest-bound Goal Task without creating another runtime, scheduler, dispatcher, request identity, or authority plane.

The four reusable Interlock/InTr operational identities above were decomposed from the frozen `STEGVERSE-002-SELF-CHARACTERIZATION-001` v0.3 boundary semantics and are governed by `docs/INTR_REUSABLE_PROTOCOL_COMPONENTS_MIRROR_HANDOFF.md`. They compose existing transport-family components rather than duplicating implementation.

## Invocation semantics

A session or canonical task may reference a reusable task by `reusable_task_id` and bind it to the current repository/task/material scope. Invocation does not clone the reusable definition into a new implementation unless a distinct implementation is actually required.

Reusable-task execution must remain bounded to materially affected scope. `RT-SESSION-CLOSEOUT-001` must not recursively audit the entire ecosystem and must not become a prerequisite that blocks an otherwise admissible primary runtime transition.

## Authority separation

```text
Reusable Task Registry = reusable task definition/discovery
Canonical Task Registry = work intent / coordination
WorkerCoordinator = execution claim / fence
Master Records = observed reality / reconstruction
Interlock/InTr = governed ingress / egress
TV/TVC = credential authority
StegIndex = read/discovery projection
HB32 oscillator = reference/timing only
GitHub token runtime authority = NONE
```

## README completeness determination for this change

`NO_README_CHANGE_REQUIRED` for `StegVerse-Labs/.github` in this change set.

Evidence basis: the repository README already documents Canonical Work, the Reusable Task Component Model, and the Interlock/InTr transport family with separated downstream authority. This change adds reusable Interlock/InTr task identities and a dedicated handoff without changing runtime behavior, interfaces, credential authority, admission semantics, execution semantics, failure behavior, or capability authority.

## Next integration

StegIndex should index the new reusable Interlock/InTr task identities as discovery-only and point back to `docs/INTR_REUSABLE_PROTOCOL_COMPONENTS_MIRROR_HANDOFF.md` and the registry shards. The index must not assert runtime completion merely because reusable definitions exist.

## Portable Canonical Work reusable binding — 2026-09-17

The reusable-task trigger already provides the canonical one-trigger lifecycle and passes invocation parameters through `STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON`, while `scripts/refresh_and_dispatch_resident_requests.py` already provides the exact portable source-refresh -> resident-dispatch bridge. The missing seam was only an identity/binding between those two existing surfaces.

`RT-CANONICAL-WORK-PORTABLE-DISPATCH-001` therefore declares the existing bridge itself as its sole runner template. The bridge reads reusable parameters only when `STEGVERSE_REUSABLE_TASK_ID` exactly matches that identity; it requires `source_root`, `runtime_root`, `only_consumer=canonical_work_coordination`, and a non-empty `goal_task_id`, and rejects unknown fields or CLI/manifest disagreement. Ordinary CLI invocation retains its historical defaults and behavior.

The neutral reusable scheduler resolves child definitions from the already-local repository root supplied in its existing `repo_roots` mapping and injects `source_root` / `runtime_root` before calling `scripts/trigger_reusable_task.py`. Therefore no new scheduler, control-plane package, resident runtime, transport, or second-device dependency is required for this identity. This binding grants no authority: Task Registry remains coordination truth, WorkerCoordinator remains claim/fence authority, Interlock/InTr remains governed transition authority, TV/TVC remains credential authority, and Master Records remains observed-reality/reconstruction authority.

Source registration does not prove that a resident invocation occurred. The required runtime evidence remains the exact reusable/portable invocation reaching an authentic Task Registry `CONTINUE` disposition before WorkerCoordinator claim/fence and Interlock/InTr admission.


## Portable Canonical Work binding merge — 2026-09-17

PR #2092 merged `RT-CANONICAL-WORK-PORTABLE-DISPATCH-001` and its existing-bridge manifest binding as `c8ae6b6e83eb046319170d6a939f675f7d9ffd97` from exact head `0b8f0f540fdd76d5c4cffa68320f4315d11bf30f`. The merge creates no new runtime/scheduler/dispatcher implementation; the sole runner remains `scripts/refresh_and_dispatch_resident_requests.py`.

Exact-head PR validations passed, including Python compilation of the modified bridge. Authentic reusable/resident execution remains separately evidence-gated; no runtime completion, Task Registry `CONTINUE`, WorkerCoordinator claim/fence, or Interlock/InTr admission is inferred from the merge.
