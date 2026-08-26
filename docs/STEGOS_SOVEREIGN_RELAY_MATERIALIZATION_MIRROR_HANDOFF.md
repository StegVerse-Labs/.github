# StegOS Sovereign Relay Materialization Mirror Handoff

Updated: 2026-08-26

```text
goal_id: SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001
repository: StegVerse-Labs/.github
branch: dev/stegos-sovereign-relay-materialization
parent_goal: SHWP-DURABLE-RUNTIME-ACTIVATION
upstream_goal: STEGOS-SOVEREIGN-NETWORK-CAPACITY-001
state: SOURCE_IMPLEMENTATION_ACTIVE
credential_authority: TV/TVC
github_token_runtime_authority: NONE
heartbeat_grants_execution_authority: false
physical_additional_machine_required: false
third_party_runtime_required: false
```

## Authority and nonduplication

This lane binds the merged `StegVerse-Labs/StegOS` sovereign relay adapter to the existing `.github` WorkerCoordinator/G18 execution plane. It does not create a second HeartBeat, worker scheduler, compute authority, route authority, credential path, canonical-state authority, or transport broker.

Canonical upstream StegOS source is merge `a91838bf1c20eaacbbdada7e391aa462a862d72e` and includes `stegos/ephemeral_relay_service.py`, `stegos/sovereign_ephemeral_node_adapter.py`, and the provider-neutral ESRL runtime-dispatch controller.

Live HeartBeat/runtime authority remains `SHWP-DURABLE-RUNTIME-ACTIVATION` / G18 until its canonical owner releases or supersedes that fence. This task is independently admitted task-control work only; HeartBeat is a reference frame and grants no execution authority.

## Intended runtime transition

```text
HANDOFF_READY relay-materialization task
-> independent WorkerCoordinator admission
-> fresh fence
-> resolve already-materialized StegOS source root
-> verify exact pinned relay adapter surface
-> consume admitted relay activation request
-> invoke merged StegOS ESRL controller + SovereignEphemeralNodeAdapter
-> existing .github sovereign materializer/supervisor
-> isolated sovereign runtime root
-> bounded opaque relay process
-> local identity verification
-> bounded rendezvous probe
-> ESRL LEASE_OPEN evidence
-> durable .github receipt
```

No network credential checkout is permitted. If the pinned StegOS source is not already materialized on the sovereign carrier, the worker remains active with a machine-resolvable source-materialization requirement rather than inventing another host or credential path.

## Completion predicates

Source completion requires the worker, source resolver, process-adapter registration, worker-registry fragment, executable handoff, and tests to be merged with repository-owned validation.

Runtime completion requires a deployment-local execution under an admitted fresh fence that observes all of:

```text
stegos source root resolved and exact required source surfaces present
runtime request admitted
credential_authority = TV/TVC
credential material absent
third-party runtime absent
sovereign runtime materialized
relay process started
local identity verified
bounded rendezvous verified
ESRL lease_state = LEASE_OPEN
route_admitted = false
outbound_egress_executed = false
canonical_transition_committed = false
```

A hosted CI pass, fake process/socket test, or source merge does not satisfy runtime completion.

## Downstream

After authentic `LEASE_OPEN`, prove durable Node-KV identity continuity across teardown/recreation. Route admission, outbound ESRL EGRESS, TV/TVC mandate/broker execution, far-side transport evidence, verified-work compensation, and settlement remain separate downstream governed transitions.
