# Device <-> KV <-> SKAP Roundtrip Mirror Handoff

Updated: 2026-09-11

```text
goal_id: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
parent_goal: KV-CONNECTION-REVALIDATION-WORKER-001
cosv_id: 50000000102000
state: ACTIVE
checkout_state: CHECKED_OUT
canonical_owner: StegVerse-Labs/.github
implementation_owner: StegVerse-Labs/StegOS
canonical_runtime_lifecycle_owner: StegVerse-Labs/StegOS/stegos/canonical_runtime_lane.py
domain_binding_owner: StegVerse-Labs/StegOS/stegos/device_kv_skap_canonical_runtime.py
worker_entrypoint: workers/run_device_kv_skap_canonical_runtime_worker.py
worker_claim_authority: WorkerCoordinator
transition_authority: Interlock/InTr
credential_authority: TV/TVC
github_runtime_authority: NONE
hosted_runtime_fallback: NONE
second_user_operated_device_required: false
persistent_transport_runtime_required: false
event_ephemeral_materialization_allowed: true
source_integration_complete: true
ios_recipient_capability_source_complete: true
authentic_runtime_complete: false
```

## Goal

Prove one authentic sovereign operation lineage:

```text
DEVICE_SYSTEM -> KV -> SKAP_VAULT -> KV -> DEVICE_SYSTEM
```

Completion requires four adjacent canonical InTr receipts, exact packet/readback verification, one continuous receipt-hash chain, authentic retained-Node continuity, a fresh WorkerCoordinator claim/fence, canonical EVENT_EPHEMERAL lease evidence, TV/TVC credential authority, no secret plaintext in ordinary KV/device/repository state, no authority transfer, no hosted fallback, and no second user-operated device.

## Canonical runtime and authority ownership

```text
Canonical Runtime Lane
  -> runtime lease lifecycle / materialization / evidence retention / teardown

WorkerCoordinator
  -> fresh task claim / fence

WorkerCoordinatorCanonicalRuntimeBridge
  -> binds exact claim/fence + exact open lease + retained Node + domain capability

DeviceKVSKAPCanonicalRuntimeCapability
  -> Device/KV/SKAP bounded domain execution only

Interlock/InTr
  -> each governed hop / transition admission

TV/TVC
  -> credential authority
  -> TVC remains sole SKAP ciphertext custody writer

retained StegOS Node
  -> identity / genesis / continuity / evidence lineage

GitHub / CI / HeartBeat
  -> source validation / evidence / observation only
```

An open runtime lease does not grant transition authority. The bridge and domain capability mint no claim/fence, open no lease, grant no Interlock/InTr admission, and carry no credential authority.

Persistent identity/continuity and ephemeral execution remain deliberately separate. A persistent server, always-on receiver, TestFlight deployment, Remote Desktop connector, Render/Vercel runtime, or second user-operated machine is not a prerequisite for this proof.

## Current merged source lineage

Transport/custody:

- StegOS #326 -> `2339f2f2fc8c28eb4d63077387013154dac9b75c`; four-leg roundtrip composition/verification.
- LLM-adapter #331 -> `f4db7005818c7b77bf7e25345c86df1277760a93`; secret-free canonical DEVICE->KV Gateway sidecar.
- TVC #377 -> `72aa78c8f60226621c19d58751ec776f777583f9`; sidecar validation and sole SKAP ciphertext custody writer.
- `.github` #1352 -> `ec7594aac88b8d60b0d230be15f7901f1040b0fa`; bounded event executor/COSV reconciliation.
- `.github` #1371 -> `f00ab3f885f172a4703b8ae1b83e5676f3341eba`; authentic Gateway/TVC input pair made explicit prerequisite.

Canonical runtime / WorkerCoordinator:

- StegOS #332 -> `288a5a32c8c89bf0e44176330ce99bf487e4cc6c`; initial Node capability bridge.
- StegOS #333 -> `f955068eb23556458434e22d25d696ce9ff5cc9d`; canonical runtime lease separated from per-transition Interlock/InTr admission.
- `.github` #1399 -> `b273b35fbe96010ca136e84e3d48914d087a00fd`; roundtrip worker consumes exact fenced `stegverse.worker-invocation/v0.1` and emits canonical worker response.
- StegOS #334 -> `18020e50bc5732216abeb5c2f00e6ec2ea91a11a`; bridge absorbed into the pre-existing Canonical Runtime Lane.
- `.github` #1400 -> `97f47cbc28fdaf95535a04b48fbe5368f27fc8d5`; canonical ownership collision reconciliation.
- `.github` #1401 -> `2e4997dc50687ec6e4972f2b63f2e515bb6491bd`; one-shot terminal proof parser repair.
- StegOS #335 -> `abeeed3bc57f7e9bac191f61b6acfd7754bbe644`; same-device local sovereign EVENT_EPHEMERAL adapter; no relay/public route dependency.
- StegOS #336 -> `c1a5393f970f2f9eb3e10f0945a4371bfb120f08`; exact-head CI `34563132304` SUCCESS. Merged the canonical runtime domain binding, exact claim/fence and lease-ID binding, hosted-runtime refusal, worker-response verification, and terminal exact-readback validation.
- `.github` #1403 -> `002c928ba387080fcabc557002abc1df58301b64`; deterministic suite `34563316067`, organization-control `34563316089`, and Heartbeat Worker validation `34563316085` all SUCCESS. Registered the WorkerCoordinator canonical runtime entrypoint.

