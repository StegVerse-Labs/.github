# Portable Organization Claim Allocator iPhone Mirror Handoff

Updated: 2026-09-02
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

The first portable package is anchored to:
- `tasks/TASK-2026-0007.json`
- `tasks/TASK-2026-0008.json`
- `control/claims-active.json`
- `control/queue.json`

TASK-0006 remains superseded/proposed and is not eligible. Existing durable task history remains source provenance.

TASK-0007 is older release-priority work and may be selected first. Its dependency surface does not overlap TASK-0008, so repeatable allocator execution must be able to grant TASK-0008 afterward.

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

## Runtime evidence

Source/merge/CI prove only implementation.

Authentic completion requires the physical current iPhone to atomically advance the portable allocator state and retain an exact TASK claim observation.

## Bootstrap circularity

Current public Site does not yet contain this allocator, while publication of the full current iPhone surface is itself gated on TASK-0008.

This lane must not solve that by bypassing the claim gate. A separate bootstrap resolution must provide the canonical allocator to the already-established iPhone without granting product publication or task claim authority.
