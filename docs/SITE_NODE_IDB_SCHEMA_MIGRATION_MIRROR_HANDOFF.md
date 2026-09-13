# Site Node IndexedDB Schema Migration Mirror Handoff

Goal Task ID: `SITE-NODE-IDB-SCHEMA-MIGRATION-001`
Parent Goal Task ID: `SS-EVIDENCE-COMPARISON-001`
COSV: `40000100100000`
Status: `ACTIVE / CLAIMED_INTEGRATION`

## Canonical repair and propagation

Site PR `StegVerse-Labs/Site#1235` is merged at `a3bd73f0ced551738f37a6222b3ca933c3433fdf`. The repair defines `stegos-node-v1` version 3 with `meta`, `receipts`, and `intr_outbox`, migrates legacy v1 and malformed v2 additively, preserves registration and Receipt #1, and aligns runtime openers. Exact-head and post-merge Site validation passed.

Public observation run `34617268914` observed the live StegOS Node source and produced artifact `stegos-node-public-observation-34617268914-1` (artifact ID `10270802544`, digest `sha256:023a1af3e71b1591574cccdd576e8b5991e440206617e79bfd22b351c231c2f4`). This satisfies live source propagation only, not browser-local completion proof.

## StegBrowser runtime observation

StegBrowser PR #35 is merged at `0dd96a39ccc17a9eb0361e1eb975ad6dc542d87e`. Exact-head Validate run `34737855784` and post-merge Validate run `34737881539` passed. The merged observer seeds a controlled same-origin legacy v2 state, loads the live Site repair, and verifies version 3 stores, `intr_outbox` transaction availability, and continuity-record preservation. Source/CI execution remains non-authorizing.

StegBrowser PR #36 adds a fail-closed runtime evidence workflow and README documentation. It separates GitHub-hosted regression preflight from the compatible-node lane. The compatible-node lane requires runner labels `self-hosted` and `stegos-browser-node` plus a local runtime attestation bound to this Goal Task and COSV before it can emit completion-eligible evidence.

PR #36 exact head `88ac7d87950c3f5671f97a4b0f08a613661c445f` passed Validate run `34738049472`. The PR is open and mergeable. Merge attempts from the current tool surface were safety-gated, so no merge is claimed.

Remote Desktop Commander returned zero connected devices in this continuation. That is current execution-surface state only; no named device is required and device identity grants no user-verification authority.

## Current transition

`MERGE_STEGBROWSER_RUNTIME_EVIDENCE_LANE`

After merge, execute the compatible-node lane on any qualifying interchangeable StegOS browser node and retain the resulting evidence.

## Remaining completion predicate

`AUTHENTIC_INTERCHANGEABLE_NODE_RUNTIME_NO_MISSING_OBJECT_STORE_FAILURE`

The Goal Task remains ACTIVE until qualifying browser-local runtime evidence demonstrates that the missing-object-store failure is absent while required continuity records remain preserved and `intr_outbox` is transaction-accessible. CI, public-source observation, and GitHub-hosted preflight cannot substitute for that execution evidence.

After confirmation, control returns to `SS-EVIDENCE-COMPARISON-001` for the parent ERL standard flow. No ERL admission, exact ERL readback, StegSocials draft save/readback, or evidence export is claimed here.

Issue: `StegVerse-Labs/Site#1233`
