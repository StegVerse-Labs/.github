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


## 2026-09-21 fresh-Node My KV relationship-state repair

A real third registered Node exposed a source-semantic defect in the Site My KV Step 2 projection: a Node that had never had any KnowledgeVault relationship was being represented as `KV_INSTALLATION_NOT_VERIFIED` with `resident_kv_root_observed=true`, which incorrectly implied an existing KV relationship and exposed installation-receipt recovery.

Site PR #1450 repaired the existing DEVICE_KV path and merged as `f713330551999125b90868930927984bc33fba9d`. Exact-head Site validation was green before merge. Site PR #1451 then terminalized the temporary Site implementation claim and active COSV projection, merging as `0699af6abb554c4ece47228fd28d35c6135eded4`.

The installation-status projection now preserves three distinct non-authorizing states:

```text
KV_RELATIONSHIP_NOT_ESTABLISHED
  kv_relationship_established=false
  resident_kv_root_observed=false
  installation_receipt_present=false

KV_INSTALLATION_NOT_VERIFIED
  kv_relationship_established=true
  resident_kv_root_observed=true
  installation_receipt_present=false

KV_INSTALLATION_VERIFIED
  kv_relationship_established=true
  resident_kv_root_observed=true
  installation_receipt_present=true
```

A fresh registered Node now exposes explicit create-new-KV versus connect-existing-KV choices. Existing-KV installation-receipt recovery remains hidden until the owner deliberately selects that path or authentic DEVICE_KV relationship evidence is already present. `MY_KV_ONBOARDING_STEP_1_COMPLETED` remains Node onboarding evidence only and cannot create, attach, verify, or imply a KnowledgeVault relationship.

This repair does not satisfy or weaken any authentic parent runtime predicate. `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` remains `ACTIVE / CHECKED_OUT`; TV/TVC remains credential authority, Interlock/InTr remains transition authority, WorkerCoordinator remains claim/fence authority, and the authentic Device -> KV -> SKAP -> KV -> Device evidence chain remains outstanding.


## 2026-09-21 browser-origin installation truth correction

Authentic current-iPhone Safari evidence showed a distinct defect after the fresh-Node relationship-state repair: the Device KV page reported `State: INSTALLED` while also reporting `Storage: device-local-browser-indexeddb`, `Persistence: requested; granted=false`, and `Exact readback: true`. That was not an authentic device/native installation. It was origin-scoped IndexedDB initialization with successful byte readback.

Site PR #1452 repaired that semantic overclaim and merged as `290318a285089b45259a87811d11585f531b1261` after exact-head validation. Site PR #1453 terminalized the temporary Site claim/COSV projection and merged as `c0785763c72518364cf2ae5e7a5a8213907ed7ae`.

The browser helper now exposes:

```text
BROWSER_KV_NOT_INITIALIZED
BROWSER_KV_INITIALIZED_BEST_EFFORT
BROWSER_KV_INITIALIZED_PERSISTENCE_GRANTED
```

and never converts either browser-initialized state into `installed=true`. `installation_claimed=false` is explicit. A Safari persistence grant only classifies browser-origin durability; it is still not proof of a native app, filesystem service, background process, OS-level vault, or independently resident device runtime.

Exact readback remains useful evidence that the browser can recover the exact IndexedDB bytes it wrote. It is not installation proof. The My KV create path now says “Create browser-local KV”, and cloud-peer setup may consume that initialized local data instance without changing the installation claim.

The canonical parent Goal remains `ACTIVE / CHECKED_OUT`. No authentic Device -> KV -> SKAP -> KV -> Device runtime predicate was satisfied by this repair.


## .github import and validation isolation repair — 2026-09-21

A repository validation repair is staged under the existing Goal rather than creating a new runtime or authority lane. `scripts/execute_device_kv_skap_roundtrip_event.py` now adds its own `scripts/` directory to `sys.path` when imported by spec, matching its direct-script import behavior for bare sibling imports. The predecessor-closure test fixture now scopes its synthetic `heartbeat_runtime` modules with `patch.dict(...)` so they cannot leak into later tests and shadow the real package.

This repair changes source import/test isolation only. It does not establish authentic Device/KV/SKAP runtime execution, a KV relationship, native installation, WorkerCoordinator authority, Interlock/InTr admission, or TV/TVC credential evidence. The Goal remains `ACTIVE / CHECKED_OUT` and authentic runtime predicates remain evidence-gated.

## .github import and validation isolation merge reconciliation — 2026-09-21

PR #2565 merged as `4661a8eb839241c0bff188a991374f45fac1b334` from exact head `06d5f11eaad047934e3131a20ad243e04ff1fda3` after the branch was rebased onto current `main` to resolve a documentation-only base advance. Exact-head pull-request validations passed: `validate-deepseek-resident` run `35686779849` and `Validate KV AI Memory Resident Binding` run `35686779918`. Push validation run `35686765254` also passed.

The merged repair is limited to sibling-script import parity and isolation of the synthetic `heartbeat_runtime` test stub. It does not promote any authentic runtime predicate: no KV relationship, native installation, WorkerCoordinator claim/fence, Interlock/InTr admission, TV/TVC credential event, Device -> KV -> SKAP -> KV -> Device roundtrip, Master Records closure, or exact terminal readback is claimed from source/CI evidence. The Goal remains `ACTIVE / CHECKED_OUT`.

## Canonical execution-substrate registration reconciliation — 2026-09-21

Cross-Task Coordination run `35686885863` exposed a registry-conformance defect only: this existing runtime-capable Goal predated the mandatory `stegverse.execution-substrate-resolution/v1` field. The task already declared `CANONICAL_STEGOS_EVENT_EPHEMERAL_LANE` and `SOVEREIGN_CANONICAL_EVENT_EPHEMERAL_STEGOS_NODE_INVOCATION`; the canonical record now projects that existing choice as `selected_substrate_id=ADMITTED-EPHEMERAL-STEGOS-NODE`, preserves the canonical single-device-first review order, sets `external_device_required=false`, `second_user_operated_device_allowed=false`, and `authority_effect=NONE`.

This registration repair does not create a runtime, establish reachability, satisfy retained-Node evidence, or promote any authentic Device/KV/SKAP predicate. Earlier same-device substrates remain suitable or evidence-reachability-limited rather than being falsely declared unsuitable, and remote/external-device fallback remains not applicable.
