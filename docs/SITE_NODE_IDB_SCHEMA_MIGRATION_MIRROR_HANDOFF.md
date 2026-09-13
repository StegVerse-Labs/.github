# Site Node IndexedDB Schema Migration Mirror Handoff

Goal Task ID: `SITE-NODE-IDB-SCHEMA-MIGRATION-001`
Parent Goal Task ID: `SS-EVIDENCE-COMPARISON-001`
COSV: `40000100100000`
Status: `ACTIVE / CLAIMED_INTEGRATION`

## Trigger

The original authentic failure was observed on an iPhone after the iOS synchronous picker repair and produced an independent DEVICE_KV directory-readback failure:

```text
Failed to execute 'transaction' on 'IDBDatabase': One of the specified object stores was not found.
```

That device reference is historical evidence provenance only. Under the canonical StegVerse device-role invariant, compatible StegOS devices are interchangeable execution/transport nodes and no device identity is a user-verification authority. The same screen still exposed the registered-Node resident action, so registration/Receipt #1 continuity remained readable. The repair therefore had to preserve browser-local continuity records while repairing the shared `stegos-node-v1` schema.

## Canonical repair

Site PR `StegVerse-Labs/Site#1235` was squash-merged to `main` at `a3bd73f0ced551738f37a6222b3ca933c3433fdf`.

The merged repair:

- defines canonical `stegos-node-v1` version 3 with `meta`, `receipts`, and `intr_outbox`;
- additively migrates legacy v1 and malformed v2 without deleting the database, stores, registration, or Receipt #1;
- installs migration-safe parser-time first-opener wrappers for shared Node/StegOS bootstrap paths while preserving the prior implementations behind `*-impl.js` paths;
- aligns the remaining native `services.js` opener to v3/full-store behavior;
- preserves prior Node projection, HIL sync, Master Records governance, bootstrap, and continuity validators rather than weakening them;
- exhaustively checks repository HTML entrypoints so canonical migration occurs before lower-version helper opens;
- reconciles Site README and task-specific handoff.

All exact-head pull-request validation lanes were green before merge. Post-merge `main` validation also passed for the merge commit.

## Live propagation evidence

Post-merge StegOS Node Public Observation run `34617268914` executed from exact source SHA `a3bd73f0ced551738f37a6222b3ca933c3433fdf` and successfully observed `https://stegverse.org/stegos-node/`.

The live step emitted, among other required markers:

```text
STEGOS_NODE_PUBLIC_OBSERVATION_PASS https://stegverse.org/stegos-node/
STEGOS_NODE_KV_CAPABILITY_SHELL_PUBLIC_OBSERVATION_PASS
STEGOS_NODE_KV_READINESS_BROWSER_STATE_PUBLIC_OBSERVATION_PASS
STEGOS_NODE_KV_INTR_BROWSER_APPLY_PUBLIC_OBSERVATION_PASS
STEGOS_NODE_HIL_INTR_LOCAL_OUTBOX_PUBLIC_SOURCE_PASS
STEGOS_NODE_OFFLINE_PROOF_PUBLIC_OBSERVATION_PASS
AUTHORITY_EFFECT=NONE
PHYSICAL_NODE_ACTIVATION_CLAIMED=false
NETWORK_ACTIVATION_CLAIMED=false
```

The non-authorizing observation receipt was uploaded as artifact `stegos-node-public-observation-34617268914-1`, artifact ID `10270802544`, digest `sha256:023a1af3e71b1591574cccdd576e8b5991e440206617e79bfd22b351c231c2f4`.

This satisfies `LIVE_SOURCE_PROPAGATION_OBSERVED_BEFORE_RUNTIME_REOBSERVATION`. It does not establish authentic execution of the repaired browser-local state.

## StegBrowser runtime-observation binding

StegBrowser PR `StegVerse-Labs/StegBrowser#35` binds the repository's existing Playwright-capable runtime to reusable component `RTC-BROWSER-LOCAL-STATE-SCHEMA-MIGRATION-V1` for this Goal Task.

The initial implementation head `6dabe45d051a68c8a87e336dec6662092327068b` passed Validate run `34736996551`. The task-specific README was then reconciled on the same PR branch at head `ad470c01a33136abb3fca3c54188de3fea5966b7`, and exact-head Validate run `34737855784` completed successfully.

PR #35 was squash-merged to StegBrowser `main` at `0dd96a39ccc17a9eb0361e1eb975ad6dc542d87e` after the successful exact-head validation. The binding is therefore integrated in canonical source.

The binding remains non-authorizing source-level runtime-observation plumbing. Merge and CI do not substitute for authentic browser-local runtime evidence and do not satisfy the Goal Task completion predicate.

## Current next transition

`REQUEST_AUTHENTIC_INTERCHANGEABLE_NODE_RUNTIME_REOBSERVATION`

No named device is required. Any compatible interchangeable StegOS browser execution node may satisfy the remaining runtime predicate by authentically opening a qualifying browser-local continuity state under the merged repair and demonstrating that the missing-object-store failure is absent while required continuity records remain preserved.

A device/node identity remains execution/transport context only and cannot substitute for KV/SKAP user verification.

## Remaining completion predicate

`AUTHENTIC_INTERCHANGEABLE_NODE_RUNTIME_NO_MISSING_OBJECT_STORE_FAILURE`

The Goal Task remains ACTIVE until authentic compatible-node runtime evidence demonstrates the repaired database state. Source, CI, and public-source observation cannot substitute for authentic runtime execution. The evidence is not tied to the device on which the original defect was observed.

After the repair is confirmed, control returns to `SS-EVIDENCE-COMPARISON-001` for the parent ERL standard flow. No ERL admission, exact ERL readback, StegSocials draft save/readback, or evidence export is claimed by this handoff.

Issue: `StegVerse-Labs/Site#1233`
