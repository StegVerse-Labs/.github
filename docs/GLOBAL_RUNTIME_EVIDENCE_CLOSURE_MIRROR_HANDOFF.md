# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
Canonical PR: `StegVerse-Labs/.github#1261` (merged) plus current repair branch `fix/global-runtime-selector-convergence-1260`
COSV: `50000000100000`
Status: `ACTIVE / PERSISTENT_NODE_EPHEMERAL_EXECUTION_MODEL_PROJECTED / FAILURE_FRONTIER_OVERLAY_MATERIALIZED / AUTHENTIC_RETAINED_NODE_AND_CONVERGENCE_RECEIPTS_PENDING`

## Purpose

Converge all StegVerse ecosystem capabilities that are implemented or integration-ready but still require authentic runtime execution/evidence, receipt custody, reconstruction, runtime-bound validation, or downstream propagation proof. The umbrella preserves child Goal Task IDs and resumes each child from its first genuinely unresolved evidence predicate instead of restarting completed stages.

## Canonical registration

The umbrella is registered under issue #1260 and merged source from PR #1261. The task record is `ACTIVE / CLAIMED_INTEGRATION` with task.v1 COSV `50000000100000`.

## Reusable solution model

The ecosystem-wide composite runtime class is:

`PERSISTENT_NODE_EPHEMERAL_EXECUTION`

The reusable behavior is:

```text
persistent StegOS node
  - stable node identity
  - genesis commitment
  - non-secret state commitment
  - continuity generation
  - admitted evidence commitments

for each bounded operation:
  -> ephemeral task/request manifestation
  -> ephemeral WorkerCoordinator claim/fence lifecycle as applicable
  -> ephemeral Interlock/InTr invocation
  -> ephemeral data transport
  -> ephemeral provider/browser/model/action session
  -> component execution
  -> exact result/readback/receipt
  -> admitted evidence commitment advances retained node state
  -> transport/session/credential/transient execution state destroyed
  -> persistent node remains for the next operation
```

StegBrowser is the first concrete implementation of this pattern: browser execution is ephemeral while StegOS node continuity persists. The same pattern is projected across all 18 runtime members. Persistence is an identity/evidence-continuity property, not a requirement that task processes, Interlock/InTr calls, transports, network connections, provider sessions, or credentials stay alive.

Cross-task evidence remains subject-bound; mechanism reuse does not make one task's receipt evidence for another task.

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

The comparison axis is now:

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

The former resident-process-persistence wall therefore disappears from the projected map. The map becomes strongly bimodal:

- **5 lanes** concentrate at exact ephemeral request binding/consumption: CryptoBot, DEVICE_KV/MyKV, SV002, StegClaw, Runtime Profile Map.
- **8 lanes** concentrate at component execution/re-execution: Hugging Face/SV-DN1, SDK/Ecosystem Chat, VACC after bridge, Endpoint Fanout, GLM 5.3, SV-011 Phase 5, StegBrowser, DE-006.
- GADI and Governed Multilane Manifold remain at fresh WorkerCoordinator claim/fence.
- StegVerse-001 moves to ephemeral root InTr/current-device continuation.
- HIL and Native Email remain at transport/provider/lease binding.

This is a materially sharper failure topology than the prior resident-process model. If authentic retained-node continuity is proven, a lane still reporting `resident_process_alive_supervised` must be examined for a stale predicate/model assumption rather than automatically requiring a permanently alive task process.

## Validation

`tools/validate_runtime_partial_solution_projection.py` now validates both the all-member `PERSISTENT_NODE_EPHEMERAL_EXECUTION` adoption and the failure-frontier overlay. It fails if the old split classes reappear, any member omits the composite class, the overlay member set diverges from the 18-member projection, or the projected frontier counts drift without an intentional update.

There is still no authentic `receipts/sovereign-host/global-runtime-evidence-convergence.latest.json` observed in repository state. The source runner exists, but source presence is not execution evidence.

## Authentic proof target

The highest-value substrate proof remains authentic current-iPhone retained-node continuity:

```text
same StegOS node before operation
-> ephemeral governed operation executes
-> ephemeral transport/session is destroyed
-> same node remains
-> later independent operation binds to the same node
```

Transient browser/provider/transport credentials or session state must not persist merely because the node persists.

## Next machine work

1. finish VACC exact resident bridge;
2. validate and merge the current repair branch;
3. obtain authentic retained-node continuity evidence;
4. execute Runtime Profile Map + global convergence visitor;
5. compare the authentic 18-member first unresolved predicates against `control/global-runtime-failure-frontier-overlay.json`;
6. treat any residual resident-process-persistence predicate as a candidate stale modeling defect and reconcile it against persistent-node continuity;
7. reconcile successful execution receipts into Master Records and downstream propagation tasks.

## README review

The current work adds a diagnostic/projection model and validation around already-declared bounded reusable-task and continuity semantics. It does not itself alter the deployed runtime, create a persistent transport, add a scheduler/dispatcher, or alter credential authority. README remains unchanged for this projection-only step. Any subsequent runtime implementation that changes actual lifecycle behavior must update README in the same change set.

## Manual work

None currently required.
