# COSV Heartbeat State Packet Mirror Handoff

Updated: 2026-08-26T22:46:00-05:00
Repository: `StegVerse-Labs/.github`
Branch: `main`

## Goal and authority

`COSV-HEARTBEAT-STATE-PACKET-002` is the authority-neutral state/transition packet layer for COSV observations.

Canonical issue: `#217` CLOSED_COMPLETED for the first live packet.
Parent COSV handoff: `docs/CANONICAL_OPERATIONAL_STATE_VECTOR_MIRROR_HANDOFF.md`.
Heartbeat reference authority: `docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md` + `control/heartbeat-protocol-anchor.json`.
Gradient consumer: `StegVerse-Labs/StegBrain#861`.
Credential authority: TV/TVC.
GitHub-token runtime authority: NONE.
Third-party runtime role: FALLBACK_ONLY.

The packet grants no execution, claim, fence, route, credential, custody, policy, admissibility, wallet, signing, broadcast, or source-mutation authority.

## Packet modes

- `FULL`: complete ordered COSV record set for an observation/reference.
- `DELTA`: changed records only, predecessor packet digest, unchanged-state root, resulting full-state root, and deterministic transition/gradient inputs.
- Record deletion remains fail-closed in v1.

Every packet binds its reference identity, observation time/context, ordered state records, constraint/evidence commitments, packet digest, and authority invariants.

## Historical first live packet

`receipts/cosv/live/HB31.json` remains valid historical evidence:

```text
carrier_ref: heartbeat_epoch:31
packet_sha256: 618ca9d0b8d6a2dbd661378b8ca9814dd9b882efb40d351c0d517bff8f4e17bd
state_root_sha256: b9ae6209961a3cbd85cc9531088ca91531b03c3eaa4ccc53ee46b0dc1937d22a
mode: FULL
heartbeat_authority_effect: NONE
packet_authority_effect: NONE
credential_authority: TV/TVC
```

HB31 is a preserved pre-anchor observation. It is not the current heartbeat position or current timing authority.

## Canonical heartbeat reference after correction

Current heartbeat state is defined by:

- `control/heartbeat-protocol-anchor.json`
- `heartbeat_runtime/independent_oscillator.py#current_reference`
- `control/heartbeat-live-status.json`

Verified protocol:

```text
anchor epoch: 32
anchor time: 2026-08-23T19:00:00.000Z
period: 10 ms
rate: 100 Hz
progression dependency: OSCILLATOR_ONLY
continuous process required: false
resident sampler required for progression: false
LIVE-009: COMPLETED
heartbeat core: ACTIVE_PROTOCOL_VERIFIED
```

Future COSV packets must bind a canonical post-anchor heartbeat reference. A resident sampler, WorkerCoordinator cycle, assignment trigger, G18 transition, claim/fence, route, or credential is not required for heartbeat reference existence.

## Recurring packet automation

Canonical source:

```text
handoff: handoffs/COSV-LIVE-PACKET-AUTOMATION-006.json
materializer: scripts/materialize_live_cosv_packet.py
worker: workers/cosv_live_packet_worker.py
registry: control/worker-registry.d/cosv-live-packet-automation-006.json
adapter: control/process-worker-adapters.d/cosv-live-packet-automation-006.json
tests: tests/test_cosv_live_packet_automation.py
validation: receipts/cosv/COSV-LIVE-PACKET-AUTOMATION-006-source-validation.json
```

Current lifecycle:

```text
source: COMPLETE_RELEASED
task: HANDOFF_READY
heartbeat-carried trigger required: false
first post-anchor packet execution: PENDING
first post-anchor changed DELTA: PENDING
```

The recurring producer may be independently admitted under task-control authority. Heartbeat is reference-only and never grants that authority.

## Gradient-ready continuation

The first actual post-anchor DELTA with non-empty `gradient_inputs` is the next eligible live input for `StegVerse-Labs/StegBrain#861`.

Changed identities may expose:

```text
identity
level
profile
previous_vector
current_vector
transition_vector
previous_exact_metrics
current_exact_metrics
admissibility_ref
coherency_group_ref
authority_effect=NONE
```

The historical HB32 expectation is invalidated and must not be used. A future residual requires an expectation provably committed before actual target occurrence.

## Current continuation

1. Execute/consume `COSV-LIVE-PACKET-AUTOMATION-006` against canonical post-anchor reference/state evidence.
2. Preserve HB31 as historical FULL provenance; do not rewrite it as post-anchor evidence.
3. If canonical state differs, emit the first post-anchor DELTA with non-empty `gradient_inputs`.
4. StegBrain #861 consumes that immutable DELTA and persists the first live gradient.
5. StegBrain #865 accepts only a separately valid pre-occurrence expectation for a matching target.
6. After enough ordered observations, #863/#865 persist matrix/residual-series/curvature evidence.
7. Sovereign inference proceeds independently through `.github#60`; heartbeat and COSV grant it no execution authority.

## Completion accounting

```text
packet source: COMPLETE_RELEASED
HB31 historical FULL adoption: COMPLETE
heartbeat protocol dependency: SATISFIED / ACTIVE_PROTOCOL_VERIFIED
recurring packet source: COMPLETE_RELEASED
recurring packet runtime execution: PENDING
first post-anchor packet: PENDING
first post-anchor changed DELTA: PENDING
first live gradient: PENDING
chat-session dependency: NONE once global coordination is synchronized
```
