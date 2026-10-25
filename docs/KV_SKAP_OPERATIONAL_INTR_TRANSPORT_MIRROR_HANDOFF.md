# KV -> SKAP Vault Operational In-KV SKAP Gate Transport Mirror Handoff

Repository: `StegVerse-Labs/.github`
Canonical merge: `3ec15ed7937fa621a215f78b4992a6e3af63566f` (original transport, PR #716)
Updated: 2026-10-25 (laned/kv-skap-roundtrip-device-kv-consumer, PROVISIONAL_ON_RULING_C)
State: SOURCE_REBOUND_TO_TWO_LEG_ROUNDTRIP / AUTHENTIC_RESIDENT_KV_SKAP_EVENT_NOT_YET_OBSERVED
Credential authority: TV/TVC
Authority effect: NONE

## Goal

KV and the SKAP Vault are one organisation, so KV <-> SKAP is the in-KV SKAP gate and never an InTr hop
(StegVerse-org/.github#167 ruling c6393224851 (3); Coordination ruling C, PROVISIONAL_ON_RULING_C). The
credential-custody round trip has two InTr legs. The in-KV gate exchange between them is bound by the sha256
of its exact bytes:

```text
DEVICE_SYSTEM
  -> device-kv (InTr leg 1)
  -> KV / KnowledgeVault:Interlock
       in-KV SKAP gate: KnowledgeVault:SKAPClient -> SKAP:Vault (TVC custody, exact readback)
       gate exchange record, kv_skap_gate_exchange_hash = sha256(exact bytes)
  -> device-kv response (InTr leg 2, prior = DEVICE->KV terminal receipt, payload carries the gate hash)
  -> DEVICE_SYSTEM
```

The `.github` organization boundary owns ingress/egress and event dispatch. It does not own credential
plaintext, credential authority, provider execution or SKAP admission policy. No Labs source resolves the
retired StegOS profiles `kv-skap`, `kv-skap-custody` or `kv-skap-account-metadata` (retired in
StegVerse-Labs/StegOS#428). The only StegOS connector profile used is `device-kv`.

## Canonical upstream contracts

- StegOS `device-kv` connector profile (owned outside this repository), used for both InTr legs.
- TVC double-Interlock gate:
  - the DEVICE -> KV receipt must validate;
  - the KV -> SKAP_VAULT receipt must chain to DEVICE -> KV;
  - the KV -> SKAP_VAULT connector is the in-KV SKAP gate `KV_INTERNAL_SKAP_GATE`, never InTr (TVC#544);
  - secret plaintext is forbidden;
  - authority transfer is forbidden.
- TVC SKAP store:
  - the storage backend id must begin `KV_SKAP_GATE_`;
  - exact ciphertext readback is required;
  - replay is denied.

## Operational source path

```text
validated DEVICE -> KV boundary receipt + canonical DEVICE_SYSTEM -> KV hop receipt
+ exact sealed capsule
  -> scripts/dispatch_kv_skap_custody_materialization.py   (gate request stegverse.kv-skap-gate.custody-request/v1; no InTr intent)
  -> scripts/consume_kv_skap_custody_materialization_request.py admit()   (write-once gate admission, credential-scrubbed dispatch)
  -> consume_one: current local TVC double-Interlock validation, _Vault/SKAP exact ciphertext custody + readback
  -> scripts/materialize_kv_skap_canonical_return.py        (gate exchange bound to the DEVICE->KV receipt)
  -> scripts/materialize_kv_device_from_skap_return.py      (KV persist/readback, device-kv response leg)
```

The TVC-drain continuation `scripts/continue_device_kv_skap_from_tvc_custody.py` follows the same two-leg
shape. `workers/device_kv_skap_roundtrip_verifier.py` (input/proof v2) verifies it and fails closed on any
`kv_skap` or `skap_kv` InTr leg.

The shared ingress `workers/universal_intr_profiled_ingress.py` no longer advertises or routes
`KV:SKAPCiphertextCustody`. No second WorkerCoordinator task is introduced, and admission mints no claim or
fence. No GitHub runner, Render, Vercel, Cloudflare, HB carrier or request grants execution or credential
authority.

## Runtime evidence still required

No authentic `stegverse.kv-skap-gate.custody-consumption/v1` receipt with state `ADMITTED_TO_SKAP_VAULT` and
`canonical_return_state` `KV_TO_DEVICE_RETURN_PERSISTED` has been observed yet. The first concrete event
runs the dispatcher on a resident host (STEGVERSE_STEGOS_ROOT, STEGVERSE_TVC_ROOT and STEGVERSE_KV_ROOT
present). It is then observed at:

```text
receipts/sovereign-network/kv-skap-gate-dispatch/<materialization_id>.json
receipts/sovereign-host/kv-skap-gate-admission/<materialization_id>.json
receipts/sovereign-host/kv-skap-gate-custody/<materialization_id>.json
receipts/sovereign-host/device-kv-skap-roundtrip/<materialization_id>/kv-skap-gate-exchange.json
<STEGVERSE_KV_ROOT>/_Vault/SKAP/Credentials/coinbase/<operation_id>.json
```

Only that authentic execution and its exact readback may upgrade this lane to runtime-observed SKAP custody.

## KV -> SKAP Vault gate naming (laned/kv-skap-gate-roundtrip-rename)

The KV -> SKAP Vault step is the in-KV SKAP gate (the SKAP Vault sits inside KV), not an InTr hop, so the client names
here describe that gate. Retired names, held absent by `tests/test_kv_skap_gate_client_naming.py` with no aliases:

- env `STEGVERSE_DEVICE_KV_SKAP_INTR_MATERIALIZATION` -> `STEGVERSE_DEVICE_KV_SKAP_MATERIALIZATION` (read by
  `workers/run_device_kv_skap_canonical_runtime_worker.py`; not secret- or variable-backed in any workflow, so renamed in code;
  a resident host that exported the old name must export the new one);
- `scripts/dispatch_kv_skap_custody_materialization.py` no longer describes the event as an InTr custody event (file name kept).

Registry component `kv-skap-bidirectional-intr` -> `kv-skap-gate-roundtrip` (Coordination ruling (1), StegVerse-org/.github#167
c6393224851): renamed at canonical-task-registry generation 321 in the registry, the STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001 record and
the KV-SKAP-VAULT-FUNCTIONAL-001 adjacency ruling (evidence_digest re-sealed with `scripts/adjacency_ruling.py digest`); the six
i1 goal manifest requests are re-sealed at observed generation 321 in the same change. No alias.

Kept unchanged: the StegOS-owned profile/module names (`specs/universal-intr-connector-profiles.v1.json`, `stegos/universal_intr_*`).
