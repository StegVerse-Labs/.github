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
