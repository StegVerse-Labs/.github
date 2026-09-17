# StegBrowser Manifest Interlock/InTr Ingress Execution Mirror Handoff

Updated: 2026-09-17

- Goal Task ID: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT`
- Reusable owner: `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001`

## Canonical execution path

```text
manifest
-> StegVerse Node
-> Interlock
-> InTr materialization
-> bounded invocation lease
-> EVENT_EPHEMERAL StegOS runtime
-> execution-time runtime identity
-> WorkerCoordinator claim/fence
-> authentic governed ingress
-> Round Trip 1
-> Master Records record/reconstruct/process
-> Round Trip 2
```

No route, endpoint, receiver, external host, external device, standing runtime, or generic process-host discovery stage exists.

## StegVerse-002 connection parts imported as reusable components

The successful SV002 experiment is the implementation precedent for A1 through A2.2. Historical Site paths are provenance only; Site is not a runtime owner or required Goal Chart stage.

A1 reuses registered-node continuity and Receipt #1 binding from the proven SV002 lane. Retain exact `node_id`, `interlock_id`, genesis/device commitment, manifest, Goal, and COSV correlation.

A2 reuses the Node-bound Interlock and non-authorizing Universal InTr materialization mechanics: build the exact request, queue it into the write-once Node InTr outbox, submit the governed transition, and require authentic InTr admission. The request grants no execution authority and mints no claim/fence.

A2.1 reuses the invocation-scoped bounded lease created only after InTr admission. The lease binds Node + Interlock + materialization + manifest + Goal + COSV and creates no standing host/runtime relationship.

A2.2 reuses the admitted-event materializer from SV002: materialize `EVENT_EPHEMERAL_STEGOS`, then bind execution-time `runtime_id` to the same Node/Interlock/InTr/lease/manifest/Goal/COSV correlation. No pre-existing runtime or external host is required.

Proven source provenance:

- `StegVerse-Labs/Site:assets/stegverse-node-continuity-impl.js`
- `StegVerse-Labs/Site:assets/evaluator-intr-connector.js`
- `StegVerse-Labs/Site:stegos-node/sv002-intr-sync.js`
- `StegVerse-Labs/Site:assets/sv002-local-runtime-materializer.js`
- `StegVerse-Labs/Site:assets/sv002-principal-worker.js`

The reusable contract is now encoded in `source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json`.

## Ordering after connection materialization

A3 WorkerCoordinator claim/fence occurs after the EVENT_EPHEMERAL runtime identity is bound. WorkerCoordinator does not create the event, materialization, lease, or runtime.

A4 must correlate the same Node, Interlock, materialization, lease, runtime, manifest, Goal, COSV, claim ID, and fencing token before `ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED` or `AUTHENTIC_INTR_INGRESS_OBSERVED` may become true.

## Required reusable sequence

```text
MANIFEST_BOUND_TO_INVOCATION
-> STEGVERSE_NODE_BOUND_TO_INVOCATION
-> INTERLOCK_BOUND_TO_NODE_AND_MANIFEST
-> INTR_MATERIALIZATION_ADMITTED
-> INVOCATION_SCOPED_LEASE_ESTABLISHED
-> EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED
-> EXECUTION_TIME_RUNTIME_IDENTITY_BOUND
-> CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED
-> ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED
-> AUTHENTIC_INTR_INGRESS_OBSERVED
-> Round Trip 1
-> mirror-boundary processing
-> Round Trip 2
```

No new reusable task is required.

## Immutable invocation

```text
canonical request commit = 19935454cd8c68000b3a0fd70478b0d89d5cd622
nonce = STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z
requested invocation count = 1
destination = StegBrowser:ManifestInvocation
COSV = 40000100100000
```

No second request and no mutation of the existing nonce/payload are allowed.

## Current authentic state

A0 is source-bound with runtime confirmation pending. A1, A2, A2.1, A2.2, A3, and A4 remain not authentically observed for the current invocation. Round Trip 1 and Round Trip 2 have not been entered. Historical SV002 evidence, source state, CI, or architecture precedent cannot promote current runtime predicates.

## Retained-evidence seam repair — 2026-09-17

Canonical re-observation again found no retained authority-owned same-nonce A1/A2/lease/EVENT_EPHEMERAL receipt set. The existing runtime-connection observer already writes `receipts/sovereign-host/stegbrowser-runtime-connection-transition-observation.latest.json` and `receipts/sovereign-host/stegbrowser-runtime-connection-resolution.latest.json`, but its final A1-A4 observation path contained two evidence-integrity defects:

1. when the canonical registered Node Receipt #1 was unavailable, `resolve_registered_node_receipt(...)` raised before `receipts/sovereign-host/stegbrowser-runtime-connection-a1-a4.latest.json` could be retained;
2. a callable InTr profile could label the final observation `A1_OBSERVED...` even though no registered Node binding had been retained.

The bounded repair on branch `stegbrowser-runtime-evidence-retention-failclosed-20260917` changes only this evidence-retention seam. It catches only the missing canonical Node-receipt condition, retains it as `node_resolution_error`, writes the final observation anyway, and uses fail-closed states beginning with `A1_NOT_OBSERVED...`. `registered_stegverse_node_bound_to_invocation` becomes true only when the authority-owned boundary contains the correlated Node/Interlock/registration binding. Lease and EVENT_EPHEMERAL predicates remain downstream of that authentic A1 binding.

This repair creates no Node, host, endpoint, runtime, listener, scheduler, dispatcher, WorkerCoordinator, second invocation, second device, or authority path. It does not turn source/CI evidence into runtime evidence and does not activate Round Trip 1. The invariant remains: a missing authentic receipt must be durably observable as missing, never promoted and never lost because observation terminated early.

README reviewed for this repair. No byte change is required because public architecture/topology is unchanged; this is an internal fail-closed evidence-retention correction.

## Authority map

Manifest = route declaration only. Node = continuity/admission anchor. Lease = bounded invocation scope only. EVENT_EPHEMERAL StegOS = compute/execution surface. WorkerCoordinator = claim/fence authority. Interlock/InTr = transition and governed packet-movement authority. TV/TVC = credential authority. Master Records = custody/reconstruction authority, not transport authority. GitHub/CI runtime authority = `NONE`. Healer remains exception/remediation only.

## Next execution boundary

Validate and merge the fail-closed retained-evidence repair. Then re-observe the existing same-nonce runtime path. If the retained A1-A4 observation reports an authentic registered Node binding, continue only through the existing Interlock/InTr -> bounded lease -> EVENT_EPHEMERAL -> WorkerCoordinator -> A4 chain and write every authentic governed transition through Master Records. If it reports `A1_NOT_OBSERVED...`, repair only the exact native Node-evidence exposure condition named by that retained record. Enter Round Trip 1 only after authentic A4.