Current-iPhone TVC recipient capability:

- `.github` #1420 -> `f75426b62862047fcc999e44f085fa69ff2c23a2`; registered `TVC-IOS-OPAQUE-RECIPIENT-CAPABILITY-001`.
- StegOS #338 -> `9b532806f3c7d71dd7ae90ecc5ba76192b6027a7`; Secure-Enclave-only P-256 candidate source.
- StegOS #339 -> `cff17eb68ac156bd60e6db388dfefeefb71ea01b`; StegOSMobile target integration and Apple-toolchain validation.
- StegOS #340 -> `01fc87a88cd956d83fb3206082513e9de59c0647`; TVC-challenge-bound proof-of-possession signing.
- TVC #407 -> `3fbdba0cb539b3672b53c3aa29e948e58e4fdb8e`; TVC-owned challenge issuer/verifier/adopter and Coinbase activation-seam binding.
- StegOS #341 -> `a43b203d7c6d738f8c571d64b1669bd6285fc9ff`; bounded current-iPhone invocation through the existing `stegverse` URL scheme. Exact head `710fc16d4c3c7cca07257e7575e8914859d76846` passed StegOS CI `34612835986`, GADI native boundary defense `34612835913`, iOS Device Package Validation `34612836055`, and iOS Apple Toolchain Validation `34612835919`.

Source/CI do not constitute authentic Device->KV->SKAP->KV->Device runtime proof.

## Canonical WorkerCoordinator -> StegOS execution chain

```text
exact WorkerCoordinator invocation
  schema = stegverse.worker-invocation/v0.1
  exact claim_id + fencing_token

-> workers/run_device_kv_skap_canonical_runtime_worker.py
-> authentic retained-Node object
-> authentic Universal InTr materialization object
-> authentic canonical LEASE_OPEN snapshot
-> exact same lease ID
-> DeviceKVSKAPCanonicalRuntimeCapability
-> WorkerCoordinatorCanonicalRuntimeBridge
-> workers/run_device_kv_skap_roundtrip_worker.py
-> scripts/continue_device_kv_skap_from_tvc_custody.py
-> canonical Interlock/InTr admissions per hop
-> stegverse.device-kv-skap.runtime-roundtrip-proof/v1
   state = DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED
-> bridge receipt retained
-> canonical lease evidence retained before teardown
-> lease closes
```

Only non-secret path bindings are admitted. No token, password, private key, provider credential value, or GitHub credential is part of those bindings.

## Authentic prerequisite sequence

The parent runtime cannot yet consume an authentic Gateway/TVC input pair because current-iPhone TVC recipient activation is not yet observed. The source path to produce it is now complete.

Close these predicates in order:

```text
1 AUTHENTIC_CURRENT_IPHONE_TVC_RECIPIENT_ACTIVATION_OBSERVED
2 AUTHENTIC_TVC_CHALLENGE_EXCHANGE_VERIFIED
3 TVC_PUBLIC_RECIPIENT_CONFIG_PROJECTED_FROM_AUTHENTIC_EXCHANGE
4 AUTHENTIC_CURRENT_DEVICE_GATEWAY_CANONICAL_SIDECAR_OBSERVED
5 AUTHENTIC_TVC_CANONICAL_ROUNDTRIP_ELIGIBLE_DRAIN_RECEIPT_OBSERVED
6 AUTHENTIC_FOUR_LEG_INTR_ROUNDTRIP_OBSERVED
7 AUTHENTIC_SKAP_KV_RETURN_RECEIPT_OBSERVED
8 KV_SKAP_TERMINAL_EXACT_READBACK_OBSERVED
```

The current-iPhone exchange is owned by `TVC-IOS-OPAQUE-RECIPIENT-CAPABILITY-001`. It must use the merged Secure Enclave candidate/challenge-signing route and TVC #407 verifier/adopter. GitHub Actions artifacts, fixtures, reconstructions, hosted substitutes, or fabricated receipts are not eligible runtime evidence.

