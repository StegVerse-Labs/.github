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
worker_claim_authority: WorkerCoordinator
transition_authority: Interlock/InTr
credential_authority: TV/TVC
github_runtime_authority: NONE
hosted_runtime_fallback: NONE
second_user_operated_device_required: false
persistent_transport_runtime_required: false
event_ephemeral_materialization_allowed: true
```

## Goal

Prove one authentic sovereign operation lineage:

```text
DEVICE_SYSTEM -> KV -> SKAP_VAULT -> KV -> DEVICE_SYSTEM
```

Completion requires four adjacent canonical InTr receipts, exact packet/readback verification, one continuous receipt-hash chain, authentic retained-Node continuity, a fresh WorkerCoordinator claim/fence, canonical EVENT_EPHEMERAL lease evidence, TV/TVC credential authority, no secret plaintext in ordinary KV/device/repository state, no authority transfer, no hosted fallback, and no second user-operated device.

## Canonical runtime / authority separation

Persistent identity and continuity belong to the retained StegOS Node. Runtime materialization is bounded and event-ephemeral. The canonical runtime lifecycle is owned by `stegos/canonical_runtime_lane.py` plus `LeaseMachine`; this task must not create a competing runtime.

Authority layers remain:

```text
Canonical Runtime Lane -> runtime lease lifecycle / teardown
WorkerCoordinator -> task claim/fence
WorkerCoordinatorCanonicalRuntimeBridge -> binds exact claim/fence + open lease + retained Node + capability
DeviceKVSKAPCanonicalRuntimeCapability -> Device/KV/SKAP domain binding only
Interlock/InTr -> per-hop governed transition admission
TV/TVC -> credential authority and sole TVC SKAP ciphertext custody writer
retained StegOS Node -> identity/continuity/evidence lineage
GitHub/CI/HB -> source validation / evidence / observation only
```

An open runtime lease grants no transition authority. The bridge and domain binding mint no claim/fence, open no lease, grant no Interlock/InTr admission, and carry no credential authority.

## Merged lineage

Transport/custody:

- StegOS #326 -> `2339f2f2fc8c28eb4d63077387013154dac9b75c`; four-leg roundtrip composition/verification.
- LLM-adapter #331 -> `f4db7005818c7b77bf7e25345c86df1277760a93`; secret-free DEVICE->KV Gateway sidecar.
- TVC #377 -> `72aa78c8f60226621c19d58751ec776f777583f9`; sidecar validation and sole SKAP ciphertext custody writer.
- `.github` #1332 -> `42996a4582e2fb9e4d3207dd3e45b764dc727723`; WorkerCoordinator registration/verification.
- `.github` #1339 -> `861647893df88c30f591e374a8be30fccaf7c64f`; false persistent-receiver prerequisite removed.
- `.github` #1352 -> `ec7594aac88b8d60b0d230be15f7901f1040b0fa`; bounded event executor/COSV reconciliation.
- `.github` #1371 -> `f00ab3f885f172a4703b8ae1b83e5676f3341eba`; authentic Gateway/TVC input pair made explicit prerequisite.
- Site #1196 -> `064f77f24b9ad505d2533bc4efc4a46f74c76799`; provider-neutral MyKV federation source.
- Site #1227 -> `64701e9e9896af0e0e97672706918b9417540cf3`; Site implementation claim released while this child remains ACTIVE.

Canonical runtime / WorkerCoordinator:

- StegOS #332 -> `288a5a32c8c89bf0e44176330ce99bf487e4cc6c`; WorkerCoordinator/Node capability bridge source.
- StegOS #333 -> `f955068eb23556458434e22d25d696ce9ff5cc9d`; runtime lease separated from transition admission.
- `.github` #1399 -> `b273b35fbe96010ca136e84e3d48914d087a00fd`; exact fenced `stegverse.worker-invocation/v0.1` and canonical worker response support.
- StegOS #334 -> `18020e50bc5732216abeb5c2f00e6ec2ea91a11a`; bridge absorbed into pre-existing Canonical Runtime Lane.
- `.github` #1400 -> `97f47cbc28fdaf95535a04b48fbe5368f27fc8d5`; canonical runtime ownership reconciliation.
- `.github` #1401 -> `2e4997dc50687ec6e4972f2b63f2e515bb6491bd`; one-shot wrapper terminal proof repaired for actual WorkerCoordinator cycle evidence.
- StegOS #335 -> `abeeed3bc57f7e9bac191f61b6acfd7754bbe644`; local-only sovereign EVENT_EPHEMERAL adapter with `RendezvousRequirement.NOT_REQUIRED` and no relay/public-route dependency.
- StegOS #336 -> `c1a5393f970f2f9eb3e10f0945a4371bfb120f08`; exact-head StegOS CI `34563132304` SUCCESS. Added `stegos/device_kv_skap_canonical_runtime.py`, binding the exact fenced WorkerCoordinator invocation to the already-open canonical lease, same lease ID, retained Node, authentic materialization, and existing roundtrip worker. It verifies exact terminal proof readback and preserves Interlock/InTr + TV/TVC authority boundaries.

No source merge or CI result above is authentic Device->KV->SKAP->KV->Device runtime proof.

## Current `.github` integration under PR #1403

Branch `feat/device-kv-skap-canonical-domain-binding-001` changes the registered process adapter to:

```text
command = python workers/run_device_kv_skap_canonical_runtime_worker.py
```

The `.github` wrapper is intentionally thin. It consumes the exact WorkerCoordinator invocation plus authentic non-secret evidence paths and delegates domain semantics to merged StegOS #336:

```text
StegOS module:
  stegos.device_kv_skap_canonical_runtime

