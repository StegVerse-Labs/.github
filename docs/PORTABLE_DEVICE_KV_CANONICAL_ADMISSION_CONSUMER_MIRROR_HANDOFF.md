# Portable DEVICE_KV Canonical Admission Consumer Mirror Handoff

Repository: `StegVerse-Labs/.github`
Issue: `#668`
Branch: `feat/device-kv-canonical-admission-657`
State: ACTIVE_IMPLEMENTATION
Updated: 2026-08-31T11:39:00-05:00
Credential authority: TV/TVC
Authority effect: NONE

## Goal

Advance the existing resident DEVICE_KV portable payload path from CVK exact staging through credential-free owner-controlled canonical KV admission/readback.

## Canonical chain

```text
DEVICE_KV INGRESS_ADMITTED
 -> existing DEVICE_KV targeted observation
 -> CVK admit_portable_direct_source(...)
 -> STAGED_UNTRUSTED + exact staging readback
 -> CVK promote_portable_direct_source(...)
 -> CANONICAL_ADMITTED + exact canonical readback
 -> connection-health projection VERIFIED
 -> resident consumption receipt
```

## Scope

Only portable payloads carrying the owner-controlled, credential-free CVK profile. Provider/SKAP sessions remain separate lanes.

## Claimed surfaces

- `scripts/consume_device_kv_intr_materialization_request.py`
- `tests/test_device_kv_intr_event_materialization.py`
- `docs/PORTABLE_DEVICE_KV_CANONICAL_ADMISSION_CONSUMER_MIRROR_HANDOFF.md`

## Completion boundary

Source implementation + validation + merge after the corresponding CVK canonical-admission source is merged. Authentic resident execution then requires current CVK source and real private `STEGVERSE_KV_ROOT`.
