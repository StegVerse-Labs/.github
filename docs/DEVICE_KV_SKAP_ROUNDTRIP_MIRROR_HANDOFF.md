# Device <-> KV <-> SKAP Roundtrip Mirror Handoff

Updated: 2026-09-10

```text
goal_id: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
parent_goal: KV-CONNECTION-REVALIDATION-WORKER-001
cosv_id: 50000000102000
state: ACTIVE
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

Completion requires four adjacent canonical InTr receipts, exact packet/readback verification, one continuous receipt-hash chain, TV/TVC credential authority, no secret plaintext in ordinary KV/device/repository state, no authority transfer, no hosted fallback, and no second user-operated device.

## Persistent Node / ephemeral execution separation

```text
PERSISTENT
retained StegBrowser/StegOS Node identity
genesis
continuity generation
state commitment
append-only evidence lineage

EPHEMERAL
current WorkerCoordinator claim/fence
canonical StegOS runtime lease
Interlock/InTr invocation
transport connection
task process
provider session
```

Universal InTr does not require an always-on receiver. A persistent physical server, TestFlight deployment, Render/Vercel runtime, Remote Desktop connector, or second user-operated machine is not a prerequisite to this proof.

## Canonical runtime collision reconciliation

StegOS already had a proven application-neutral `EVENT_EPHEMERAL` runtime before this roundtrip work:

```text
stegos/canonical_runtime_lane.py
stegos/ephemeral_runtime_lease.py
docs/CANONICAL_RUNTIME_LANE_MIRROR_HANDOFF.md
evidence/canonical-runtime/2026-08-30-first-observed-lane.json
```

That lane has authentic end-to-end evidence from an existing StegVerse Node through `REQUESTED -> ADMITTED -> PROVISIONING -> LOCAL_READY -> LEASE_OPEN -> bounded operation -> evidence retention -> LEASE_CLOSED`, with no persistent host or second participant/developer machine required.

Therefore this task MUST NOT create a competing Node runtime lifecycle. The recently added `stegos/node_event_execution_broker.py` is now canonically narrowed to a compatibility bridge whose role is:

```text
WORKERCOORDINATOR_TO_CANONICAL_RUNTIME_LANE
```

It binds one fresh WorkerCoordinator claim/fence and one registered domain capability to an already-open canonical lease plus exact retained-Node continuity. `WorkerCoordinatorCanonicalRuntimeBridge` aliases the historical class name so consumers do not fork implementation.

## Authority layering

```text
Canonical Runtime Lane -> runtime lease lifecycle / materialization / teardown contract
LeaseMachine -> canonical lease state + snapshot/resume
WorkerCoordinator -> fresh task claim/fence
WorkerCoordinator->Runtime bridge -> exact claim/fence + exact open lease + retained Node + capability binding
Interlock/InTr -> each governed state-transition admission inside the capability
TV/TVC -> credential authority and sole TVC SKAP ciphertext custody writer
retained StegOS Node -> identity/continuity/evidence lineage
GitHub/CI/HB -> source validation / evidence / observation only
```

A process being allowed to run is not itself a state-transition admission. An open canonical lease grants no Interlock/InTr transition authority. The bridge does not mint claims, open leases, grant transition admission, or own runtime lifecycle.

## Merged source lineage

Existing transport/custody work remains applicable:

- StegOS #326 -> `2339f2f2fc8c28eb4d63077387013154dac9b75c`; four-leg roundtrip composition/verification.
- LLM-adapter #331 -> `f4db7005818c7b77bf7e25345c86df1277760a93`; canonical secret-free DEVICE->KV Gateway sidecar.
- TVC #377 -> `72aa78c8f60226621c19d58751ec776f777583f9`; sidecar validation + sole SKAP ciphertext custody writer.
- `.github` #1332 -> `42996a4582e2fb9e4d3207dd3e45b764dc727723`; canonical continuation from Gateway/TVC evidence.
- `.github` #1339 -> `861647893df88c30f591e374a8be30fccaf7c64f`; false persistent-receiver prerequisite removed.
- `.github` #1352 -> `ec7594aac88b8d60b0d230be15f7901f1040b0fa`; event-execution/COSV reconciliation.
- Site #1196 -> `064f77f24b9ad505d2533bc4efc4a46f74c76799`; provider-neutral MyKV service federation.
- Site #1227 -> `64701e9e9896af0e0e97672706918b9417540cf3`; Site claim released while this task remains ACTIVE.

Runtime/WorkerCoordinator reconciliation:

- StegOS #332 merged `288a5a32c8c89bf0e44176330ce99bf487e4cc6c`; exact-head CI `34561345030` SUCCESS. Added the WorkerCoordinator/Node capability bridge source and tests.
- StegOS #333 merged `f955068eb23556458434e22d25d696ce9ff5cc9d`; exact-head CI `34561637472` SUCCESS. Corrected process admission to consume canonical `LeaseMachine` `EVENT_EPHEMERAL` state instead of pre-admitting Interlock transitions.
- `.github` #1399 merged `b273b35fbe96010ca136e84e3d48914d087a00fd`; exact-head organization-control `34561728446`, deterministic repository suite `34561728451`, and Heartbeat Worker validation `34561728452` all SUCCESS. The roundtrip process worker now consumes its actual fenced `stegverse.worker-invocation/v0.1`, fail-closes task/handoff/claim/fence/authority mismatches, and returns `stegverse.worker-response/v0.1`.
- StegOS #334 merged `18020e50bc5732216abeb5c2f00e6ec2ea91a11a`; exact-head StegOS CI `34561948078` SUCCESS. Explicitly absorbed the new bridge into the pre-existing Canonical Runtime Lane, records `bridge_owns_runtime_lifecycle=false`, and prohibits parallel runtime semantics.

No source merge or CI result above is authentic Device->KV->SKAP->KV->Device runtime proof.

## Node Manifold collision boundary

`STEGOS-NODE-MANIFOLD-001` remains a separate ACTIVE owner of physical multi-node/network-manifold proof: distinct second Node, `NETWORK_PRESENT`, fragmentation/reformation, and exact multi-node replay/reconstruction.

Its canonical record explicitly permits separately tracked service-KV work to reuse retained-Node and Interlock/InTr primitives without claiming physical-network proof. This task MUST NOT claim Node-Manifold completion, second-node participation, or physical-network evidence.

## Canonical consumer architecture

The intended final source path is now:

```text
retained Node identity/continuity
-> Universal InTr materialization request
-> canonical StegOS EVENT_EPHEMERAL lease lifecycle
-> fresh WorkerCoordinator claim/fence
-> WorkerCoordinatorCanonicalRuntimeBridge
-> Device/KV/SKAP bounded domain capability
-> Interlock/InTr admission per governed hop
-> exact four-leg proof/readbacks
-> canonical runtime evidence/closure
-> retained Node continuity advances
```

The bridge consumes an exact canonical `LEASE_OPEN` snapshot with:

```text
runtime_class = EVENT_EPHEMERAL
max_operations = 1
persistent_host_required = false
participant_machine_required = false
developer_machine_required = false
credential_authority = TV/TVC
authority_effect = NONE
bridge_owns_runtime_lifecycle = false
runtime_lease_grants_transition_authority = false
```

## WorkerCoordinator integration

Registered adapter:

```text
control/process-worker-adapters.d/device-kv-skap-roundtrip-001.json
adapter_ref = process:device-kv-skap-roundtrip-v1
command = python workers/run_device_kv_skap_roundtrip_worker.py
```

After `.github` #1399 the worker requires/binds:

```text
schema = stegverse.worker-invocation/v0.1
task.task_id = STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
scope.claim_id = task.claim_id
scope.fencing_token = task.heartbeat_timing.fencing_token
claim generation suffix matches fence
handoff goal/task identity matches
credential_authority = TV/TVC
github_token_runtime_authority = NONE
transition_authority = Interlock/InTr
```

The worker may not mint claim/fence. Terminal worker response may be `COMPLETED / DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED` only after authentic roundtrip verification succeeds.

## Preferred custody continuation

After TVC admits one authentic sealed ciphertext, `scripts/continue_device_kv_skap_from_tvc_custody.py`:

1. validates canonical DEVICE->KV sidecar;
2. validates terminal TVC custody and exact SKAP readback;
3. executes canonical KV->SKAP semantics;
4. emits chained SKAP->KV evidence;
5. persists/exact-readbacks KV return;
6. emits final KV->DEVICE receipt chained to SKAP->KV;
7. materializes four-leg manifest;
8. runs terminal verifier.

TVC remains the single ciphertext custody writer. Compatibility/direct custody code MUST NOT duplicate the same TVC custody write.

## Current bounded event wrapper

`scripts/execute_device_kv_skap_roundtrip_event.py` remains the existing one-shot WorkerCoordinator wrapper. It rejects hosted markers, refreshes already-local source, validates task/COSV, forwards only non-secret evidence paths, and invokes targeted WorkerCoordinator runtime.

Its current direct WorkerCoordinator execution semantics are valid but not yet the final canonical consumer wiring. Remaining source work is to bind the fenced worker invocation into the already-proven Canonical Runtime Lane/bridge without creating another claim, lease, or transition-authority path.

## Authentic prerequisite pair

Required runtime pair remains:

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

Canonical TVC producer: `StegVerse-Labs/TVC/tools/coinbase_gateway_stage_drain.py`.
Receipt tree: `_Vault/SKAP/Receipts/coinbase-drain`.

Fixture, reconstruction, GitHub Actions artifact, hosted substitute, or synthetic packet is not eligible.

## Completion contract

One authentic bounded execution must prove:

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
bridge owns no runtime/transition/credential authority
canonical runtime evidence retained before teardown
canonical lease closes cleanly
persistent transport process required = false
always-on receiver required = false
hosted_runtime_used = false
second_user_operated_device_used = false
terminal state = DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED
```

