# StegBrowser Current-iPhone A1-A4 Execution Mirror Handoff

Updated: 2026-09-16
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `STEG-BROWSER-CURRENT-IPHONE-A1-A4-EXECUTION-001`
- Parent Goal: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / AUTHENTIC SAME-IPHONE A1-A4 EXECUTION PENDING`

## Immutable invocation

Reuse only the already-issued request:

```text
source goal = STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001
canonical request commit = 19935454cd8c68000b3a0fd70478b0d89d5cd622
nonce = STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z
requested invocation count = 1
destination = StegBrowser:ManifestInvocation
COSV = 40000100100000
```

Do not emit a second request or mutate the nonce/payload.

## Current-device execution surface

Use the already-merged Site current-iPhone surface:

```text
https://stegverse.org/stegos-bootstrap/canonical-work-runtime-consumption.html?autostart=1
```

It must be opened in the same non-private Safari site-data context that owns the registered StegVerse Node. Do not clear site data.

The merged source repair behind this surface is Site PR #1360, exact validated head `d031a1c560814a1c1cd275656925258cee11f323`, merged as `76af62f2befdfa7034d3dd00891bfe60a0990abb`. Site handoff PR #1361 merged as `7c483335f259d5eacf9a55dde923c0c4fefd660e`. The invalid claim-only terminalization PR #1362 was closed without merge.

## Required authentic chain

```text
registered Node Receipt #1
-> deterministic unchanged-nonce Node outbox entry
-> StegBrowser:ManifestInvocation Universal InTr materialization
-> write-once INGRESS_ADMITTED
-> bounded invocation lease
-> EVENT_EPHEMERAL runtime identity
-> WorkerCoordinator claim/fence
-> exact governed StegBrowser A4 ingress
```

Promote only predicates directly proven by authority-owned, same-invocation evidence with exact Goal/COSV/nonce/manifest/node/interlock/materialization/lease/runtime/claim/fence correlation.

## Current authentic predicates

All remain false until exact page/runtime evidence proves them:

```text
REGISTERED_STEGVERSE_NODE_BOUND_TO_INVOCATION = false
INTERLOCK_BOUND_TO_NODE_AND_MANIFEST = false
INTR_MATERIALIZATION_ADMITTED = false
INVOCATION_SCOPED_LEASE_ESTABLISHED = false
EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED = false
EXECUTION_TIME_RUNTIME_IDENTITY_BOUND = false
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = false
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED = false
AUTHENTIC_INTR_INGRESS_OBSERVED = false
A1_A4_COMPLETE = false
```

## Failure handling

If the returned page JSON is fail-closed or stops before A4, repair only the first authentic transition failure exposed by that evidence. Do not add a second listener, scheduler, dispatcher, materializer, WorkerCoordinator, runtime plane, credential authority, or second user-operated device.

## Completion transition

Only after authentic A1-A4 completion is proven may `STEG-BROWSER-GOVERNED-ROUNDTRIP-001` be activated. Until then, Round Trip 1 remains unstarted.

## README review

README remains accurate; no byte change is required because the runtime/authority topology is unchanged.

## Manual work

On the same iPhone/Safari context that owns the registered StegVerse Node, open `https://stegverse.org/stegos-bootstrap/canonical-work-runtime-consumption.html?autostart=1` without Private Browsing and without clearing site data. Return the complete displayed JSON exactly, or the exact `FAIL_CLOSED` reason unchanged.
