# Portable Organization Claim Allocator iPhone Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Issue: #884
Parent allocator: #842
Same-device architecture owner: #201

## Goal

Express the existing canonical organization claim allocator on `CURRENT_USER_IPHONE` without changing claim authority.

```text
canonical claim authority: StegVerse-Labs/.github organization allocator
execution surface: CURRENT_USER_IPHONE
serialization: atomic compare-and-swap portable state
HB authority effect: NONE
request/dispatcher authority effect: NONE
StegOS claim authority: NONE
credential authority: TV/TVC
GitHub runtime authority: NONE
requires_other_machine: false
```

This is the same allocator semantics as `scripts/allocate_claims.py`, not a second allocator.

## Current source floor

The portable package is anchored to:
- `tasks/TASK-2026-0007.json`
- `tasks/TASK-2026-0008.json`
- `tasks/TASK-2026-0009.json`
- `control/claims-active.json`
- `control/queue.json`

TASK-0006 remains superseded/proposed and is not eligible. Existing durable task history remains source provenance.

TASK-0007 and TASK-0008 are retained predecessor catalog identities. TASK-0009 is the exact non-overlapping HB31 Ecosystem Chat current-iPhone Site successor projection. A catalog extension does not reactivate or reset any prior task or fence.

## Portable state

Schema: `stegverse.org-allocator-portable-state/v1`.

State contains:
- canonical claim registry generation;
- active claims;
- portable task statuses;
- queue generation/order;
- hash-linked allocation tail;
- retained full last allocation/claim observation.

A state transition exists only after atomic compare-and-swap succeeds against the exact expected predecessor state.

Portable CAS is the same-device serialization primitive corresponding to the native O_EXCL lock. It grants no authority independently.

## Canonical allocation semantics

Preserve:
1. only `queued` tasks with complete dependencies are candidates;
2. priority order `security -> release -> critical -> elevated -> normal`, then `requested_at`, then task id;
3. every mandatory mutable request must declare a dependency surface or explicit exemption;
4. shared dependency surfaces collide before repository identity;
5. repository-exclusive and repository-local scope collision semantics remain unchanged;
6. selected task receives claim generation = prior generation + 1;
7. each granted claim receives the same generation as fencing token;
8. task becomes `active`;
9. queue ordering/generation advances;
10. no selection means no claim authority effect.

The allocation/CAS/lease/fence logic remains unchanged for TASK-0009. Only the exact package catalog validator now accepts either the historical two-task predecessor package or the exact three-task successor package.

## Runtime evidence

Source/merge/CI prove only implementation.

Authentic claim completion requires the physical current iPhone to atomically advance the portable allocator state and retain an exact TASK claim observation.

## Bootstrap circularity

The allocator bootstrap is intentionally separate from TASK-owned `stegos-bootstrap/*` product paths. This lane must not solve publication by bypassing a task claim gate. The already-established Site `stegos-node/` bootstrap remains the same-device delivery surface for the canonical allocator package and grants no product mutation authority.

## Implemented source — 2026-09-02

Installed:
- `org_allocator/portable_allocator.js`;
- `control/portable-org-allocator/current-iphone-package.json`;
- `schemas/org-allocator-portable-state.schema.json`;
- `tests/test_portable_org_claim_allocator_iphone.py`.

The original package was bound to TASK-0007/TASK-0008 with claim generation floor 2. The module validates exact task identity/request-time/repository/dependency-surface floors before allocating.

Expected original repeatable sequence on an uncontended initial package:
```text
first allocation -> TASK-2026-0007 / claim generation 3
later allocation -> TASK-2026-0008 / claim generation 4
```

## Authentic current-iPhone execution — 2026-09-03

The physical established current iPhone executed the canonical portable organization allocator.

Verified exported evidence:

```text
schema: stegverse.device-org-allocator-execution-evidence/v1
state: CANONICAL_ALLOCATION_EXECUTED
node_id: stegnode-web-f24e3bfb7f5343cb37323187a88e51f3
selected task: TASK-2026-0008
claim registry generation: 4
fencing token: 4
dependency surface: site:stegos-de006-bound-inference-publication
execution surface: CURRENT_USER_IPHONE
credential authority: TV/TVC
GitHub token runtime authority: NONE
requires other machine: false
journal replay: PASS
journal entries: 53
journal tail: 867ef9a2955e67a7676987327d98e30708ff4b9d2a923935ba8e3aa4b15987d4
evidence file sha256: 84f5def9ab0b810299fcb1d726f85fa000857252c33bc75ab7f846ed3f19be90
allocator receipt sha256: sha256:b7ae12318e6f9619ca87351fea27dc72fd4e4687c4788273d80006f8fcae360b
claim snapshot sha256: 09f4a79bc073d07f322db6a15b8958baa6fb1618c96e36132b2cf937be74f054
```

Independent deterministic verification confirmed the 53-entry journal chain, G4/fence 4 identity, exact TASK-0008 dependency surface, and `task_0008_granted=true`.

Authority remains unchanged: the canonical organization allocator is the claim authority; the observation itself grants no authority; Site, StegOS, HB, browser shell, transport, GitHub, and source publication do not mint this claim.

The native repository file `control/claims-active.json` remains the native filesystem allocator registry and is not rewritten to masquerade this portable-device CAS transition as a native allocator execution.

Downstream result:
- Site #932 was authentically admitted under this claim;
- Site PR #952 merged and deployed the predecessor current-iPhone StegOS projection;
- later runtime/source successors require their own fresh exact task/fence.

## TASK-0009 successor catalog — 2026-09-06

StegOS PR #218 repaired the existing HB31 Ecosystem Chat current-iPhone autostart runtime-opportunity seam. The released successor package was merged by StegOS #220 as `4265ca06c8b6cd49c5ffcab8de265140ef1f24f9`; its package claim was released as `7f6e473c6c28d53ac5b6d81788227a4a17e90d93`.

Site still projects predecessor autostart blob:

```text
3927e2aa650f3267c53af73f3ef8bea2379805b9
```

while the released StegOS source is:

```text
7d8d02cfee688a58cbb813cf04c1fada8801b2a6
```

TASK-0008/G4 must not be reactivated. Its exact Site path set never included `stegos-bootstrap/device-local-autostart.js`. TASK-2026-0009 therefore represents genuinely new, non-overlapping work with dependency surface:

```text
site:hb31-ecosystem-chat-runtime-opportunity-successor
```

The updated portable package retains the same `ORG-ALLOCATOR-PORTABLE-IPHONE-20260902` authority epoch and predecessor seed state. An already-persisted G3/G4 portable state remains valid. Because `effectiveTasks()` falls back to the package's queued status for a newly cataloged task when no persisted status exists, TASK-0009 may be considered without resetting old state. Existing G3/G4 claims remain in the collision set and are preserved.

Regression validation explicitly constructs retained G3/G4 state, keeps TASK-0007/TASK-0008 active, and requires the unchanged allocator selection/CAS logic to select TASK-0009 at generation/fence 5 only because its exact dependency/path scope is non-overlapping.

This is source capability, not runtime proof:

```text
TASK-0009 physical allocator claim: NOT OBSERVED
G5 or later successor fence: NOT OBSERVED
Site successor projection: NOT OBSERVED
HB31 current-iPhone Ecosystem Chat execution from successor Site source: NOT OBSERVED
```

No source/package/CI/README/handoff change grants a claim. HeartBeat remains non-authorizing; TV/TVC remains credential authority; GitHub runtime authority remains NONE; no second machine, scheduler, allocator, or WorkerCoordinator is introduced.
