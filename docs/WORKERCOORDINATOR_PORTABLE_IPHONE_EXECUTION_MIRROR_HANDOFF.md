# Portable WorkerCoordinator iPhone Execution Mirror Handoff

Updated: 2026-09-02
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

A portable checkout MUST reject:
- task state other than `HANDOFF_READY`;
- pre-existing task worker/claim binding;
- authority domain other than `INDEPENDENT_TASK_CONTROL`;
- claim state other than `AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM`;
- `fresh_fence_required != true`;
- any assertion that HB grants execution authority;
- incomplete dependencies;
- unauthorized handoff execution;
- stale/invalid source-state binding;
- unresolved worker binding;
- credential authority other than TV/TVC;
- GitHub token/runtime authority;
- stale portable WorkerCoordinator state hash/generation;
- reused claim/fence;
- non-atomic persistence.

## State model

Portable canonical state:

`stegverse.workercoordinator-portable-state/v1`

The persisted state contains the canonical WorkerCoordinator generation and a hash-linked checkout tail. It grants no authority merely by existing. A new claim/fence exists only after atomic compare-and-set succeeds against the exact expected prior state.

The portable state is reconstructable and may live in the established StegOS IndexedDB on the current iPhone. Its namespace MUST remain distinct from `device-task-control-generation`.

## First consumer

`SHWP-STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001`

The first consumer already has:
- independent task-control admission;
- no task dependencies;
- TV/TVC bounded-autonomy lease authority;
- no repository/network/financial/credential side-effect authority;
- iPhone subordinate executor in StegOS merge `835372a69af23dc73b6f75591ced6281c43ffa8d`.

Portable WorkerCoordinator checkout does not satisfy the TVC lease predicate. TVC issuance/validation remains separate.

## Completion

Source completion:
- portable transaction module;
- state + checkout schemas;
- deterministic positive/negative tests;
- SV001 package/binding;
- exact StegOS persistence adapter projection.

Runtime completion:
- physical iPhone atomically advances canonical WC portable state;
- fresh SV001 claim/fence is emitted;
- exact checkout receipt is retained/reconstructable;
- subordinate SV001 envelope consumes that claim/fence;
- no second user-operated device participates.

Source/merge/CI never substitute for runtime completion.


## Duplicate-terminal prevention — 2026-09-03

Fresh current-iPhone evidence exposed a missing serial-terminal guard: after the valid
G23 SV001 cycle completed, the persisted portable generation could be checked out
again as G24. The checkout itself was atomic and non-parallel, but the task-specific
terminality contract prohibited re-execution.

Issue #944 repairs the canonical source by requiring the SV001 portable package to be
single-checkout for its authority epoch/task package. Portable state now retains
`checkout_count`; legacy state without that field infers prior checkout count from
`generation - predecessor_generation_floor` and therefore fails closed when a prior
checkout already occurred.

This does not erase or rewrite G24 evidence. G24 remains retained as duplicate,
non-custodial evidence. G23 remains the canonical terminal SV001 execution because it
was the first terminal execution and the handoff already required
`terminal_autonomy_reexecution_allowed=false`.

Downstream retry remains permitted; terminal task re-execution does not.

## Reset-lineage terminal propagation — 2026-09-04

Fresh authentic CURRENT_USER_IPHONE evidence exposed the remaining hole in #944: the
single-checkout counter is local to one portable state lineage. A newly established
StegOS web node can begin from the still-published G22 predecessor floor when the
canonical task package itself remains `HANDOFF_READY`.

Observed duplicate execution:

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

This is authentic execution evidence, but it is duplicate/non-custodial because the
first terminal G23 already closed the task contract.

Canonical custody remains:

`sha256:81a078eeeacffb8fc86d287d7aaa8a9904c6f53973471dad7f6d7c3fa6818a35`.

Issue #976 therefore moves terminality into the canonical portable package itself.
After the first authentic terminal execution, the package is no longer a preclaim
input:

```text
task.state = COMPLETED
claim_state = TERMINAL_NO_FURTHER_CLAIM
fresh_fence_required = false
execution_authorized = false
authority_effect = CANONICAL_WORKERCOORDINATOR_PORTABLE_TERMINAL_PACKAGE
```

The package binds the canonical first-terminal G23 receipt and retains both known
duplicate terminal receipts as non-custodial evidence. Because the generic checkout
validator already requires a clean `HANDOFF_READY` task before it reads/initializes
portable state, any fresh node receiving this terminal package fails closed before a
new G23 can be minted.

This is terminal-state propagation, not a second runtime authority. WorkerCoordinator
remains the claim/fence authority, TV/TVC remains credential authority, HB grants no
authority, and downstream Master Records/SV002 retry remains allowed without SV001
re-execution.
