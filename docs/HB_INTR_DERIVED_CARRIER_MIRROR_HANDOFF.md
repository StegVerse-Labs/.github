# HB / InTr Derived Carrier Mirror Handoff

Updated: 2026-08-31
Repository: `StegVerse-Labs/.github`
Goal: `HB-INTR-DERIVED-CARRIER-001`
Parent heartbeat authority: `docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md`
InTr policy: `STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001`
Credential authority: `TV/TVC`
Authority effect: `NONE_CARRIER_ONLY`

## Finding

A local HB-derived runtime signaling mechanism already exists.

Current executable/runtime evidence includes:

```text
heartbeat_runtime/engine_v9.py
  _worker_coordination_subsignal(...)
  _carry_subsignals(...)

control/heartbeat-subsignals.json
  worker_coordination
  organization_federation
  steggate_transport_lease

heartbeat_runtime/carrier_envelope.py
  deterministic phase_slots
  deterministic phase_offsets_deg
  alternate_phases_are_authority_channels = false
```

The existing implementation proves that a downstream signal may be derived from and
carried with the canonical heartbeat reference while remaining non-authorizing.

The missing capability is a reusable profile that carries an already-governed InTr
packet as opaque application bytes on such a derived signal.

## Canonical model

```text
HB 100 Hz oscillator/reference
        |
        v
deterministic derived phase/channel
        ^
        |
already-governed InTr packet
        |
        v
internal/external observer
```

Heartbeat remains oscillator-only. The derived signal is a carrier projection, not an
authority source.

## Required invariants

```text
heartbeat progression dependency: OSCILLATOR_ONLY
heartbeat grants admission authority: false
heartbeat grants execution authority: false
heartbeat grants credential authority: false
heartbeat grants routing authority: false
heartbeat grants transition authority: false
heartbeat grants receiving authority: false

derived carrier grants admission authority: false
derived carrier grants execution authority: false
derived carrier grants credential authority: false
derived carrier grants routing authority: false
derived carrier grants transition authority: false
derived carrier grants receiving authority: false

InTr packet governance authority: EXTERNAL_TO_HB
credential authority: TV/TVC
```

## Deterministic derived-carrier contract

Canonical implementation:

`heartbeat_runtime/intr_derived_carrier.py`

Schema:

`schemas/heartbeat-intr-derived-carrier.schema.json`

Given:
- canonical numeric heartbeat epoch;
- canonical heartbeat identifier/reference;
- canonical InTr packet ID and payload hash;
- canonical HB sample time/reference;
- exact already-governed InTr packet bytes;
- InTr transport profile and boundary identities;

the carrier derives:
- exact packet SHA-256;
- deterministic channel slot from the canonical packet identity rule (`SHA256(packet_id)` first 32 bits modulo 16);
- deterministic phase offset from slot/phase count;
- stable carrier signal identity;
- exact base64 packet bytes;
- HB reference identity;
- zero-authority declarations.

No packet semantics are rewritten or interpreted by HB.

## Application data semantics

The old shorthand “HB is not application payload transport” is too broad.

Corrected meaning:

```text
The primary HB reference does not interpret, authorize, route, admit, execute,
or receive application payloads.

Application data MAY be carried directly or as opaque InTr packet bytes on
deterministic signals derived from HB.

InTr governs those packets. The HB reference and derived carrier only supply
synchronization, deterministic channel/phase identity, observation coordinates,
and carrier continuity.
```

## SV-DN-1 consequence

The canonical SV-DN-1 Universal InTr hop may bind its governed packet to this derived
carrier profile without changing its existing route/admission semantics.

This does not itself prove an authentic carrier-bound SV-DN-1 packet has been observed.
That requires a fresh runtime receipt binding:
- exact InTr receipt hash;
- exact HB epoch/reference;
- exact derived channel/phase;
- exact packet SHA-256;
- observer evidence.

## Completion boundary

Source completion requires:
- derived-carrier implementation;
- schema;
- deterministic tests;
- heartbeat semantic handoff reconciliation;
- SV-DN-1 InTr handoff reference to the carrier profile.

Runtime activation/observation remains separate.


## Current local propagation runtime

Issue #624 installs the current equivalent of historical local HB subsignal carriage:

```text
heartbeat_runtime/intr_subsignal_runtime.py

propagate_local_intr_subsignal(...)
  -> derive canonical HB/InTr binding
  -> preserve exact packet bytes in derived carrier frame
  -> write-once local signal
  -> append observation event only after exact re-read/recovery PASS

recover_local_intr_subsignal(...)
  -> revalidate carrier binding
  -> revalidate channel/reference identity
  -> revalidate packet SHA-256
  -> return exact original bytes
```

Dedicated state is used instead of `control/heartbeat-subsignals.json` so the historical carrier concept is retained without making current worker-coordination state a transport/control authority.

Canonical local paths:

```text
control/heartbeat-derived-signals.d/
events/heartbeat-derived-carrier.jsonl
```

An identical repeat is idempotent; a write-once collision or any carrier/packet tamper fails closed.
