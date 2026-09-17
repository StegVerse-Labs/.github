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

The reusable contract is encoded in `source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json`.

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

A0 is source-bound with runtime confirmation pending. A1, A2, A2.1, A2.2, A3, and A4 remain not authentically observed for the current invocation. Round Trip 1 and Round Trip 2 have not been entered. Historical SV002 evidence, source state, CI, repository absence of a runtime receipt, or architecture precedent cannot promote current runtime predicates.

## Retained-evidence seam repair — merged 2026-09-17

Canonical re-observation had found no retained authority-owned same-nonce A1/A2/lease/EVENT_EPHEMERAL receipt set. The runtime-connection observer writes `receipts/sovereign-host/stegbrowser-runtime-connection-transition-observation.latest.json` and `receipts/sovereign-host/stegbrowser-runtime-connection-resolution.latest.json`, but its final A1-A4 observation path contained two evidence-integrity defects:

1. when the canonical registered Node Receipt #1 was unavailable, `resolve_registered_node_receipt(...)` raised before `receipts/sovereign-host/stegbrowser-runtime-connection-a1-a4.latest.json` could be retained;
2. a callable InTr profile could label the final observation `A1_OBSERVED...` even though no registered Node binding had been retained.

The bounded repair changes only this evidence-retention seam. It catches only the missing canonical Node-receipt condition, retains it as `node_resolution_error`, writes the final observation anyway, and uses fail-closed states beginning with `A1_NOT_OBSERVED...`. `registered_stegverse_node_bound_to_invocation` becomes true only when the authority-owned boundary contains the correlated Node/Interlock/registration binding. Lease and EVENT_EPHEMERAL predicates remain downstream of that authentic A1 binding.

The repository-wide MIR Admissible-Existence and validation-drift prerequisite was reconciled in PR #2048. Exact-head Deterministic Repository Suite, Organization Control, and Heartbeat validation all passed, and PR #2048 merged with expected-head protection at `cf81378f296458f0458fe1eb33920e337f4e5f21`.

The StegBrowser repair was then rebased as exactly one commit and exactly three changed files onto that canonical main. Exact-head Deterministic Repository Suite, Organization Control, and Heartbeat validation all passed, the current-main collision check remained clean, and PR #2047 merged with expected-head protection at `4888b63b5b72fd7930177e33a2548b1a98f7240c`.

This repair creates no Node, host, endpoint, runtime, listener, scheduler, dispatcher, WorkerCoordinator, second invocation, second device, or authority path. It does not turn source/CI evidence into runtime evidence and does not activate Round Trip 1. The invariant remains: a missing authentic receipt must be durably observable as missing, never promoted and never lost because observation terminated early.

Post-merge runtime re-observation from the execution interfaces available to this continuation did not expose an authorized runtime context from which the retained `stegbrowser-runtime-connection-a1-a4.latest.json` could be read. The receipt is not tracked repository state, so its absence from GitHub is not evidence of `A1_NOT_OBSERVED`. No A1-A4 predicate was promoted or denied from that repository observation.

README was reviewed for this repair. No byte change is required because public architecture/topology is unchanged; this is an internal fail-closed evidence-retention correction.

## Native Receipt #1 invocation-context exposure repair — 2026-09-17

Re-verification of the canonical resident request and the existing resident dispatcher identified a source-level exposure defect in the already-registered native path. The request contract requires the concrete Receipt #1 path through environment locator `STEGVERSE_NODE_GENESIS_RECEIPT`, while `scripts/dispatch_resident_execution_requests.py` rebuilds a non-secret child execution environment and did not forward that locator. A valid caller context could therefore hold the registered Node receipt while the exact StegBrowser consumer received no Receipt #1 path and could only fail closed before authentic A1 binding.

The bounded repair on branch `stegbrowser-native-node-receipt-exposure-20260917` changes only the existing resident-dispatch environment contract and its focused regression coverage:

- `STEGVERSE_NODE_GENESIS_RECEIPT` is admitted to the dispatcher's non-secret locator allowlist;
- credential-bearing GitHub environment remains stripped and GitHub runtime authority remains `NONE`;
- the dispatcher recognizes the retained-observer v2 A1/A2.1/A2.2/A3/A4 states, including all `A1_NOT_OBSERVED...` states, without converting them into authority or completion;
- the existing `stegbrowser_runtime_connection_ingress` consumer registration remains the sole child execution path;
- the immutable invocation nonce and existing request are unchanged; no second request, second dispatcher, runtime, host, endpoint, listener, scheduler, device, credential path, or authority path is created.

This source repair does not prove that Receipt #1 exists in a current invocation context and does not promote A1. Its purpose is narrower: when an authentic StegVerse-native invocation already has the canonical registered Node Receipt #1 locator, the existing dispatcher no longer removes that locator before invoking the already-registered StegBrowser consumer.

## Authority map

Manifest = route declaration only. Node = continuity/admission anchor. Lease = bounded invocation scope only. EVENT_EPHEMERAL StegOS = compute/execution surface. WorkerCoordinator = claim/fence authority. Interlock/InTr = transition and governed packet-movement authority. TV/TVC = credential authority. Master Records = custody/reconstruction authority, not transport authority. GitHub/CI runtime authority = `NONE`. Healer remains exception/remediation only.

## Next execution boundary

Validate and merge the bounded native Receipt #1 exposure repair. Then re-observe the authority-owned retained runtime record `receipts/sovereign-host/stegbrowser-runtime-connection-a1-a4.latest.json` for immutable nonce `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z` through the existing StegVerse-native invocation path. If that record authenticates A1, continue only through the existing Interlock/InTr -> bounded lease -> EVENT_EPHEMERAL -> WorkerCoordinator A3 -> exact-correlated A4 path, recording every observed governed transition through canonical Master Records custody before entering Round Trip 1, B1, and Round Trip 2. If the record reports `A1_NOT_OBSERVED...`, repair only the exact remaining native exposure condition in `node_resolution_error`. Do not infer either outcome from source, CI, GitHub repository state, or an unavailable execution context.