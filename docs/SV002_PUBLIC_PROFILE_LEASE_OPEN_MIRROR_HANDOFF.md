# SV002 Public Profile Canonical Lease-Open Mirror Handoff

Updated: 2026-09-02
Repository: `StegVerse-Labs/.github`
Issue: `#616`
State: SOURCE_MERGED_VALIDATED / AUTHENTIC_PUBLIC_LEASE_OPEN_EVIDENCE_PENDING
Credential authority: TV/TVC
GitHub token runtime authority: NONE
Authority effect: NONE

## Goal

Advance the SAME canonical SV002 public-observation lease from persisted `PUBLIC_VERIFYING` to `LEASE_OPEN` only after an independent credential-free HTTPS observation of the public Universal InTr profile proves that `SV002:PublicObservation` is advertised at exactly:

`https://stegverse.org/intr/profile`

## Existing source basis

- `.github` canonical SV002 lease absorption: #609 / `112416c1393ac957a6ccde9ec42876da0802f687`.
- StegOS application-neutral public profile verifier: `stegos/universal_intr_public_profile.py`.
- StegOS canonical lease snapshot/resume: `LeaseMachine.snapshot()` / `LeaseMachine.from_snapshot(...)`.
- Current persisted precondition:
  `ABSENT -> REQUESTED -> ADMITTED -> PROVISIONING -> LOCAL_READY -> PUBLIC_VERIFYING`.

## Required source path

```text
persisted canonical lease snapshot state=PUBLIC_VERIFYING
-> verify exact snapshot digest/history/request identity
-> already-local StegOS public-profile verifier
-> independent HTTPS GET https://stegverse.org/intr/profile
-> schema + sovereign InTr contract validation
-> require profile SV002:PublicObservation
-> require observation_origin=INDEPENDENT_PUBLIC_HTTPS
-> bind observed URL/profile schema/profile SHA-256
-> LeaseMachine.from_snapshot(the SAME snapshot)
-> transition PUBLIC_VERIFYING -> LEASE_OPEN
-> atomically persist evolved snapshot
-> consumer revalidates exact LEASE_OPEN history/snapshot
-> only then invoke existing WorkerCoordinator targeted task
```

## Invariants

- `PUBLIC_VERIFYING` must exist before public observation.
- Public profile observation grants no execution, credential, route, publication, custody, claim/fence, receiving, transition, or sovereign authority by itself.
- The public HTTPS request is observation of an already-public endpoint; it is not network source acquisition.
- No GitHub token or non-TV/TVC credential is accepted.
- Same canonical lease request identity/history must survive resume; request/history drift fails closed.
- No new lease may replace a failed/mismatched persisted lease.
- `LEASE_OPEN` may be persisted only after verified independent public HTTPS evidence.
- Materialization consumer must not dispatch WorkerCoordinator while snapshot remains `PUBLIC_VERIFYING`.
- No receiver READY, READ_OBSERVATION round trip, Master Records custody, SV002 principal execution, or public experiment finding may be inferred from `LEASE_OPEN`.
- Canonical StegVerse-002 principal execution ownership remains `StegVerse-002/.github`; this is only the StegVerse-Labs public-observation/reference lane.

## Source implementation targets

```text
workers/sv002_public_profile_lease_resumer.py
workers/sv002_intr_materialization_consumer.py
tests/test_sv002_public_profile_lease_resumer.py
tests/test_sv002_event_ephemeral_materialization.py
docs/SV002_PUBLIC_OBSERVATION_RUNTIME_MIRROR_HANDOFF.md
```

No additional WorkerCoordinator task, scheduler, heartbeat authority, or parallel runtime lane should be created.

## Required deterministic tests

- exact PUBLIC_VERIFYING history resumes to LEASE_OPEN;
- wrong URL fails closed;
- missing required profile fails closed;
- wrong observation origin fails closed;
- snapshot digest drift fails closed;
- request/history drift fails closed;
- stale/already-LEASE_OPEN snapshot is idempotently accepted only when its bound public verification evidence matches;
- consumer refuses to dispatch on PUBLIC_VERIFYING;
- consumer dispatches only on exact LEASE_OPEN history;
- public profile evidence cannot claim receiver READY, round trip, custody, or principal execution.

## Authentic completion boundary

Source merge/CI proves source implementation only.

Authentic runtime completion for this issue additionally requires deployment-local evidence that the persisted SV002 lease transitioned from `PUBLIC_VERIFYING` to `LEASE_OPEN` after an actual independent public HTTPS profile observation.

Issue #462 remains the separate close condition for receiver READY and authentic `RECEIVED -> FORWARDED` public observation round trip.

## Next authorized machine action

Implement the bounded lease resumer and integrate it before WorkerCoordinator dispatch in the existing materialization consumer. Validate against current organization-control and Heartbeat suites before merge.


## 2026-09-02 implementation checkpoint

Implemented source now:
- resumes the exact persisted `PUBLIC_VERIFYING` lease through `LeaseMachine.from_snapshot`;
- invokes the already-local StegOS `verify_public_intr_profile` against exactly `https://stegverse.org/intr/profile`;
- requires `SV002:PublicObservation`, verified independent HTTPS origin, exact profile schema/hash, no credential use, and zero execution authority;
- advances only the same lease request/history to `LEASE_OPEN`;
- persists an observation sidecar binding pre/post lease hashes to URL/schema/profile hash;
- requires the materialization consumer to validate exact `LEASE_OPEN` history before WorkerCoordinator dispatch;
- preserves false claims for receiver READY, round trip, Master Records custody, and SV002 principal execution;
- handles an already-open lease only when the persisted public-observation evidence binds to the exact open snapshot.

Source validation and merge remain pending. Authentic external public observation/runtime execution remains unobserved.


## 2026-09-02 validated source closure

```text
implementation PR: #782
merge: 921b55eb1b93b621fb0ae0e648ab789dfb056731
organization control validation: SUCCESS
Heartbeat Worker Project validation: SUCCESS
source implementation: MERGED_VALIDATED_CURRENT_MAIN
authentic independent public HTTPS observation: NOT OBSERVED
authentic deployment-local LEASE_OPEN transition: NOT OBSERVED
receiver READY: NOT OBSERVED
public READ_OBSERVATION round trip: NOT OBSERVED
```

The source gate is closed. The materialization consumer now dispatches the existing WorkerCoordinator task only after the same persisted canonical lease has been independently verified against the public Universal InTr profile and evolved from `PUBLIC_VERIFYING` to `LEASE_OPEN`.

Merge and hosted validation are not evidence that the public profile was actually observed or that the deployment-local lease has opened.
