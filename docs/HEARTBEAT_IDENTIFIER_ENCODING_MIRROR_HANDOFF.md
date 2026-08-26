# Heartbeat Identifier Encoding Mirror Handoff

Updated: 2026-08-26T15:18:00-05:00

## Authority and goal

```text
goal_id: HEARTBEAT-IDENTIFIER-ENCODING-014
repository: StegVerse-Labs/.github
parent_semantics_handoff: docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
protocol_anchor: control/heartbeat-protocol-anchor.json
credential_authority: TV/TVC
github_runtime_authority: NONE
state: SOURCE_COMPLETE_VALIDATION_PENDING
```

This goal changes only the human/machine display encoding of heartbeat identifiers. It does not change the canonical integer heartbeat epoch, the HB32 anchor, the 10 ms period, the 100 Hz rate, oscillator causality, progression authority, or historical receipts.

## Canonical encoding

```text
canonical numeric heartbeat: non-negative integer epoch
canonical display radix: 36
alphabet: 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ
canonical display width: 8 characters
canonical display format: HB-XXXXXXXX
encoding: uppercase fixed-width Base36 of the integer epoch
ordering: lexicographic order equals numeric order while epoch <= 36^8 - 1
reversible: true
```

Examples:

```text
32 -> HB-0000000W
33 -> HB-0000000X
35 -> HB-0000000Z
36 -> HB-00000010
```

The canonical integer remains authoritative for arithmetic and protocol derivation. The display identifier is a deterministic reversible projection for receipts, logs, UI, URLs, indexes, and cross-module references.

## Implemented source

```text
c0b09c8109956bde0f0cb9cff5cfec0801a3d7e4  handoff created
87bd6bf1ac2ebe87533b99890bb391d8921645ed  initial Base36 encoder/decoder integration
a66c36bf8fe248ff7698b53fa89a6ac5f76198cb  compatibility correction: preserve legacy reference_frame
ddfc3ba179a2af22d6bc3bb9199e8f4c7e764cc7  focused encoding tests updated
4b3564020fb66544dc822e7451210e268a1996a5  live-status encoding contract published
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

Compatibility rule:

```text
reference_frame = heartbeat_epoch:<decimal integer>   # retained existing machine contract
heartbeat_id = HB-XXXXXXXX                            # new canonical compact identifier
display_reference_frame = HB-XXXXXXXX                # display projection
```

Historical HB29/HB30/HB31 artifacts are not rewritten. Existing decimal reference fields remain valid compatibility surfaces.

## Focused tests installed

`tests/test_heartbeat_identifier_encoding.py` covers:

- known Base36 values;
- encode/decode round trip;
- fixed-width lexical ordering;
- `HB32 -> HB-0000000W`;
- <10 ms stability and exactly-10-ms successor change;
- sample-state integer/display coexistence;
- rejection of negative, overflow, lowercase, malformed-prefix, malformed-width, and invalid-alphabet values.

Hosted validation has not yet been observed for the latest direct-main commits. No PASS is claimed until an exact applicable run or equivalent deterministic execution is observed.

## Live status projection

`control/heartbeat-live-status.json` now publishes the identifier contract and anchor alias:

```text
protocol_anchor_epoch: 32
protocol_anchor_heartbeat_id: HB-0000000W
encoding: FIXED_WIDTH_BASE36
width: 8
reversible: true
integer_epoch_remains_canonical: true
validation_state: SOURCE_COMPLETE_HOSTED_VALIDATION_PENDING
```

## Completion predicate

```text
Base36 encode/decode implemented: YES
8-character HB display identifier implemented: YES
integer epoch retained: YES
legacy reference_frame compatibility retained: YES
focused tests installed: YES
hosted/exact-head validation: PENDING
consumer propagation: PENDING
```

## Downstream propagation

After exact-head/source validation, propagate the encoding contract to current status/UI consumers in Site, Publisher, admissibility-wiki, and StegGuardian. Do not reinterpret historical decimal HB labels as errors; treat them as historical aliases for the same integer epochs.

No user credential, iPhone action, resident sampler, GitHub token, or third-party runtime is required for this encoding goal.
