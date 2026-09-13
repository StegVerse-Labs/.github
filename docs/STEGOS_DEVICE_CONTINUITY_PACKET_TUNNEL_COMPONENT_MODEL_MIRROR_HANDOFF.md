# StegOS Device Continuity Packet Tunnel — Reusable Task Component Model Handoff

Updated: 2026-09-13
Goal Task: `STEGOS-DEVICE-CONTINUITY-PACKET-TUNNEL-RUNTIME-001`
COSV: `NOT ESTABLISHED`
Parent Goal: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
Runtime truth handoff: `StegVerse-Labs/StegOS/docs/STEGOS_DEVICE_CONTINUITY_CARRIER_TARGET_INTEGRATION_MIRROR_HANDOFF.md`
Status: `ACTIVE / COMPONENT MODEL RECONCILED / SUBJECT-BOUND OBSERVATION CONFIGURED / RUNTIME EVIDENCE PENDING`

## Identity and decomposition

The existing Goal Task remains valid, `IN_PROGRESS`, and without an established COSV. Componentization does not restart, rename, close, or replace it. The deterministic decomposition score remains `19` with disposition `STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION`.

## Subtraction-first correction

Inspection of the canonical StegOS controller shows that `DeviceContinuityCarrierController.start()` calls `NETunnelProviderSession.startVPNTunnel()` and records `START_REQUESTED_RUNTIME_UNPROVEN`. The controller explicitly states that the request is local transport capability only and is not transition admission or transition authority. `PacketTunnelProvider` likewise exposes the carrier with `authority_effect=NONE_TRANSPORT_ONLY` and separately validates an already-admitted recovery envelope before retaining or serving it.

Therefore starting/stopping or status-observing `DeviceContinuityPacketTunnel` is **not itself a StegVerse governed state transition**. Requiring an Interlock/InTr admission merely to start the carrier was a self-created prerequisite and is removed.

Interlock/InTr remains the canonical governed admission/state-transition authority and is required whenever an admitted recovery envelope or another actual StegVerse state transition is submitted. This correction narrows component selection; it does not weaken authority separation.

## Required reusable component

### Authentic runtime observation

Component/owner: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`. Measurement machinery is non-authorizing; Master Records remains observed-reality custody/reconstruction authority.

The observation is subject-bound:

- runtime subject: `DeviceContinuityPacketTunnel`;
- provider bundle: `org.stegverse.stegosmobile.devicecontinuity`;
- substrate: `STEGOS-CURRENT-DEVICE-NODE`;
- probe: `GET http://127.0.0.1:8766/api/device-continuity/v1/status`;
- expected schema: `stegos.device_continuity_recovery_transport.v1`;
- accepted live states: `AVAILABLE_NO_ENVELOPE` or `AVAILABLE_WITH_ADMITTED_ENVELOPE`;
- persistence test: observe the exact endpoint, foreground another browser/app container on the same StegOS Node, then observe the same endpoint again.

This reuses the provider's existing status surface. It creates no new probe, listener, daemon, observer, WorkerCoordinator, scheduler, transport, or authority source.

## Conditional component

`RTC-INTERLOCK-INTR-TRANSPORT-008` is conditional, not required for these three carrier-runtime predicates. It becomes applicable only when this or a downstream Goal Task actually submits an admitted recovery envelope or another governed StegVerse transition.

## Cross-task runtime-presence rule

Generic WorkerCoordinator/runtime-presence evidence, HeartBeat liveness/freshness evidence, the frozen global convergence receipt, source/CI, merge state, or a host start request cannot satisfy the packet-tunnel predicates. `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001` is reused only for the exact packet-tunnel subject/interface.

## Authority separation

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority where a task-controlled operation requires it.
- Interlock/InTr: every actual governed StegVerse admission/state transition.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS Node: interchangeable transport/execution node, never a user verifier.
- Master Records: observed-reality custody/reconstruction authority.
- HeartBeat: timing, liveness, freshness, state correlation, observability only.
- GitHub: source/evidence coordination only; no runtime authority.

## Completion predicates

1. `HOST_ACTIVATION_SOURCE_VALIDATED` — satisfied by StegOS PR #363 and exact-head validation.
2. `AUTHENTIC_PACKET_TUNNEL_ACTIVATION_OBSERVED` — pending.
3. `AUTHENTIC_CROSS_APP_PERSISTENCE_OBSERVED` — pending.
4. `AUTHENTIC_LOOPBACK_8766_REACHABILITY_OBSERVED` — pending.

`runtime_resolution` remains `null`. The endpoint and lifecycle semantics are source-only `runtime_observation_configuration` until authentic runtime evidence exists.

## Validation history

PR #1754 first exposed four stale StegBrowser tests unrelated to this Goal Task. Main repaired those tests at `c16263e0700a8d2e4d2188198193cc0e1375a1da`; #1754 was rebased and exact head `1f8cb29a846301aa56daf2c1b0aa36899b2c2771` then passed organization control `34779474683`, HeartBeat validation `34779474653`, and deterministic diagnostics `34779474749`, merging at `00ab112f9d0628553d6186e120469a12d7458c4c`.

## Next admissible work

Do not build an Interlock admission request for carrier startup. The next authentic work is simply to allow the already-wired StegOSMobile launch path to request the local packet tunnel, then observe the exact `DeviceContinuityPacketTunnel` status endpoint. If observed, foreground another browser/app container on the same StegOS Node and re-observe it for persistence. Any future continuity-envelope POST remains governed by its already-admitted envelope contract and Interlock/InTr authority.

No second user-operated device is required or permitted. No device verification is introduced.
