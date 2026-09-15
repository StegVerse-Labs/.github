# StegBrowser Runtime Materialization Remediation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Parent/remediates: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Shared runtime-evidence owner: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / TWO-ROUND-TRIP TRANSPORT MODEL CORRECTION IN VALIDATION / AUTHENTIC RUNTIME EVIDENCE PENDING`
- External/second user-operated device required: `false`

## Current exact condition

The reusable runtime binding repair from PR #1907 remains merged and validated. Authentic runtime execution is still unobserved. The current source correction fixes a transport-model error: StegBrowser is not one round trip followed by wholly post-transport Master Records work.

The correct end-to-end shape contains two governed Interlock/InTr round-trip phases separated by record/reconstruction and mirror-boundary processing.

## Corrected transport semantics

### Round Trip 1 — return to records for verification

The invocation enters governed Interlock/InTr transport and progresses through allowed intermediate endpoint-local transitions. At the first final allowed Interlock/InTr exit transition, the correlated records packet returns to the recording surface.

That return is the first round trip. Durable recording is verification evidence for that first return; Master Records does not wait until after an already-closed end-to-end transport lifecycle to begin recording.

Required evidence:

```text
GOVERNED_RETURN_PACKET_RECEIVED = true
RECORDS_PACKET_DELIVERED_FOR_RECORDING = true
RETURN_RECORD_DURABLY_RECORDED = true
FIRST_FINAL_ALLOWED_INTR_EXIT_TRANSITION_OBSERVED = true
SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED = true
```

Master Records retains observed-reality/custody/reconstruction authority. It does not become Interlock/InTr transport authority.

### Between Round Trips — processing to mirror boundary

After the first return is recorded and verified, the recorded material may undergo custody/reconstruction, governed processing, reconciliation, and the applicable mirror-boundary processing.

This interval is between the two round trips. A processing failure here does not retroactively erase an authentically completed first recording/verification round trip, but it prevents initiation or completion of the second ecosystem-return round trip.

### Round Trip 2 — mirror boundary return to ecosystem

After mirror-boundary processing is complete, the mirror boundary initiates Interlock/InTr again. The return path calls the endpoint Interlock/InTr. If allowed, the final endpoint transition returns the processed result into the ecosystem.

Required evidence:

```text
MIRROR_BOUNDARY_PROCESSING_COMPLETE = true
MIRROR_BOUNDARY_INTR_REENTRY_OBSERVED = true
ENDPOINT_INTERLOCK_INTR_CALLED = true
ENDPOINT_INTERLOCK_INTR_ALLOWED = true
ECOSYSTEM_REENTRY_FINAL_ALLOWED_TRANSITION_OBSERVED = true
SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED = true
```

Only when both governed round trips are authentically identified may the composition-level predicate become true:

```text
SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIPS_IDENTIFIED = true
```

## Reusable transport composition

- `RTC-ROUNDTRIP-003` — repeat count `2` for this StegBrowser composition.
- `RTC-INTERLOCK-INTR-TRANSPORT-008` — repeat where required at governed state crossings in both round trips.
- `RTC-EVIDENCE-CUSTODY-004` — record/custody/reconstruction work between round trips; Master Records authority only.
- `RTC-STEGVERSE-EGRESS-007` — applicable to initiating the second governed egress from the mirror-side processing boundary.
- `RTC-FARSIDE-FINAL-009` — applicable to endpoint-side final receive/state transition for ecosystem re-entry.

Internal transition groups such as `canonical_work_ingress_and_resident_consumption` and `tvc_source_promotion_and_runtime_observation` do not independently add round trips. The two round trips are created by two distinct governed return lifecycles with different terminal purposes.

## Corrected Goal Chart

### A1 — Resolve invocation-bound connection state

Resolve `callable`, `refreshable`, applicable InTr protocol, and selected execution substrate from authentic invocation state.

### A2 — Materialize selected runtime/source state

Refresh only if the admitted transition resolves `callable=true, refreshable=true`. Do not infer persistent source freshness.

### A3 — Establish current WorkerCoordinator claim/fence

Require authentic claim/fence for the exact active Goal/COSV invocation.

### A4 — Enter governed Interlock/InTr transport

Admit the manifested invocation through existing Canonical Work / Interlock-InTr surfaces.

### A5 — Execute allowed intermediate transitions

Authorized endpoint-local transitions may occur iff allowed.

### A6 — Round Trip 1 return to recording

Return the correlated records packet at the first final Interlock/InTr exit and deliver it to the recording surface.

### A7 — Verify Round Trip 1 by durable recording

Durably record the return record and identify `SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED=true` from authentic evidence.

### B1 — Record/reconstruct/process toward mirror boundary

Master Records and exact downstream processing owners operate on the recorded material. This is between round trips, not after the complete end-to-end return lifecycle.

### B2 — Reach mirror boundary

Complete the processing state required to initiate the ecosystem return.

### C1 — Initiate Round Trip 2 through Interlock/InTr

From the mirror boundary, initiate the second governed Interlock/InTr return.

### C2 — Call endpoint Interlock/InTr

The governed return reaches and calls the endpoint Interlock/InTr; the endpoint transition occurs only iff allowed.

### C3 — Re-enter ecosystem

Observe the final allowed endpoint transition placing the processed result back into the ecosystem and identify `SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED=true`.

### C4 — Composition transport success

Set `SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIPS_IDENTIFIED=true` only after authentic success evidence for both Round Trip 1 and Round Trip 2.

## Current runtime evidence state

No authentic runtime predicate is promoted by this source correction. The first runtime evidence target remains invocation-bound connection/Interlock-InTr ingress, followed by WorkerCoordinator claim/fence and Round Trip 1 progression.

## Authority invariants

- Task Registry: coordination only.
- Reusable tasks/components: bounded work only; no independent authority.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition and packet-movement authority for both round trips.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: sole user-verification authority.
- Master Records: recording/custody/reconstruction authority between the two governed transport returns; not transport authority.
- HeartBeat: observability/timing/freshness/correlation only.
- Healer: triggered bounded remediation only.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.

## Manual work

None.
