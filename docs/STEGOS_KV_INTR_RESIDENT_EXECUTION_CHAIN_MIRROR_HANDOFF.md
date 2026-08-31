# StegOS / KnowledgeVault InTr Resident Execution Chain Mirror Handoff

Updated: 2026-08-30

```text
repository: StegVerse-Labs/.github
request: control/resident-execution-request.d/stegos-kv-intr-chain-001.json
consumer: scripts/consume_stegos_kv_intr_chain_request.py
state: SOURCE_MERGED_VALIDATED / RESIDENT_CONSUMPTION_PENDING
credential_authority: TV/TVC
github_token_runtime_authority: NONE
heartbeat_grants_execution_authority: false
second_machine_required: false
authority_effect: NONE_REQUEST_ONLY
```

## Purpose

Close the resident-dispatch gap for the already-built machine-owned chain, without
creating a new task, claim, fence, scheduler, HeartBeat, runtime owner, credential
path, route authority, or transport broker.

```text
SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001
-> SOVEREIGN_RELAY_LEASE_OPEN
-> SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001
-> RELAY_NODE_KV_CONTINUITY_VERIFIED
-> SHWP-DEVICE-KV-INTR-OBSERVATION-001
-> DEVICE_KV_INTR_OBSERVED
```

## Execution contract

The consumer invokes the merged portable targeted execution bridge for exactly one
existing task at a time. It advances only when the preceding canonical terminal
receipt exists locally with the exact required state/transition. A blocked parent
records ATTEMPT_RECORDED and stops; successor evidence is never synthesized.

The portable bridges must forward only non-secret local locators, including
STEGVERSE_STEGOS_ROOT, STEGVERSE_KV_SOURCE_ROOT, and STEGVERSE_RELAY_RUNTIME_BASE.
GitHub tokens and NON-TV/TVC credentials are rejected, and network source fetch is
not authorized.

## Required authentic terminal evidence

```text
receipts/stegos-sovereign-relay/SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001.json
  state=COMPLETED
  transition_id=SOVEREIGN_RELAY_LEASE_OPEN

receipts/stegos-sovereign-relay/SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001.json
  state=COMPLETED
  transition_id=RELAY_NODE_KV_CONTINUITY_VERIFIED

receipts/device-kv-intr/SHWP-DEVICE-KV-INTR-OBSERVATION-001.json
  state=OBSERVED
  transition_id=DEVICE_KV_INTR_OBSERVED
```

## Lifecycle boundary

```text
request merged != resident request consumed
resident request consumed != parent terminal receipt
parent terminal receipt != successor terminal receipt
DEVICE_KV_INTR_OBSERVED != production Interlock global activation
```

Hosted validation may prove the consumer fails closed; it cannot satisfy a runtime
terminal predicate.


## Native materialization parity follow-up

Post-merge inspection found that native bootstrap uses an explicit script allowlist.
The dispatcher registration alone therefore did not guarantee that a fresh sovereign
runtime contained this chain consumer. The same omission was present for the recently
merged Bootstrap v1 InTr bundle-delivery consumer.

The parity repair adds both registered consumers to:
- native heartbeat runtime COPY_FILES and required-file validation;
- native sovereign bootstrap REQUIRED_SOURCE_FILES;
- already-local sovereign source refresh STATIC_FILES;
- regression tests for fresh materialization and local refresh.

This changes source materialization only. It does not prove resident consumption,
lease opening, Node-KV continuity, DEVICE_KV_INTR observation, or global activation.


## Resident execution wiring merge evidence

The machine-execution request/consumer path is now source-complete and merged.

```text
PR #570
validated_head: a91ef2cfa6b74ba8c305f7b320f3adb450799b0c
merge: 0fc4d4e9bd5b1a691c43f4ad2001061c5cd654f3
Validate organization control plane: 33345860778 SUCCESS
Heartbeat Worker Project: 33345860872 SUCCESS
Cross-Framework Current-Basis Resident Request Validation: 33345860816 SUCCESS

PR #571
validated_head: d7d1f45b758e8b06112a769db4ea44edad7d6104
merge: bb0cfe28a2b0444018748a681ab76259ee6fe16a
Validate organization control plane: 33345999217 SUCCESS
Heartbeat Worker Project: 33345999175 SUCCESS
Cross-Framework Current-Basis Resident Request Validation: 33345999180 SUCCESS
```

Merged source predicates now satisfied:

- resident request exists under `control/resident-execution-request.d/`;
- exact `stegos_kv_intr_chain` consumer is registered and selectable;
- `STEGVERSE_STEGOS_ROOT`, `STEGVERSE_KV_SOURCE_ROOT`, and relay runtime root
  survive the portable execution boundary as non-secret locators;
- fresh native materialization includes the chain consumer;
- already-local source refresh includes the chain consumer;
- Bootstrap v1 InTr's registered consumer is also included in fresh native
  materialization, closing the adjacent parity defect found during this work;
- mutable resident `worker-registry.json` remains preserved while current
  `worker-registry.d` fragments are applied by WorkerCoordinator before targeted
  independent admission.

Current runtime evidence remains deliberately unsatisfied:

```text
receipts/sovereign-host/stegos-kv-intr-chain-consumption.latest.json: NOT OBSERVED
SOVEREIGN_RELAY_LEASE_OPEN: NOT OBSERVED
RELAY_NODE_KV_CONTINUITY_VERIFIED: NOT OBSERVED
DEVICE_KV_INTR_OBSERVED: NOT OBSERVED
production Interlock activation: NOT PROVEN
```

The remaining state-changing event must occur on an eligible non-hosted sovereign
resident with current local source and writable durable state. The existing G18
resolver may derive the node declaration there automatically. No additional user
authorization, second user-operated machine, GitHub runtime credential, or
third-party runtime substitution is required or permitted by this chain.


## Outbound resident rendezvous continuation — issue #578

The missing interactive server-control connector is now being removed as an architectural dependency rather than accepted as an operational blocker.

The sovereign WorkerCoordinator runtime gains an outbound-only Service Gateway rendezvous consumer:

```text
StegVerse Service Gateway bounded intent
-> resident outbound poll
-> exact digest/schema/task/mode validation
-> local resident request materialization
-> existing dispatch_resident_execution_requests.py
-> existing stegos_kv_intr_chain consumer
-> WorkerCoordinator independent admission/claim/fence
-> local execution attempt
-> bounded acknowledgement
```

The Gateway request itself grants no authority. The consumer is copied by the existing local source refresh and native materializer, and the continuous WorkerCoordinator polls it only when explicit non-secret rendezvous URL/node-ref configuration is installed. Targeted task execution does not poll recursively.

Canonical scoped handoff: `docs/RESIDENT_RENDEZVOUS_CONSUMER_MIRROR_HANDOFF.md`.

This source work does not itself prove the current resident has refreshed to the new consumer, the public Gateway is deployed with rendezvous enabled, or the three runtime terminal receipts exist.


## 2026-08-31 request-003 rendezvous propagation — issue #654

The canonical Device-KV resident intent is now `RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-003`.

Resident rendezvous local materialization permits only the bounded historical migration:
```text
001 -> 003
002 -> 003
```
provided the execution contract remains identical for schema, state, task, mode, entrypoint, credential/authority flags, and the canonical three-step chain. The prior local request is archived write-once before replacement and verified after write.

No unrelated request id, task, mode, command, credential, or step vector may be substituted. This is request continuity only; it does not create WorkerCoordinator claim/fence, execution authority, HB progression authority, or runtime evidence.
