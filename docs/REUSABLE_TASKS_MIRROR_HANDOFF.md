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
