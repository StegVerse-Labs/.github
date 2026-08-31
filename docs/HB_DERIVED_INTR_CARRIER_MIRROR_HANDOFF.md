# HB-Derived InTr Carrier Runtime Mirror Handoff

Repository: `StegVerse-Labs/.github`
Issue: `#619`
Branch: `feat/hb-derived-intr-carrier-612`
State: ACTIVE_IMPLEMENTATION
Updated: 2026-08-31T07:56:00-05:00
Credential authority: TV/TVC
Authority effect: NONE

## Goal

Bind Universal InTr materialization requests to a deterministic carrier coordinate derived from the canonical HeartBeat reference without granting any transport, admission, execution, credential, routing, transition, receiving, publication, custody, or claim/fence authority.

## Canonical lineage

```text
HB32 protocol anchor
 -> 10 ms / 100 Hz OSCILLATOR_ONLY reference
 -> deterministic packet channel from packet_id
 -> non-authorizing carrier binding
 -> Universal InTr materialization request
 -> profiled ingress validation
 -> ordinary profile-specific admission remains separately governed
```

## Carrier profile

- fundamental: HB / 100 Hz
- reference derivation: canonical HB32 protocol anchor + elapsed 10 ms quanta
- channel family: H1 / 16 deterministic phase slots
- channel selection: first 32 bits of SHA-256(packet_id) modulo 16
- phase coordinate: `2π * slot / 16`
- packet binding: packet_id + payload_hash + sampled_unix_ms + HB reference + channel coordinate
- binding digest: canonical SHA-256
- freshness/admission implication: NONE
- credential authority: TV/TVC

The binding proves only that the packet claims a reconstructable carrier coordinate relative to HB. A valid carrier binding is not a route, receiver, execution, transition, admission, or credential grant.

## Migration

The profiled ingress advertises this carrier now. Existing non-carrier-aware clients remain temporarily accepted with `carrier_binding_present=false`. Carrier-aware clients are validated fail-closed and receipts record the exact carrier binding digest/reference/channel. Site DEVICE_KV is the first migration target.

## Claimed surfaces

- `heartbeat_runtime/intr_carrier_profile.py`
- `workers/universal_intr_profiled_ingress.py`
- `tests/test_intr_hb_carrier_profile.py`
- `docs/HB_DERIVED_INTR_CARRIER_MIRROR_HANDOFF.md`

## Completion boundary

Source completion requires deterministic carrier derivation/validation, ingress profile publication, focused tests, organization/heartbeat validation, and merge. Live carrier propagation remains runtime evidence and must not be inferred from source merge.
