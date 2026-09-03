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


## Implemented source — 2026-09-02

Installed:
- `org_allocator/portable_allocator.js`;
- `control/portable-org-allocator/current-iphone-package.json`;
- `schemas/org-allocator-portable-state.schema.json`;
- `tests/test_portable_org_claim_allocator_iphone.py`.

The current package is bound to:
```text
scripts/allocate_claims.py blob 7c0105c8529b682c24a94b39ba31a8ca574c3717
TASK-2026-0007 blob       a5fd4662b2a370e8a86099c943b8d1ec18b93e19
TASK-2026-0008 blob       f534167633c867bbee6b397ae345b10ed502aa2b
claims predecessor blob   9e7eaf9cb1319dd570714a0c1806d7173a7ba7ff
queue predecessor blob    6cab961c8750495dab36d1a523980516b1ac3a5e
claim generation floor    2
```

The module validates exact task identity/request-time/repository/dependency-surface floors before allocating.

Expected repeatable sequence on an uncontended current package:
```text
first allocation -> TASK-2026-0007 / claim generation 3
later allocation -> TASK-2026-0008 / claim generation 4
```

The second transition is permitted because the two dependency surfaces are disjoint. This is a semantic expectation from the packaged current state, not a runtime claim.

Physical iPhone allocation remains NOT OBSERVED.


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

Independent deterministic verification of the complete export confirmed:
- all 53 journal entries form one valid hash chain;
- projected journal tail equals the recomputed tail;
- allocator receipt self-hash matches;
- claim snapshot hash matches;
- TASK-2026-0008 is the selected task;
- generation and fencing token are both 4;
- the exact required dependency surface is present;
- `task_0008_granted=true`.

Authority remains unchanged: the canonical organization allocator is the claim authority; the observation itself grants no authority; Site, StegOS, HB, browser shell, transport, GitHub, and source publication do not mint this claim.

The native repository file `control/claims-active.json` remains the native filesystem allocator registry and is not rewritten to masquerade this portable-device CAS transition as a native allocator execution.

Downstream result:
- Site #932 was authentically admitted under this claim;
- Site PR #952 merged and deployed the exact current-iPhone StegOS projection;
- physical SV001 execution remains a separate subsequent predicate.


## TASK-2026-0007 catalog reconciliation — 2026-09-03

Authentic CURRENT_USER_IPHONE allocator history is retained:

```text
TASK-2026-0007 portable claim generation/fence: 3 / 3
significance: authentic allocator runtime history only
source-completion cause: Site PR #401 / merge cdf68fe70294d43b59607c2991478c2cc4b53546
source-completion time: 2026-08-22T12:23:32Z
```

The organization task catalog had incorrectly left TASK-0007 as `queued` after that source merge. Issue #912 reconciles it to `completed` without asserting Site#239 product activation.

The portable package continues to retain TASK-0007 as provenance, but its status is now `completed`, so fresh-device allocator initialization cannot offer it again. TASK-0008 remains independently `queued` in this package. Existing physical iPhone G3/G4 allocator state is not rewritten, reset, or manufactured by this source repair.

Authority boundaries remain unchanged: organization allocator = claim authority; TV/TVC = credential authority; HB/GitHub/StegOS do not grant claim authority; no second machine is introduced.
