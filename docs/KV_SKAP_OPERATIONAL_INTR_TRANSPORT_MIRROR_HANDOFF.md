# KV -> SKAP Vault Operational InTr Transport Mirror Handoff

Repository: `StegVerse-Labs/.github`
Canonical merge: `3ec15ed7937fa621a215f78b4992a6e3af63566f`
Updated: 2026-08-31T17:50:00-05:00
State: MERGED_ORGANIZATION_VALIDATED / AUTHENTIC_RESIDENT_KV_SKAP_EVENT_NOT_YET_OBSERVED
Credential authority: TV/TVC
Authority effect: NONE

## Goal

Make the organization-resident Universal InTr transport layer operational across the complete credential-custody path:

```text
DEVICE_SYSTEM
  -> device-kv
  -> KV / KnowledgeVault:Interlock
  -> kv-skap-custody
  -> SKAP_VAULT / SKAP:Vault
```

The `.github` organization boundary owns transport ingress/egress and event dispatch. It does not own credential plaintext, credential authority, provider execution, or SKAP admission policy.

## Canonical upstream contracts

- StegOS Universal InTr profile: `kv-skap-custody`
  - request class: `KV_SKAP_CIPHERTEXT_CUSTODY`
  - operation: `ADMIT_CIPHERTEXT`
  - source: `KV / KnowledgeVault:SKAPClient`
  - destination: `SKAP_VAULT / SKAP:Vault`
  - downstream owner: `StegVerse-Labs/TVC`
  - custody mode: `EXACT_BYTES`
  - materialization extensions: `sealed_capsule`, `device_kv_receipt`
- TVC double-Interlock gate:
  - DEVICE -> KV receipt must validate;
  - KV -> SKAP_VAULT receipt must chain to DEVICE -> KV;
  - both connectors are InTr;
  - secret plaintext forbidden;
  - authority transfer forbidden.
- TVC SKAP store:
  - storage backend id must begin `KV_SKAP_INTR_`;
  - resident compatibility backend writes under `<STEGVERSE_KV_ROOT>/_Vault/SKAP`;
  - exact ciphertext readback required;
  - replay denied.

## Operational source path

```text
validated DEVICE -> KV boundary receipt
+ exact sealed capsule
  -> scripts/dispatch_kv_skap_custody_materialization.py
  -> canonical StegOS kv-skap-custody transport intent
  -> canonical event-ephemeral materialization request
  -> HB-derived non-authorizing carrier binding
  -> TVC_RELAY_EGRESS
  -> workers/universal_intr_profiled_ingress.py
  -> write-once KV/SKAP ingress receipt
  -> direct credential-scrubbed event dispatch
  -> scripts/consume_kv_skap_custody_materialization_request.py
  -> current local TVC double-Interlock validation
  -> same resident STEGVERSE_KV_ROOT
  -> _Vault/SKAP exact ciphertext custody + receipts
```

No second WorkerCoordinator task is introduced for this transport hop. Event admission does not mint a claim or fence. No GitHub runner, Render, Vercel, Cloudflare, HB carrier, or request grants execution or credential authority.

## Implemented surfaces

- `scripts/dispatch_kv_skap_custody_materialization.py`
- `scripts/consume_kv_skap_custody_materialization_request.py`
- `workers/universal_intr_profiled_ingress.py`
- `tests/test_kv_skap_custody_materialization.py`
- `tests/test_sv002_event_ephemeral_materialization.py`
- this handoff

## Validation / merge evidence

- PR: `StegVerse-Labs/.github#716`
- merge: `3ec15ed7937fa621a215f78b4992a6e3af63566f`
- final source head: `98b717150879913bb84222bac2d0cde4b45d421f`
- organization control validation: run `33448181170` — SUCCESS
- heavyweight Heartbeat Worker Project run `33448181186` remained queued at merge time and is not treated as passed or failed.
- An earlier heavyweight run compiled the new ingress/consumer source and exposed one stale exact profile-list assertion; that assertion was updated before merge. Its other failures were concurrent COSV/Healer/federation baseline drift and were not changed by this transport task.

## Source completion predicates

1. canonical StegOS `kv-skap-custody` intent/materialization construction from exact sealed capsule + DEVICE->KV receipt;
2. HB-derived non-authorizing carrier binding and TVC relay egress admission;
3. write-once ingress receipt;
4. direct event dispatch without claim/fence minting or a second WorkerCoordinator task;
5. TVC current-source double-Interlock validation;
6. exact sealed ciphertext persistence path under `_Vault/SKAP`;
7. DEVICE -> KV -> SKAP receipt lineage;
8. replay denial inherited from the TVC SKAP store;
9. organization control validation passing.

## Runtime evidence still required

No authentic `stegverse.kv-skap-custody.materialization-consumption/v1` receipt with state `ADMITTED_TO_SKAP_VAULT` has yet been observed in the organization repository evidence.

The next runtime goal is therefore one concrete event, not additional architecture:

```text
current resident roots present:
  STEGVERSE_STEGOS_ROOT
  STEGVERSE_TVC_ROOT
  STEGVERSE_KV_ROOT

plus:
  exact owner-sealed capsule
  validated DEVICE -> KV receipt
  TVC relay authorization reference

execute:
  scripts/dispatch_kv_skap_custody_materialization.py

observe:
  receipts/sovereign-network/kv-skap-custody-egress/<materialization_id>.json
  receipts/sovereign-network/kv-skap-custody-ingress/<materialization_id>.json
  receipts/sovereign-host/kv-skap-custody/<materialization_id>.json
  <STEGVERSE_KV_ROOT>/_Vault/SKAP/Credentials/coinbase/<operation_id>.json
  <STEGVERSE_KV_ROOT>/_Vault/SKAP/Receipts/coinbase/*
```

Only that authentic execution and exact readback may upgrade this lane from merged/validated source to runtime-observed SKAP custody.
