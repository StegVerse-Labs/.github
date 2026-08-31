# KV -> SKAP Vault Operational InTr Transport Mirror Handoff

Repository: `StegVerse-Labs/.github`
Branch: `feat/kv-skap-operational-transport-20260831`
Updated: 2026-08-31T17:44:00-05:00
State: ACTIVE_IMPLEMENTATION
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

## Runtime ownership

```text
shared profiled Universal InTr ingress
  -> write-once materialization receipt
  -> credential-scrubbed KV/SKAP consumer
  -> TVC current-source validation/gate
  -> same resident STEGVERSE_KV_ROOT
  -> _Vault/SKAP exact ciphertext custody + receipts
```

No GitHub runner, Render, Vercel, Cloudflare, HB carrier, or request grants execution or credential authority.

## Required implementation surfaces

- `scripts/consume_kv_skap_custody_materialization_request.py`
- `workers/universal_intr_profiled_ingress.py`
- `tests/test_kv_skap_custody_materialization.py`
- `control/worker-registry.d/kv-skap-custody-001.json`
- `control/process-worker-adapters.d/kv-skap-custody-001.json`
- `handoffs/KV-SKAP-CUSTODY-001.json`
- this handoff

## Completion evidence

Source completion requires:
1. exact canonical `kv-skap-custody` request validation;
2. write-once ingress receipt;
3. direct event dispatch without claim/fence minting or a second WorkerCoordinator task;
4. TVC current-source double-Interlock validation;
5. exact sealed ciphertext persisted unchanged under `_Vault/SKAP`;
6. DEVICE -> KV -> SKAP receipt lineage;
7. replay denial;
8. tests and organization validation passing.

Runtime activation remains separate and requires an authentic resident materialization receipt plus exact custody/readback evidence. The transport path intentionally does not register a separate WorkerCoordinator task: shared ingress performs bounded event dispatch directly, while TVC remains the downstream gate/custody authority.
