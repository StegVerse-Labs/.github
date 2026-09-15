# StegBrowser Runtime Materialization Remediation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Parent/remediates: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Shared runtime-evidence owner: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / TWO-ROUND-TRIP MODEL MERGED+VALIDATED / INVOCATION-BOUND RUNTIME MATERIALIZATION REQUIRED / AUTHENTIC RUNTIME EVIDENCE PENDING`
- External/second user-operated device required: `false`

## Critical runtime-materialization invariant

There is **no standing StegBrowser runtime device, resident surface, or endpoint expected to be online waiting for work**.

The execution surface is invocation-bound and callable. The selected substrate identifies what may be materialized for the invocation; it is not a persistent-online prerequisite.

Therefore:

```text
WAIT_FOR_ONLINE_DEVICE = false
STANDING_RESIDENT_SURFACE_REQUIRED = false
PREEXISTING_RUNTIME_CONNECTION_REQUIRED = false
SELECTED_SUBSTRATE_IS_ON_DEMAND_MATERIALIZATION_TARGET = true
CALLABLE_AND_REFRESHABLE_ARE_INVOCATION_BOUND_INTR_VARIABLES = true
```

Checking whether a device is already online is not a valid prerequisite, completion predicate, or reason to defer execution. A missing pre-existing device is not a runtime failure because no pre-existing device is expected.

Correct progression is:

```text
invoke active Goal/COSV
-> Interlock/InTr resolves invocation state
-> resolve callable + refreshable
-> materialize/instantiate the admitted execution surface for this invocation
-> establish the invocation-bound runtime connection
-> continue governed execution
```

If `callable=true, refreshable=true`, refresh/materialize from current canonical local source as part of the invocation. If `callable=true, refreshable=false`, instantiate the allowed connection without inventing a refresh prerequisite. If `callable=false`, the invocation is not callable under that transition and must not be represented as executed.

## Source validation state

PR #1907 repaired binding of `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` to the active remediation Goal while preserving the retired historical runtime-consumption task as lineage only.

PR #1908 corrected the StegBrowser data path to two governed Interlock/InTr round-trip phases.

Validated PR #1908 source evidence:

```text
validated head = 947c4c7d0f8b1547dff0c3e303a9dbf4d47860e8
organization-control run = 34914042377 PASS
deterministic repository suite = 34914042375 PASS
heartbeat validation = 34914042368 PASS
merge commit = 0fdac00dd761da61fbd6f2f0e9c5d60463b1b924
```

GitHub/CI runtime authority remains `NONE`.

## Current exact runtime condition

```text
AUTHENTIC_INVOCATION_BOUND_RUNTIME_MATERIALIZATION_AND_INTR_INGRESS_NOT_YET_OBSERVED
```

This means the invocation has not yet produced authentic evidence of its own materialized execution surface and admitted Interlock/InTr ingress. It does **not** mean an already-running device must be found.

## Round Trip 1 — return to records for verification

The invocation enters governed Interlock/InTr transport and progresses through allowed state transitions. At the first final allowed Interlock/InTr exit transition, the correlated records packet returns to the recording surface.

Required authentic evidence:

```text
GOVERNED_RETURN_PACKET_RECEIVED = true
RECORDS_PACKET_DELIVERED_FOR_RECORDING = true
RETURN_RECORD_DURABLY_RECORDED = true
FIRST_FINAL_ALLOWED_INTR_EXIT_TRANSITION_OBSERVED = true
SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED = true
```

Master Records retains observed-reality/custody/reconstruction authority and does not become Interlock/InTr transport authority.

## Between Round Trips — processing to mirror boundary

After Round Trip 1 is recorded and verified, the recorded material may undergo custody/reconstruction, governed processing, reconciliation, and applicable mirror-boundary processing.

A failure here does not retroactively erase an authentically completed Round Trip 1, but it prevents initiation or completion of Round Trip 2.

## Round Trip 2 — mirror-boundary return to ecosystem