## Current implementation condition

```text
DEVICE_KV_SKAP_CANONICAL_RUNTIME_DOMAIN_BINDING_NOT_YET_MERGED
```

This is source integration only. It does not replace or satisfy authentic runtime evidence.

## Current authentic evidence conditions

```text
AUTHENTIC_CURRENT_DEVICE_GATEWAY_SIDECAR_NOT_YET_OBSERVED
AUTHENTIC_TVC_CANONICAL_ROUNDTRIP_ELIGIBLE_DRAIN_RECEIPT_NOT_YET_OBSERVED
AUTHENTIC_FOUR_LEG_INTR_ROUNDTRIP_NOT_YET_OBSERVED
AUTHENTIC_SKAP_KV_RETURN_RECEIPT_NOT_YET_OBSERVED
KV_SKAP_TERMINAL_EXACT_READBACK_NOT_YET_OBSERVED
```

`PHYSICAL_RUNTIME_NOT_PRESENT`, `ALWAYS_ON_RECEIVER_NOT_PRESENT`, `TESTFLIGHT_NOT_INSTALLED`, `REMOTE_DESKTOP_NOT_CONNECTED`, or `SECOND_DEVICE_NOT_PRESENT` MUST NOT be introduced as blockers.

## Next

1. Bind `run_device_kv_skap_roundtrip_worker.py` as the Device/KV/SKAP domain consumer of the existing Canonical Runtime Lane using the exact fresh WorkerCoordinator claim/fence; do not create a second runtime lifecycle.
2. Consume authentic retained-Node and canonical lease evidence; never fabricate them merely to make the domain adapter callable.
3. Produce/locate one authentic current-device Gateway sidecar + matching TVC `ADMITTED_TO_SKAP_VAULT_CUSTODY` / `canonical_roundtrip_eligible=true` receipt through the non-hosted TV/TVC path.
4. Execute the canonical lane/domain consumer and retain bridge + lease + four-hop + exact-readback evidence through canonical closure.
5. Close evidence conditions only when terminal verification returns `DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED`.

## Manual work

None. Do not enter provider credential into chat, GitHub, Drive, ordinary KV, logs, screenshots, or repository state. Any eventual owner credential entry remains browser-local sealing only after authentic ingress readiness predicates are satisfied.
