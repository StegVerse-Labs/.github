# Resident Organization Claim Allocator Mirror Handoff

Updated: 2026-09-02
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

`TASK-2026-0008` / `StegVerse-Labs/Site#932` is the target consumer for this session.
It requests only `site:stegos-de006-bound-inference-publication`.

The catalog also contains older queued release-priority `TASK-2026-0007`. The allocator
may grant that task first. Its Site scope is non-overlapping with TASK-2026-0008, so
a later resident dispatch can grant TASK-2026-0008 without collision. The repeatable
resident request is specifically required so queue progress does not stop after one grant.

Runtime proof remains deployment-local. Source merge or CI does not prove that the
resident allocator has consumed the request or granted TASK-2026-0008.


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


## Minimum source-catalog freshness floor — 2026-09-02

A resident runtime can have current allocator consumer source but still be pointed at an
older already-local canonical checkout. That checkout may predate newly queued
organization work. The allocator must not silently operate on such a stale catalog.

The repeatable resident request now carries a non-authorizing source-catalog floor:

```text
task_id: TASK-2026-0008
requested_at: 2026-09-03T00:28:00Z
repository: StegVerse-Labs/Site
dependency_surface: site:stegos-de006-bound-inference-publication
purpose: MINIMUM_SOURCE_CATALOG_FRESHNESS_ONLY
task_eligibility_effect: NONE
```

Before any runtime task/control input is materialized and before the canonical
allocator is invoked, the consumer verifies that the local source checkout contains a
matching task identity, requested timestamp, repository, and dependency surface.

A missing or older catalog fails with `STALE_SOURCE_CATALOG`. No network fetch is
attempted and no claim is granted.

The floor does **not** require TASK-2026-0008 to remain queued. Once the minimum source
catalog is known to include that task, later task status is still determined by the
canonical allocator. This preserves the allocator's generic future use.


## Portable exact allocator selector — 2026-09-02

The native source-refresh service already visits all registered resident consumers, but the portable refresh+dispatch bridge maintains an explicit allowlist for one-consumer execution. `org_claim_allocator` is now admitted to that exact-selector list.

This permits an already-existing non-hosted resident surface to refresh current already-local `.github` source and dispatch only `org_claim_allocator` without visiting unrelated resident requests and without requiring systemd.

The portable bridge still grants no claim, fence, execution, heartbeat, credential, or publication authority. The canonical allocator remains the only claim-grant authority, and the source-catalog freshness floor still applies before allocation.


## Retained per-task claim-grant evidence — 2026-09-02

A successful allocator process result is not sufficient by itself to prove a claim.
After the canonical allocator reports a selected task, the resident consumer now
re-reads the post-allocation `control/claims-active.json` state and requires one or
more canonical claims for that exact task with valid lease fencing tokens.

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

DE-006 binds the stable TASK-2026-0008 receipt as the distinct
`site_projection_claim_grant` predicate. An allocator visit, an unrelated task grant,
HB progression, or a selected task id without a matching post-allocation claim cannot
satisfy that predicate.