StegOS API:
  DeviceKVSKAPCanonicalRuntimeCapability
  execute_bound_device_kv_skap_roundtrip
  worker_claim_from_invocation
  build_runtime_admission_from_lease_snapshot
```

Required non-secret bindings:

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

The wrapper:

1. validates the exact fenced WorkerCoordinator invocation through the existing domain worker contract;
2. loads the merged StegOS #336 domain binding from the supplied local StegOS root;
3. independently requires StegOS to derive the same claim/fence from the exact invocation;
4. derives runtime admission only from the authentic canonical open-lease snapshot;
5. binds the capability to that exact canonical lease ID;
6. delegates one bounded execution to StegOS #336;
7. requires `DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED` from the StegOS bridge result;
8. reconstructs the outer WorkerCoordinator response and requires its hash to equal the exact worker response hash observed by StegOS;
9. persists the bridge receipt write-once and adds it to the outer WorkerCoordinator evidence refs.

It does not instantiate `LeaseMachine`, reimplement `WorkerCoordinatorCanonicalRuntimeBridge`, mint/renew a claim/fence, open a lease, create a route, launch a second runtime lifecycle, grant Interlock/InTr admission, resolve credentials, or write SKAP ciphertext custody.

## Node Manifold non-collision boundary

`STEGOS-NODE-MANIFOLD-001` remains the separate owner of distinct-second-node, `NETWORK_PRESENT`, fragmentation/reformation, and exact multi-node replay/reconstruction proof. This roundtrip may reuse retained-Node and Interlock/InTr primitives but must not claim physical-network completion.

## Authentic prerequisite pair

Runtime execution still requires one authentic matching pair:

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

Canonical TVC producer remains `StegVerse-Labs/TVC/tools/coinbase_gateway_stage_drain.py`; receipt tree `_Vault/SKAP/Receipts/coinbase-drain`.

Coinbase recipient-key/liveness/public-route/stage-drain activation remains owned by the existing `StegVerse-Labs/TVC/tasks/TVC-COINBASE-RESIDENT-ACTIVATION-091.json` lane. This goal consumes that authentic evidence and must not duplicate its runtime owner.

Fixture, reconstruction, GitHub Actions artifact, hosted substitute, or synthetic packet is not eligible.

## Completion contract

One authentic bounded execution must prove:

```text
DEVICE->KV receipt
KV->SKAP receipt chained to DEVICE->KV
SKAP->KV receipt chained to KV->SKAP
KV->DEVICE receipt chained to SKAP->KV
exact packet bytes match intent hashes
all governed transitions admitted by Interlock/InTr
SKAP exact ciphertext/reference readback verified
KV exact return readback verified
TV/TVC credential authority preserved
TVC single ciphertext custody writer preserved
credential plaintext absent from ordinary transport/evidence
retained Node identity/continuity binding preserved
fresh WorkerCoordinator claim/fence preserved
canonical EVENT_EPHEMERAL lease preserved
exact same lease ID bound to domain capability
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

## Current source condition

```text
WORKERCOORDINATOR_STEGOS_DOMAIN_INTEGRATION_PR_1403_VALIDATION_PENDING
```

The StegOS domain binding itself is merged and exact-head validated through #336. Only the `.github` WorkerCoordinator entrypoint integration on #1403 remains source-pending. Source/CI still do not satisfy any authentic runtime predicate.

## Current authentic evidence conditions

```text
AUTHENTIC_CURRENT_DEVICE_GATEWAY_SIDECAR_NOT_YET_OBSERVED
AUTHENTIC_TVC_CANONICAL_ROUNDTRIP_ELIGIBLE_DRAIN_RECEIPT_NOT_YET_OBSERVED
AUTHENTIC_FOUR_LEG_INTR_ROUNDTRIP_NOT_YET_OBSERVED
AUTHENTIC_SKAP_KV_RETURN_RECEIPT_NOT_YET_OBSERVED
KV_SKAP_TERMINAL_EXACT_READBACK_NOT_YET_OBSERVED
```

`PHYSICAL_RUNTIME_NOT_PRESENT`, `ALWAYS_ON_RECEIVER_NOT_PRESENT`, `TESTFLIGHT_NOT_INSTALLED`, `REMOTE_DESKTOP_NOT_CONNECTED`, or `SECOND_DEVICE_NOT_PRESENT` are not valid blockers for this proof.

## Next

1. Validate and merge `.github` #1403 without reintroducing duplicate StegOS bridge/domain logic.
2. Produce or locate one authentic current-device Gateway sidecar + matching TVC `ADMITTED_TO_SKAP_VAULT_CUSTODY` / `canonical_roundtrip_eligible=true` receipt through the existing TVC owner.
3. Execute the canonical lane/domain consumer using authentic retained-Node, materialization, open-lease, Gateway, and TVC evidence.
4. Retain bridge + lease + four-hop + exact-readback evidence through canonical closure.
5. Close evidence conditions only when terminal verification returns `DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED`.

## README

Root `README.md` was reviewed for this source task. This is internal runtime/coordination wiring and does not alter repository-facing framework principles, so no README prose change is required.

## Manual work

None. Do not enter provider credential into chat, GitHub, Drive, ordinary KV, logs, screenshots, or repository state. Any eventual owner credential entry remains browser-local sealing only after authentic ingress readiness predicates are satisfied.
