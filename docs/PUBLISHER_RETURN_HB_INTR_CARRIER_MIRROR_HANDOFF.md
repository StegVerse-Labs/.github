# Publisher Return HB-Derived InTr Carrier Mirror Handoff

Repository: `StegVerse-Labs/.github`
Issue: `#640`
Branch: `feat/publisher-return-hb-carrier-636`
State: ACTIVE_IMPLEMENTATION
Updated: 2026-08-31T08:36:00-05:00
Credential authority: TV/TVC
Authority effect: NONE

## Goal

Bind the runtime-generated Publisher -> KV return materialization request to the canonical HB-derived InTr carrier before write-once persistence.

## Path

```text
Publisher response InTr intent
 -> canonical materialization request
 -> HB-derived carrier binding(packet_id,payload_hash,current HB reference)
 -> carrier_binding inserted
 -> request_hash recomputed
 -> write-once materialization persistence
 -> KV Publisher-return ingress validates same carrier contract
```

## Invariants

- no new transport route;
- no carrier authority;
- existing return transport receipt chain unchanged;
- request hash covers carrier binding;
- credential authority remains TV/TVC;
- GitHub-token runtime authority remains NONE.

## Claimed surfaces

- `scripts/consume_publisher_intr_materialization_request.py`
- `tests/test_publisher_intr_materialization.py`
- `docs/PUBLISHER_RETURN_HB_INTR_CARRIER_MIRROR_HANDOFF.md`

## Completion boundary

Focused tests + complete repository validation + merge.
