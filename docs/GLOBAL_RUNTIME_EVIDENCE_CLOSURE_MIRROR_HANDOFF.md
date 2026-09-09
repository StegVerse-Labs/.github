# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
Canonical PR: `StegVerse-Labs/.github#1261` (merged) plus current repair branch `fix/global-runtime-selector-convergence-1260`
COSV: `50000000100000`
Status: `ACTIVE / PROFILE_DERIVED_PERSISTENT_NODES / EPHEMERAL_EXECUTION_AND_TRANSPORT / SOURCE_DEVICE_HB_LINEAGE_IMPLEMENTED_IN_STEGBROWSER / STEGOS_RECEIPT_HOOK_IMPLEMENTED_SOURCE / AUTHENTIC_RETAINED_NODE_AND_CONVERGENCE_RECEIPTS_PENDING`

## Purpose

Converge all StegVerse ecosystem capabilities that are implemented or integration-ready but still require authentic runtime execution/evidence, receipt custody, reconstruction, runtime-bound validation, or downstream propagation proof. The umbrella preserves child Goal Task IDs and resumes each child from its first genuinely unresolved evidence predicate instead of restarting completed stages.

## Canonical registration

The umbrella is registered under issue #1260 and merged source from PR #1261. The task record remains `ACTIVE / CLAIMED_INTEGRATION` with task.v1 COSV `50000000100000`.

## Reusable solution model

The ecosystem-wide composite runtime class is `PERSISTENT_NODE_EPHEMERAL_EXECUTION`.

Runtime profiles are reusable definitions. Individual components materialize specific StegOS node instances from the applicable profile. Node identity, genesis, continuity generation, committed non-secret state, admitted evidence commitments, and source-device HB lineage persist. Task execution, WorkerCoordinator claim/fence lifecycles, Interlock/InTr invocations, transports, provider/browser/model/action sessions, credentials, and temporary execution processes remain bounded and ephemeral.

```text
runtime / node profile
  -> component-specific StegOS node instance
       - stable node identity
       - genesis commitment
       - continuity generation
       - non-secret state commitment
       - admitted evidence commitments
       - immutable source-device HB root reference
       - append-only HB/evidence transition history

for each bounded operation:
  -> ephemeral task/request manifestation
  -> ephemeral WorkerCoordinator claim/fence lifecycle
  -> ephemeral Interlock/InTr invocation
  -> ephemeral data transport
  -> ephemeral provider/browser/model/action session
  -> component execution
  -> exact result/readback/receipt
  -> admitted evidence + HB transition lineage advance node state
  -> transient execution/transport/session state destroyed
  -> node instance remains for the next operation
```

Cross-task evidence remains subject-bound; mechanism reuse does not make one task's receipt evidence for another task.

## Source-device HB lineage invariant

Canonical umbrella contract:

`control/stegos-node-hb-lineage-contract.json`

The reference HB from the source device propagates outward with node lineage. A profile-derived node remains aware of the originating source-device HB reference and retains append-only transition history relating subsequent transitions back to that root. A later transition adds a fresh current HB observation but may not replace the immutable source-device HB root.

HB remains non-authorizing. The lineage grants no execution, claim/fence, Interlock/InTr admission, credential, custody, publication, or completion authority.

## StegBrowser durable-node implementation

StegBrowser PR #33 has now merged at:

`bbb8075298d2e7b309aafd5507d6a7a6ad118a18`

The merged retained node schema `stegbrowser.resident-node-state/v2` implements:

- explicit runtime-profile binding;
- immutable source-device HB reference;
- append-only transition history;
- fresh current-observed HB reference per transition;
- task/request/COSV references when applicable;
- Interlock/InTr transition reference when applicable;
- result and state commitments;
- prior-transition and transition commitments;
- fail-closed reconstruction on node/profile/source-HB/history substitution.

StegBrowser exact-head validation run `34378439457` completed `SUCCESS` before merge. Browser cookies, provider sessions, credentials, history, and temporary page state remain excluded from retained node state.

## StegOS compiled/mobile implementation

StegOS PR #310 remains open on `feat/source-device-hb-lineage`.

The compiled node bootstrap in `mobile/ios/StegOSMobile/StegBrowserResidentNodeBootstrap.swift` implements the same persistent profile-derived node semantics and canonical HB32 source-root derivation.

The generic transition path in `stegos/heartbeat_protocol_sample.py` creates `stegos.node-heartbeat-lineage/v1` and propagates a non-authorizing source-device HB root plus fresh current observation outward through transition packets while preserving `heartbeat_payload_included=false`, `heartbeat_grants_authority=false`, and `authority_effect=NONE`.

