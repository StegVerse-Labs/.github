# MIR / StegVerse separation-of-powers evidence contract mirror handoff

Updated: 2026-09-17
Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / V0.3 FREEZE ACCEPTED / REFERENCE ARCHITECTURE DRAFT V0.2 / PROVEN SV002 ROUTE REUSED / EVENT-DRIVEN MIR RUNTIME MODEL / LIVE PER-TRANSITION MASTER RECORDS PROBE WIRED / COUNTERPART EVIDENCE-SEAM INPUT PENDING`

## Canonical state

The Goal Task remains `ACTIVE`. Frozen v0.3 remains separate from the post-freeze reference-architecture lane. Draft v0.2 continues to enforce separation of governance, admission/state transition, execution, credential/provider authority, evidence custody/reconstruction, and observability. `SEAM_CONFORMANCE != RUNTIME_CHAIN_PROOF` remains unchanged.

The child `MIR-LEAF-V3-CONFORMANCE-FIXTURE-001` still requires authentic MIR independent reproduction. Richard's Bitcoin-anchor statement remains `COUNTERPART_REPORTED / UNVERIFIED` until an independently checkable anchor/inclusion artifact is supplied.

## Proven route and current runtime model

StegVerse-002 already established the reusable route:

```text
registered StegVerse Node
-> Interlock
-> InTr materialization
-> bounded invocation lease
-> EVENT_EPHEMERAL runtime
-> execution-time runtime identity
-> authority-owned continuation
-> independent Master Records reconstruction
```

`MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001` duplicates that route first and adds only current MIR Goal/COSV, destination-profile, transition, and evidence requirements. Generic SV002 mechanics are not a fresh re-proof gate; historical receipts grant no present authority.

The MIR event runtime is state-transition dependent, not an idle remotely reachable service. The current event must obtain the current WorkerCoordinator claim/fence and enter Interlock/InTr; the admitted transition then materializes the EVENT_EPHEMERAL runtime.

## Live per-transition Master Records probe

The actual MIR process adapter now invokes `workers/mir_roundtrip_transition_probe_worker.py`, which wraps and executes the existing MIR worker rather than creating another runtime or transport plane.

For the same current invocation it emits Master Records confirmation packets after each observed step, beginning before the event runtime exists:

```text
WORKERCOORDINATOR_CLAIM_FENCE_BOUND
MIR_EVENT_INGRESS_INTENT_BOUND
CURRENT_NODE_PROOF_VERIFIED
LEASE_STATE_REQUESTED
LEASE_STATE_ADMITTED
LEASE_STATE_PROVISIONING
EVENT_COMPUTE_PROVISIONED
EVENT_EPHEMERAL_RUNTIME_MATERIALIZED
EXECUTION_TIME_RUNTIME_IDENTITY_VERIFIED
LEASE_LOCAL_IDENTITY_ACCEPTED
CURRENT_INTERLOCK_INTR_INGRESS_RECEIVED
RTC-STEGVERSE-EGRESS-007
RTC-INTERLOCK-INTR-TRANSPORT-008
RTC-FARSIDE-FINAL-009
BOUNDED_EVENT_TRANSITION_RECORDED
GOVERNED_RETURN_QUEUED
MIR_DESTINATION_EVIDENCE_RETAINED
MIR_EVIDENCE_EXPORTED
EVIDENCE_EXPORT_STATE_RECORDED
LEASE_STATE_RELEASING
EVENT_COMPUTE_RELEASED
LEASE_STATE_LEASE_CLOSED
EVENT_EPHEMERAL_LEASE_CLOSURE_RETAINED
EXACT_GOVERNED_RETURN_PACKET_RETAINED
```

Every observed packet is byte-exact ingested/reconstructed by the existing Master Records lifecycle worker. `receipts/mir-roundtrip-egress-authenticity/live-transition-diagnostic.latest.json` retains ordered results and `first_non_return_transition_id`. A Master Records non-return does not grant or revoke transition authority; it identifies an evidence/custody boundary.

Implementation/source evidence:

- `f89384515abee696b9627ae81720cd602aedde8e` — live transition probe worker;
- `4fe1f751cabaf1a1ff5605868f0d40399295b006` — MIR process adapter routed through the probe wrapper;
- `55bf8679e3a36a2bfc063e8b436b5f300e44c751` — probe wiring tests;
- `599b0922a1b2348c7ad816dc25d5d0a6aff6b301` — `MIR-LIVE-TRANSITION-PROBE-001` preflight;
- Site transport handoff reconciled at `f7512481071acbe5897622811705d2b3eea0df23`.

## Current exact break

No authentic current live-transition diagnostic or current MIR runtime receipt is retained yet. Therefore no new runtime transition is claimed.

Because the probe begins at the current WorkerCoordinator claim/fence before event ingress, the unresolved boundary is now stated precisely as:

`CURRENT_AUTHENTIC_WORKERCOORDINATOR_EVENT_INVOCATION_NOT_YET_OBSERVED`

This is not a requirement for a continuously running runtime. It means the already-standing current event has not yet produced the first authentic invocation receipt on the instrumented path. Once it does, the probe sequence will identify the exact last successful transition and the first Master Records confirmation-return failure, if any.

## Separation-of-powers invariants

- WorkerCoordinator remains claim/fence authority.
- Interlock/InTr remains admission/state-transition authority.
- TV/TVC remains credential authority where required.
- MIR remains MIR-native semantics authority.
- Master Records remains observed-reality custody/reconstruction only.
- GitHub/GitHub Actions remain source validation/evidence transport only; runtime authority `NONE`.
- Historical SV002 evidence grants no present authority.
- Confirmation packets do not create missing transitions.

## Counterpart evidence still required

Separately from the owned-mirror transport work, Richard/MIR evidence-custody seam input, concrete minimum custody receipts, independently checkable Bitcoin anchor/inclusion evidence, and authentic MIR `mir.leaf.v3` independent reproduction remain pending.

## Next action

Reconcile the first authentic live transition diagnostic from the existing WorkerCoordinator event invocation. If no first probe is produced, repair only the existing selector/claim-to-event invocation transition. If probes are produced, repair only the exact event or Master Records return boundary named by `first_non_return_transition_id`; then continue through RTC 007/008/009, exact return retention, governed return, and final transport exit without adding another scheduler, dispatcher, runtime plane, device prerequisite, remote-surface gate, or generic SV002 re-proof.
