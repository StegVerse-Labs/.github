# Device <-> KV <-> SKAP Roundtrip Mirror Handoff

Updated: 2026-09-10

```text
goal_id: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
parent_goal: KV-CONNECTION-REVALIDATION-WORKER-001
cosv_id: 50000000102000
state: ACTIVE
canonical_owner: StegVerse-Labs/.github
implementation_owner: StegVerse-Labs/StegOS
transition_authority: Interlock/InTr
credential_authority: TV/TVC
worker_claim_authority: WorkerCoordinator
github_runtime_authority: NONE
hosted_runtime_fallback: NONE
second_user_operated_device_required: false
persistent_transport_runtime_required: false
event_ephemeral_materialization_allowed: true
```

## Goal

Prove one authentic sovereign single-device operation lineage:

```text
DEVICE_SYSTEM -> KV -> SKAP_VAULT -> KV -> DEVICE_SYSTEM
```

Completion requires four adjacent canonical InTr receipts, exact packet/readback verification, one continuous receipt-hash chain, TV/TVC credential authority, no secret plaintext in ordinary KV/device/repository state, no authority transfer, no hosted fallback, and no second user-operated device.

## Persistent Node / ephemeral execution separation

Canonical StegOS architecture separates retained identity from bounded task execution:

```text
PERSISTENT
retained StegBrowser/StegOS Node identity
genesis
continuity generation
state commitment
append-only evidence lineage

EPHEMERAL
current WorkerCoordinator task claim
StegOS runtime lease
Interlock/InTr invocation
transport connection
task process
provider session
```

Universal InTr does not require an always-on receiver. Exact packets may be transported immediately, durably queued, or cause bounded `EVENT_EPHEMERAL` materialization. A persistent physical server, TestFlight deployment, Render/Vercel runtime, or second user-operated machine is therefore not a prerequisite to this proof.

Ephemeral execution does not relax authority or evidence requirements. The bounded invocation must bind to retained Node identity/continuity and authentic runtime evidence.

## Correct authority layering

```text
WorkerCoordinator -> fresh task claim/fence
StegOS runtime lease -> bounded process lifetime/admission
Interlock/InTr -> each governed state-transition admission
TV/TVC -> credential authority and TVC SKAP ciphertext custody writer
StegOS retained Node -> identity/continuity/evidence lineage
GitHub/CI/HB -> source validation / evidence / observation only
```

A process being allowed to run is not itself an Interlock/InTr transition admission. Conversely, an `EVENT_EPHEMERAL` lease grants no transition authority. Each Device/KV/SKAP hop remains individually governed by canonical Interlock/InTr.

## Merged source lineage

Earlier source remains merged and applicable:

- StegOS #326 -> `2339f2f2fc8c28eb4d63077387013154dac9b75c`; four-leg roundtrip composition/verification source.
- LLM-adapter #331 -> `f4db7005818c7b77bf7e25345c86df1277760a93`; Gateway emits canonical secret-free DEVICE->KV sidecar.
- TVC #377 -> `72aa78c8f60226621c19d58751ec776f777583f9`; TVC validates sidecar and remains sole SKAP ciphertext custody writer.
- `.github` #1332 -> `42996a4582e2fb9e4d3207dd3e45b764dc727723`; canonical continuation from Gateway/TVC evidence.
- `.github` #1339 -> `861647893df88c30f591e374a8be30fccaf7c64f`; persistent physical transport/always-on receiver removed as false prerequisite.
- `.github` #1352 -> `ec7594aac88b8d60b0d230be15f7901f1040b0fa`; canonical event-execution/COSV reconciliation validated.
- Site #1196 -> `064f77f24b9ad505d2533bc4efc4a46f74c76799`; provider-neutral MyKV service federation source.
- Site #1227 -> `64701e9e9896af0e0e97672706918b9417540cf3`; Site implementation claim released while canonical child remained ACTIVE.

Native Node execution progression:

