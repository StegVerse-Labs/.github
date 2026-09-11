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

The same screen still exposed the registered-Node resident action, so registration/Receipt #1 continuity remained readable. Repository inspection shows the shared `stegos-node-v1` database is opened by multiple runtime modules with inconsistent fixed versions and upgrade ownership. `assets/stegverse-node-continuity.js` and `stegos-node/stegos-node.js` require `meta`, `receipts`, and `intr_outbox`, while DEVICE_KV/HIL sync paths also open the same database for metadata writes. A partial version advance can therefore leave a database whose version is current to the opener but whose canonical object-store set is incomplete.

## Required repair

1. Define one canonical `stegos-node-v1` schema version and complete store set: `meta`, `receipts`, `intr_outbox`.
2. Repair both authentic legacy shapes without deleting the database:
   - v1 containing `meta` + `receipts`;
   - malformed v2 containing `meta` + `receipts` but missing `intr_outbox`.
3. Preserve exact registration and Receipt #1 rows across migration.
4. Align every Site runtime opener of `stegos-node-v1` to the canonical current version so no lower fixed version can throw `VersionError` after migration and no partial opener can advance the version without creating the complete schema.
5. Add deterministic migration coverage for v1 -> current, malformed-v2 -> current, and current -> current reopen.
6. Update Site `README.md` and this handoff with exact merged commit/PR and validation evidence.
7. Verify live source propagation before requesting exactly one new current-iPhone ERL retry.

## Nonclaims

The screenshot does not by itself prove whether the native Files sheet visibly opened. No ERL admission, exact ERL readback, StegSocials draft save/readback, or evidence export is claimed. Do not clear Safari/site storage or re-register the Node; the existing local continuity state is part of the evidence that must be preserved.

## Current next transition

`IMPLEMENT_CANONICAL_NODE_DB_MIGRATION`

Issue: `StegVerse-Labs/Site#1233`
