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


## TASK-0008 claim-scope freshness fingerprint — 2026-09-02

TASK-2026-0008 was widened while still queued from the older five-file DE-006 Site
projection to the canonical current-iPhone projection package.

Task identity, requested timestamp, repository, and dependency surface did not change,
so those fields alone cannot distinguish an old local checkout from the current task.

The resident source-catalog floor now pins the canonical SHA-256 of the mandatory
claim scope:

`98096b5825e85dd558f9cb5a4e882002543d4c703cfa7981cd2d826c80c1a05b`

The digest covers the claim scope object (paths, contracts, release surfaces,
capabilities, workflows, dependency surfaces) and deliberately excludes mutable
runtime task status.

Before any materialization or allocator invocation, the consumer recomputes that digest
from the already-local source task. A mismatch fails `STALE_SOURCE_CATALOG` and no
allocator call occurs.


## Collision reconciliation — canonical same-device bootstrap — 2026-09-03

A later implementation duplicated the already-merged canonical same-device allocator.

Canonical lane:
- `.github#884` / merge `d3da58e0f6822bde7316ada3f532f15f75a2fdcf`;
- portable allocator: `org_allocator/portable_allocator.js`;
- exact current-iPhone package:
  `control/portable-org-allocator/current-iphone-package.json`;
- Site bootstrap: `StegVerse-Labs/Site#945` / merge
  `9868b62ba2bfaaba0a0164318ac4d1d4f6d235d5`;
- public bootstrap paths live under `stegos-node/`, outside TASK-0008 product paths.

The later StegOS#181/#182 allocator under `mobile/web-bootstrap/` and .github#905
TASK widening are superseded duplicate work and must not become the product claim
boundary.

TASK-2026-0008 is therefore restored to its canonical 17-file Site product scope and
source-catalog scope SHA-256:

`98096b5825e85dd558f9cb5a4e882002543d4c703cfa7981cd2d826c80c1a05b`

This preserves the bootstrap separation:

```text
Site stegOS-node allocator bootstrap
-> physical current-iPhone canonical allocation
-> TASK-0007 may grant first
-> repeat allocation
-> authentic TASK-0008 claim
-> only then Site#932 stegOS-bootstrap product projection
```

No claim/runtime predicate is promoted by this cleanup.


## Event-ephemeral materialization — 2026-10-17 (PR #3211, source only, not merged)

This section supersedes the earlier statements that only the resident dispatcher
may consume `control/resident-execution-request.d/org-claim-allocator-*.json`.
Under `data/task-registry-global-invariants.json`
(`external_machine_awaiting_allowed=false`,
`receiver_unavailable_disposition=DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION`)
a receiver's liveness is not a transition predicate, so a durably queued request
no longer waits on a resident machine. The resident path stays valid; it is no
longer the only one.

### Materialization path

- **Trigger:** `.github/workflows/organization-claim-allocator-transition.yml`
  runs on a push to `main` that touches `org-claim-allocator-*.json` (the commit
  carrying the durable queue entry), and on `workflow_dispatch`. A
  `pull_request` run only validates against temporary ledgers.
- **Declared git-ref store:** the workflow asserts that `org-contract.json`
  declares `organization_ledger` as `store=git`,
  `ref=refs/stegverse/organization-ledger`, and that `contract.json`
  `repository_ledger_location` is on the same ref with `new_ledger_root=false`.
  It fetches that ref (FAIL_CLOSED `ORGANIZATION_LEDGER_REF_ABSENT` if it is not
  published) and runs the **existing** consumer, which runs the **existing**
  `scripts/allocate_claims.py`, with no `--org-ledger-root` and
  `--repo-ledger-root git+<checkout>#refs/stegverse/organization-ledger:<namespace>`.
- **Concurrency:** `concurrency: group: organization-ledger`,
  `cancel-in-progress: false`, shared with every other writer of the ref. Only
  the transition job has `contents: write`.
- **Compare-and-swap push:** the run requires the local ref to fast-forward the
  fetched tip (else FAIL_CLOSED `ORGANIZATION_LEDGER_HISTORY_REWRITTEN`, nothing
  pushed), then publishes with a non-forced push, which the remote accepts only
  as a fast-forward of its current tip. A lost race is FAIL_CLOSED
  `ORGANIZATION_LEDGER_PUBLISH_RACE` and publishes nothing.
- **Fresh-fetch readback:** a new bare repository fetches the published ref with
  the checkout's own credential, checks that its tip equals the pushed tip, and
  runs `consume_org_claim_allocator_request.py --readback-result`, which reads
  every appended Organization receipt back through the existing
  `organization_readback` verifier. Any receipt that does not read back makes the
  readback FAIL_CLOSED.
- A run passes only if every attempt is typed `ORGANIZATION_WORKER_CLAIM_GRANTED`,
  `_REFUSED` or `_FAIL_CLOSED`. No new secret, PAT, credential, scheduler, host or
  dependency is used. The run is not claim authority; the ledger receipts are
  the evidence.

### HOSTED_ENV relaxation and the refusals that remain

`clean_env` still refuses every `HOSTED_ENV` marker, except when
`event_ephemeral_materialization()` holds. That requires all three of the
following:

1. no explicit `--org-ledger-root`;
2. the manifest-declared Organization store is non-posix and declares a ref;
3. `--repo-ledger-root` is a `git+…#<that declared ref>:…` locator.

Even then, `ledger_custody` refuses
(`EVENT_EPHEMERAL_REPOSITORY_LEDGER_NOT_ON_DECLARED_REF`) unless the repository
store shares the Organization store's git dir and ref. Still refused in a hosted
environment: an explicit POSIX Organization root, a POSIX repository root, a
repository chain on another ref, and a repository store in a different git dir.
The relaxed environment carries no hosted markers into the allocator.

### Defects fixed

- **`git+` locator:** `ledger_custody` used to wrap every `--repo-ledger-root` in
  `PosixLedgerStore`, so a `git+…` locator silently became a POSIX directory
  named after the locator. `repository_ledger_store()` now opens a `git+` locator
  as that ref, and the CLI keeps the argument as a string so that it is not
  path-normalized.
- **Shared-ref compare-and-swap pin:** the Organization store pins the ref tip
  while it computes the fence. Because the repository receipt is written to the
  same ref, that write moved the tip, and every ALLOW failed with
  `ORGANIZATION_LEDGER_REF_COMPARE_AND_SWAP`. `adopt_repository_append()` now
  advances the pin only to the pinned snapshot itself, or past exactly one
  commit whose sole parent is the pinned snapshot and whose repository HEAD is
  the receipt just appended. Any other move is FAIL_CLOSED
  `ORGANIZATION_LEDGER_SNAPSHOT_MOVED` through the existing retry path, and the
  repository receipt is retained.

### Expected first live run and its repair

The committed `control/claims-active.json` is at generation 2, while issued
fences reach 7 (`TASK-2026-0012` `allocator_fence=7`, the provenance floor). The
first run on `main` is therefore expected to record, for each queued request,
`ORGANIZATION_WORKER_CLAIM_FAIL_CLOSED` with
`FENCE_GENERATION_BEHIND_ISSUED_FENCES`. That is a typed terminal disposition,
not a wait. Its repair is to rematerialize the runtime claim registry at or
beyond the issued fences. PR #3211 does not touch the claim registry (fence
authority), and no machine is awaited. Until a run is observed and read back,
none of this is runtime evidence.