- StegOS #332 merged at `288a5a32c8c89bf0e44176330ce99bf487e4cc6c`; exact-head StegOS CI run `34561345030` SUCCESS. Added reusable `stegos/node_event_execution_broker.py`, focused tests, and Node broker handoff. The broker consumes Universal InTr materialization + retained Node continuity + external WorkerCoordinator authority and executes one registered bounded capability without becoming credential or transition authority.
- StegOS #333 merged at `f955068eb23556458434e22d25d696ce9ff5cc9d`; exact-head StegOS CI run `34561637472` SUCCESS. Corrected the broker authority layering so process execution is admitted by the existing canonical StegOS `EVENT_EPHEMERAL` `LeaseMachine`, while Interlock/InTr remains responsible for each state transition inside the task. The broker requires an exact `LEASE_OPEN` single-operation admission and cannot open its own lease, mint claim/fence, or grant transition admission.
- `.github` #1399 merged at `b273b35fbe96010ca136e84e3d48914d087a00fd`; exact-head organization-control run `34561728446`, deterministic repository suite `34561728451`, and Heartbeat Worker validation `34561728452` all SUCCESS. The registered Device/KV/SKAP worker now consumes the actual fenced `stegverse.worker-invocation/v0.1`, validates task/handoff/claim/fence/authority bindings before touching runtime evidence, and emits the required `stegverse.worker-response/v0.1` rather than ignoring the ProcessWorkerAdapter invocation protocol.

No merge or CI result above is authentic four-leg runtime proof.

## Node Manifold collision boundary

`STEGOS-NODE-MANIFOLD-001` remains a distinct ACTIVE workstream owning physical multi-node/network-manifold proof: distinct second Node, `NETWORK_PRESENT`, fragmentation/reformation, and exact multi-node replay/reconstruction.

Its canonical record explicitly permits separately tracked service-KV work to reuse retained-Node and Interlock/InTr primitives without claiming physical network proof. This task therefore reuses Node execution primitives but MUST NOT claim Node-Manifold completion, second-node participation, or physical-network evidence.

## Native Node execution broker

The durable execution architecture is now:

```text
retained Node identity/continuity
-> Universal InTr materialization request
-> fresh WorkerCoordinator claim/fence
-> canonical StegOS EVENT_EPHEMERAL lease -> LEASE_OPEN
-> registered capability adapter
-> bounded task invocation
-> canonical Interlock/InTr per governed hop
-> exact result / receipt commitments
-> lease/process teardown
-> retained Node identity/continuity remains
```

Remote Desktop Commander or another external terminal bridge may be operationally useful, but it is not part of the StegOS architecture and is not a completion predicate.

The generic broker is merged. The roundtrip-specific binding of the existing Device/KV/SKAP worker into that broker remains an implementation condition. That binding must consume authentic retained-Node and runtime-lease evidence; it may not fabricate either merely to make the adapter callable.

## Preferred custody continuation

After TVC has admitted one authentic sealed ciphertext, `scripts/continue_device_kv_skap_from_tvc_custody.py`:

1. validates the canonical DEVICE->KV sidecar;
2. validates terminal TVC custody and exact SKAP readback;
3. uses canonical `kv-skap` REFERENCE semantics for KV->SKAP;
4. emits chained SKAP->KV evidence;
5. persists and exact-readbacks the KV return;
6. emits final KV->DEVICE receipt chained to SKAP->KV;
7. materializes the four-leg manifest;
8. runs the terminal verifier.

TVC remains the single ciphertext custody writer. `consume_kv_skap_custody_materialization_request.py` MUST NOT duplicate a TVC custody write for the same ciphertext.

The worker may invoke canonical StegOS Interlock/InTr only under the admitted task/runtime scope. The connector may materialize hop receipts under its own transition semantics. WorkerCoordinator, GitHub, HB, transport, broker, and verifier grant no transition or credential authority.

## WorkerCoordinator integration

The registered process adapter remains:

```text
control/process-worker-adapters.d/device-kv-skap-roundtrip-001.json
adapter_ref = process:device-kv-skap-roundtrip-v1
command = python workers/run_device_kv_skap_roundtrip_worker.py
```

After `.github` #1399, the worker binds the exact ProcessWorkerAdapter invocation:

```text
schema = stegverse.worker-invocation/v0.1
task.task_id = STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
scope.claim_id = task.claim_id
scope.fencing_token = task.heartbeat_timing.fencing_token
claim suffix generation matches fence
handoff goal/task identity matches
credential_authority = TV/TVC
github_token_runtime_authority = NONE
transition_authority = Interlock/InTr
```