After mirror-boundary processing is complete, the mirror boundary initiates Interlock/InTr again. The governed return calls endpoint Interlock/InTr. If allowed, the endpoint transition returns the processed result into the ecosystem.

Required authentic evidence:

```text
MIRROR_BOUNDARY_PROCESSING_COMPLETE = true
MIRROR_BOUNDARY_INTR_REENTRY_OBSERVED = true
ENDPOINT_INTERLOCK_INTR_CALLED = true
ENDPOINT_INTERLOCK_INTR_ALLOWED = true
ECOSYSTEM_REENTRY_FINAL_ALLOWED_TRANSITION_OBSERVED = true
SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED = true
```

Only after both governed round trips are authentically identified may:

```text
SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIPS_IDENTIFIED = true
```

## Reusable transport composition

- `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` — existing reusable execution capability selected for this Goal.
- `RT-SOVEREIGN-SOURCE-REFRESH-001` — selected iff admitted invocation resolves `callable=true AND refreshable=true`.
- `RTC-ROUNDTRIP-003` — repeat count `2` for this StegBrowser composition.
- `RTC-INTERLOCK-INTR-TRANSPORT-008` — repeat at required governed state crossings.
- `RTC-EVIDENCE-CUSTODY-004` — recording/custody/reconstruction between round trips.
- `RTC-STEGVERSE-EGRESS-007` — second governed egress from mirror-side processing boundary where applicable.
- `RTC-FARSIDE-FINAL-009` — endpoint-side final receive/state transition for ecosystem re-entry where applicable.

## Corrected Goal Chart

### A1 — Invoke and resolve invocation-bound state

Invoke the active Goal/COSV through the existing reusable capability. Interlock/InTr resolves `callable`, `refreshable`, applicable protocol state, and allowed substrate materialization for this invocation.

No online-device discovery stage exists.

### A2 — Materialize invocation-bound runtime surface

Instantiate/materialize the admitted execution surface for this invocation.

- `callable=true, refreshable=true` -> run admitted source refresh/materialization and retain receipt.
- `callable=true, refreshable=false` -> instantiate without invented refresh.
- `callable=false` -> no runtime-execution representation.

### A3 — Establish WorkerCoordinator claim/fence

Require authentic claim/fence for the exact active Goal/COSV invocation.

### A4 — Enter governed Interlock/InTr transport

Admit the manifested invocation through existing Canonical Work / Interlock-InTr surfaces and retain authentic ingress evidence.

### A5 — Execute allowed intermediate transitions

Authorized endpoint-local transitions may occur iff allowed.

### A6 — Round Trip 1 return to recording

Return the correlated records packet at the first final Interlock/InTr exit and deliver it to the recording surface.

### A7 — Verify Round Trip 1

Durably record the return record and identify `SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED=true` from authentic evidence.

### B1 — Record/reconstruct/process toward mirror boundary

Master Records and exact downstream processing owners operate on the recorded material between the two governed round trips.

### B2 — Reach mirror boundary

Complete processing required to initiate ecosystem return.

### C1 — Initiate Round Trip 2

From the mirror boundary, initiate the second governed Interlock/InTr return.

### C2 — Call endpoint Interlock/InTr

The governed return reaches and calls endpoint Interlock/InTr; endpoint transition occurs only iff allowed.

### C3 — Re-enter ecosystem

Observe the final allowed endpoint transition placing the processed result back into the ecosystem and identify `SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED=true`.

### C4 — Composition transport success

Set `SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIPS_IDENTIFIED=true` only after authentic success evidence for both round trips.

## Authority invariants

- Task Registry: coordination only.
- Reusable tasks/components: bounded work only; no independent authority.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: invocation-state, transition, and governed packet-movement authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: sole user-verification authority.
- Master Records: recording/custody/reconstruction authority between governed returns; not transport authority.
- HeartBeat: observability/timing/freshness/correlation only.
- Healer: triggered bounded remediation only.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.
- Standing online device: not required and not expected.
- Second user-operated device: not required.

## Manual work

None.
