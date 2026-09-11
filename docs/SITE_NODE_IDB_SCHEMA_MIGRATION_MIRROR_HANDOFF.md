# Site Node IndexedDB Schema Migration Mirror Handoff

Goal Task ID: `SITE-NODE-IDB-SCHEMA-MIGRATION-001`
Parent Goal Task ID: `SS-EVIDENCE-COMPARISON-001`
COSV: `40000100100000`
Status: `ACTIVE / CLAIMED_INTEGRATION`

## Trigger

Authentic current-iPhone execution after the iOS synchronous picker repair produced an independent DEVICE_KV directory-readback failure:

```text
Failed to execute 'transaction' on 'IDBDatabase': One of the specified object stores was not found.
```

The same screen still exposed the registered-Node resident action, so registration/Receipt #1 continuity remained readable. The repair therefore had to preserve the existing browser-local Node identity while repairing the shared `stegos-node-v1` schema.

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

This satisfies the task predicate `LIVE_SOURCE_PROPAGATION_OBSERVED_BEFORE_IPHONE_RETRY`. It does not establish repaired physical-device execution.

## Current next transition

`REQUEST_SINGLE_CURRENT_IPHONE_RETRY`

Exactly one current-iPhone ERL retry is now permitted. Preserve existing Safari/site storage and the existing Node registration/Receipt #1. Do not clear storage or re-register the Node.

The retry should open the current ERL directory, reload once, tap `Import owner-controlled files` once, and report the resulting state. If the native Files sheet opens, select the intended OpenAI ERL Markdown artifact and wait for canonical admission/readback before preparing a post.

## Remaining completion predicate

This task remains ACTIVE until authentic current-iPhone execution demonstrates the repaired database state. Source/CI/live-site observation cannot substitute for that device-local result.

No ERL admission, exact ERL readback, StegSocials draft save/readback, or evidence export is claimed yet.

Issue: `StegVerse-Labs/Site#1233`
