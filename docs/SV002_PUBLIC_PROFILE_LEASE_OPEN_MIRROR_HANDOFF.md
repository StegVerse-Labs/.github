# SV002 Public Profile Canonical Lease-Open Mirror Handoff

Updated: 2026-09-02
Repository: `StegVerse-Labs/.github`
Issue: `#616`
State: HANDOFF_ESTABLISHED / SOURCE_IMPLEMENTATION_PENDING
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