After the public recipient configuration is authentically projected, the existing TVC activation owner may produce the canonical Gateway sidecar plus matching terminal drain receipt:

```text
A. Gateway sidecar
schema = stegverse.service-gateway.device-kv-canonical-stage/v1
canonical DEVICE_SYSTEM -> KV intent + RECEIVED receipt
credential_material_present = false
authority_effect = NONE_EVIDENCE_ONLY

B. TVC terminal drain receipt
status = ADMITTED_TO_SKAP_VAULT_CUSTODY
canonical_roundtrip_eligible = true
canonical_device_kv_binding.receipt_hash matches A
credential_persistence_ref points to exact TVC-written SKAP ciphertext
```

Canonical TVC producer remains `StegVerse-Labs/TVC/tools/coinbase_gateway_stage_drain.py`; TV/TVC remains credential authority and sole SKAP ciphertext custody writer.

## Completion contract

One authentic bounded operation must prove four chained Device/KV/SKAP/KV/Device receipts; exact packet bytes against intent hashes; Interlock/InTr admission for every governed hop; exact SKAP ciphertext/reference and KV return readback; TV/TVC credential authority and single-writer custody; no credential plaintext in ordinary evidence; retained Node continuity; fresh WorkerCoordinator claim/fence; canonical EVENT_EPHEMERAL lease and exact lease-ID binding; retained bridge and lease evidence; clean teardown; no hosted runtime; no second user-operated device; and terminal state `DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED`.

## Current source state

```text
SOURCE_INTEGRATION_COMPLETE
IOS_RECIPIENT_CAPABILITY_SOURCE_COMPLETE
NATIVE_CURRENT_IPHONE_INVOCATION_SOURCE_COMPLETE
```

There is no known remaining repository/source implementation blocker in the canonical chain. New source work is warranted only if authentic current-iPhone or roundtrip execution exposes a real defect.

## Current authentic evidence conditions

```text
AUTHENTIC_CURRENT_IPHONE_TVC_RECIPIENT_ACTIVATION_NOT_YET_OBSERVED
AUTHENTIC_TVC_CHALLENGE_EXCHANGE_NOT_YET_OBSERVED
AUTHENTIC_CURRENT_DEVICE_GATEWAY_SIDECAR_NOT_YET_OBSERVED
AUTHENTIC_TVC_CANONICAL_ROUNDTRIP_ELIGIBLE_DRAIN_RECEIPT_NOT_YET_OBSERVED
AUTHENTIC_FOUR_LEG_INTR_ROUNDTRIP_NOT_YET_OBSERVED
AUTHENTIC_SKAP_KV_RETURN_RECEIPT_NOT_YET_OBSERVED
KV_SKAP_TERMINAL_EXACT_READBACK_NOT_YET_OBSERVED
```

The following are explicitly not blockers for this proof:

```text
ALWAYS_ON_RECEIVER_NOT_PRESENT
TESTFLIGHT_NOT_INSTALLED
REMOTE_DESKTOP_NOT_CONNECTED
SECOND_DEVICE_NOT_PRESENT
HOSTED_RUNTIME_NOT_PRESENT
```

## Next

1. Execute the merged bounded recipient-capability route on the current iPhone and retain the public Secure Enclave candidate artifact.
2. Complete one fresh TVC #407 challenge/proof-of-possession verification using that same opaque key handle; project the public recipient configuration only after successful verification.
3. Produce the authentic current-device Gateway sidecar plus matching TVC `ADMITTED_TO_SKAP_VAULT_CUSTODY` / `canonical_roundtrip_eligible=true` receipt through the existing TVC activation owner.
4. Materialize/consume authentic retained-Node, Universal InTr materialization, and canonical open-lease evidence.
5. Execute the registered WorkerCoordinator -> StegOS canonical lane/domain consumer with the authentic pair.
6. Retain bridge + canonical lease + four-hop + SKAP/KV exact-readback evidence through canonical closure, and close only on `DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED`.

## README

StegOS #341 updated the StegOS README for the bounded current-iPhone exchange and TVC #407 updated TVC documentation for verifier/adopter behavior. The `.github` root README was reviewed during this coordination reconciliation; no organization-level principle, authority model, or generic runtime contract changed, so no additional root README prose change is required.

## Manual work

None at this coordination stage. Do not enter provider credentials, private-key material, Secure Enclave secrets, or raw key bytes into chat, GitHub, Drive, ordinary KV, logs, screenshots, or repository state. Any eventual owner credential entry remains browser-local sealing only after authentic ingress-readiness predicates are satisfied.
