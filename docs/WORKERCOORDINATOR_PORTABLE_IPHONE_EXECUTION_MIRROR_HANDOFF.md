# Portable WorkerCoordinator iPhone Execution Mirror Handoff

Updated: 2026-09-04
Repository: `StegVerse-Labs/.github`
Issue: #862
Goal: `WORKERCOORDINATOR-PORTABLE-IPHONE-EXECUTION-001`

Parent contracts:
- `docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md`
- `docs/WORKER_TASK_ADMISSION_PACKET_MIRROR_HANDOFF.md`
- `docs/STEGVERSE_001_BOUNDED_AUTONOMY_RUNTIME_MIRROR_HANDOFF.md`

## Purpose

Remove execution-surface coupling from the existing canonical WorkerCoordinator claim/fence transaction. This does **not** create a second WorkerCoordinator and does not promote StegOS device-local task fencing into canonical WorkerCoordinator authority.

Canonical identity:

```text
authority owner: StegVerse-Labs/.github WorkerCoordinator
authority domain: INDEPENDENT_TASK_CONTROL
credential authority: TV/TVC
portable execution surface: CURRENT_USER_IPHONE
StegOS role: atomic persistence + bounded subordinate execution adapter
HB authority effect: NONE
GitHub runtime authority: NONE
second user-operated device required: false
always-on external host required: false
```

## Portable transaction

```text
canonical static task package
+ executable handoff
+ source/semantic state binding
+ worker capability binding
+ current portable WorkerCoordinator state
-> same independent-task-control admission invariants
-> atomic compare-and-set canonical WC generation
-> fresh generation/fencing token
-> deterministic SHWP-<task>-G<generation> claim
-> portable WorkerCoordinator checkout receipt
-> subordinate StegOS externally-admitted task envelope
```

The portable transaction is the same WorkerCoordinator authority expressed on another execution surface. It is not `stegos.device_task_claim.v1` and must never consume or reinterpret StegOS's device-local generation as the WorkerCoordinator generation.

## Fail-closed invariants

A portable checkout MUST reject task state other than `HANDOFF_READY`, pre-existing task worker/claim binding, authority-domain or claim-state drift, missing fresh-fence requirement, HB authority claims, incomplete dependencies, unauthorized handoff execution, stale source/state, unresolved worker binding, non-TV/TVC credential authority, GitHub runtime authority, stale/reused claims/fences, or non-atomic persistence.

## State model

Portable canonical state is `stegverse.workercoordinator-portable-state/v1`. The persisted state contains canonical WorkerCoordinator generation and a hash-linked checkout tail. It grants no authority merely by existing. The namespace remains distinct from StegOS `device-task-control-generation`.

## First consumer

`SHWP-STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001`.

Portable WorkerCoordinator checkout does not satisfy the TVC lease predicate. TVC issuance/validation remains separate.

## Duplicate-terminal prevention — 2026-09-03

Issue #944 added a per-portable-state `checkout_count` guard after the valid canonical G23 cycle was followed by duplicate G24. G24 remains retained as duplicate/non-custodial evidence. Canonical first-terminal G23 remains custody source. Downstream retry remains permitted; terminal task re-execution does not.

## Reset-lineage terminal propagation — 2026-09-04

Fresh authentic CURRENT_USER_IPHONE evidence exposed the remaining hole in #944: the local checkout counter does not survive a newly established portable state lineage. A new StegOS web node could see the still-published G22 preclaim package and mint another G23.

Observed reset-lineage duplicate:

```text
node: stegnode-web-2d6daa94e496d451d16bd5619bd30a25
claim/fence: G23 / 23
checkout receipt: sha256:8ef913db2cc4b79fb8b4d78deef9160efd98eacac0a8f2ba8d1fd58433c2223d
TVC lease: SV001-LEASE-d63af357d4b7245e39a284ae
cycle receipt: sha256:7b66f6cf260a46fcb8555d207cd868eaf2d31aa67372f0701841f91c648d00d4
transition: SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED
same-execution reconstruction: PASS
TVC lease consumption: CONSUMED
```

This execution is authentic, but duplicate/non-custodial because the first terminal G23 already closed the task contract. Canonical custody remains `sha256:81a078eeeacffb8fc86d287d7aaa8a9904c6f53973471dad7f6d7c3fa6818a35` from node `stegnode-web-f24e3bfb7f5343cb37323187a88e51f3`.

Issue #976 moves terminality into the canonical package itself:

```text
task.state = COMPLETED
claim_state = TERMINAL_NO_FURTHER_CLAIM
fresh_fence_required = false
execution_authorized = false
authority_effect = CANONICAL_WORKERCOORDINATOR_PORTABLE_TERMINAL_PACKAGE
```

Because `portable_checkout.js` already rejects any task that is not clean `HANDOFF_READY` before local state initialization, a fresh node receiving this terminal package cannot recreate G23 from the G22 predecessor floor.

The package retains canonical first-terminal G23 plus both known duplicate terminal receipts (G24 and reset-lineage G23), with only the first G23 custody-eligible. Master Records custody and SV002 disposition remain PENDING and must continue from the first canonical G23 without another SV001 execution.

This is terminal-state propagation, not a second runtime authority. WorkerCoordinator remains claim/fence authority, TV/TVC remains credential authority, HB grants no authority, GitHub runtime authority is NONE, and no other machine is required.

## Current-base validation reconciliation — 2026-09-04

The first #977 merge-ref was based before an independent AE/COSV denominator reconciliation and therefore failed on the already-installed `LEGACY-CONTINUITY-VALIDATION-WORKER-001`. Current main now reports 83 unique worker task IDs, 76 canonically indexed worker task IDs, and includes that worker. The terminal-package repair is migrated unchanged onto this fresh current-main branch rather than duplicating the denominator repair.
