# Heartbeat Identifier Encoding Mirror Handoff

Updated: 2026-08-26T15:24:00-05:00

## Authority and goal

```text
goal_id: HEARTBEAT-IDENTIFIER-ENCODING-014
repository: StegVerse-Labs/.github
parent_semantics_handoff: docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
protocol_anchor: control/heartbeat-protocol-anchor.json
credential_authority: TV/TVC
github_runtime_authority: NONE
state: COMPLETE_VALIDATED
```

This goal changes only the human/machine display encoding of heartbeat identifiers. It does not change the canonical integer heartbeat epoch, HB32 anchor, 10 ms period, 100 Hz rate, oscillator causality, progression authority, or historical receipts.

## Canonical encoding

```text
canonical numeric heartbeat: non-negative integer epoch
canonical display radix: 36
alphabet: 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ
canonical display width: 8 characters
canonical display format: HB-XXXXXXXX
encoding: uppercase fixed-width Base36 of integer epoch
ordering: lexical order equals numeric order while epoch <= 36^8 - 1
reversible: true
```

Examples:

```text
32 -> HB-0000000W
33 -> HB-0000000X
35 -> HB-0000000Z
36 -> HB-00000010
```

The integer epoch remains authoritative for arithmetic/protocol derivation. `heartbeat_id` is the canonical compact display identifier.

## Implemented source

```text
c0b09c8109956bde0f0cb9cff5cfec0801a3d7e4  handoff
87bd6bf1ac2ebe87533b99890bb391d8921645ed  encoder/decoder integration
a66c36bf8fe248ff7698b53fa89a6ac5f76198cb  preserve legacy reference_frame
ddfc3ba179a2af22d6bc3bb9199e8f4c7e764cc7  focused encoding tests
4b3564020fb66544dc822e7451210e268a1996a5  live-status contract
00a19cf3380d0edc0069b3f64ee7aee306d90bab  exact-head validation trigger
```

Canonical implementation:

```text
heartbeat_runtime/independent_oscillator.py
  encode_heartbeat_id(epoch)
  decode_heartbeat_id(identifier)
  current_reference(...)["heartbeat_id"]
  derive_reference(...)["heartbeat_id"]
  sample_state(...)["heartbeat_id"]
  sample_state(...)["display_reference_frame"]
```

Compatibility remains:

```text
reference_frame = heartbeat_epoch:<decimal integer>
heartbeat_id = HB-XXXXXXXX
display_reference_frame = HB-XXXXXXXX
```

Historical HB29/HB30/HB31 artifacts remain immutable.

## Validation evidence

```text
workflow: Heartbeat Worker Project - Validation Only / No GitHub Token Authority
run_id: 33011670720
job_id: 98319243364
head_sha: 00a19cf3380d0edc0069b3f64ee7aee306d90bab
result: SUCCESS
complete deterministic repository test suite: PASS
canonical JSON parse: PASS
executable handoffs: PASS
external timing fixed-cadence zero-authority contract: PASS
historical HB29 replay: PASS
current protocol-anchor derivation: PASS
carrier/worker separation: PASS
workflow non-authority proof: PASS
```

The focused Base36 suite is included in the complete deterministic suite and validates known values, round trip, lexical ordering, HB32 display, exactly-10-ms successor change, compatibility fields, and malformed/noncanonical rejection.

## Live status

`control/heartbeat-live-status.json` publishes:

```text
protocol_anchor_epoch: 32
protocol_anchor_heartbeat_id: HB-0000000W
encoding: FIXED_WIDTH_BASE36
width: 8
reversible: true
integer_epoch_remains_canonical: true
```

## Completion

```text
Base36 encode/decode: COMPLETE
8-character compact identifier: COMPLETE
legacy compatibility: PRESERVED
focused validation: PASS
complete deterministic repository suite: PASS
heartbeat runtime semantics changed: NO
user action required: NONE
```

## Successor integration

Propagate `HB-XXXXXXXX` display aliases to current Site, Publisher, admissibility-wiki, and StegGuardian status/UI consumers without rewriting historical decimal labels. Consumer propagation is a downstream integration goal and must not reopen this completed encoding implementation.
