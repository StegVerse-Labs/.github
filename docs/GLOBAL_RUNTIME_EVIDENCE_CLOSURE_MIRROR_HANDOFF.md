# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
Canonical PR: `StegVerse-Labs/.github#1261` (merged) plus current repair branch `fix/global-runtime-selector-convergence-1260`
COSV: `50000000100000`
Status: `ACTIVE / PROFILE_DERIVED_PERSISTENT_NODES / EPHEMERAL_EXECUTION_AND_TRANSPORT / SOURCE_DEVICE_HB_LINEAGE_PROJECTED / FAILURE_FRONTIER_OVERLAY_MATERIALIZED / AUTHENTIC_RETAINED_NODE_AND_CONVERGENCE_RECEIPTS_PENDING`

## Purpose

Converge all StegVerse ecosystem capabilities that are implemented or integration-ready but still require authentic runtime execution/evidence, receipt custody, reconstruction, runtime-bound validation, or downstream propagation proof. The umbrella preserves child Goal Task IDs and resumes each child from its first genuinely unresolved evidence predicate instead of restarting completed stages.

## Canonical registration

The umbrella is registered under issue #1260 and merged source from PR #1261. The task record is `ACTIVE / CLAIMED_INTEGRATION` with task.v1 COSV `50000000100000`.

## Reusable solution model

The ecosystem-wide composite runtime class is:

`PERSISTENT_NODE_EPHEMERAL_EXECUTION`

Runtime profiles are reusable definitions. Individual components materialize **specific StegOS node instances** from the applicable profile. Node identity, genesis, continuity generation, committed non-secret state, admitted evidence commitments, and source-device HB lineage persist. Task execution, WorkerCoordinator claim/fence lifecycles, Interlock/InTr invocations, transports, provider/browser/model/action sessions, credentials, and temporary execution processes remain bounded and ephemeral.

