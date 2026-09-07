# Resident Organization Claim Allocator Mirror Handoff

Updated: 2026-09-06
Issue: StegVerse-Labs/.github#842
Parent control plane: #12

## Defect

The canonical organization allocator already existed in
`scripts/allocate_claims.py`, but its only invocation in GitHub Actions was
explicitly ephemeral validation. Runner-local claim mutations were discarded.

As a result, a valid queued organization task could remain indefinitely unclaimed
even though the handoff described allocation as machine-owned.

## Repair

The existing allocator remains the sole claim-grant logic.

The resident runtime now receives:

- `control/resident-execution-request.d/org-claim-allocator-001.json`
- `scripts/consume_org_claim_allocator_request.py`
- existing `scripts/allocate_claims.py`

The consumer is registered in the existing
`dispatch_resident_execution_requests.py` dispatcher and is carried by bootstrap,
native install, and source refresh.

The request is repeatable on resident dispatch so future queued tasks do not require
a new scheduler or one request per task.

## Concurrency

`allocate_claims.py` now uses a deployment-local O_EXCL serialization fence:

`control/claims-allocator.lock`

The fence grants no task authority. It prevents concurrent resident dispatcher
processes from mutating claim generation/state simultaneously. A live owner produces
`ALLOCATOR_BUSY`; a dead local owner can be recovered.

## Authority boundary

```text
request grants claim authority: false
heartbeat grants execution authority: false
dispatcher grants authority: false
canonical allocator remains claim authority: true
GitHub token required: false
network source fetch: false
second machine required: false
second scheduler created: false
```

A selected task receives only the pre-existing allocator claim semantics. This repair
does not execute the claimed repository task by itself and does not confer publication
or product authority.

## Immediate queued consumer

`TASK-2026-0009` is now the minimum source-catalog freshness consumer for the existing
resident allocator path. It requests only:

`site:hb31-ecosystem-chat-runtime-opportunity-successor`.

TASK-2026-0008/G4 remains predecessor provenance and must not be reactivated. The
resident allocator may retain existing TASK-0007/TASK-0008 runtime state and claims;
TASK-0009 is a distinct queued successor whose non-overlapping Site scope permits the
next monotonic canonical claim/fence when the established resident allocator actually
runs.

Runtime proof remains deployment-local. Source merge or CI does not prove that the
resident allocator has consumed the request or granted TASK-2026-0009.

## Post-merge source reconciliation

```text
source merge: b19b94a5512b160e086ffa8460e8a9ba7f7efcb1
organization control-plane validation: SUCCESS
cross-framework resident-dispatch validation: SUCCESS
original Heartbeat Worker Project PR run: CHECKOUT_INFRA_FAILURE_BEFORE_TESTS
retry of original merged-PR run: CHECKOUT_INFRA_FAILURE_BEFORE_TESTS
runtime allocator consumption observed: false
runtime claim grant observed: false
```

The two Heartbeat failures above occurred at the anonymous PR-ref checkout step after
the source PR had already merged; all validation/test steps were skipped. They are
not source-test failures and are not runtime evidence.

This reconciliation PR exists to validate the exact current-main source through a live
PR ref. Even if validation passes, deployment-local allocator consumption and task
claim evidence remain independently required.

## Minimum source-catalog freshness floor

A resident runtime can have current allocator consumer source but still be pointed at an
older already-local canonical checkout. That checkout may predate newly queued
organization work. The allocator must not silently operate on such a stale catalog.

The repeatable resident request carries a non-authorizing source-catalog floor. The
current exact floor is:

```text
task_id: TASK-2026-0009
requested_at: 2026-09-06T13:25:00Z
repository: StegVerse-Labs/Site
dependency_surface: site:hb31-ecosystem-chat-runtime-opportunity-successor
scope_sha256: 121d9e79d98d582642e032a607ef9cacc5965acfba6fdc371bbbc9ccf8716ce1
purpose: MINIMUM_SOURCE_CATALOG_FRESHNESS_ONLY
task_eligibility_effect: NONE
```

