# StegBrowser Runtime Materialization Remediation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Parent/remediates: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Shared runtime-evidence owner: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
- Issue: `StegVerse-Labs/.github#1866`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / ACTIVE-REMEDIATION REUSABLE BINDING SOURCE REPAIR IN VALIDATION / AUTHENTIC ROUND-TRIP PENDING`
- External/second user-operated device required: `false`
- Source-repair branch: `fix/stegbrowser-active-remediation-reusable-binding`

## Current exact condition

The transport-boundary source contract is merged, but authentic runtime evidence is still absent.

The first machine-executable source defect discovered while pursuing runtime evidence was that `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` and its runner still required the historical task `STEG-BROWSER-RUNTIME-CONSUMPTION-001` to be `ACTIVE/CHECKED_OUT`. That task is canonically `RETIRED / DECOMPOSED_AT_PROMPT_LIMIT` and must not be reopened.

The active tracking identity is therefore:

```text
STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001
COSV 40000100100000
```

The historical task remains operation lineage only:

```text
STEG-BROWSER-RUNTIME-CONSUMPTION-001
```

The repair branch reuses the existing reusable capability and existing Canonical Work / Interlock-InTr runtime surfaces. It does not create a new reusable task, scheduler, dispatcher, WorkerCoordinator, credential route, runtime plane, or user-device requirement.

## Governing GC model

The Goal Chart is a state-transition graph, not a fixed waterfall. Reusable tasks/components are candidates selected from invocation-bound state and transition predicates. Reusable definitions are non-authorizing.

`callable` and `refreshable` are invocation-bound Interlock/InTr state-transition variables. There is no assumed always-on runtime source and no persistent source-freshness completion state.

The StegBrowser transport composition contains **one governed round-trip lifecycle**. It may contain multiple internal transition groups, including:

- `canonical_work_ingress_and_resident_consumption`
- `tvc_source_promotion_and_runtime_observation`

Those groups are not separate round-trip goals and do not increment `RTC-ROUNDTRIP-003` lifecycle count.

## Governed transport terminal boundary

The governed Interlock/InTr data-transport lane ends at the final allowed state transition that exits transport after the governed return record has been received and durably recorded.

Required semantics:

- intermediate Interlock/InTr state transitions may occur locally at either authorized endpoint iff allowed;
- the governed return packet completes the round-trip lifecycle;
- packet arrival time at the final state-transition boundary is not extended merely because the lifecycle is round-trip;
- the return record must be received and durably recorded;
- the final allowed Interlock/InTr transport-exit transition must be observed;
- only then may the terminal transport predicate become true:

```text
SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED = true
```

Master Records ingress, custody, reconstruction, mirroring, reconciliation, persistence, projection, measurement, publication, or any later action is post-transport. A downstream failure after successful final transport exit must not be reclassified as transport failure. Master Records is reconstruction authority, not transport-success authority.

## Reusable-task/component fit

### Transport side

- `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` — existing bounded StegBrowser runtime-consumption capability; now bound to the active remediation Goal for current invocation tracking.
- `RT-SOVEREIGN-SOURCE-REFRESH-001` — selected iff the admitted invocation resolves `callable=true` and `refreshable=true`.
- `RT-INTR-PROTOCOL-ESTABLISH-001` — selected only if no applicable existing InTr protocol resolves.
- `RTC-ROUNDTRIP-003` — exactly one governed round-trip lifecycle for this composition.
- `RTC-INTERLOCK-INTR-TRANSPORT-008` — repeatable at required governed state crossings within that lifecycle.

### Post-transport side

- `RT-CANONICAL-STATE-RECONCILIATION-001`
- `RT-MIRROR-HANDOFF-VALIDATION-001`
- conditional `RT-STEGINDEX-VALIDATION-001`
- conditional `RT-README-VALIDATION-001`
- `RT-SESSION-CLOSEOUT-001`
- `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`

No new reusable task is required by this repair.

## Corrected Goal Chart

### Domain A — Invocation and governed transport-loop completion

#### A1 — Resolve invocation-bound connection state

- Bind active Goal/COSV to the existing reusable capability.
- Resolve `callable`, `refreshable`, applicable InTr protocol, and execution substrate through current state.
- Authority: Interlock/InTr for governed transition admission.
- Current status: source binding is being repaired; authentic transition-variable evidence is not yet observed.

#### A2 — Materialize only selected runtime/source state

- If `callable=true, refreshable=true`, invoke `RT-SOVEREIGN-SOURCE-REFRESH-001` and retain authentic local refresh evidence.
- If `callable=true, refreshable=false`, do not invent a refresh requirement.
- If `callable=false`, do not represent a callable runtime.
- Authority effect of refresh remains `NONE_LOCAL_SOURCE_REFRESH`.

#### A3 — Establish current WorkerCoordinator claim/fence

- WorkerCoordinator must claim the exact active Goal/COSV-bound executable work.
- Completion predicate: `CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = true`.
- Current status: not authentically observed.

#### A4 — Enter governed Interlock/InTr transport

- Use the existing Canonical Work bootstrap and shared Universal InTr listener.
- The repair runner stages only a runtime-local `PROPOSED` projection of the active remediation Goal; canonical source remains `ACTIVE`.
- Authentic `INGRESS_ADMITTED` evidence is retained in the existing resident root.
- The runner must stop at the next real authority/evidence boundary rather than infer later success.

#### A5 — Execute required allowed intermediate transitions

- Intermediate transitions may occur locally at authorized endpoints iff allowed.
- `RTC-INTERLOCK-INTR-TRANSPORT-008` may repeat at required state crossings.
- `RTC-ROUNDTRIP-003` remains one lifecycle.
- WorkerCoordinator claim/fence remains binding throughout the invocation.

#### A6 — Receive and durably record governed return record

- Complete return leg.
- Receive governed return packet.
- Durably record exact correlated return record.
- Completion predicates:
  - `GOVERNED_RETURN_PACKET_RECEIVED = true`
  - `RETURN_RECORD_DURABLY_RECORDED = true`

#### A7 — Final allowed transport-exit transition

- Observe final allowed Interlock/InTr state transition exiting the transport lane.
- After A6 + final exit:

```text
SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED = true
```

- Transport subproblem is then closed for that invocation.

### Domain B — Post-transport processing

Domain B begins only after A7.

#### B1 — Bind/classify retained evidence

Consume already-completed transport evidence without recreating or reproving transport.

#### B2 — Master Records ingress/custody/reconstruction

Master Records reconstructs observed reality after transport. Failure here does not negate A7 transport success.

#### B3 — Selected downstream mirror/reconciliation/persistence/projection

Each downstream authority owns its own result. No post-transport failure may be back-propagated as transport failure.

#### B4 — Global runtime evidence measurement

Run only after authentic retained evidence exists; measurement remains non-authorizing.

#### B5 — Goal closure

Close only from authentic A-domain transport proof plus independently required B-domain terminal predicates.

## Current source-repair implementation

Branch `fix/stegbrowser-active-remediation-reusable-binding` currently changes:

- `source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json`
  - active tracking task becomes `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`;
  - retired runtime-consumption task is lineage only.
- `control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json`
  - current request binds active remediation Goal/COSV;
  - historical reactivation is explicitly forbidden.
- `control/task-vectors/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json`
  - supplies current task.v1 source vector.
- `data/canonical-task-records/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json`
  - binds admitted ephemeral StegOS substrate, projection-only WorkerCoordinator claim boundary, and `INGRESS_ADMITTED` as an allowed candidate transition while preserving actual authority owners.
- `scripts/run_stegbrowser_runtime_consumption_reusable.py`
  - tracks the active remediation Goal;
  - preserves the retired task as operation lineage;
  - uses the existing SovereignLocalEventRuntimeAdapter and existing Canonical Work bootstrap;
  - retains authentic ingress evidence exactly in the existing resident root;
  - stops at `CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED` rather than claiming later runtime completion.
- regression tests
  - enforce one round-trip lifecycle;
  - enforce active-remediation tracking and historical-task retirement.

## Runtime evidence status

No authentic runtime completion is claimed from this branch, CI, GitHub, or source state.

The authorized remote runtime connector was unavailable when checked in this session, so no local resident execution was performed from ChatGPT. GitHub evidence also does not currently show authentic observations for:

```text
RUNTIME_CONNECTION_TRANSITION_VARIABLES_OBSERVED
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED
GOVERNED_RETURN_PACKET_RECEIVED
RETURN_RECORD_DURABLY_RECORDED
FINAL_ALLOWED_TRANSPORT_EXIT_TRANSITION_OBSERVED
SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED
```

The first authentic runtime target after source validation is an active-remediation `INGRESS_ADMITTED` receipt retained from the existing Canonical Work / Interlock-InTr bootstrap. The next boundary is current WorkerCoordinator claim/fence evidence.

## Failure ownership

```text
BEFORE TRANSPORT ENTRY
  -> exact pre-transport owning domain

INSIDE TRANSPORT THROUGH FINAL EXIT
  -> transport or exact in-lane authority/component

RETURN RECORD RECEIVED + DURABLY RECORDED
AND FINAL ALLOWED TRANSPORT EXIT SUCCEEDS
  -> SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED = true
  -> transport subproblem CLOSED

AFTER FINAL TRANSPORT EXIT
  -> exact post-transport domain
  -> MUST NOT be classified as transport failure
```

## Healer

Healer is triggered remediation only. A pending predicate, missing runtime signal, or transition-variable value is not by itself a Healer trigger. Healer never becomes the normal stage owner, scheduler, carrier, transport authority, or reconstruction authority.

## Authority invariants

- Task Registry: coordination only.
- Reusable tasks/components: bounded work only; no independent authority.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition and packet-movement authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: sole user-verification authority.
- Master Records: observed-reality/custody/reconstruction authority after transport.
- HeartBeat: observability/timing/freshness/correlation only.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.
- Second user-operated device: not required.

## Manual work

None.
