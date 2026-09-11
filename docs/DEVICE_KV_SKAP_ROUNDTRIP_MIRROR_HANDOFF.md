# Device <-> KV <-> SKAP Roundtrip Mirror Handoff

Updated: 2026-09-10

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

Persistent identity/continuity and ephemeral execution remain deliberately separate:

```text
PERSISTENT
retained Node identity / genesis / continuity generation / state commitment

EPHEMERAL
WorkerCoordinator claim/fence / canonical lease / InTr invocation / task process / provider session
```

A persistent server, always-on receiver, TestFlight deployment, Remote Desktop connector, Render/Vercel runtime, or second user-operated machine is not a prerequisite for this proof.

## Current merged source lineage

Transport/custody:

- StegOS #326 -> `2339f2f2fc8c28eb4d63077387013154dac9b75c`; four-leg roundtrip composition/verification.
- LLM-adapter #331 -> `f4db7005818c7b77bf7e25345c86df1277760a93`; secret-free canonical DEVICE->KV Gateway sidecar.
- TVC #377 -> `72aa78c8f60226621c19d58751ec776f777583f9`; sidecar validation and sole SKAP ciphertext custody writer.
- `.github` #1332 -> `42996a4582e2fb9e4d3207dd3e45b764dc727723`; WorkerCoordinator task registration/verification.
- `.github` #1339 -> `861647893df88c30f591e374a8be30fccaf7c64f`; false persistent-receiver prerequisite removed.
- `.github` #1352 -> `ec7594aac88b8d60b0d230be15f7901f1040b0fa`; bounded event executor/COSV reconciliation.
- `.github` #1371 -> `f00ab3f885f172a4703b8ae1b83e5676f3341eba`; authentic Gateway/TVC input pair made explicit prerequisite.

Canonical runtime / WorkerCoordinator:

- StegOS #332 -> `288a5a32c8c89bf0e44176330ce99bf487e4cc6c`; initial Node capability bridge.
- StegOS #333 -> `f955068eb23556458434e22d25d696ce9ff5cc9d`; canonical runtime lease separated from per-transition Interlock/InTr admission.
- `.github` #1399 -> `b273b35fbe96010ca136e84e3d48914d087a00fd`; roundtrip worker consumes exact fenced `stegverse.worker-invocation/v0.1` and emits canonical worker response.
- StegOS #334 -> `18020e50bc5732216abeb5c2f00e6ec2ea91a11a`; bridge absorbed into pre-existing Canonical Runtime Lane; no parallel runtime lifecycle.
- `.github` #1400 -> `97f47cbc28fdaf95535a04b48fbe5368f27fc8d5`; canonical ownership collision reconciliation.
- `.github` #1401 -> `2e4997dc50687ec6e4972f2b63f2e515bb6491bd`; one-shot terminal proof parser repaired for actual WorkerCoordinator cycle evidence.
- StegOS #335 -> `abeeed3bc57f7e9bac191f61b6acfd7754bbe644`; same-device local sovereign EVENT_EPHEMERAL adapter; `RendezvousRequirement.NOT_REQUIRED`, no relay/public route dependency.
- StegOS #336 -> `c1a5393f970f2f9eb3e10f0945a4371bfb120f08`; exact-head CI `34563132304` SUCCESS. Merged `stegos/device_kv_skap_canonical_runtime.py`, including exact WorkerCoordinator claim/fence derivation, exact canonical lease-ID binding, non-secret path forwarding, hosted-runtime refusal, worker-response verification, and terminal proof exact readback.
- `.github` #1403 -> `002c928ba387080fcabc557002abc1df58301b64`; exact-head deterministic suite `34563316067`, organization-control `34563316089`, and Heartbeat Worker validation `34563316085` all SUCCESS. Registered `workers/run_device_kv_skap_canonical_runtime_worker.py` as the WorkerCoordinator entrypoint and delegated domain semantics to merged StegOS #336 rather than duplicating the bridge.

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

-> build_runtime_admission_from_lease_snapshot

-> exact same lease ID
-> DeviceKVSKAPCanonicalRuntimeCapability
-> WorkerCoordinatorCanonicalRuntimeBridge

-> existing workers/run_device_kv_skap_roundtrip_worker.py

-> existing scripts/continue_device_kv_skap_from_tvc_custody.py

-> canonical Interlock/InTr admissions per hop

-> stegverse.device-kv-skap.runtime-roundtrip-proof/v1
   state = DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED

