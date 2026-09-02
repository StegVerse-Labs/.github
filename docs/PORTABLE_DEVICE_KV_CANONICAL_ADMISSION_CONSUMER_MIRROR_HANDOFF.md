# Portable DEVICE_KV Canonical Admission Consumer Mirror Handoff

Repository: `StegVerse-Labs/.github`
Issue: `#668`
Branch: `feat/device-kv-canonical-admission-657`
State: SOURCE_MERGED_VALIDATED / AUTHENTIC_RESIDENT_EXECUTION_PENDING
Updated: 2026-09-02T10:18:00-05:00
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

## Upstream CVK closure

CVK #162 merged through PR #163 at `715d49e8bfd3f517ef9653c605beadf5a47f5f41`. The resident consumer may now require both `admit_portable_direct_source` and `promote_portable_direct_source` from current local CVK source.


## 2026-09-02 source release reconciliation

The source completion boundary for issue #668 has been satisfied.

```text
upstream CVK canonical-admission merge: 715d49e8bfd3f517ef9653c605beadf5a47f5f41
implementation PR: #669
implementation merge: 4b64594468a81f2f58edbfd5bd7fe04073c4cf8f
source implementation: COMPLETE
source validation: COMPLETE
merge: COMPLETE
authentic resident execution: PENDING
```

The runtime gate remains distinct: a current sovereign resident must execute the already-installed DEVICE_KV consumer against current local CVK source and a real private `STEGVERSE_KV_ROOT`, producing authentic staging, canonical admission/readback, and connection-health evidence. No source merge or hosted validation is promoted into that runtime result.

Issue #668 may close as source-complete while the machine-owned runtime predicate remains open in the resident execution chain.
