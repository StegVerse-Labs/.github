# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
Canonical PR: `StegVerse-Labs/.github#1261` (merged) plus current repair branch `fix/global-runtime-selector-convergence-1260`
COSV: `50000000100000`
Status: `ACTIVE / PROFILE_DERIVED_PERSISTENT_NODES / EPHEMERAL_EXECUTION_AND_TRANSPORT / SOURCE_DEVICE_HB_LINEAGE_IMPLEMENTATION_ACTIVE / STEGBROWSER_PR33 / STEGOS_PR310 / FAILURE_FRONTIER_OVERLAY_MATERIALIZED / AUTHENTIC_RETAINED_NODE_AND_CONVERGENCE_RECEIPTS_PENDING`

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

StegBrowser is the first concrete component implementation of this pattern. Cross-task evidence remains subject-bound; mechanism reuse does not make one task's receipt evidence for another task.

## Source-device HB lineage invariant

Canonical umbrella contract:

`control/stegos-node-hb-lineage-contract.json`

The reference HB from the source device propagates outward with node lineage. A profile-derived node remains aware of the originating source-device HB reference and retains append-only transition history relating subsequent transitions back to that root. A later transition adds a fresh current HB observation but may not replace the immutable source-device HB root.

HB remains non-authorizing. The lineage grants no execution, claim/fence, Interlock/InTr admission, credential, custody, publication, or completion authority.

## Runtime implementation now active

### StegBrowser PR #33

`StegVerse-Labs/StegBrowser#33` on `feat/source-device-hb-lineage` now implements retained node schema `stegbrowser.resident-node-state/v2` in `ios/StegBrowserResidentNodeStore.swift`.

Implemented retained fields include:

- profile reference;
- immutable source-device HB reference;
- append-only transition history;
- fresh current-observed HB reference per transition;
- task/request/COSV references when applicable;
- Interlock/InTr transition reference when applicable;
- result and state commitments;
- prior-transition and transition commitments.

Transition commitments are SHA-256 hash-linked and reload validation fails closed on node/profile/source-HB/history substitution. Browser cookies, provider sessions, credentials, history, and temporary page state remain excluded from retained node state.

PR #33 validation initially exposed handoff compatibility assertions rather than implementation defects. The first missing legacy status string was repaired at `a1b1f961edaaf1e949e29c0b56741770fff3659b`; the second was repaired at `d1f10004fa7cbf5ed559278c04a82ed4cc3b8500`. Exact-head validation run `34378267926` is queued after the second repair.

### StegOS PR #310

`StegVerse-Labs/StegOS#310` on `feat/source-device-hb-lineage` implements the compiled StegOSMobile side and generic outward InTr propagation.

`mobile/ios/StegOSMobile/StegBrowserResidentNodeBootstrap.swift` now:

- uses retained node schema v2;
- binds the node to `canonical-resident-substrate-v1/stegbrowser`;
- derives the source-device HB from the canonical HB32 protocol anchor (`epoch 32`, anchor Unix ms `1787511600000`, 10 ms period);
- persists the immutable source-device HB root at node materialization;
- exposes `appendTransition` to derive a fresh current HB observation and append a hash-linked transition record;
- validates node/profile/HB/COSV/result/state/prior-transition lineage on reload.

The generic StegOS transition path in `stegos/heartbeat_protocol_sample.py` now creates `stegos.node-heartbeat-lineage/v1` and requires transition packets to carry non-authorizing lineage containing:

```text
source_device_heartbeat_reference
current_observed_heartbeat_reference
protocol_anchor_source
reference_frequency_hz
reference_period_ms
propagation_direction = OUTWARD
heartbeat_payload_included = false
heartbeat_grants_authority = false
authority_effect = NONE
```

`stegos/real_peer_manifold_pipeline.py` and `scripts/build_real_ipod_current_hb32_network_observation.py` now propagate that same source HB root through node-to-node / observation-sink transition packets, and focused tests reject HB-lineage substitution or digest tampering.

On StegOS head `bc78192d8a04c7abdb0d0c0ee4fc0d18e9297754`:

- StegOS CI run `34378182741`: SUCCESS;
- iOS Device Package Validation `34378182582`: SUCCESS;
- iOS Apple Toolchain Validation `34378182287`: IN PROGRESS at last observation.

The prior StegOS CI failure on `160cc11d07b71521277265e28041d1a6babc6c7e` was one stale handoff string assertion after 1372/1373 tests passed; that compatibility assertion was repaired at `bc78192d8a04c7abdb0d0c0ee4fc0d18e9297754` and the full deterministic suite then passed.

## Remaining runtime hook

The current-iPhone loopback discovery/result receipt path in StegOSMobile still needs to call the retained node `appendTransition` API with the exact receipt/result commitment and the same current HB observation. Until that hook is integrated and authentically executed, source/build validation does not constitute current-iPhone HB-lineage proof.

The StegOS README must also be updated in the same functional PR before merge to describe profile-derived retained nodes, outward source-HB lineage, and ephemeral InTr/transport/session semantics.

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
-> transition receipt links source/current HB + profile/node/task identity
-> ephemeral transport/session destroyed
-> same node remains
-> later independent operation binds to same node
-> transition history reconstructs to original source-device HB root
```

Transient browser/provider/transport credentials or session state must not persist merely because the node and its evidence lineage persist.

## Next machine work

1. complete exact StegBrowser #33 validation;
2. complete StegOS #310 Apple-toolchain validation;
3. wire StegOSMobile loopback receipt/result commitment into `appendTransition`;
4. update StegOS README in the same functional PR;
5. validate and merge the two implementation PRs only after exact-head gates are clean;
6. finish VACC exact resident bridge;
7. obtain authentic current-iPhone profile-derived node + source-HB-lineage evidence;
8. execute Runtime Profile Map + global convergence visitor and compare measured frontiers with `control/global-runtime-failure-frontier-overlay.json`;
9. reconcile successful node/HB/execution receipts into Master Records and downstream propagation tasks.

## Manual work

None while source/build integration and validation remain machine-executable.
