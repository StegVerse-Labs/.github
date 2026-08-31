# HB-Derived InTr Carrier Runtime Mirror Handoff

Repository: `StegVerse-Labs/.github`
Issue: `#619`
Branch: `feat/hb-derived-intr-carrier-612`
State: MERGED_PROFILE / LOCAL_PROPAGATION_INTEGRATION_ACTIVE
Updated: 2026-08-31T08:10:00-05:00
Credential authority: TV/TVC
Authority effect: NONE

## Goal

Bind Universal InTr materialization requests to a deterministic carrier coordinate derived from the canonical HeartBeat reference without granting any transport, admission, execution, credential, routing, transition, receiving, publication, custody, or claim/fence authority.

## Canonical lineage

```text
HB32 protocol anchor
 -> 10 ms / 100 Hz OSCILLATOR_ONLY reference
 -> deterministic packet channel from canonical payload SHA-256
 -> non-authorizing carrier binding
 -> Universal InTr materialization request
 -> profiled ingress validation
 -> ordinary profile-specific admission remains separately governed
```

## Carrier profile

- fundamental: HB / 100 Hz
- reference derivation: canonical HB32 protocol anchor + elapsed 10 ms quanta
- channel family: H1 / 16 deterministic phase slots
- channel selection: first 64 bits of canonical payload SHA-256 modulo 16
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


## Profile merge

Issue #619 / PR #620 merged as `ea09c87106b63fab8bba29872213a91c4e2cf82e`.

Validation:
- organization control plane `33394873703`: SUCCESS;
- Heartbeat Worker Project `33394873627`: SUCCESS.

The Universal InTr profile/binding layer is therefore merged. Authentic propagation is not inferred from those validations.

## Local propagation continuation — issue #624

Historical `engine_v9._carry_subsignals()` proved that an HB-associated derived signal can be persisted locally without becoming authority. The modern implementation now restores that useful behavior for opaque InTr packet carriage through a dedicated application-neutral surface rather than reviving worker-coordination state as carrier authority.

Canonical sequence:

```text
already-governed exact InTr packet bytes
-> canonical #620 packet_id-derived H1 phase/channel binding
-> exact-byte HB-derived carrier signal
-> control/heartbeat-derived-signals.d/<signal>.json (write once)
-> events/heartbeat-derived-carrier.jsonl (append-only observation)
-> independent exact packet recovery + hash/binding verification
```

The local propagation operation:
- does not run the heartbeat sampler;
- does not advance or gate HB;
- does not invoke WorkerCoordinator;
- does not create a task, claim, fence, route, admission, execution, transition, receipt, credential, or receiving grant;
- preserves exact packet bytes and independently reconstructable channel/HB identity.

The previously separate exact-byte carrier formula is reconciled to the ingress-advertised canonical rule:

```text
channel = first32(SHA256(packet_id)) mod 16
family = H1_PHASE_SLOTS
```

Packet bytes determine their own exact SHA-256 but no longer select a second conflicting channel.

New surfaces:
- `heartbeat_runtime/intr_subsignal_runtime.py`
- `tests/test_heartbeat_intr_local_subsignal_runtime.py`

Source implementation still does not claim that a production endpoint has emitted an authentic carrier-bound packet. Runtime proof requires a real producer/observer pair and retained carrier evidence.
## 2026-08-31 merged local propagation and producer integration

PR #638 merged the canonical local HB/InTr subsignal runtime to main as `7bba6e0461ba131b3a04f32c84c3b393d22e14d0` after exact-head validations:
- organization control plane run `33396883584`: SUCCESS;
- Heartbeat Worker Project run `33396883590`: SUCCESS.

Issue #624 is CLOSED. Superseded PR #630 is CLOSED without merge. Issue #619 is CLOSED after the previously merged carrier-profile PR #620.

Issue #645 continues the machine-owned source integration from capability to actual producer use. Current Device KV and SV-DN-1 carrier producers now publish the exact already-transported/already-validated carrier frame into the shared local signal surface through `persist_local_intr_subsignal(...)`. They do not re-sample HB and do not derive a second carrier frame for persistence.

Canonical persistence root:
```text
STEGVERSE_HEARTBEAT_ROOT
or resident fallback:
$XDG_STATE_HOME/stegverse/heartbeat-runtime
or ~/.local/state/stegverse/heartbeat-runtime
```

This source integration makes the next authentic producer execution capable of emitting the canonical shared local signal directly. It does not itself prove that such a production execution has occurred.

## 2026-08-31 canonical channel reconciliation — issue #642

The materialization binding profile and the exact-byte HB carrier now use one phase/channel rule: `slot = int(payload_hash[7:23], 16) mod 16`. This is the 16-slot specialization carried by the canonical HB/InTr producer. `packet_id` remains identity-bound but no longer selects the carrier phase. This eliminates browser/runtime channel divergence without changing any authority semantics.
