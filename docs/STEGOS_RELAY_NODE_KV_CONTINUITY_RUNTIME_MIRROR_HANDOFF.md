# StegOS Relay Node-KV Continuity Runtime Mirror Handoff

Updated: 2026-08-26

```text
goal_id: SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001
repository: StegVerse-Labs/.github
branch: dev/stegos-relay-node-kv-continuity-runtime
parent_goal: SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001
upstream_goal: STEGOS-SOVEREIGN-NETWORK-CAPACITY-001
state: SOURCE_IMPLEMENTATION_ACTIVE
credential_authority: TV/TVC
github_token_runtime_authority: NONE
heartbeat_grants_execution_authority: false
physical_additional_machine_required: false
third_party_runtime_required: false
runtime_activation: false
```

## Purpose and authority boundary

This lane closes the source gap between the first authentic sovereign relay `LEASE_OPEN` and the already-merged StegOS Node-KV teardown/recreation continuity verifier.

It does not create a second HeartBeat, WorkerCoordinator, compute/runtime owner, route authority, credential mechanism, canonical-state authority, transport broker, or hosted substitute. It is a bounded successor worker under the existing `INDEPENDENT_TASK_CONTROL` plane.

The parent runtime proof remains mandatory and cannot be synthesized:

```text
receipts/stegos-sovereign-relay/SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001.json
state: COMPLETED
transition_id: SOVEREIGN_RELAY_LEASE_OPEN
```

If that object is absent or incomplete, this worker remains active and performs no teardown/recreation.

## Runtime sequence

```text
authentic parent SOVEREIGN_RELAY_LEASE_OPEN
-> fresh independently admitted WorkerCoordinator fence > 21
-> load exact first materialization evidence/runtime
-> reuse merged SovereignEphemeralNodeAdapter
-> real adapter.release(first runtime)
-> verify relay + carrier + worker termination
-> build teardown observation
-> derive distinct controlled recreation request
-> advance generation
-> preserve Node-KV state root / implementation / registry / region
-> reuse existing materialize_relay path
-> obtain distinct second LEASE_OPEN
-> run merged StegOS prove_node_kv_recreation_continuity
-> durable continuity worker receipt
```

The recreation remains a controlled runtime proof and does not claim a real production capacity deficit.

## Installed source surfaces

```text
docs/STEGOS_RELAY_NODE_KV_CONTINUITY_RUNTIME_MIRROR_HANDOFF.md
handoffs/SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001.json
workers/stegos_relay_node_kv_continuity_worker.py
control/worker-registry.d/stegos-relay-node-kv-continuity-001.json
control/process-worker-adapters.d/stegos-relay-node-kv-continuity-001.json
cost-basis/worker-runtime/stegos-relay-node-kv-continuity.json
control/admissible-existence-retrospective-conformance.d/stegos-relay-node-kv-continuity-001.json
tests/test_stegos_relay_node_kv_continuity_worker.py
```

## Completion predicates

Source completion requires all listed surfaces to be merged with repository-owned validation.

Runtime completion requires:

```text
parent authentic LEASE_OPEN observed
real first runtime release
relay_terminated = true
carrier_terminated = true
worker_terminated = true
recreated evidence identity != first evidence identity
recreated lease identity != first lease identity
recreated generation > first generation
exact Node-KV state-root continuity
implementation/registry/region continuity
credential_authority = TV/TVC
credential_material_present = false
route_admitted = false
outbound_egress_executed = false
canonical_transition_committed = false
```

Terminal evidence:

```text
receipts/stegos-sovereign-relay/SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001.json
state: COMPLETED
transition_id: RELAY_NODE_KV_CONTINUITY_VERIFIED
```

Hosted CI, fixture evidence, source merge, or a repeated observation of the same lease cannot satisfy runtime continuity.

## Downstream

After authentic continuity proof, the next distinct transitions remain:

```text
real production capacity-deficit / regional rebalance
independent route admission
TV/TVC ESRL EGRESS mandate lifecycle
real brokered outbound emission
far-side transport evidence
durable return carrier
Interlock result ingestion
verified useful-work compensation evidence
settlement
physical-network sovereignty
```

Each remains separately governed.
