# StegBrowser Manifest Interlock/InTr Ingress Execution Mirror Handoff

Updated: 2026-09-15
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / STEGVERSE-002 EVENT_EPHEMERAL SOURCE IDENTIFIED / STEGBROWSER UNIVERSAL-INTR MATERIALIZATION BINDING REQUIRED / AUTHENTIC A1-A4 EVIDENCE PENDING`
- Issue `#1918`: remains closed; its generic-process-host premise is invalid under the validated StegVerse-002 event-ephemeral architecture.

## Correct source of truth

The validated source documentation and implementation for the invocation-owned runtime architecture is the StegVerse-002 experiment, specifically:

- `docs/SV002_EVENT_EPHEMERAL_OBSERVATION_MIRROR_HANDOFF.md`
- `workers/universal_intr_profiled_ingress.py`
- `workers/sv002_intr_materialization_consumer.py`
- `workers/sv002_observation_esrl_runtime_bridge.py`
- `tests/test_sv002_event_ephemeral_materialization.py`

That implementation establishes the reusable architecture:

```text
valid StegVerse Node
-> exact local request
-> stegverse.universal-intr-transport/v1 intent
-> stegverse.universal-intr-materialization-request/v1
-> node-bound write-once InTr trigger
-> shared /intr/materialization ingress
-> write-once INGRESS_ADMITTED receipt
-> credential-scrubbed non-authorizing consumer dispatch
-> StegOS EVENT_EPHEMERAL runtime materialization
-> bounded lease state
-> existing WorkerCoordinator targeted execution
```

Authority remains unchanged:

```text
materialization request execution authority = NONE
ingress execution authority = NONE
ingress claim/fence minting = false
consumer claim/fence minting = false
WorkerCoordinator claim/fence authority = true
Interlock/InTr transition authority = true
TV/TVC credential authority = true
GitHub runtime authority = NONE
always-on receiver prerequisite = false
second user machine prerequisite = false
```

## Correction to the prior StegBrowser interpretation

The prior continuation incorrectly treated these as runtime prerequisites:

```text
control-plane source-package relay
resident source localization
resident-request sweep consumption
profile polling until A1 appears
```

They are not the architecture defined by the validated StegVerse-002 experiment.

PR `#1941` remains valid historical source-localization work, but source-package relay/localization is not a prerequisite to Node -> Universal InTr materialization for this Goal.

The resident request `RESIDENT-EXEC-STEGBROWSER-RUNTIME-CONNECTION-INGRESS-001` may remain as a coordination projection, but its sweep consumption is not the authority-bearing event that creates the runtime path.

## Canonical StegBrowser path

```text
A0 manifest/path binding
-> A1 registered StegVerse Node binding + Node-bound materialization intent
-> A2 shared Universal Interlock/InTr /intr/materialization admission
-> A2.1 bounded invocation lease/state binding
-> A2.2 EVENT_EPHEMERAL StegOS materialization
-> A3 WorkerCoordinator claim/fence
-> A4 exact governed StegBrowser manifest ingress
-> Round Trip 1
-> Master Records / mirror processing
-> Round Trip 2
-> ecosystem re-entry
```

No external runtime/device/host discovery stage exists. No always-on process or waiting external machine is required.

## Current implementation mapping

Already existing and reusable:

```text
Shared Node/InTr materialization architecture:
  workers/universal_intr_profiled_ingress.py

Validated EVENT_EPHEMERAL consumer pattern:
  workers/sv002_intr_materialization_consumer.py
  workers/sv002_observation_esrl_runtime_bridge.py

StegBrowser downstream manifest/runtime implementation:
  scripts/run_stegbrowser_manifest_bound_runtime.py
  scripts/run_stegbrowser_runtime_consumption_reusable.py
  workers/stegbrowser_manifest_intr_ingress.py

Worker claim/fence:
  existing WorkerCoordinator targeted execution path
```

The exact source-level gap is now bounded to one thing:

`Bind the StegBrowser manifest invocation to the existing shared Universal InTr materialization route using the already-validated StegVerse-002 pattern, then dispatch the already-existing StegBrowser downstream runner.`

This does not authorize a second listener, runtime, scheduler, dispatcher, materializer, WorkerCoordinator, host path, or device path.

## Current authentic predicates

```text
SV002_RUNTIME_ARCHITECTURE_SOURCE_IDENTIFIED = true
SV002_SHARED_UNIVERSAL_INTR_IMPLEMENTATION_IDENTIFIED = true
SV002_EVENT_EPHEMERAL_IMPLEMENTATION_IDENTIFIED = true
CONTROL_PLANE_SOURCE_PACKAGE_IS_RUNTIME_PREREQUISITE = false
RESIDENT_REQUEST_SWEEP_IS_RUNTIME_PREREQUISITE = false
STEGBROWSER_UNIVERSAL_INTR_MATERIALIZATION_BINDING_COMPLETE = false
RUNTIME_CONNECTION_TRANSITION_VARIABLES_OBSERVED = false
STEGVERSE_NODE_BOUND_TO_INVOCATION = false
INTERLOCK_BOUND_TO_NODE_AND_MANIFEST = false
INTR_MATERIALIZATION_ADMITTED = false
INVOCATION_SCOPED_LEASE_ESTABLISHED = false
EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED = false
EXECUTION_TIME_RUNTIME_IDENTITY_BOUND = false
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = false
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED = false
AUTHENTIC_INTR_INGRESS_OBSERVED = false
ROUND_TRIP_1_STARTED = false
```

Current exact source condition:

`STEGBROWSER_UNIVERSAL_INTR_MATERIALIZATION_BINDING_NOT_YET_REUSED_FROM_VALIDATED_SV002_IMPLEMENTATION`

No runtime predicate is promoted from this architectural correction.

## Immediate continuation

Implement only the StegBrowser-specific adapter/binding into the already-existing shared `/intr/materialization` route, using the StegVerse-002 request/Node-trigger/write-once-ingress/non-authorizing-consumer pattern. The consumer must call the existing StegBrowser manifest-bound runner and preserve WorkerCoordinator as sole claim/fence authority. Then validate exact head. Authentic A1-A4 may be promoted only from execution receipts emitted by that corrected path.

## Manual work

None.
