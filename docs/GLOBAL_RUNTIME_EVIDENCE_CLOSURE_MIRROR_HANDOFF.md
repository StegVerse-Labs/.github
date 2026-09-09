# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
Canonical PR: `StegVerse-Labs/.github#1261` (merged) plus current repair branch `fix/global-runtime-selector-convergence-1260`
COSV: `50000000100000`
Status: `ACTIVE / PARTIAL_SOLUTIONS_MACHINE_PROJECTED_ACROSS_18_MEMBERS / RESIDENT_CONVERGENCE_WIRED / STALE_VACC_ID_REPAIRED / ENDPOINT_FANOUT_ROUTE_REPAIRED / GADI_EXISTING_RUNTIME_WRAPPER_REUSED / PERSISTENT_NODE_EPHEMERAL_EXECUTION_MODEL_PROJECTED / AUTHENTIC_RESIDENT_CONVERGENCE_EXECUTION_NEXT`

## Purpose

Converge all StegVerse ecosystem capabilities that are implemented or integration-ready but still require authentic runtime execution/evidence, receipt custody, reconstruction, runtime-bound validation, or downstream propagation proof. The umbrella preserves child Goal Task IDs and resumes each child from its first genuinely unresolved evidence predicate instead of restarting completed stages.

## Canonical registration

The umbrella is registered under issue #1260 and merged source from PR #1261. The task record is `ACTIVE / CLAIMED_INTEGRATION` with task.v1 COSV `50000000100000`.

## Reusable solution model

The projection keeps existing specific mechanism classes and now adds one ecosystem-wide composite runtime class:

`PERSISTENT_NODE_EPHEMERAL_EXECUTION`

This supersedes the earlier attempt to model retained-node continuity and StegBrowser ephemeral execution as two independent ecosystem solution classes.

### Persistent node + ephemeral calls/transports/execution

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

The StegBrowser implementation is the first concrete source implementation of this ecosystem pattern: browser execution is ephemeral while node continuity persists. The same pattern is appropriate beyond browser lanes because Interlock/InTr calls and data transports are themselves bounded transient operations; they do not need to become persistent merely because the node is persistent.

Therefore `PERSISTENT_NODE_EPHEMERAL_EXECUTION` is projected across all 18 current runtime members.

This does not mean every member uses a browser. It means every member can bind ephemeral governed work and ephemeral transport to the same persistent StegOS continuity anchor.

### What persists

Only continuity-bearing state:

- canonical node identity;
- genesis commitment;
- continuity generation;
- non-secret committed state;
- admitted evidence commitments and references necessary for reconstruction.

### What remains ephemeral

As applicable to the lane:

- task execution process;
- Interlock/InTr invocation;
- request/response transport;
- browser context;
- provider/model session;
- credential exposure/material;
- network connection;
- temporary page/application state;
- transient worker/action process.

Persistence is therefore an identity/evidence continuity property, not a requirement that execution processes or transport channels stay alive indefinitely.

## Implication for the global failure map

This model directly changes the interpretation of the early shared failure band.

The desired ecosystem progression becomes:

```text
persistent retained node observed
-> exact ephemeral task/request binds to retained node
-> fresh bounded claim/fence
-> ephemeral Interlock/InTr call
-> ephemeral transport
-> component execution
-> receipt/readback
-> node evidence commitment advances
-> transient execution/transport torn down
-> retained node remains
```

If authentic current-iPhone retained-node continuity is established, then repeated failure at `AUTHENTIC_RESIDENT_PROCESS_OBSERVED` should no longer require rediscovering/recreating a resident subject per task. The comparison can move immediately to whether each exact ephemeral request is consumed and admitted against the already-known node.

If multiple lanes then fail at the same request-consumption or claim/fence transition, that is a much sharper common failure boundary.

If they diverge after node binding, the persistent substrate is functioning and the remaining failures are task-specific ephemeral execution-path defects.

## Existing specific reusable mechanisms retained

- `HIL_G25_BROWSER`
- `HF_UNIVERSAL_INTR`
- `VACC_LOCAL_RUNTIME`
- `DE006_SAME_EXEC_RECONSTRUCTION`
- `SV001_POST_TERMINAL_CONTINUATION`
- `EXACT_RESIDENT_REQUEST`
- `RUNTIME_PROFILE_MAP`
- `PERSISTENT_NODE_EPHEMERAL_EXECUTION`

Cross-task evidence remains subject-bound; mechanism reuse does not make one task's receipt evidence for another task.

## Current routing corrections

The repaired convergence routing preserves:

- VACC current task identity: `VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023`;
- Endpoint Fanout through the existing `stegos_kv_intr_chain`;
- GADI through its existing bounded preflight/consumer route;
- Runtime Profile Map as the convergence diagnostic trigger.

Current VACC still requires its exact resident bridge before the measured convergence run can represent all 18 members without an artificial integration boundary.

## Authentic proof target

The highest-value substrate proof remains authentic current-iPhone retained-node continuity:

```text
same StegOS node before operation
-> ephemeral governed operation executes
-> ephemeral transport/session is destroyed
-> same node remains
-> later independent operation binds to the same node
```

The proof should additionally show that transient browser/provider/transport credentials or session state did not persist merely because the node persisted.

This is the substrate experiment that can determine whether node/session conflation has been contributing to the repeated runtime failures.

## README review

No new scheduler, dispatcher, credential authority, or persistent transport is introduced. The model reuses the existing single resident substrate while explicitly making work/transport lifecycles bounded and ephemeral. README changes are not currently required for this correction.

## Validation and next execution

Next machine work is:

1. finish VACC exact resident bridge;
2. validate the corrected composite projection;
3. obtain authentic retained-node continuity evidence;
4. execute Runtime Profile Map + global convergence visitor;
5. compare all 18 first unresolved predicates after they bind ephemeral operations to one persistent node.

## Manual work

None currently required.