```text
runtime / node profile
  -> component-specific StegOS node instance
       - stable node identity
       - genesis commitment
       - continuity generation
       - non-secret state commitment
       - admitted evidence commitments
       - immutable source-device HB root reference
       - append-only HB-related transition history

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

StegBrowser is the first concrete implementation demonstrating the pattern: the node persists while browser execution is ephemeral. The same architectural behavior is projected across all 18 runtime members; it does not mean all members use a browser.

Cross-task evidence remains subject-bound; mechanism reuse does not make one task's receipt evidence for another task.

## Source-device HB lineage invariant

Canonical contract:

`control/stegos-node-hb-lineage-contract.json`

The reference HB from the source device propagates outward with the node lineage. A derived/profile-materialized node must remain aware of the originating source-device HB reference and retain an append-only transition history relating its own transitions back to that source reference.

Each transition history entry is expected to retain, when applicable:

- source-device HB reference;
- current observed HB reference;
- profile reference;
- node ID;
- task ID and request ID;
- COSV vector;
- Interlock/InTr route or transition reference;
- result/receipt commitment;
- prior transition commitment.

A descendant node may add a fresh observed HB reference for freshness/correlation, but it must not replace or erase the immutable source-device HB root reference. The result is an outward-propagating temporal/lineage chain from source device -> profile-derived node -> ephemeral governed transitions -> descendant node/evidence state.

HB remains non-authorizing. This lineage grants no execution, claim/fence, Interlock/InTr admission, credential, custody, publication, or completion authority. Existing DEVICE_KV evidence already demonstrates the compatible transport principle: canonical HB reference -> HB-derived carrier -> request/response transport, with HB serving carriage/observation rather than transition authority.

## Corrected routing

The convergence routing preserves:

- VACC current task identity: `VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023`;
- Endpoint Fanout through the existing `stegos_kv_intr_chain`;
- GADI through its existing bounded preflight/consumer route;
- DE-006 through the existing Ecosystem Chat parent continuation path;
- StegClaw through the shared runtime-presence projector plus subject-specific continuation;
- Runtime Profile Map as the convergence diagnostic trigger.

Current VACC still requires its exact resident bridge before an authentic measured 18-member convergence run can remove that artificial integration condition.

## Failure-frontier overlay under the composite model

Machine-readable projection:

`control/global-runtime-failure-frontier-overlay.json`

This projection is explicitly **not** an authentic runtime receipt. It asks what the failure map becomes under two assumptions:

1. authentic persistent-node continuity has been established; and
2. VACC's exact resident bridge has been wired.

Existing later-stage authentic evidence is never moved backward merely to adopt the new solution class.

The comparison axis is:

1. `SOURCE_AND_REQUEST_READY`
2. `PERSISTENT_NODE_CONTINUITY_OBSERVED`
3. `EPHEMERAL_REQUEST_BOUND_AND_CONSUMED`
4. `WORKERCOORDINATOR_CLAIM_FENCE`
5. `EPHEMERAL_INTERLOCK_INTR_ADMISSION`
6. `EPHEMERAL_TRANSPORT_PROVIDER_OR_LEASE_BINDING`
7. `COMPONENT_EXECUTION_OR_REEXECUTION`
8. `EXACT_RECEIPT_COMMITMENT_OR_RETENTION`
9. `MASTER_RECORDS_CUSTODY_RECONSTRUCTION`
10. `DOWNSTREAM_PROPAGATION_VERIFICATION`

Projected first-frontier counts after persistent-node continuity and VACC bridge:

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

The former resident-process-persistence wall disappears from the projected map. The map becomes strongly bimodal:

- **5 lanes** at exact ephemeral request binding/consumption: CryptoBot, DEVICE_KV/MyKV, SV002, StegClaw, Runtime Profile Map.
- **8 lanes** at component execution/re-execution: Hugging Face/SV-DN1, SDK/Ecosystem Chat, VACC after bridge, Endpoint Fanout, GLM 5.3, SV-011 Phase 5, StegBrowser, DE-006.
- GADI and Governed Multilane Manifold remain at fresh WorkerCoordinator claim/fence.
- StegVerse-001 moves to ephemeral root InTr/current-device continuation.
- HIL and Native Email remain at transport/provider/lease binding.

The added HB-lineage invariant does not move these failure frontiers by itself. It sharpens subject/time correlation across profile-derived node instances and their ephemeral transitions, which should make the authentic convergence receipt substantially easier to compare across nodes and descendants.

## Validation

`tools/validate_runtime_partial_solution_projection.py` validates:

- all-member `PERSISTENT_NODE_EPHEMERAL_EXECUTION` adoption;
- profile-derived node-instance policy;
- mandatory source-device HB lineage and outward propagation;
- `control/stegos-node-hb-lineage-contract.json` non-authorizing semantics;
- the failure-frontier overlay and its 18-member counts.

There is still no authentic `receipts/sovereign-host/global-runtime-evidence-convergence.latest.json` observed in repository state. The source runner exists, but source presence is not execution evidence.

## Authentic proof target

The highest-value substrate proof now requires both node continuity and HB lineage:

```text
source-device HB root observed
-> profile materializes component-specific StegOS node instance
-> node retains source-device HB root reference
-> ephemeral governed operation executes with current HB observation
-> transition receipt links current HB + source HB + node/profile/task identity
-> ephemeral transport/session is destroyed
-> same node remains
-> later independent operation binds to the same node
-> transition history still reconstructs back to source-device HB root
```

Transient browser/provider/transport credentials or session state must not persist merely because the node and its HB/evidence lineage persist.

## Next machine work

1. finish VACC exact resident bridge;
2. validate and merge the current repair branch;
3. propagate the HB-lineage contract into actual StegOS/StegBrowser/component node materialization and transition receipt emitters;
4. obtain authentic current-iPhone profile-derived node continuity + source-device-HB-lineage evidence;
5. execute Runtime Profile Map + global convergence visitor;
6. compare authentic 18-member first unresolved predicates against `control/global-runtime-failure-frontier-overlay.json`;
7. reconcile successful execution receipts and node/HB lineage into Master Records and downstream propagation tasks.

## README review

The current branch now contains a canonical node/HB lineage contract and projection semantics, but runtime propagation into actual node materializers/receipt emitters is still pending. A README functional update is required in the same change set when that runtime implementation is added; this source/control contract alone does not claim deployed behavior.

## Manual work

None currently required.
