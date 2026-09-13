# Site ECE Publication Binding Reconciliation

Updated: 2026-09-13
Goal Task ID: `SITE-ECE-CURRENT-PROJECTION-MATERIALIZER-001`
COSV: `71000000102000`
Publication owner: `SITE-PUBLICATION-NATIVE-RUNTIME-EXECUTION-001` / COSV `50000000102000`
Status: `SOURCE RECONCILED / RUNTIME PREDICATES UNCHANGED`

## Purpose

Reconcile the ECE current-projection materializer with the merged fail-closed Site publication candidate binding from `.github` PR #1767 without changing runtime truth or adding another publication/runtime mechanism.

## Merged publication repair

PR #1767 exact head `de86af37d00172cff393b1ccc2aaca527e2edb27` passed:

- Deterministic Repository Suite `34781655303`.
- Organization Control `34781655347`.
- Heartbeat Worker Project `34781655362`.

It squash-merged at `1d10dd97475c910de83847f7e5344e387dd81cf7`.

The Site publication WorkerCoordinator child now resolves the opaque materialization id from authentic local Universal InTr ingress evidence:

```text
receipts/sovereign-network/site-publication-intr-ingress.latest.json
-> exact queue_ref
-> intr-materialization/<materialization_id>.json
```

The ingress receipt remains non-authorizing. WorkerCoordinator still owns fresh claim/fence authority. An optional `STEGVERSE_SITE_PUBLICATION_MATERIALIZATION_ID` may correlate the candidate but cannot substitute for the local admitted receipt and must match it when present.

## ECE binding

`SITE-ECE-CURRENT-PROJECTION-MATERIALIZER-001` continues to consume only:

1. `RTC-EVIDENCE-CUSTODY-004` — Master Records exact custody/reconstruction.
2. `RTC-PUBLISHER-005` — canonical publication owned by `SITE-PUBLICATION-NATIVE-RUNTIME-EXECUTION-001`.
3. Canonical runtime observation — independent served-byte/page observation.

The ECE-specific exact-byte materializer remains the adapter for `RTC-PUBLISHER-005`; it is not a second publication owner. No source-repository writeback path is introduced.

## Current authentic continuation

```text
RT-ECOSYSTEM-CONTINUITY-EVALUATION-001 authentic cycle
-> Master Records exact ECE custody/reconstruction
-> Site-safe projection
-> ECE exact-byte materializer binding
-> RT-SOVEREIGN-SOURCE-REFRESH-001 authentic child receipt for publication owner
-> authentic Universal InTr Site-publication ingress receipt + write-once queue
-> fresh WorkerCoordinator claim/fence for SITE-PUBLICATION-INTR-CONSUMER-001
-> candidate validation under that fence
-> bounded EVENT_EPHEMERAL publication lease
-> independent public HTTPS byte/path observation
-> lease closure + final Interlock/InTr publication transition
-> Master Records publication evidence custody/reconstruction
-> independently observe served data/ecosystem-continuity/current.json and continuity page
```

Neutral reusable scheduling may carry the source-refresh invocation; it grants no authority and does not satisfy a runtime predicate by itself.

## Runtime truth

No authentic scheduler/source-refresh receipt or Site-publication ingress receipt was found in the connected retained evidence surface immediately after #1767 merged. Public StegVerse homepage reachability is independently observed, but exact ECE `current.json` materialization and continuity-page rendering remain unproven.

The Goal-specific predicates remain exactly:

1. `AUTHENTIC_SITE_SAFE_PROJECTION_MATERIALIZED`.
2. `SITE_LIVE_CONTINUITY_PROJECTION_OBSERVED`.

No device-verification policy/process, device identity gate, second user-operated device, hosted-runtime substitute, or synthetic evidence is introduced by this reconciliation.
