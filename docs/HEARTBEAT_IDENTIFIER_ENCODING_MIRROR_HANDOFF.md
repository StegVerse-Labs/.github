# Heartbeat Identifier Encoding Mirror Handoff

Updated: 2026-08-26T15:00:00-05:00

## Authority and goal

```text
goal_id: HEARTBEAT-IDENTIFIER-ENCODING-014
repository: StegVerse-Labs/.github
parent_semantics_handoff: docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
protocol_anchor: control/heartbeat-protocol-anchor.json
credential_authority: TV/TVC
github_runtime_authority: NONE
state: ACTIVE_IMPLEMENTATION
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

## Requirements

1. Add deterministic Base36 encode/decode helpers to the canonical heartbeat runtime module.
2. `current_reference()` and `derive_reference()` retain integer `epoch` and `generation` fields.
3. Current references additionally expose the canonical fixed-width display identifier.
4. `sample_state()` exposes the same display identifier without rewriting historical state semantics.
5. Reject negative epochs, malformed prefixes, lowercase/noncanonical forms, wrong widths, and values beyond the fixed-width range.
6. Preserve HB32 anchor and continuous 10 ms / 100 Hz progression unchanged.
7. Add deterministic tests for round-trip, lexical ordering, boundary values, anchor display, and 10 ms increments.
8. Historical HB29/HB30/HB31 artifacts remain immutable; consumers may derive display aliases without modifying those artifacts.

## Completion predicate

```text
Base36 encode/decode implemented
8-character HB display identifier implemented
round-trip validation PASS
lexical ordering validation PASS
HB32 -> HB-0000000W
10 ms successor changes display ID exactly once
integer epoch remains canonical
no runtime/authority semantics changed
```

## Downstream propagation

After source validation, propagate the encoding contract to current status/UI consumers in Site, Publisher, admissibility-wiki, and StegGuardian. Do not reinterpret historical decimal HB labels as errors; treat them as historical aliases for the same integer epochs.