Before any runtime task/control input is materialized and before the canonical
allocator is invoked, the consumer verifies that the already-local source checkout
contains the exact task identity, requested timestamp, repository, dependency surface,
and mandatory claim-scope digest.

A missing or older catalog fails with `STALE_SOURCE_CATALOG`. No network fetch is
attempted and no claim is granted.

The floor does **not** require TASK-2026-0009 to remain queued. Once the minimum source
catalog is known to include that task, later task status is still determined by the
canonical allocator. This preserves the allocator's generic future use and the retained
TASK-0007/TASK-0008 runtime history.

## Portable exact allocator selector

The native source-refresh service already visits all registered resident consumers, but
the portable refresh+dispatch bridge maintains an explicit allowlist for one-consumer
execution. `org_claim_allocator` is admitted to that exact-selector list.

This permits an already-existing non-hosted resident surface to refresh current
already-local `.github` source and dispatch only `org_claim_allocator` without visiting
unrelated resident requests and without requiring systemd.

The portable bridge still grants no claim, fence, execution, heartbeat, credential, or
publication authority. The canonical allocator remains the only claim-grant authority,
and the source-catalog freshness floor still applies before allocation.

## Retained per-task claim-grant evidence

A successful allocator process result is not sufficient by itself to prove a claim.
After the canonical allocator reports a selected task, the resident consumer re-reads
the post-allocation `control/claims-active.json` state and requires one or more canonical
claims for that exact task with valid lease fencing tokens.

Only after that post-state agrees does it retain:

```text
receipts/sovereign-host/org-claim-allocator-grants/<TASK>-G<generation>.json
receipts/sovereign-host/org-claim-allocator-grants/<TASK>.latest.json
```

The receipt contains:
- exact granted claims;
- claim-registry generation;
- canonical lease fencing tokens;
- dependency surfaces;
- stable claim snapshot SHA-256;
- TV/TVC credential authority;
- no GitHub-token/network/second-machine requirement;
- `authority_effect=NONE_OBSERVATION_ONLY`.

The observation receipt grants no claim authority. The canonical allocator mutation
remains the sole grant transition.

## TASK-0008 claim-scope freshness fingerprint — retained provenance

TASK-2026-0008 was widened while still queued from the older five-file DE-006 Site
projection to the canonical current-iPhone projection package. Its final canonical
claim-scope digest remains retained as predecessor provenance:

`98096b5825e85dd558f9cb5a4e882002543d4c703cfa7981cd2d826c80c1a05b`

That fingerprint no longer defines the minimum resident source-catalog floor after the
TASK-0009 successor was merged. It remains useful for reconstructing the authentic G4
predecessor state and must not be reused as successor authority.

## Collision reconciliation — canonical same-device bootstrap

Canonical lane:
- `.github#884` / merge `d3da58e0f6822bde7316ada3f532f15f75a2fdcf`;
- portable allocator: `org_allocator/portable_allocator.js`;
- exact current-iPhone package:
  `control/portable-org-allocator/current-iphone-package.json`;
- Site bootstrap: `StegVerse-Labs/Site#945` / merge
  `9868b62ba2bfaaba0a0164318ac4d1d4f6d235d5`;
- public bootstrap paths live under `stegos-node/`, outside TASK-owned product paths.

The later StegOS#181/#182 allocator under `mobile/web-bootstrap/` and .github#905 TASK
widening are superseded duplicate work and must not become the product claim boundary.

The canonical same-device sequence is now:

```text
Site stegOS-node allocator bootstrap
-> already-local resident source refresh
-> exact TASK-0009 source-catalog floor passes
-> existing canonical organization allocator runs
-> retained G3/G4 history remains intact
-> authentic TASK-0009 claim receives next monotonic generation/fence if collision-free
-> only then Site successor projection may mutate TASK-0009 product paths
```

No claim/runtime predicate is promoted by this source reconciliation.