On authentic terminal success it returns `stegverse.worker-response/v0.1` with `state=COMPLETED` and transition `DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED`. It does not mint the claim/fence and it still requires the authentic continuation inputs.

## Existing bounded event wrapper

`scripts/execute_device_kv_skap_roundtrip_event.py` remains the current one-shot orchestration wrapper. It rejects hosted markers, refreshes already-local canonical WorkerCoordinator source, validates the task/COSV pointer, forwards only non-secret evidence paths, and invokes:

```text
scripts/run_worker_runtime.py --task-id STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
```

That targeted runtime obtains normal WorkerCoordinator claim/fence semantics. The wrapper itself grants no execution, transition, provider, or credential authority.

The next implementation step is to route this one-shot path through the merged native Node execution broker using an authentic retained-Node snapshot and exact open `EVENT_EPHEMERAL` lease admission, without creating a second WorkerCoordinator or Interlock authority path.

## Authentic prerequisite pair

Repository evidence still does not contain an eligible authentic current-device outcome carrying both an authentic Gateway first hop and matching TVC roundtrip-eligible custody admission. Required pair:

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

## MyKV relationship

Ordinary personal information belongs in KV. Credential/signing material belongs in SKAP; KV may retain only a non-secret SKAP reference/binding. This child proves the governed transport/evidence lane connecting those boundaries and does not move ordinary personal data wholesale into SKAP.

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
canonical retained Node identity/continuity binding preserved
fresh WorkerCoordinator claim/fence preserved
bounded StegOS EVENT_EPHEMERAL lease preserved
broker grants no transition/credential authority
persistent transport process required = false
always-on receiver required = false
hosted_runtime_used = false
second_user_operated_device_used = false
terminal state = DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED
```

## Current implementation condition

```text
ROUNDTRIP_SPECIFIC_NODE_EVENT_EXECUTION_BROKER_BINDING_NOT_YET_MERGED
```

This is a source integration condition, not runtime evidence and not a reason to introduce a persistent server. The generic broker, runtime-lease correction, and WorkerCoordinator process protocol are merged/validated.

## Current authentic evidence conditions

```text
AUTHENTIC_CURRENT_DEVICE_GATEWAY_SIDECAR_NOT_YET_OBSERVED
AUTHENTIC_TVC_CANONICAL_ROUNDTRIP_ELIGIBLE_DRAIN_RECEIPT_NOT_YET_OBSERVED
AUTHENTIC_FOUR_LEG_INTR_ROUNDTRIP_NOT_YET_OBSERVED
AUTHENTIC_SKAP_KV_RETURN_RECEIPT_NOT_YET_OBSERVED
KV_SKAP_TERMINAL_EXACT_READBACK_NOT_YET_OBSERVED
```

`PHYSICAL_RUNTIME_NOT_PRESENT`, `ALWAYS_ON_RECEIVER_NOT_PRESENT`, `TESTFLIGHT_NOT_INSTALLED`, `REMOTE_DESKTOP_NOT_CONNECTED`, or `SECOND_DEVICE_NOT_PRESENT` MUST NOT be introduced as blockers for this proof.

## Next

1. Bind the registered Device/KV/SKAP worker as the first consumer of the merged StegOS Node event broker, reusing the existing WorkerCoordinator claim/fence and canonical StegOS single-operation `EVENT_EPHEMERAL` lease; do not create parallel claim, lease, or transition authority.
2. Produce or locate one authentic current-device Gateway canonical sidecar and matching TVC `ADMITTED_TO_SKAP_VAULT_CUSTODY` / `canonical_roundtrip_eligible=true` drain receipt through the existing non-hosted TV/TVC path.
3. Execute the broker-bound one-shot roundtrip under retained Node identity/continuity.
4. Retain the four chained receipts plus exact SKAP/KV readbacks and broker/lease/claim evidence.
5. Close the evidence conditions only when terminal verification returns `DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED`.

## Manual work

None. Do not enter provider credential into chat, GitHub, Drive, ordinary KV, logs, screenshots, or repository state. Any eventual owner credential entry remains browser-local sealing only after the authentic ingress readiness predicates are satisfied.