-> bridge receipt retained
-> canonical lease evidence retained before teardown
-> lease closes
```

Only non-secret path bindings are admitted:

```text
STEGVERSE_DEVICE_KV_SKAP_RUNTIME_ROOT
STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_OUTPUT
STEGVERSE_DEVICE_KV_SKAP_GATEWAY_SIDECAR
STEGVERSE_DEVICE_KV_SKAP_TVC_DRAIN_RECEIPT
STEGVERSE_STEGOS_ROOT
STEGVERSE_DEVICE_KV_SKAP_INTR_MATERIALIZATION
STEGVERSE_DEVICE_KV_SKAP_RETAINED_NODE
STEGVERSE_DEVICE_KV_SKAP_CANONICAL_LEASE_SNAPSHOT
STEGVERSE_DEVICE_KV_SKAP_BRIDGE_RECEIPT
```

No token, password, private key, provider credential value, or GitHub credential is part of these bindings.

## Node Manifold collision boundary

`STEGOS-NODE-MANIFOLD-001` remains the separate owner of physical multi-node/network-manifold proof: distinct second active Node, `NETWORK_PRESENT`, fragmentation/reformation, and exact multi-node replay/reconstruction. This task may reuse retained-Node and Interlock/InTr primitives but must not claim Node-Manifold completion.

## Authentic prerequisite pair

Runtime execution requires one authentic matching pair:

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

Canonical TVC producer:

```text
StegVerse-Labs/TVC/tools/coinbase_gateway_stage_drain.py
```

Canonical receipt tree:

```text
_Vault/SKAP/Receipts/coinbase-drain
```

Recipient-key/liveness/public-route/stage-drain activation remains owned by the existing:

```text
StegVerse-Labs/TVC/tasks/TVC-COINBASE-RESIDENT-ACTIVATION-091.json
```

This task consumes that evidence and must not create a duplicate TVC runtime owner. Fixture, reconstruction, repository-only synthetic packet, GitHub Actions artifact, hosted substitute, or fabricated receipt is not eligible.

## Completion contract

One authentic bounded operation must prove:

```text
1 DEVICE->KV receipt
2 KV->SKAP receipt chained to #1
3 SKAP->KV receipt chained to #2
4 KV->DEVICE receipt chained to #3
all packet bytes match intent hashes
all governed transitions admitted by Interlock/InTr
SKAP exact ciphertext/reference readback verified
KV exact return readback verified
TV/TVC credential authority preserved
TVC single ciphertext custody writer preserved
credential plaintext absent from ordinary transport/evidence
retained Node identity/continuity binding preserved
fresh WorkerCoordinator claim/fence preserved
canonical EVENT_EPHEMERAL lease preserved
exact same lease ID bound through the domain capability
bridge receipt retained
bridge/domain binding own no runtime/transition/credential authority
canonical runtime evidence retained before teardown
canonical lease closes cleanly
persistent transport process required = false
always-on receiver required = false
hosted_runtime_used = false
second_user_operated_device_used = false
terminal state = DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED
```

## Current source state

```text
SOURCE_INTEGRATION_COMPLETE
```

There is no remaining repository/source implementation blocker currently known for the canonical execution chain. New source work is warranted only if authentic runtime execution exposes a real defect.

## Current authentic evidence conditions

```text
AUTHENTIC_CURRENT_DEVICE_GATEWAY_SIDECAR_NOT_YET_OBSERVED
AUTHENTIC_TVC_CANONICAL_ROUNDTRIP_ELIGIBLE_DRAIN_RECEIPT_NOT_YET_OBSERVED
AUTHENTIC_FOUR_LEG_INTR_ROUNDTRIP_NOT_YET_OBSERVED
AUTHENTIC_SKAP_KV_RETURN_RECEIPT_NOT_YET_OBSERVED
KV_SKAP_TERMINAL_EXACT_READBACK_NOT_YET_OBSERVED
```

The following are explicitly not blockers for this proof:

```text
PHYSICAL_RUNTIME_NOT_PRESENT
ALWAYS_ON_RECEIVER_NOT_PRESENT
TESTFLIGHT_NOT_INSTALLED
REMOTE_DESKTOP_NOT_CONNECTED
SECOND_DEVICE_NOT_PRESENT
```

## Next

1. Produce or locate one authentic current-device Gateway sidecar plus matching TVC `ADMITTED_TO_SKAP_VAULT_CUSTODY` / `canonical_roundtrip_eligible=true` receipt through the existing TVC activation owner.
2. Materialize/consume authentic retained-Node, Universal InTr materialization, and canonical open-lease evidence.
3. Execute the registered WorkerCoordinator -> StegOS canonical lane/domain consumer with the authentic pair.
4. Retain bridge + canonical lease + four-hop + SKAP/KV exact-readback evidence through canonical closure.
5. Close evidence conditions only when terminal verification returns `DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED`.

## README

Root `README.md` was reviewed during the source integration. The changes are internal runtime/coordination wiring and do not alter repository-facing framework principles, so no README prose change is required.

## Manual work

None. Do not enter provider credentials into chat, GitHub, Drive, ordinary KV, logs, screenshots, or repository state. Any eventual owner credential entry remains browser-local sealing only after authentic ingress-readiness predicates are satisfied.
