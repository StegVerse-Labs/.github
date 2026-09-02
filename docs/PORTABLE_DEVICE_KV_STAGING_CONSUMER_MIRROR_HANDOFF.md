# Portable DEVICE_KV Staging Consumer Mirror Handoff

Repository: `StegVerse-Labs/.github`
Issue: `#608`
Branch: `feat/portable-device-kv-staging-608`
State: SOURCE_MERGED_VALIDATED / AUTHENTIC_RESIDENT_STAGING_PENDING
Updated: 2026-09-02T10:18:00-05:00
Credential authority: TV/TVC
Authority effect: NONE

## Goal

Extend the existing DEVICE_KV Universal InTr materialization consumer so a request carrying the portable owner-controlled inline payload profile can be durably staged into the canonical KnowledgeVault data root through continuity-vault-kit.

This is not a second ingress, scheduler, WorkerCoordinator, claim/fence owner, KV runtime owner, or credential path.

## Canonical upstream

- Site #789 / PR #790
- CVK #156 / PR #158
- existing profiled ingress: `workers/universal_intr_profiled_ingress.py`
- existing materialization consumer: `scripts/consume_device_kv_intr_materialization_request.py`
- existing observation owner: `SHWP-DEVICE-KV-INTR-OBSERVATION-001`

## Required behavior

```text
INGRESS_ADMITTED DEVICE_KV request
 -> validate canonical materialization request
 -> existing targeted DEVICE_KV observation attempt
 -> if portable_payload schema present:
      resolve current local continuity-vault-kit source
      require explicit STEGVERSE_KV_ROOT
      invoke runtime/portable_direct_source_ingress.py
      exact staging/readback receipt
 -> emit materialization consumption receipt with distinct:
      transport observation state
      canonical KV staging state
```

## Authority invariants

- ingress grants no claim/fence;
- WorkerCoordinator remains sole task claim/fence authority;
- CVK staging does not grant trusted semantic admission;
- provider/SKAP activation remains false;
- GitHub runtime authority remains NONE;
- `STEGVERSE_KV_ROOT` is a non-secret local locator only;
- no network source fetch.

## Claimed surfaces

- `scripts/consume_device_kv_intr_materialization_request.py`
- `scripts/refresh_and_execute_resident_task.py`
- `scripts/consume_stegos_kv_intr_chain_request.py`
- `scripts/consume_resident_rendezvous.py`
- `tests/test_device_kv_intr_event_materialization.py`
- `docs/PORTABLE_DEVICE_KV_STAGING_CONSUMER_MIRROR_HANDOFF.md`

## Completion boundary

Source completion requires exact-head organization/worker validation and merge.
Runtime completion requires an authentic resident request plus real `STEGVERSE_KV_ROOT`, CVK source, ingress receipt, staged exact bytes, exact readback, and durable CVK staging receipt.

## Upstream CVK source closure

CVK #156 merged through PR #158 at `8b02312c352463059c966ee7ee8f4b1fa9f942e9`. The resident consumer may therefore require `runtime/portable_direct_source_ingress.py` from current local CVK source; repository merge still does not prove a resident has refreshed or that a real KV data root is bound.


## 2026-09-02 source release reconciliation

The source completion boundary for issue #608 has been satisfied.

```text
upstream CVK portable staging merge: 8b02312c352463059c966ee7ee8f4b1fa9f942e9
implementation PR: #611
implementation merge: eb178edc9621b9542c94ec1f0e9a3d19cf695d4c
source implementation: COMPLETE
source validation: COMPLETE
merge: COMPLETE
authentic resident staging execution: PENDING
```

The downstream canonical-admission continuation has also been source-completed under issue #668 / PR #669, but neither source path proves that a current sovereign resident has observed the request, bound a real private `STEGVERSE_KV_ROOT`, staged the exact bytes, or produced an authentic staging receipt.

Issue #608 may therefore close as source-complete while the resident runtime evidence gate remains open.