### Current-iPhone receipt -> retained transition hook

The previously missing source hook is now implemented in `SV001ResidentActivationController.persistRuntimeReceipt`.

For one exact loopback discovery observation the code now:

1. loads the already-retained profile-derived StegBrowser node;
2. refuses node-reference drift;
3. derives the exact current canonical HB reference at one observation time;
4. writes profile, immutable source HB, current HB, task, COSV, node, discovery result, and non-authority semantics into the receipt body;
5. computes the exact receipt-body SHA-256;
6. derives the next state commitment from prior node state + exact receipt digest + source/current HB + task/COSV/session identity;
7. calls `appendTransition` using the receipt digest as `resultCommitment` and the same observation time;
8. verifies the resulting transition preserves exact source/current HB, receipt digest, and next state commitment;
9. persists the receipt envelope with retained-node generation, state commitment, transition sequence, transition commitment, and an envelope SHA-256.

Canonical reconstruction shape is now:

```text
exact loopback observation
-> exact receipt body digest
-> retained node appendTransition(result_commitment = receipt digest)
-> append-only transition commitment
-> receipt envelope references resulting transition commitment
```

This is source/build implementation, not authentic current-iPhone runtime proof.

## Exact-head validation state

On StegOS head `e10cceb9bf5eb2d3128056029e617728f5fed40e`:

- StegOS CI run `34379628347`: `SUCCESS`;
- iOS Device Package Validation `34379628253`: `SUCCESS`;
- iOS Apple Toolchain Validation `34379628365`: `IN_PROGRESS` at last observation.

The StegOS README still contains an older paragraph saying the application target binds a Site-provided node identity. That paragraph is now stale relative to the compiled source and is a merge-blocking documentation defect until reconciled. PR #310 must not be merged while that contradiction remains.

## Corrected routing

The convergence routing preserves:

- VACC current task identity: `VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023`;
- Endpoint Fanout through existing `stegos_kv_intr_chain`;
- GADI through its existing bounded preflight/consumer route;
- DE-006 through the existing Ecosystem Chat parent continuation path;
- StegClaw through the shared runtime-presence projector plus subject-specific continuation;
- Runtime Profile Map as the convergence diagnostic trigger.

Current VACC still requires its exact resident bridge before an authentic measured 18-member convergence run removes that artificial integration condition.

## Failure-frontier overlay

Machine-readable projection remains:

`control/global-runtime-failure-frontier-overlay.json`

Projected first-frontier counts after authentic persistent-node continuity and VACC bridge remain:

```text
persistent-node continuity             0
exact ephemeral request consumption    5
WorkerCoordinator claim/fence          2
ephemeral Interlock/InTr admission     1
ephemeral transport/provider/lease     2
component execution/re-execution       8
receipt commitment                     0
Master Records reconstruction          0
propagation                             0
```

The HB-lineage implementation sharpens cross-node subject/time correlation but does not by itself promote any lane to a later authentic runtime stage.

## Authentic proof target

```text
source-device HB root observed
-> runtime profile materializes component-specific StegOS node instance
-> node retains immutable source-device HB root
-> ephemeral governed operation executes with fresh current HB observation
-> exact receipt digest advances persistent node transition history
-> receipt envelope references resulting transition commitment
-> ephemeral transport/session destroyed
-> same node remains
-> later independent operation binds to same node
-> transition history reconstructs to original source-device HB root
```

Transient browser/provider/transport credentials or session state must not persist merely because the node and its evidence lineage persist.

## Next machine work

1. complete StegOS #310 Apple-toolchain validation on exact head `e10cceb9...`;
2. reconcile the stale StegOS README current-iPhone node-origin paragraph;
3. re-run exact-head deterministic/device-package/Apple-toolchain gates after README reconciliation;
4. merge StegOS #310 only when all exact-head gates are clean and README/source semantics agree;
5. finish VACC exact resident bridge;
6. propagate profile-derived node/HB-lineage semantics into remaining component-specific node materializers/receipt emitters that do not already inherit the generic transition path;
7. obtain authentic current-iPhone retained-node/source-HB/receipt-to-transition evidence;
8. execute Runtime Profile Map + global convergence visitor and compare measured frontiers with `control/global-runtime-failure-frontier-overlay.json`;
9. reconcile successful node/HB/execution receipts into Master Records and downstream propagation tasks.

## Manual work

None while source/build integration and validation remain machine-executable.
